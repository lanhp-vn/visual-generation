"""The `directory` template family: a paged document listing many entities with
structured facts and one action each, N per page.

The first test is a gate rather than a feature test. A directory's contents page
and its per-group indexes are only worth building if a jump link survives the
Paged.js plus headless-Chromium print into the PDF. If it does not, the fallback
is printed page numbers with no jump behaviour, which is a decision to bring
back to the operator rather than one to absorb.
"""
from pathlib import Path

from pypdf import PdfReader
from visgen.document import render_doc

FIX = Path(__file__).resolve().parent / "fixtures/docs"


def assert_internal_links(pdf_path) -> list:
    """Return the 0-based page indexes carrying at least one internal jump link.

    Chromium writes an internal link either as an action (`/A` with `/S /GoTo`)
    or as a bare `/Dest` on the annotation. Check both: treating only the first
    as a link would report a working feature as broken.
    """
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            action = obj.get("/A")
            if obj.get("/Dest") is not None or (
                action is not None and action.get_object().get("/S") == "/GoTo"
            ):
                pages.append(i)
                break
    return pages


def test_internal_anchors_survive_pdf_print(tmp_path):
    out = tmp_path / "probe"
    render_doc(FIX / "directory-min.md", out)
    pdf = next((out / "pdf").glob("*.pdf"))
    assert assert_internal_links(pdf), (
        "no internal jump links in the PDF: a clickable contents page is not "
        "achievable through Paged.js plus Chromium print"
    )


def test_both_anchor_routes_resolve_to_a_destination(tmp_path):
    """A link annotation is not a working jump.

    Chromium writes these as named destinations and registers them in the
    catalog's /Dests dictionary. A name that is linked but never registered
    lands nowhere in a reader while still counting as an annotation, so assert
    the registration rather than the annotation. Both routes matter: the
    auto-generated table of contents (group-*) and a hand-written anchor into a
    hand-written id (entry-*), which is how a per-group index is built.
    """
    out = tmp_path / "probe"
    render_doc(FIX / "directory-min.md", out)
    pdf = next((out / "pdf").glob("*.pdf"))
    reader = PdfReader(str(pdf))
    registered = set(reader.named_destinations)
    assert {"/group-one", "/group-two"} <= registered, sorted(registered)
    assert {"/entry-one", "/entry-two"} <= registered, sorted(registered)

    linked = set()
    for page in reader.pages:
        for annot in page.get("/Annots") or []:
            dest = annot.get_object().get("/Dest")
            if dest is not None:
                linked.add(str(dest))
    assert linked <= registered, sorted(linked - registered)


def test_directory_is_a_template_family():
    from visgen.schema import DOC_TEMPLATES

    assert "directory" in DOC_TEMPLATES


def test_directory_cover_renders_its_fields(tmp_path):
    """The body class is `doc directory lang-en`, so an equality match on
    class="directory" would never fire. Assert the token, not the attribute."""
    out = tmp_path / "cover"
    render_doc(FIX / "directory-min.md", out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "cover-directory" in html
    assert 'class="doc directory ' in html
    assert "Directory Anchor Probe" in html
    assert "2 entries" in html
    assert "Confidential" in html
    assert "Updated September 2026" in html
