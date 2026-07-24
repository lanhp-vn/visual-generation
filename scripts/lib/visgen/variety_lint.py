"""Deterministic composition-variety checks on authored social-post content.

Grades the CONTENT JSON, not the render: layout names, eyebrows, and text
lengths all live in the content, so a campaign is checkable before a render is
spent. Same violation contract as brand_lint / doc_lint ({"code", "detail"}).

Scope: only pages whose layout starts with "social-". A deck legitimately
repeats `stat-grid`; a campaign of posts does not legitimately repeat
`social-hero`. A batch is the social pages of every input document concatenated
in order, so a campaign authored as one JSON with N pages and one authored as N
JSONs grade identically.

Brand values (palette, fonts, dashes, diacritics) belong to brand_lint; copy
voice belongs to brand/voice-and-tone.md and the copy-reviewer agent. Nothing
here reads or restates either. Rules adapted from the vendored taste-skill
reference (see docs/superpowers/specs/2026-07-24-social-post-variety-lint-design.md).
"""
import math
import re

from visgen.schema import document_pages

SOCIAL_PREFIX = "social-"

# Word caps per text field; the "<field>-too-long" codes are generated from this.
WORD_CAPS = {"headline": 8, "sub": 20, "detail": 20, "quote": 25}

# Fields that are not prose: a file path and a nested object.
NON_TEXT_FIELDS = {"photo", "qr"}

_TAGS = re.compile(r"<[^>]+>")
_NUMBERED = re.compile(r"^\s*(?:\d+\s*[/.·:,-]|(?:no|phase|stage|step|part)\.?\s*\d)", re.I)
_VERSION = re.compile(r"\bv\d+\.\d+|\bbeta\b|\balpha\b|\bearly access\b|\binvite[ -]?only\b", re.I)


def _plain(value):
    """Visible text of a content field: inline markup stripped, or "" if not a string."""
    return _TAGS.sub("", value).strip() if isinstance(value, str) else ""


def _social_pages(docs):
    """Social pages of every document, concatenated in argument order."""
    pages = []
    for doc in docs:
        for page in document_pages(doc) or []:
            if str(page.get("layout", "")).startswith(SOCIAL_PREFIX):
                pages.append(page)
    return pages


def _lint_page(index, page):
    violations = []
    content = page.get("content") or {}
    where = f"post {index + 1} ({page.get('layout')})"

    for field, value in content.items():
        if field in NON_TEXT_FIELDS:
            continue
        text = _plain(value)
        if not text:
            continue
        if text.count("·") > 1:
            violations.append({"code": "middot-spam",
                               "detail": f"{where}: {text.count('·')} middots in {field!r}"})
        cap = WORD_CAPS.get(field)
        if cap is not None:
            words = len(text.split())
            if words > cap:
                violations.append({"code": f"{field}-too-long",
                                   "detail": f"{where}: {words} words in {field!r}, cap {cap}"})

    eyebrow = _plain(content.get("eyebrow"))
    if eyebrow and _NUMBERED.match(eyebrow):
        violations.append({"code": "numbered-eyebrow", "detail": f"{where}: {eyebrow!r}"})
    for field in ("eyebrow", "headline"):
        text = _plain(content.get(field))
        hit = _VERSION.search(text)
        if hit:
            violations.append({"code": "version-label",
                               "detail": f"{where}: {hit.group(0)!r} in {field!r}"})
    return violations


def lint_batch(docs):
    """Grade one or more content documents as a single campaign batch."""
    pages = _social_pages(docs)
    violations = []
    for i, page in enumerate(pages):
        violations += _lint_page(i, page)

    n = len(pages)
    layouts = [p.get("layout") for p in pages]
    for i in range(1, n):
        if layouts[i] == layouts[i - 1]:
            violations.append({"code": "layout-repeat-adjacent",
                               "detail": f"posts {i} and {i + 1} both use {layouts[i]!r}"})
    if n >= 4:
        # taste-skill's ratio (>= 4 layout families per 8 sections), capped at the
        # 5 social layouts that exist.
        needed = min(5, math.ceil(n / 2))
        distinct = len(set(layouts))
        if distinct < needed:
            violations.append({"code": "layout-monotony",
                               "detail": f"{distinct} distinct layouts across {n} posts, need {needed}"})
    if n:
        cap = math.ceil(n / 3)
        used = sum(1 for p in pages if _plain((p.get("content") or {}).get("eyebrow")))
        if used > cap:
            violations.append({"code": "eyebrow-overuse",
                               "detail": f"{used} of {n} posts carry an eyebrow, cap {cap}"})
    return {"passed": not violations, "violations": violations, "posts": n}


if __name__ == "__main__":
    clean = {"meta": {"format": "square"}, "pages": [
        {"layout": "social-stat", "content": {"eyebrow": "Cohort 1", "stat": "65",
                                              "label": 'Fellows in our <span class="hl">first</span> cohort'}},
        {"layout": "social-hero", "content": {"headline": "Care that reaches the home"}},
        {"layout": "social-quote", "content": {"quote": "The nurse sees my numbers before I call."}},
        {"layout": "social-cta", "content": {"headline": "Join the pilot", "cta": "Sign up"}},
    ]}
    assert lint_batch([clean])["passed"], lint_batch([clean])
    assert lint_batch([clean])["posts"] == 4

    # A deck is out of scope even when it repeats a layout.
    deck = {"meta": {"format": "deck-16x9"}, "pages": [
        {"layout": "stat-grid", "content": {"title": "A", "stats": []}},
        {"layout": "stat-grid", "content": {"title": "B", "stats": []}},
    ]}
    assert lint_batch([deck]) == {"passed": True, "violations": [], "posts": 0}

    # Every check fires.
    bad = {"meta": {"format": "square"}, "pages": [
        {"layout": "social-hero", "content": {
            "eyebrow": "01 / Index",
            "headline": "The one platform that finally connects every part of remote care",
            "sub": " ".join(["word"] * 21)}},
        {"layout": "social-hero", "content": {
            "eyebrow": "BETA", "headline": "Now open", "foot": "Hue · Da Nang · Hanoi"}},
        {"layout": "social-hero", "content": {"headline": "Third", "eyebrow": "Phase 2"}},
        {"layout": "social-hero", "content": {"quote": " ".join(["word"] * 26)}},
    ]}
    codes = {v["code"] for v in lint_batch([bad])["violations"]}
    assert codes == {"numbered-eyebrow", "headline-too-long", "sub-too-long", "quote-too-long",
                     "version-label", "middot-spam", "layout-repeat-adjacent",
                     "layout-monotony", "eyebrow-overuse"}, codes

    # A batch split across documents grades like one document.
    split = [{"meta": {"format": "square"}, "pages": [p]} for p in clean["pages"]]
    assert lint_batch(split) == lint_batch([clean])
    print("variety_lint self-check ok")
