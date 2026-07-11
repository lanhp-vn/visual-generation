"""Content-data schema for slide documents. Validation only — no rendering.
Facts live here; brand/styling never does."""

from visgen.formats import FORMATS

VALID_FORMATS = set(FORMATS)

VALID_THEMES = {"light", "dark"}

# layout name -> required keys in its `content` object
LAYOUTS = {
    # Donor deck layouts (original set; kept untouched).
    "title": ["title", "subtitle_vi", "subtitle_en", "footer"],
    "gaps-bridge": ["title", "gaps", "bridge"],
    "pillars-tiers": ["title", "pillars", "tiers"],
    "impact-roi": ["title", "stats", "flow"],
    "donor-tiers": ["title", "tiers", "footer"],
    "one-pager-3col": ["header", "gaps", "bridge", "impacts"],
    # Event deck layouts (light + dark capable).
    "hero": ["title"],
    "stat-grid": ["title", "stats"],
    "agenda": ["title", "items"],
    "icon-cards": ["title", "cards"],
    "people": ["title", "people"],
    "timeline-phases": ["title", "phases"],
    "columns": ["title", "columns"],
    "cta-qr": ["title", "blocks", "qr"],
    "quote": ["quote"],
    "section-divider": ["title"],
    # Freeform escape hatch: a non-empty list of typed blocks.
    "freeform": ["blocks"],
    # Social-post layouts (M3): one message per canvas, feed-legible.
    "social-hero": ["headline"],          # optional sub, photo, qr, cta
    "social-quote": ["quote"],            # optional attribution, photo
    "social-stat": ["stat", "label"],
    "social-announce": ["headline", "detail"],
    "social-cta": ["headline", "cta"],    # optional qr
    # Poster / banner / email-header layouts (M4): denser hierarchy than social.
    "poster-event": ["title", "when", "where"],   # optional qr, photo, details
    "banner-headline": ["headline"],              # optional sub, cta
    "email-header": ["headline"],                 # optional sub
}


class SchemaError(Exception):
    pass


def document_pages(doc: dict) -> list:
    """The pages list; accepts the legacy cat-canh 'slides' key as an alias."""
    return doc.get("pages", doc.get("slides"))


def validate_document(doc: dict) -> None:
    if not isinstance(doc, dict):
        raise SchemaError("document must be an object")
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        raise SchemaError("missing 'meta' object")
    fmt = meta.get("format")
    if fmt not in VALID_FORMATS:
        raise SchemaError(f"meta.format must be one of {sorted(VALID_FORMATS)}, got {fmt!r}")
    theme = meta.get("theme", "light")
    if theme not in VALID_THEMES:
        raise SchemaError(f"meta.theme must be one of {sorted(VALID_THEMES)}, got {theme!r}")
    if "decor" in meta and not isinstance(meta["decor"], bool):
        raise SchemaError(f"meta.decor must be a boolean, got {type(meta['decor']).__name__}")
    slides = document_pages(doc)
    if not isinstance(slides, list) or not slides:
        raise SchemaError("'pages' (or legacy 'slides') must be a non-empty list")
    for i, slide in enumerate(slides):
        layout = slide.get("layout")
        if layout not in LAYOUTS:
            raise SchemaError(f"slide {i}: unknown layout {layout!r}")
        content = slide.get("content")
        if not isinstance(content, dict):
            raise SchemaError(f"slide {i}: missing 'content' object")
        for key in LAYOUTS[layout]:
            if key not in content:
                raise SchemaError(f"slide {i} ({layout}): missing required field {key!r}")
        if layout == "freeform":
            blocks = content.get("blocks")
            if not isinstance(blocks, list) or not blocks:
                raise SchemaError(f"slide {i} (freeform): 'blocks' must be a non-empty list")


# --- Document front-matter (generate-doc) -------------------------------------
DOC_TEMPLATES = {"report", "handbook"}
DOC_LANGS = {"en", "vi"}


def validate_frontmatter(meta: dict) -> None:
    """Validate a document's YAML front-matter. Facts/styling never live here;
    this only checks the template family, a title, and the language code."""
    if not isinstance(meta, dict):
        raise SchemaError("front-matter must be a mapping")
    template = meta.get("template")
    if template not in DOC_TEMPLATES:
        raise SchemaError(
            f"front-matter 'template' must be one of {sorted(DOC_TEMPLATES)}, got {template!r}")
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SchemaError("front-matter 'title' is required and must be a non-empty string")
    lang = meta.get("lang", "en")
    if lang not in DOC_LANGS:
        raise SchemaError(f"front-matter 'lang' must be one of {sorted(DOC_LANGS)}, got {lang!r}")
