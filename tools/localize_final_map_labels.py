#!/usr/bin/env python3
"""Localize the English source/author panel and remove the baked duplicate caption."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "images" / "pg095_im172.png"
image = Image.open(path).convert("RGB")
draw = ImageDraw.Draw(image)

font_candidates = [
    ROOT / "assets" / "fonts" / "AtkinsonHyperlegible-Regular.ttf",
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
]
font_path = next((candidate for candidate in font_candidates if candidate.exists()), None)
font = ImageFont.truetype(str(font_path), 16) if font_path else ImageFont.load_default()

# The printed map includes an English metadata panel at lower right.
draw.rectangle((543, 876, 790, 997), fill="white", outline="#555555", width=2)
lines = [
    "Chanzo: Ofisi ya Takwimu",
    "Tanzania (2019)",
    "Mwandishi: Taasisi ya Elimu",
    "Tanzania (TET)",
]
y = 891
for line in lines:
    box = draw.textbbox((0, 0), line, font=font)
    width = box[2] - box[0]
    draw.text((666 - width / 2, y), line, font=font, fill="black")
    y += 22

# Remove the baked caption; the semantic HTML figcaption remains the single caption.
draw.rectangle((0, 1080, image.width, image.height), fill="white")
image.save(path, optimize=True)
