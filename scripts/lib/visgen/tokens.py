"""Brand tokens: the single source of truth is <active brand>/tokens.json
(resolved via visgen.brand.active_brand_dir, so a working repo can inject its own
theme). This module turns it into per-theme :root CSS (consumed live by
html_render and written to <brand>/generated/) and into the lint palette
allowlist, so theme and lint can never drift apart."""
import json
import re
from functools import lru_cache
from pathlib import Path

from visgen.brand import active_brand_dir

_HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")


@lru_cache(maxsize=8)
def _load(brand_dir: str) -> dict:
    return json.loads((Path(brand_dir) / "tokens.json").read_text(encoding="utf-8"))


def load_tokens() -> dict:
    return _load(str(active_brand_dir()))


def theme_css(theme: str) -> str:
    themes = load_tokens()["themes"]
    if theme not in themes:
        raise KeyError(f"unknown theme {theme!r}; known: {sorted(themes)}")
    decls = "".join(f"{k}:{v};" for k, v in themes[theme].items())
    return ":root{" + decls + "}"


def palette() -> set[str]:
    t = load_tokens()
    hexes = {h.lower() for h in t.get("extra_allowed_hexes", [])}
    for theme in t["themes"].values():
        for value in theme.values():
            hexes.update(h.lower() for h in _HEX.findall(value))
    return hexes


def build_css() -> None:
    out = active_brand_dir() / "generated"
    out.mkdir(exist_ok=True)
    for theme in load_tokens()["themes"]:
        (out / f"tokens-{theme}.css").write_text(theme_css(theme) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_css()
    print(f"wrote generated/tokens-*.css; palette has {len(palette())} hexes")
