#!/usr/bin/env python3
"""Brand-lint a render output directory. Local-only; deterministic.

Delegates all checks to slidegen.brand_lint (single source of truth): the
sanctioned palette (navy/green house hexes + token shades, the gold accent
#F5B433 and its shades, and the dark-theme token hexes) is allowed; any other
hex is flagged. Vendored <style>/<svg>, the decoration sparkles
(<svg class="spark">), and the .qrbox QR module SVG are exempt from the palette
scan. Em/en dashes, off-brand fonts, page size, overflow, and required/forbidden
strings (e.g. "Cat Canh" without diacritics) are still checked.

Usage: uv run python scripts/ops/grade_brand.py OUTDIR [--task TASK.json]
A TASK.json may carry {"required_strings": [...], "forbidden_strings": [...],
"expected_page_px": [w,h]}.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.brand_lint import lint  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--task")
    args = ap.parse_args()
    out = Path(args.outdir)
    html = (out / "index.html").read_text(encoding="utf-8")
    report = json.loads((out / "render_report.json").read_text(encoding="utf-8"))
    task = json.loads(Path(args.task).read_text(encoding="utf-8")) if args.task else {}
    res = lint(html, report,
               required_strings=task.get("required_strings", []),
               forbidden_strings=task.get("forbidden_strings", ["Cat Canh"]),
               expected_page_px=task.get("expected_page_px"))
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
