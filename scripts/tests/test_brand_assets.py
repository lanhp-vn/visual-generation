import re
from pathlib import Path

BRAND = Path(__file__).resolve().parents[2] / "brand"

def test_fonts_present():
    fonts = sorted(p.name for p in (BRAND / "fonts").glob("*.woff2"))
    assert len(fonts) == 8
    for w in ("400", "500", "600", "700"):
        assert f"be-vietnam-pro-latin-{w}.woff2" in fonts
        assert f"be-vietnam-pro-vietnamese-{w}.woff2" in fonts

def test_logos_present():
    logos = {p.name for p in (BRAND / "logos").iterdir()}
    assert {"visemi-logo-color.svg", "visemi-logo-white.svg", "visemi-mark-320.png"} <= logos

def test_icons_present():
    assert len(list((BRAND / "icons").glob("*.svg"))) >= 15

def test_fonts_css_selfconsistent():
    css = (BRAND / "fonts.css").read_text(encoding="utf-8")
    assert css.count("@font-face") == 8
    for m in re.finditer(r'url\("fonts/([^"]+)"\)', css):
        assert (BRAND / "fonts" / m.group(1)).is_file()
    assert 'url("../' not in css  # paths are brand-relative, not skill-relative
