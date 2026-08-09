#!/usr/bin/env python3
"""Remove marked PDF watermark artifacts without touching page artwork."""

from pathlib import Path
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject


def remove_watermarks(source: Path, destination: Path) -> None:
    reader = PdfReader(source)
    writer = PdfWriter()

    for page in reader.pages:
        stream = ContentStream(page.get_contents(), reader)
        filtered = []
        skipped_depth = 0
        for operands, operator in stream.operations:
            if operator in (b"BDC", b"BMC"):
                if skipped_depth:
                    skipped_depth += 1
                    continue
                properties = operands[1] if operator == b"BDC" and len(operands) > 1 else None
                if isinstance(properties, dict) and properties.get("/Subtype") == "/Watermark":
                    skipped_depth = 1
                    continue
            elif operator == b"EMC" and skipped_depth:
                skipped_depth -= 1
                continue

            if not skipped_depth:
                filtered.append((operands, operator))

        stream.operations = filtered
        page[NameObject("/Contents")] = stream
        writer.add_page(page)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        writer.write(output)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"Usage: {sys.argv[0]} SOURCE DESTINATION")
    remove_watermarks(Path(sys.argv[1]), Path(sys.argv[2]))
