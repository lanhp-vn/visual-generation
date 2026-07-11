#!/usr/bin/env python3
"""Render a Markdown+front-matter document to an A4 PDF + per-page PNGs via Paged.js/Chromium.

Usage:
    uv run python scripts/ops/render_doc.py DOC.md [--out DIR]

Writes into DIR (default: output/<doc-stem>/):
    index.html, png/page-NN.png, pdf/<dirname>.pdf, render_report.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.document import print_doc, render_doc  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Render a Markdown document to A4 PDF + PNGs.")
    ap.add_argument("doc", nargs="?", help="Path to the Markdown document (with YAML front-matter).")
    ap.add_argument("--out", help="Output directory (default: output/<stem>/).")
    ap.add_argument("--print-only", metavar="DIR",
                     help="Re-print an already-edited DIR/index.html to PDF+PNG "
                          "without regenerating it from Markdown (for docs with no "
                          "retained Markdown source).")
    ap.add_argument("--brand", help="Brand source dir (overrides VISGEN_BRAND / cwd brand/).")
    args = ap.parse_args()
    if args.brand:
        import os
        os.environ["VISGEN_BRAND"] = args.brand

    from visgen.preflight import check_branch
    msg = check_branch()
    if msg:
        print(msg, file=sys.stderr)
        sys.exit(2)

    if args.print_only:
        out = Path(args.print_only)
        prior_path = out / "render_report.json"
        prior = json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.exists() else {}
        report = print_doc(out, template=prior.get("template"), title=prior.get("title"))
        print(f"Re-printed {report['page_count']} page(s) to {out}")
        return

    if not args.doc:
        ap.error("doc is required unless --print-only is given")
    doc_path = Path(args.doc)
    out = Path(args.out) if args.out else Path("output") / doc_path.stem
    report = render_doc(doc_path, out)
    print(f"Rendered {report['page_count']} page(s) to {out}")


if __name__ == "__main__":
    main()
