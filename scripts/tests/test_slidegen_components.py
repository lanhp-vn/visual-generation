import jinja2
from visgen.html_render import DEFAULT_SKILL_DIR
from visgen.icons import render_icon


def _env():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(DEFAULT_SKILL_DIR / "templates")),
                             autoescape=True)
    env.globals["icon"] = render_icon
    return env


def _macros():
    return _env().get_template("components.html.j2").module


def test_icon_list_item_renders_lead_and_body():
    out = _macros().icon_list_item({"icon": "globe", "lead": "Talent Gap", "body": "shortage"})
    assert "Talent Gap" in out and "shortage" in out and "<svg" in out


def test_stat_card_renders_number_and_label():
    out = _macros().stat_card({"variant": "navy", "number": "15",
                               "label": "Fellows Funded", "bullets": ["80%+"]})
    assert "15" in out and "Fellows Funded" in out and "80%+" in out


def test_tier_banner_variant_class():
    out = _macros().tier_banner({"variant": "green", "title": "Tier 2", "body": "x"})
    assert "tier-green" in out and "Tier 2" in out


def test_placeholder_has_label():
    out = _macros().placeholder("QR code", 180, 180)
    assert "QR code" in out
