#!/usr/bin/env python3
"""Merge ADT fragments the validation report identifies as one source page."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

MERGES = {
    # destination: later fragments folded into the destination
    "pg012_sec001.html": ["pg012_sec002.html"],
    "pg025_sec002.html": ["pg025_sec003.html", "pg025_sec004.html"],
    "pg026_sec001.html": ["pg026_sec002.html"],
    "pg035_sec001.html": ["pg035_sec002.html", "pg035_sec003.html"],
    "pg039_sec001.html": ["pg039_sec002.html", "pg039_sec003.html", "pg039_sec004.html"],
}

SECTION_RE = re.compile(r"<section\b[\s\S]*?</section>", re.IGNORECASE)

for destination, sources in MERGES.items():
    destination_path = ROOT / destination
    html = destination_path.read_text(encoding="utf-8")
    marker = '<div class="relative z-50" id="interface-container"></div>'
    if marker not in html:
        raise RuntimeError(f"interface marker missing in {destination}")
    # Idempotency marker.
    if "validation-merged-sections" in html:
        continue
    sections = []
    for source in sources:
        source_html = (ROOT / source).read_text(encoding="utf-8")
        found = SECTION_RE.findall(source_html)
        if not found:
            raise RuntimeError(f"section missing in {source}")
        sections.extend(found)
    insertion = (
        '\n      <div class="validation-merged-sections mt-8 space-y-8" '
        'data-validation-merged="true">\n        '
        + "\n        ".join(sections)
        + "\n      </div>\n"
    )
    interface_at = html.index(marker)
    content_close = html.rfind("</div>", 0, interface_at)
    if content_close < 0:
        raise RuntimeError(f"content wrapper close missing in {destination}")
    html = html[:content_close] + insertion + html[content_close:]
    destination_path.write_text(html, encoding="utf-8")

# Remove merged fragments and report-confirmed blank pages from the reading spine.
manifest_path = ROOT / "content" / "pages.json"
pages = json.loads(manifest_path.read_text(encoding="utf-8"))
removed = {item for values in MERGES.values() for item in values}
removed.update({"pg023_sec002.html", "pg087_sec002.html", "pg088_sec002.html"})
pages = [page for page in pages if page.get("href") not in removed]
manifest_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep table-of-contents links on navigable merged destinations.
toc_path = ROOT / "content" / "toc.json"
toc = json.loads(toc_path.read_text(encoding="utf-8"))
destination_for = {source: destination for destination, sources in MERGES.items() for source in sources}
section_for = {page["href"]: page["section_id"] for page in pages}
revised_toc = []
seen_toc_targets = set()
for entry in toc:
    href = entry.get("href")
    if href in {"pg023_sec002.html", "pg087_sec002.html", "pg088_sec002.html"}:
        continue
    href = destination_for.get(href, href)
    if href in section_for:
        entry["href"] = href
        entry["section_id"] = section_for[href]
    target = (entry.get("section_id"), entry.get("href"))
    if target in seen_toc_targets:
        continue
    seen_toc_targets.add(target)
    revised_toc.append(entry)
toc_path.write_text(json.dumps(revised_toc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Navigation indexes are 1-based positions in the revised manifest.
for index, page in enumerate(pages, start=1):
    path = ROOT / page["href"]
    if not path.exists():
        raise RuntimeError(f"manifest target missing: {page['href']}")
    html = path.read_text(encoding="utf-8")
    html, count = re.subn(
        r'(<meta\s+name="page-section-id"\s+content=")[^"]+("\s*/?>)',
        rf"\g<1>{index}\2",
        html,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"page-section-id missing in {page['href']}")
    path.write_text(html, encoding="utf-8")

print(f"reading spine now contains {len(pages)} entries; removed {len(removed)} fragments")
