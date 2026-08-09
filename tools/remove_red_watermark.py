#!/usr/bin/env python3
"""Remove the translucent red print watermark from a book image asset."""

from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageFilter


def remove_watermark(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGB")
    pixels = np.asarray(image, dtype=np.float32)
    red, green, blue = np.moveaxis(pixels, 2, 0)

    # The source watermark is pure red composited at roughly 25% opacity.
    # Estimate each pixel's unwatermarked red/cyan relationship from a local
    # median. This accommodates white, beige, blue, green, and gray artwork:
    # genuine colours persist across the window, while letter strokes are
    # local positive red deviations.
    cyan = (green + blue) / 2.0
    red_excess = red - cyan
    encoded_excess = np.clip((red_excess + 255.0) / 2.0, 0, 255).astype(np.uint8)
    local_excess = np.asarray(
        Image.fromarray(encoded_excess).filter(ImageFilter.MedianFilter(101)),
        dtype=np.float32,
    ) * 2.0 - 255.0
    alpha = np.clip(
        (red_excess - local_excess) / np.maximum(255.0 - local_excess, 1.0),
        0.0,
        0.27,
    )
    red_seed = alpha > 0.035
    footprint = Image.fromarray((red_seed * 255).astype(np.uint8)).filter(
        ImageFilter.MaxFilter(9)
    )
    footprint = np.asarray(footprint, dtype=bool)
    alpha = np.where((alpha > 0.004) & footprint, alpha, 0.0)

    denominator = np.maximum(1.0 - alpha, 0.01)
    restored = pixels.copy()
    restored[..., 0] = (red - 255.0 * alpha) / denominator
    restored[..., 1] = green / denominator
    restored[..., 2] = blue / denominator

    result = np.where((alpha > 0)[..., None], restored, pixels)
    result = np.clip(result, 0, 255).astype(np.uint8)
    Image.fromarray(result, "RGB").save(destination, quality=95, subsampling=0)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"Usage: {sys.argv[0]} SOURCE DESTINATION")
    remove_watermark(Path(sys.argv[1]), Path(sys.argv[2]))
