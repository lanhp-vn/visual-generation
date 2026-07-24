"""The brand contract owns the logo filenames, not the engine.

Hardcoding visemi-logo-*.svg in html_render meant every consuming brand had to
ship VISEMI-named files. The names now come from tokens.json's optional `logos`
group, defaulting to the studio's own so existing brands keep working.
"""
import json
from pathlib import Path

from visgen.brand import DEFAULT_BRAND
from visgen.tokens import logo_paths


def _brand(tmp_path: Path, tokens: dict) -> Path:
    b = tmp_path / "brand"
    b.mkdir()
    (b / "tokens.json").write_text(json.dumps(tokens), encoding="utf-8")
    return b


def test_defaults_to_the_studio_filenames(tmp_path, monkeypatch):
    """A brand silent about logos keeps the studio names, so every brand
    override that predates the `logos` group needs no change."""
    b = _brand(tmp_path, {"themes": {}})
    monkeypatch.setenv("VISGEN_BRAND", str(b))
    paths = logo_paths()
    assert paths["color"] == b / "logos" / "visemi-logo-color.svg"
    assert paths["white"] == b / "logos" / "visemi-logo-white.svg"


def test_logos_group_overrides_the_filenames(tmp_path, monkeypatch):
    b = _brand(tmp_path, {"themes": {}, "logos": {
        "color": "logos/nouslogic-telehealth-logo.svg",
        "white": "logos/nouslogic-telehealth-logo-dark.svg",
    }})
    monkeypatch.setenv("VISGEN_BRAND", str(b))
    paths = logo_paths()
    assert paths["color"] == b / "logos" / "nouslogic-telehealth-logo.svg"
    assert paths["white"] == b / "logos" / "nouslogic-telehealth-logo-dark.svg"


def test_partial_override_falls_back_per_key(tmp_path, monkeypatch):
    """Naming one colourway must not silently lose the other."""
    b = _brand(tmp_path, {"themes": {}, "logos": {"color": "logos/only-color.svg"}})
    monkeypatch.setenv("VISGEN_BRAND", str(b))
    paths = logo_paths()
    assert paths["color"] == b / "logos" / "only-color.svg"
    assert paths["white"] == b / "logos" / "visemi-logo-white.svg"


def test_the_studio_default_points_at_real_files(monkeypatch):
    """The fallback must actually exist, not merely resolve to a path."""
    monkeypatch.setenv("VISGEN_BRAND", str(DEFAULT_BRAND))
    for role, p in logo_paths().items():
        assert p.is_file(), f"studio brand is missing its {role} logo: {p}"
