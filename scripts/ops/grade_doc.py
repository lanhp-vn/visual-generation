#!/usr/bin/env python3
"""Grade a rendered document output directory. Local-only; deterministic.

Runs the brand surface check (visgen.brand_lint on index.html), pagination
integrity (TOC page numbers match, no overflow, no orphaned headings, running
headers/footers present), and PDF sanity (page count, fonts embedded, text
selectable) via visgen.doc_lint.

Usage: uv run python scripts/ops/grade_doc.py OUTDIR
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.doc_lint import lint_doc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--brand", help="Brand source dir (overrides VISGEN_BRAND / cwd brand/).")
    args = ap.parse_args()
    if args.brand:
        import os
        os.environ["VISGEN_BRAND"] = args.brand
    out = Path(args.outdir)
    html = (out / "index.html").read_text(encoding="utf-8")
    report = json.loads((out / "render_report.json").read_text(encoding="utf-8"))
    pdfs = sorted((out / "pdf").glob("*.pdf"))
    if not pdfs:
        print(json.dumps({"passed": False, "violations": [{"code": "no-pdf", "detail": str(out)}]}))
        sys.exit(1)
    res = lint_doc(html, report, pdfs[0])
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
