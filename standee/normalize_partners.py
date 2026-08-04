#!/usr/bin/env python3
"""Optically normalize the partner logos so a logo wall reads evenly.

The source logos are all 480x200 canvases, but the artwork inside them varies
enormously: Viettel fills 391px of width, VietSpark only 127px. Scaling them all
to same box height therefore renders them all the same HEIGHT while the narrow
marks carry a fraction of the visual weight, which is what makes a logo row look
sloppy and half-finished.

Equal height is the wrong invariant. This normalizes on the geometric mean of
the trimmed artwork, sqrt(w*h), so a tall narrow mark and a long wordmark end up
carrying the same optical weight, then centres each on one uniform canvas. After
this the layout CSS can be dumb: every cell is the same size and every logo is
already correct inside it.

Idempotent - it always rebuilds from assets/partners/ and never reads its own
output.

    uv run --project <repo root> python normalize_partners.py
"""

from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageChops

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "assets" / "partners"
OUT = HERE / "assets" / "partners-norm"

CANVAS = (600, 300)  # uniform output canvas, aspect 2.0
# Target sqrt(w*h) in px. Ceiling is set by the tallest mark, VietSpark at
# aspect 0.80: it renders 250/sqrt(0.80) = 279px tall, which still clears the
# 300px canvas. Raising this past ~260 clips it.
TARGET_GM = 250
ALPHA_FLOOR = 12     # ignore near-invisible antialiasing when finding content


def content_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    """Bounding box of real artwork, ignoring transparent AND white padding."""
    flat = Image.new("RGB", im.size, "white")
    flat.paste(im, mask=im.split()[3])
    diff = ImageChops.difference(flat, Image.new("RGB", im.size, "white")).convert("L")
    return diff.point(lambda p: 255 if p > ALPHA_FLOOR else 0).getbbox()


def normalize(path: pathlib.Path) -> tuple[str, int, int]:
    im = Image.open(path).convert("RGBA")
    box = content_bbox(im)
    if box is None:
        raise ValueError(f"{path.name}: no visible content")
    art = im.crop(box)
    w, h = art.size

    # Equal optical weight: hold sqrt(w*h) constant across every logo.
    scale = TARGET_GM / (w * h) ** 0.5
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    if nw > CANVAS[0] or nh > CANVAS[1]:
        # Never let a wide wordmark or a tall emblem blow past the canvas.
        fit = min(CANVAS[0] / nw, CANVAS[1] / nh)
        nw, nh = max(1, int(nw * fit)), max(1, int(nh * fit))

    art = art.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(art, ((CANVAS[0] - nw) // 2, (CANVAS[1] - nh) // 2), art)
    out = OUT / (path.stem + ".png")
    canvas.save(out)
    return out.name, nw, nh


if __name__ == "__main__":
    if not SRC.is_dir():
        sys.exit(f"missing source dir: {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SRC.iterdir() if p.suffix.lower() in {".png", ".webp"})
    if not files:
        sys.exit(f"no logos found in {SRC}")
    gms = []
    for f in files:
        name, w, h = normalize(f)
        gms.append((w * h) ** 0.5)
        print(f"{name:34} -> content {w:3}x{h:3}  gm {(w*h)**0.5:5.1f}")
    spread = max(gms) - min(gms)
    print(f"\n{len(files)} logos, optical-weight spread {spread:.1f}px (lower is better)")
    assert spread < 25, f"normalization failed: weights still vary by {spread:.1f}px"
    print("optical weights are even")
