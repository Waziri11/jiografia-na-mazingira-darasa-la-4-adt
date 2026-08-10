#!/usr/bin/env python3
"""Place one read-aloud hook inside #content before every illustration ID."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
IMG = re.compile(r'<img\b[^>]*\bdata-id="(?P<id>[^"]+)"[^>]*>', re.I | re.S)


def remove_empty_hook(source: str, data_id: str) -> str:
    escaped = re.escape(data_id)
    pattern = re.compile(
        rf'<(?P<tag>span|p)\b'
        rf'(?=[^>]*\bclass="[^"]*\bsr-only\b[^"]*")'
        rf'(?=[^>]*\bdata-id="{escaped}")[^>]*>\s*</(?P=tag)>\s*',
        re.I | re.S,
    )
    return pattern.sub("", source)


def main() -> int:
    changed_files = 0
    inserted_hooks = 0
    for html_path in sorted(ROOT.glob("pg*.html")):
        source = html_path.read_text(encoding="utf-8")
        ids = list(dict.fromkeys(match.group("id") for match in IMG.finditer(source)))
        if not ids:
            continue

        updated = source
        for data_id in ids:
            updated = remove_empty_hook(updated, data_id)

        for data_id in ids:
            image = re.search(
                rf'<img\b(?=[^>]*\bdata-id="{re.escape(data_id)}")[^>]*>',
                updated,
                re.I | re.S,
            )
            if image is None:
                raise RuntimeError(f"{html_path.name}: image disappeared for {data_id}")
            hook = f'<span class="sr-only" data-id="{data_id}"></span>\n'
            updated = updated[: image.start()] + hook + updated[image.start() :]
            inserted_hooks += 1

        if updated != source:
            html_path.write_text(updated, encoding="utf-8")
            changed_files += 1

    print(f"files={changed_files} read_aloud_hooks={inserted_hooks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
