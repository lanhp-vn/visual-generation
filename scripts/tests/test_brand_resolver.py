import os
from pathlib import Path
from visgen.brand import active_brand_dir, DEFAULT_BRAND


def test_env_override_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("VISGEN_BRAND", str(tmp_path))
    assert active_brand_dir() == tmp_path


def test_cwd_brand_used_when_present(tmp_path, monkeypatch):
    monkeypatch.delenv("VISGEN_BRAND", raising=False)
    (tmp_path / "brand").mkdir()
    (tmp_path / "brand" / "tokens.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert active_brand_dir() == tmp_path / "brand"


def test_defaults_to_submodule_brand(tmp_path, monkeypatch):
    monkeypatch.delenv("VISGEN_BRAND", raising=False)
    monkeypatch.chdir(tmp_path)  # no brand/ here
    assert active_brand_dir() == DEFAULT_BRAND
    assert (DEFAULT_BRAND / "tokens.json").is_file()
