import re
from pathlib import Path

from visgen.html_render import build_env

DOC_SKILL = Path(__file__).resolve().parents[2] / ".claude/skills/generate-doc"


def test_document_css_has_no_literal_hex():
    """Brand values live only in tokens.json; document.css must be all var() refs."""
    css = (DOC_SKILL / "assets/document.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert re.findall(r"#[0-9a-fA-F]{3,6}\b", css) == []


def test_covers_and_base_exist():
    assert (DOC_SKILL / "templates/base.html.j2").is_file()
    assert (DOC_SKILL / "templates/partials/cover-report.html.j2").is_file()
    assert (DOC_SKILL / "templates/partials/cover-handbook.html.j2").is_file()


def _render(meta):
    env = build_env(DOC_SKILL / "templates")
    return env.get_template("base.html.j2").render(
        meta=meta,
        body_html='<h1 id="s">Sec</h1><p>Body.</p>',
        toc_html='<div class="toc"><ul><li><a href="#s">Sec</a></li></ul></div>',
        brand_css="/*brand*/", document_css="/*doc*/",
        pagedjs_js="/*PAGEDJS*/", logo="<svg id='logo'></svg>")


def test_base_report_has_cover_toc_body_pagedjs():
    html = _render({"template": "report", "title": "My Report", "lang": "en"})
    assert "cover-report" in html
    assert 'class="toc-page"' in html
    assert "Contents" in html
    assert '<main class="report">' in html and "Sec" in html
    assert "/*PAGEDJS*/" in html            # Paged.js inlined
    assert "__PAGED_DONE" in html           # completion flag wired
    assert "My Report" in html


def test_base_handbook_selects_handbook_cover_and_lang():
    html = _render({"template": "handbook", "title": "Fellow Handbook", "lang": "vi"})
    assert "cover-handbook" in html
    assert "Nội dung" in html               # Vietnamese "Contents"
    assert 'class="doc handbook' in html
