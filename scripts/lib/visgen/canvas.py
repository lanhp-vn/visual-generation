"""Render a canvas content dict to pixel-exact PNGs + a combined PDF via headless
Chromium (Playwright). Local-only: no outward action, no credentials."""
import json
from pathlib import Path

from visgen.html_render import render_document
from visgen.formats import page_px


def render_canvas(doc: dict, out_dir: Path, fmt: str = "both",
                  skill_dir: Path | None = None) -> dict:
    page_w, page_h = page_px(doc["meta"]["format"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    html = render_document(doc, skill_dir=skill_dir)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright

    report = {"format": doc["meta"]["format"], "page_px": [page_w, page_h], "pages": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": page_w, "height": page_h},
                                device_scale_factor=1)
        page.goto((out_dir / "index.html").resolve().as_uri())
        page.emulate_media(media="print", reduced_motion="reduce")
        page.wait_for_timeout(300)  # let fonts settle

        sections = page.query_selector_all(".slide")
        if fmt in ("png", "both"):
            (out_dir / "png").mkdir(exist_ok=True)
        for i, sec in enumerate(sections, start=1):
            box = sec.bounding_box()
            overflow = sec.evaluate("el => el.scrollHeight > el.clientHeight "
                                    "|| el.scrollWidth > el.clientWidth")
            report["pages"].append({"index": i, "overflow": bool(overflow),
                                    "width": round(box["width"]), "height": round(box["height"])})
            if fmt in ("png", "both"):
                sec.screenshot(path=str(out_dir / "png" / f"page-{i:02d}.png"))

        if fmt in ("pdf", "both"):
            (out_dir / "pdf").mkdir(exist_ok=True)
            page.pdf(path=str(out_dir / "pdf" / f"{out_dir.name}.pdf"),
                     width=f"{page_w}px", height=f"{page_h}px",
                     print_background=True,
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()

    (out_dir / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
