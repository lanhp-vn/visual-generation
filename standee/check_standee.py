#!/usr/bin/env python3
"""Acceptance gate for the VISEMI Foundation roll-up standee.

This is the contract for the design spec in DESIGN.md. For every ``*.src.html``
in this folder it checks the authoring source for the right asset wiring and the
BUILT file for print correctness and required copy, then measures the built PDF
if one is there. Sources are found by glob, matching ``build_standee.py``, but
each one's page size is registered in ``PAGE_SIZES`` below.

Unlike ``check_deck.py`` next door, this does NOT do naive substring matching on
the raw HTML. A built file is mostly base64, and base64 contains every digit and
letter, so a bare search for "65" or an em dash always "finds" one. Every text
assertion here runs against **visible text only**: data URIs stripped, then
<style>/<script> removed, then tags replaced with spaces and whitespace
collapsed. That is the difference between a check and a coin flip.

    uv run --project .. python check_standee.py
    uv run --project .. python check_standee.py --self-test
"""

from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_SUFFIX = ".src.html"

# Every physical print format the folder ships, keyed by source stem. Sources are
# still discovered by glob (delete one and it simply stops being checked), but a
# NEW one has to register its page size here rather than be trusted to declare its
# own: "the built @page matches the source's @page" would pass a source that has
# the wrong size in it, which is the mistake this check exists to catch.
# Whitespace-stripped and lowercased, to match the normalisation below.
PAGE_SIZES = {
    "visemi-standee": "size:36in72in",
    "visemi-standee-80x200": "size:80cm200cm",
}

# What each format must actually measure once printed, in PDF points (72/in), and
# the tolerance. This is the only check that catches a wrong `zoom` on the 80x200
# variant: its body is authored at 36 x 90in and scaled to the page, so a bad
# scale factor still produces a plausible-looking HTML file and a silently wrong
# print master. 2pt is under a millimetre.
PAGE_PT = {
    "visemi-standee": (36 * 72, 72 * 72),
    "visemi-standee-80x200": (80 / 2.54 * 72, 200 / 2.54 * 72),
}
PAGE_PT_TOL = 2.0

DATA_URI = re.compile(r"data:[a-z0-9.+/-]+;base64,[A-Za-z0-9+/=]+", re.I)
BLOCK = re.compile(r"<(style|script)\b[^>]*>.*?</\1>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

# Copy that must render, verbatim (compared case-insensitively).
REQUIRED = [
    "unlock vietnam's talents in semiconductors",
    "a u.s. 501(c)(3) nonprofit",
    "visemi.org",
    "connects vietnamese talent with the semiconductor industry",
    "chip demand is surging",
    "skilled talent is not",
    "industry needs and educational output have drifted apart",
    "scan to learn more about us",  # operator-specified CTA wording
]

# The four live initiatives, full diacritics.
PROGRAMS = [
    "demystifying semiconductors",
    "visemi chip chat",
    "cất cánh (takeoff) fellowship",
    "cất cánh pathway",
]

# The operator chose to print no statistics: every one available is either
# cumulative or cohort-bound, so any of these on a banner dates the print.
FORBIDDEN_NUMBERS = ["35.5k", "$200k", "$15,000", "300+", "80%+", "25+", "8 webinars"]

# Partner logos are deliberately excluded from this design.
PARTNER_DIRS = ("assets/partners/", "assets/partners-norm/")

# The band is baked by make_chip_band.py with its fade already in the pixels: an
# alpha CSS gradient over the raw chip.svg becomes a PDF soft mask, which some
# viewers drop, leaving a hard seam across the banner. So the source must
# reference a baked JPEG, never chip.svg directly. Which one is per format (a band
# has to reach the bottom edge, so a taller banner needs a taller bake), hence the
# prefix match rather than one filename.
BAND = re.compile(r"__A\(assets/chip-band-baked[\w-]*\.jpg\)__")

FONT_WEIGHTS = ("400", "500", "600", "700")


def visible_text(raw: str) -> str:
    """Reduce an HTML document to the words a reader would actually see."""
    s = DATA_URI.sub(" ", raw)
    s = BLOCK.sub(" ", s)
    s = TAG.sub(" ", s)
    s = htmllib.unescape(s)
    # Justified copy carries &shy; inside long words (see the source). A soft
    # hyphen is invisible unless the line breaks there, so it must not count as
    # text - otherwise every required-copy assertion fails on a word that in fact
    # renders perfectly.
    s = s.replace("­", "")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return WS.sub(" ", s).strip().casefold()


def pdf_page_pt(pdf: Path) -> tuple[int, tuple[float, float]] | None:
    """Page count and first-page size in points, or None if it cannot be read.

    pypdfium2 lives in the working repo's env, not the plugin's, so a missing
    import is a skip and not a failure - the HTML checks still stand on their own.
    """
    try:
        import pypdfium2  # noqa: PLC0415  optional, see docstring
    except ImportError:
        return None
    doc = pypdfium2.PdfDocument(pdf)
    return len(doc), doc[0].get_size()


def check(errors: list[str]) -> None:
    found = sorted(HERE.glob(f"*{SRC_SUFFIX}"))
    if not found:
        errors.append(f"no *{SRC_SUFFIX} in {HERE.name}/")
        return
    for src in found:
        check_one(src.name[: -len(SRC_SUFFIX)], errors)


def check_one(stem: str, errors: list[str]) -> None:
    def bad(msg: str) -> None:
        errors.append(msg)

    src_path = HERE / f"{stem}.src.html"
    out_path = HERE / f"{stem}.html"
    if stem not in PAGE_SIZES:
        bad(f"{src_path.name}: unregistered print format, add its size to PAGE_SIZES")
        return
    if not out_path.is_file():
        bad(f"{out_path.name}: missing (run build_standee.py)")
        return

    src = src_path.read_text(encoding="utf-8")
    out = out_path.read_text(encoding="utf-8")
    text = visible_text(out)

    # --- asset wiring, read from the source where paths are still legible
    if not BAND.search(src):
        bad(f"{src_path.name}: no baked chip band wired, expected {BAND.pattern}")
    if "assets/chip.svg" in src:
        bad(f"{src_path.name}: uses chip.svg raw, use the baked {BAND}")
    # A soft-mask fade is invisible until it reaches a PDF viewer that drops it,
    # so guard the two ways of reintroducing one.
    for prop in ("mask-image:", "-webkit-mask-image:"):
        if prop in src:
            bad(f"{src_path.name}: {prop} does not survive Chrome's print path")
    if "__A(assets/qr-visemi.svg)__" not in src:
        bad(f"{src_path.name}: vector QR not wired")
    if "visemi-logo-white.svg" not in src:
        bad(f"{src_path.name}: white logo SVG not wired")
    for lowres in ("Key Visual", "Linkedin-1"):
        if lowres in src:
            bad(f"{src_path.name}: uses {lowres!r}, too low-res for 36in")
    # A placeholder is resolved at build time, so a source pointing into a
    # git-ignored scratch path builds here and nowhere else.
    if "data/.tmp" in src:
        bad(f"{src_path.name}: asset addressed via git-ignored data/.tmp, copy it into assets/")
    for d in PARTNER_DIRS:
        if d in src:
            bad(f"{src_path.name}: partner logos are excluded from this design, found {d}")

    # --- build integrity
    if "__A(" in out:
        bad(f"{out_path.name}: placeholders survived the build")

    # --- print correctness
    page = re.search(r"@page\s*\{[^}]*\}", out, re.I)
    if not page:
        bad(f"{out_path.name}: no @page rule")
    else:
        rule = WS.sub("", page.group(0)).lower()
        if PAGE_SIZES[stem] not in rule:
            bad(f"{out_path.name}: @page must be {PAGE_SIZES[stem]!r}, got {page.group(0)!r}")
        if "margin:0" not in rule:
            bad(f"{out_path.name}: @page must set margin:0")
    if "print-color-adjust" not in out:
        bad(f"{out_path.name}: no print-color-adjust, Chrome will drop backgrounds")

    # The PDF is the deliverable, and it is the only place a wrong `zoom` or a
    # leaked px unit becomes visible. Absent PDF or absent pypdfium2 is a skip.
    pdf_path = HERE / f"{stem}.pdf"
    if pdf_path.is_file():
        measured = pdf_page_pt(pdf_path)
        if measured is None:
            print(f"  (skipped {pdf_path.name} page-size check: pypdfium2 not installed)")
        else:
            pages, size = measured
            want = PAGE_PT[stem]
            if pages != 1:
                bad(f"{pdf_path.name}: {pages} pages, must be exactly 1")
            if any(abs(g - w) > PAGE_PT_TOL for g, w in zip(size, want)):
                bad(f"{pdf_path.name}: page is {tuple(round(v, 1) for v in size)}pt, "
                    f"must be {tuple(round(v, 1) for v in want)}pt")

    # --- fonts: both subsets at all four weights, or diacritics break
    for w in FONT_WEIGHTS:
        for subset in ("latin", "vietnamese"):
            if f"be-vietnam-pro-{subset}-{w}.woff2" not in src:
                bad(f"{src_path.name}: missing font {subset} {w}")
    n_fonts = out.count("data:font/woff2;base64,")
    if n_fonts < 8:
        bad(f"{out_path.name}: expected 8 inlined woff2, found {n_fonts}")
    if "unicode-range" not in out:
        bad(f"{out_path.name}: font faces need unicode-range or the subsets collide")

    # --- copy
    for phrase in REQUIRED + PROGRAMS:
        if phrase not in text:
            bad(f"{out_path.name}: missing required copy {phrase!r}")
    for num in FORBIDDEN_NUMBERS:
        if num in text:
            bad(f"{out_path.name}: statistic {num!r} must not be printed")
    for dash in ("—", "–"):
        if dash in text:
            bad(f"{out_path.name}: contains {dash!r}, house rule forbids em/en dashes")
    if "cat canh" in text:
        bad(f"{out_path.name}: 'Cat Canh' without diacritics")


def self_test() -> None:
    # The whole point of visible_text is that base64 must not be searchable.
    poisoned = '<img src="data:image/png;base64,AAA35BQBBBem300xyz80">ok'
    assert visible_text(poisoned) == "ok", visible_text(poisoned)
    assert "35" not in visible_text(poisoned), "base64 leaked into visible text"

    assert visible_text("<style>.a{content:'35.5K'}</style>hi") == "hi"
    assert visible_text("<b>Unlock</b><b>Vietnam’s</b>") == "unlock vietnam's"
    # Tags must become spaces, not vanish, or adjacent lines fuse into one word.
    assert visible_text("<span>TALENTS IN</span><span>SEMICONDUCTORS</span>") == (
        "talents in semiconductors"
    )
    # Soft hyphens must vanish, whether written as an entity or a literal, and
    # must not leave a space that would split the word into two.
    assert visible_text("semi&shy;con&shy;duc&shy;tor") == "semiconductor"
    assert visible_text("semi­conductor") == "semiconductor"

    # Two registries, one per format. A stem in one and not the other means a
    # format silently loses either its @page check or its PDF measurement.
    assert PAGE_SIZES.keys() == PAGE_PT.keys(), (PAGE_SIZES.keys(), PAGE_PT.keys())
    # And every registered format must still have a source, or the registry is
    # carrying a name that no longer exists.
    for stem in PAGE_SIZES:
        assert (HERE / f"{stem}{SRC_SUFFIX}").is_file(), f"no source for {stem}"
    print("self-test ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        sys.exit(0)
    errs: list[str] = []
    check(errs)
    if errs:
        print(f"FAILED ({len(errs)})")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)
    print("PASSED")
