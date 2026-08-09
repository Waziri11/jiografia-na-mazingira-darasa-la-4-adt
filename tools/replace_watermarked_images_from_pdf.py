#!/usr/bin/env python3
"""Replace watermarked ADT crops from clean renders of their source PDF pages."""

from pathlib import Path
import json
import re
import shutil
import sys

import numpy as np
from PIL import Image


def edge_map(image: Image.Image, scale: float = 0.25) -> np.ndarray:
    width = max(8, round(image.width * scale))
    height = max(8, round(image.height * scale))
    gray = np.asarray(image.convert("L").resize((width, height), Image.Resampling.BILINEAR), dtype=np.float32)
    gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    gy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    edge = gx + gy
    return np.where(edge > 10.0, edge, 0.0)


def normalized_match(full: np.ndarray, template: np.ndarray) -> tuple[float, int, int]:
    fh, fw = full.shape
    th, tw = template.shape
    shape = (fh + th - 1, fw + tw - 1)
    corr = np.fft.irfft2(
        np.fft.rfft2(full, shape) * np.fft.rfft2(template[::-1, ::-1], shape),
        shape,
    ).real
    corr = corr[th - 1 : fh, tw - 1 : fw]

    squared = np.pad(full * full, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    local_energy = (
        squared[th:, tw:]
        - squared[:-th, tw:]
        - squared[th:, :-tw]
        + squared[:-th, :-tw]
    )
    template_energy = float((template * template).sum())
    score = corr / np.sqrt(np.maximum(local_energy * template_energy, 1.0))
    y, x = np.unravel_index(np.argmax(score), score.shape)
    return float(score[y, x]), int(x), int(y)


def locate_crop(page: Image.Image, target: Image.Image) -> tuple[int, int, int, int, float]:
    downsample = 0.25
    page_edges = edge_map(page, downsample)
    target_edges = edge_map(target, downsample)
    best = (-1.0, 0, 0, 1.0, target_edges.shape[1], target_edges.shape[0])
    for ratio in np.arange(0.80, 1.251, 0.01):
        tw = max(8, round(target_edges.shape[1] * ratio))
        th = max(8, round(target_edges.shape[0] * ratio))
        if tw >= page_edges.shape[1] or th >= page_edges.shape[0]:
            continue
        template = np.asarray(
            Image.fromarray(target_edges).resize((tw, th), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        score, x, y = normalized_match(page_edges, template)
        if score > best[0]:
            best = (score, x, y, float(ratio), tw, th)

    score, x, y, ratio, _, _ = best
    left = round(x / downsample)
    top = round(y / downsample)
    width = round(target.width * ratio)
    height = round(target.height * ratio)
    return left, top, left + width, top + height, score


def replace(page_path: Path, target_path: Path, destination: Path) -> tuple[tuple[int, int, int, int], float]:
    page = Image.open(page_path).convert("RGB")
    target = Image.open(target_path).convert("RGB")
    left, top, right, bottom, score = locate_crop(page, target)
    crop = page.crop((left, top, right, bottom)).resize(target.size, Image.Resampling.LANCZOS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.suffix.lower() in {".jpg", ".jpeg"}:
        crop.save(destination, quality=95, subsampling=0)
    else:
        crop.save(destination)
    return (left, top, right, bottom), score


def watermark_pixels(target_path: Path, clean_path: Path) -> int:
    target = np.asarray(Image.open(target_path).convert("RGB"), dtype=np.int16)
    clean = np.asarray(Image.open(clean_path).convert("RGB"), dtype=np.int16)
    red, green, blue = np.moveaxis(target, 2, 0)
    clean_red, clean_green, clean_blue = np.moveaxis(clean, 2, 0)
    signature = (
        (clean_green - green > 9)
        & (clean_blue - blue > 9)
        & (red - (green + blue) / 2 > 14)
        & (clean_red - red < 18)
    )
    return int(signature.sum())


def batch_audit(root: Path, render_dir: Path, preview_dir: Path, apply: bool) -> list[dict]:
    referenced = set()
    for html_path in root.glob("*.html"):
        referenced.update(re.findall(r'images/([^"?]+)', html_path.read_text(encoding="utf-8")))

    preview_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for filename in sorted(referenced):
        match = re.match(r"pg(\d{3})_", filename)
        if not match:
            continue
        page_number = int(match.group(1))
        page_path = render_dir / f"page-{page_number:02d}.png"
        target_path = root / "images" / filename
        if not page_path.is_file() or not target_path.is_file():
            continue
        candidate_path = preview_dir / filename
        try:
            box, score = replace(page_path, target_path, candidate_path)
        except Exception as error:
            report.append({"file": filename, "error": str(error)})
            continue
        count = watermark_pixels(target_path, candidate_path)
        total = Image.open(target_path).width * Image.open(target_path).height
        threshold = max(24, round(total * 0.00025))
        affected = score >= 0.64 and count >= threshold
        if apply and affected:
            shutil.copyfile(candidate_path, target_path)
        report.append(
            {
                "file": filename,
                "page": page_number,
                "box": box,
                "score": round(score, 4),
                "watermark_pixels": count,
                "threshold": threshold,
                "affected": affected,
            }
        )
        print(
            f"{'WATERMARK' if affected else 'clean/skip':9} {filename:42} "
            f"score={score:.3f} pixels={count}"
        )

    (preview_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    if len(sys.argv) in (4, 5) and sys.argv[1] == "--batch":
        batch_audit(Path.cwd(), Path(sys.argv[2]), Path(sys.argv[3]), len(sys.argv) == 5 and sys.argv[4] == "--apply")
    elif len(sys.argv) == 4:
        box, score = replace(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
        print(f"box={box} score={score:.4f}")
    else:
        raise SystemExit(
            f"Usage: {sys.argv[0]} CLEAN_PAGE TARGET_IMAGE DESTINATION\n"
            f"   or: {sys.argv[0]} --batch RENDER_DIR PREVIEW_DIR [--apply]"
        )
