"""Deterministic document checks: pagination integrity + PDF sanity. Reuses the
brand surface check (visgen.brand_lint.lint_html) and adds only the document-only
guarantees the spec names. Grades the produced artifact (render report + PDF)."""
import re

from pypdf import PdfReader

from visgen.brand_lint import lint_html

_EMBED_KEYS = ("/FontFile", "/FontFile2", "/FontFile3")

# --- directory entry character budgets ----------------------------------------
# The real body is `class="doc directory lang-en"`, so the family is a token on
# <body>'s class attribute. A guard that looked for the literal `class="directory"`
# would match no rendered document and silently return [] forever.
_BODY_CLASS = re.compile(r'<body\b[^>]*\bclass="([^"]*)"', re.I)
# Entries nest several <div>s, so an entry's extent cannot be found by matching
# to the first `</div>` (that stops inside the head). Slice from each entry's own
# open tag to the next one instead; siblings never nest. The lookarounds keep
# `dentry` from matching the `dentry-bio`/`-head`/... class tokens.
_DIRECTORY_ENTRY = re.compile(
    r'<div\b[^>]*\bclass="[^"]*(?<![\w-])dentry(?![\w-])[^"]*"[^>]*>')
_DIRECTORY_NAME = re.compile(
    r'<p\b[^>]*\bclass="[^"]*(?<![\w-])dentry-name(?![\w-])[^"]*"[^>]*>(.*?)</p>',
    re.S)
_DIRECTORY_BUDGETS = {"dentry-bio": 280, "dentry-fact": 160}
_FIELD_RE = {
    cls: re.compile(
        rf'<p\b[^>]*\bclass="[^"]*(?<![\w-]){cls}(?![\w-])[^"]*"[^>]*>(.*?)</p>',
        re.S)
    for cls in _DIRECTORY_BUDGETS
}


def _plain_text(fragment: str) -> str:
    """Strip inline markup and collapse whitespace so the budget counts content,
    not tags: a field's length is what a reader sees, not its source bytes."""
    return " ".join(re.sub(r"<[^>]+>", "", fragment).split())


def lint_directory_budgets(html: str) -> list:
    """Flag directory entry fields longer than their character budget.

    Only directories are policed; any other family returns [] so `lint_doc` can
    call this unconditionally. One violation per over-long field, so a fix is a
    specific field rather than a whole entry.
    """
    body = _BODY_CLASS.search(html)
    if not body or "directory" not in body.group(1).split():
        return []

    violations = []
    starts = [m.start() for m in _DIRECTORY_ENTRY.finditer(html)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(html)
        entry = html[start:end]
        name_match = _DIRECTORY_NAME.search(entry)
        name = _plain_text(name_match.group(1)) if name_match else "(unnamed entry)"
        for cls, limit in _DIRECTORY_BUDGETS.items():
            for field in _FIELD_RE[cls].finditer(entry):
                n = len(_plain_text(field.group(1)))
                if n > limit:
                    violations.append({
                        "code": "entry-over-budget",
                        "detail": f"{name}: {cls} {n} > {limit}",
                    })
    return violations


def lint_pagination(report: dict) -> list:
    v = []
    for pg in report.get("pages", []):
        if pg.get("overflow"):
            v.append({"code": "page-overflow", "detail": f'page {pg.get("index")}'})
    for h in report.get("orphan_headings", []):
        v.append({"code": "orphan-heading",
                  "detail": f'{h.get("text")!r} alone at foot of page {h.get("page")}'})
    for e in report.get("toc", []):
        tp = e.get("targetPage")
        if not isinstance(tp, int) or tp < 1:
            v.append({"code": "toc-dangling", "detail": e.get("href")})
            continue
        sp = e.get("shownPage")
        if isinstance(sp, int) and sp != tp:
            v.append({"code": "toc-page-mismatch",
                      "detail": f'{e.get("href")}: shows {sp}, target on page {tp}'})
    for c in report.get("chrome", []):
        if c.get("page", 1) <= 1:      # cover is page 1: no running chrome by design
            continue
        if not c.get("hasHeader"):
            v.append({"code": "missing-header", "detail": f'page {c.get("page")}'})
        if not c.get("hasFooterNum"):
            v.append({"code": "missing-footer-page-number", "detail": f'page {c.get("page")}'})
    return v


def _font_embedded(font) -> bool:
    descs = []
    if "/FontDescriptor" in font:
        descs.append(font["/FontDescriptor"].get_object())
    for df in (font.get("/DescendantFonts") or []):
        d = df.get_object()
        if "/FontDescriptor" in d:
            descs.append(d["/FontDescriptor"].get_object())
    if not descs:
        return False
    return all(any(k in d for k in _EMBED_KEYS) for d in descs)


def _all_fonts_embedded(reader) -> bool:
    for page in reader.pages:
        res = page.get("/Resources")
        fonts = res.get("/Font") if res else None
        if not fonts:
            continue
        for ref in fonts.values():
            if not _font_embedded(ref.get_object()):
                return False
    return True


def lint_pdf(pdf_path, expected_pages=None) -> list:
    """The 'converts to PDF cleanly' guarantee: page count, selectable text, embedded fonts."""
    v = []
    reader = PdfReader(str(pdf_path))
    n = len(reader.pages)
    if expected_pages is not None and n != expected_pages:
        v.append({"code": "pdf-page-count", "detail": f"{n} != {expected_pages}"})
    text = "".join((pg.extract_text() or "") for pg in reader.pages)
    if not text.strip():
        v.append({"code": "pdf-no-text", "detail": "no selectable text extracted"})
    if not _all_fonts_embedded(reader):
        v.append({"code": "pdf-fonts-not-embedded", "detail": "a font lacks an embedded FontFile"})
    return v


def lint_doc(html, report, pdf_path, expected_pages=None) -> dict:
    v = lint_html(html)
    v += lint_pagination(report)
    v += lint_directory_budgets(html)
    v += lint_pdf(pdf_path, expected_pages=expected_pages or report.get("page_count"))
    return {"passed": not v, "violations": v}
