#!/usr/bin/env python3
"""Normalize multiple-choice option markers."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

LABEL_RE = re.compile(r'<label\b(?=[^>]*\bactivity-option\b)[\s\S]*?</label>', re.IGNORECASE)
CIRCLE_RE = re.compile(
    r'(<div\b[^>]*class="[^"]*(?:rounded-full|option-letter)[^"]*"[^>]*>)\s*([1-9])\s*(</div>)',
    re.IGNORECASE,
)
LETTERS = "abcdefghi"


def fix_label(match):
    label = match.group(0)
    circle = CIRCLE_RE.search(label)
    if not circle:
        return label
    letter = LETTERS[int(circle.group(2)) - 1]
    label = CIRCLE_RE.sub(lambda m: m.group(1) + letter + m.group(3), label, count=1)
    question = re.search(r'name="question-group-(\d+)"', label)
    if question:
        q = question.group(1)
        label = re.sub(
            r'aria-label="[^"]*"',
            f'aria-label="Swali la {q}, chaguo {letter}"',
            label,
            count=1,
        )
    return label


changed = 0
for path in sorted(ROOT.glob("pg*.html")):
    source = path.read_text(encoding="utf-8")
    updated = LABEL_RE.sub(fix_label, source)
    if updated != source:
        path.write_text(updated, encoding="utf-8")
        changed += 1

print(f"updated activity markers/duplicate figures in {changed} files")
