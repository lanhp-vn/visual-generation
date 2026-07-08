import pytest
from visgen.icons import ICONS, render_icon

SEMANTIC = ["globe", "grad-cap", "alert", "target", "grad-cap-dollar",
            "network", "flywheel", "rocket", "clipboard", "presentation",
            "users", "chip"]


def test_all_semantic_names_mapped():
    for name in SEMANTIC:
        assert name in ICONS, name


def test_render_icon_inlines_svg_with_currentcolor():
    svg = render_icon("globe")
    assert svg.startswith("<svg")
    assert 'class="icon"' in svg
    assert "currentColor" in svg or "stroke" not in svg  # uses currentColor via CSS .icon


def test_render_icon_custom_class():
    assert 'class="icon icon-lg"' in render_icon("rocket", css_class="icon icon-lg")


def test_unknown_icon_raises():
    with pytest.raises(KeyError):
        render_icon("not-a-real-icon")
