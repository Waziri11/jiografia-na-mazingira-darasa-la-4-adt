#!/usr/bin/env python3
"""Add deterministic audio mappings for every reader-facing non-empty text ID."""

from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]


def is_reader_text(key: str, value: str) -> bool:
    if not re.search(r"\w", value, flags=re.UNICODE):
        return False
    if "_ans_" in key or "_sec" in key:
        return False
    return key.startswith(("pg", "gl"))


def main() -> None:
    added_by_language: dict[str, list[str]] = {}
    for language in ("sw", "sw-TZ"):
        base = ROOT / "content" / "i18n" / language
        texts_path = base / "texts.json"
        audios_path = base / "audios.json"
        texts = json.loads(texts_path.read_text(encoding="utf-8"))
        audios = json.loads(audios_path.read_text(encoding="utf-8"))
        added = []
        for key, value in texts.items():
            if is_reader_text(key, value) and key not in audios:
                audios[key] = f"{key}.mp3"
                added.append(key)
        audios_path.write_text(
            json.dumps(audios, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        added_by_language[language] = added
    if added_by_language["sw"] != added_by_language["sw-TZ"]:
        raise SystemExit("language audio mappings diverged")
    print(f"added {len(added_by_language['sw'])} reader audio mappings per language")
    for key in added_by_language["sw"]:
        print(key)


if __name__ == "__main__":
    main()
