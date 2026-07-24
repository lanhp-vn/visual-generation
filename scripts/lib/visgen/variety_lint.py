"""Deterministic composition and copy checks on authored content.

Grades the CONTENT JSON, not the render: layouts, eyebrows, and text lengths all
live in the content, so a deck or a campaign is checkable before a render is
spent. Same violation contract as brand_lint / doc_lint ({"code", "detail"}).

Two entry points with deliberately different scopes:

- lint_pages(docs) - per-page copy checks on EVERY layout. Nothing about a
  numbered eyebrow or a slop verb is social-specific: `eyebrow` is rendered by 9
  of the slides layouts, both poster layouts, and both document covers, so a
  pitch deck could carry "01 / Index" on every page with nothing to catch it.
- lint_batch(docs) - repetition checks on `social-` pages ONLY. A deck
  legitimately repeats `stat-grid`; a campaign of posts does not legitimately
  repeat `social-hero`.

The page checks live in lint_pages and NOT in lint_batch, so a caller running
both (grade_variety.py does) reports each code exactly once.

Both are ADVISORY. brand_lint stays the only blocking gate, because these rules
are judgment calls with real false-positive cost: a slop-verb blocklist will
eventually flag a headline someone actually wants. Nothing here needs a
suppression flag precisely because nothing here blocks.

Brand values (palette, fonts, dashes, diacritics) belong to brand_lint; copy
voice belongs to brand/voice-and-tone.md and the copy-reviewer agent. Nothing
here reads or restates either - in particular the em/en-dash ban and the emoji
ban are brand_lint's, not duplicated here.

Rules adapted from the vendored taste-skill reference. The items deliberately NOT
adopted, and why, are recorded in
docs/superpowers/specs/2026-07-24-reference-harvest-design.md - read that before
mining these submodules again, because several of their instructions contradict
this repo's non-negotiables.
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

# Vocabulary tells. Scanned over every string in a page's content, nested
# included, because deck layouts keep their prose inside lists of dicts (items,
# columns, cards, stats, people, phases, tiers, blocks).
#
# Two patterns are deliberately narrower than the taste-skill source:
#   - "elevat(e|es|ing)" excludes "elevated", which is ordinary clinical copy
#     ("elevated blood pressure") in a telehealth brand.
#   - "next-gen" excludes "next generation", which is ordinary fellowship copy
#     ("the next generation of healthcare leaders").
# "Transform" and "Empower" are omitted entirely: both are slop in the abstract
# and both are legitimate, frequent words in health and nonprofit copy, so even
# at advisory severity they would train operators to ignore the report.
_VOCAB = {
    "placeholder-text": re.compile(
        r"\b(lorem ipsum|john doe|jane doe|acme|your name here|company name|tbd|todo)\b", re.I),
    "filler-verb": re.compile(
        r"\b(elevat(?:e|es|ing)|unleash\w*|seamless(?:ly)?|next[- ]gen\b|revolutioniz\w+"
        r"|supercharg\w+|unlock the power|cutting[- ]edge|game[- ]chang\w+|harness\w*"
        r"|delv(?:e|es|ing))\b", re.I),
    "coy-social-proof": re.compile(r"\bquietly (?:in use at|trusted by|used by)\b", re.I),
    "poetic-label": re.compile(
        r"\b(from the field|field notes|on our desks|currently on the bench|loose plates)\b", re.I),
    "fake-precise-number": re.compile(r"\b(?:99\.9{1,2}|100\.0{1,2})\s*%|\b1234567"),
}

# Vietnamese tells, intentionally empty. Vietnamese marketing has its own slop
# register and it takes native-speaker judgment to name; guessing it would ship
# false positives against real Vietnamese copy. Adding entries here needs no
# logic change - _lint_page already scans this alongside _VOCAB.
VI_VOCAB = {}

# Verbless all-caps strips: "BRAND. MOTION. SPATIAL.", "DESIGN · BUILD · SHIP".
# Applied to `eyebrow` and `foot` only, because that is where the tell lives;
# scanning every field would flag legitimate all-caps branding elsewhere.
_DECOR_STRIP = re.compile(r"^(?:[A-Z]{2,}\s*[.·]\s*){1,3}[A-Z]{2,}\.?$")


def _plain(value):
    """Visible text of a content field: inline markup stripped, or "" if not a string."""
    return _TAGS.sub("", value).strip() if isinstance(value, str) else ""


def _walk_strings(value, path=""):
    """Every string inside a content value, with a dotted path label.

    Deck layouts nest nearly all their prose in lists of dicts, so a top-level
    field walk would leave decks and posters effectively unchecked.
    """
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, sub in value.items():
            if key in NON_TEXT_FIELDS:
                continue
            yield from _walk_strings(sub, f"{path}.{key}" if path else str(key))
    elif isinstance(value, (list, tuple)):
        for i, sub in enumerate(value):
            yield from _walk_strings(sub, f"{path}[{i}]")


def _all_pages(docs):
    """Every page of every document, concatenated in argument order."""
    pages = []
    for doc in docs:
        pages += list(document_pages(doc) or [])
    return pages


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
    layout = str(page.get("layout", ""))
    is_social = layout.startswith(SOCIAL_PREFIX)
    where = f"page {index + 1} ({page.get('layout')})"

    # Field-specific structural checks stay on TOP-LEVEL fields. The word caps
    # are tuned per field for feed legibility; applying them to nested deck body
    # prose would misjudge it.
    for field, value in content.items():
        if field in NON_TEXT_FIELDS:
            continue
        text = _plain(value)
        if not text:
            continue
        # Middot rationing is a FEED-LEGIBILITY rule, so it stays social-only even
        # though the other copy checks widened to every layout. On a social overlay
        # a dotted strip is noise; on a wide email header or a 1920x1080 deck column
        # a 3- or 4-part dotted chain is a deliberate, legible idiom. Widening this
        # one flagged two committed on-brand exemplars (email-header `sub`, columns
        # `spirit`), which means the rule was wrong, not the exemplars.
        if is_social and text.count("·") > 1:
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
    for field in ("eyebrow", "foot"):
        text = _plain(content.get(field))
        if text and _DECOR_STRIP.match(text):
            violations.append({"code": "decoration-strip",
                               "detail": f"{where}: {text!r} in {field!r}"})

    # Vocabulary over every string, nested included.
    for path, raw in _walk_strings(content):
        text = _TAGS.sub("", raw).strip()
        if not text:
            continue
        for code, pattern in (*_VOCAB.items(), *VI_VOCAB.items()):
            hit = pattern.search(text)
            if hit:
                violations.append({"code": code,
                                   "detail": f"{where}: {hit.group(0)!r} in {path!r}"})
    return violations


def lint_pages(docs):
    """Per-page copy checks across EVERY layout. Advisory, never blocking."""
    pages = _all_pages(docs)
    violations = []
    for i, page in enumerate(pages):
        violations += _lint_page(i, page)
    return {"passed": not violations, "violations": violations, "pages": len(pages)}


def lint_batch(docs):
    """Repetition checks across the social- pages of one campaign batch.

    Per-page copy checks are NOT repeated here; they live in lint_pages, which
    covers every layout. Advisory, never blocking.
    """
    pages = _social_pages(docs)
    violations = []
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
    assert lint_pages([clean])["passed"], lint_pages([clean])
    assert lint_pages([clean])["pages"] == 4

    # A deck is out of scope for REPETITION even when it repeats a layout, but its
    # pages are in scope for copy checks.
    deck = {"meta": {"format": "deck-16x9"}, "pages": [
        {"layout": "stat-grid", "content": {"title": "A", "stats": []}},
        {"layout": "stat-grid", "content": {"title": "B", "stats": []}},
    ]}
    assert lint_batch([deck]) == {"passed": True, "violations": [], "posts": 0}
    assert lint_pages([deck]) == {"passed": True, "violations": [], "pages": 2}

    # Every per-page check fires, on social layouts.
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
    page_codes = {v["code"] for v in lint_pages([bad])["violations"]}
    assert page_codes == {"numbered-eyebrow", "headline-too-long", "sub-too-long",
                          "quote-too-long", "version-label", "middot-spam"}, page_codes
    batch_codes = {v["code"] for v in lint_batch([bad])["violations"]}
    assert batch_codes == {"layout-repeat-adjacent", "layout-monotony",
                           "eyebrow-overuse"}, batch_codes

    # Vocabulary tells fire on a DECK, including inside nested cards.
    vocab_bad = {"meta": {"format": "deck-16x9"}, "pages": [
        {"layout": "icon-cards", "content": {
            "title": "Seamless care",
            "eyebrow": "BRAND. MOTION. SPATIAL.",
            "cards": [{"title": "Jane Doe", "body": "We elevate outcomes by 99.99%."},
                      {"title": "Field notes", "body": "Quietly trusted by clinics."}]}}]}
    vocab_codes = {v["code"] for v in lint_pages([vocab_bad])["violations"]}
    assert vocab_codes == {"filler-verb", "placeholder-text", "fake-precise-number",
                           "decoration-strip", "poetic-label",
                           "coy-social-proof"}, vocab_codes
    # The nested hit is reported with its path, not swallowed.
    nested = [v for v in lint_pages([vocab_bad])["violations"] if v["code"] == "placeholder-text"]
    assert nested and "cards[0].title" in nested[0]["detail"], nested

    # Middot rationing stays social-only. A multi-part dotted strip is the correct
    # compact idiom on a wide email header (event, topic, date) and in a deck
    # column (a role or process chain), so neither shape may fire.
    dotted = {"meta": {"format": "deck-16x9"}, "pages": [
        {"layout": "email-header", "content": {
            "headline": "Second session",
            "sub": "Session two · Programme overview · 12 March"}},
        {"layout": "columns", "content": {
            "title": "How it works",
            "spirit": "We coordinate · You lead · They share · Partners enable"}},
    ]}
    assert lint_pages([dotted])["passed"], lint_pages([dotted])
    # ...but the same shape on a social overlay is still noise.
    assert {v["code"] for v in lint_pages([{"meta": {"format": "square"}, "pages": [
        {"layout": "social-hero", "content": {"headline": "Open", "foot": "A · B · C"}}]}])[
        "violations"]} == {"middot-spam"}

    # Narrowed patterns do NOT fire on legitimate clinical / fellowship copy.
    ok_words = {"meta": {"format": "deck-16x9"}, "pages": [
        {"layout": "hero", "content": {"title": "Elevated blood pressure, caught early"}},
        {"layout": "hero", "content": {"title": "The next generation of care leaders"}},
    ]}
    assert lint_pages([ok_words])["passed"], lint_pages([ok_words])

    # A batch split across documents grades like one document.
    split = [{"meta": {"format": "square"}, "pages": [p]} for p in clean["pages"]]
    assert lint_batch(split) == lint_batch([clean])
    assert lint_pages(split) == lint_pages([clean])
    print("variety_lint self-check ok")
