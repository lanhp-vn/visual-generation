#!/usr/bin/env python3
"""Render a canvas content JSON (slides, posts, posters) to PNG/PDF.

Usage:
    uv run python scripts/ops/render_canvas.py CONTENT.json [--format png|pdf|both] [--out DIR]

Writes into DIR (default: output/<content-stem>/):
    index.html, png/page-NN.png, pdf/<dirname>.pdf, render_report.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.canvas import render_canvas  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Render canvas content JSON to PNG/PDF via Chromium.")
    ap.add_argument("content", help="Path to the content JSON.")
    ap.add_argument("--format", choices=["png", "pdf", "both"], default="both")
    ap.add_argument("--out", help="Output directory (default: output/<stem>/).")
    args = ap.parse_args()

    content_path = Path(args.content)
    doc = json.loads(content_path.read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else Path("output") / content_path.stem
    report = render_canvas(doc, out, fmt=args.format)
    print(f"Rendered {len(report['pages'])} page(s) to {out}")


if __name__ == "__main__":
    main()
