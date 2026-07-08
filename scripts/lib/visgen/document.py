"""Render a Markdown+front-matter document to an A4 PDF + per-page PNGs via a
vendored, inlined Paged.js polyfill in headless Chromium. Second renderer on the
shared engine: it reuses visgen.tokens / html_render theme assembly / brand_lint
and the Playwright pattern from visgen.canvas. Local-only; no credentials.

This module is import-safe without a browser: Playwright is imported lazily
inside render_doc (added in a later task), so parse_frontmatter / markdown_to_html
can be used and tested standalone."""
import json
import re
from pathlib import Path

import markdown
import yaml

from visgen.schema import SchemaError, validate_frontmatter
from visgen.html_render import render_doc_html

DOC_EXTENSIONS = ["extra", "toc", "admonition"]

_FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a leading `--- yaml --- ` block. Returns (meta, body_markdown)."""
    m = _FRONT_MATTER.match(text)
    if not m:
        raise SchemaError("document must start with a YAML front-matter block delimited by '---'")
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise SchemaError("front-matter must be a mapping")
    return meta, text[m.end():]


def markdown_to_html(body_md: str) -> tuple[str, str]:
    """Convert body Markdown to (body_html, toc_html). toc_html is python-markdown's
    <div class="toc"> nav; Paged.js fills its real page numbers via target-counter."""
    md = markdown.Markdown(
        extensions=DOC_EXTENSIONS,
        extension_configs={"toc": {"toc_depth": "1-3"}},
        output_format="html5",
    )
    body_html = md.convert(body_md)
    toc_html = getattr(md, "toc", "") or ""
    return body_html, toc_html


# --- browser-side introspection (run after Paged.js finishes) -----------------
_HEADINGS_JS = """() => Array.from(
  document.querySelectorAll('main h1, main h2, main h3, main h4')
).map(h => {
  const pg = h.closest('.pagedjs_page');
  return { id: h.id || null, text: h.textContent.trim(), level: Number(h.tagName[1]),
           page: pg ? Number(pg.getAttribute('data-page-number')) : null };
})"""

_TOC_JS = """() => Array.from(document.querySelectorAll('.toc a')).map(a => {
  const href = a.getAttribute('href') || '';
  const id = href.replace(/^#/, '');
  const target = id ? document.getElementById(id) : null;
  const pg = target ? target.closest('.pagedjs_page') : null;
  const targetPage = pg ? Number(pg.getAttribute('data-page-number')) : null;
  const after = getComputedStyle(a, '::after').content || '';
  const m = after.match(/\\d+/);
  return { href, targetPage, shownPage: m ? Number(m[0]) : null };
})"""

_CHROME_JS = """() => Array.from(document.querySelectorAll('.pagedjs_page')).map(pg => {
  const n = Number(pg.getAttribute('data-page-number'));
  const footer = pg.querySelector('.pagedjs_margin-bottom-right, .pagedjs_margin-bottom-center');
  const header = pg.querySelector('.pagedjs_margin-top-left, .pagedjs_margin-top-right, .pagedjs_margin-top-center');
  return { page: n,
           hasHeader: !!(header && header.textContent.trim()) || !!(header && header.querySelector('svg,img')),
           hasFooterNum: !!(footer && /\\d/.test(footer.textContent || '')) };
})"""

_ORPHAN_JS = """() => {
  const bad = [];
  document.querySelectorAll('main h1, main h2, main h3, main h4').forEach(h => {
    const pg = h.closest('.pagedjs_page'); if (!pg) return;
    const content = pg.querySelector('.pagedjs_page_content') || pg;
    const blocks = Array.from(
      content.querySelectorAll('h1,h2,h3,h4,p,ul,ol,table,figure,blockquote,.admonition')
    ).filter(e => e.closest('.pagedjs_page') === pg);
    if (blocks.length && blocks[blocks.length - 1] === h)
      bad.push({ text: h.textContent.trim(),
                 page: Number(pg.getAttribute('data-page-number')) });
  });
  return bad;
}"""


def render_doc(md_path, out_dir, skill_dir=None) -> dict:
    text = Path(md_path).read_text(encoding="utf-8")
    meta, body_md = parse_frontmatter(text)
    validate_frontmatter(meta)
    body_html, toc_html = markdown_to_html(body_md)
    html = render_doc_html(meta, body_html, toc_html, skill_dir=skill_dir)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright  # lazy: keeps this module import-safe

    report = {"template": meta["template"], "title": meta["title"], "pages": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto((out_dir / "index.html").resolve().as_uri())
        # Paged.js runs on load; PagedConfig.after sets the flag (see base template).
        page.wait_for_function("window.__PAGED_DONE === true", timeout=60000)

        (out_dir / "png").mkdir(exist_ok=True)
        page_boxes = page.query_selector_all(".pagedjs_page")
        for i, pg in enumerate(page_boxes, start=1):
            box = pg.bounding_box()
            overflow = pg.evaluate(
                "el => { const c = el.querySelector('.pagedjs_page_content'); "
                "return c ? (c.scrollHeight > c.clientHeight + 1) : false; }")
            report["pages"].append({"index": i, "overflow": bool(overflow),
                                    "width": round(box["width"]), "height": round(box["height"])})
            pg.screenshot(path=str(out_dir / "png" / f"page-{i:02d}.png"))

        report["headings"] = page.evaluate(_HEADINGS_JS)
        report["toc"] = page.evaluate(_TOC_JS)
        # Paged.js 0.4.3 names its target-counter with an embedded UUID, so the
        # getComputedStyle('::after') readout in _TOC_JS captures garbage digits, not the
        # rendered TOC page number (e.g. 3837 for target page 3). The visible TOC number
        # is correct (it comes straight from target-counter); only this readout is
        # untrustworthy. targetPage (from the heading's real .pagedjs_page) is
        # authoritative, so null out shownPage rather than feed doc_lint a false mismatch.
        for _e in report["toc"]:
            _e["shownPage"] = None
        report["chrome"] = page.evaluate(_CHROME_JS)
        report["orphan_headings"] = page.evaluate(_ORPHAN_JS)

        (out_dir / "pdf").mkdir(exist_ok=True)
        # Paged.js already produced print-ready A4 page boxes; print WITHOUT
        # emulating print media (mirrors pagedjs-cli). prefer_css_page_size honors
        # @page { size: A4 }; print_background keeps cover/table fills.
        page.pdf(path=str(out_dir / "pdf" / f"{out_dir.name}.pdf"),
                 prefer_css_page_size=True, print_background=True)
        browser.close()

    report["page_count"] = len(report["pages"])
    (out_dir / "render_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
