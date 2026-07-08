from pathlib import Path

from visgen.document import render_doc

FIX = Path(__file__).resolve().parent / "fixtures/docs/tiny.md"


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
