from visgen.html_render import (
    render_doc_html, _fonts_and_tokens, _theme_css, DEFAULT_SKILL_DIR,
)


def test_fonts_and_tokens_is_prefix_of_canvas_theme_css():
    """Refactor invariant: canvas _theme_css = _fonts_and_tokens + components.css,
    so canvas rendering is unchanged."""
    ft = _fonts_and_tokens("light")
    full = _theme_css("light", DEFAULT_SKILL_DIR)
    assert full.startswith(ft)
    assert "data:font/woff2;base64," in ft   # fonts embedded
    assert "--navy:#001669;" in ft            # light tokens present


def test_render_doc_html_is_self_contained():
    meta = {"template": "report", "title": "Cohort Report", "lang": "en",
            "subtitle": "Cohort 1", "date": "2026-07-08", "audience": "Partners"}
    body = '<h1 id="ov">Overview</h1><p>Body text.</p>'
    toc = '<div class="toc"><ul><li><a href="#ov">Overview</a></li></ul></div>'
    html = render_doc_html(meta, body, toc)
    # brand + doc CSS inlined
    assert "data:font/woff2;base64," in html      # fonts embedded, offline
    assert "--navy:#001669;" in html              # light theme tokens
    assert "@page" in html                        # document.css inlined
    # Paged.js inlined (no CDN, no external src)
    assert "PagedPolyfill" in html or "Paged" in html
    assert "src=" not in html.split("<main")[0] or "http" not in html  # no external script/CDN
    # structure
    assert "cover-report" in html and "<main class=" in html and "Overview" in html
    assert "__PAGED_DONE" in html


def test_render_doc_html_handbook_cover():
    html = render_doc_html({"template": "handbook", "title": "Fellow Handbook"},
                           "<p>x</p>", "")
    assert "cover-handbook" in html
