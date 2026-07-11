# Visual Generation Submodule-Plugin Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `visual-generation` into a self-contained Claude Code plugin that is consumed as a git submodule in a working repo, discoverable there, themeable per working repo via a brand override, guarded to a dedicated project branch, and complete (slides, docs, social posts, posters + the `visual-designer` agent).

**Architecture:** One repo plays three roles with no duplication: a standalone studio, a Claude Code plugin (skills at top-level `skills/`, agents at `agents/`, manifests in `.claude-plugin/`), and a git submodule. The seam that makes per-repo themes work is *brand injection*: the engine and brand-lint both resolve their brand source (tokens/fonts/logos/palette) through one `active_brand_dir()` resolver instead of hardcoding `brand/`. Scripts already anchor to `__file__`, so they run correctly from any CWD.

**Tech Stack:** Python 3.12+, `uv` (project manager), Jinja2, Playwright/Chromium, Paged.js, pytest. Claude Code plugin + git submodule mechanics.

## Global Constraints

- **Brand is locked, tokens are the only source.** Palette navy `#001669`, dark purple `#262538`, green `#01B68B`, white, token ramps, cyan `#00E5FF` (very sparing), gold `#F5B433` (sparing). Status colors `--warn`/`--bad`/`--good` functional-only. No hardcoded hexes outside `brand/`. Be Vietnam Pro only. No em/en dashes, no emojis. Vietnamese keeps full diacritics ("Cất Cánh", never "Cat Canh").
- **DRY / single source of truth.** Brand values only in `brand/tokens.json`; render/grade logic only in `scripts/lib/visgen/`; layout schemas only in `schema.py`; rubrics only in `scripts/evals/rubrics/`. Skills carry no private copies of engine/brand.
- **Plugin name is `visual-generation`.** Skills namespaced `visual-generation:<skill>`. Skills auto-discovered from `skills/<name>/SKILL.md`; agents from `agents/<name>.md`. Manifests only in `.claude-plugin/`.
- **`${CLAUDE_SKILL_DIR}` is the only reliable path token in skill Bash calls** (NOT `$CLAUDE_PLUGIN_ROOT`). Plugin root from a skill = `${CLAUDE_SKILL_DIR}/../..`.
- **Facts from the brief, never invented.** A visual is done only when it renders (no overflow), brand-lint passes, and PNGs were eyeballed.
- **Never commit `output/`** (git-ignored). Per-project studio work lives on a permanent project branch, never forced back to `master`.
- **Windows/PowerShell primary shell; Bash tool available.** Renders need `PYTHONIOENCODING=utf-8`. Run Python via `uv run`.
- **Verify commands** run from the submodule root (standalone) unless a task says otherwise: `uv run pytest scripts/tests -q` and `uv run python scripts/evals/run_evals.py`.

## File Structure

**New files (in `visual-generation`):**
- `.claude-plugin/plugin.json` — plugin manifest
- `.claude-plugin/marketplace.json` — single-plugin local marketplace
- `.claude/settings.json` — enables the local plugin for standalone use
- `scripts/lib/visgen/brand.py` — `active_brand_dir()` resolver (the injection seam)
- `scripts/lib/visgen/preflight.py` — branch guard
- `scripts/tests/test_brand_resolver.py`, `test_preflight.py`, `test_brand_injection.py`
- `skills/visgen-setup/SKILL.md` — bootstrap skill (branch + scaffold)
- `agents/visual-designer.md` — end-to-end agent
- `skills/generate-social-post/…` and `skills/generate-poster/…` — new skills (SKILL.md, templates/, assets/)
- `scripts/evals/references/social-*.content.json`, `poster-*.content.json` + `scripts/evals/tasks/social-*.json`, `poster-*.json` — exemplars + eval tasks

**Moved (git mv):**
- `.claude/skills/generate-slides` → `skills/generate-slides`
- `.claude/skills/generate-doc` → `skills/generate-doc`
- `.claude/skills/knowledge-update` → `skills/knowledge-update`

**Modified:**
- `scripts/lib/visgen/tokens.py` — resolve brand via `active_brand_dir()`, cache by path
- `scripts/lib/visgen/brand_lint.py` — palette at call time, not import time
- `scripts/lib/visgen/html_render.py` — use `active_brand_dir()`; fix `DEFAULT_*SKILL_DIR` to `skills/`
- `scripts/lib/visgen/schema.py` — add social + poster layouts
- `scripts/ops/render_canvas.py`, `render_doc.py`, `grade_brand.py`, `grade_doc.py` — add `--brand`; render CLIs call the branch guard
- `scripts/tests/test_tokens.py`, `test_slidegen_brand.py`, `test_brand_lint_palette.py`, `test_doc_skill.py`, `test_doc_templates.py` — path/palette updates from move + injection
- `CLAUDE.md` — layout paths `.claude/skills/` → `skills/`, note plugin/submodule model
- **In `cat-canh-program-management` (Phase 7):** `.claude/settings.json`, `.gitignore`, retire frozen `generate-slides` skill + `slide-designer` agent, add submodule

---

## Phase 1 — Plugin skeleton + layout move

### Task 1: Plugin manifests + standalone enablement

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.claude/settings.json`

**Interfaces:**
- Produces: plugin named `visual-generation` in marketplace `visual-generation`; enable key `"visual-generation@visual-generation"`.

- [ ] **Step 1: Write `.claude-plugin/plugin.json`**

```json
{
  "name": "visual-generation",
  "description": "VISEMI visual-generation studio: brand-locked slides, docs, social posts, and posters rendered to pixel-exact PNG/PDF, with a shared engine, brand tokens, and eval/grader stack.",
  "version": "0.1.0",
  "author": { "name": "VISEMI", "email": "lanph@visemi.org" },
  "homepage": "https://github.com/lanhp-vn/visual-generation",
  "repository": "https://github.com/lanhp-vn/visual-generation",
  "license": "UNLICENSED",
  "keywords": ["visemi", "cat-canh", "slides", "documents", "brand", "playwright"]
}
```

- [ ] **Step 2: Write `.claude-plugin/marketplace.json`**

```json
{
  "name": "visual-generation",
  "description": "Local marketplace for the VISEMI visual-generation plugin.",
  "owner": { "name": "VISEMI", "email": "lanph@visemi.org" },
  "plugins": [
    {
      "name": "visual-generation",
      "description": "VISEMI visual-generation studio (slides, docs, social, posters).",
      "version": "0.1.0",
      "source": "./",
      "author": { "name": "VISEMI", "email": "lanph@visemi.org" }
    }
  ]
}
```

- [ ] **Step 3: Write `.claude/settings.json` (standalone self-enable; marketplace source is the repo itself)**

```json
{
  "extraKnownMarketplaces": {
    "visual-generation": { "source": { "source": "directory", "path": "." } }
  },
  "enabledPlugins": { "visual-generation@visual-generation": true }
}
```

- [ ] **Step 4: Validate JSON**

Run: `uv run python -c "import json,glob; [json.load(open(p,encoding='utf-8')) for p in ['.claude-plugin/plugin.json','.claude-plugin/marketplace.json','.claude/settings.json']]; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json .claude/settings.json
git commit -m "feat(plugin): add plugin + local marketplace manifests and standalone enablement"
```

### Task 2: Move skills to plugin layout and fix all broken paths

**Files:**
- Move: `.claude/skills/{generate-slides,generate-doc,knowledge-update}` → `skills/`
- Create: `agents/` (empty dir placeholder via `.gitkeep`)
- Modify: `scripts/lib/visgen/html_render.py:18-19`
- Modify: `scripts/tests/test_doc_skill.py:4`, `scripts/tests/test_doc_templates.py:6`, `scripts/tests/test_tokens.py:48`
- Modify: `skills/knowledge-update/SKILL.md` (path prose `.claude/skills/` → `skills/`)
- Modify: `CLAUDE.md` (Layout section)

**Interfaces:**
- Produces: `REPO_ROOT / "skills/generate-slides"` and `REPO_ROOT / "skills/generate-doc"` as the default skill dirs consumed by `html_render.render_document` / `render_doc_html`.

- [ ] **Step 1: Move the three skill dirs (preserve history)**

```bash
git mv .claude/skills/generate-slides skills/generate-slides
git mv .claude/skills/generate-doc skills/generate-doc
git mv .claude/skills/knowledge-update skills/knowledge-update
mkdir -p agents && touch agents/.gitkeep && git add agents/.gitkeep
```

- [ ] **Step 2: Fix engine default paths in `html_render.py`**

Replace lines 18-19:
```python
DEFAULT_SKILL_DIR = REPO_ROOT / "skills/generate-slides"
DEFAULT_DOC_SKILL_DIR = REPO_ROOT / "skills/generate-doc"
```

- [ ] **Step 3: Fix the three tests' hardcoded skill paths**

`test_doc_skill.py:4` → `... parents[2] / "skills/generate-doc/SKILL.md"`
`test_doc_templates.py:6` → `... parents[2] / "skills/generate-doc"`
`test_tokens.py:48` → `... root / "skills/generate-slides/assets/components.css" ...`

- [ ] **Step 4: Sweep for any remaining `.claude/skills/` references and fix to `skills/`**

Run: `grep -rniE "\.claude/skills" scripts skills CLAUDE.md | grep -viE "workspace|\.pyc"`
Expected after fixes: only `generate-slides-workspace` (git-ignored scratch) may remain. Fix every other hit (notably prose in `skills/knowledge-update/SKILL.md` and the Layout block in `CLAUDE.md`).

- [ ] **Step 5: Run the full suite to confirm the move broke nothing**

Run: `uv run pytest scripts/tests -q`
Expected: PASS (same count as before the move).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor(plugin): move skills to top-level skills/, add agents/, fix engine + test paths"
```

---

## Phase 2 — Brand injection

### Task 3: Brand resolver

**Files:**
- Create: `scripts/lib/visgen/brand.py`
- Test: `scripts/tests/test_brand_resolver.py`

**Interfaces:**
- Produces: `active_brand_dir() -> Path` and `DEFAULT_BRAND: Path`. Resolution order: `VISGEN_BRAND` env → `<cwd>/brand` if it has `tokens.json` → `DEFAULT_BRAND` (submodule `brand/`).

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_brand_resolver.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_brand_resolver.py -q`
Expected: FAIL (`ModuleNotFoundError: visgen.brand`)

- [ ] **Step 3: Write `scripts/lib/visgen/brand.py`**

```python
"""Active brand-source resolution — the injection seam that lets a working repo
supply its own theme without touching shared code. The engine and brand-lint
both resolve their brand root here, so render and lint can never disagree on the
palette. Resolution order:
  1. VISGEN_BRAND env var (set by a CLI --brand flag or the caller)
  2. <cwd>/brand if it has tokens.json (a working repo's own theme)
  3. the submodule's own brand/ (default VISEMI theme)
Brand is threaded as an env var, not a function argument, to avoid adding a
brand parameter to every render/lint function (ponytail: env carrier)."""
import os
from pathlib import Path

DEFAULT_BRAND = Path(__file__).resolve().parents[3] / "brand"


def active_brand_dir() -> Path:
    env = os.environ.get("VISGEN_BRAND")
    if env:
        return Path(env)
    cwd_brand = Path.cwd() / "brand"
    if (cwd_brand / "tokens.json").is_file():
        return cwd_brand
    return DEFAULT_BRAND
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest scripts/tests/test_brand_resolver.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/visgen/brand.py scripts/tests/test_brand_resolver.py
git commit -m "feat(brand): add active_brand_dir resolver (VISGEN_BRAND / cwd / default)"
```

### Task 4: tokens.py reads the resolved brand, cached by path

**Files:**
- Modify: `scripts/lib/visgen/tokens.py`
- Modify: `scripts/tests/test_slidegen_brand.py:2,29,36` (import `active_brand_dir` instead of `BRAND_DIR`)

**Interfaces:**
- Consumes: `visgen.brand.active_brand_dir`.
- Produces: `load_tokens()`, `theme_css(theme)`, `palette()`, `build_css()` all operate on the *resolved* brand; a per-path cache so switching `VISGEN_BRAND` in-process picks up a different brand. `BRAND_DIR` module constant is removed.

- [ ] **Step 1: Rewrite `scripts/lib/visgen/tokens.py`**

```python
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
```

- [ ] **Step 2: Update `test_slidegen_brand.py`**

Replace `from visgen.tokens import BRAND_DIR` (line 2) with `from visgen.brand import active_brand_dir`, and at lines 29/36 replace `BRAND_DIR` with `active_brand_dir()` (bind once at test top: `BRAND_DIR = active_brand_dir()`).

- [ ] **Step 3: Run affected tests**

Run: `uv run pytest scripts/tests/test_tokens.py scripts/tests/test_slidegen_brand.py -q`
Expected: PASS (with CWD = submodule root, `active_brand_dir()` returns the submodule `brand/`, so behavior is unchanged).

- [ ] **Step 4: Commit**

```bash
git add scripts/lib/visgen/tokens.py scripts/tests/test_slidegen_brand.py
git commit -m "refactor(brand): tokens.py resolves brand via active_brand_dir, cache by path"
```

### Task 5: brand-lint resolves the palette at call time

**Files:**
- Modify: `scripts/lib/visgen/brand_lint.py:20-22,48`
- Modify: `scripts/tests/test_brand_lint_palette.py:86-90`

**Interfaces:**
- Consumes: `visgen.tokens.palette` (called inside `lint_html`, not at import).
- Produces: `lint_html`/`lint` honor the active brand's palette; module-level `BRAND_HEX` removed.

- [ ] **Step 1: Edit `brand_lint.py`** — remove the import-time freeze and resolve per call.

Delete line 22 (`BRAND_HEX = palette()`). Keep `from visgen.tokens import palette` (line 20). Inside `lint_html`, immediately after `violations = []` add:
```python
    brand_hex = palette()  # resolved per call so an injected working-repo brand is honored
```
Change line 48's `if hx.lower() not in BRAND_HEX:` to `if hx.lower() not in brand_hex:`.

- [ ] **Step 2: Rewrite the stale module-attr test** `test_brand_lint_palette.py` (the `test_lint_palette_is_tokens_palette` case, ~lines 86-90):

```python
def test_lint_uses_tokens_palette():
    """An on-brand hex passes and an off-brand hex is flagged, proving lint reads
    the tokens palette (not a frozen copy)."""
    from visgen.tokens import palette
    on = next(iter(palette()))
    assert _offbrand_hexes(f'<span style="color:{on}">x</span>') == []
    assert "#ff00aa" in [h.lower() for h in _offbrand_hexes('<span style="color:#FF00AA">x</span>')]
```

- [ ] **Step 3: Run affected tests**

Run: `uv run pytest scripts/tests/test_brand_lint_palette.py scripts/tests/test_slidegen_brand_lint.py -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/lib/visgen/brand_lint.py scripts/tests/test_brand_lint_palette.py
git commit -m "refactor(brand): lint resolves palette at call time (honors injected brand)"
```

### Task 6: html_render uses the resolved brand

**Files:**
- Modify: `scripts/lib/visgen/html_render.py:13,39,48,68-69,116`

**Interfaces:**
- Consumes: `visgen.brand.active_brand_dir`.
- Produces: fonts and logos load from the resolved brand, so an injected theme re-brands renders.

- [ ] **Step 1: Change the import (line 13)**

```python
from visgen.tokens import theme_css as tokens_css
from visgen.brand import active_brand_dir
```

- [ ] **Step 2: In `_embed_fonts` (line ~39)** bind and use the resolved brand:

```python
    def repl(m):
        data = (active_brand_dir() / "fonts" / m.group(1)).read_bytes()
        b64 = base64.standard_b64encode(data).decode("ascii")
        return f'url("data:font/woff2;base64,{b64}")'
```

- [ ] **Step 3: In `_fonts_and_tokens` (line ~48)**

```python
    fonts = _embed_fonts((active_brand_dir() / "fonts.css").read_text(encoding="utf-8"))
```

- [ ] **Step 4: In `render_document` (lines ~68-69) and `render_doc_html` (line ~116)** replace `BRAND_DIR` with `active_brand_dir()`:

```python
    brand = active_brand_dir()
    logo_color = (brand / "logos/visemi-logo-color.svg").read_text(encoding="utf-8")
    logo_white = (brand / "logos/visemi-logo-white.svg").read_text(encoding="utf-8")
```
and in `render_doc_html`:
```python
    logo = (active_brand_dir() / "logos/visemi-logo-color.svg").read_text(encoding="utf-8")
```

- [ ] **Step 5: Full suite (slides + docs render paths)**

Run: `uv run pytest scripts/tests -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/visgen/html_render.py
git commit -m "refactor(brand): html_render loads fonts/logos from resolved brand"
```

### Task 7: `--brand` on the CLIs

**Files:**
- Modify: `scripts/ops/render_canvas.py`, `scripts/ops/render_doc.py`, `scripts/ops/grade_brand.py`, `scripts/ops/grade_doc.py`

**Interfaces:**
- Produces: each CLI accepts `--brand PATH`; when given it sets `os.environ["VISGEN_BRAND"]` before any render/lint call.

- [ ] **Step 1: Add the flag + wiring to each CLI.** In each `main()`, add the argument and set the env var *before* importing/using engine functions that read the brand. Pattern (apply to all four):

```python
    ap.add_argument("--brand", help="Brand source dir (overrides VISGEN_BRAND / cwd brand/).")
    args = ap.parse_args()
    if args.brand:
        import os
        os.environ["VISGEN_BRAND"] = args.brand
```

(For `grade_brand.py`/`grade_doc.py`, `palette()` is now called at lint time, so setting the env before `lint(...)`/`lint_doc(...)` is sufficient.)

- [ ] **Step 2: Smoke test the flag routes through the resolver**

Run:
```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py scripts/evals/references/kickoff.content.json --format png --out output/_brandsmoke --brand brand
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_brand.py output/_brandsmoke
```
Expected: renders with `overflow: false`; grade prints `"passed": true`.

- [ ] **Step 3: Commit**

```bash
git add scripts/ops/render_canvas.py scripts/ops/render_doc.py scripts/ops/grade_brand.py scripts/ops/grade_doc.py
git commit -m "feat(brand): --brand flag on render/grade CLIs (sets VISGEN_BRAND)"
```

### Task 8: Brand-injection integration test (render + lint share the brand)

**Files:**
- Test: `scripts/tests/test_brand_injection.py`

**Interfaces:**
- Consumes: `active_brand_dir`, `palette`, `theme_css`.

- [ ] **Step 1: Write the test** — a temp brand with one extra allowed hex re-themes both palette and generated CSS; render and lint agree on the resolved root.

```python
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
```

- [ ] **Step 2: Run**

Run: `uv run pytest scripts/tests/test_brand_injection.py -q`
Expected: PASS (2 passed)

- [ ] **Step 3: Commit**

```bash
git add scripts/tests/test_brand_injection.py
git commit -m "test(brand): render and lint share the injected brand; default falls back"
```

---

## Phase 3 — Branch guard, bootstrap, skill command updates

### Task 9: Branch guard (pure decision + git wiring)

**Files:**
- Create: `scripts/lib/visgen/preflight.py`
- Test: `scripts/tests/test_preflight.py`

**Interfaces:**
- Produces: `branch_guard_message(is_submodule: bool, branch: str) -> str | None` (pure) and `check_branch() -> str | None` (wires real git). A submodule checkout has a `.git` *file*; a normal clone has a `.git` *directory*.

- [ ] **Step 1: Write the failing test**

```python
from visgen.preflight import branch_guard_message

def test_blocks_master_as_submodule():
    msg = branch_guard_message(True, "master")
    assert msg and "dedicated project branch" in msg

def test_blocks_main_as_submodule():
    assert branch_guard_message(True, "main") is not None

def test_allows_project_branch_as_submodule():
    assert branch_guard_message(True, "visemi-catcanh") is None

def test_allows_master_when_standalone():
    assert branch_guard_message(False, "master") is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest scripts/tests/test_preflight.py -q`
Expected: FAIL (`ModuleNotFoundError: visgen.preflight`)

- [ ] **Step 3: Write `scripts/lib/visgen/preflight.py`**

```python
"""Branch guard: when the studio runs as a submodule inside a working repo it
must be on a dedicated project branch, never on master/main — so per-project
studio upgrades never accumulate on the shared baseline by accident. Renders are
refused on master/main when a submodule checkout is detected. Standalone use
(a normal clone, .git is a directory) is never blocked; evals call the engine
directly and bypass this guard."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def running_as_submodule() -> bool:
    # A submodule working tree has a .git FILE ("gitdir: ..."); a clone has a dir.
    return (REPO_ROOT / ".git").is_file()


def current_branch() -> str:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def branch_guard_message(is_submodule: bool, branch: str) -> str | None:
    if is_submodule and branch in ("master", "main"):
        return (f"visual-generation is on '{branch}' as a submodule inside a working "
                "repo. Create a dedicated project branch first: run the visgen-setup "
                "skill, or `git -C visual-generation checkout -b <project>` (e.g. "
                "visemi-catcanh), then retry.")
    return None


def check_branch() -> str | None:
    return branch_guard_message(running_as_submodule(), current_branch())
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest scripts/tests/test_preflight.py -q`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/visgen/preflight.py scripts/tests/test_preflight.py
git commit -m "feat(guard): branch pre-flight refusing renders on master as a submodule"
```

### Task 10: Wire the guard into the render CLIs

**Files:**
- Modify: `scripts/ops/render_canvas.py`, `scripts/ops/render_doc.py`

**Interfaces:**
- Consumes: `visgen.preflight.check_branch`.

- [ ] **Step 1: In each render CLI `main()`, before rendering** (after arg parse / brand env set):

```python
    from visgen.preflight import check_branch
    msg = check_branch()
    if msg:
        print(msg, file=sys.stderr)
        sys.exit(2)
```

- [ ] **Step 2: Confirm standalone is not blocked**

Run: `PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py scripts/evals/references/kickoff.content.json --format png --out output/_guardsmoke`
Expected: renders normally (standalone `.git` is a directory → guard returns None).

- [ ] **Step 3: Commit**

```bash
git add scripts/ops/render_canvas.py scripts/ops/render_doc.py
git commit -m "feat(guard): render CLIs refuse to run on master as a submodule"
```

### Task 11: Update SKILL.md invocation commands to be location + brand aware

**Files:**
- Modify: `skills/generate-slides/SKILL.md`, `skills/generate-doc/SKILL.md`

**Interfaces:**
- Produces: render/grade commands that work standalone AND from a working repo, using `${CLAUDE_SKILL_DIR}/../..` as the plugin root and `--brand`/`--out` pointing into the caller's repo.

- [ ] **Step 1: Replace the render/grade command blocks.** In `generate-slides/SKILL.md` Step 2/3 (and the equivalents in `generate-doc/SKILL.md`), use this canonical form (repo-relative `CONTENT.json`, `--out output/<name>` and `--brand brand` resolve against the CALLER's CWD):

```bash
# Render (works standalone or from a working repo; VG = plugin root)
VG="${CLAUDE_SKILL_DIR}/../.."
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  CONTENT.json --format both --out output/<name> --brand brand

# Grade
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/grade_brand.py" \
  output/<name>
```

Add a one-line note: "`--brand brand` uses the working repo's `brand/`; omit it to use the studio's default VISEMI theme. Output lands in the working repo's `output/`, which must be git-ignored."

- [ ] **Step 2: Sanity-check the standalone path still resolves** (from submodule root, `${CLAUDE_SKILL_DIR}` = `skills/generate-slides`, so `$VG` = repo root):

Run: `bash -c 'VG="skills/generate-slides/../.."; ls "$VG/scripts/ops/render_canvas.py"'`
Expected: the path prints (file exists).

- [ ] **Step 3: Commit**

```bash
git add skills/generate-slides/SKILL.md skills/generate-doc/SKILL.md
git commit -m "docs(skills): location- and brand-aware render/grade commands"
```

### Task 12: `visgen-setup` bootstrap skill

**Files:**
- Create: `skills/visgen-setup/SKILL.md`

**Interfaces:**
- Produces: a skill that, run in a working repo, guarantees a dedicated project branch and scaffolds the override + output wiring.

- [ ] **Step 1: Write `skills/visgen-setup/SKILL.md`.** Frontmatter + a numbered, copy-pasteable procedure. It MUST:
  1. Detect the submodule dir (default `visual-generation/`) and its current branch; if on `master`/`main`, STOP and prompt the user for a project branch name, then `git -C visual-generation checkout -b <name>` and `git -C visual-generation push -u origin <name>`.
  2. Scaffold `<working-repo>/brand/` if absent by copying the studio default as an editable starting point: `cp -r visual-generation/brand/* brand/` (user then edits tokens/logos for a non-VISEMI theme; for VISEMI leave as-is).
  3. Ensure `<working-repo>/.gitignore` contains `output/`.
  4. Ensure `<working-repo>/.claude/settings.json` has the `extraKnownMarketplaces` + `enabledPlugins` entries from Phase 7 Task 20 Step 2 (print them if the file must be created; ask before editing an existing settings.json).
  5. Run `uv run --project visual-generation python -c "import playwright"` (or `uv sync --project visual-generation`) once so the submodule env is ready.
  6. Print a "ready" summary with a sample render command.

Frontmatter:
```markdown
---
name: visgen-setup
description: Bootstrap the visual-generation studio inside a working repo. Use once after adding visual-generation as a submodule, or whenever the submodule is on master/main and needs a dedicated project branch. Creates the project branch, scaffolds the brand/ override and output/ gitignore, and enables the plugin. Also use when a render was refused with a "create a dedicated project branch" message.
---
```

- [ ] **Step 2: Lint the frontmatter is parseable**

Run: `uv run python -c "import pathlib,re,sys; t=pathlib.Path('skills/visgen-setup/SKILL.md').read_text(encoding='utf-8'); assert t.startswith('---') and 'name: visgen-setup' in t; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add skills/visgen-setup/SKILL.md
git commit -m "feat(skill): visgen-setup bootstrap (project branch + brand + output wiring)"
```

---

## Phase 4 — visual-designer agent

### Task 13: Port the `visual-designer` agent

**Files:**
- Create: `agents/visual-designer.md`
- Reference: `cat-canh-program-management/.claude/agents/slide-designer.md` (the generalization source — read it during authoring)

**Interfaces:**
- Produces: an agent that routes a brief to the right skill/format, authors content, renders, grades, iterates (cap 4), eyeballs, and reports.

- [ ] **Step 1: Write `agents/visual-designer.md`.** Frontmatter (`name: visual-designer`, a `description` that triggers on "make a visual/deck/report/post/poster from this brief") + body that encodes the loop:
  1. Read the brief; pick the skill (`generate-slides` | `generate-doc` | `generate-social-post` | `generate-poster`) and format from what the brief implies.
  2. Author content JSON / Markdown — facts from the brief only, never invented; ask when a fact is missing.
  3. Render with the canonical command from Task 11 (`$VG` + `--brand brand` + `--out output/<name>`).
  4. Grade: brand-lint always; rubric if `ANTHROPIC_API_KEY` present.
  5. On overflow/lint failure fix content (trim/split), re-render; cap 4 iterations, then surface the failing report.
  6. Eyeball the PNGs against intent.
  7. Report: output paths, verification results, and any facts it had to ask about.
  The body must reference the shared engine/brand/graders by the plugin paths, carry no private brand values, and honor the branch guard (if a render is refused, run `visgen-setup`).

- [ ] **Step 2: Validate frontmatter**

Run: `uv run python -c "import pathlib; t=pathlib.Path('agents/visual-designer.md').read_text(encoding='utf-8'); assert t.startswith('---') and 'name: visual-designer' in t; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add agents/visual-designer.md
git commit -m "feat(agent): visual-designer end-to-end brief->render->grade->iterate"
```

---

## Phase 5 — generate-social-post (M3)

> The canvas engine + formats registry already support `square` (1080x1080), `portrait` (1080x1350), `story` (1080x1920), `link` (1200x627). This phase adds layouts, a skill, an exemplar, and an eval task on top — no engine changes. Mirror the proven structure of `skills/generate-slides` (SKILL.md + `templates/layouts/*.html.j2` built on the shared `templates/components.html.j2` macros + `assets/base.css`/`components.css`, tokens only).

### Task 14: Social layout schemas

**Files:**
- Modify: `scripts/lib/visgen/schema.py` (add to `LAYOUTS`)
- Test: `scripts/tests/test_schema_social_layouts.py`

**Interfaces:**
- Consumes: existing `LAYOUTS` dict + `validate_document` in `schema.py`.
- Produces: layout keys `social-hero`, `social-quote`, `social-stat`, `social-announce`, `social-cta` with required-field lists.

- [ ] **Step 1: Read `schema.py` to learn the exact `LAYOUTS` entry shape** (required-field declaration used by the 17 existing layouts). Match it.

Run: `uv run python -c "from visgen.schema import LAYOUTS; import json; print(list(LAYOUTS)[:3]); print(LAYOUTS[list(LAYOUTS)[0]])"`

- [ ] **Step 2: Write the failing test** (mirror `test_schema_event_layouts.py`):

```python
from visgen.schema import validate_document

def _doc(layout, content):
    return {"meta": {"format": "square", "theme": "light", "title": "t"},
            "pages": [{"layout": layout, "content": content}]}

def test_social_hero_requires_headline():
    import pytest
    from visgen.schema import SchemaError
    with pytest.raises(SchemaError):
        validate_document(_doc("social-hero", {}))

def test_social_hero_valid():
    validate_document(_doc("social-hero", {"headline": "Cất Cánh", "sub": "x"}))
```

- [ ] **Step 3: Run to verify it fails**

Run: `uv run pytest scripts/tests/test_schema_social_layouts.py -q`
Expected: FAIL (`social-hero` unknown layout)

- [ ] **Step 4: Add the layout entries to `LAYOUTS` in `schema.py`** following the existing shape. Suggested required fields: `social-hero`→`{headline}` (optional `sub`, `photo`, `qr`, `cta`); `social-quote`→`{quote}` (optional `attribution`, `photo`); `social-stat`→`{stat, label}`; `social-announce`→`{headline, detail}`; `social-cta`→`{headline, cta}` (optional `qr`).

- [ ] **Step 5: Run to verify it passes**

Run: `uv run pytest scripts/tests/test_schema_social_layouts.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/visgen/schema.py scripts/tests/test_schema_social_layouts.py
git commit -m "feat(social): schemas for five social-post layouts"
```

### Task 15: Social templates

**Files:**
- Create: `skills/generate-social-post/templates/base.html.j2` (or reuse the shared base by importing components)
- Create: `skills/generate-social-post/templates/layouts/{social-hero,social-quote,social-stat,social-announce,social-cta}.html.j2`
- Create: `skills/generate-social-post/assets/base.css`, `skills/generate-social-post/assets/components.css` (tokens only; bigger type floors for feed legibility)

**Interfaces:**
- Consumes: the shared macro library. The renderer resolves templates from `skill_dir/templates`; social layouts render at `meta.format` sizes.

- [ ] **Step 1: Copy the slides base + macros as the starting point**, then tune type scale up for feed legibility:

```bash
mkdir -p skills/generate-social-post/templates/layouts skills/generate-social-post/assets
cp skills/generate-slides/templates/base.html.j2 skills/generate-social-post/templates/base.html.j2
cp skills/generate-slides/templates/components.html.j2 skills/generate-social-post/templates/components.html.j2
cp skills/generate-slides/assets/base.css skills/generate-social-post/assets/base.css
cp skills/generate-slides/assets/components.css skills/generate-social-post/assets/components.css
```

- [ ] **Step 2: Author the five layout templates** (one message per canvas, large type, optional photo + navy scrim, optional QR/CTA), tokens only, no hardcoded hexes. Each consumes exactly the fields declared in Task 14.

- [ ] **Step 3: Assert no literal hex in the new CSS/templates**

Run: `grep -rniE "#[0-9a-fA-F]{3,6}\b" skills/generate-social-post/assets skills/generate-social-post/templates | grep -viE "components.css:.*/\*"` (should print nothing but comments; fix any real hits to `var(--token)`).

- [ ] **Step 4: Commit**

```bash
git add skills/generate-social-post/templates skills/generate-social-post/assets
git commit -m "feat(social): five feed-legible layout templates (tokens only)"
```

### Task 16: Social skill + exemplar + eval task (verified render)

**Files:**
- Create: `skills/generate-social-post/SKILL.md`
- Create: `scripts/evals/references/social-square.content.json`
- Create: `scripts/evals/tasks/social-square.json`
- Modify: `scripts/ops/render_canvas.py` (add `--skill-dir`, Step 1)

**Interfaces:**
- Consumes: the render CLI's `--skill-dir` flag (added in Step 1). The engine already supports it: `canvas.render_canvas(doc, out_dir, fmt, skill_dir=None)` threads `skill_dir` into `render_document(doc, skill_dir=...)`; only the CLI lacks the flag.

- [ ] **Step 1: Add `--skill-dir` to `render_canvas.py`** (confirmed the engine already accepts `skill_dir`; only the CLI needs it). In `main()`:

```python
    ap.add_argument("--skill-dir", help="Template/skill dir (default: skills/generate-slides).")
    # ...
    skill_dir = Path(args.skill_dir) if args.skill_dir else None
    report = render_canvas(doc, out, fmt=args.format, skill_dir=skill_dir)
```
(When `skill_dir` is None the engine's `render_document` defaults to `DEFAULT_SKILL_DIR`, so slides are unchanged.)

- [ ] **Step 2: Write `skills/generate-social-post/SKILL.md`** — frontmatter with a triggering description ("social post / Instagram / Facebook / LinkedIn image / square / story / feed graphic"), the size table, feed-legibility writing rules, the layout table (from Task 14), and the canonical render/grade commands from Task 11 with the social skill-dir.

- [ ] **Step 3: Author `social-square.content.json`** (a real VISEMI/Cất Cánh single-message post, facts placeholder-free, one `square` page) and `social-square.json` eval task (`{"expected_page_px":[1080,1080],"required_strings":[...],"forbidden_strings":["Cat Canh"]}`).

- [ ] **Step 4: Render + grade the exemplar**

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py scripts/evals/references/social-square.content.json --format both --out output/social-square --skill-dir skills/generate-social-post
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_brand.py output/social-square --task scripts/evals/tasks/social-square.json
```
Expected: `overflow: false`; grade `"passed": true`. **Eyeball `output/social-square/png/page-01.png`.**

- [ ] **Step 5: Confirm the eval runner picks it up**

Run: `uv run python scripts/evals/run_evals.py`
Expected: the social task appears and passes.

- [ ] **Step 6: Commit**

```bash
git add skills/generate-social-post/SKILL.md scripts/evals/references/social-square.content.json scripts/evals/tasks/social-square.json scripts/ops/render_canvas.py
git commit -m "feat(social): generate-social-post skill + exemplar + eval task"
```

---

## Phase 6 — generate-poster (M4)

> Sizes already registered: `poster-a` (1240x1748), `banner-wide` (2048x1448), `email-header` (1200x400). Same approach as Phase 5.

### Task 17: Poster layout schemas

**Files:**
- Modify: `scripts/lib/visgen/schema.py`
- Test: `scripts/tests/test_schema_poster_layouts.py`

- [ ] **Step 1: Write the failing test** (mirror Task 14 Step 2 with `format: "poster-a"` and layouts `poster-event`, `banner-headline`, `email-header`).
- [ ] **Step 2: Run — expect FAIL** (`uv run pytest scripts/tests/test_schema_poster_layouts.py -q`).
- [ ] **Step 3: Add `LAYOUTS` entries.** Suggested: `poster-event`→`{title, when, where}` (optional `qr`, `photo`, `details`); `banner-headline`→`{headline}` (optional `sub`, `cta`); `email-header`→`{headline}` (optional `sub`).
- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** (`git commit -m "feat(poster): schemas for poster/banner/email-header layouts"`).

### Task 18: Poster templates

**Files:**
- Create: `skills/generate-poster/templates/{base.html.j2,components.html.j2,layouts/*.html.j2}`, `skills/generate-poster/assets/{base.css,components.css}`

- [ ] **Step 1: Seed from slides templates** (as Task 15 Step 1, into `skills/generate-poster/`).
- [ ] **Step 2: Author `poster-event.html.j2`, `banner-headline.html.j2`, `email-header.html.j2`** (denser hierarchy than social; tokens only).
- [ ] **Step 3: Assert no literal hex** (as Task 15 Step 3 for the poster dirs).
- [ ] **Step 4: Commit** (`git commit -m "feat(poster): poster/banner/email-header templates (tokens only)"`).

### Task 19: Poster skill + exemplar + eval task (verified render)

**Files:**
- Create: `skills/generate-poster/SKILL.md`, `scripts/evals/references/poster-event.content.json`, `scripts/evals/tasks/poster-event.json`

- [ ] **Step 1: Write `skills/generate-poster/SKILL.md`** — triggering description ("poster / event graphic / banner / email header / flyer"), size table, density rules, layout table, canonical commands with the poster skill-dir.
- [ ] **Step 2: Author the exemplar** (`poster-a` page, real facts, no placeholders) + eval task (`expected_page_px:[1240,1748]`).
- [ ] **Step 3: Render + grade + eyeball**

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py scripts/evals/references/poster-event.content.json --format both --out output/poster-event --skill-dir skills/generate-poster
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_brand.py output/poster-event --task scripts/evals/tasks/poster-event.json
```
Expected: `overflow: false`, `"passed": true`. **Eyeball the PNG.**

- [ ] **Step 4: Full suite + eval runner green**

Run: `uv run pytest scripts/tests -q && uv run python scripts/evals/run_evals.py`
Expected: all PASS; social + poster tasks included.

- [ ] **Step 5: Commit** (`git commit -m "feat(poster): generate-poster skill + exemplar + eval task"`).

---

## Phase 7 — Wire the studio into cat-canh (working repo)

> This phase edits **`D:\2-VISEMI\cat-canh-program-management`** (a separate git repo). Do these steps there. Requires the plugin branches above to be pushed to `origin` first.

### Task 20: Add submodule, enable plugin, create project branch, retire frozen copies

**Files (in cat-canh):**
- Create/modify: `.gitmodules` (submodule entry), `.claude/settings.json`, `.gitignore`
- Delete: `.claude/skills/generate-slides/`, `.claude/agents/slide-designer.md`
- Add: `visual-generation/` submodule

**Interfaces:**
- Consumes: the pushed `visual-generation` repo (master) and its plugin manifests.

- [ ] **Step 1: Add the submodule at the working-repo root**

```bash
cd "D:/2-VISEMI/cat-canh-program-management"
git submodule add https://github.com/lanhp-vn/visual-generation.git visual-generation
```

- [ ] **Step 2: Enable the plugin in committed project settings.** Merge into `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "visual-generation": { "source": { "source": "directory", "path": "./visual-generation" } }
  },
  "enabledPlugins": { "visual-generation@visual-generation": true }
}
```
(Preserve existing `permissions`/`hooks`/`enabledPlugins` keys — add, do not overwrite. `playwright@claude-plugins-official` stays.)

- [ ] **Step 3: Run `visgen-setup`** (in cat-canh) to create the project branch + scaffold. Or manually:

```bash
git -C visual-generation checkout -b visemi-catcanh
git -C visual-generation push -u origin visemi-catcanh
# cat-canh IS VISEMI: use the studio's default theme, so no brand/ override is required.
# (For a future non-VISEMI repo: cp -r visual-generation/brand/* brand/ and edit.)
```

- [ ] **Step 4: Ensure `output/` is git-ignored** in cat-canh `.gitignore` (add the line if missing). `slides/` is already ignored.

- [ ] **Step 5: Retire the colliding frozen copies**

```bash
git rm -r .claude/skills/generate-slides
git rm .claude/agents/slide-designer.md
```

- [ ] **Step 6: Acceptance — render an existing brief through the plugin, from cat-canh, CWD = cat-canh root.** Pick an existing `programs/*/*.content.json` (e.g. `programs/kickoff-meeting/kickoff.content.json`):

```bash
VG="visual-generation"
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  programs/kickoff-meeting/kickoff.content.json --format both --out output/kickoff
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/grade_brand.py" output/kickoff
```
Expected: renders with `overflow: false`; grade `"passed": true`. **Eyeball `output/kickoff/png/`.** Confirms portability: engine invoked from the parent, CWD = parent, output in the parent, brand defaulted to VISEMI.

- [ ] **Step 7: Confirm the branch guard fires on master** (negative test)

```bash
git -C visual-generation checkout master
PYTHONIOENCODING=utf-8 uv run --project visual-generation python visual-generation/scripts/ops/render_canvas.py programs/kickoff-meeting/kickoff.content.json --out output/_x ; echo "exit=$?"
git -C visual-generation checkout visemi-catcanh
```
Expected: refused with the "create a dedicated project branch" message, `exit=2`.

- [ ] **Step 8: Commit (in cat-canh)**

```bash
git add .gitmodules visual-generation .claude/settings.json .gitignore
git commit -m "feat: consume visual-generation studio as plugin-submodule; retire frozen slide skill"
```

---

## Self-Review

**Spec coverage:**
- Consumption model / plugin discovery → Tasks 1, 20. ✓
- Layout move to `skills/`/`agents/` → Task 2. ✓
- Brand injection (resolver, tokens, lint, html_render, CLIs, integration test) → Tasks 3-8. ✓
- CWD-independence → already `__file__`-anchored; verified by Tasks 6/8/20 running from the parent. ✓
- Branch workflow + guard + "always asked" → Tasks 9, 10, 12; enforced in Task 20 Step 7. ✓
- `visgen-setup` bootstrap → Task 12. ✓
- `visual-designer` agent → Task 13. ✓
- M3 social / M4 poster (skills, layouts, schema, exemplar, eval task) → Tasks 14-19. ✓
- Retire parent frozen copies → Task 20 Step 5. ✓
- Content/brand/output locations → Task 11 (commands), Task 20 (wiring). ✓
- Knowledge-growth (knowledge-update in plugin, runs from working repo) → shipped by the move in Task 2; operates on the project branch. ✓

**Placeholder scan:** No "TBD/TODO". Content-authoring tasks (12, 13, 15, 16, 18, 19) specify exact files, required fields, and a concrete render+lint+eyeball verification gate rather than pre-writing creative Jinja/prose — the correct altitude for template/exemplar work, and every one ends in a runnable green check.

**Type/name consistency:** `active_brand_dir()` / `DEFAULT_BRAND` (Task 3) used identically in Tasks 4/6/8. `palette()` call-time (Task 5) matches its use in Task 8. `branch_guard_message`/`check_branch` (Task 9) used verbatim in Task 10. `VISGEN_BRAND` env var consistent across Tasks 3/7. Enable key `visual-generation@visual-generation` consistent across Tasks 1/20. `${CLAUDE_SKILL_DIR}/../..` consistent across Tasks 11/13.

**Verified during planning:** `canvas.render_canvas(...)` already threads a `skill_dir` param into `render_document`, so Phases 5-6 only add a `--skill-dir` CLI flag (Task 16 Step 1) to point renders at the social/poster template dirs — no engine change. All nine formats are pre-registered in `formats.py`, so social/poster need no size work.
