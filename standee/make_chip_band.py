#!/usr/bin/env python3
"""Bake the standee C chip band into one opaque raster with its fade in the pixels.

Variation C used to place ``assets/chip.svg`` and feather it into the navy field
with a stacked ``linear-gradient`` overlay carrying alpha. That renders correctly
in the browser AND in pypdfium2, so it survived review twice - but Chrome emits a
varying-alpha gradient as a PDF **soft mask**, and any viewer that ignores soft
masks drops the overlay entirely and shows the raw artwork with a hard horizontal
seam across the banner. Flat ``rgba()`` fills are safe (constant alpha becomes a
plain ExtGState), which is why the glass cards render fine and only this one broke.

There is no vector way out: feathering a raster into a background inherently needs
transparency somewhere. So the fade is composited here instead, against the exact
field colour the band sits on, and the deliverable ships an opaque JPEG that every
renderer draws identically.

Two steps, both needed because the source is a Figma SVG with filters and a
``foreignObject`` backdrop-filter that only a browser resolves correctly:

    1. Chrome headless rasterises chip.svg at 3x.
    2. Pillow cover-crops it to the band's aspect and composites the vignette.

Run from the REPO ROOT, not this folder: Pillow is a dependency of the working
repo's env, not the visual-generation plugin's.

    uv run python visual-generation/standee/make_chip_band.py
    uv run python visual-generation/standee/make_chip_band.py --self-test

Re-run only when chip.svg, the band's inch dimensions, or FIELD change.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

# At 300 DPI the intermediate rasterisation is 10800px square = 117MP, over
# Pillow's 89MP decompression-bomb guard. That guard is there to stop a hostile
# file; this one is written by Chrome three lines earlier from a source in this
# repo, so raise the ceiling rather than let the build print a scary warning.
Image.MAX_IMAGE_PIXELS = 200_000_000

HERE = Path(__file__).resolve().parent
SRC = HERE / "assets/chip.svg"
SRC_PX = 1200  # chip.svg's own declared width/height

# Width is shared: both standee formats are authored 36in wide (the 80x200 is the
# same coordinate system scaled by CSS zoom), so one raster serves both and the
# band is always cover-cropped by width. FIELD must match the banner's held bottom
# gradient stop. A mismatch there is a seam that no amount of feathering hides,
# because the fade would be resolving to the wrong colour.
BAND_W_IN = 36.0
FIELD = (0x00, 0x0B, 0x2A)  # #000B2A

# One entry per band the folder ships: (output file, height in authoring inches,
# object-position-y). Both are cropped from the SAME rasterisation, so adding a
# height costs a crop and an encode, not another Chrome run.
#
# The band shows only part of a square source's height, so which part is a real
# choice. It is aimed at the TOP: the chip package's apex sits at 25% of the
# source and the operator wants it visible. At 0.284 the 19.2in crop opens at
# 13.3%, putting the apex 22% down the band. An earlier 0.47 opened at 27.3% and
# sliced the corner clean off, which is what made the band read as an anonymous
# glow.
#
# Raising the band is the ONLY way to move the chip up the banner while keeping
# its corner: opening the crop higher in the source just adds empty field above
# the apex and pushes the chip further down the band. That is exactly why the
# 80x200 has its own 24in band rather than reusing the 19.2in one at a higher
# `top` - a band must reach the bottom edge, so "move the chip up" means "grow the
# band". Height and OBJECT_POSITION_Y are coupled and the self-test is what tells
# you the apex has drifted out of range; 0.284 happens to hold for both heights.
BANDS = (
    ("chip-band-baked.jpg", 19.2, 0.284),       # 36 x 72in master
    ("chip-band-baked-24in.jpg", 24.0, 0.284),  # 80 x 200cm, authored 36 x 90in
)

# HARD CEILING on how large Chrome will rasterise this SVG faithfully, and the
# most important constant in this file. Past ~3600px it SILENTLY drops the Figma
# background mask partway down the image, exposing the artwork's white base rect -
# a flat chip on a white block where a glowing chip on navy belongs. Measured with
# a probe that samples the band's own crop window: scale 3 is faithful, scale 4
# and up are not. This shipped once as a white-backgrounded print master, so treat
# it as a measured limit, not a guess, and re-measure if chip.svg is replaced.
#
# Two failed attempts, recorded so they are not retried blind:
#   - Sampling only the raster's top-left corner cleared scales 4 and 5. The mask
#     renders for the top slice and fails below it, so the corner is correct navy
#     while the middle is white. Any check MUST sample the crop window.
#   - Deleting the mask attribute lifts the ceiling to 10800px and beyond, but
#     shifts the background colour: the masked group is an isolated stacking
#     context, so removing it changes what the inner foreignObject
#     backdrop-filter blurs. Measured 38/255 off on the original white base, 9/255
#     with a hand-tuned base fill. Not worth shipping altered vendor artwork,
#     colour-matched by eye, for a decorative band.
MAX_SCALE = 3
FAITHFUL_DPI = int(SRC_PX * MAX_SCALE / BAND_W_IN)  # 100 - real detail available
SCALE = MAX_SCALE

# 150 DPI output from that 100 DPI of real detail: a deliberate, bounded 1.5x
# LANCZOS upscale. Legitimate here specifically because the source is smooth
# vector art - flat fills and gradients, no fine texture - where resampling is
# perceptually free, and it hands the press more pixels than it needs rather than
# leaving it to do its own coarser upscale. 150 DPI is also standard for
# large-format banners read from several feet.
#
# What is NOT legitimate is silent or unbounded upscaling: an earlier revision
# paired a fixed scale of 3 with DPI 200 and then 300, quietly stretching 2x and
# 3x while reporting the nominal DPI. MAX_UPSCALE below makes that a build error.
#
# This is the only raster in the deliverable - type, logo, QR and the chart are all
# vector and resolution-independent - and Chrome's print path embeds a JPEG BYTE
# FOR BYTE (verified: /DCTDecode with /Length equal to the file size), so what is
# written here is exactly what the vendor receives. Feeding a PNG instead would
# only invite Chrome to re-encode it.
DPI = 150
QUALITY = 98
MAX_UPSCALE = 1.6

# Fade depth per edge, as a fraction of the band.
#   top    0.26 runs PAST the apex on purpose, so the corner emerges out of the
#          blend at ~85% strength rather than appearing at full strength the
#          instant the fade ends. The band top was raised to 54.2in to buy the
#          room for it, which puts its first inch behind the explainer - harmless,
#          because at that depth the fade keeps under a fifth of an already
#          near-black part of the artwork. Keep the apex in the fade's last sixth:
#          deeper and the corner washes out, shallower and the artwork starts with
#          a visible edge.
#   bottom shallow on purpose: the band's last inches sit inside the roller
#          cassette, so a deep fade there only costs die that is still visible.
#   sides  0.13 clears the die's left and right corners at this crop.
FADE = {"top": 0.26, "bottom": 0.10, "left": 0.13, "right": 0.13}

CHROMES = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


def find_chrome(override: str | None) -> Path:
    if override:
        p = Path(override)
        if not p.is_file():
            sys.exit(f"no chrome at {p}")
        return p
    for p in CHROMES:
        if p.is_file():
            return p
    sys.exit("Chrome not found; pass --chrome PATH")


def rasterize(chrome: Path, svg: Path, scale: int = SCALE) -> Image.Image:
    """Screenshot the SVG through Chrome, which is the only thing that resolves
    its filters and foreignObject backdrop-filter faithfully.

    At the default scale the intermediate is SRC_PX*SCALE square, which at 300 DPI
    is 10800px (~350MB in memory). That is the cost of not upscaling."""
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / "chip.png"
        subprocess.run(
            [
                str(chrome), "--headless=new", "--disable-gpu",
                f"--user-data-dir={Path(td) / 'profile'}",
                "--window-size=1200,1200",
                f"--force-device-scale-factor={scale}",
                f"--screenshot={png}",
                "--virtual-time-budget=8000",
                svg.resolve().as_uri(),
            ],
            capture_output=True,
            check=False,
        )
        if not png.is_file():
            sys.exit("Chrome wrote no screenshot; try --chrome PATH")
        return Image.open(png).convert("RGB").copy()


def ramp(size: tuple[int, int], depth: float, edge: str) -> Image.Image:
    """A keep-mask that is 0 at `edge` and 255 once `depth` of the way in.

    The strip is built at the output's own length along its axis, so the resize
    only stretches the *other* axis and NEAREST replicates it exactly. Building a
    fixed-length strip and resampling it instead leaves the edge row at ~3/255
    rather than 0, i.e. a faint band of un-faded artwork right on the seam.
    """
    w, h = size
    vertical = edge in ("top", "bottom")
    n = h if vertical else w
    span = max(1, round(n * depth))
    vals = [min(255, round(255 * i / span)) for i in range(n)]
    if edge in ("bottom", "right"):
        vals.reverse()
    strip = Image.new("L", (1, n) if vertical else (n, 1))
    strip.putdata(vals)
    return strip.resize((w, h), Image.Resampling.NEAREST)


def vignette(img: Image.Image) -> Image.Image:
    """Composite `img` onto FIELD, fading out at all four edges.

    Multiplying the four keep-masks reproduces what the four stacked CSS
    gradients did: keep = product of (1 - alpha_i), so corners fade twice.
    """
    keep = ramp(img.size, FADE["top"], "top")
    for edge in ("bottom", "left", "right"):
        keep = ImageChops.multiply(keep, ramp(img.size, FADE[edge], edge))
    return Image.composite(img, Image.new("RGB", img.size, FIELD), keep)


def cover_crop(img: Image.Image, band_h_in: float, opy: float) -> Image.Image:
    """`object-fit:cover` + `object-position:50% <opy>` on a square source: scale
    is set by the wider axis, so we keep the full width and take a horizontal
    slice of the height."""
    w, h = img.size
    keep_h = round(h * (band_h_in / BAND_W_IN) * (w / h))
    top = round((h - keep_h) * opy)
    return img.crop((0, top, w, top + keep_h))


def assert_faithful(cropped: Image.Image) -> None:
    """Fail the build if Chrome dropped the SVG's mask or filter groups.

    That failure is silent - no error, no warning, just a plausible-looking image -
    and it reached a print master once. Runs on the CROPPED band, not the raw
    raster, because the mask fails partway down the source: the raster's corner
    stays correct while the band's own region turns white. Checking the corner is
    what let it through the first time.

    Two independent signatures: the background mask failing exposes the artwork's
    white base rect, and the blurred upper die vanishing takes the gold pins with
    it. The side margins are background-only at this crop, so any near-white there
    is the first signature.
    """
    w, h = cropped.size
    for fy in (0.02, 0.15, 0.3, 0.5, 0.7, 0.85, 0.98):
        for fx in (0.01, 0.04, 0.08, 0.92, 0.96, 0.99):
            px = cropped.getpixel((round(w * fx), round(h * fy)))
            if sum(px) > 600:
                sys.exit(
                    f"rasterisation failed: margin pixel at ({fx:.0%},{fy:.0%}) is {px}, "
                    f"the SVG's white base rect is showing. Chrome dropped the background "
                    f"mask at scale {SCALE}; MAX_SCALE is {MAX_SCALE}.")
    gold = sum(
        1
        for y in range(0, h, max(1, h // 150))
        for x in range(round(w * 0.20), round(w * 0.55), max(1, w // 150))
        for r, g, b in [cropped.getpixel((x, y))]
        if r > 150 and 110 < g < 210 and b < 110
    )
    if gold < 5:
        sys.exit(f"rasterisation failed: found {gold} gold pin pixels, so the filtered "
                 f"upper die did not render at scale {SCALE}.")


def build(chrome: Path) -> None:
    if not SRC.is_file():
        sys.exit(f"missing source: {SRC}")
    raster = rasterize(chrome, SRC)  # once, then cropped per band
    for name, band_h_in, opy in BANDS:
        out = HERE / "assets" / name
        out_px = (round(BAND_W_IN * DPI), round(band_h_in * DPI))
        img = cover_crop(raster, band_h_in, opy)
        upscale = out_px[0] / img.size[0]
        if upscale > MAX_UPSCALE:
            sys.exit(f"DPI {DPI} would upscale the faithful {img.size[0]}px raster by "
                     f"{upscale:.2f}x, over MAX_UPSCALE {MAX_UPSCALE}. Real detail tops "
                     f"out at {FAITHFUL_DPI} DPI; raising SCALE past {MAX_SCALE} breaks "
                     f"the mask.")
        if img.size != out_px:
            img = img.resize(out_px, Image.Resampling.LANCZOS)
        assert_faithful(img)
        vignette(img).save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        print(f"{out.name}  {out_px[0]}x{out_px[1]}  {out.stat().st_size / 1e6:.2f} MB  "
              f"{DPI} DPI nominal / {FAITHFUL_DPI} DPI real detail  "
              f"(rasterised at {SRC_PX * SCALE}px, {upscale:.2f}x upscale)")


def self_test() -> None:
    # A solid white band makes the vignette's effect unambiguous.
    out = vignette(Image.new("RGB", (400, 200), (255, 255, 255)))
    assert out.getpixel((200, 100)) == (255, 255, 255), "centre must be untouched"
    for corner in ((0, 0), (399, 0), (0, 199), (399, 199)):
        assert out.getpixel(corner) == FIELD, f"corner {corner} must reach the field colour"
    # The top edge must resolve to the field right across the width, or the seam
    # this whole script exists to remove comes back.
    for x in (0, 120, 200, 380):
        assert out.getpixel((x, 0)) == FIELD, f"top edge leaks at x={x}"
    # And it must be a fade, not a step.
    mid = [out.getpixel((200, y))[0] for y in (0, 12, 24, 36, 48)]
    assert mid == sorted(mid), f"top fade is not monotonic: {mid}"
    assert mid[0] < mid[-1], "top fade does not actually ramp"

    # Every band: cover_crop must keep full width and the documented slice of the
    # height, and the chip's apex (25% of the source) must survive. Two ways to
    # lose it, both guarded: crop past it, or bury it so deep in the top fade that
    # it washes out. Heights and their object-position are coupled, so a new entry
    # in BANDS fails here rather than in a print proof.
    src = 1000
    assert len({name for name, _, _ in BANDS}) == len(BANDS), "duplicate band output name"
    for name, band_h_in, opy in BANDS:
        keep_h = round(src * band_h_in / BAND_W_IN)
        c = cover_crop(Image.new("RGB", (src, src)), band_h_in, opy)
        assert c.size == (src, keep_h), (name, c.size)
        top = round((src - keep_h) * opy)
        assert top < 0.25 * src, f"{name}: crop opens at {top / src:.1%}, at or below the apex"
        apex_in_band = (0.25 * src - top) / keep_h
        keep_at_apex = min(1.0, apex_in_band / FADE["top"])
        assert keep_at_apex >= 0.6, (
            f"{name}: apex is {1 - keep_at_apex:.0%} faded; it lands {apex_in_band:.1%} "
            f"into the band against a {FADE['top']:.0%} top fade"
        )

    # Catch an over-ambitious DPI here, without paying for a Chrome run to find out.
    assert SCALE <= MAX_SCALE, f"SCALE {SCALE} > MAX_SCALE {MAX_SCALE}"
    faithful_px = SRC_PX * SCALE
    assert BAND_W_IN * DPI / faithful_px <= MAX_UPSCALE, (
        f"DPI {DPI} upscales the {faithful_px}px raster past MAX_UPSCALE {MAX_UPSCALE}"
    )

    # assert_faithful must reject both silent-failure signatures.
    try:
        assert_faithful(Image.new("RGB", (200, 200), (255, 255, 255)))
    except SystemExit as e:
        assert "white base rect" in str(e), e
    else:
        raise AssertionError("assert_faithful passed an all-white render")
    try:
        assert_faithful(Image.new("RGB", (200, 200), (27, 43, 79)))  # dark, but no die
    except SystemExit as e:
        assert "gold pin" in str(e), e
    else:
        raise AssertionError("assert_faithful passed a render with no die")
    print("self-test ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--chrome", help="path to chrome.exe")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        build(find_chrome(args.chrome))
