# Reference Harvest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harvest the transferable knowledge from the `taste-skill`, `flat-ui`, and `design-resources-for-developers` submodules into the plugin's lint, skills, agent, and rubrics, and record what was deliberately rejected.

**Architecture:** One module gains a second entry point (`variety_lint.lint_pages`) so per-page copy checks cover every layout instead of only `social-`; new vocabulary checks scan nested strings because deck prose lives in lists of dicts. Everything stays advisory - `brand_lint` remains the only blocking gate. One new skill (`author-brand`) supplies the brand-override derivation method that `visgen-setup` Step 2 lacked. Rubric knowledge folds into the two existing rubrics rather than adding a judged dimension.

**Tech Stack:** Python 3 (stdlib `re` only), Jinja2 templates (untouched here), Markdown skills and rubrics, `uv` for running.

**Spec:** `docs/superpowers/specs/2026-07-24-reference-harvest-design.md`

## Global Constraints

- Palette: navy `#001669`, dark purple `#262538`, green `#01B68B`, white, token ramps, accent cyan `#00E5FF` (very sparing), gold `#F5B433` (sparing). No other hexes; no hardcoded hexes outside `brand/`.
- Type: Be Vietnam Pro only (400/500/600/700).
- No em dashes, no en dashes, no emojis, in code comments and prose alike.
- Vietnamese keeps full diacritics ("Cất Cánh", never "Cat Canh").
- DRY: brand values only in `brand/tokens.json`; render/grade logic only in `scripts/lib/visgen/`; schemas only in `schema.py`; rubrics only in `scripts/evals/rubrics/`.
- The new lint is ADVISORY. It must never cause `brand_lint` to fail, and must never gate `brand_pass` in the eval sweep.
- Violation contract is `{"code": str, "detail": str}`, matching `brand_lint` and `doc_lint`.
- `references/` is read-only. Never edit a submodule; cite it.
- Never `git add` or `git commit` unless the user asks.

---

### Task 1: Widen copy checks to every layout and add vocabulary tells

**Files:**
- Modify: `scripts/lib/visgen/variety_lint.py`
- Test: the module's own `__main__` self-check (this repo's established pattern; no separate test dir exists)

**Interfaces:**
- Consumes: `visgen.schema.document_pages(doc) -> list`
- Produces:
  - `lint_pages(docs) -> {"passed": bool, "violations": list, "pages": int}` - per-page copy checks, every layout
  - `lint_batch(docs) -> {"passed": bool, "violations": list, "posts": int}` - repetition only, `social-` pages only

- [ ] **Step 1: Add the recursive string collector and vocabulary patterns**

Deck layouts nest prose in lists of dicts, so a top-level walk misses it.

```python
_VOCAB = {
    "placeholder-text": re.compile(
        r"\b(lorem ipsum|john doe|jane doe|acme|your name here|company name|tbd|todo)\b", re.I),
    "filler-verb": re.compile(
        r"\b(elevate\w*|unleash\w*|seamless(?:ly)?|next[- ]gen(?:eration)?|revolutioniz\w+"
        r"|supercharge\w*|unlock the power|cutting[- ]edge|game[- ]chang\w+|harness\w*|delve\w*)\b", re.I),
    "coy-social-proof": re.compile(r"\bquietly (?:in use at|trusted by|used by)\b", re.I),
    "poetic-label": re.compile(
        r"\b(from the field|field notes|on our desks|currently on the bench|loose plates)\b", re.I),
    "fake-precise-number": re.compile(r"\b(?:99\.9{1,2}|100\.0{1,2})\s*%|\b1234567"),
}

VI_VOCAB = {}

_DECOR_STRIP = re.compile(r"^(?:[A-Z]{2,}\s*[.·]\s*){1,3}[A-Z]{2,}\.?$")


def _walk_strings(value, path=""):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, sub in value.items():
            if key in NON_TEXT_FIELDS:
                continue
            yield from _walk_strings(sub, f"{path}.{key}" if path else str(key))
    elif isinstance(value, (list, tuple)):
        for i, sub in enumerate(value):
            yield from _walk_strings(sub, f"{path}[{i}]")
```

- [ ] **Step 2: Split scope - `_all_pages`, vocabulary in `_lint_page`, `lint_pages`, and `lint_batch` reduced to repetition**

Page checks move out of `lint_batch` rather than being duplicated, so running both reports each code exactly once.

- [ ] **Step 3: Extend the `__main__` self-check so every new code fires**

```python
    vocab_bad = {"meta": {"format": "deck-16x9"}, "pages": [
        {"layout": "icon-cards", "content": {
            "title": "Seamless care", "eyebrow": "BRAND. MOTION. SPATIAL.",
            "cards": [{"title": "Jane Doe", "body": "We elevate outcomes by 99.99%."}]}}]}
    codes = {v["code"] for v in lint_pages([vocab_bad])["violations"]}
    assert codes == {"filler-verb", "placeholder-text", "fake-precise-number",
                     "decoration-strip"}, codes
```

- [ ] **Step 4: Run the self-check**

Run: `PYTHONIOENCODING=utf-8 uv run python scripts/lib/visgen/variety_lint.py`
Expected: `variety_lint self-check ok`

- [ ] **Step 5: Run the widened lint across all 16 committed exemplars**

A hit on an on-brand committed exemplar means the pattern is wrong, not the exemplar. Fix the pattern, not the exemplar.

Run: `PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_variety.py scripts/evals/references/*.content.json`

---

### Task 2: Report both entry points from the CLI

**Files:**
- Modify: `scripts/ops/grade_variety.py`

**Interfaces:**
- Consumes: `lint_pages`, `lint_batch` from Task 1

- [ ] **Step 1: Merge both reports and update the docstring to state the split scope and advisory status**
- [ ] **Step 2: Run it against a social exemplar and confirm both `pages` and `posts` counts appear**

---

### Task 3: Give the copy lint regression coverage in the sweep

**Files:**
- Modify: `scripts/evals/run_evals.py`

- [ ] **Step 1: Record `lint_pages` findings per trial in the transcript and surface deduped codes in the aggregate, without gating `brand_pass`.** Skip doc tasks: they are Markdown, and this lint reads content JSON.
- [ ] **Step 2: Run the full sweep and confirm no regression**

Run: `PYTHONIOENCODING=utf-8 uv run python scripts/evals/run_evals.py`

---

### Task 4: `skills/author-brand/SKILL.md` (new) and `visgen-setup` Step 2 pointer

**Files:**
- Create: `skills/author-brand/SKILL.md`
- Modify: `skills/visgen-setup/SKILL.md` (Step 2)
- Modify: `.claude-plugin/plugin.json` if skills are enumerated there

- [ ] **Step 1: Check whether the plugin manifest enumerates skills**
- [ ] **Step 2: Write the six-step method from the spec, citing `design-resources-for-developers` for asset sourcing**
- [ ] **Step 3: Shrink `visgen-setup` Step 2 to a pointer**

---

### Task 5: `visual-designer` quality fix-ladder

**Files:**
- Modify: `agents/visual-designer.md`

- [ ] **Step 1: Add Step 5b with the seven-rung ladder, bounded by the existing four-pass cap**
- [ ] **Step 2: Add the rejected-upgrades line (no noise or grain, no gradient-family swaps, no font swaps, no motion) to Anti-patterns**

---

### Task 6: Rubric enrichment

**Files:**
- Modify: `scripts/evals/rubrics/polish.md`
- Modify: `scripts/evals/rubrics/layout.md`
- Modify: `scripts/evals/rubrics/flat.md`

- [ ] **Step 1: `polish.md` - anti-nested-box, micro-UI clutter, decorative grids, filled tracks, uniform radius; reword "slide" to the canvas**
- [ ] **Step 2: `layout.md` - headline line cap, baseline alignment, break relentless centering, optical padding; reword "slide" and drop the hardcoded 1920x1080**
- [ ] **Step 3: `flat.md` - add the `flat-ui` provenance line**

---

### Task 7: Docs - ledger pointer, submodule count, social skill scope note

**Files:**
- Modify: `CLAUDE.md` (one line)
- Modify: `skills/generate-social-post/SKILL.md`

- [ ] **Step 1: `CLAUDE.md` - point the `references/` line at the ledger and fix the stale count (15 to 18)**
- [ ] **Step 2: `generate-social-post/SKILL.md` - note that copy checks now cover every layout while repetition stays social-only**

---

### Task 8: Final verification

- [ ] **Step 1: `variety_lint` self-check passes**
- [ ] **Step 2: All 16 exemplars clean under the widened lint**
- [ ] **Step 3: Full `run_evals.py` sweep green**
- [ ] **Step 4: `git status` reviewed and reported to the user; do not commit**
