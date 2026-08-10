#!/usr/bin/env python3
"""Verify the structure, crops, and narration hooks for every Kazi ya kufanya."""

from pathlib import Path
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXTS = json.loads((ROOT / "content/i18n/sw/texts.json").read_text(encoding="utf-8"))
AUDIOS = json.loads((ROOT / "content/i18n/sw/audios.json").read_text(encoding="utf-8"))
HTML = {path.name: path.read_text(encoding="utf-8") for path in ROOT.glob("pg*_sec*.html")}

# Illustrations that belong to a Kazi ya kufanya and therefore require a
# substantive image-only description. Decorative activity icons are excluded.
ACTIVITY_ILLUSTRATIONS = {
    "pg016_im039_seg001_v1", "pg016_im039_seg002_v1", "pg016_im039_seg003_v1",
    "pg016_im039_seg004_v1", "pg019_im037", "pg030_im113", "pg034_im050", "pg047_im129",
    "pg048_im087", "pg060_im030", "pg061_im038", "pg062_im043_seg004_v1",
    "pg067_im035", "pg070_im036", "pg075_im027", "pg080_im127", "pg081_im029",
    "pg083_im113", "pg085_im155",
}

# These replacements deliberately contain only the illustration. Their exact
# dimensions prove that the printed activity banner and page footer are absent.
STRICT_CROPS = {
    "images/pg030_im113_illustration_v3.png": (592, 491),
    "images/pg048_im087_illustration_v3.png": (519, 487),
    "images/pg061_im038_illustration_v3.png": (577, 631),
}


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", header[16:24])


errors: list[str] = []
title_ids = {
    text_id: text for text_id, text in TEXTS.items()
    if re.fullmatch(r"pg\d+_n\d+", text_id)
    and re.fullmatch(r"Kazi ya kufanya namba \d+(?::.*)?", text, re.I)
}

for text_id, title in title_ids.items():
    matches = []
    for filename, source in HTML.items():
        for tag in re.findall(rf"<[^>]+data-id=\"{re.escape(text_id)}\"[^>]*>", source):
            matches.append((filename, tag))
    visible = [item for item in matches if not item[1].startswith("<img") and "sr-only" not in item[1]]
    if not visible:
        errors.append(f"{text_id}: activity title is not a separate visible heading ({title})")
    if text_id not in AUDIOS:
        errors.append(f"{text_id}: activity title has no audio mapping")

used_image_ids = set()
for filename, source in HTML.items():
    for tag in re.findall(r"<img\b[^>]*>", source):
        match = re.search(r'data-id="([^"]+)"', tag)
        if not match:
            continue
        text_id = match.group(1)
        used_image_ids.add(text_id)
        description = TEXTS.get(text_id, "").strip()
        if description.lower().startswith("kazi ya kufanya"):
            errors.append(f"{filename}: {text_id} folds the activity title into the image description")

for text_id in sorted(ACTIVITY_ILLUSTRATIONS):
    description = TEXTS.get(text_id, "").strip()
    if text_id not in used_image_ids:
        errors.append(f"{text_id}: expected activity illustration is not used in HTML")
    if len(description) < 120:
        errors.append(f"{text_id}: illustration description is not sufficiently complete ({len(description)} chars)")
    audio_name = AUDIOS.get(text_id)
    if not audio_name:
        errors.append(f"{text_id}: illustration description has no audio mapping")
    elif not (ROOT / "content/i18n/sw/audio" / audio_name).is_file():
        errors.append(f"{text_id}: missing illustration audio file {audio_name}")

all_html = "\n".join(HTML.values())
for relative_path, expected_size in STRICT_CROPS.items():
    path = ROOT / relative_path
    if relative_path not in all_html:
        errors.append(f"{relative_path}: strict illustration crop is not referenced")
    elif not path.is_file():
        errors.append(f"{relative_path}: strict illustration crop is missing")
    elif png_size(path) != expected_size:
        errors.append(f"{relative_path}: unexpected crop size {png_size(path)}, expected {expected_size}")

if errors:
    print("\n".join(f"ERROR: {error}" for error in errors))
    sys.exit(1)

print(
    f"activity_titles={len(title_ids)} separate_headings=ok "
    f"illustrations={len(ACTIVITY_ILLUSTRATIONS)} descriptions=ok "
    f"strict_crops={len(STRICT_CROPS)} image_only=ok audio_links=ok"
)
