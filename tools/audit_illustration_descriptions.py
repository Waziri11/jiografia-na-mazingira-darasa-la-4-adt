#!/usr/bin/env python3
"""Audit description and audio coverage for every illustration in the ADT."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import glob
import hashlib
import json
import sys

from audit_map_descriptions import MAP_IDS


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("sw", "sw-TZ")
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

# These educational visuals need explanatory narration, not only a short label.
EXPLANATORY_VISUAL_IDS = {
    "pg027_im003",
    "pg013_im030",
    "pg044_im003", "pg044_im004", "pg044_im005", "pg044_im006",
    "pg044_im007", "pg044_im008",
    "pg063_im018", "pg068_im008", "pg069_im003",
    "pg071_im003", "pg072_im003", "pg073_im003",
    "pg074_im003", "pg074_im004", "pg074_im005_seg001_v1",
    "pg074_im005_seg002_v1", "pg078_im004",
}


class IllustrationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images: dict[str, list[tuple[str, str, str]]] = {}
        self.decorative: list[tuple[str, str, str, str]] = []
        self.content_depth = 0
        self.non_image_ids_in_content: set[str] = set()
        self.filename = ""

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if self.content_depth and tag not in VOID_TAGS:
            self.content_depth += 1
        elif tag == "div" and values.get("id") == "content":
            self.content_depth = 1

        data_id = values.get("data-id")
        if self.content_depth and data_id and tag != "img":
            self.non_image_ids_in_content.add(data_id)
        if tag != "img":
            return
        src = values.get("src", "")
        alt = values.get("alt", "")
        if data_id:
            self.images.setdefault(data_id, []).append((self.filename, src, alt))
        else:
            self.decorative.append(
                (self.filename, src, alt, values.get("aria-hidden", ""))
            )

    def handle_startendtag(self, tag, attrs):
        # HTMLParser otherwise calls handle_starttag and handle_endtag, which
        # would incorrectly change #content depth for void image elements.
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.content_depth:
            self.content_depth -= 1


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = IllustrationParser()
    for filename in sorted(glob.glob(str(ROOT / "pg*.html"))):
        parser.filename = Path(filename).name
        parser.feed(Path(filename).read_text(encoding="utf-8"))

    texts = {
        lang: load_json(f"content/i18n/{lang}/texts.json") for lang in LANGUAGES
    }
    audios = {
        lang: load_json(f"content/i18n/{lang}/audios.json") for lang in LANGUAGES
    }
    errors: list[str] = []

    for data_id, occurrences in sorted(parser.images.items()):
        description = texts["sw"].get(data_id, "").strip()
        if not description:
            errors.append(f"{data_id}: missing description")
        if texts["sw-TZ"].get(data_id) != texts["sw"].get(data_id):
            errors.append(f"{data_id}: sw and sw-TZ descriptions differ")
        if data_id not in parser.non_image_ids_in_content:
            errors.append(f"{data_id}: no read-aloud hook inside #content")
        if data_id in MAP_IDS and len(description) < 350:
            errors.append(f"{data_id}: map description is only {len(description)} characters")
        if data_id in EXPLANATORY_VISUAL_IDS and len(description) < 180:
            errors.append(
                f"{data_id}: educational visual description is only {len(description)} characters"
            )

        for html_file, src, alt in occurrences:
            if not src or not (ROOT / src).exists():
                errors.append(f"{html_file}: missing image source for {data_id}: {src}")
            if not alt.strip():
                errors.append(f"{html_file}: empty alt text for {data_id}")

        language_files = []
        for lang in LANGUAGES:
            filename = audios[lang].get(data_id)
            if not filename:
                errors.append(f"{data_id}: missing {lang} audio mapping")
                continue
            audio_path = ROOT / "content" / "i18n" / lang / "audio" / filename
            if not audio_path.exists() or audio_path.stat().st_size < 1_000:
                errors.append(f"{data_id}: missing or empty {lang} audio file {filename}")
                continue
            language_files.append(audio_path)
        if len(language_files) == 2 and digest(language_files[0]) != digest(language_files[1]):
            errors.append(f"{data_id}: sw and sw-TZ audio files differ")

    # Page 27 uses an inline SVG rather than an <img>; it still needs one
    # unified spatial description in addition to its four visible labels.
    inline_svg_id = "pg027_im003"
    inline_description = texts["sw"].get(inline_svg_id, "").strip()
    if len(inline_description) < 180:
        errors.append(
            f"{inline_svg_id}: inline direction diagram description is only "
            f"{len(inline_description)} characters"
        )
    page_27 = (ROOT / "pg027_sec001.html").read_text(encoding="utf-8")
    if f'data-id="{inline_svg_id}"' not in page_27:
        errors.append(f"{inline_svg_id}: missing read-aloud hook for inline SVG")
    for lang in LANGUAGES:
        if texts[lang].get(inline_svg_id) != texts["sw"].get(inline_svg_id):
            errors.append(f"{inline_svg_id}: {lang} inline SVG description differs")
        filename = audios[lang].get(inline_svg_id)
        audio_path = ROOT / "content" / "i18n" / lang / "audio" / (filename or "")
        if not filename or not audio_path.exists() or audio_path.stat().st_size < 1_000:
            errors.append(f"{inline_svg_id}: missing {lang} inline SVG audio")

    for html_file, src, alt, aria_hidden in parser.decorative:
        if alt.strip() or aria_hidden.lower() != "true":
            errors.append(
                f"{html_file}: image without data-id must be explicitly decorative: {src}"
            )

    if errors:
        print("illustration description audit failed")
        for error in errors:
            print(f"ERROR {error}")
        return 1

    print(
        f"illustrations={len(parser.images) + 1} decorative={len(parser.decorative)} "
        f"descriptions=ok audio_links=ok audio_files=ok languages_synchronized=ok"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
