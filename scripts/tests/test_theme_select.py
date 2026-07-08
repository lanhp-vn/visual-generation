"""Theme token-contract tests.

Both themes (light, dark) must define the same core event-deck tokens by name so a
single layout/component renders under either theme. The renderer wiring (Task 2)
selects which theme to inline; this test only asserts both themes parse and define
the shared token contract.
"""

from visgen.html_render import DEFAULT_SKILL_DIR, _theme_css

CORE = ["--heading", "--text", "--box", "--line", "--green", "--gold-fill", "--bg-grad", "--dot"]

# A minimal slide using an EXISTING layout (`title`) so these tests do not depend
# on the not-yet-built event layouts (e.g. `hero`). The renderer change under test
# selects the theme CSS and theme-aware logo regardless of which layout is used.
_TITLE_CONTENT = {
    "title": "Cất Cánh",
    "subtitle_vi": "Học bổng Cất Cánh",
    "subtitle_en": "Takeoff Fellowship",
    "footer": "VISEMI Foundation",
}


def _doc(meta_extra=None):
    return {
        "meta": {**{"format": "deck-16x9", "lang": "vi", "title": "t"}, **(meta_extra or {})},
        "slides": [{"layout": "title", "content": _TITLE_CONTENT}],
    }


def test_both_themes_define_core_tokens():
    for theme in ["light", "dark"]:
        css = _theme_css(theme, DEFAULT_SKILL_DIR)
        for tok in CORE:
            assert f"{tok}:" in css, f"{theme} missing {tok}"


def test_dark_theme_inlines_dark_css():
    from visgen.html_render import render_document
    html = render_document(_doc({"theme": "dark"}))
    assert "#000B26" in html  # dark bg token value present -> dark theme inlined
    # #F3F7FF is the light-only --bg-grad mid-stop; it must be absent under dark.
    assert "#F3F7FF" not in html


def test_light_is_default():
    from visgen.html_render import render_document
    html = render_document(_doc())  # no theme -> default light
    assert "#F3F7FF" in html  # light-only bg token value present -> light theme inlined
    # The dark --bg-grad opening stop #00091F is dark-only; it must be absent under light.
    assert "#00091F" not in html


class _SpyTemplate:
    """Wrap a Jinja template so render() kwargs can be inspected."""

    def __init__(self, real, sink):
        self._real = real
        self._sink = sink

    def render(self, **kw):
        self._sink.update(kw)
        return self._real.render(**kw)


def _render_capturing_layout_kwargs(doc, monkeypatch):
    """Render `doc` and return the kwargs the renderer handed to the layout template."""
    from visgen import html_render

    captured = {}
    real_build_env = html_render.build_env

    def spy_build_env(templates_dir):
        env = real_build_env(templates_dir)
        real_get = env.get_template

        def patched(name):
            tmpl = real_get(name)
            return _SpyTemplate(tmpl, captured) if name.startswith("layouts/") else tmpl

        env.get_template = patched
        return env

    monkeypatch.setattr(html_render, "build_env", spy_build_env)
    html_render.render_document(doc)
    return captured


def test_theme_aware_logo_passed_to_templates(monkeypatch):
    """The renderer passes the white logo on dark and the color logo on light as
    `logo`. Asserted at the wiring level because the bundled `title` layout still
    references logo_color directly."""
    dark = _render_capturing_layout_kwargs(_doc({"theme": "dark"}), monkeypatch)
    assert dark["logo"] == dark["logo_white"]
    assert dark["decor"] is True

    light = _render_capturing_layout_kwargs(_doc(), monkeypatch)  # default light
    assert light["logo"] == light["logo_color"]


def test_decor_meta_overrides_to_false(monkeypatch):
    captured = _render_capturing_layout_kwargs(_doc({"decor": False}), monkeypatch)
    assert captured["decor"] is False
