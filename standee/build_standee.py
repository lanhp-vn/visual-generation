#!/usr/bin/env python3
"""Inline every local asset into the VISEMI Foundation standee.

Reads each ``*.src.html`` beside this script, replaces each ``__A(path)__``
placeholder with a base64 data URI, and writes the matching ``*.html`` -
self-contained files that open and print to a 36x72in PDF from any Chrome with
zero external requests. That matters here: the deliverable goes to a print
vendor, so it has to survive being emailed and opened on a machine that has
never seen this repo.

Sources are discovered by glob rather than listed. The folder used to hold three
named variations (a/b/c); only the one design survived review, so a hard-coded
list would just be a place for the names to go stale.

The substitution logic is imported from the onsemi pitch-deck build rather
than re-implemented, so there is exactly one copy of it in the repo.

Placeholder paths resolve against this folder first, then the repo root, so
both ``assets/qr-visemi.svg`` and
``visual-generation/brand/fonts/be-vietnam-pro-latin-700.woff2`` work.

    uv run python build_standee.py               # build every source found
    uv run python build_standee.py --self-test   # verify both resolve roots
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]  # .../cat-canh-program-management
PITCH = REPO / "programs/grant-applications/onsemi/supporting-materials/pitch-deck"

sys.path.insert(0, str(PITCH))
from build_pitch import inline  # noqa: E402  shared substitution logic

SRC_SUFFIX = ".src.html"


def sources() -> list[Path]:
    return sorted(HERE.glob(f"*{SRC_SUFFIX}"))


def build() -> None:
    found = sources()
    if not found:
        sys.exit(f"no *{SRC_SUFFIX} found in {HERE}")
    for src in found:
        html, n = inline(src.read_text(encoding="utf-8"), [HERE, REPO])
        out = HERE / (src.name[: -len(SRC_SUFFIX)] + ".html")
        out.write_text(html, encoding="utf-8")
        print(f"{out.name}  {len(html) / 1e6:.2f} MB  {n} assets inlined")


def self_test() -> None:
    # The real risk is a resolve root silently not working, so exercise both:
    # one asset beside this script, one addressed from the repo root.
    src = (
        '<img src="__A(assets/qr-visemi.svg)__">'
        '<i style="src:url(__A(visual-generation/brand/fonts/be-vietnam-pro-latin-700.woff2)__)">'
        '<img src="__A(assets/chip-band-baked.jpg)__">'
    )
    html, n = inline(src, [HERE, REPO])
    assert n == 3, f"expected 3 assets inlined, got {n}"
    assert "data:image/svg+xml;base64," in html, "HERE-relative svg did not inline"
    assert "data:font/woff2;base64," in html, "REPO-relative font did not inline"
    assert "data:image/jpeg;base64," in html, "baked chip band did not inline"
    assert "__A(" not in html, "placeholders survived substitution"
    # A rename that misses this script leaves it silently building nothing.
    assert sources(), f"no *{SRC_SUFFIX} beside {HERE.name}/"
    print("self-test ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    self_test() if args.self_test else build()
