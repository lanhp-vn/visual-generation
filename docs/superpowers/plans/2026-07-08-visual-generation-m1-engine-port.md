# Visual Generation M1 — Engine Port + Brand Tokens + generate-slides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the shared visual-generation engine in this repo — `brand/` tokens as single source of truth, the ported+generalized canvas renderer with a formats registry, brand-lint whose palette derives from the tokens, the `generate-slides` skill, and the eval harness — proven by all four cat-canh reference exemplars rendering and passing lint here.

**Architecture:** Port `scripts/lib/slidegen/` from `D:\2-VISEMI\cat-canh-program-management` into `scripts/lib/visgen/`, generalizing three things: page size comes from a formats registry (not a hardcoded 1920×1080 pair), brand assets/tokens come from a repo-level `brand/` directory (not skill-vendored theme CSS), and the document accepts `pages` with `slides` as a back-compat alias. Everything else ports with import/path updates only.

**Tech Stack:** Python ≥3.12 via `uv`, Jinja2, Playwright (chromium), segno, anthropic (rubric judge only), pytest.

**Spec:** `docs/superpowers/specs/2026-07-08-visual-generation-skills-design.md` (approved). This plan covers Milestone M1 only; M2 (document renderer) gets its own plan after M1 lands.

## Global Constraints

- **Source repo for all ports:** `D:\2-VISEMI\cat-canh-program-management` (call it `$CC` below; in bash: `CC="/d/2-VISEMI/cat-canh-program-management"`). Read-only — never modify it.
- **DRY / Single Source of Truth:** brand values only in `brand/tokens.json`; render/grade logic only in `scripts/lib/visgen/`; schemas only in `schema.py`. No hardcoded hex outside `brand/` (generated files and vendored `base.css` excepted).
- **Brand locked:** palette navy `#001669`, purple `#262538`, green `#01B68B`, white, token ramps, gold `#F5B433` sparing, cyan `#00E5FF` very sparing; Be Vietnam Pro only; no em dash (U+2014), no en dash (U+2013), no emojis; Vietnamese keeps diacritics ("Cất Cánh" never "Cat Canh").
- **Verify by rendering:** nothing is done until it renders `overflow: false` and brand-lint reports `passed: true`.
- **Never commit rendered output** — `output/` is git-ignored.
- Run Python via `uv run`; prefix commands printing Vietnamese with `PYTHONIOENCODING=utf-8`.
- Commit after every green test cycle (each task's final step).

---

### Task 1: Repo scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `scripts/tests/conftest.py`

**Interfaces:**
- Produces: a working `uv` environment with jinja2/playwright/segno/anthropic/pytest; chromium installed; `scripts/tests/` wired to import from `scripts/lib` and `scripts/ops`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "visual-generation"
version = "0.0.0"
description = "VISEMI visual-generation skills: shared engine, brand tokens, evals/graders."
requires-python = ">=3.12"
dependencies = [
    "jinja2",
    "playwright",
    "segno",
    "anthropic",
]

[dependency-groups]
dev = ["pytest"]

[tool.uv]
package = false

[tool.pytest.ini_options]
testpaths = ["scripts/tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-q"
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
output/
__pycache__/
*.pyc
.venv/
scripts/evals/runs/
brand/generated/
```

(`brand/generated/` is build output of `tokens.py` — regenerable, so ignored.)

- [ ] **Step 3: Write `scripts/tests/conftest.py`**

```python
"""Pytest config: put the scripts/ layers on sys.path (same pattern as cat-canh).
Engine modules are imported as `from visgen.x import ...`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for sub in ("lib", "util", "ops"):
    p = ROOT / "scripts" / sub
    if p.is_dir():
        sys.path.insert(0, str(p))
```

- [ ] **Step 4: Install and verify**

Run:
```bash
cd /d/2-VISEMI/visual-generation
uv sync
uv run playwright install chromium
uv run python -c "import jinja2, segno, anthropic; from playwright.sync_api import sync_playwright; print('deps ok')"
```
Expected: `deps ok`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore scripts/tests/conftest.py uv.lock
git commit -m "feat(m1): repo scaffolding — uv project, pytest wiring, gitignore"
```

---

### Task 2: brand/ static assets (fonts, logos, icons, fonts.css)

**Files:**
- Create: `brand/fonts/*.woff2` (8 files), `brand/logos/*` (3+ files), `brand/icons/*.svg` (17 files), `brand/fonts.css`
- Test: `scripts/tests/test_brand_assets.py`

**Interfaces:**
- Produces: `brand/fonts.css` whose `@font-face` rules use `url("fonts/<name>.woff2")` paths; consumed by `html_render._embed_fonts` (Task 6). Icon SVGs consumed by `visgen/icons.py` (Task 5).

- [ ] **Step 1: Write the failing test**

`scripts/tests/test_brand_assets.py`:
```python
import re
from pathlib import Path

BRAND = Path(__file__).resolve().parents[2] / "brand"

def test_fonts_present():
    fonts = sorted(p.name for p in (BRAND / "fonts").glob("*.woff2"))
    assert len(fonts) == 8
    for w in ("400", "500", "600", "700"):
        assert f"be-vietnam-pro-latin-{w}.woff2" in fonts
        assert f"be-vietnam-pro-vietnamese-{w}.woff2" in fonts

def test_logos_present():
    logos = {p.name for p in (BRAND / "logos").iterdir()}
    assert {"visemi-logo-color.svg", "visemi-logo-white.svg", "visemi-mark-320.png"} <= logos

def test_icons_present():
    assert len(list((BRAND / "icons").glob("*.svg"))) >= 17

def test_fonts_css_selfconsistent():
    css = (BRAND / "fonts.css").read_text(encoding="utf-8")
    assert css.count("@font-face") == 8
    for m in re.finditer(r'url\("fonts/([^"]+)"\)', css):
        assert (BRAND / "fonts" / m.group(1)).is_file()
    assert 'url("../' not in css  # paths are brand-relative, not skill-relative
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_brand_assets.py -v`
Expected: FAIL (no `brand/` dir yet)

- [ ] **Step 3: Copy the assets**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
SK="$CC/.claude/skills/generate-slides"
mkdir -p brand/fonts brand/logos brand/icons
cp "$SK"/assets/fonts/*.woff2 brand/fonts/
cp "$SK"/assets/logos/visemi-logo-color.svg "$SK"/assets/logos/visemi-logo-white.svg "$SK"/assets/logos/visemi-mark-320.png brand/logos/
cp "$SK"/assets/icons/*.svg brand/icons/
```

- [ ] **Step 4: Create `brand/fonts.css`**

Extract the `@font-face` block — the lines from the first `@font-face` up to (not including) `:root{` — from `$SK/assets/themes/visemi.css` (lines 6–30), then make paths brand-relative:

```bash
sed -n '/^@font-face/,/^$/p' "$SK/assets/themes/visemi.css" | sed 's|\.\./fonts/|fonts/|g' > brand/fonts.css
```

Verify by eye: 8 `@font-face` rules (400/500/600/700 × latin/vietnamese), all `src:url("fonts/...")`.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest scripts/tests/test_brand_assets.py -v`
Expected: 4 PASS

- [ ] **Step 6: Commit**

```bash
git add brand scripts/tests/test_brand_assets.py
git commit -m "feat(m1): brand/ static assets — Be Vietnam Pro fonts, logos, icon set, fonts.css"
```

---

### Task 3: brand/tokens.json + visgen/tokens.py (single source of truth)

**Files:**
- Create: `scripts/tests/fixtures/themes/visemi.css`, `scripts/tests/fixtures/themes/visemi-dark.css` (frozen originals, test fixtures)
- Create: `scripts/util/extract_tokens.py` (one-time port helper, kept for reproducibility)
- Create: `brand/tokens.json`
- Create: `scripts/lib/visgen/__init__.py` (empty), `scripts/lib/visgen/tokens.py`
- Test: `scripts/tests/test_tokens.py`

**Interfaces:**
- Produces (consumed by Tasks 6, 8):
  - `visgen.tokens.load_tokens() -> dict` — parsed `brand/tokens.json`
  - `visgen.tokens.theme_css(theme: str) -> str` — a `:root{...}` block for `"light"` or `"dark"`
  - `visgen.tokens.palette() -> set[str]` — every lowercased hex appearing in any theme value, plus `extra_allowed_hexes`
  - `visgen.tokens.build_css() -> None` — writes `brand/generated/tokens-{light,dark}.css`
  - `tokens.json` schema: `{"font_stack": str, "type_scale": {name: px}, "extra_allowed_hexes": [str], "themes": {"light": {"--token": "value"}, "dark": {...}}}`

- [ ] **Step 1: Freeze the original theme CSS as fixtures**

```bash
mkdir -p scripts/tests/fixtures/themes scripts/util
cp "$SK/assets/themes/visemi.css" "$SK/assets/themes/visemi-dark.css" scripts/tests/fixtures/themes/
```

- [ ] **Step 2: Write the extraction helper**

`scripts/util/extract_tokens.py`:
```python
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
    light["--body"] = "#262538"          # old light body color: var(--purple)
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
```

- [ ] **Step 3: Generate `brand/tokens.json`**

Run: `uv run python scripts/util/extract_tokens.py`
Expected: `wrote .../brand/tokens.json (~50 light / ~50 dark tokens)`. Open it and spot-check: `--navy: #001669`, `--gold-fill: #F5B433`, `--body` and `--num-bg` present in both themes. Note: `--num-bg` resolves to a var reference value (`light["--navy"]` is the *string* `#001669` because parse resolves declarations literally — verify it is a hex, not `var(...)`; if the source declared `--navy:#001669`, it is `#001669`).

- [ ] **Step 4: Write the failing tests**

`scripts/tests/test_tokens.py`:
```python
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
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `uv run pytest scripts/tests/test_tokens.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'visgen'`

- [ ] **Step 6: Write `scripts/lib/visgen/tokens.py`** (and empty `scripts/lib/visgen/__init__.py`)

```python
"""Brand tokens: the single source of truth is brand/tokens.json. This module
turns it into per-theme :root CSS (consumed live by html_render and written to
brand/generated/ for humans/other tools) and into the lint palette allowlist,
so theme and lint can never drift apart."""
import json
import re
from functools import lru_cache
from pathlib import Path

BRAND_DIR = Path(__file__).resolve().parents[3] / "brand"
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")


@lru_cache(maxsize=1)
def load_tokens() -> dict:
    return json.loads((BRAND_DIR / "tokens.json").read_text(encoding="utf-8"))


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
    out = BRAND_DIR / "generated"
    out.mkdir(exist_ok=True)
    for theme in load_tokens()["themes"]:
        (out / f"tokens-{theme}.css").write_text(theme_css(theme) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_css()
    print(f"wrote brand/generated/tokens-*.css; palette has {len(palette())} hexes")
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/test_tokens.py scripts/tests/test_brand_assets.py -v`
Expected: all PASS. If `test_roundtrip_every_original_token` fails on a whitespace mismatch, normalize the assertion the same way `parse_root_block` normalizes (`re.sub(r"\s+", " ", ...)`) — intent is value equality, not byte equality.

- [ ] **Step 8: Commit**

```bash
git add brand/tokens.json scripts/util/extract_tokens.py scripts/lib/visgen scripts/tests/test_tokens.py scripts/tests/fixtures/themes
git commit -m "feat(m1): brand tokens SSoT — tokens.json + visgen.tokens (theme CSS + lint palette)"
```

---

### Task 4: Formats registry

**Files:**
- Create: `scripts/lib/visgen/formats.py`
- Test: `scripts/tests/test_formats.py`

**Interfaces:**
- Produces (consumed by Tasks 5–10):
  - `visgen.formats.FORMATS: dict[str, tuple[int, int]]`
  - `visgen.formats.page_px(fmt: str) -> tuple[int, int]` — raises `ValueError` naming known formats on unknown key

- [ ] **Step 1: Write the failing test**

`scripts/tests/test_formats.py`:
```python
import pytest
from visgen.formats import FORMATS, page_px

def test_registry_matches_output_specs():
    assert page_px("deck-16x9") == (1920, 1080)
    assert page_px("one-pager-landscape") == (1920, 1080)
    assert page_px("square") == (1080, 1080)
    assert page_px("portrait") == (1080, 1350)
    assert page_px("story") == (1080, 1920)
    assert page_px("link") == (1200, 627)
    assert page_px("poster-a") == (1240, 1748)
    assert page_px("banner-wide") == (2048, 1448)
    assert page_px("email-header") == (1200, 400)
    assert len(FORMATS) == 9

def test_unknown_format_raises_with_known_keys():
    with pytest.raises(ValueError, match="deck-16x9"):
        page_px("a3-poster")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_formats.py -v`
Expected: FAIL with `No module named 'visgen.formats'`

- [ ] **Step 3: Write `scripts/lib/visgen/formats.py`**

```python
"""Canvas formats registry — the sizes from the design kit's output specs
(references/visemi-internal/design-kit-visemi/04-output-specs.md). Every canvas
render resolves its stage size here; nothing else hardcodes pixel dimensions."""

FORMATS = {
    # slides / one-pagers
    "deck-16x9": (1920, 1080),
    "one-pager-landscape": (1920, 1080),
    # social posts
    "square": (1080, 1080),
    "portrait": (1080, 1350),
    "story": (1080, 1920),
    "link": (1200, 627),
    # posters / event graphics
    "poster-a": (1240, 1748),
    "banner-wide": (2048, 1448),
    "email-header": (1200, 400),
}


def page_px(fmt: str) -> tuple[int, int]:
    try:
        return FORMATS[fmt]
    except KeyError:
        raise ValueError(f"unknown format {fmt!r}; known: {sorted(FORMATS)}") from None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest scripts/tests/test_formats.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/visgen/formats.py scripts/tests/test_formats.py
git commit -m "feat(m1): canvas formats registry (9 sizes from design-kit output specs)"
```

---

### Task 5: Port pure engine modules (schema, icons, qr, pngsize) + eval data

**Files:**
- Create: `scripts/lib/visgen/schema.py`, `scripts/lib/visgen/icons.py`, `scripts/lib/visgen/qr.py`, `scripts/lib/visgen/pngsize.py`
- Create: `scripts/evals/references/*` , `scripts/evals/tasks/*` (verbatim data copies)
- Test: ported `scripts/tests/{test_slidegen_schema,test_schema_event_layouts,test_slidegen_icons,test_qr}.py`

**Interfaces:**
- Consumes: `visgen.formats.FORMATS`
- Produces (consumed by Tasks 6–10):
  - `visgen.schema.validate_document(doc: dict) -> None` (raises `SchemaError`); accepts `pages` or legacy `slides` key; `meta.format` validated against the full `FORMATS` registry
  - `visgen.schema.document_pages(doc: dict) -> list` — the one accessor for the pages list (DRY: render + evals use this, never `doc["slides"]` directly)
  - `visgen.icons.render_icon(name, css_class="icon") -> str` reading SVGs from `brand/icons/`
  - `visgen.qr.qr_svg(url) -> str`; `visgen.pngsize.png_size(path) -> tuple`

- [ ] **Step 1: Copy modules and eval data**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
cp "$CC"/scripts/lib/slidegen/{schema.py,icons.py,qr.py,pngsize.py} scripts/lib/visgen/
mkdir -p scripts/evals
cp -r "$CC"/scripts/evals/references "$CC"/scripts/evals/tasks scripts/evals/
```

- [ ] **Step 2: Generalize `schema.py`**

Apply exactly these edits to `scripts/lib/visgen/schema.py`:

Replace:
```python
VALID_FORMATS = {"deck-16x9", "one-pager-landscape"}
```
with:
```python
from visgen.formats import FORMATS

VALID_FORMATS = set(FORMATS)
```

Replace (in `validate_document`):
```python
    slides = doc.get("slides")
    if not isinstance(slides, list) or not slides:
        raise SchemaError("'slides' must be a non-empty list")
    for i, slide in enumerate(slides):
```
with:
```python
    slides = document_pages(doc)
    if not isinstance(slides, list) or not slides:
        raise SchemaError("'pages' (or legacy 'slides') must be a non-empty list")
    for i, slide in enumerate(slides):
```

And add at module level (below `class SchemaError`):
```python
def document_pages(doc: dict) -> list:
    """The pages list; accepts the legacy cat-canh 'slides' key as an alias."""
    return doc.get("pages", doc.get("slides"))
```

- [ ] **Step 3: Repoint `icons.py` at brand/**

In `scripts/lib/visgen/icons.py` replace:
```python
ICONS_DIR = Path(__file__).resolve().parents[3] / ".claude/skills/generate-slides/assets/icons"
```
with:
```python
ICONS_DIR = Path(__file__).resolve().parents[3] / "brand/icons"
```
(`qr.py` and `pngsize.py` need no changes.)

- [ ] **Step 4: Port the four test files**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
for f in test_slidegen_schema test_schema_event_layouts test_slidegen_icons test_qr; do
  sed 's/\bslidegen\b/visgen/g' "$CC/scripts/tests/$f.py" > "scripts/tests/$f.py"
done
```
Then open each ported test; if any references cat-canh paths (e.g. `scripts/evals/tasks/_fixtures/...`), those now exist here from Step 1 — fix only path roots, keep assertions identical.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/test_slidegen_schema.py scripts/tests/test_schema_event_layouts.py scripts/tests/test_slidegen_icons.py scripts/tests/test_qr.py -v`
Expected: all PASS. A failure here is a port bug (wrong path root or missed rename) — fix the port, not the assertion.

- [ ] **Step 6: Add a regression test for the pages alias**

Append to `scripts/tests/test_slidegen_schema.py`:
```python
def test_pages_key_preferred_and_slides_alias_accepted():
    from visgen.schema import validate_document, document_pages
    base = {"meta": {"format": "deck-16x9"},
            "pages": [{"layout": "hero", "content": {"title": "Hi"}}]}
    validate_document(base)  # no raise
    legacy = {"meta": {"format": "deck-16x9"},
              "slides": [{"layout": "hero", "content": {"title": "Hi"}}]}
    validate_document(legacy)  # no raise
    assert document_pages(base) == base["pages"]
    assert document_pages(legacy) == legacy["slides"]
```

Run: `uv run pytest scripts/tests/test_slidegen_schema.py -v` — Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/lib/visgen scripts/evals scripts/tests
git commit -m "feat(m1): port schema/icons/qr/pngsize to visgen — pages alias, formats-registry validation, brand/ icons"
```

---

### Task 6: Port html_render (theme assembly from brand/, skill_dir parameter)

**Files:**
- Create: `scripts/lib/visgen/html_render.py`
- Test: ported `scripts/tests/{test_slidegen_html,test_theme_select}.py`

**Interfaces:**
- Consumes: `visgen.tokens.theme_css`, `visgen.formats.page_px`, `visgen.schema.{validate_document,document_pages}`, `visgen.icons.render_icon`, `visgen.qr.qr_svg`, `brand/fonts.css`, `brand/logos/*.svg`
- Produces (consumed by Task 7, 10):
  - `visgen.html_render.render_document(doc: dict, skill_dir: Path | None = None) -> str` — full HTML string; default `skill_dir` is `<repo>/.claude/skills/generate-slides`
  - `visgen.html_render.build_env(templates_dir: Path) -> jinja2.Environment`
  - Template contract unchanged: layouts receive `c, meta, page_num, logo, logo_color, logo_white, decor, page_w, page_h, qr_svg_markup`; base template receives `meta, slides_html, base_css, theme_css, decor, page_w, page_h`.

- [ ] **Step 1: Write `scripts/lib/visgen/html_render.py`** (full new file — ported from `$CC/scripts/lib/slidegen/html_render.py` with brand/-based theme assembly)

```python
"""Assemble a canvas document into one HTML string. Validates, renders each
page's layout template, wraps them in the base template with inlined brand CSS.
Theme CSS is assembled from brand/ (single source of truth): embedded fonts +
generated tokens for meta.theme + the skill's tokenised components.css.
Output is html-ppt-compatible (<div class="deck"> wrapping <section class="slide">)."""
import base64
import re
from pathlib import Path
import jinja2

from visgen.schema import validate_document, document_pages
from visgen.formats import page_px
from visgen.tokens import BRAND_DIR, theme_css as tokens_css
from visgen.icons import render_icon
from visgen.qr import qr_svg

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SKILL_DIR = REPO_ROOT / ".claude/skills/generate-slides"

_FONT_URL = re.compile(r'url\(\s*["\']?(?:\.\./)?fonts/([^"\')]+)["\']?\s*\)')


def build_env(templates_dir: Path) -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        autoescape=jinja2.select_autoescape(["html", "j2"]),
    )
    env.globals["icon"] = render_icon
    env.globals["qr_svg"] = qr_svg
    return env


def _embed_fonts(css: str) -> str:
    """Replace url("fonts/x.woff2") with a base64 data URI so the inlined CSS is
    self-contained — renders deterministically offline, wherever the file lives."""
    def repl(m):
        data = (BRAND_DIR / "fonts" / m.group(1)).read_bytes()
        b64 = base64.standard_b64encode(data).decode("ascii")
        return f'url("data:font/woff2;base64,{b64}")'
    return _FONT_URL.sub(repl, css)


def _theme_css(theme: str, skill_dir: Path) -> str:
    fonts = _embed_fonts((BRAND_DIR / "fonts.css").read_text(encoding="utf-8"))
    components = (skill_dir / "assets/components.css").read_text(encoding="utf-8")
    return "\n".join([fonts, tokens_css(theme), components])


def render_document(doc: dict, skill_dir: Path | None = None) -> str:
    validate_document(doc)
    skill_dir = skill_dir or DEFAULT_SKILL_DIR
    env = build_env(skill_dir / "templates")
    meta = doc["meta"]
    page_w, page_h = page_px(meta["format"])
    base_css = (skill_dir / "assets/base.css").read_text(encoding="utf-8")

    theme = meta.get("theme", "light")
    theme_css = _theme_css(theme, skill_dir)

    logo_color = (BRAND_DIR / "logos/visemi-logo-color.svg").read_text(encoding="utf-8")
    logo_white = (BRAND_DIR / "logos/visemi-logo-white.svg").read_text(encoding="utf-8")
    active_logo = logo_white if theme == "dark" else logo_color

    decor = meta.get("decor", True)

    slides_html = []
    for i, page in enumerate(document_pages(doc), start=1):
        tmpl = env.get_template(f"layouts/{page['layout']}.html.j2")
        content = page["content"]
        qr_markup = None
        qr = content.get("qr") if isinstance(content, dict) else None
        if (page["layout"] == "cta-qr" or qr) and isinstance(qr, dict) and qr.get("url"):
            qr_markup = qr_svg(qr["url"])
        slides_html.append(tmpl.render(
            c=content, meta=meta, page_num=i,
            logo=active_logo, logo_color=logo_color, logo_white=logo_white,
            decor=decor, page_w=page_w, page_h=page_h,
            qr_svg_markup=qr_markup,
        ))

    base = env.get_template("base.html.j2")
    return base.render(meta=meta, slides_html=slides_html,
                       base_css=base_css, theme_css=theme_css,
                       decor=decor, page_w=page_w, page_h=page_h)
```

- [ ] **Step 2: Port the two test files**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
for f in test_slidegen_html test_theme_select; do
  sed 's/\bslidegen\b/visgen/g' "$CC/scripts/tests/$f.py" > "scripts/tests/$f.py"
done
```
Open both. Any test that read `assets/themes/visemi.css` / `visemi-dark.css` directly must now assemble the equivalent via the new sources — replace such reads with `visgen.html_render._theme_css("light"|"dark", DEFAULT_SKILL_DIR)`. Keep what each assertion *checks* (e.g. "dark theme HTML carries the dark token values", "page size 1920px appears") unchanged.

- [ ] **Step 3: Run tests**

Run: `uv run pytest scripts/tests/test_slidegen_html.py scripts/tests/test_theme_select.py -v`
Expected: FAIL — `components.css`, templates, and `base.css` don't exist until Task 9. Record the failures and proceed to Task 7 ONLY if every failure is a missing-skill-asset (`FileNotFoundError`/`TemplateNotFound` on `components.css`, `base.css`, or `templates/`). These tests go green in Task 9 Step 6. Any *other* failure (import error, logic) must be fixed now.

- [ ] **Step 4: Commit**

```bash
git add scripts/lib/visgen/html_render.py scripts/tests/test_slidegen_html.py scripts/tests/test_theme_select.py
git commit -m "feat(m1): port html_render — brand/ theme assembly, skill_dir param, pages accessor"
```

---

### Task 7: Canvas renderer + render_canvas CLI

**Files:**
- Create: `scripts/lib/visgen/canvas.py`
- Create: `scripts/ops/render_canvas.py`
- Test: ported `scripts/tests/test_slidegen_render.py` + new `scripts/tests/test_canvas_formats.py`

**Interfaces:**
- Consumes: `visgen.html_render.render_document`, `visgen.formats.page_px`, `visgen.schema.document_pages`
- Produces (consumed by Tasks 8, 10):
  - `visgen.canvas.render_canvas(doc: dict, out_dir: Path, fmt: str = "both", skill_dir: Path | None = None) -> dict` — writes `index.html`, `png/page-NN.png`, `pdf/<out_dir.name>.pdf`, `render_report.json`; returns the report dict `{"format", "page_px", "pages": [{"index", "overflow", "width", "height"}]}`
  - CLI: `uv run python scripts/ops/render_canvas.py CONTENT.json [--format png|pdf|both] [--out DIR]` (default out: `output/<content-stem>/`)
  - **Report key rename:** the per-page list is `"pages"` (was `"slides"`); PNG files are `page-NN.png` (was `slide-NN.png`). Tasks 8 and 10 use the new names.

- [ ] **Step 1: Write `scripts/lib/visgen/canvas.py`** (logic ported from `$CC/scripts/ops/render_slides.py`, lifted into the library per DRY so the CLI and eval runner share it)

```python
"""Render a canvas content dict to pixel-exact PNGs + a combined PDF via headless
Chromium (Playwright). Local-only: no outward action, no credentials."""
import json
from pathlib import Path

from visgen.html_render import render_document
from visgen.formats import page_px


def render_canvas(doc: dict, out_dir: Path, fmt: str = "both",
                  skill_dir: Path | None = None) -> dict:
    page_w, page_h = page_px(doc["meta"]["format"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    html = render_document(doc, skill_dir=skill_dir)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright

    report = {"format": doc["meta"]["format"], "page_px": [page_w, page_h], "pages": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": page_w, "height": page_h},
                                device_scale_factor=1)
        page.goto((out_dir / "index.html").resolve().as_uri())
        page.emulate_media(media="print", reduced_motion="reduce")
        page.wait_for_timeout(300)  # let fonts settle

        sections = page.query_selector_all(".slide")
        if fmt in ("png", "both"):
            (out_dir / "png").mkdir(exist_ok=True)
        for i, sec in enumerate(sections, start=1):
            box = sec.bounding_box()
            overflow = sec.evaluate("el => el.scrollHeight > el.clientHeight "
                                    "|| el.scrollWidth > el.clientWidth")
            report["pages"].append({"index": i, "overflow": bool(overflow),
                                    "width": round(box["width"]), "height": round(box["height"])})
            if fmt in ("png", "both"):
                sec.screenshot(path=str(out_dir / "png" / f"page-{i:02d}.png"))

        if fmt in ("pdf", "both"):
            (out_dir / "pdf").mkdir(exist_ok=True)
            page.pdf(path=str(out_dir / "pdf" / f"{out_dir.name}.pdf"),
                     width=f"{page_w}px", height=f"{page_h}px",
                     print_background=True,
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()

    (out_dir / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
```

- [ ] **Step 2: Write `scripts/ops/render_canvas.py`** (thin CLI)

```python
#!/usr/bin/env python3
"""Render a canvas content JSON (slides, posts, posters) to PNG/PDF.

Usage:
    uv run python scripts/ops/render_canvas.py CONTENT.json [--format png|pdf|both] [--out DIR]

Writes into DIR (default: output/<content-stem>/):
    index.html, png/page-NN.png, pdf/<dirname>.pdf, render_report.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.canvas import render_canvas  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Render canvas content JSON to PNG/PDF via Chromium.")
    ap.add_argument("content", help="Path to the content JSON.")
    ap.add_argument("--format", choices=["png", "pdf", "both"], default="both")
    ap.add_argument("--out", help="Output directory (default: output/<stem>/).")
    args = ap.parse_args()

    content_path = Path(args.content)
    doc = json.loads(content_path.read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else Path("output") / content_path.stem
    report = render_canvas(doc, out, fmt=args.format)
    print(f"Rendered {len(report['pages'])} page(s) to {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Port the render test + add the multi-format test**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
sed 's/\bslidegen\b/visgen/g; s/"slides"/"pages"/g; s/slide-01\.png/page-01.png/g' \
  "$CC/scripts/tests/test_slidegen_render.py" > scripts/tests/test_slidegen_render.py
```
Open it and reconcile with the new interfaces: it should import `from visgen.canvas import render_canvas`, call it with a doc dict + `tmp_path`, and assert `png_size(...) == (1920, 1080)`, `report["page_px"] == [1920, 1080]`, and every `report["pages"][i]["overflow"] is False`. Adjust mechanically; keep assertion intent.

New `scripts/tests/test_canvas_formats.py`:
```python
"""The generalization test: the same engine renders non-slide stage sizes."""
from visgen.canvas import render_canvas
from visgen.pngsize import png_size

def test_square_format_renders_1080x1080(tmp_path):
    doc = {"meta": {"format": "square", "theme": "light", "title": "t"},
           "pages": [{"layout": "quote", "content": {"quote": "Cất Cánh"}}]}
    report = render_canvas(doc, tmp_path / "sq", fmt="png")
    assert report["page_px"] == [1080, 1080]
    assert png_size(tmp_path / "sq/png/page-01.png") == (1080, 1080)
```
(Overflow is NOT asserted here — slide layouts aren't tuned for square yet; M3 adds tuned layouts. The stage size is the contract under test.)

- [ ] **Step 4: Run tests**

Run: `uv run pytest scripts/tests/test_slidegen_render.py scripts/tests/test_canvas_formats.py -v`
Expected: FAIL on missing skill templates (Task 9). Same gate as Task 6 Step 3: only missing-skill-asset failures are acceptable; they go green in Task 9. Logic/import failures must be fixed now.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/visgen/canvas.py scripts/ops/render_canvas.py scripts/tests/test_slidegen_render.py scripts/tests/test_canvas_formats.py
git commit -m "feat(m1): canvas renderer lib + render_canvas CLI — parameterized stage sizes, pages report"
```

---

### Task 8: Brand-lint with tokens-derived palette + grade_brand CLI

**Files:**
- Create: `scripts/lib/visgen/brand_lint.py`
- Create: `scripts/ops/grade_brand.py`
- Test: ported `scripts/tests/{test_slidegen_brand_lint,test_brand_lint_palette}.py`

**Interfaces:**
- Consumes: `visgen.tokens.palette()`
- Produces (consumed by Task 10):
  - `visgen.brand_lint.lint(html, report=None, required_strings=(), forbidden_strings=(), expected_page_px=None) -> {"passed": bool, "violations": [...]}` — same contract as cat-canh
  - CLI: `uv run python scripts/ops/grade_brand.py OUTDIR [--task TASK.json]`, exit 0 iff passed

- [ ] **Step 1: Port with the palette swap**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
cp "$CC/scripts/lib/slidegen/brand_lint.py" scripts/lib/visgen/brand_lint.py
cp "$CC/scripts/ops/grade_brand.py" scripts/ops/grade_brand.py
```

In `scripts/lib/visgen/brand_lint.py`, replace the entire hardcoded `BRAND_HEX = {...}` literal (the ~14-line set) with:

```python
from visgen.tokens import palette

BRAND_HEX = palette()
```
Update the module docstring's palette sentence to: `Palette: every hex named in brand/tokens.json (all theme token values) plus its extra_allowed_hexes; any other hex is flagged.`

In `scripts/lib/visgen/brand_lint.py` `lint_render_report`, replace:
```python
    for s in report.get("slides", []):
```
with:
```python
    for s in report.get("pages", report.get("slides", [])):
```
(back-compat: old cat-canh reports still lintable).

In `scripts/ops/grade_brand.py`, replace `from slidegen.brand_lint import lint` with `from visgen.brand_lint import lint` (the `sys.path` insert stays).

- [ ] **Step 2: Port the two test files**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
for f in test_slidegen_brand_lint test_brand_lint_palette; do
  sed 's/\bslidegen\b/visgen/g' "$CC/scripts/tests/$f.py" > "scripts/tests/$f.py"
done
```
`test_slidegen_brand_lint.py` builds a report with a `"slides"` key (see its lines ~31–33) — leave it; the alias in Step 1 covers it and doubles as the back-compat test.

- [ ] **Step 3: Add the anti-drift test**

Append to `scripts/tests/test_brand_lint_palette.py`:
```python
def test_lint_palette_is_tokens_palette():
    """Lint allowlist and theme tokens cannot drift: same function, same set."""
    from visgen.brand_lint import BRAND_HEX
    from visgen.tokens import palette
    assert BRAND_HEX == palette()

def test_gold_and_house_hexes_allowed():
    from visgen.brand_lint import lint_html
    ok = '<div style="color:#01B68B;background:#F5B433;border-color:#001669">x</div>'
    assert lint_html(ok) == []
    bad = '<div style="color:#FF00AA">x</div>'
    assert any(v["code"] == "offbrand-hex" for v in lint_html(bad))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest scripts/tests/test_slidegen_brand_lint.py scripts/tests/test_brand_lint_palette.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/visgen/brand_lint.py scripts/ops/grade_brand.py scripts/tests/test_slidegen_brand_lint.py scripts/tests/test_brand_lint_palette.py
git commit -m "feat(m1): brand-lint with tokens-derived palette (lint cannot drift from theme)"
```

---

### Task 9: Port the generate-slides skill (templates, components.css, SKILL.md)

**Files:**
- Create: `.claude/skills/generate-slides/templates/**` (base + components + 17 layouts, verbatim)
- Create: `.claude/skills/generate-slides/assets/{base.css,runtime.js,THIRD_PARTY_LICENSES,components.css}`
- Create: `.claude/skills/generate-slides/SKILL.md`
- Test: ported `scripts/tests/{test_slidegen_components,test_slidegen_deck,test_slidegen_onepager,test_slidegen_brand}.py` + the deferred Task 6/7 tests go green

**Interfaces:**
- Consumes: template contract from Task 6 (`c, meta, page_num, logo, ..., qr_svg_markup`; base gets `slides_html, base_css, theme_css, ...`)
- Produces: the default `skill_dir` consumed by `render_document`; `assets/components.css` (fully tokenized, both themes) consumed by `_theme_css`.

- [ ] **Step 1: Copy templates and vendored assets verbatim**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
SK="$CC/.claude/skills/generate-slides"
mkdir -p .claude/skills/generate-slides/assets
cp -r "$SK/templates" .claude/skills/generate-slides/
cp "$SK/assets/base.css" "$SK/assets/runtime.js" "$SK/assets/THIRD_PARTY_LICENSES" .claude/skills/generate-slides/assets/
```
(No fonts/logos/icons/themes copies — those live in `brand/` now. Do NOT copy `$SK/assets/themes/`.)

- [ ] **Step 2: Create the shared `components.css`** (helper classes from the old theme, minus `@font-face` and `:root` — those come from `brand/`)

```bash
# Everything AFTER the closing brace of :root (line 81) in the frozen light theme:
sed -n '82,$p' scripts/tests/fixtures/themes/visemi.css > .claude/skills/generate-slides/assets/components.css
```
Then apply the two tokenizations (the only light/dark divergences, per the port analysis):
1. In the `body{...}` rule: `color:var(--purple)` → `color:var(--body)`
2. In the `.agenda-item .n{...}` rule: `background:var(--navy)` → `background:var(--num-bg)`

- [ ] **Step 3: Guard: components.css is fully tokenized**

Append to `scripts/tests/test_tokens.py`:
```python
def test_components_css_has_no_literal_hex():
    """Brand values live only in tokens.json; component CSS must be all var() refs."""
    import re
    root = Path(__file__).resolve().parents[2]
    css = (root / ".claude/skills/generate-slides/assets/components.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert re.findall(r"#[0-9a-fA-F]{3,6}\b", css) == []
```
Run: `uv run pytest scripts/tests/test_tokens.py -v` — if a literal hex remains in `components.css`, move its value into `tokens.json` as a new token (both themes) and reference `var(--...)`; that is the DRY fix, never an allowlist exception.

- [ ] **Step 4: Write `.claude/skills/generate-slides/SKILL.md`**

Start from `$SK/SKILL.md` (copy it), then apply exactly these edits:
1. Frontmatter `description`: keep it unchanged (it contains no paths; its pushy triggering language stays).
2. Replace every `scripts/ops/render_slides.py` → `scripts/ops/render_canvas.py`; every `slides/<name>` output path → `output/<name>`; every `scripts/lib/slidegen/` → `scripts/lib/visgen/`; `png/slide-NN.png` → `png/page-NN.png`.
3. Rewrite the "Workspace note" blockquote to: templates vendored under this skill; brand assets (fonts/logos/icons/tokens) in `brand/` (single source of truth, `brand/tokens.json`); render/grade machinery in `scripts/ops/` + `scripts/lib/visgen/`; exemplars in `scripts/evals/references/`.
4. In the content-JSON shape section: document `"pages": [...]` as the key, with `"slides"` accepted as a legacy alias.
5. In the "Themes" section: themes are assembled from `brand/fonts.css` + `brand/tokens.json` (via `visgen.tokens`) + this skill's `assets/components.css`; still selected by `meta.theme`, same token names, never hardcode a hex.
6. In "Ecosystem follow-on": vendored toolkit paths are this repo's `references/presentation-frameworks/html-ppt-skill` and `references/presentation-frameworks/beautiful-html-templates`.
7. Delete the `extract_pptx.py` sentence (not ported in M1).

- [ ] **Step 5: Port the remaining skill tests**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
for f in test_slidegen_components test_slidegen_deck test_slidegen_onepager test_slidegen_brand; do
  sed 's/\bslidegen\b/visgen/g' "$CC/scripts/tests/$f.py" > "scripts/tests/$f.py"
done
```
Open each; fix path roots only (e.g. references to `assets/themes/*.css` → the Task 6 `_theme_css` assembly; fixture paths already exist from Task 5). Keep assertion intent.

- [ ] **Step 6: Run the full suite — deferred tests must go green now**

Run: `uv run pytest -v`
Expected: ALL tests pass, including Task 6's `test_slidegen_html.py` / `test_theme_select.py` and Task 7's render tests. Debug port issues until green (missing template file, path root, etc.). Do not weaken assertions.

- [ ] **Step 7: Render + eyeball one exemplar**

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py scripts/evals/references/kickoff.content.json --out output/kickoff-smoke
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_brand.py output/kickoff-smoke
```
Expected: render report all `overflow: false`; grade prints `"passed": true`, exit 0. Open 2–3 PNGs in `output/kickoff-smoke/png/` (Read tool) and eyeball: navy/green brand, Be Vietnam Pro, logo top-right, decoration dots/glow.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/generate-slides scripts/tests
git commit -m "feat(m1): port generate-slides skill — templates, tokenized components.css, SKILL.md for visgen engine"
```

---

### Task 10: Port the eval harness + rubric grader

**Files:**
- Create: `scripts/evals/run_evals.py`, `scripts/evals/rubrics/{brand,layout,content,polish}.md`
- Create: `scripts/ops/grade_rubric.py`
- Test: ported `scripts/tests/{test_slidegen_evals,test_slidegen_rubric}.py`

**Interfaces:**
- Consumes: `visgen.brand_lint.lint`, `visgen.formats.page_px`, `scripts/ops/render_canvas.py` (subprocess), tasks/references data from Task 5
- Produces: `uv run python scripts/evals/run_evals.py [--task F]... [--trials N] [--judge] [--out DIR]` → `scripts/evals/runs/latest/aggregate.json` with `pass_at_k`/`pass_caret_k` per task; `grade_rubric.py OUTDIR --task TASK.json` (needs `ANTHROPIC_API_KEY`, model `claude-opus-4-8`).

- [ ] **Step 1: Copy and update**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
cp "$CC/scripts/evals/run_evals.py" scripts/evals/run_evals.py
cp -r "$CC/scripts/evals/rubrics" scripts/evals/
cp "$CC/scripts/ops/grade_rubric.py" scripts/ops/grade_rubric.py
```

Apply exactly these edits to `scripts/evals/run_evals.py`:
1. `from slidegen.brand_lint import lint` → `from visgen.brand_lint import lint`
2. In `_render`: `scripts/ops/render_slides.py` → `scripts/ops/render_canvas.py`
3. In `_judge`: `(trial_dir / "png").glob("slide-*.png")` → `(trial_dir / "png").glob("page-*.png")`
4. Replace the synthesized-reference-task block's hardcoded size with the registry (DRY):
```python
            doc_meta = json.loads(ref.read_text(encoding="utf-8"))["meta"]
            tasks.append({
                "id": f"ref-{ref.name[:-len('.content.json')]}",
                "description": f"Regression: render + brand-lint reference exemplar {ref.name}.",
                "content": rel,
                "expected_page_px": list(page_px(doc_meta["format"])),
                "trials": 1,
            })
```
   and add `from visgen.formats import page_px` next to the lint import.

In `scripts/ops/grade_rubric.py`: replace any `from slidegen...`/`sys.path` slidegen references with `visgen` (same one-line pattern as `grade_brand.py`); leave `DIMENSIONS`, prompts, and model `claude-opus-4-8` untouched.

Check the seed task JSONs copied in Task 5 (`scripts/evals/tasks/*.json`): any carrying `"expected_page_px"` keep working as-is; no edits.

- [ ] **Step 2: Port the two test files**

```bash
CC="/d/2-VISEMI/cat-canh-program-management"
for f in test_slidegen_evals test_slidegen_rubric; do
  sed 's/\bslidegen\b/visgen/g' "$CC/scripts/tests/$f.py" > "scripts/tests/$f.py"
done
```
Open both; fix path roots (`render_slides` → `render_canvas`, `slide-*.png` → `page-*.png`) if referenced. Keep assertion intent. If `test_slidegen_rubric` calls the Anthropic API, it must already be mocked/skipped in cat-canh — preserve that behavior exactly.

- [ ] **Step 3: Run tests, then the real harness (no API key)**

Run: `uv run pytest scripts/tests/test_slidegen_evals.py scripts/tests/test_slidegen_rubric.py -v`
Expected: PASS

Run: `PYTHONIOENCODING=utf-8 uv run python scripts/evals/run_evals.py`
Expected: renders every seed task + all 4 references (kickoff, kickoff-dark, pitch-deck, one-pager), writes `scripts/evals/runs/latest/aggregate.json`; every entry `"pass_at_k": 1.0`. (`--judge` not passed → no API key needed.)

- [ ] **Step 4: Commit**

```bash
git add scripts/evals/run_evals.py scripts/evals/rubrics scripts/ops/grade_rubric.py scripts/tests/test_slidegen_evals.py scripts/tests/test_slidegen_rubric.py
git commit -m "feat(m1): port eval harness + rubric judge — pass@k over seed tasks and reference exemplars"
```

---

### Task 11: M1 acceptance gate

**Files:**
- Modify: `CLAUDE.md` (only if any path/command documented there changed during the port)

**Interfaces:**
- Consumes: everything above.
- Produces: the M1 deliverable — verified green state for M2 to build on.

- [ ] **Step 1: Full test suite**

Run: `uv run pytest -v`
Expected: ALL PASS (≈20 test files: brand assets, tokens, formats, schema×2, icons, qr, html, theme, render, canvas-formats, lint×2, components, deck, onepager, brand, evals, rubric).

- [ ] **Step 2: Render and grade all four exemplars end-to-end via the CLIs**

```bash
for ref in kickoff kickoff-dark pitch-deck one-pager; do
  PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py \
    "scripts/evals/references/$ref.content.json" --out "output/accept-$ref" &&
  PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_brand.py "output/accept-$ref" || echo "FAILED: $ref"
done
```
Expected: four `"passed": true`, zero `FAILED:` lines.

- [ ] **Step 3: Eyeball against the originals**

Read 3–4 PNGs from `output/accept-kickoff/png/` and `output/accept-kickoff-dark/png/` and compare against the same slides rendered in cat-canh (`$CC/scripts/evals/runs/latest/.../png/` has donor renders; or render there if needed). They must be visually identical (same tokens, same templates). Any visible difference = a theme-split bug; fix before proceeding.

- [ ] **Step 4: Full eval harness once more, from clean**

```bash
rm -rf scripts/evals/runs/latest
PYTHONIOENCODING=utf-8 uv run python scripts/evals/run_evals.py
```
Expected: all `pass_at_k: 1.0` in the printed aggregate.

- [ ] **Step 5: Final commit**

```bash
git add -A
git status   # verify: no output/ or runs/ files staged (gitignore working)
git commit -m "feat(m1): M1 acceptance — all exemplars render + pass lint, full suite green"
```

---

## After M1 (not in this plan)

- **M2:** document renderer (Markdown + Paged.js → A4 PDF) + `generate-doc` skill — write its plan with superpowers:writing-plans after M1 lands, reading the spec's Document renderer section.
- **Skill iteration:** run the skill-creator loop (test prompts vs baseline, eval viewer, human review) on `generate-slides` and each new skill.
- **M3/M4/M5:** social posts, posters + `visual-designer` agent, description optimization + design-kit update + portability audit.
