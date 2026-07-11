---
name: generate-doc
description: Build brand-locked VISEMI / Cất Cánh reports and handbooks from Markdown with YAML front-matter, paginate them with Paged.js in headless Chromium, and print an A4 PDF with selectable text plus per-page PNGs, then grade them (deterministic doc-lint + brand-lint, optional LLM-judge rubric). Use whenever the operator wants a report, cohort or program report, donor/partner/founder update, impact report, handbook, fellow or mentor handbook, guide, or any "write this up as a proper PDF / make a report / make a handbook" task, even if they do not say "Markdown" or "PDF". Content is Markdown (facts from the brief, never invented); layout is one of two template families (report or handbook); brand lives in brand/tokens.json. A4, light theme, local only.
---

# generate-doc

Produces VISEMI / Cất Cánh reports and handbooks in the house brand: navy `#001669`, green `#01B68B` accent, gold `#F5B433` (sparing), Be Vietnam Pro, on A4 pages with a branded cover, an auto table of contents with real page numbers, and running headers/footers. It separates three concerns: **content** (a Markdown file with YAML front-matter), **layout** (the report or handbook template family), **brand** (the tokens in `brand/tokens.json`), so output is repeatable, gradeable, and on-brand. It is the document counterpart to `generate-slides`: same engine, same brand, a second renderer.

> **Workspace note.** Templates and `document.css` are vendored under this skill
> (`skills/generate-doc/`). Brand assets (fonts, logos, icons, tokens) are
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
  Report covers also accept `tagline` (a green positioning line), `founders` (a
  "Founded by ..." line), `organizer`, `sponsors`, `cover_stats` (a list of
  `"value|label"` strings shown as a stat band), `cover_stats_2` (an optional
  second, shorter list of `"value|label"` strings shown as its own centered
  row below `cover_stats` - for a distinct group of numbers, e.g. program-scale
  stats vs. cohort stats), `partner_logos` (a list of logo paths shown beside
  the VISEMI mark), and `cover_bg_logo` (a single image path rendered as a
  decorative watermark in the cover's top-right corner; see Cover extras below).
- Body Markdown supports (via `python-markdown` `extra` + `toc` + `admonition`):
  headings, paragraphs, **bold**/`links`, bullet and numbered lists, tables,
  footnotes, blockquotes, fenced code, callouts, and the rich HTML components
  below (stat tiles, bars, pies, profile cards). Do not hardcode a color hex or an
  inline style that carries a brand/type value; styling comes from the tokens.
  Data-carrying inline values (a bar's `width:NN%`, a pie's `conic-gradient` built
  from `var()` colors) are the sanctioned exception.
- **Content before the TOC.** A `<!-- TOC -->` marker in the body splits it:
  everything before the marker renders right after the cover, ahead of the auto
  table of contents (e.g. a one-page program summary); everything after follows the
  TOC. The TOC is always built from the post-marker headings.

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

## Rich components (HTML blocks in the Markdown)

`document.css` ships token-driven, print-safe components you drop into the Markdown
as raw HTML blocks (surround with blank lines so `md_in_html` treats them as blocks).
Colors come from token classes, never inline hex. Modeled on structures mined from
`references/ui-component-libs/{tabler,gentelella}` and restyled to VISEMI.

- **Stat tiles (`.statrow` / `.stile`)** - a KPI row, big number over label, auto-fits:
  ```html
  <div class="statrow">
    <div class="stile"><strong>65</strong><span>Fellows</span></div>
    <div class="stile"><strong>14</strong><span>Universities</span></div>
  </div>
  ```
- **Proportional bars (`.bars`)** - a category distribution; the fill width is the
  ACTUAL share, never normalized to the max (or a 40% value renders as a full bar):
  ```html
  <div class="bars">
    <div class="bar-row"><span class="bar-label">US</span><div class="bar-track"><div class="bar-fill" style="width:65%"></div></div><span class="bar-val">39 (65%)</span></div>
  </div>
  ```
- **100% stacked bar + legend (`.stackbar` / `.legend`)** - parts of a whole; segment
  and swatch colors are the categorical set `c1`-`c6` (navy, green, gold, navy-300,
  green-300, purple-300):
  ```html
  <div class="stackbar"><div class="seg c1" style="width:40%"></div><div class="seg c2" style="width:37%"></div></div>
  <div class="legend"><span><i class="c1"></i>CS &amp; Maths: 24 (40%)</span></div>
  ```
- **Pie chart (`.pie-disc` / `.pie-legend`)** - weights that sum to 100% (e.g. a
  rubric); pure-CSS `conic-gradient` with `var()` colors. Pair two with `.twocol`:
  ```html
  <div class="pie-disc" style="background:conic-gradient(var(--navy) 0 30%, var(--green) 30% 55%)"></div>
  <div class="pie-legend"><span><i class="c1"></i>Research (30%)</span></div>
  ```
- **Profile card (`.pcard`)** - a person spotlight, ~3 per page. Precede each group
  with a `## Field name ({n} fellows) {: .pgroup }` heading (a colored section band;
  add `.er` for the gold "Early Research" variant). Metric-forward; omit the
  Publications stat and research line when a fellow has 0 publications:
  ```html
  <div class="pcard">
    <p class="pcard-name">Name</p>
    <p class="pcard-sub">Institution &middot; Major</p>
    <div class="pcard-stats"><div><strong>3.9</strong><span>GPA</span></div></div>
    <p class="pcard-hi">One to three sentences naming awards in full.</p>
    <p class="pcard-needs"><b>Support needs:</b> ...</p>
  </div>
  ```
- **Two-column block (`.twocol`)** - `<div class="twocol"><div>..</div><div>..</div></div>`
  for side-by-side lists or a pie pair.

**Chart choice:** proportional `.bars` for multi-select / independent categories;
`.stackbar` for one whole split into parts; `.pie-disc` for weights summing to 100%.
The `c1`-`c6` order is fixed so every chart reads as one system.

## Profile-heavy / per-fellow documents

Reports that profile individuals (e.g. a cohort's fellows) carry real PII, so:

- Never commit the generated Markdown or the rendered output when it holds real
  fellow data. Keep the source `.md` in a scratchpad outside the repo; `output/` is
  already git-ignored.
- Per-fellow facts live in `cat-canh-program-management/data/fellow_info/<name>/`.
  The `SUMMARY-EVALUATION-R1R2.md` is the reliable, correctly-matched source; some
  folders hold MISFILED loose PDFs (another applicant's Resume/SOP), so verify a PDF
  is the right person (name / md5) before trusting it. Tier-4 "Early Research"
  fellows have only PDFs (no summary/application markdown).
- Card highlights name awards in FULL (title + level + year), never a vague "First
  Prize", and carry NO reviewer/interviewer names or internal evaluation terms
  (R1/R2, composite, "the reviewer flagged"). State impressions as plain fact.

## Cover extras (report)

The report cover renders, when present in front-matter: a `partner_logos` lockup
beside the VISEMI mark (each path `.svg` inlined or raster embedded as a base64
data URI; repo-relative like `brand/logos/marvell-logo.webp` or absolute), a green
`tagline`, a `founders` line, a `cover_stats` band (`"value|label"` items) plus an
optional `cover_stats_2` second band shown as its own centered row, an
`organizer` / `sponsors` credits line, and a `cover_bg_logo` (one image path,
repo-relative or absolute, any raster or SVG format) rendered as a small
decorative watermark in the cover's top-right corner, behind all other cover
content. The whole hero block (logos, eyebrow, tagline, title, subtitle,
founders, stats) is centered as a unit; date/audience and the org line sit in a
separated footer strip at the bottom. Loading logic is `_load_partner_logos` /
`_load_data_uri` in `visgen/html_render.py`.

`cover_bg_logo` is embedded as an opaque base64 data URI for use as a plain CSS
`background-image` - it is NOT inlined as manipulable markup, so an icon built
on `stroke="currentColor"` (the `brand/icons/*` set) renders in whatever color
the browser defaults `currentColor` to (black) rather than an on-brand tone,
and a raster logo with a solid/white matte behind it paints as a visible hard
edge, not a subtle watermark. Neither is caught by brand-lint (it does not
decode embedded image bytes) or `doc_lint` (no overflow, so no failure) - only
eyeballing the rendered PNG catches it. Use genuinely watermark-style art:
pre-colored, with real alpha transparency around the shape (like a line/pattern
motif), never a generic monochrome icon or an opaque logo file.

## Page-break behavior

Headings use `break-after: avoid` (never orphaned at a page foot) and
`break-inside: avoid`. Figures, blockquotes, callouts, and table rows avoid
breaking mid-block. Handbook chapter headings force a page break before; report
`#` headings flow continuously by default (no forced break) - opt one into a
fresh page with `# Section title {: .pagebreak }` (e.g. a closing/CTA section
that should stand alone rather than share a page with what precedes it). If
content overflows a page box, fix the content (trim or split a section), never
off-brand sizing tricks; `doc_lint` fails on any overflow.

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
- Hardcoding a color hex, or an inline style carrying a brand/type value, in the
  Markdown or `document.css`; styling lives in the tokens. (Data-carrying inline
  values - a bar's `width:NN%`, a pie's `conic-gradient` of `var()` colors - are
  the sanctioned exception.)
- Putting a reviewer/interviewer name or an internal evaluation term (R1/R2,
  composite, "the reviewer flagged") in a fellow profile; naming an award vaguely
  ("First Prize") instead of its full title.
- Normalizing a `.bars` fill to the max value so a minority share reads as a full
  bar; use the actual percentage as the width.
- Using a status color (amber/red/green) as a decorative fill instead of a
  functional callout/status accent.
- Declaring a document done without rendering it and checking `render_report.json`
  (overflow false, TOC resolved, no orphaned headings) and eyeballing the PNGs.
- Committing anything under `output/`.
- Using a `brand/icons/*` currentColor icon or an opaque/matte logo file as
  `cover_bg_logo` - it bakes in the wrong color or a visible hard edge, and
  neither brand-lint nor `doc_lint` will catch it; only the rendered PNG will.
- Forcing a cover heading to one line with `white-space: nowrap` against
  `.cover`'s `overflow: hidden` - a longer title/eyebrow than the one you
  tested against will silently clip instead of wrapping. Size for the common
  case and let it wrap; don't force single-line.
