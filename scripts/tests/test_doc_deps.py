import importlib
from pathlib import Path

VENDOR = Path(__file__).resolve().parents[2] / "scripts/lib/visgen/vendor"


def test_markdown_yaml_pypdf_importable():
    for mod in ("markdown", "yaml", "pypdf"):
        importlib.import_module(mod)


def test_pagedjs_polyfill_vendored():
    f = VENDOR / "paged.polyfill.js"
    assert f.is_file(), "paged.polyfill.js must be vendored (no CDN)"
    text = f.read_text(encoding="utf-8")
    assert len(text) > 100_000, "expected the full ~400KB polyfill, not a stub"
    assert "Paged" in text  # sanity: it is the Paged.js polyfill


def test_pagedjs_license_recorded():
    lic = VENDOR / "THIRD_PARTY_LICENSES"
    assert lic.is_file()
    body = lic.read_text(encoding="utf-8").lower()
    assert "pagedjs" in body or "paged.js" in body
    assert "mit" in body
