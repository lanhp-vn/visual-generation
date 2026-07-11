import json
from pathlib import Path
from visgen.brand import active_brand_dir, DEFAULT_BRAND
from visgen.tokens import palette, load_tokens


def _clone_brand(dst: Path):
    src = DEFAULT_BRAND
    (dst / "tokens.json").write_text((src / "tokens.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_injected_brand_changes_palette(tmp_path, monkeypatch):
    _clone_brand(tmp_path)
    t = json.loads((tmp_path / "tokens.json").read_text(encoding="utf-8"))
    t.setdefault("extra_allowed_hexes", []).append("#123456")
    (tmp_path / "tokens.json").write_text(json.dumps(t), encoding="utf-8")
    monkeypatch.setenv("VISGEN_BRAND", str(tmp_path))
    assert active_brand_dir() == tmp_path
    assert "#123456" in palette()           # lint sees the injected brand
    assert "#123456" in {h.lower() for h in palette()}


def test_default_brand_has_no_injected_hex(monkeypatch):
    monkeypatch.delenv("VISGEN_BRAND", raising=False)
    assert "#123456" not in palette()        # falls back to VISEMI default
