# Visual Generation Skills Suite — Design

**Date:** 2026-07-08
**Repo:** `visual-generation`
**Status:** Approved by lanph@visemi.org (interview + section-by-section review)

## Goal

A suite of Claude Code skills that generate VISEMI-branded visuals — slides, reports,
handbooks, social media posts, posters/event graphics — as HTML that converts cleanly
to PDF (and PNG), with a complete tools/scripts/evals/graders stack so every output is
rendered, linted, and verifiable rather than just drafted.

## Decisions made (interview summary)

| Question | Decision |
|---|---|
| Relationship to cat-canh `generate-slides` engine | **Port & generalize** it into this repo; cat-canh keeps its frozen copy |
| Visual types covered | Slides & one-pagers, social posts, reports & handbooks, posters & event graphics |
| Build order | Slides port first, then **reports/handbooks**, then social posts, then posters |
| Consumption model | This repo is the studio for now; **design for portability** as the future goal |
| Content format | **JSON for canvas formats, Markdown + front-matter for documents** |
| Gold `#F5B433` | **Sanctioned suite-wide sparing accent** (joins the design-kit palette) |
| Imagery | **Photo slots from day one** (local paths; crops, headshots, scrims — no sourcing/generation) |
| Eval model | **One shared harness**: deterministic lint + LLM rubric judges + pass@k runner |
| Canonical brand source | **`brand/` in this repo** (machine-readable tokens); design-kit markdown updated to point here |
| Architecture | **A: one engine, two renderers, thin skills** |
| Document pagination | **Paged.js + Chromium** (same Playwright stack as canvas) |

The design kit (`references/visemi-internal/design-kit-visemi/`) is explicitly open to
updates to become more Claude-compatible; this repo's `brand/` becomes its
machine-readable companion.

## Repo conventions (apply to all tools/scripts/docs/skills/agents/engines/evals/graders)

- **Don't Repeat Yourself / Single Source of Truth.** Anything needed twice lives
  once, in a shared place: brand values only in `brand/tokens.json`; render/grade
  logic only in `scripts/lib/visgen/`; layout schemas only in `schema.py`; rubric
  language only in `scripts/evals/rubrics/`. Skills and agents point at these — they
  never carry private copies.
- **Build for reuse.** When a task needs a script/helper/skill/agent that future
  tasks could plausibly need again, create or improve the shared one rather than
  writing a throwaway — the repo should get more capable with every task done in it.
  (Recorded in `CLAUDE.md` so it governs every session.)

## Repo layout

```
visual-generation/
├── brand/                        # canonical machine-readable brand source
│   ├── tokens.json               # colors + ramps (incl. gold), type scale, spacing,
│   │                             # radii, per-theme (light/dark) values
│   ├── tokens.css                # GENERATED from tokens.json — never hand-edited
│   ├── fonts/                    # Be Vietnam Pro woff2 (latin + vietnamese, 400–700)
│   ├── logos/                    # visemi color / white / mark
│   └── icons/                    # line-icon set (rocket, globe, grad-cap, network, …)
├── scripts/
│   ├── lib/visgen/               # shared Python engine
│   │   ├── tokens.py             # tokens.json → tokens.css build + palette export
│   │   ├── schema.py             # layout schemas per format family
│   │   ├── html_render.py        # Jinja2 → HTML (theme inline, fonts base64-embedded)
│   │   ├── canvas.py             # fixed-stage renderer (parameterized size) → PNG + PDF
│   │   ├── document.py           # Markdown → HTML → Paged.js/Chromium → A4 PDF + page PNGs
│   │   ├── brand_lint.py         # deterministic lint core (palette from tokens.json)
│   │   ├── doc_lint.py           # pagination-integrity checks for documents
│   │   ├── icons.py / qr.py      # semantic icon registry; segno QR → inline SVG
│   ├── ops/                      # CLI: render_canvas.py, render_doc.py,
│   │                             #      grade_brand.py, grade_rubric.py
│   ├── evals/                    # run_evals.py, rubrics/, tasks/, references/
│   └── tests/
├── .claude/
│   ├── skills/
│   │   ├── generate-slides/      # port of cat-canh (templates, exemplar pointers)
│   │   ├── generate-doc/         # reports + handbooks (template families)
│   │   ├── generate-social-post/
│   │   └── generate-poster/
│   └── agents/visual-designer.md # end-to-end brief → render → grade → iterate agent
├── docs/
├── output/                       # git-ignored rendered output (like cat-canh slides/)
└── references/                   # existing 20 submodules (unchanged)
```

Skills reference the engine only by repo-relative paths; portability later means
relocating this one repo (or extracting `brand/` + `scripts/` as a package), not
re-plumbing N skills.

## Brand system

- `brand/tokens.json` is the single source of truth. `tokens.py` generates
  `tokens.css` (CSS custom properties with light and dark theme blocks) and exports
  the palette allowlist the brand-lint uses — lint can never drift from the theme.
- Palette: design kit core (navy `#001669`, dark purple `#262538`, green `#01B68B`,
  white, the three tint/shade ramps, accent cyan `#00E5FF` very sparingly) **plus**
  gold `#F5B433` and its token shades as a sanctioned sparing accent.
- Typography: Be Vietnam Pro only (400/500/600/700, latin + vietnamese subsets,
  vendored and base64-embedded at render time so renders are offline-deterministic).
- Suite-wide rules carried over from cat-canh: facts from the brief only, never
  invented; no em/en dashes; no emojis; full Vietnamese diacritics ("Cất Cánh",
  never "Cat Canh"); hierarchy by size + weight, green ≈ 10–20% of a layout;
  eyebrow/kicker as the signature polish move; templates use tokens only — no
  hardcoded hexes anywhere outside `brand/`.

## Engine

Everything format-independent lives once in `scripts/lib/visgen/`: theme inlining,
font embedding, the Jinja2 component macro library (cards, stat blocks, avatars with
initials fallback, icon circles, QR cards, dot-grid + glow decor, photo frames with
navy scrim), schema validation, and Playwright driving. Two renderers sit on top.

### Canvas renderer (slides, posts, posters, banners)

Fixed-stage pages at a parameterized size via a **formats registry** (replacing
cat-canh's hardcoded 1920×1080):

| Format key | Size (px) | Used by |
|---|---|---|
| `deck-16x9` | 1920×1080 | slides |
| `one-pager-landscape` | 1920×1080 | slides |
| `square` | 1080×1080 | social posts |
| `portrait` | 1080×1350 | social posts, posters |
| `story` | 1080×1920 | social posts |
| `link` | 1200×627 | social posts |
| `poster-a` | 1240×1748 | posters |
| `banner-wide` | 2048×1448 | posters |
| `email-header` | 1200×400 | posters |

- Input: content JSON `{ "meta": { format, theme, lang, title, decor? },
  "pages": [ { "layout": ..., "content": { ... } } ] }`, schema-validated per layout.
  For deck formats the renderer also accepts cat-canh's `"slides"` key as an alias
  for `"pages"`, so existing cat-canh content JSONs render unchanged (this is what
  makes the M1 acceptance test possible).
- Output: `output/<name>/{index.html, png/page-NN.png, pdf/<name>.pdf,
  render_report.json}` with a per-page `overflow` flag (scrollHeight check).
- Photo slots: layouts accept local image paths; macros handle cover-crops, circular
  headshots, and the navy gradient scrim for text-on-photo legibility.
- Inline emphasis contract unchanged: `<span class="hl">`, `<span class="gold">`,
  `<b>`, `<span class="muted">` only.

### Document renderer (reports, handbooks)

- Input: Markdown with YAML front-matter (`template: report | handbook`, title,
  subtitle, lang, date, audience, cover fields). Markdown → HTML (python-markdown),
  poured into a doc template, paginated by **Paged.js in Chromium** (same Playwright
  stack), printed to PDF.
- Doc templates provide: branded cover page; auto-generated TOC with real page
  numbers (Paged.js target-counters); running headers/footers (logo, doc title,
  page N); heading/callout/table/figure/blockquote styles from tokens; page-break
  rules (no orphaned headings, keep-with-next, figure captions stay with figures).
- Output: A4 PDF with selectable text + per-page PNGs (for graders and eyeballing)
  + a render report.

## Skills (thin) and agent

Each skill = SKILL.md (workflow, layout table, writing rules, worked exemplars) +
`templates/` + reference exemplars in `scripts/evals/references/`. Engine, brand,
graders are shared.

1. **`generate-slides`** — port of cat-canh: 17 layouts (11 event + 6 donor),
   light/dark themes, same content-JSON contract. Existing cat-canh exemplars
   re-render and pass in this repo as the port's acceptance test.
2. **`generate-doc`** — reports and handbooks as two template families over the
   document renderer. One handbook exemplar + one report exemplar ship with it.
3. **`generate-social-post`** — square/portrait/story/link sizes; layouts tuned for
   feed legibility (bigger type floors, one message per canvas, photo or graphic
   background variants, QR/CTA variants).
4. **`generate-poster`** — posters, wide banners, QR cards, email headers; shares
   canvas layouts with social posts where sensible, differs in sizes and density.

**`visual-designer` agent** — generalizes cat-canh's slide-designer: reads the brief,
picks skill + format, authors content JSON/Markdown, renders, runs graders, fixes and
re-renders (cap 4 iterations), eyeballs PNGs, reports output paths + verification
results + any facts it had to ask about.

## Graders & evals

**Deterministic layer (free, every render):**
- Brand-lint core: palette allowlist generated from `tokens.json`; Be Vietnam Pro
  only; no em/en dashes; no emojis; diacritics preserved; correct stage/page size.
- Canvas checks: `overflow: false` per page; minimum font size (≥12px equivalent).
- Document checks (`doc_lint.py`): TOC page numbers match actual heading pages; no
  overflowing page boxes; no orphaned headings; running headers/footers present;
  PDF sanity — expected page count, fonts embedded, text selectable (the
  "converts to PDF cleanly" guarantee).

**LLM rubric layer (optional, `ANTHROPIC_API_KEY`):** isolated judges score rendered
PNGs 0–5 with justification on brand / layout / content / polish; shared rubric core
with per-format additions (documents: coherent pagination, TOC usefulness; social:
legible at feed size, single focal message). Read justifications; don't trust scores
blindly.

**Eval runner:** `scripts/evals/run_evals.py` — one harness across all skills; seed
tasks + reference exemplars per skill (every exemplar regression-covered by a
synthesized task); reports pass@k / pass^k. During development, the skill-creator
loop (with-skill vs baseline runs, eval viewer, human feedback) is the process layer;
the runner is the permanent regression layer this repo keeps.

## Error handling

- Schema validation fails → renderer exits with the field-level error; fix JSON, re-render.
- Overflow or lint failure → fix content (trim/split), never off-brand sizing tricks;
  iteration cap 4, then surface to the operator with the failing report.
- Rubric judge unavailable (no key) → skip, never block.
- Rendered output is never committed (`output/` git-ignored).

## Milestones

1. **M1** — `brand/` tokens + engine port with formats registry + `generate-slides`
   green (cat-canh exemplars re-render and pass here).
2. **M2** — document renderer + `generate-doc` (handbook + report exemplars) + doc graders.
3. **M3** — `generate-social-post` (4 sizes, photo slots).
4. **M4** — `generate-poster` + `visual-designer` agent.
5. **M5** — skill-description optimization pass (skill-creator), design-kit markdown
   update pass, portability audit (no absolute paths, engine extractable).

Each milestone ends verified: exemplars render, lint green, eval runner green, human
eyeball via the skill-creator review viewer.

## Out of scope (v1)

- Canva/Drive integration (the design kit's Canva canon remains for Canva work).
- Photo sourcing or AI image generation (photo *placement* only).
- reveal.js / slidev runtimes (rejected in cat-canh: heavy, weak pixel-exact export).
- Animated/video outputs.
