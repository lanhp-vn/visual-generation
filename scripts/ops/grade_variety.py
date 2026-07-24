#!/usr/bin/env python3
"""Variety-lint social-post content JSON. Local-only; deterministic.

Delegates all checks to visgen.variety_lint (single source of truth): layout
repetition and monotony across a campaign, eyebrow overuse, middot spam,
numbered eyebrows, version labels, and per-field word caps. Only social-*
layouts are considered; decks and posters pass untouched.

Grades the authored content, not the render, so it runs before a render is
spent. Brand conformance (palette, fonts, dashes, diacritics, page size,
overflow) stays with grade_brand.py on the rendered output.

Usage: uv run python scripts/ops/grade_variety.py CONTENT.json [CONTENT2.json ...]
Multiple files are graded as one campaign batch, in the order given.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.variety_lint import lint_batch  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content", nargs="+", help="Content JSON path(s), graded as one batch.")
    args = ap.parse_args()
    docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.content]
    res = lint_batch(docs)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
