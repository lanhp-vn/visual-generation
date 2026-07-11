import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/util"))
from extract_tokens import parse_root_block, FIX
from visgen.tokens import load_tokens, theme_css, palette, build_css

# The exact allowlist cat-canh's brand_lint.py hardcoded — palette() must not regress it.
CATCANH_BRAND_HEX = {h.lower() for h in [
    "#001669", "#262538", "#01B68B", "#019974", "#FFFFFF", "#F6F6F6", "#00E5FF",
    "#717171", "#000F4D", "#001259", "#4D6299", "#99A8C9", "#CCD4E4",
    "#1A1929", "#6B6A7D", "#A9A8B5", "#D4D4DA", "#018A6A", "#019578",
    "#4DD4AF", "#99E5CF", "#CCF2E7", "#000000", "#FFF", "#000",
    "#F5B433", "#D99A1F", "#FBD27A",
    "#000B26", "#001152", "#00091F", "#0D2156", "#0A2470",
    "#EAF0FF", "#B9C4E0", "#8FA0C8",
    "#33405E", "#5C6B92", "#8190B4", "#EAF1FF", "#E5EEFF", "#F3F7FF", "#EAF7F1",
]}

def test_roundtrip_every_original_token():
    """Every :root declaration in the frozen originals survives into theme_css()."""
    for name, fixture in (("light", "visemi.css"), ("dark", "visemi-dark.css")):
        original = parse_root_block((FIX / fixture).read_text(encoding="utf-8"))
        generated = theme_css(name)
        for prop, value in original.items():
            assert f"{prop}:{value};" in generated, f"{name} lost {prop}"

def test_new_shared_component_tokens():
    t = load_tokens()["themes"]
    for theme in ("light", "dark"):
        assert "--body" in t[theme] and "--num-bg" in t[theme]
    assert t["light"]["--num-bg"].startswith("#")

def test_palette_superset_of_catcanh_allowlist():
    assert CATCANH_BRAND_HEX <= palette()

def test_build_css_writes_both_themes(tmp_path):
    build_css()
    root = Path(__file__).resolve().parents[2]
    for theme in ("light", "dark"):
        f = root / "brand/generated" / f"tokens-{theme}.css"
        assert f.is_file() and f.read_text(encoding="utf-8").startswith(":root{")

def test_components_css_has_no_literal_hex():
    """Brand values live only in tokens.json; component CSS must be all var() refs."""
    import re
    root = Path(__file__).resolve().parents[2]
    css = (root / "skills/generate-slides/assets/components.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert re.findall(r"#[0-9a-fA-F]{3,6}\b", css) == []
