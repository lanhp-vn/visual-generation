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
