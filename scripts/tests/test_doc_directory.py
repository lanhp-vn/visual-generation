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


# --- entry block and group openers (frozen contract) -------------------------

FIXTURE_BIO = "A short biography of the first entry, kept inside the character budget."


def test_five_entries_lay_out_without_overflow(tmp_path):
    out = tmp_path / "entries"
    report = render_doc(FIX / "directory-min.md", out)
    assert all(not p["overflow"] for p in report["pages"]), \
        [p["index"] for p in report["pages"] if p["overflow"]]
    html = (out / "index.html").read_text(encoding="utf-8")
    assert html.count('class="dentry"') == 5

    # "two per page" is the whole point of the block, and an overflow check
    # cannot see it: Paged.js just flows a too-tall entry onto another page,
    # reporting no overflow while the layout is wrong. The place name appears
    # only inside an entry, so it disambiguates from the index links.
    pdf = next((out / "pdf").glob("*.pdf"))
    pages = [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]
    first = [i for i, t in enumerate(pages) if "Entry One" in t and "Country A" in t]
    second = [i for i, t in enumerate(pages) if "Entry Two" in t and "Country B" in t]
    assert first and second, (first, second)
    assert first[0] == second[0], (
        f"the first two entries landed on pages {first[0] + 1} and {second[0] + 1}; "
        "a directory lays two entries out per page"
    )


def test_group_opener_starts_its_own_page(tmp_path):
    """Assert the page actually broke, not merely that the class is present.

    Paged.js resolves break-before/after against a content-only clone that drops
    the <body> element and its class, so a rule anchored on the body class
    (`.directory .dgroup`) silently never fires there. document.css records the
    identical regression for `.handbook main h1`, whose fix was to anchor the
    fragmentation rule on <main>, which does survive the clone.

    A class-presence check passes over exactly that bug, so this drives off the
    printed PDF instead: the role line appears only inside a `.dentry`, so a
    full-page opener that shares its page with one has not broken.
    """
    out = tmp_path / "groups"
    render_doc(FIX / "directory-min.md", out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'class="dgroup"' in html
    assert 'class="dgroup-inline"' in html

    pdf = next((out / "pdf").glob("*.pdf"))
    pages = [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]
    opener = [i for i, t in enumerate(pages) if "Second Field" in t and "2 entries" in t]
    assert opener, "group opener text not found in the printed PDF"
    assert "Institution Name" not in pages[opener[0]], (
        "the full-page group opener shares a page with a directory entry, so "
        "break-before did not fire: anchor the rule on main.directory, not "
        "on the body class"
    )


# --- character budget lint (frozen contract) ---------------------------------


def test_budget_lint_recognises_a_real_rendered_document(tmp_path):
    """Drive the lint from real rendered HTML, never a hand-written snippet.

    The rendered body is `class="doc directory lang-en"`, so a family guard
    written as `'class="directory"' not in html` matches nothing and returns []
    for every real document. The check would then pass while never running. A
    snippet-only test cannot catch that; this one does.
    """
    from visgen.doc_lint import lint_directory_budgets

    out = tmp_path / "budget"
    render_doc(FIX / "directory-min.md", out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert lint_directory_budgets(html) == []

    bloated = html.replace(FIXTURE_BIO, "x" * 400)
    assert bloated != html, "fixture bio text not found in the render; test is stale"
    violations = lint_directory_budgets(bloated)
    assert len(violations) == 1, violations
    assert violations[0]["code"] == "entry-over-budget"
    assert "Entry One" in violations[0]["detail"]
    assert "dentry-bio" in violations[0]["detail"]


def test_budget_lint_ignores_a_non_directory_document(tmp_path):
    from visgen.doc_lint import lint_directory_budgets

    out = tmp_path / "report"
    render_doc(FIX / "tiny.md", out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert lint_directory_budgets(html) == []


def test_lint_doc_surfaces_a_budget_violation(tmp_path):
    """The lint is only worth writing if lint_doc actually calls it."""
    from visgen.doc_lint import lint_doc

    out = tmp_path / "lintdoc"
    report = render_doc(FIX / "directory-min.md", out)
    pdf = next((out / "pdf").glob("*.pdf"))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert lint_doc(html, report, pdf)["passed"], "clean fixture should lint clean"

    bloated = html.replace(FIXTURE_BIO, "x" * 400)
    result = lint_doc(bloated, report, pdf)
    assert not result["passed"]
    assert any(v["code"] == "entry-over-budget" for v in result["violations"]), \
        result["violations"]
