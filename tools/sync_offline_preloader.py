#!/usr/bin/env python3
"""Synchronize JSON embedded in the offline fetch preloader with bundle files."""

from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "assets/offline-preloader.js"
source = path.read_text(encoding="utf-8")
prefix = "  var INLINE = "
suffix = ";\n  var BASE_DIR = "
start = source.index(prefix) + len(prefix)
end = source.index(suffix, start)
inline = json.loads(source[start:end])

updated = 0
for key in list(inline):
    relative = key[2:] if key.startswith("./") else key
    local = ROOT / relative
    if local.is_file() and local.suffix == ".json":
        inline[key] = json.loads(local.read_text(encoding="utf-8"))
        updated += 1
    elif local.is_file() and local.suffix == ".html":
        inline[key] = local.read_text(encoding="utf-8")
        updated += 1

# Keep every current reading-order page available when the bundle is opened
# directly from disk, including newly restored front-matter pages.
pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
for page in pages:
    relative = page["href"]
    local = ROOT / relative
    if local.is_file():
        inline[f"./{relative}"] = local.read_text(encoding="utf-8")
        updated += 1

payload = json.dumps(inline, ensure_ascii=False, separators=(",", ":"))
path.write_text(source[:start] + payload + source[end:], encoding="utf-8")
digest = hashlib.sha256(path.read_bytes()).hexdigest()
for html_path in list(ROOT.glob("*.html")):
    html = html_path.read_text(encoding="utf-8")
    revised = re.sub(r"offline-preloader\.js(?:\?v=[^\"']+)?", f"offline-preloader.js?v={digest[:12]}", html)
    if revised != html:
        html_path.write_text(revised, encoding="utf-8")
(ROOT / ".build-hash").write_text(digest + "\n", encoding="utf-8")
print(f"synchronized {updated} embedded JSON resources")
