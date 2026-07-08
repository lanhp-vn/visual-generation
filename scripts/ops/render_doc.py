#!/usr/bin/env python3
"""Render a Markdown+front-matter document to an A4 PDF + per-page PNGs via Paged.js/Chromium.

Usage:
    uv run python scripts/ops/render_doc.py DOC.md [--out DIR]

Writes into DIR (default: output/<doc-stem>/):
    index.html, png/page-NN.png, pdf/<dirname>.pdf, render_report.json
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.document import render_doc  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Render a Markdown document to A4 PDF + PNGs.")
    ap.add_argument("doc", help="Path to the Markdown document (with YAML front-matter).")
    ap.add_argument("--out", help="Output directory (default: output/<stem>/).")
    args = ap.parse_args()

    doc_path = Path(args.doc)
    out = Path(args.out) if args.out else Path("output") / doc_path.stem
    report = render_doc(doc_path, out)
    print(f"Rendered {report['page_count']} page(s) to {out}")


if __name__ == "__main__":
    main()
