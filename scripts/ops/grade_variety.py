#!/usr/bin/env python3
"""Variety- and copy-lint content JSON. Local-only; deterministic; ADVISORY.

Delegates all checks to visgen.variety_lint (single source of truth) and reports
both of its entry points, which have deliberately different scopes:

- lint_pages: per-page copy checks on EVERY layout - middot spam, per-field word
  caps, numbered eyebrows, version labels, verbless decoration strips, and the
  vocabulary tells (placeholder text, filler verbs, coy social proof, poetic
  labels, fake-precise numbers). Vocabulary is scanned inside nested content too,
  since deck prose lives in lists of dicts.
- lint_batch: repetition checks on social-* pages ONLY - layout repetition,
  monotony, eyebrow overuse. Decks and posters are exempt because a deck
  legitimately repeats stat-grid.

This report is ADVISORY: it flags judgment calls, not brand violations, so a
nonzero exit means "read these findings", not "the visual is rejected".
brand_lint (grade_brand.py / grade_doc.py) remains the only blocking gate.

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
from visgen.variety_lint import lint_batch, lint_pages  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content", nargs="+", help="Content JSON path(s), graded as one batch.")
    args = ap.parse_args()
    docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.content]
    pages, batch = lint_pages(docs), lint_batch(docs)
    res = {"passed": pages["passed"] and batch["passed"],
           "pages": pages["pages"], "posts": batch["posts"],
           "violations": pages["violations"] + batch["violations"]}
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
