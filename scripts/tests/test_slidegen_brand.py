from visgen.html_render import DEFAULT_SKILL_DIR, _theme_css
from visgen.brand import active_brand_dir

ASSETS = DEFAULT_SKILL_DIR / "assets"
BRAND_DIR = active_brand_dir()


def test_package_imports():
    import visgen  # noqa: F401


def test_visemi_theme_has_core_tokens():
    # themes are assembled (Task 6 _theme_css), not vendored as a static file
    css = _theme_css("light", DEFAULT_SKILL_DIR)
    for token in ("#001669", "#262538", "#01B68B", "#F6F6F6", "#00E5FF", "#717171"):
        assert token in css, token
    assert "Be Vietnam Pro" in css
    assert "@font-face" in css
    assert "--accent" in css and "--navy" in css  # html-ppt tokens + our aliases


def test_html_ppt_assets_vendored():
    assert (ASSETS / "base.css").is_file()
    assert (ASSETS / "runtime.js").is_file()
    assert (ASSETS / "THIRD_PARTY_LICENSES").is_file()


def test_fonts_vendored():
    # fonts are the shared brand/ source, not vendored per-skill
    fonts = list((BRAND_DIR / "fonts").glob("*.woff2"))
    assert len(fonts) >= 8, [f.name for f in fonts]


def test_logos_present():
    # logos are the shared brand/ source, not vendored per-skill
    for name in ("visemi-logo-color.svg", "visemi-logo-white.svg", "visemi-mark-320.png"):
        assert (BRAND_DIR / "logos" / name).is_file(), name
