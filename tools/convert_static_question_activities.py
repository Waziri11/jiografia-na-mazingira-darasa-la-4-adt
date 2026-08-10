#!/usr/bin/env python3
"""Convert known static question blocks to accessible open-answer activities."""

from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[1]

OPEN_QUESTIONS = {
    "pg008_sec001.html": ["pg008_n0003", "pg008_n0004"],
    "pg015_sec002.html": ["pg015_n0038", "pg015_n0040", "pg015_n0042"],
    "pg021_sec001.html": ["pg021_n0027", "pg021_n0028"],
    "pg024_sec001.html": ["pg024_n0012", "pg024_n0014"],
    "pg027_sec001.html": ["pg027_n0017", "pg027_n0019", "pg027_n0021"],
    "pg030_sec001.html": ["pg030_n0002", "pg030_n0003", "pg030_n0004"],
    "pg031_sec001.html": ["pg031_n0003", "pg031_n0004", "pg031_n0005", "pg031_n0006", "pg031_n0007"],
    "pg035_sec001.html": ["pg035_n0020", "pg035_n0021", "pg035_n0022", "pg035_n0023"],
    "pg038_sec001.html": ["pg038_n0004", "pg038_n0007", "pg038_n0010", "pg038_n0013"],
    "pg042_sec001.html": ["pg042_n0005", "pg042_n0006"],
    "pg048_sec001.html": ["pg048_n0005", "pg048_n0007"],
    "pg062_sec001.html": ["pg062_n0007", "pg062_n0009", "pg062_n0011", "pg062_n0013", "pg062_n0015"],
    "pg071_sec001.html": ["pg071_n0007", "pg071_n0009", "pg071_n0011"],
    "pg076_sec001.html": ["pg076_n0005", "pg076_n0007", "pg076_n0009"],
    "pg081_sec001.html": ["pg081_n0007", "pg081_n0010", "pg081_n0013", "pg081_n0016", "pg081_n0019"],
    "pg082_sec001.html": ["pg082_n0003", "pg082_n0004", "pg082_n0005"],
    "pg089_sec001.html": ["pg089_n0006", "pg089_n0014", "pg089_n0016", "pg089_n0018"],
}

BLOCKS = {"p", "li", "div", "article", "section"}


def insertion_block(node):
    current = node
    while current.getparent() is not None:
        if current.tag in BLOCKS and current.tag not in {"section", "article"}:
            return current
        current = current.getparent()
    return node


for filename, ids in OPEN_QUESTIONS.items():
    path = ROOT / filename
    document = html.fromstring(path.read_text(encoding="utf-8"))
    sections = document.xpath("//section[@data-section-type]")
    if sections:
        sections[0].set("data-section-type", "activity_open_ended_answer")
    for index, text_id in enumerate(ids, 1):
        matches = document.xpath(f'//*[@data-id="{text_id}"]')
        if not matches:
            raise RuntimeError(f"{filename}: missing {text_id}")
        block = insertion_block(matches[0])
        parent = block.getparent()
        next_node = block.getnext()
        if next_node is not None and next_node.tag == "textarea":
            continue
        textarea = html.Element("textarea")
        textarea.set("class", "mt-3 mb-5 min-h-24 w-full resize-y rounded-lg border border-gray-400 bg-white p-3 text-base")
        textarea.set("data-aria-id", f"aria-{path.stem}-{index}")
        textarea.set("aria-label", f"Jibu la swali la {index}")
        textarea.set("tabindex", "0")
        parent.insert(parent.index(block) + 1, textarea)
    rendered = "<!DOCTYPE html>\n" + html.tostring(document, encoding="unicode", method="html") + "\n"
    path.write_text(rendered, encoding="utf-8")

print(f"converted {len(OPEN_QUESTIONS)} static sections to open-answer activities")
