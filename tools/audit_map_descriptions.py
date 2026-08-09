#!/usr/bin/env python3
"""Verify that every substantive map has detailed, linked narration."""

from html.parser import HTMLParser
from pathlib import Path
import glob
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

# One narration ID per standalone map. Composite maps use one unified hidden
# narration ID instead of repeating descriptions for every visual segment.
MAP_IDS = [
    "pg009_im001", "pg010_im160", "pg011_n0009", "pg013_im001",
    "pg014_im001", "pg015_im007", "pg016_im039_seg001_v1",
    "pg016_im039_seg002_v1", "pg016_im039_seg003_v1",
    "pg016_im039_seg004_v1", "pg018_im001", "pg019_im037",
    "pg030_im113", "pg037_im003", "pg042_im018", "pg047_im129",
    "pg048_im087", "pg052_im003", "pg052_im004", "pg053_im003",
    "pg053_im004", "pg054_im003", "pg054_im004", "pg056_im003",
    "pg060_im030", "pg061_im038", "pg062_n0042", "pg067_im035",
    "pg070_im036", "pg075_im027", "pg077_im003", "pg077_im004",
    "pg078_im003", "pg079_im010_seg001_v1", "pg079_im010_seg002_v1",
    "pg080_im127", "pg081_im029", "pg083_im113", "pg085_im155",
    "pg095_im172",
]


class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.non_image_ids = set()

    def handle_starttag(self, tag, attrs):
        data_id = dict(attrs).get("data-id")
        if data_id and tag != "img":
            self.non_image_ids.add(data_id)


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main():
    texts = {lang: load(f"content/i18n/{lang}/texts.json") for lang in ("sw", "sw-TZ")}
    audios = {lang: load(f"content/i18n/{lang}/audios.json") for lang in ("sw", "sw-TZ")}
    parser = IdParser()
    for filename in glob.glob(str(ROOT / "pg*.html")):
        parser.feed(Path(filename).read_text(encoding="utf-8"))

    errors = []
    for data_id in MAP_IDS:
        sw_text = texts["sw"].get(data_id, "").strip()
        if len(sw_text) < 350:
            errors.append(f"{data_id}: description is only {len(sw_text)} characters")
        if texts["sw-TZ"].get(data_id) != texts["sw"].get(data_id):
            errors.append(f"{data_id}: sw and sw-TZ descriptions differ")
        if data_id not in parser.non_image_ids:
            errors.append(f"{data_id}: no non-image read-aloud hook in HTML")
        for lang in ("sw", "sw-TZ"):
            filename = audios[lang].get(data_id)
            if not filename:
                errors.append(f"{data_id}: missing {lang} audio mapping")
                continue
            audio_path = ROOT / f"content/i18n/{lang}/audio" / filename
            if not audio_path.exists() or audio_path.stat().st_size < 10_000:
                errors.append(f"{data_id}: missing or empty {lang} audio file {filename}")

    if errors:
        print("map narration audit failed")
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print(f"maps={len(MAP_IDS)} detailed_descriptions=ok audio_links=ok read_aloud_hooks=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
