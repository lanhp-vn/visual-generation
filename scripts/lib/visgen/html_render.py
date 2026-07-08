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


def _theme_css(theme: str, skill_dir: Path) -> str:
    fonts = _embed_fonts((BRAND_DIR / "fonts.css").read_text(encoding="utf-8"))
    components = (skill_dir / "assets/components.css").read_text(encoding="utf-8")
    return "\n".join([fonts, tokens_css(theme), components])


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
