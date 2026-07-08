# Visual Generation M2 — Document Renderer + generate-doc Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the second renderer to the shared engine — a Markdown+front-matter document renderer that paginates reports and handbooks to A4 PDF (selectable text) + per-page PNGs via Paged.js in the existing Playwright/Chromium stack — plus the thin `generate-doc` skill, document graders (`doc_lint.py`), and two real Cất Cánh exemplars, all reusing the M1 engine (tokens, theme assembly, brand-lint, Playwright driving) with no parallel copy.

**Architecture:** Markdown with YAML front-matter → HTML via `python-markdown` (`extra` + `toc` + `admonition`) → poured into a doc template → paginated by a vendored, inlined **Paged.js** polyfill in headless Chromium → printed to an A4 PDF and screenshotted per page. The renderer reuses `visgen.tokens` (theme CSS + lint palette), `visgen.html_render`'s font-embed/theme assembly (refactored into a shared `_fonts_and_tokens`), `visgen.brand_lint.lint_html` (brand surface), and the Playwright pattern from `visgen.canvas`. Reports and handbooks are one pipeline over one stylesheet with `.report`/`.handbook` body-class modifiers and two cover partials. Documents are light-theme only (print).

**Tech Stack:** Python ≥3.12 via `uv`, Jinja2, Playwright (chromium), `python-markdown`, `PyYAML`, `pypdf`, Paged.js 0.4.3 (vendored, MIT), segno/anthropic (unchanged), pytest.

**Spec:** `docs/superpowers/specs/2026-07-08-visual-generation-skills-design.md` (approved) — sections "Document renderer (reports, handbooks)", "Skills (thin) and agent", "Graders & evals". This plan covers Milestone M2 only. M1 is done and merged.

## Decisions resolved in planning (interview 2026-07-08)

| Question | Decision |
|---|---|
| Paged.js vendoring | Vendor pinned `paged.polyfill.js` (**0.4.3**, MIT) under `scripts/lib/visgen/vendor/`, **inlined** into the doc HTML at render time like the base64 fonts; THIRD_PARTY_LICENSES entry. index.html is self-contained and offline-deterministic. |
| A4 sizing | A4 is **not** added to the canvas `FORMATS` pixel registry. Page size is a print size via CSS `@page { size: A4 }`; per-page PNG pixel size derives from the rendered `.pagedjs_page` box. |
| Markdown extensions | `python-markdown` with `["extra", "toc", "admonition"]` — tables, attr_list, fenced_code, footnotes, def_list, abbr, md_in_html (from `extra`); heading ids + TOC nav (`toc`); callouts mapped to functional status colors (`admonition`). |
| Report vs handbook | One pipeline, one `document.css` with `.report`/`.handbook` modifiers, two cover partials. Both single-column. Handbook adds chapter-divider pages (body `h1` breaks to a new page, styled opener) + a running chapter name in the header; report flows sections continuously with the doc title in the header. |
| Exemplar facts | Reuse vetted Cất Cánh facts from the repo's `scripts/evals/references/*.content.json` and cat-canh `data/reports/` + kickoff-meeting materials. Cohort 1 is framed as plan + progress (no fabricated results). Any genuinely-absent fact is an explicit `[TK: operator confirm]` marker; a permanent test forbids `TK:` in committed exemplars, forcing resolution before commit. **No real fellow PII in committed fixtures** — program-level / aggregate facts only. |

## Global Constraints

- **Source repo for facts/references (read-only):** `D:\2-VISEMI\cat-canh-program-management` (`CC="/d/2-VISEMI/cat-canh-program-management"`). Never modify it. For exemplar facts, use the Cất Cánh Fellowship material (`data/reports/`, `programs/kickoff-meeting/`) and the repo's own slide exemplars — **not** `programs/claude-corp/` (that is the unrelated Anthropic "Claude Corps" program).
- **DRY / Single Source of Truth:** brand values only in `brand/tokens.json`; render/grade logic only in `scripts/lib/visgen/`; schemas only in `schema.py`; rubric language only in `scripts/evals/rubrics/`. No hardcoded hex outside `brand/` (generated files excepted). The document renderer REUSES the M1 engine — it never copies theme assembly, font embedding, palette, or the Playwright pattern.
- **Brand locked:** palette navy `#001669`, purple `#262538`, green `#01B68B`, white, token ramps, gold `#F5B433` sparing, cyan `#00E5FF` very sparing. Functional status colors `--warn #F5A524` / `--bad #DC2626` / `--good` are for functional use only (callouts, status), never decorative fills. Be Vietnam Pro only (no mono font — code styled in the sans stack). No em dash (U+2014), no en dash (U+2013), no emojis. Vietnamese keeps diacritics ("Cất Cánh" never "Cat Canh").
- **Documents are light-theme only** (print/PDF); doc front-matter has no `theme` field.
- **Verify by rendering:** nothing is done until the PDF + page PNGs render with no overflow, `doc_lint` and brand-lint report `passed: true`, and the PNGs were eyeballed.
- **Never commit rendered output** — `output/` and `scripts/evals/runs/` are git-ignored.
- Run Python via `uv run`; prefix commands printing Vietnamese with `PYTHONIOENCODING=utf-8`.
- Commit after every green test cycle (each task's final step).

---

### Task 1: Dependencies + Paged.js vendoring

**Files:**
- Modify: `pyproject.toml` (add `markdown`, `pyyaml`, `pypdf`)
- Create: `scripts/lib/visgen/vendor/paged.polyfill.js` (fetched + pinned)
- Create: `scripts/lib/visgen/vendor/THIRD_PARTY_LICENSES`
- Test: `scripts/tests/test_doc_deps.py`

**Interfaces:**
- Produces (consumed by Tasks 2, 4, 6): the `markdown`, `yaml`, `pypdf` importable modules; the vendored `paged.polyfill.js` at `visgen/vendor/paged.polyfill.js` (read + inlined by `html_render.render_doc_html`, Task 4).

- [ ] **Step 1: Write the failing test**

`scripts/tests/test_doc_deps.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_doc_deps.py -v`
Expected: FAIL (`pypdf` not importable / vendor dir missing).

- [ ] **Step 3: Add the Python dependencies**

Run:
```bash
cd /d/2-VISEMI/visual-generation
uv add markdown pyyaml pypdf
```
This edits `pyproject.toml` `[project].dependencies` and refreshes `uv.lock`. Verify `pyproject.toml` now lists `markdown`, `pyyaml`, `pypdf` alongside the existing `jinja2`, `playwright`, `segno`, `anthropic`.

- [ ] **Step 4: Vendor the Paged.js polyfill (pinned, no CDN at render time)**

Fetch the pinned release once and commit it (after this, renders never touch the network):
```bash
mkdir -p scripts/lib/visgen/vendor
curl -fsSL https://cdn.jsdelivr.net/npm/pagedjs@0.4.3/dist/paged.polyfill.js \
  -o scripts/lib/visgen/vendor/paged.polyfill.js
wc -c scripts/lib/visgen/vendor/paged.polyfill.js   # expect ~400000+ bytes
```
If `curl` is unavailable, download `https://cdn.jsdelivr.net/npm/pagedjs@0.4.3/dist/paged.polyfill.js` by any means and save it to that exact path. Do not minify or edit it.

- [ ] **Step 5: Record the license**

`scripts/lib/visgen/vendor/THIRD_PARTY_LICENSES`:
```
Paged.js (pagedjs) v0.4.3 - https://gitlab.coko.foundation/pagedjs/pagedjs
Vendored file: paged.polyfill.js
License: MIT

Copyright (c) 2018-2023 Coko Foundation and Paged.js contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest scripts/tests/test_doc_deps.py -v`
Expected: 3 PASS.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock scripts/lib/visgen/vendor scripts/tests/test_doc_deps.py
git commit -m "feat(m2): deps (markdown, pyyaml, pypdf) + vendored Paged.js 0.4.3 polyfill"
```

---

### Task 2: Front-matter schema + Markdown parse pipeline

**Files:**
- Modify: `scripts/lib/visgen/schema.py` (add `DOC_TEMPLATES`, `DOC_LANGS`, `validate_frontmatter`)
- Create: `scripts/lib/visgen/document.py` (pure functions only this task: `parse_frontmatter`, `markdown_to_html`, `DOC_EXTENSIONS`)
- Test: `scripts/tests/test_doc_schema.py`

**Interfaces:**
- Consumes: `visgen.schema.SchemaError` (existing).
- Produces (consumed by Task 5):
  - `visgen.schema.validate_frontmatter(meta: dict) -> None` — raises `SchemaError`; requires `template ∈ {"report","handbook"}`, non-empty string `title`, `lang ∈ {"en","vi"}` if present.
  - `visgen.document.parse_frontmatter(text: str) -> tuple[dict, str]` — splits a leading `---\n…\n---\n` YAML block; returns `(meta_dict, body_markdown)`; raises `SchemaError` if the fence is missing or not a mapping.
  - `visgen.document.markdown_to_html(body_md: str) -> tuple[str, str]` — returns `(body_html, toc_html)`; `toc_html` is python-markdown's `<div class="toc">…</div>` (empty string if no headings).
  - `visgen.document.DOC_EXTENSIONS: list[str]` == `["extra", "toc", "admonition"]`.
- Note: `document.py` must NOT import Playwright at module top (Task 5 adds `render_doc` with a lazy import inside the function), so these parse functions stay importable without a browser.

- [ ] **Step 1: Write the failing tests**

`scripts/tests/test_doc_schema.py`:
```python
import pytest

from visgen.schema import validate_frontmatter, SchemaError
from visgen.document import parse_frontmatter, markdown_to_html, DOC_EXTENSIONS


def test_validate_frontmatter_accepts_report_and_handbook():
    validate_frontmatter({"template": "report", "title": "X"})
    validate_frontmatter({"template": "handbook", "title": "X", "lang": "vi"})


def test_validate_frontmatter_rejects_unknown_template():
    with pytest.raises(SchemaError, match="template"):
        validate_frontmatter({"template": "flyer", "title": "X"})


def test_validate_frontmatter_requires_nonempty_title():
    with pytest.raises(SchemaError, match="title"):
        validate_frontmatter({"template": "report"})
    with pytest.raises(SchemaError, match="title"):
        validate_frontmatter({"template": "report", "title": "  "})


def test_validate_frontmatter_rejects_bad_lang():
    with pytest.raises(SchemaError, match="lang"):
        validate_frontmatter({"template": "report", "title": "X", "lang": "fr"})


def test_parse_frontmatter_splits_yaml_and_body():
    text = "---\ntemplate: report\ntitle: Hello\n---\n\n# Section\n\nBody text.\n"
    meta, body = parse_frontmatter(text)
    assert meta["template"] == "report"
    assert meta["title"] == "Hello"
    assert body.lstrip().startswith("# Section")


def test_parse_frontmatter_requires_fence():
    with pytest.raises(SchemaError):
        parse_frontmatter("# no front-matter here\n")


def test_doc_extensions_value():
    assert DOC_EXTENSIONS == ["extra", "toc", "admonition"]


def test_markdown_to_html_tables_headings_toc():
    body_html, toc_html = markdown_to_html(
        "# Intro\n\n## Sub\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert "<table>" in body_html
    assert 'id="intro"' in body_html      # toc extension slugs + ids headings
    assert 'href="#intro"' in toc_html    # toc nav links to it


def test_markdown_to_html_admonition_callout():
    body_html, _ = markdown_to_html('!!! warning "Heads up"\n    Be careful.\n')
    assert 'class="admonition warning"' in body_html


def test_markdown_to_html_no_smart_dashes():
    """extra/toc/admonition must not turn -- / --- into en/em dashes (no smarty)."""
    body_html, _ = markdown_to_html("A range 10--20 and a break --- like so.\n")
    assert "–" not in body_html  # en dash
    assert "—" not in body_html  # em dash
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest scripts/tests/test_doc_schema.py -v`
Expected: FAIL (`validate_frontmatter` / `visgen.document` not defined).

- [ ] **Step 3: Add `validate_frontmatter` to `scripts/lib/visgen/schema.py`**

Append at the end of `scripts/lib/visgen/schema.py`:
```python

# --- Document front-matter (generate-doc) -------------------------------------
DOC_TEMPLATES = {"report", "handbook"}
DOC_LANGS = {"en", "vi"}


def validate_frontmatter(meta: dict) -> None:
    """Validate a document's YAML front-matter. Facts/styling never live here;
    this only checks the template family, a title, and the language code."""
    if not isinstance(meta, dict):
        raise SchemaError("front-matter must be a mapping")
    template = meta.get("template")
    if template not in DOC_TEMPLATES:
        raise SchemaError(
            f"front-matter 'template' must be one of {sorted(DOC_TEMPLATES)}, got {template!r}")
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SchemaError("front-matter 'title' is required and must be a non-empty string")
    lang = meta.get("lang", "en")
    if lang not in DOC_LANGS:
        raise SchemaError(f"front-matter 'lang' must be one of {sorted(DOC_LANGS)}, got {lang!r}")
```

- [ ] **Step 4: Create `scripts/lib/visgen/document.py`** (pure functions only for now)

```python
"""Render a Markdown+front-matter document to an A4 PDF + per-page PNGs via a
vendored, inlined Paged.js polyfill in headless Chromium. Second renderer on the
shared engine: it reuses visgen.tokens / html_render theme assembly / brand_lint
and the Playwright pattern from visgen.canvas. Local-only; no credentials.

This module is import-safe without a browser: Playwright is imported lazily
inside render_doc (added in a later task), so parse_frontmatter / markdown_to_html
can be used and tested standalone."""
import re

import markdown
import yaml

from visgen.schema import SchemaError

DOC_EXTENSIONS = ["extra", "toc", "admonition"]

_FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a leading `--- yaml --- ` block. Returns (meta, body_markdown)."""
    m = _FRONT_MATTER.match(text)
    if not m:
        raise SchemaError("document must start with a YAML front-matter block delimited by '---'")
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise SchemaError("front-matter must be a mapping")
    return meta, text[m.end():]


def markdown_to_html(body_md: str) -> tuple[str, str]:
    """Convert body Markdown to (body_html, toc_html). toc_html is python-markdown's
    <div class="toc"> nav; Paged.js fills its real page numbers via target-counter."""
    md = markdown.Markdown(
        extensions=DOC_EXTENSIONS,
        extension_configs={"toc": {"toc_depth": "1-3"}},
        output_format="html5",
    )
    body_html = md.convert(body_md)
    toc_html = getattr(md, "toc", "") or ""
    return body_html, toc_html
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/test_doc_schema.py -v`
Expected: all PASS. (If `test_markdown_to_html_no_smart_dashes` fails, confirm no `smarty` extension leaked in — `DOC_EXTENSIONS` must be exactly `["extra","toc","admonition"]`; `extra` does not include `smarty`.)

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/visgen/schema.py scripts/lib/visgen/document.py scripts/tests/test_doc_schema.py
git commit -m "feat(m2): doc front-matter schema + Markdown->HTML/TOC parse pipeline"
```

---

### Task 3: Doc templates + `document.css`

**Files:**
- Create: `.claude/skills/generate-doc/templates/base.html.j2`
- Create: `.claude/skills/generate-doc/templates/partials/cover-report.html.j2`
- Create: `.claude/skills/generate-doc/templates/partials/cover-handbook.html.j2`
- Create: `.claude/skills/generate-doc/assets/document.css`
- Test: `scripts/tests/test_doc_templates.py`

**Interfaces:**
- Consumes: `visgen.html_render.build_env` (existing Jinja env factory).
- Produces (consumed by Task 4's `render_doc_html`):
  - `templates/base.html.j2` — renders with context `{meta, body_html, toc_html, brand_css, document_css, pagedjs_js, logo}`; emits `<html>` with the cover partial, a `.toc-page` nav wrapping `toc_html`, a running `.brandmark`, `<main>{body_html}</main>`, and the inlined Paged.js at end of body. Defines `window.PagedConfig.after` to set `window.__PAGED_DONE`.
  - `partials/cover-{report,handbook}.html.j2` — cover markup per family, selected by `meta.template`.
  - `assets/document.css` — fully tokenized (var() refs only, no literal hex): reset, `@page` A4 + running chrome, cover, TOC with leader + `target-counter` page numbers, body typography, tables, `.admonition` callouts (functional status colors), figures/blockquote/code, and the `.report`/`.handbook` break rules.

- [ ] **Step 1: Write the failing tests**

`scripts/tests/test_doc_templates.py`:
```python
import re
from pathlib import Path

from visgen.html_render import build_env

DOC_SKILL = Path(__file__).resolve().parents[2] / ".claude/skills/generate-doc"


def test_document_css_has_no_literal_hex():
    """Brand values live only in tokens.json; document.css must be all var() refs."""
    css = (DOC_SKILL / "assets/document.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    assert re.findall(r"#[0-9a-fA-F]{3,6}\b", css) == []


def test_covers_and_base_exist():
    assert (DOC_SKILL / "templates/base.html.j2").is_file()
    assert (DOC_SKILL / "templates/partials/cover-report.html.j2").is_file()
    assert (DOC_SKILL / "templates/partials/cover-handbook.html.j2").is_file()


def _render(meta):
    env = build_env(DOC_SKILL / "templates")
    return env.get_template("base.html.j2").render(
        meta=meta,
        body_html='<h1 id="s">Sec</h1><p>Body.</p>',
        toc_html='<div class="toc"><ul><li><a href="#s">Sec</a></li></ul></div>',
        brand_css="/*brand*/", document_css="/*doc*/",
        pagedjs_js="/*PAGEDJS*/", logo="<svg id='logo'></svg>")


def test_base_report_has_cover_toc_body_pagedjs():
    html = _render({"template": "report", "title": "My Report", "lang": "en"})
    assert "cover-report" in html
    assert 'class="toc-page"' in html
    assert "Contents" in html
    assert "<main>" in html and "Sec" in html
    assert "/*PAGEDJS*/" in html            # Paged.js inlined
    assert "__PAGED_DONE" in html           # completion flag wired
    assert "My Report" in html


def test_base_handbook_selects_handbook_cover_and_lang():
    html = _render({"template": "handbook", "title": "Fellow Handbook", "lang": "vi"})
    assert "cover-handbook" in html
    assert "Nội dung" in html               # Vietnamese "Contents"
    assert 'class="doc handbook' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest scripts/tests/test_doc_templates.py -v`
Expected: FAIL (templates/CSS do not exist yet).

- [ ] **Step 3: Create `.claude/skills/generate-doc/templates/base.html.j2`**

```jinja
<!doctype html>
<html lang="{{ meta.lang | default('en') }}">
<head>
<meta charset="utf-8">
<title>{{ meta.title }}</title>
<script>window.PagedConfig = { auto: true, after: () => { window.__PAGED_DONE = true; } };</script>
<style>{{ brand_css | safe }}</style>
<style>{{ document_css | safe }}</style>
</head>
<body class="doc {{ meta.template }} lang-{{ meta.lang | default('en') }}">
  <div class="brandmark">{{ logo | safe }}</div>
  {% include "partials/cover-" ~ meta.template ~ ".html.j2" %}
  <nav class="toc-page">
    <h2 class="toc-title">{{ 'Nội dung' if meta.lang == 'vi' else 'Contents' }}</h2>
    {{ toc_html | safe }}
  </nav>
  <main>{{ body_html | safe }}</main>
  <script>{{ pagedjs_js | safe }}</script>
</body>
</html>
```

- [ ] **Step 4: Create `.claude/skills/generate-doc/templates/partials/cover-report.html.j2`**

```jinja
<header class="cover cover-report">
  <div class="cover-brand">{{ logo | safe }}</div>
  <p class="cover-eyebrow">{{ meta.eyebrow | default('Cất Cánh (Takeoff) Fellowship') }}</p>
  <h1 class="cover-title">{{ meta.title }}</h1>
  {% if meta.subtitle %}<p class="cover-subtitle">{{ meta.subtitle }}</p>{% endif %}
  <div class="cover-meta">
    {% if meta.date %}<span>{{ meta.date }}</span>{% endif %}
    {% if meta.audience %}<span>{{ meta.audience }}</span>{% endif %}
  </div>
  <p class="cover-orgline">{{ meta.orgline | default('VISEMI Foundation | visemi.org') }}</p>
</header>
```

- [ ] **Step 5: Create `.claude/skills/generate-doc/templates/partials/cover-handbook.html.j2`**

```jinja
<header class="cover cover-handbook">
  <div class="cover-brand">{{ logo | safe }}</div>
  <span class="cover-label">{{ 'Sổ tay' if meta.lang == 'vi' else 'Handbook' }}</span>
  <p class="cover-eyebrow">{{ meta.eyebrow | default('Cất Cánh (Takeoff) Fellowship') }}</p>
  <h1 class="cover-title">{{ meta.title }}</h1>
  {% if meta.subtitle %}<p class="cover-subtitle">{{ meta.subtitle }}</p>{% endif %}
  <div class="cover-meta">
    {% if meta.edition %}<span>{{ meta.edition }}</span>{% endif %}
    {% if meta.date %}<span>{{ meta.date }}</span>{% endif %}
  </div>
  <p class="cover-orgline">{{ meta.orgline | default('VISEMI Foundation | visemi.org') }}</p>
</header>
```

- [ ] **Step 6: Create `.claude/skills/generate-doc/assets/document.css`**

Every color/size is a `var(--token)` from `brand/tokens.json` (light theme). No literal hex (the Step 1 test enforces this). If you need a value that has no token, add a token to `tokens.json` for both themes and reference it, never a literal.

```css
/* generate-doc :: document.css - A4 print documents. All brand tokens (var refs
   only, no literal hex). Reset + @page chrome + cover + TOC + body typography +
   tables + callouts + figures, with .report / .handbook modifiers. */

*, *::before, *::after { box-sizing: border-box; }
html { font-family: var(--font-sans); color: var(--text); line-height: 1.55;
  -webkit-font-smoothing: antialiased; }
body { margin: 0; }

/* ============ PAGE GEOMETRY + RUNNING CHROME (Paged.js) ============ */
@page {
  size: A4;
  margin: 24mm 20mm 22mm 20mm;
  @top-left { content: element(brandmark); }
  @top-right { content: string(runhead); font-size: 9pt; letter-spacing: .10em;
    text-transform: uppercase; color: var(--muted); }
  @bottom-right { content: "Page " counter(page); font-size: 9pt; color: var(--muted); }
  @bottom-center { content: string(docfoot); font-size: 8.5pt; color: var(--faint); }
}
@page cover {
  margin: 0;
  @top-left { content: none; } @top-right { content: none; }
  @bottom-right { content: none; } @bottom-center { content: none; }
}

.brandmark { position: running(brandmark); }
.brandmark svg, .brandmark img { height: 15px; width: auto; display: block; }

/* running strings: report header = doc title; handbook header = current chapter */
.report .cover-title { string-set: runhead content(text); }
.handbook .cover-title { string-set: runhead content(text); }   /* until first chapter */
.handbook main h1 { string-set: runhead content(text); }
.cover-orgline { string-set: docfoot content(text); }

/* ============ COVER ============ */
.cover { page: cover; break-after: page; width: 210mm; height: 297mm;
  display: flex; flex-direction: column; justify-content: center;
  padding: 40mm 28mm; background: var(--bg-grad); color: var(--heading); }
.cover-brand svg, .cover-brand img { height: 34px; width: auto; margin-bottom: 24mm; }
.cover-eyebrow { font-size: 11pt; font-weight: 600; letter-spacing: .16em;
  text-transform: uppercase; color: var(--green-deep); margin: 0 0 10px; }
.cover-title { font-family: var(--font-display); font-size: 30pt; line-height: 1.1;
  font-weight: 700; color: var(--heading); margin: 0 0 12px; }
.cover-subtitle { font-size: 14pt; color: var(--text); margin: 0 0 20px; }
.cover-meta { display: flex; gap: 18px; font-size: 11pt; color: var(--muted); margin-top: auto; }
.cover-orgline { font-size: 9.5pt; color: var(--muted); margin-top: 14px; }
.cover-label { display: inline-block; align-self: flex-start; font-size: 10pt; font-weight: 600;
  letter-spacing: .14em; text-transform: uppercase; border-radius: 999px;
  padding: 4px 14px; margin-bottom: 16px; }

/* handbook cover: warmer, feature gradient, light text */
.handbook .cover { background: var(--grad-feature); color: var(--white); }
.handbook .cover-title, .handbook .cover-eyebrow { color: var(--white); }
.handbook .cover-subtitle { color: var(--green-200); }
.handbook .cover-meta, .handbook .cover-orgline { color: var(--navy-100); }
.handbook .cover-label { color: var(--white); border: 1px solid var(--line-strong); }

/* ============ TABLE OF CONTENTS ============ */
.toc-page { break-after: page; padding-top: 6mm; }
.toc-title { font-family: var(--font-display); font-size: 20pt; color: var(--heading);
  margin: 0 0 16px; padding-bottom: 8px; border-bottom: 2px solid var(--green); }
.toc ul { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 7px 0; }
.toc a { display: flex; align-items: baseline; text-decoration: none;
  color: var(--text); font-size: 11.5pt; }
.toc a::before { content: ""; order: 1; flex: 1; margin: 0 6px;
  border-bottom: 1px dotted var(--line); transform: translateY(-3px); }
.toc a::after { order: 2; content: target-counter(attr(href), page);
  color: var(--muted); font-variant-numeric: tabular-nums; }
.toc ul ul { padding-left: 16px; }
.toc ul ul a { font-size: 10.5pt; color: var(--muted); }

/* ============ BODY TYPOGRAPHY ============ */
main h1 { font-family: var(--font-display); font-size: 19pt; line-height: 1.2;
  font-weight: 700; color: var(--heading); margin: 0 0 10px; padding-top: 2mm;
  break-after: avoid; break-inside: avoid; }
main h2 { font-size: 14.5pt; font-weight: 600; color: var(--heading);
  margin: 18px 0 8px; break-after: avoid; break-inside: avoid; }
main h3 { font-size: 12pt; font-weight: 600; color: var(--navy-300);
  margin: 14px 0 6px; break-after: avoid; break-inside: avoid; }
main p { margin: 0 0 9px; font-size: 11pt; color: var(--text); orphans: 2; widows: 2; }
main a { color: var(--green-deep); text-decoration: none;
  border-bottom: 1px solid var(--line-strong); }
main ul, main ol { margin: 0 0 10px; padding-left: 20px; }
main li { margin: 3px 0; font-size: 11pt; color: var(--text); }
strong, b { color: var(--heading); font-weight: 600; }
hr { border: none; border-top: 1px solid var(--line); margin: 16px 0; }

/* handbook: each top-level heading opens a new chapter page */
.handbook main h1 { break-before: page; font-size: 24pt; padding-top: 8mm;
  border-top: 3px solid var(--green); }

/* ============ TABLES ============ */
table { width: 100%; border-collapse: collapse; margin: 10px 0 14px; font-size: 10.5pt;
  break-inside: auto; }
thead { display: table-header-group; }         /* repeat header when a table splits */
thead th { background: var(--navy); color: var(--white); text-align: left;
  font-weight: 600; padding: 7px 10px; }
tbody tr { break-inside: avoid; }
tbody td { padding: 6px 10px; border-bottom: 1px solid var(--line); color: var(--text); }
tbody tr:nth-child(even) td { background: var(--box); }
table caption { caption-side: top; text-align: left; font-size: 9.5pt;
  color: var(--muted); margin-bottom: 4px; }

/* ============ CALLOUTS (admonition) - functional status colors only ============ */
.admonition { border: 1px solid var(--line); border-left: 4px solid var(--navy);
  background: var(--box); border-radius: var(--radius-sm); padding: 10px 14px;
  margin: 12px 0; break-inside: avoid; }
.admonition-title { font-weight: 600; color: var(--heading); margin: 0 0 4px; font-size: 10.5pt; }
.admonition p { margin: 0; font-size: 10.5pt; color: var(--text); }
.admonition.tip, .admonition.success, .admonition.hint {
  border-left-color: var(--good); background: var(--green-100); }
.admonition.warning, .admonition.caution { border-left-color: var(--warn); }
.admonition.danger, .admonition.important, .admonition.error { border-left-color: var(--bad); }

/* ============ FIGURES / QUOTES / CODE ============ */
figure { margin: 14px 0; break-inside: avoid; }
figure img { width: 100%; height: auto; border-radius: var(--radius-sm); border: 1px solid var(--line); }
figcaption { font-size: 9.5pt; color: var(--muted); margin-top: 6px; break-before: avoid; }
blockquote { margin: 12px 0; padding: 6px 16px; border-left: 3px solid var(--green);
  color: var(--text-2); font-size: 11.5pt; font-style: italic; break-inside: avoid; }
blockquote p { margin: 4px 0; }
code { font-family: var(--font-sans); background: var(--box); padding: 1px 5px;
  border-radius: 4px; font-size: 10pt; }
pre { background: var(--box-2); border: 1px solid var(--line); border-radius: var(--radius-sm);
  padding: 12px 14px; overflow-x: auto; break-inside: avoid; }
pre code { background: none; padding: 0; }

/* ============ FOOTNOTES (extra) ============ */
.footnote { font-size: 9pt; color: var(--muted); }
.footnote ol { padding-left: 16px; }
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest scripts/tests/test_doc_templates.py -v`
Expected: all PASS. If `test_document_css_has_no_literal_hex` fails, the offending value must become a `tokens.json` token (both themes) referenced via `var(--...)`, not an allowlist exception.

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/generate-doc/templates .claude/skills/generate-doc/assets/document.css scripts/tests/test_doc_templates.py
git commit -m "feat(m2): doc templates (base + report/handbook covers) + tokenized document.css"
```

---

### Task 4: html_render doc assembly (shared `_fonts_and_tokens` + `render_doc_html`)

**Files:**
- Modify: `scripts/lib/visgen/html_render.py` (extract `_fonts_and_tokens`; add `DEFAULT_DOC_SKILL_DIR`, `render_doc_html`)
- Test: `scripts/tests/test_doc_html_render.py`

**Interfaces:**
- Consumes: `visgen.tokens.{BRAND_DIR, theme_css}`, the vendored `visgen/vendor/paged.polyfill.js` (Task 1), the doc templates + `document.css` (Task 3), existing `build_env` / `_embed_fonts`.
- Produces (consumed by Task 5):
  - `visgen.html_render._fonts_and_tokens(theme: str) -> str` — base64-embedded fonts + `theme_css(theme)`. The canvas `_theme_css` is refactored to call it, so canvas output is byte-identical (its tests stay green).
  - `visgen.html_render.render_doc_html(meta: dict, body_html: str, toc_html: str, skill_dir: Path | None = None) -> str` — full self-contained doc HTML; default `skill_dir` is `<repo>/.claude/skills/generate-doc`. Docs are light-theme only.
  - `visgen.html_render.DEFAULT_DOC_SKILL_DIR: Path`.

- [ ] **Step 1: Write the failing tests**

`scripts/tests/test_doc_html_render.py`:
```python
from visgen.html_render import (
    render_doc_html, _fonts_and_tokens, _theme_css, DEFAULT_SKILL_DIR,
)


def test_fonts_and_tokens_is_prefix_of_canvas_theme_css():
    """Refactor invariant: canvas _theme_css = _fonts_and_tokens + components.css,
    so canvas rendering is unchanged."""
    ft = _fonts_and_tokens("light")
    full = _theme_css("light", DEFAULT_SKILL_DIR)
    assert full.startswith(ft)
    assert "data:font/woff2;base64," in ft   # fonts embedded
    assert "--navy:#001669;" in ft            # light tokens present


def test_render_doc_html_is_self_contained():
    meta = {"template": "report", "title": "Cohort Report", "lang": "en",
            "subtitle": "Cohort 1", "date": "2026-07-08", "audience": "Partners"}
    body = '<h1 id="ov">Overview</h1><p>Body text.</p>'
    toc = '<div class="toc"><ul><li><a href="#ov">Overview</a></li></ul></div>'
    html = render_doc_html(meta, body, toc)
    # brand + doc CSS inlined
    assert "data:font/woff2;base64," in html      # fonts embedded, offline
    assert "--navy:#001669;" in html              # light theme tokens
    assert "@page" in html                        # document.css inlined
    # Paged.js inlined (no CDN, no external src)
    assert "PagedPolyfill" in html or "Paged" in html
    assert "src=" not in html.split("<main>")[0] or "http" not in html  # no external script/CDN
    # structure
    assert "cover-report" in html and "<main>" in html and "Overview" in html
    assert "__PAGED_DONE" in html


def test_render_doc_html_handbook_cover():
    html = render_doc_html({"template": "handbook", "title": "Fellow Handbook"},
                           "<p>x</p>", "")
    assert "cover-handbook" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest scripts/tests/test_doc_html_render.py -v`
Expected: FAIL (`render_doc_html` / `_fonts_and_tokens` not defined).

- [ ] **Step 3: Refactor `_theme_css` and add the doc assembly**

In `scripts/lib/visgen/html_render.py`:

First, add the doc skill default and the Paged.js path near the existing `DEFAULT_SKILL_DIR` (line 18):
```python
DEFAULT_SKILL_DIR = REPO_ROOT / ".claude/skills/generate-slides"
DEFAULT_DOC_SKILL_DIR = REPO_ROOT / ".claude/skills/generate-doc"
_PAGEDJS = Path(__file__).resolve().parent / "vendor/paged.polyfill.js"
```

Then replace the existing `_theme_css` function (lines 43-46) with the extracted helper plus the thin canvas wrapper:
```python
def _fonts_and_tokens(theme: str) -> str:
    """Shared brand CSS both renderers build on: base64-embedded Be Vietnam Pro
    (offline-deterministic) + the generated :root token block for `theme`."""
    fonts = _embed_fonts((BRAND_DIR / "fonts.css").read_text(encoding="utf-8"))
    return "\n".join([fonts, tokens_css(theme)])


def _theme_css(theme: str, skill_dir: Path) -> str:
    components = (skill_dir / "assets/components.css").read_text(encoding="utf-8")
    return "\n".join([_fonts_and_tokens(theme), components])
```

Then add `render_doc_html` at the end of the module:
```python
def render_doc_html(meta: dict, body_html: str, toc_html: str,
                    skill_dir: Path | None = None) -> str:
    """Assemble a document (front-matter + converted Markdown) into one
    self-contained HTML string: inlined brand CSS (light theme) + the skill's
    document.css + the vendored Paged.js polyfill, wrapped in the doc base
    template with the template-specific cover. Docs are light-theme only."""
    skill_dir = skill_dir or DEFAULT_DOC_SKILL_DIR
    env = build_env(skill_dir / "templates")
    brand_css = _fonts_and_tokens("light")
    document_css = (skill_dir / "assets/document.css").read_text(encoding="utf-8")
    pagedjs_js = _PAGEDJS.read_text(encoding="utf-8")
    logo = (BRAND_DIR / "logos/visemi-logo-color.svg").read_text(encoding="utf-8")
    base = env.get_template("base.html.j2")
    return base.render(meta=meta, body_html=body_html, toc_html=toc_html,
                       brand_css=brand_css, document_css=document_css,
                       pagedjs_js=pagedjs_js, logo=logo)
```

- [ ] **Step 4: Run the new tests AND the canvas regression suite**

Run: `uv run pytest scripts/tests/test_doc_html_render.py scripts/tests/test_slidegen_html.py scripts/tests/test_theme_select.py -v`
Expected: all PASS. The canvas HTML/theme tests prove the `_theme_css` refactor did not change canvas output.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/visgen/html_render.py scripts/tests/test_doc_html_render.py
git commit -m "feat(m2): html_render doc assembly (render_doc_html) + shared _fonts_and_tokens refactor"
```

---

### Task 5: `document.py` renderer (Paged.js/Chromium) + `render_doc.py` CLI

**Files:**
- Modify: `scripts/lib/visgen/document.py` (add `render_doc` + the page-introspection JS constants; lazy Playwright import)
- Create: `scripts/ops/render_doc.py` (thin CLI)
- Create: `scripts/tests/fixtures/docs/tiny.md` (render fixture)
- Test: `scripts/tests/test_doc_render.py`

**Interfaces:**
- Consumes: `visgen.document.{parse_frontmatter, markdown_to_html}`, `visgen.schema.validate_frontmatter`, `visgen.html_render.render_doc_html`, Playwright chromium.
- Produces (consumed by Tasks 6, 8, 9, 10):
  - `visgen.document.render_doc(md_path, out_dir, skill_dir=None) -> dict` — writes `index.html`, `png/page-NN.png` (one per rendered page), `pdf/<out_dir.name>.pdf` (A4, selectable text), `render_report.json`; returns the report dict:
    ```python
    {"template": str, "title": str, "page_count": int,
     "pages":   [{"index": int, "overflow": bool, "width": int, "height": int}],
     "headings":[{"id": str|None, "text": str, "level": int, "page": int|None}],
     "toc":     [{"href": str, "targetPage": int|None, "shownPage": int|None}],
     "chrome":  [{"page": int, "hasHeader": bool, "hasFooterNum": bool}],
     "orphan_headings": [{"text": str, "page": int}]}
    ```
  - CLI: `uv run python scripts/ops/render_doc.py DOC.md [--out DIR]` (default out: `output/<doc-stem>/`).
- Page size is A4 via CSS `@page` (not the pixel FORMATS registry); PNG px comes from the `.pagedjs_page` box.

- [ ] **Step 1: Create the render fixture `scripts/tests/fixtures/docs/tiny.md`**

```markdown
---
template: report
title: Tiny Test Report
subtitle: Rendering smoke test
lang: en
date: 2026-07-08
audience: internal
---

# Overview

Some introductory text with enough words to fill a little vertical space on the
first content page so pagination has something real to lay out.

## Details

| Metric | Value |
|--------|-------|
| Alpha  | 10    |
| Beta   | 20    |

!!! warning "Careful"
    A functional callout in the body.

# Second Section

More text to force a second top-level heading and exercise the table of contents
with two entries.
```

- [ ] **Step 2: Write the failing test**

`scripts/tests/test_doc_render.py`:
```python
from pathlib import Path

from visgen.document import render_doc

FIX = Path(__file__).resolve().parent / "fixtures/docs/tiny.md"


def test_render_doc_produces_html_pdf_pngs(tmp_path):
    out = tmp_path / "tiny"
    report = render_doc(FIX, out)
    assert report["page_count"] >= 2
    assert (out / "index.html").is_file()
    pngs = sorted((out / "png").glob("page-*.png"))
    assert len(pngs) == report["page_count"]
    assert list((out / "pdf").glob("*.pdf"))


def test_render_doc_report_facts(tmp_path):
    report = render_doc(FIX, tmp_path / "tiny")
    assert report["template"] == "report"
    # no page overflows for this small doc
    assert all(p["overflow"] is False for p in report["pages"])
    # headings mapped to real pages
    texts = {h["text"] for h in report["headings"]}
    assert {"Overview", "Second Section"} <= texts
    assert all(isinstance(h["page"], int) for h in report["headings"])
    # TOC entries resolve to real target pages
    assert report["toc"]
    assert all(isinstance(e["targetPage"], int) and e["targetPage"] >= 1
               for e in report["toc"])
    # content pages (page >= 2) carry running header + footer page number
    body_pages = [c for c in report["chrome"] if c["page"] >= 2]
    assert body_pages and all(c["hasHeader"] and c["hasFooterNum"] for c in body_pages)
    # no orphaned headings
    assert report["orphan_headings"] == []
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_doc_render.py -v`
Expected: FAIL (`render_doc` not defined).

- [ ] **Step 4: Add `render_doc` + JS introspection to `scripts/lib/visgen/document.py`**

Append these module-level JS constants and the `render_doc` function to `scripts/lib/visgen/document.py` (keep the existing imports; add `json` and `Path`):
```python
import json
from pathlib import Path

from visgen.schema import validate_frontmatter
from visgen.html_render import render_doc_html

# --- browser-side introspection (run after Paged.js finishes) -----------------
_HEADINGS_JS = """() => Array.from(
  document.querySelectorAll('main h1, main h2, main h3, main h4')
).map(h => {
  const pg = h.closest('.pagedjs_page');
  return { id: h.id || null, text: h.textContent.trim(), level: Number(h.tagName[1]),
           page: pg ? Number(pg.getAttribute('data-page-number')) : null };
})"""

_TOC_JS = """() => Array.from(document.querySelectorAll('.toc a')).map(a => {
  const href = a.getAttribute('href') || '';
  const id = href.replace(/^#/, '');
  const target = id ? document.getElementById(id) : null;
  const pg = target ? target.closest('.pagedjs_page') : null;
  const targetPage = pg ? Number(pg.getAttribute('data-page-number')) : null;
  const after = getComputedStyle(a, '::after').content || '';
  const m = after.match(/\\d+/);
  return { href, targetPage, shownPage: m ? Number(m[0]) : null };
})"""

_CHROME_JS = """() => Array.from(document.querySelectorAll('.pagedjs_page')).map(pg => {
  const n = Number(pg.getAttribute('data-page-number'));
  const footer = pg.querySelector('.pagedjs_margin-bottom-right, .pagedjs_margin-bottom-center');
  const header = pg.querySelector('.pagedjs_margin-top-left, .pagedjs_margin-top-right, .pagedjs_margin-top-center');
  return { page: n,
           hasHeader: !!(header && header.textContent.trim()) || !!(header && header.querySelector('svg,img')),
           hasFooterNum: !!(footer && /\\d/.test(footer.textContent || '')) };
})"""

_ORPHAN_JS = """() => {
  const bad = [];
  document.querySelectorAll('main h1, main h2, main h3, main h4').forEach(h => {
    const pg = h.closest('.pagedjs_page'); if (!pg) return;
    const content = pg.querySelector('.pagedjs_page_content') || pg;
    const blocks = Array.from(
      content.querySelectorAll('h1,h2,h3,h4,p,ul,ol,table,figure,blockquote,.admonition')
    ).filter(e => e.closest('.pagedjs_page') === pg);
    if (blocks.length && blocks[blocks.length - 1] === h)
      bad.push({ text: h.textContent.trim(),
                 page: Number(pg.getAttribute('data-page-number')) });
  });
  return bad;
}"""


def render_doc(md_path, out_dir, skill_dir=None) -> dict:
    text = Path(md_path).read_text(encoding="utf-8")
    meta, body_md = parse_frontmatter(text)
    validate_frontmatter(meta)
    body_html, toc_html = markdown_to_html(body_md)
    html = render_doc_html(meta, body_html, toc_html, skill_dir=skill_dir)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright  # lazy: keeps this module import-safe

    report = {"template": meta["template"], "title": meta["title"], "pages": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto((out_dir / "index.html").resolve().as_uri())
        # Paged.js runs on load; PagedConfig.after sets the flag (see base template).
        page.wait_for_function("window.__PAGED_DONE === true", timeout=60000)

        (out_dir / "png").mkdir(exist_ok=True)
        page_boxes = page.query_selector_all(".pagedjs_page")
        for i, pg in enumerate(page_boxes, start=1):
            box = pg.bounding_box()
            overflow = pg.evaluate(
                "el => { const c = el.querySelector('.pagedjs_page_content'); "
                "return c ? (c.scrollHeight > c.clientHeight + 1) : false; }")
            report["pages"].append({"index": i, "overflow": bool(overflow),
                                    "width": round(box["width"]), "height": round(box["height"])})
            pg.screenshot(path=str(out_dir / "png" / f"page-{i:02d}.png"))

        report["headings"] = page.evaluate(_HEADINGS_JS)
        report["toc"] = page.evaluate(_TOC_JS)
        report["chrome"] = page.evaluate(_CHROME_JS)
        report["orphan_headings"] = page.evaluate(_ORPHAN_JS)

        (out_dir / "pdf").mkdir(exist_ok=True)
        # Paged.js already produced print-ready A4 page boxes; print WITHOUT
        # emulating print media (mirrors pagedjs-cli). prefer_css_page_size honors
        # @page { size: A4 }; print_background keeps cover/table fills.
        page.pdf(path=str(out_dir / "pdf" / f"{out_dir.name}.pdf"),
                 prefer_css_page_size=True, print_background=True)
        browser.close()

    report["page_count"] = len(report["pages"])
    (out_dir / "render_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
```

Troubleshooting notes for the implementer:
- If `wait_for_function` times out, Paged.js did not finish. Confirm the base template defines `window.PagedConfig` BEFORE the polyfill `<script>` runs (it is in `<head>`), and that the polyfill text was inlined (Task 4).
- If the PDF double-paginates (blank pages between content), do NOT call `page.emulate_media("print")`; if it still misbehaves, try `page.emulate_media(media="screen")` before `page.pdf(...)`.
- If `shownPage` is `null` for every TOC entry (Paged.js `target-counter` not surfaced via computed style in this version), that is tolerated by `doc_lint` (Task 6) as long as `targetPage` resolves; the mismatch check only fires when `shownPage` is a number.

- [ ] **Step 5: Create the CLI `scripts/ops/render_doc.py`**

```python
#!/usr/bin/env python3
"""Render a Markdown+front-matter document to an A4 PDF + per-page PNGs via Paged.js/Chromium.

Usage:
    uv run python scripts/ops/render_doc.py DOC.md [--out DIR]

Writes into DIR (default: output/<doc-stem>/):
    index.html, png/page-NN.png, pdf/<dirname>.pdf, render_report.json
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.document import render_doc  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Render a Markdown document to A4 PDF + PNGs.")
    ap.add_argument("doc", help="Path to the Markdown document (with YAML front-matter).")
    ap.add_argument("--out", help="Output directory (default: output/<stem>/).")
    args = ap.parse_args()

    doc_path = Path(args.doc)
    out = Path(args.out) if args.out else Path("output") / doc_path.stem
    report = render_doc(doc_path, out)
    print(f"Rendered {report['page_count']} page(s) to {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest scripts/tests/test_doc_render.py -v`
Expected: both PASS. This exercises Paged.js end-to-end (cover + TOC + 2 body sections over >= 2 pages).

- [ ] **Step 7: Smoke the CLI**

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_doc.py scripts/tests/fixtures/docs/tiny.md --out output/tiny-smoke
```
Expected: prints `Rendered N page(s) to output/tiny-smoke`; `output/tiny-smoke/pdf/tiny-smoke.pdf` and `png/page-01.png` exist. Open `page-01.png` (the cover) and one body page (Read tool): navy/green brand, Be Vietnam Pro, logo in the running header, page number in the footer.

- [ ] **Step 8: Commit**

```bash
git add scripts/lib/visgen/document.py scripts/ops/render_doc.py scripts/tests/test_doc_render.py scripts/tests/fixtures/docs/tiny.md
git commit -m "feat(m2): document renderer (Paged.js/Chromium) -> A4 PDF + page PNGs + render report; render_doc CLI"
```

---

### Task 6: `doc_lint.py` (pagination integrity + PDF sanity) + `grade_doc.py` CLI

**Files:**
- Create: `scripts/lib/visgen/doc_lint.py`
- Create: `scripts/ops/grade_doc.py`
- Test: `scripts/tests/test_doc_lint.py`

**Interfaces:**
- Consumes: `visgen.brand_lint.lint_html` (brand surface reuse), `pypdf.PdfReader`, the render report dict from Task 5.
- Produces (consumed by Tasks 8, 9, 10):
  - `visgen.doc_lint.lint_pagination(report: dict) -> list[dict]` — violations: `page-overflow`, `orphan-heading`, `toc-dangling`, `toc-page-mismatch`, `missing-header`, `missing-footer-page-number` (cover page 1 exempt).
  - `visgen.doc_lint.lint_pdf(pdf_path, expected_pages=None) -> list[dict]` — violations: `pdf-page-count`, `pdf-no-text`, `pdf-fonts-not-embedded`.
  - `visgen.doc_lint.lint_doc(html, report, pdf_path, expected_pages=None) -> {"passed": bool, "violations": [...]}` — brand surface (`lint_html`) + pagination + PDF sanity.
  - CLI: `uv run python scripts/ops/grade_doc.py OUTDIR`, exit 0 iff passed.

- [ ] **Step 1: Write the failing tests**

`scripts/tests/test_doc_lint.py`:
```python
from visgen.doc_lint import lint_pagination


def test_pagination_flags_all_defect_classes():
    report = {
        "pages": [{"index": 1, "overflow": False}, {"index": 2, "overflow": True}],
        "orphan_headings": [{"text": "Lonely", "page": 3}],
        "toc": [{"href": "#a", "targetPage": 2, "shownPage": 9},
                {"href": "#b", "targetPage": None, "shownPage": None}],
        "chrome": [{"page": 1, "hasHeader": False, "hasFooterNum": False},
                   {"page": 2, "hasHeader": True, "hasFooterNum": True},
                   {"page": 3, "hasHeader": False, "hasFooterNum": True}],
    }
    codes = {v["code"] for v in lint_pagination(report)}
    assert "page-overflow" in codes
    assert "orphan-heading" in codes
    assert "toc-page-mismatch" in codes     # #a shows 9 but target on 2
    assert "toc-dangling" in codes          # #b has no target page
    assert "missing-header" in codes        # page 3 lacks a running header
    # cover (page 1) is exempt from the header/footer requirement:
    assert not any("page 1" in v.get("detail", "") for v in lint_pagination(report))


def test_pagination_clean_report_passes():
    report = {
        "pages": [{"index": 1, "overflow": False}, {"index": 2, "overflow": False}],
        "orphan_headings": [],
        "toc": [{"href": "#a", "targetPage": 2, "shownPage": 2}],
        "chrome": [{"page": 1, "hasHeader": False, "hasFooterNum": False},
                   {"page": 2, "hasHeader": True, "hasFooterNum": True}],
    }
    assert lint_pagination(report) == []


def test_toc_mismatch_only_when_shown_is_a_number():
    """If Paged.js does not surface the shown number, targetPage alone must not trip
    the mismatch check."""
    report = {"pages": [{"index": 1, "overflow": False}], "orphan_headings": [],
              "chrome": [], "toc": [{"href": "#a", "targetPage": 4, "shownPage": None}]}
    assert lint_pagination(report) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest scripts/tests/test_doc_lint.py -v`
Expected: FAIL (`visgen.doc_lint` not defined).

- [ ] **Step 3: Create `scripts/lib/visgen/doc_lint.py`**

```python
"""Deterministic document checks: pagination integrity + PDF sanity. Reuses the
brand surface check (visgen.brand_lint.lint_html) and adds only the document-only
guarantees the spec names. Grades the produced artifact (render report + PDF)."""
from pypdf import PdfReader

from visgen.brand_lint import lint_html

_EMBED_KEYS = ("/FontFile", "/FontFile2", "/FontFile3")


def lint_pagination(report: dict) -> list:
    v = []
    for pg in report.get("pages", []):
        if pg.get("overflow"):
            v.append({"code": "page-overflow", "detail": f'page {pg.get("index")}'})
    for h in report.get("orphan_headings", []):
        v.append({"code": "orphan-heading",
                  "detail": f'{h.get("text")!r} alone at foot of page {h.get("page")}'})
    for e in report.get("toc", []):
        tp = e.get("targetPage")
        if not isinstance(tp, int) or tp < 1:
            v.append({"code": "toc-dangling", "detail": e.get("href")})
            continue
        sp = e.get("shownPage")
        if isinstance(sp, int) and sp != tp:
            v.append({"code": "toc-page-mismatch",
                      "detail": f'{e.get("href")}: shows {sp}, target on page {tp}'})
    for c in report.get("chrome", []):
        if c.get("page", 1) <= 1:      # cover is page 1: no running chrome by design
            continue
        if not c.get("hasHeader"):
            v.append({"code": "missing-header", "detail": f'page {c.get("page")}'})
        if not c.get("hasFooterNum"):
            v.append({"code": "missing-footer-page-number", "detail": f'page {c.get("page")}'})
    return v


def _font_embedded(font) -> bool:
    descs = []
    if "/FontDescriptor" in font:
        descs.append(font["/FontDescriptor"].get_object())
    for df in (font.get("/DescendantFonts") or []):
        d = df.get_object()
        if "/FontDescriptor" in d:
            descs.append(d["/FontDescriptor"].get_object())
    if not descs:
        return False
    return all(any(k in d for k in _EMBED_KEYS) for d in descs)


def _all_fonts_embedded(reader) -> bool:
    for page in reader.pages:
        res = page.get("/Resources")
        fonts = res.get("/Font") if res else None
        if not fonts:
            continue
        for ref in fonts.values():
            if not _font_embedded(ref.get_object()):
                return False
    return True


def lint_pdf(pdf_path, expected_pages=None) -> list:
    """The 'converts to PDF cleanly' guarantee: page count, selectable text, embedded fonts."""
    v = []
    reader = PdfReader(str(pdf_path))
    n = len(reader.pages)
    if expected_pages is not None and n != expected_pages:
        v.append({"code": "pdf-page-count", "detail": f"{n} != {expected_pages}"})
    text = "".join((pg.extract_text() or "") for pg in reader.pages)
    if not text.strip():
        v.append({"code": "pdf-no-text", "detail": "no selectable text extracted"})
    if not _all_fonts_embedded(reader):
        v.append({"code": "pdf-fonts-not-embedded", "detail": "a font lacks an embedded FontFile"})
    return v


def lint_doc(html, report, pdf_path, expected_pages=None) -> dict:
    v = lint_html(html)
    v += lint_pagination(report)
    v += lint_pdf(pdf_path, expected_pages=expected_pages or report.get("page_count"))
    return {"passed": not v, "violations": v}
```

- [ ] **Step 4: Create the CLI `scripts/ops/grade_doc.py`**

```python
#!/usr/bin/env python3
"""Grade a rendered document output directory. Local-only; deterministic.

Runs the brand surface check (visgen.brand_lint on index.html), pagination
integrity (TOC page numbers match, no overflow, no orphaned headings, running
headers/footers present), and PDF sanity (page count, fonts embedded, text
selectable) via visgen.doc_lint.

Usage: uv run python scripts/ops/grade_doc.py OUTDIR
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from visgen.doc_lint import lint_doc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    args = ap.parse_args()
    out = Path(args.outdir)
    html = (out / "index.html").read_text(encoding="utf-8")
    report = json.loads((out / "render_report.json").read_text(encoding="utf-8"))
    pdfs = sorted((out / "pdf").glob("*.pdf"))
    if not pdfs:
        print(json.dumps({"passed": False, "violations": [{"code": "no-pdf", "detail": str(out)}]}))
        sys.exit(1)
    res = lint_doc(html, report, pdfs[0])
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests + grade the Task 5 smoke output end-to-end**

Run: `uv run pytest scripts/tests/test_doc_lint.py -v`
Expected: 3 PASS.

Then exercise `lint_pdf` on a real render (proves the PDF path, which the unit tests do not cover):
```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_doc.py scripts/tests/fixtures/docs/tiny.md --out output/tiny-smoke
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_doc.py output/tiny-smoke
```
Expected: `"passed": true`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/visgen/doc_lint.py scripts/ops/grade_doc.py scripts/tests/test_doc_lint.py
git commit -m "feat(m2): doc_lint (pagination integrity + PDF sanity) + grade_doc CLI, reusing brand_lint"
```

---

### Task 7: `generate-doc` SKILL.md (thin skill)

**Files:**
- Create: `.claude/skills/generate-doc/SKILL.md`
- Test: `scripts/tests/test_doc_skill.py`

**Interfaces:**
- Consumes: everything above (front-matter contract, `render_doc.py`, `grade_doc.py`, templates, exemplars).
- Produces: the operator-facing workflow. No new engine code.

- [ ] **Step 1: Write the failing test**

`scripts/tests/test_doc_skill.py`:
```python
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / ".claude/skills/generate-doc/SKILL.md"


def test_skill_present_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^name:\s*generate-doc\s*$", text, re.M)
    assert "description:" in text


def test_skill_documents_contract_and_commands():
    text = SKILL.read_text(encoding="utf-8")
    for token in ("template", "report", "handbook", "front-matter",
                  "scripts/ops/render_doc.py", "scripts/ops/grade_doc.py",
                  "admonition", "brand/tokens.json"):
        assert token in text, f"SKILL.md should mention {token!r}"


def test_skill_has_no_forbidden_dashes():
    text = SKILL.read_text(encoding="utf-8")
    assert "—" not in text and "–" not in text  # no em/en dash
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest scripts/tests/test_doc_skill.py -v`
Expected: FAIL (SKILL.md missing).

- [ ] **Step 3: Create `.claude/skills/generate-doc/SKILL.md`**

Write this file verbatim (uses only ASCII hyphens; no em/en dashes):

````markdown
---
name: generate-doc
description: Build brand-locked VISEMI / Cất Cánh reports and handbooks from Markdown with YAML front-matter, paginate them with Paged.js in headless Chromium, and print an A4 PDF with selectable text plus per-page PNGs, then grade them (deterministic doc-lint + brand-lint, optional LLM-judge rubric). Use whenever the operator wants a report, cohort or program report, donor/partner/founder update, impact report, handbook, fellow or mentor handbook, guide, or any "write this up as a proper PDF / make a report / make a handbook" task, even if they do not say "Markdown" or "PDF". Content is Markdown (facts from the brief, never invented); layout is one of two template families (report or handbook); brand lives in brand/tokens.json. A4, light theme, local only.
---

# generate-doc

Produces VISEMI / Cất Cánh reports and handbooks in the house brand: navy `#001669`, green `#01B68B` accent, gold `#F5B433` (sparing), Be Vietnam Pro, on A4 pages with a branded cover, an auto table of contents with real page numbers, and running headers/footers. It separates three concerns: **content** (a Markdown file with YAML front-matter), **layout** (the report or handbook template family), **brand** (the tokens in `brand/tokens.json`), so output is repeatable, gradeable, and on-brand. It is the document counterpart to `generate-slides`: same engine, same brand, a second renderer.

> **Workspace note.** Templates and `document.css` are vendored under this skill
> (`.claude/skills/generate-doc/`). Brand assets (fonts, logos, icons, tokens) are
> the single source of truth in `brand/` (`brand/tokens.json` generates both the
> theme CSS and the brand-lint palette). Render/grade machinery lives in
> `scripts/ops/` and `scripts/lib/visgen/` (`document.py`, `doc_lint.py`). The
> reference exemplars in `scripts/evals/references/*.md` are the canonical
> examples; open their rendered output as visual references.

## Three rules that define this skill

1. **Facts from the brief; never invent.** Every number, date, name, and dollar
   amount must come from the operator's brief or a cited source file. If a fact is
   missing, ask; do not guess or carry a stale figure. Documents go out under
   VISEMI's name, so a wrong figure is expensive. Never put real fellow or
   applicant personal data (names, contact details, individual profiles) in a
   committed exemplar; use program-level or aggregate facts.

2. **Brand is locked.** Only the VISEMI palette and Be Vietnam Pro. The functional
   status colors (`--warn` amber, `--bad` red, `--good` green) are for callouts and
   status only, never decorative fills. No off-brand colors, no other fonts, no em
   dashes, no en dashes, no emojis. Vietnamese keeps full diacritics ("Cất Cánh",
   never "Cat Canh"). The deterministic brand-lint enforces this.

3. **Verify by rendering.** A document is not done until the PDF and page PNGs
   render with no overflow, `doc_lint` and brand-lint pass, and you have eyeballed
   the PNGs (cover, TOC, a body spread) against the intent.

## Workflow

### Step 1 - Author / confirm the Markdown

Write a `.md` file with a YAML front-matter block, then the body in Markdown. Shape:

```markdown
---
template: report        # report | handbook
title: Cất Cánh Cohort 1 Program Report
subtitle: Plan and progress to date
lang: en                # en | vi
date: July 2026
audience: Partners and founders
eyebrow: Cất Cánh (Takeoff) Fellowship
orgline: VISEMI Foundation | visemi.org
# handbook-only cover extra: edition: Cohort 1
---

# Executive Summary

Body text. Use **bold** for emphasis; keep green to roughly 10-20% of a page.
```

- `template`: `report` (sections flow continuously; doc title in the running
  header) or `handbook` (each top-level `#` heading opens a new chapter page; the
  chapter name runs in the header). Validated on render.
- `lang`: `en` (default) or `vi`. Full Vietnamese diacritics always.
- Cover fields (`subtitle`, `date`, `audience`, `eyebrow`, `orgline`, and for
  handbooks `edition`) are optional; present ones render on the branded cover.
- Body Markdown supports (via `python-markdown` `extra` + `toc` + `admonition`):
  headings, paragraphs, **bold**/`links`, bullet and numbered lists, tables,
  footnotes, blockquotes, fenced code, and callouts (see below). Do not hardcode a
  color or inline style; styling comes from the tokens.

### Step 2 - Render

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_doc.py CONTENT.md --out output/<name>
```

Writes `output/<name>/{index.html, png/page-NN.png, pdf/<name>.pdf, render_report.json}`.
The renderer converts Markdown to HTML, pours it into the `template` family, runs
Paged.js in Chromium to paginate to A4, screenshots each page, and prints the PDF
with selectable text and embedded fonts. Check `render_report.json`: every page
`overflow: false`, `toc` entries resolve to real target pages, `orphan_headings`
empty. `output/` is git-ignored; never commit rendered output.

### Step 3 - Grade

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_doc.py output/<name>                     # deterministic
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_rubric.py output/<name> --task TASK.json  # LLM judge (needs ANTHROPIC_API_KEY)
```

`grade_doc` must pass (`"passed": true`): brand surface (palette, fonts, dashes,
diacritics) + pagination integrity (TOC page numbers match actual heading pages,
no overflow, no orphaned headings, running headers/footers present) + PDF sanity
(page count, fonts embedded, text selectable). The rubric grader scores
**brand / layout / content / polish** plus the document dimensions
**coherent pagination** and **TOC usefulness** 0-5 with justifications; read them,
do not trust the score blindly. For the full suite over the seed tasks plus every
reference exemplar: `uv run python scripts/evals/run_evals.py` (reports pass@k).

## Template families

Both families share one pipeline and one `document.css`; a body class
(`.report` / `.handbook`) selects the differences.

| Feature | `report` | `handbook` |
| --- | --- | --- |
| Cover | Data-forward: eyebrow, title, subtitle, date, audience | Warmer feature gradient: "Handbook" label, edition, title |
| Section headings (`#`) | Flow continuously down the page | Each opens a new chapter page (styled opener, green top rule) |
| Running header | Document title | Current chapter name |
| Best for | Cohort/program reports, donor and partner updates, impact summaries | Fellow/mentor handbooks, program guides, long-form onboarding |

Common to both: branded cover, auto TOC with real page numbers, running footer
with page number and org line, token-driven heading/table/callout/figure/blockquote
styles, and page-break rules (no orphaned headings, keep-with-next, figure captions
stay with figures, table headers repeat when a table splits).

## Callouts, tables, figures, quotes

- **Callout** (functional status color): admonition syntax.
  ```markdown
  !!! warning "Deadline"
      Applications close 17 July 2026.
  ```
  Types map to tokens: `note`/`info` (navy), `tip`/`success` (green), `warning`
  (amber), `danger`/`important` (red). Use functionally, not as decoration.
- **Table**: standard Markdown pipe tables. Header row is navy; long tables split
  across pages with the header repeated.
- **Figure with caption**: write explicit HTML (allowed via `md_in_html`):
  ```html
  <figure>
    <img src="path/to/image.png" alt="Description">
    <figcaption>Caption text, from the brief.</figcaption>
  </figure>
  ```
  Local image paths only (no sourcing/generation). Captions stay with the figure.
- **Blockquote**: `> Quoted text.` renders as a green-ruled pull quote. For a person
  quote, confirm consent and attribute in plain language; never expose private data.

## Page-break behavior

Headings use `break-after: avoid` (never orphaned at a page foot) and
`break-inside: avoid`. Figures, blockquotes, callouts, and table rows avoid
breaking mid-block. Handbook chapter headings force a page break before. If content
overflows a page box, fix the content (trim or split a section), never off-brand
sizing tricks; `doc_lint` fails on any overflow.

## Graders & exemplars

- **doc-lint** (`scripts/ops/grade_doc.py`, logic in
  `scripts/lib/visgen/doc_lint.py`): deterministic. Brand surface reuses
  `visgen.brand_lint`; adds pagination integrity and PDF sanity.
- **Rubric grader** (`scripts/ops/grade_rubric.py`, rubrics in
  `scripts/evals/rubrics/`): isolated LLM judge per dimension over the rendered
  PNGs; documents add `doc-pagination` and `toc-usefulness`. Model `claude-opus-4-8`;
  needs `ANTHROPIC_API_KEY`.
- **Exemplars** in `scripts/evals/references/`: `cat-canh-cohort-report.md` (a
  report) and `cat-canh-fellow-handbook.md` (a handbook). `run_evals.py` synthesizes
  a regression task per exemplar so both are rendered + doc-linted on every run.

## Ecosystem follow-on (documents beyond the exemplars)

For report/handbook patterns the two families do not cover, reuse the vendored
references rather than inventing from scratch (apply the VISEMI tokens; never adopt
a reference's own palette):

- **Report / doc structure and components:** `references/doc-visualization-tools/`
  (`PowerDocu`, `visual-explainer`) for document-generation patterns, and the
  admin/report component CSS in `references/ui-component-libs/tabler` and
  `references/ui-component-libs/gentelella` (tables, stat cards, callouts) as
  structural inspiration.
- **Layout / typographic inspiration:** `references/design-inspiration/`
  (`open-design`, `web-design`) and `references/claude-design-galleries/`
  (`awesome-claude-design-rohitg00`, `awesome-claude-design-voltagent`).

## Anti-patterns

- Inventing or reusing a number/date/name not in the brief; putting real fellow PII
  in a committed exemplar.
- Any off-brand color or non-Be-Vietnam-Pro font; em dashes, en dashes, emojis;
  stripped Vietnamese diacritics.
- Hardcoding a hex or inline style in the Markdown or in `document.css`; styling
  lives in the tokens.
- Using a status color (amber/red/green) as a decorative fill instead of a
  functional callout/status accent.
- Declaring a document done without rendering it and checking `render_report.json`
  (overflow false, TOC resolved, no orphaned headings) and eyeballing the PNGs.
- Committing anything under `output/`.
````

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest scripts/tests/test_doc_skill.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/generate-doc/SKILL.md scripts/tests/test_doc_skill.py
git commit -m "feat(m2): generate-doc SKILL.md (thin skill: front-matter contract, families, graders, references)"
```

---

### Task 8: Report exemplar - Cất Cánh Cohort 1 Program Report

**Files:**
- Create: `scripts/evals/references/cat-canh-cohort-report.md`
- Test: `scripts/tests/test_reference_exemplars_clean.py` (permanent TK/PII guard, shared with Task 9)

**Interfaces:**
- Consumes: the `report` template family, `render_doc`, `grade_doc`.
- Produces: a regression fixture wired into `run_evals.py` in Task 10.

**Fact sourcing (binding):** Reuse the vetted Cất Cánh facts already in
`scripts/evals/references/pitch-deck.content.json` (founders, tagline, 3 pillars,
6-month accelerator 06/26-12/26, tiered funding, Year-1 targets, 5-year goal, ROI,
501(c)(3), contacts). Pull any additional real facts from cat-canh
`data/reports/FINANCIAL_SUPPORT_TIERS_REPORT.pdf` and
`programs/kickoff-meeting/` (read-only). **Frame Cohort 1 as plan + progress; do
not fabricate outcomes.** Every `[TK: ...]` marker must be resolved from a cited
source or by asking the operator before commit. **No real fellow/applicant PII** -
program-level and aggregate facts only.

- [ ] **Step 1: Write the permanent guard test (shared with Task 9)**

`scripts/tests/test_reference_exemplars_clean.py`:
```python
import re
from pathlib import Path

REFS = Path(__file__).resolve().parents[2] / "scripts/evals/references"


def _doc_exemplars():
    return sorted(REFS.glob("*.md"))


def test_at_least_two_doc_exemplars_present():
    assert len(_doc_exemplars()) >= 2  # cohort report + fellow handbook


def test_no_unresolved_tk_markers():
    """Gated-placeholder rule: a committed exemplar must carry no [TK: ...] markers."""
    offenders = {}
    for md in _doc_exemplars():
        hits = re.findall(r"\bTK:[^\]\n]*", md.read_text(encoding="utf-8"))
        if hits:
            offenders[md.name] = hits
    assert not offenders, f"unresolved TK markers: {offenders}"


def test_no_forbidden_dashes_in_exemplars():
    for md in _doc_exemplars():
        text = md.read_text(encoding="utf-8")
        assert "—" not in text, f"em dash in {md.name}"
        assert "–" not in text, f"en dash in {md.name}"


def test_diacritics_preserved():
    """The program name must keep its diacritics; 'Cat Canh' (stripped) is a defect."""
    for md in _doc_exemplars():
        text = md.read_text(encoding="utf-8")
        assert "Cat Canh" not in text
```

Run: `uv run pytest scripts/tests/test_reference_exemplars_clean.py -v`
Expected: FAIL on `test_at_least_two_doc_exemplars_present` (no `.md` exemplars yet).

- [ ] **Step 2: Author `scripts/evals/references/cat-canh-cohort-report.md`**

Start from this content (real facts inline; resolve every `[TK: ...]` from the
cited source or by asking the operator, then delete the marker). Use ASCII hyphens
only; keep Vietnamese diacritics.

```markdown
---
template: report
title: Cất Cánh (Takeoff) Fellowship - Cohort 1 Program Report
subtitle: Plan and progress to date
lang: en
date: July 2026
audience: Partners and founders
eyebrow: Cất Cánh (Takeoff) Fellowship
orgline: VISEMI Foundation | visemi.org | catcanh@visemi.org
---

# Executive Summary

The Cất Cánh (Takeoff) Fellowship, "Bệ phóng cho trí tuệ Việt" (the launch pad
for Viet talent), is a structured 6-month accelerator that helps top Vietnamese
STEM students win fully funded graduate programs overseas. Founded by
Dr. Loi Nguyen (Executive VP Emeritus, Marvell) and the VISEMI Foundation, Cohort 1
runs from June to December 2026. This report summarizes the program design, the
financial support model, and Cohort 1 progress to date.

!!! note "At a glance"
    Year 1 targets: **15 fellows funded**, an **80%+ admission success rate**, and a
    **$150,000** fundraising goal for grants and operations.

# Program Overview

Cất Cánh addresses a clear gap: talented Vietnamese STEM students face financial,
language, and strategic barriers that limit access to fully funded MS and PhD
programs in the USA, Taiwan, Korea, Japan, and the EU. The program delivers three
pillars.

| Pillar | Focus |
|--------|-------|
| 1. Intensive Preparation | Structured English training and strategic application coaching |
| 2. Milestone Funding | Up to $15,000 per student across English, testing, conference, application, and basic needs |
| 3. Global Mentorship | Local ambassadors and worldwide experts for coaching and long-term placement |

Every fellow commits to mentoring the next cohort, building an alumni flywheel that
compounds the program's reach year over year.

# The 6-Month Accelerator

Cohort 1 runs June to December 2026. The journey moves from preparation through
application to placement.

| Phase | Window | Focus |
|-------|--------|-------|
| Preparation | [TK: months, e.g. Jun-Aug 2026 - confirm from programs/kickoff-meeting/planning] | English and profile building |
| Application | [TK: months - confirm] | Program selection, essays, submissions |
| Placement | [TK: months - confirm] | Interviews, offers, funding confirmation |

# Financial Support Model

Support is tiered to match each fellow's need and readiness. (Figures from the
Cất Cánh financial support tiers model.)

| Tier | Grant | Who it serves |
|------|-------|---------------|
| Tier 1: Full Support Grant | $8,000 - $15,000 | Excellent academic record with documented financial hardship |
| Tier 2: Application Grant | $4,000 - $5,000 | Targeted funding for English and application gaps |
| Tier 3 and 4: Mentorship Grant | ~$1,000 | Strategic network access and early research exposure |

# Cohort 1 at a Glance

Cohort 1 targets 15 funded fellows with an 80%+ admission success rate against a
$150,000 fundraising goal.

!!! success "Progress to date"
    [TK: Cohort 1 progress as of July 2026 - applications received, fellows
    selected, funds raised. Aggregate numbers only, no individual names. Confirm
    with operator; if not yet available, state "selection in progress" in plain
    language.]

# Impact and ROI

A Cất Cánh prep grant of roughly $10,000 resolves the roadblocks that otherwise
keep a qualified student out of a fully funded program. Set against the value of the
degrees fellows go on to win, the return is outsized.

| Measure | Value |
|---------|-------|
| Average MS program (total degree value) | ~$70,000 |
| Average PhD program (total degree value) | ~$200,000 |
| Program ROI | 7x to 20x |

Total degree value is paid by the destination host university or secured
scholarship programs, not by Cất Cánh.

# Looking Ahead

Over five years, Cất Cánh aims to fund 150 fellows and build a global Vietnamese
tech talent network on a total budget under $2 million, sustained by the alumni
flywheel in which every fellow mentors the next cohort.

# Partner With Us

The Cất Cánh Fellowship, founded by Dr. Loi Nguyen and the VISEMI Foundation, is
administered by VISEMI Foundation, a registered 501(c)(3) nonprofit, ensuring
transparent and tax-deductible support.

> To partner with us, contact catcanh@visemi.org or visit visemi.org.
```

- [ ] **Step 3: Resolve every TK marker**

Read `programs/kickoff-meeting/planning/` and `data/reports/` in `$CC` for the
phase windows and any aggregate Cohort 1 progress figures. Fill each `[TK: ...]`
with a real fact and delete the marker, or ask the operator. If a fact genuinely
does not exist yet, replace the marker with truthful plain language (for example,
"Selection is in progress; figures will be reported at cohort close") - never a
fabricated number.

- [ ] **Step 4: Render + grade + eyeball**

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_doc.py scripts/evals/references/cat-canh-cohort-report.md --out output/cohort-report
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_doc.py output/cohort-report
```
Expected: render report all `overflow: false`, `orphan_headings` empty, `toc`
entries resolve; grade prints `"passed": true`, exit 0. Open the cover, the TOC
page, and 1-2 body pages (Read tool): branded cover, real page numbers in the TOC,
running header with the doc title and logo, navy table headers, the callouts using
functional colors. If a page overflows, trim or split the section; never resize
off-brand.

- [ ] **Step 5: Run the guard test**

Run: `uv run pytest scripts/tests/test_reference_exemplars_clean.py -v`
Expected: `test_no_unresolved_tk_markers` PASS (all TKs resolved). `test_at_least_two_doc_exemplars_present` still fails until Task 9 adds the handbook - that is expected; it goes green in Task 9.

- [ ] **Step 6: Commit**

```bash
git add scripts/evals/references/cat-canh-cohort-report.md scripts/tests/test_reference_exemplars_clean.py
git commit -m "feat(m2): report exemplar - Cất Cánh Cohort 1 program report (facts reused, no PII, no TK)"
```

---

### Task 9: Handbook exemplar - Cất Cánh Fellow Handbook

**Files:**
- Create: `scripts/evals/references/cat-canh-fellow-handbook.md`
- Test: (reuses `scripts/tests/test_reference_exemplars_clean.py` from Task 8; it now covers both exemplars)

**Interfaces:**
- Consumes: the `handbook` template family (chapter-divider pages, running chapter
  name), `render_doc`, `grade_doc`.
- Produces: the second regression fixture wired into `run_evals.py` in Task 10.

**Fact sourcing (binding):** Same rule as Task 8. Evergreen program structure
(mission, pillars, funding, flywheel/mentoring commitment) comes from the vetted
facts; handbook procedural specifics (key dates, contact/office hours, conduct, FAQ)
come from cat-canh `programs/kickoff-meeting/` (`kickoff-script.md`, `resources.md`,
`README.md`) or the operator. No real fellow PII. Resolve every `[TK: ...]` before
commit.

- [ ] **Step 1: Author `scripts/evals/references/cat-canh-fellow-handbook.md`**

Each top-level `#` heading is a chapter (opens a new page in the handbook family).
Use ASCII hyphens only; keep Vietnamese diacritics.

```markdown
---
template: handbook
title: Cất Cánh Fellow Handbook
subtitle: Your guide to the 6-month accelerator
lang: en
edition: Cohort 1 (2026)
date: June 2026
eyebrow: Cất Cánh (Takeoff) Fellowship
orgline: VISEMI Foundation | visemi.org | catcanh@visemi.org
---

# Welcome

Welcome to the Cất Cánh (Takeoff) Fellowship, "Bệ phóng cho trí tuệ Việt", the
launch pad for Viet talent. Over the next six months you will prepare for, apply to,
and step toward a fully funded graduate program overseas, supported by funding,
coaching, and a global mentor network. This handbook explains how the program works
and what we expect of one another.

Cất Cánh was founded by Dr. Loi Nguyen (Executive VP Emeritus, Marvell) and the
VISEMI Foundation, a registered 501(c)(3) nonprofit.

# Program Structure

The fellowship rests on three pillars.

| Pillar | What it gives you |
|--------|-------------------|
| 1. Intensive Preparation | Structured English training and strategic application coaching |
| 2. Milestone Funding | Up to $15,000 across English, testing, conference, application, and basic needs |
| 3. Global Mentorship | Local ambassadors and worldwide experts for coaching and placement |

!!! note "The flywheel"
    Every fellow commits to mentoring the next cohort. The network you join today is
    built by the fellows who came before you, and you will help build it for those
    who come next.

# Funding and Milestones

Financial support is tiered and released against milestones, so funding tracks your
real progress through the program.

| Tier | Grant | Who it serves |
|------|-------|---------------|
| Tier 1: Full Support Grant | $8,000 - $15,000 | Excellent record with documented financial hardship |
| Tier 2: Application Grant | $4,000 - $5,000 | English and application gaps |
| Tier 3 and 4: Mentorship Grant | ~$1,000 | Network access and early research exposure |

!!! warning "Milestone funding"
    Funds are released against milestones, not all at once. [TK: milestone release
    schedule and what each milestone requires - confirm with operator or
    programs/kickoff-meeting/.]

# Expectations and Commitments

As a Cất Cánh fellow you agree to:

- Engage fully with English training, coaching, and mentor sessions.
- Meet program milestones and communicate early if you are at risk of missing one.
- Represent the program and the community with integrity.
- Mentor a fellow in the next cohort as an alumnus.

!!! important "Code of conduct"
    [TK: code of conduct summary - confirm the official wording with the operator.]

# Timeline and Key Dates

Cohort 1 runs June to December 2026.

| Milestone | When |
|-----------|------|
| Program start | June 2026 |
| [TK: key milestone] | [TK: date - confirm from programs/kickoff-meeting/] |
| Program close | December 2026 |

# Resources and Contacts

Your support network includes program staff, local ambassadors, and global mentors.

- Program email: catcanh@visemi.org
- Website: visemi.org
- [TK: mentor office hours / primary contact person and channel - confirm with operator.]

!!! tip "Getting help"
    When in doubt, ask early. Reach your coordinator at catcanh@visemi.org.
```

- [ ] **Step 2: Resolve every TK marker**

Read `$CC/programs/kickoff-meeting/kickoff-script.md`, `resources.md`, and
`README.md` for key dates, contacts, and resources; confirm code-of-conduct and
milestone wording with the operator. Fill each `[TK: ...]` with a real fact and
delete the marker, or ask the operator. Never fabricate a date or a policy.

- [ ] **Step 3: Render + grade + eyeball**

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_doc.py scripts/evals/references/cat-canh-fellow-handbook.md --out output/fellow-handbook
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_doc.py output/fellow-handbook
```
Expected: `overflow: false` everywhere, `orphan_headings` empty, TOC resolves;
grade `"passed": true`, exit 0. Open the cover, TOC, and a chapter opener (Read
tool): warmer handbook cover, "Handbook" label + edition, each chapter starting on
a new page with the green top rule, the running header showing the current chapter
name (not the doc title), page numbers in the footer.

- [ ] **Step 4: Run the guard test (now both exemplars present)**

Run: `uv run pytest scripts/tests/test_reference_exemplars_clean.py -v`
Expected: ALL pass, including `test_at_least_two_doc_exemplars_present` and
`test_no_unresolved_tk_markers`.

- [ ] **Step 5: Commit**

```bash
git add scripts/evals/references/cat-canh-fellow-handbook.md
git commit -m "feat(m2): handbook exemplar - Cất Cánh Fellow Handbook (chapters, no PII, no TK)"
```

---

### Task 10: Wire documents into `run_evals.py` + doc rubrics

**Files:**
- Modify: `scripts/evals/run_evals.py` (renderer branch, doc grading, `.md` reference synthesis, doc judge dims)
- Modify: `scripts/ops/grade_rubric.py` (add `DOC_DIMENSIONS`; parameterize `grade`/`build_prompt_content` without changing slide defaults)
- Create: `scripts/evals/rubrics/doc-pagination.md`, `scripts/evals/rubrics/toc-usefulness.md`
- Test: `scripts/tests/test_doc_evals.py`

**Interfaces:**
- Consumes: `visgen.doc_lint.lint_doc`, `render_doc.py` (subprocess), the two `.md` exemplars.
- Produces: `run_evals.py` renders + grades doc tasks (`"renderer": "doc"`) via `render_doc.py` + `lint_doc`, synthesizes a regression task per `references/*.md`, and (with `--judge`) scores the two extra doc dimensions. `grade_rubric.DOC_DIMENSIONS = ["doc-pagination", "toc-usefulness"]`.

- [ ] **Step 1: Write the failing tests**

`scripts/tests/test_doc_evals.py`:
```python
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_doc_dimensions_and_rubric_files():
    gr = _load("grade_rubric", "scripts/ops/grade_rubric.py")
    assert gr.DOC_DIMENSIONS == ["doc-pagination", "toc-usefulness"]
    for d in gr.DOC_DIMENSIONS:
        assert (ROOT / f"scripts/evals/rubrics/{d}.md").is_file()


def test_doc_prompt_drops_theme_and_names_documents():
    gr = _load("grade_rubric", "scripts/ops/grade_rubric.py")
    doc_blocks = gr.build_prompt_content(["QQ=="], "RUBRIC", "toc-usefulness", "task",
                                         surface="document pages", theme_note=False)
    text = doc_blocks[-1]["text"]
    assert "document pages" in text
    assert "dark theme" not in text
    # slide default is unchanged (M1 behavior preserved):
    slide_blocks = gr.build_prompt_content(["QQ=="], "RUBRIC", "layout", "task")
    assert "generated Cất Cánh slides" in slide_blocks[-1]["text"]
    assert "the dark theme" in slide_blocks[-1]["text"]


def test_run_evals_grades_a_doc_task(tmp_path):
    ev = _load("run_evals", "scripts/evals/run_evals.py")
    task = {"id": "doc-tiny", "renderer": "doc",
            "content": "scripts/tests/fixtures/docs/tiny.md",
            "description": "Regression: tiny report renders + doc-lint.", "trials": 1}
    res = ev.run_task(task, 1, tmp_path)
    assert res["pass_at_k"] == 1.0
    assert res["brand_pass"] == [True]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest scripts/tests/test_doc_evals.py -v`
Expected: FAIL (`DOC_DIMENSIONS` missing; `run_task` has no doc branch).

- [ ] **Step 3: Extend `scripts/ops/grade_rubric.py` (non-breaking)**

Add the doc dimensions constant next to `DIMENSIONS` (line 22):
```python
DIMENSIONS = ["brand", "layout", "content", "polish"]
DOC_DIMENSIONS = ["doc-pagination", "toc-usefulness"]
```

Replace `build_prompt_content` (lines 41-56) with a version whose DEFAULTS reproduce
the current slide prompt byte-for-byte, plus `surface` / `theme_note` params:
```python
def build_prompt_content(image_b64_list, rubric_text, dimension, task_desc,
                         surface="slides", theme_note=True):
    """Build the user-message content blocks for one dimension's judge.

    Pure / client-free so prompt construction can be verified without an API key.
    Defaults reproduce the slide prompt exactly; documents pass surface="document
    pages", theme_note=False.
    """
    content = [{"type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64}}
               for b64 in image_b64_list]
    lead = f"You are grading the '{dimension}' dimension of generated Cất Cánh {surface}.\n"
    theme = ("The deck may use the light or the dark theme; both are correct, so judge "
             "against the theme the slides actually use.\n") if theme_note else ""
    content.append({"type": "text", "text":
        lead + theme +
        f"Task: {task_desc}\n\nRubric:\n{rubric_text}\n\n"
        "Return JSON {score, justification}. Use \"Unknown\" if you cannot tell."})
    return content
```

Thread the params through `grade_dimension` (lines 63-72) and `grade` (lines 75-81):
```python
def grade_dimension(client, model, image_b64_list, rubric_text, dimension, task_desc,
                    surface="slides", theme_note=True):
    content = build_prompt_content(image_b64_list, rubric_text, dimension, task_desc,
                                   surface=surface, theme_note=theme_note)
    resp = client.messages.create(
        model=model, max_tokens=1024,
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": SCORE_SCHEMA}},
    )
    out = _parse(resp)
    return {"dimension": dimension, "score": out["score"],
            "justification": out["justification"]}


def grade(client, model, image_b64_list, rubrics, task_desc, dimensions=DIMENSIONS,
          surface="slides", theme_note=True):
    dims, scores = {}, {}
    for d in dimensions:
        r = grade_dimension(client, model, image_b64_list, rubrics[d], d, task_desc,
                            surface=surface, theme_note=theme_note)
        dims[d] = r
        scores[d] = None if r["score"] == "Unknown" else int(r["score"])
    return {"dimensions": dims, "scores": scores}
```

- [ ] **Step 4: Create the two doc rubric files**

`scripts/evals/rubrics/doc-pagination.md`:
```markdown
# Coherent pagination (0-5)

Score whether the multi-page A4 document is paginated cleanly and reads as a professionally typeset PDF.

- Content flows sensibly across pages: no awkward gaps, no half-empty page before a
  forced break (except an intended chapter opener).
- No heading is stranded at the foot of a page with its content on the next.
- Tables, figures, callouts, and quotes are not split mid-block in a jarring way; a
  table that spans pages repeats its header.
- Running headers and footers are present and consistent on content pages (logo,
  document or chapter title, page number); the cover has no running chrome.
- Section starts are handled consistently (handbook chapters open a new page; report
  sections flow continuously).

5 = clean, consistent, professionally paginated. 3 = mostly clean with one or two awkward breaks or a missing header/footer. 0 = content overflowing page edges, stranded headings, or broken running chrome.

Return "Unknown" if the images do not show enough pages to judge pagination.
```

`scripts/evals/rubrics/toc-usefulness.md`:
```markdown
# Table of contents usefulness (0-5)

Score whether the table of contents helps a reader navigate the document.

- The TOC lists the document's real sections/chapters in reading order.
- Each entry shows a page number that matches where that section actually starts.
- Entry titles match the headings in the body (same wording).
- Hierarchy is clear: sections and their subsections are visually distinguished
  (indentation or weight).
- The TOC is on its own page (or clearly delimited), legible, and on-brand.

5 = complete, accurate page numbers, clear hierarchy. 3 = usable but with a wrong page number, a missing entry, or flat hierarchy. 0 = missing, empty, or page numbers that do not match the content.

Return "Unknown" if no TOC page is visible in the images.
```

- [ ] **Step 5: Wire documents into `scripts/evals/run_evals.py`**

Add the doc-lint import next to the existing imports (after line 17):
```python
from visgen.doc_lint import lint_doc  # noqa: E402
```

Replace `_render` (lines 26-29) with a renderer-aware version:
```python
def _render(content_path, out_dir, renderer="canvas"):
    if renderer == "doc":
        cmd = [sys.executable, str(ROOT / "scripts/ops/render_doc.py"),
               str(ROOT / content_path), "--out", str(out_dir)]
    else:
        cmd = [sys.executable, str(ROOT / "scripts/ops/render_canvas.py"),
               str(ROOT / content_path), "--format", "both", "--out", str(out_dir)]
    subprocess.run(cmd, check=True, cwd=str(ROOT))
```

Replace `run_task` (lines 32-51) so it grades docs with `lint_doc`:
```python
def run_task(task, k, out_root, judge=False):
    renderer = task.get("renderer", "canvas")
    trial_results = []
    for t in range(1, k + 1):
        trial_dir = out_root / task["id"] / f"trial-{t:02d}"
        trial_dir.mkdir(parents=True, exist_ok=True)
        _render(task["content"], trial_dir, renderer=renderer)
        html = (trial_dir / "index.html").read_text(encoding="utf-8")
        report = json.loads((trial_dir / "render_report.json").read_text(encoding="utf-8"))
        if renderer == "doc":
            pdf = sorted((trial_dir / "pdf").glob("*.pdf"))[0]
            brand = lint_doc(html, report, pdf)
        else:
            brand = lint(html, report,
                         required_strings=task.get("required_strings", []),
                         forbidden_strings=task.get("forbidden_strings", []),
                         expected_page_px=task.get("expected_page_px"))
        transcript = {"task": task["id"], "trial": t, "brand": brand}
        if judge:
            transcript["rubric"] = _judge(task, trial_dir)
        (trial_dir / "transcript.json").write_text(
            json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
        trial_results.append(brand["passed"])
    return {"task": task["id"], "trials": k, "brand_pass": trial_results,
            **metrics(trial_results, k)}
```

Replace `_judge` (lines 54-65) so doc tasks use the extra dimensions and doc-worded prompt:
```python
def _judge(task, trial_dir):
    import base64
    import importlib.util
    spec = importlib.util.spec_from_file_location("grade_rubric", ROOT / "scripts/ops/grade_rubric.py")
    gr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gr)
    import anthropic
    pngs = sorted((trial_dir / "png").glob("page-*.png"))
    imgs = [base64.standard_b64encode(p.read_bytes()).decode() for p in pngs]
    rubric_dir = ROOT / "scripts/evals/rubrics"
    if task.get("renderer") == "doc":
        dims = list(gr.DIMENSIONS) + list(gr.DOC_DIMENSIONS)
        surface, theme_note = "document pages", False
    else:
        dims = list(gr.DIMENSIONS)
        surface, theme_note = "slides", True
    rubrics = {d: (rubric_dir / f"{d}.md").read_text(encoding="utf-8") for d in dims}
    return gr.grade(anthropic.Anthropic(), "claude-opus-4-8", imgs, rubrics,
                    task["description"], dimensions=dims, surface=surface, theme_note=theme_note)
```

Finally, add `.md` reference synthesis inside the `if not args.task:` block in `main`,
right after the existing `*.content.json` synthesis loop (after line 108):
```python
        for ref in sorted((ROOT / "scripts/evals/references").glob("*.md")):
            rel = ref.relative_to(ROOT).as_posix()
            if rel in covered:
                continue
            tasks.append({
                "id": f"ref-{ref.stem}",
                "description": f"Regression: render + doc-lint reference exemplar {ref.name}.",
                "content": rel,
                "renderer": "doc",
                "trials": 1,
            })
```

- [ ] **Step 6: Run the doc eval tests, then the full harness**

Run: `uv run pytest scripts/tests/test_doc_evals.py -v`
Expected: 3 PASS.

Run: `PYTHONIOENCODING=utf-8 uv run python scripts/evals/run_evals.py`
Expected: renders every canvas seed task + all canvas references AND both doc
references (`ref-cat-canh-cohort-report`, `ref-cat-canh-fellow-handbook`); writes
`scripts/evals/runs/latest/aggregate.json`; every entry `"pass_at_k": 1.0`.

- [ ] **Step 7: Commit**

```bash
git add scripts/evals/run_evals.py scripts/ops/grade_rubric.py scripts/evals/rubrics/doc-pagination.md scripts/evals/rubrics/toc-usefulness.md scripts/tests/test_doc_evals.py
git commit -m "feat(m2): wire documents into eval harness (doc render+lint branch, .md refs) + doc rubrics"
```

---

### Task 11: Document the decorative-vs-functional status-color policy in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (Brand section)

**Interfaces:**
- Consumes: nothing. Produces: the written policy governing every future session (matches the standing 2026-07-08 decision that `--warn`/`--bad` are brand-lint-allowed but functional-only).

- [ ] **Step 1: Add the status-color bullet to CLAUDE.md**

In `CLAUDE.md`, under `## Brand (non-negotiable)`, insert a new bullet immediately
after the "Palette:" bullet (the one ending "no hardcoded hexes outside `brand/`.").
Add exactly:
```markdown
- Status colors `--warn` `#F5A524` (amber), `--bad` `#DC2626` (red), and `--good`
  (green) are functional-only: use them for document callouts, status and
  validation states, and data encodings that carry meaning; never as decorative
  fills or as a brand accent (navy, green, and gold carry the brand). They stay
  brand-lint-allowed because their use is functional, not decorative.
```

- [ ] **Step 2: Verify the note landed and the file is still clean**

Run:
```bash
grep -n "functional-only" CLAUDE.md
```
Expected: one match under the Brand section. Confirm by eye that the bullet reads
correctly and no em/en dash was introduced.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(m2): document decorative-vs-functional status-color policy in CLAUDE.md"
```

---

### Task 12: M2 acceptance gate

**Files:**
- None new. Verifies the full M2 deliverable.

**Interfaces:**
- Consumes: everything above. Produces: a verified green state for M3 to build on.

- [ ] **Step 1: Full test suite**

Run: `uv run pytest -v`
Expected: ALL PASS, including the M1 suite (unchanged) and the new M2 files:
`test_doc_deps`, `test_doc_schema`, `test_doc_templates`, `test_doc_html_render`,
`test_doc_render`, `test_doc_lint`, `test_doc_skill`, `test_reference_exemplars_clean`,
`test_doc_evals`. The canvas HTML/theme tests passing confirms the `_theme_css`
refactor (Task 4) did not change canvas output.

- [ ] **Step 2: Render + grade both exemplars end-to-end via the CLIs**

```bash
for ref in cat-canh-cohort-report cat-canh-fellow-handbook; do
  PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_doc.py \
    "scripts/evals/references/$ref.md" --out "output/accept-$ref" &&
  PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_doc.py "output/accept-$ref" || echo "FAILED: $ref"
done
```
Expected: two `"passed": true`, zero `FAILED:` lines. Confirm each
`render_report.json`: every page `overflow: false`, `orphan_headings` empty, every
`toc` entry has an integer `targetPage`, and content pages (`page >= 2`) show
`hasHeader` and `hasFooterNum` true.

- [ ] **Step 3: Confirm the gated-content rules hold (no TK, no PII)**

Run: `uv run pytest scripts/tests/test_reference_exemplars_clean.py -v`
Expected: ALL pass (>= 2 exemplars, zero `TK:` markers, no em/en dashes, diacritics
intact).

Then manually confirm no private data: the only people/contacts in the two
exemplars are the public founder (Dr. Loi Nguyen) and program contacts
(`catcanh@visemi.org`, `visemi.org`). No fellow/applicant names, personal emails,
or individual profiles appear. If any slipped in, remove them (program-level or
aggregate facts only) and re-render/grade before proceeding.

- [ ] **Step 4: Eyeball the PNGs against intent**

Read a spread from each exemplar's `output/accept-*/png/`:
- Cohort report: cover (data-forward), TOC page with real page numbers and dotted
  leaders, a body page with a navy-header table and a functional callout, running
  header showing the document title + logo, footer page number.
- Fellow handbook: warmer cover with the "Handbook" label + edition, a chapter
  opener starting on its own page with the green top rule, running header showing
  the current chapter name.

Any off-brand color, wrong font, overflow, stranded heading, or mismatched TOC page
number is a defect to fix before closing M2.

- [ ] **Step 5: Full eval harness once more, from clean**

```bash
rm -rf scripts/evals/runs/latest
PYTHONIOENCODING=utf-8 uv run python scripts/evals/run_evals.py
```
Expected: every entry in the printed aggregate `"pass_at_k": 1.0`, including
`ref-cat-canh-cohort-report` and `ref-cat-canh-fellow-handbook`.

- [ ] **Step 6: Final commit**

```bash
git add -A
git status   # verify: nothing under output/ or scripts/evals/runs/ is staged
git commit -m "feat(m2): M2 acceptance - document renderer + generate-doc green, both exemplars pass, evals 1.0"
```

---

## After M2 (not in this plan)

- **M3:** `generate-social-post` (square/portrait/story/link canvas sizes, photo
  slots, feed-legible layouts) - new plan via superpowers:writing-plans, reusing
  the canvas renderer.
- **M4:** `generate-poster` + the `visual-designer` agent (brief -> pick skill/format
  -> author -> render -> grade -> iterate).
- **M5:** skill-description optimization pass (skill-creator), design-kit markdown
  update pass, portability audit (no absolute paths, engine extractable).
- **Skill iteration:** run the skill-creator loop (with-skill vs baseline, eval
  viewer, human review) on `generate-doc`.
