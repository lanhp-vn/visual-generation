"""One-time port helper: extract the :root token blocks from the frozen cat-canh
theme CSS fixtures into brand/tokens.json. Kept so the port is reproducible and
so tests can reuse parse_root_block()."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "scripts/tests/fixtures/themes"


def parse_root_block(css: str) -> dict:
    m = re.search(r"^:root\{(.*?)^\}", css, re.S | re.M)
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    return {m.group(1): re.sub(r"\s+", " ", m.group(2)).strip()
            for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", body)}


def main():
    light = parse_root_block((FIX / "visemi.css").read_text(encoding="utf-8"))
    dark = parse_root_block((FIX / "visemi-dark.css").read_text(encoding="utf-8"))
    # Two divergences in the old helper-class sections become tokens so ONE shared
    # components.css can serve both themes (see Task 9):
    light["--body"] = light["--purple"]  # old light body color: var(--purple)
    dark["--body"] = dark["--text"]      # old dark body color: var(--text)
    light["--num-bg"] = light["--navy"]  # .agenda-item .n background on light
    dark["--num-bg"] = dark["--green"]   # ... and on dark
    tokens = {
        "font_stack": '"Be Vietnam Pro",Inter,sans-serif',
        "type_scale": {"display-2xl": 76, "display-xl": 60, "display-lg": 48,
                       "display-md": 38, "display-sm": 30, "display-xs": 25,
                       "text-xl": 20, "text-lg": 18, "text-md": 16,
                       "text-sm": 14, "text-xs": 12},
        "extra_allowed_hexes": ["#000000", "#FFFFFF", "#000", "#FFF"],
        "themes": {"light": light, "dark": dark},
    }
    out = ROOT / "brand/tokens.json"
    out.write_text(json.dumps(tokens, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(light)} light / {len(dark)} dark tokens)")


if __name__ == "__main__":
    main()
