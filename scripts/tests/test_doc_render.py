from pathlib import Path

from visgen.document import render_doc

FIX = Path(__file__).resolve().parent / "fixtures/docs/tiny.md"
FIX_HANDBOOK = Path(__file__).resolve().parent / "fixtures/docs/tiny-handbook.md"


def test_render_doc_produces_html_pdf_pngs(tmp_path):
    out = tmp_path / "tiny"
    report = render_doc(FIX, out)
    assert report["page_count"] >= 2
    assert (out / "index.html").is_file()
    pngs = sorted((out / "png").glob("page-*.png"))
    assert len(pngs) == report["page_count"]
    assert list((out / "pdf").glob("*.pdf"))


def test_render_doc_report_facts(tmp_path):
    report = render_doc(FIX, tmp_path / "tiny")
    assert report["template"] == "report"
    # no page overflows for this small doc
    assert all(p["overflow"] is False for p in report["pages"])
    # headings mapped to real pages
    texts = {h["text"] for h in report["headings"]}
    assert {"Overview", "Second Section"} <= texts
    assert all(isinstance(h["page"], int) for h in report["headings"])
    # TOC entries resolve to real target pages
    assert report["toc"]
    assert all(isinstance(e["targetPage"], int) and e["targetPage"] >= 1
               for e in report["toc"])
    assert all(e["shownPage"] is None for e in report["toc"])  # Paged.js 0.4.3 readout unreliable; targetPage authoritative
    # content pages (page >= 2) carry running header + footer page number
    body_pages = [c for c in report["chrome"] if c["page"] >= 2]
    assert body_pages and all(c["hasHeader"] and c["hasFooterNum"] for c in body_pages)
    # no orphaned headings
    assert report["orphan_headings"] == []


def test_render_doc_handbook_each_chapter_gets_own_page(tmp_path):
    """Regression: .handbook main h1 { break-before: page } silently never
    matched (Paged.js's break engine resolves selectors against a
    content-only clone that drops <body>, so a rule anchored on the body's
    .handbook class never fires) - all chapters used to land on one page."""
    report = render_doc(FIX_HANDBOOK, tmp_path / "tiny-handbook")
    assert report["template"] == "handbook"
    pages = {h["text"]: h["page"] for h in report["headings"]}
    assert list(pages) == ["Chapter One", "Chapter Two", "Chapter Three"]
    # each chapter on its own, distinct page - no chapter sharing a page
    assert len(set(pages.values())) == 3
    # cover(1) + TOC(2) + 3 chapter pages, no extra blank page before ch.1
    assert report["page_count"] == 5
    assert pages["Chapter One"] == 3
