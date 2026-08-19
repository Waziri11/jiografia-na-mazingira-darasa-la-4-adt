#!/usr/bin/env python3
"""Structural and accessibility audit for the remediated ADT bundle."""

from pathlib import Path
from collections import Counter
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
warnings = []

pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
hrefs = [p["href"] for p in pages]
section_ids = [p["section_id"] for p in pages]
for label, values in (("href", hrefs), ("section_id", section_ids)):
    duplicates = [value for value, count in Counter(values).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate manifest {label}: {duplicates}")

catalogs = {}
audios = {}
for language in ("sw", "sw-TZ"):
    catalogs[language] = json.loads((ROOT / f"content/i18n/{language}/texts.json").read_text(encoding="utf-8"))
    audios[language] = json.loads((ROOT / f"content/i18n/{language}/audios.json").read_text(encoding="utf-8"))

if set(catalogs["sw"]) != set(catalogs["sw-TZ"]):
    errors.append("text catalog keys differ between sw and sw-TZ")
if set(audios["sw"]) != set(audios["sw-TZ"]):
    errors.append("audio mapping keys differ between sw and sw-TZ")

for language in ("sw", "sw-TZ"):
    for data_id, value in catalogs[language].items():
        if (re.search(r"\w", value, flags=re.UNICODE)
                and "_ans_" not in data_id and "_sec" not in data_id
                and data_id not in audios[language]):
            errors.append(f"{language}: non-empty text has no audio mapping: {data_id}")

seen_data_ids = Counter()
for index, page in enumerate(pages, start=1):
    path = ROOT / page["href"]
    if not path.is_file():
        errors.append(f"missing page: {page['href']}")
        continue
    html = path.read_text(encoding="utf-8")
    title = re.search(r'<meta\s+name="title-id"\s+content="([^"]+)"', html)
    position = re.search(r'<meta\s+name="page-section-id"\s+content="([^"]+)"', html)
    if not title or title.group(1) != page["section_id"]:
        errors.append(f"title-id mismatch: {page['href']}")
    if not position or position.group(1) != str(index):
        errors.append(f"page-section-id mismatch: {page['href']} expected {index}")
    if "FOR ONLINE READING ONLY" in html.upper() or "FOR ONLINE USE ONLY" in html.upper():
        errors.append(f"printer-only phrase remains: {page['href']}")

    for data_id in re.findall(r'\bdata-id="([^"]+)"', html):
        seen_data_ids[data_id] += 1
        for language in ("sw", "sw-TZ"):
            if data_id not in catalogs[language]:
                errors.append(f"{page['href']}: {data_id} missing from {language} texts")
            elif (re.search(r"\w", catalogs[language][data_id], flags=re.UNICODE)
                  and data_id not in audios[language]):
                errors.append(f"{page['href']}: {data_id} missing from {language} audios")

    for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', html, flags=re.I):
        source_path = src.split("?", 1)[0].split("#", 1)[0]
        if not (ROOT / source_path).is_file():
            errors.append(f"{page['href']}: missing image {src}")

for language in ("sw", "sw-TZ"):
    audio_dir = ROOT / f"content/i18n/{language}/audio"
    for key, filename in audios[language].items():
        if (re.search(r"\w", catalogs[language].get(key, ""), flags=re.UNICODE)
                and not (audio_dir / filename).is_file()):
            errors.append(f"{language}: missing audio file for {key}: {filename}")

# Validation-report regression checks.
forbidden_terms = ("kutafanua", "zinazowezesha kuwasilishwa", "inavyoonekana", "inavvoonekana",
                  "kuonesha", "kuonyesha", "huonesha", "huonyesha", "inaonesha", "inaonyesha",
                  "kinaonesha", "zinaonesha", "FOR ONLINE")
for forbidden in forbidden_terms:
    for language in ("sw", "sw-TZ"):
        matches = [key for key, value in catalogs[language].items() if forbidden.casefold() in value.casefold()]
        if matches:
            errors.append(f"{language}: forbidden report term {forbidden!r} remains in {len(matches)} entries")

for language in ("sw", "sw-TZ"):
    glossary = json.loads((ROOT / f"content/i18n/{language}/glossary.json").read_text(encoding="utf-8"))
    glossary_blob = json.dumps(glossary, ensure_ascii=False).casefold()
    for forbidden in forbidden_terms:
        if forbidden.casefold() in glossary_blob:
            errors.append(f"{language}: forbidden report term {forbidden!r} remains in glossary")
    for entry in glossary.values():
        word = entry.get("word", "")
        matching_ids = [key for key, value in catalogs[language].items()
                        if key.startswith("gl") and not key.endswith("_def") and value.casefold() == word.casefold()]
        if matching_ids and entry.get("definition", "") != catalogs[language].get(f"{matching_ids[0]}_def", ""):
            errors.append(f"{language}: glossary/text definition mismatch for {word!r}")

required_html = {
    "pg023_sec001.html": ('id="section-b-23"',),
    "pg036_sec001.html": ('data-id="pg036_n0001"',),
    "pg036_sec002.html": ('data-id="pg036_n0047"', 'data-id="pg036_n0049"', 'data-id="pg036_n0051"'),
    "pg087_sec001.html": ('data-id="pg087_n0006"', 'data-id="pg087_n0014"'),
    "pg088_sec002.html": ('id="section-b-88"',),
}
for filename, needles in required_html.items():
    text = (ROOT / filename).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            errors.append(f"{filename}: required remediation missing: {needle}")

print(f"pages={len(pages)} data_ids={sum(seen_data_ids.values())} errors={len(errors)} warnings={len(warnings)}")
for issue in errors[:200]:
    print("ERROR", issue)
if len(errors) > 200:
    print(f"ERROR ... {len(errors) - 200} more")
for issue in warnings:
    print("WARN", issue)
sys.exit(1 if errors else 0)
