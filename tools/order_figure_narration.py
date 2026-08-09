#!/usr/bin/env python3
"""Announce figure captions before image descriptions without moving visible captions.

The reader follows data-id order.  A visually hidden copy of each figure title is
placed before its image/group, while the visible caption remains beneath the
figure without a second narration hook.
"""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
TEXTS = json.loads((ROOT / "content/i18n/sw/texts.json").read_text(encoding="utf-8"))

# Pages whose validation comments explicitly require title-first figure audio.
PAGES = {
    9, 10, 11, 15, 16, 30, 31, 34, 37, 41, 43, 44, 47, 48, 51, 52, 53,
    54, 55, 60, 61, 64, 65, 67, 68, 70, 75, 76, 77, 78, 79, 80, 81, 83,
    85, 95,
}

TAG_WITH_ID = re.compile(r'<(?P<tag>[a-z][^>]*?)\bdata-id="(?P<id>[^"]+)"[^>]*>', re.I)
IMG_TAG = re.compile(r'<img\b[^>]*\bdata-id="(?P<id>[^"]+)"[^>]*>', re.I)
HTML_TAG = re.compile(r'<\s*(?P<close>/?)\s*(?P<name>[a-z0-9]+)\b[^>]*>', re.I)
VOID_TAGS = {"area", "base", "br", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
MISSING_CAPTIONS = {
    "pg085_sec001.html": ("pg085_im155", "pg085_n0081"),
    "pg095_sec001.html": ("pg095_im172", "pg095_n0074"),
}


def is_figure_title(value: str) -> bool:
    return bool(re.match(r"\s*Kielelezo\s+namba\.?\s*\d+", value, re.I))


def visible_caption_positions(source: str, title_id: str):
    """Return caption-text positions, excluding matches inside HTML tags/attributes."""
    value = TEXTS.get(title_id, "")
    number = re.search(r"Kielelezo\s+namba\.?\s*(\d+)", value, re.I)
    if not number:
        return []
    pattern = re.compile(rf"Kielelezo\s+namba\.?\s*{number.group(1)}\s*:", re.I)
    positions = []
    for match in pattern.finditer(source):
        if source.rfind("<", 0, match.start()) < source.rfind(">", 0, match.start()):
            positions.append(match.start())
    return positions


def caption_container(source: str, position: int):
    """Find the smallest safe visible-caption container surrounding position."""
    stack = []
    for match in HTML_TAG.finditer(source, 0, position):
        name = match.group("name").lower()
        if match.group("close"):
            for index in range(len(stack) - 1, -1, -1):
                if stack[index][0] == name:
                    stack = stack[:index]
                    break
        elif name not in VOID_TAGS and not match.group(0).rstrip().endswith("/>"):
            stack.append((name, match.start(), match.end(), match.group(0)))
    chosen = next((item for item in reversed(stack) if item[0] in {"figcaption", "p"}), None)
    if not chosen:
        chosen = next(
            (item for item in reversed(stack) if item[0] == "div" and
             re.search(r"text-center|italic|caption|font-", item[3], re.I)),
            None,
        )
    if not chosen:
        chosen = next((item for item in reversed(stack) if item[0] == "span"), None)
    if not chosen:
        return None
    name, start, open_end, _tag = chosen
    depth = 0
    close_end = None
    for match in HTML_TAG.finditer(source, start):
        if match.group("name").lower() != name:
            continue
        if not match.group("close"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                close_end = match.end()
                break
    return (start, open_end, close_end) if close_end else None


changed = 0
ordered = 0
for page in sorted(PAGES):
    for path in sorted(ROOT.glob(f"pg{page:03d}_sec*.html")):
        source = path.read_text(encoding="utf-8")
        original = source
        seed = MISSING_CAPTIONS.get(path.name)
        if seed and seed[1] not in source:
            image_id, title_id = seed
            image = re.search(r'<img\b[^>]*\bdata-id="' + re.escape(image_id) + r'"[^>]*>', source, re.I)
            if image:
                title = TEXTS[title_id]
                addition = (f'<span class="sr-only" data-id="{title_id}"></span>\n' + image.group(0) +
                            f'\n<figcaption class="mt-3 text-center italic" aria-hidden="true">{title}</figcaption>')
                source = source[:image.start()] + addition + source[image.end():]
        moved_ids = re.findall(r'<span class="sr-only" data-id="([^"]+)"></span>', source)
        if not moved_ids:
            moved_ids = [
                match.group("id") for match in TAG_WITH_ID.finditer(source)
                if is_figure_title(TEXTS.get(match.group("id"), ""))
            ]
        # Remove prior generated markers so reruns can repair their exact anchor.
        updated = re.sub(r'<span class="sr-only" data-id="(?:' +
                         "|".join(re.escape(item) for item in moved_ids) +
                         r')"></span>\s*', "", source) if moved_ids else source

        captions = []
        for title_id in moved_ids:
            positions = visible_caption_positions(updated, title_id)
            if positions:
                captions.append((positions[-1], title_id))
        captions.sort()

        insertions = []
        previous_caption = 0
        for caption_pos, title_id in captions:
            images = list(IMG_TAG.finditer(updated, previous_caption, caption_pos))
            previous_caption = caption_pos
            if not images:
                continue
            seeded_image = next(
                (image_id for _name, (image_id, seeded_title) in MISSING_CAPTIONS.items()
                 if seeded_title == title_id),
                None,
            )
            ids = [match.group("id") for match in images]
            repeated = {item for item in ids if ids.count(item) > 1}
            anchor = next((m for m in images if m.group("id") == seeded_image), None)
            if not anchor:
                anchor = next((m for m in reversed(images) if m.group("id") in repeated), images[0])
            insertions.append((anchor.start(), title_id))
        for anchor_start, title_id in reversed(insertions):
            updated = (updated[:anchor_start] +
                       f'<span class="sr-only" data-id="{title_id}"></span>\n' +
                       updated[anchor_start:])
            ordered += 1

        # Hide the visual duplicate from assistive technology and remove all
        # narration hooks in that caption; the visible styling/text is unchanged.
        blocks = []
        for _caption_pos, title_id in captions:
            positions = visible_caption_positions(updated, title_id)
            if positions:
                block = caption_container(updated, positions[-1])
                if block:
                    blocks.append(block)
        for start, open_end, close_end in sorted(set(blocks), reverse=True):
            block = updated[start:close_end]
            open_tag = updated[start:open_end]
            if 'aria-hidden=' not in open_tag:
                open_tag = open_tag[:-1] + ' aria-hidden="true">'
            block = open_tag + block[open_end - start:]
            block = re.sub(r'\s*data-id="[^"]+"', "", block)
            updated = updated[:start] + block + updated[close_end:]

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

print(f"ordered {ordered} figure narrations in {changed} files")
