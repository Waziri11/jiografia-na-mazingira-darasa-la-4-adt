#!/usr/bin/env python3
"""Synchronize page-section-id metadata with content/pages.json."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
changed = 0
for position, page in enumerate(pages, 1):
    path = ROOT / page["href"]
    source = path.read_text(encoding="utf-8")
    revised, count = re.subn(
        r'(<meta\s+name="page-section-id"\s+content=")\d+("\s*/?>)',
        rf"\g<1>{position}\g<2>",
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"{path.name}: expected one page-section-id meta tag")
    if revised != source:
        path.write_text(revised, encoding="utf-8")
        changed += 1
print(f"updated {changed} page-section-id values")
