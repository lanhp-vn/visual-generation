"""Assemble a canvas document into one HTML string. Validates, renders each
page's layout template, wraps them in the base template with inlined brand CSS.
Theme CSS is assembled from brand/ (single source of truth): embedded fonts +
generated tokens for meta.theme + the skill's tokenised components.css.
Output is html-ppt-compatible (<div class="deck"> wrapping <section class="slide">)."""
import base64
import re
from pathlib import Path
import jinja2

from visgen.schema import validate_document, document_pages
from visgen.formats import page_px
from visgen.tokens import BRAND_DIR, theme_css as tokens_css
from visgen.icons import render_icon
from visgen.qr import qr_svg

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SKILL_DIR = REPO_ROOT / ".claude/skills/generate-slides"
DEFAULT_DOC_SKILL_DIR = REPO_ROOT / ".claude/skills/generate-doc"
_PAGEDJS = Path(__file__).resolve().parent / "vendor/paged.polyfill.js"

_FONT_URL = re.compile(r'url\(\s*["\']?(?:\.\./)?fonts/([^"\')]+)["\']?\s*\)')


def build_env(templates_dir: Path) -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        autoescape=jinja2.select_autoescape(["html", "j2"]),
    )
    env.globals["icon"] = render_icon
    env.globals["qr_svg"] = qr_svg
    return env


def _embed_fonts(css: str) -> str:
    """Replace url("fonts/x.woff2") with a base64 data URI so the inlined CSS is
    self-contained — renders deterministically offline, wherever the file lives."""
    def repl(m):
        data = (BRAND_DIR / "fonts" / m.group(1)).read_bytes()
        b64 = base64.standard_b64encode(data).decode("ascii")
        return f'url("data:font/woff2;base64,{b64}")'
    return _FONT_URL.sub(repl, css)


def _fonts_and_tokens(theme: str) -> str:
    """Shared brand CSS both renderers build on: base64-embedded Be Vietnam Pro
    (offline-deterministic) + the generated :root token block for `theme`."""
    fonts = _embed_fonts((BRAND_DIR / "fonts.css").read_text(encoding="utf-8"))
    return "\n".join([fonts, tokens_css(theme)])


def _theme_css(theme: str, skill_dir: Path) -> str:
    components = (skill_dir / "assets/components.css").read_text(encoding="utf-8")
    return "\n".join([_fonts_and_tokens(theme), components])


def render_document(doc: dict, skill_dir: Path | None = None) -> str:
    validate_document(doc)
    skill_dir = skill_dir or DEFAULT_SKILL_DIR
    env = build_env(skill_dir / "templates")
    meta = doc["meta"]
    page_w, page_h = page_px(meta["format"])
    base_css = (skill_dir / "assets/base.css").read_text(encoding="utf-8")

    theme = meta.get("theme", "light")
    theme_css = _theme_css(theme, skill_dir)

    logo_color = (BRAND_DIR / "logos/visemi-logo-color.svg").read_text(encoding="utf-8")
    logo_white = (BRAND_DIR / "logos/visemi-logo-white.svg").read_text(encoding="utf-8")
    active_logo = logo_white if theme == "dark" else logo_color

    decor = meta.get("decor", True)

    slides_html = []
    for i, page in enumerate(document_pages(doc), start=1):
        tmpl = env.get_template(f"layouts/{page['layout']}.html.j2")
        content = page["content"]
        qr_markup = None
        qr = content.get("qr") if isinstance(content, dict) else None
        if (page["layout"] == "cta-qr" or qr) and isinstance(qr, dict) and qr.get("url"):
            qr_markup = qr_svg(qr["url"])
        slides_html.append(tmpl.render(
            c=content, meta=meta, page_num=i,
            logo=active_logo, logo_color=logo_color, logo_white=logo_white,
            decor=decor, page_w=page_w, page_h=page_h,
            qr_svg_markup=qr_markup,
        ))

    base = env.get_template("base.html.j2")
    return base.render(meta=meta, slides_html=slides_html,
                       base_css=base_css, theme_css=theme_css,
                       decor=decor, page_w=page_w, page_h=page_h)


def render_doc_html(meta: dict, body_html: str, toc_html: str,
                    lead_html: str = "", skill_dir: Path | None = None) -> str:
    """Assemble a document (front-matter + converted Markdown) into one
    self-contained HTML string: inlined brand CSS (light theme) + the skill's
    document.css + the vendored Paged.js polyfill, wrapped in the doc base
    template with the template-specific cover. Docs are light-theme only.

    lead_html (optional) is rendered inside <main> BEFORE the auto TOC - the doc's
    content ahead of the `<!-- TOC -->` marker (see document.render_doc). Any
    meta['partner_logos'] paths are inlined (SVG as markup, raster as a base64
    data URI) and passed to the cover as `partner_logos`, keeping output
    self-contained. meta['cover_bg_logo'] (optional, one path) is loaded the
    same way but always as a base64 data URI (even for SVG), since it is used
    as a single CSS background-image rather than inline markup. Other optional
    cover fields (tagline, founders, organizer, sponsors, cover_stats) are read
    straight from meta by the cover template."""
    skill_dir = skill_dir or DEFAULT_DOC_SKILL_DIR
    env = build_env(skill_dir / "templates")
    brand_css = _fonts_and_tokens("light")
    document_css = (skill_dir / "assets/document.css").read_text(encoding="utf-8")
    pagedjs_js = _PAGEDJS.read_text(encoding="utf-8")
    logo = (BRAND_DIR / "logos/visemi-logo-color.svg").read_text(encoding="utf-8")
    partner_logos = _load_partner_logos(meta.get("partner_logos") or [])
    bg_logo = _load_data_uri(meta.get("cover_bg_logo"))
    base = env.get_template("base.html.j2")
    return base.render(meta=meta, body_html=body_html, toc_html=toc_html,
                       lead_html=lead_html, brand_css=brand_css, document_css=document_css,
                       pagedjs_js=pagedjs_js, logo=logo, partner_logos=partner_logos,
                       bg_logo=bg_logo)


def _load_data_uri(rel: str | None) -> str | None:
    """Load an optional single image path (meta.cover_bg_logo) as a base64 data
    URI, for use as a CSS background-image - unlike _load_partner_logos (inline
    markup), a background-image needs one URL, so SVGs are also base64-encoded
    rather than inlined raw. Path is absolute or repo-root-relative; None if unset
    or missing."""
    import mimetypes
    if not rel:
        return None
    p = Path(rel)
    if not p.is_absolute():
        p = REPO_ROOT / rel
    if not p.exists():
        return None
    mime = "image/svg+xml" if p.suffix.lower() == ".svg" else (mimetypes.guess_type(p.name)[0] or "image/png")
    b64 = base64.standard_b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _load_partner_logos(paths) -> list[str]:
    """Inline each partner/sponsor logo path (from meta.partner_logos) as HTML:
    .svg files inline as markup, raster files as a base64 data-URI <img>. Paths are
    absolute or repo-root-relative. Keeps the rendered HTML self-contained."""
    import mimetypes
    out = []
    for rel in paths:
        p = Path(rel)
        if not p.is_absolute():
            p = REPO_ROOT / rel
        if not p.exists():
            continue
        if p.suffix.lower() == ".svg":
            out.append(p.read_text(encoding="utf-8"))
        else:
            mime = mimetypes.guess_type(p.name)[0] or "image/png"
            b64 = base64.standard_b64encode(p.read_bytes()).decode("ascii")
            out.append(f'<img src="data:{mime};base64,{b64}" alt="partner logo">')
    return out
