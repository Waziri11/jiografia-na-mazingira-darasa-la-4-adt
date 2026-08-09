#!/usr/bin/env python3
"""Extract every Word-table row from the ADT validation report."""

from pathlib import Path
import json
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def text(node):
    parts = []
    for item in node.iter():
        if item.tag == f"{{{NS['w']}}}t" and item.text:
            parts.append(item.text)
        elif item.tag in {f"{{{NS['w']}}}br", f"{{{NS['w']}}}cr"}:
            parts.append("\n")
        elif item.tag == f"{{{NS['w']}}}tab":
            parts.append("\t")
    return "".join(parts).strip()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_validation_matrix.py REPORT.docx OUTPUT.json")
    report, output = map(Path, sys.argv[1:])
    with zipfile.ZipFile(report) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    rows = []
    for table_index, table in enumerate(root.findall(".//w:tbl", NS)):
        for row_index, row in enumerate(table.findall("./w:tr", NS)):
            cells = [text(cell) for cell in row.findall("./w:tc", NS)]
            rows.append({"table": table_index, "row": row_index, "cells": cells})
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"extracted {len(rows)} rows from {len(root.findall('.//w:tbl', NS))} tables")


if __name__ == "__main__":
    main()
