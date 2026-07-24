# Reference harvest: taste-skill, flat-ui, design-resources-for-developers

Design for what this repo takes from the three submodules added on 2026-07-23/24,
where each piece lands, and - equally load-bearing - what is deliberately NOT
taken and why.

## Why this exists

Three submodules landed without being harvested:

| Submodule | Added | Cited before this work |
| --- | --- | --- |
| `references/ui-component-libs/flat-ui` | 2026-07-23 (`f4398e7`) | nothing but `.gitmodules` |
| `references/design-inspiration/design-resources-for-developers` | 2026-07-23 (`f4398e7`) | nothing but `.gitmodules` |
| `references/claude-design-galleries/taste-skill` | 2026-07-24 (`b9c94e4`) | `variety_lint.py` only |

`taste-skill` is 13 sub-skills and roughly 6,700 lines, of which only the
social-post composition rules had been mined. The other two are thin, and saying
so plainly is part of the design rather than a gap in it.

## Value assessment per submodule

**`taste-skill` - the substance.** Sections that transfer to a fixed-canvas,
brand-locked, HTML-to-PNG pipeline: §9 AI TELLS, §14 pre-flight, `redesign-skill`
Design Audit, `stitch-skill` synthesis method, `image-to-code-skill` §14/§16/§17.
Everything else is React/Tailwind/GSAP/scroll/mobile/image-generation and does
not apply: we render a static page at a fixed size from validated JSON.

**`design-resources-for-developers` - a bookmark file.** 1,526 lines of curated
external links, no offline content. Its single legitimate use in a local-only
pipeline is asset sourcing when someone authors a new `brand/` override, so it is
cited from exactly one place (`skills/author-brand/SKILL.md`) and nowhere else.

**`flat-ui` - kept, cited, not harvested.** A 2013 Bootstrap/LESS kit, 16 MB,
shipping only a compiled `dist/css/flat-ui.css` and a 67 KB components page. Its
design system is already captured better by `scripts/evals/rubrics/flat.md` than
by the kit itself. Decision: keep it on disk as a concrete gradient-free
component reference and add a provenance line to `flat.md` so it stops being
orphaned. Mining its Bootstrap-3 idiom into our tokens-only Jinja2 templates
would be high effort for low yield.

## The DRY finding that shaped the lint work

`variety_lint._lint_page` already implemented middot-spam, per-field word caps,
`numbered-eyebrow`, and `version-label`. All of it was gated to `social-` layouts
by `_social_pages()`.

Nothing about those checks is social-specific. `eyebrow` is rendered by **9 of
the slides layouts, both poster layouts, and both document covers** - so a pitch
deck could carry `01 / Index` or `BETA` in the eyebrow on every page and nothing
would catch it. The gap was scope, not rules.

A second finding: deck layouts keep their prose in **nested** structures
(`items`, `columns`, `cards`, `stats`, `people`, `phases`, `tiers`, `blocks`).
A top-level-only field walk would miss nearly all deck text, so vocabulary
checks need a recursive string collector to be worth anything.

## Design

### 1. `variety_lint` gains `lint_pages()`; scope splits by rule kind

One module, two entry points with deliberately different scopes. No new files, no
new CLI, no codes moving between tools.

- `lint_pages(docs)` - per-page copy checks on **every** layout.
- `lint_batch(docs)` - repetition checks on **`social-` pages only**. A deck
  legitimately repeats `stat-grid`; a campaign does not legitimately repeat
  `social-hero`.

Page checks move out of `lint_batch` rather than being duplicated, so running
both reports each code exactly once. `grade_variety.py` runs both and merges.

Both stay **advisory**. `brand_lint` remains the only blocking gate, because
these rules are judgment calls with real false-positive cost: a slop-verb
blocklist will eventually flag a headline someone actually wants. No suppression
flag is needed precisely because nothing blocks.

**Rule placement, and why it is not uniform:**

| Rule kind | Scope | Reason |
| --- | --- | --- |
| Word caps, numbered-eyebrow, version-label | top-level fields, all layouts | field-specific by design; a nested walk would misapply a feed-legibility cap to deck body prose |
| Vocabulary tells | every string, nested included | deck prose lives in lists of dicts; a top-level walk would miss it |
| `decoration-strip` | `eyebrow` and `foot` only | the tell lives in those two slots; scanning everywhere would flag legitimate all-caps branding |
| `middot-spam` | `social-` only | see below - widening it was wrong |
| Repetition, eyebrow overuse | `social-` only | unchanged, and correct as it stands |

**`middot-spam` was widened and then reverted, which is the process working.**
Widening it flagged three committed, on-brand exemplars: a wide `email-header`
`sub` carrying a three-part event metadata strip, and a `columns` field carrying a
four-part role chain in two decks. Both are deliberate, legible idioms. Middot
rationing is a feed-legibility rule: a dotted strip is noise on a small social
overlay and a correct compact idiom on a wide email header or a 1920x1080 deck
column. Per the rule below, the pattern was wrong, not the exemplars, so it stays
social-only. The self-check pins both directions - those two shapes must stay
clean, and the same shape on a `social-` layout must still fire.

### 2. New vocabulary codes (English only)

| Code | Catches |
| --- | --- |
| `placeholder-text` | `Lorem ipsum`, `John/Jane Doe`, `Acme`, `Your name here`, `Company Name`, `TBD`, `TODO` |
| `filler-verb` | `Elevate`, `Unleash`, `Seamless`, `Next-Gen`, `Revolutionize`, `Supercharge`, `Unlock the power of`, `Cutting-edge`, `Game-chang*`, `Harness`, `Delve` |
| `coy-social-proof` | `Quietly in use at`, `Quietly trusted by` |
| `poetic-label` | `From the field`, `Field notes`, `On our desks`, `Currently on the bench` |
| `decoration-strip` | verbless all-caps strips: `BRAND. MOTION. SPATIAL.`, `DESIGN · BUILD · SHIP` |
| `fake-precise-number` | narrow only: `99.9%`, `99.99%`, `100.0%`, sequential runs like `1234567` |

`placeholder-text` is the highest-value addition: it is a machine-check for this
repo's standing "facts come from the operator's brief, never invented" rule.

**Vietnamese:** `VI_VOCAB` ships intentionally empty with a docstring saying so.
Vietnamese marketing has its own slop register that requires native-speaker
judgment; guessing it would ship false positives against real Vietnamese copy.
The hook exists so adding phrases later needs no logic change.

**Excluded on purpose:** `Transform` and `Empower` are omitted from
`filler-verb`. Both are slop in the abstract and both are ordinary, legitimate
words in health and nonprofit copy; at advisory severity the noise would still
train operators to ignore the report.

### 3. Regression coverage

`run_evals.py` renders and brand-lints every reference exemplar but never ran the
copy lint, so these rules had no regression coverage in the sweep. `run_task`
now records `lint_pages` findings per trial in the transcript and surfaces the
deduped codes in the aggregate, **without** gating `brand_pass` - advisory in the
sweep exactly as it is on the CLI. Doc tasks are skipped: they are Markdown, and
this lint reads content JSON.

The dirty cases live in the module's `__main__` self-check, matching the pattern
the module already used. The 16 committed exemplars stay clean, and running the
widened lint across all of them is the real test: **a hit on an on-brand
committed exemplar means the pattern is wrong, not the exemplar.**

### 4. `skills/author-brand/SKILL.md` (new)

`visgen-setup` Step 2 was `cp -r brand/*` followed by "edit tokens.json as
needed" - no method for deciding a theme. `stitch-skill`'s reference-synthesis
and `brandkit`'s brand-strategy-first supply one, retargeted from "produce a
web-page DESIGN.md" to "fill `brand/tokens.json` plus fonts, logos, icons":

1. Brand strategy inference - category, audience, emotional promise, what the
   brand must avoid. (`brandkit`'s logo-symbol metaphor table is dropped; this
   repo does not generate logos.)
2. Palette as named roles, not swatches: every hex gets a descriptive name and a
   functional role, mapped onto the token contract that already exists.
3. Type: one family at 400/500/600/700, scale from the existing `type_scale`,
   body around 65 characters, negative tracking on display sizes.
4. Assets: woff2 subsets, logos (color / white / mark), monoline SVG icons. This
   is the one place `design-resources-for-developers` is cited.
5. Write the brand's own anti-pattern list into the override.
6. Verify: regenerate `tokens.css`, render an existing exemplar with `--brand`,
   confirm brand-lint palette closure.

`visgen-setup` Step 2 shrinks to a pointer. No new rubric or lint: `brand_lint`
already validates palette closure once tokens land.

### 5. `visual-designer` quality fix-ladder

Step 5 handled only overflow and brand violations - a rendered-but-mediocre
visual had no defined next move. `redesign-skill`'s own Fix Priority is unusable
here (it opens with "font swap" and includes hover and loading states), so the
ladder is derived rather than copied, ordered impact-over-risk for a fixed
canvas, and bounded by the existing four-pass cap:

1. Cut content before resizing type
2. Hierarchy via weight and color, not raw scale
3. Spacing rhythm: even gutters; align shared elements across side-by-side cards
4. De-clutter: drop eyebrows, pills, badges, meta rows carrying no fact
5. De-nest: collapse card-in-card-in-panel to one framing move
6. Reflow orphans and widows
7. Only then swap layout

### 6. Rubric enrichment, no new dimension

Folded into the two existing rubrics rather than adding a `slop` dimension: a
fifth default dimension costs an API call per image on every judged run for
content that overlaps `polish`.

- `polish.md` gains anti-nested-box, micro-UI clutter, decorative hairline and
  crosshair grids, filled-track progress bars as comparison visuals, and
  uniform-radius-on-everything.
- `layout.md` gains a headline line cap, shared-element baseline alignment across
  side-by-side cards, breaking relentless centering, and optical vertical padding.
- Both rubrics said "the slide" and "1920x1080" while also grading social posts,
  posters, and email headers. Reworded to the canvas.
- `flat.md` gains the `flat-ui` provenance line.

Tinted-not-black shadows stays in `flat.md` only. The VISEMI theme ships `--grad`
and is therefore not flat; `polish.md` must stay theme-agnostic.

## Deliberately NOT harvested

Recorded because a future session reading these submodules cold will otherwise
"upgrade" this repo off-brand. Each of the following is a direct instruction in
the vendored references that **contradicts a non-negotiable here**.

**From `redesign-skill` and `stitch-skill`:**

| Their instruction | Why rejected |
| --- | --- |
| "Flat design with zero texture. Add subtle noise, grain, or micro-patterns" | `flat.md` bans texture and noise outright |
| "Perfectly even gradients - break with radial, noise, or mesh gradients" | `flat.md` bans gradients; VISEMI's `--grad` is a fixed token, not a canvas to improvise on |
| "Replace with a font that has character: Geist, Outfit, Cabinet Grotesk, Satoshi" | Be Vietnam Pro only, and it carries the Vietnamese subset the brand requires |
| "`Inter` is BANNED" | `Inter` here is a CSS fallback in `font_stack`, never a chosen face |
| "Maximum 1 accent color" | the token contract deliberately carries `--accent`, `--accent-2`, `--accent-3` plus gold |
| "Add high-quality background imagery, ambient gradients, picsum.photos seeds" | facts and assets come from the operator's brief; no invented imagery |
| Hover, active, loading, empty, error states; spring physics; staggered mounts | output is a static PNG and PDF |
| `min-h-[100dvh]`, mobile collapse, touch targets, `clamp()` scaling | output is a fixed-size canvas, not a viewport |

**From `taste-skill` §9 and §14:**

| Their instruction | Why rejected |
| --- | --- |
| "NO 3-column equal feature cards" | `stat-grid`, `icon-cards`, and `columns` are deliberate house layouts |
| em-dash and en-dash ban, emoji ban, pure-black ban | already fully enforced by `brand_lint`; restating them here would duplicate the source of truth |
| "NO scroll cues", marquee caps, nav height, Core Web Vitals | nothing scrolls, animates, or loads in a PNG |
| "NO pills or labels overlaid on images" | the social photo layouts overlay text on a scrim by design; only decorative meta-captions are a tell |
| Icon-library mandates (Phosphor / HugeIcons / Radix) | icons are vendored monoline SVGs under `brand/icons/` |

**Whole sub-skills not harvested:** `imagegen-frontend-web`,
`imagegen-frontend-mobile`, and most of `image-to-code-skill` (~3,700 lines) are
image-generation prompting and screenshot-to-code. This pipeline renders HTML
deterministically from validated JSON; there is no image-generation step to
prompt. `brandkit`'s logo and board-composition system is likewise unused - we
place existing logo assets, we do not generate them.

**Deferred, not rejected:** `minimalist-skill`, `soft-skill`, and
`brutalist-skill` are real content and could each become an opt-in rubric beside
`flat.md`. No brand in play needs them: VISEMI ships `--grad` and is not flat,
Nouslogic is flat and already covered. Adding three unused rubrics would be
speculative.

## Found, not fixed

Noticed while mapping the token contract for `author-brand`, out of scope for this
work, and recorded here so it is not re-discovered from scratch:

**Eight CSS custom properties are referenced by templates or stylesheets with no
definition in `tokens.json` and no `var()` fallback:** `--ease`, `--font-mono`,
`--font-serif`, `--letter-normal`, `--letter-tight`, `--shadow`, `--shadow-lg`,
`--token`. An undefined custom property with no fallback resolves to an invalid
value, so any declaration relying on one is silently dropped - `var(--shadow)`
means no shadow renders at all. This affects the studio default brand, not just
overrides, and brand-lint cannot catch it because the lint validates the palette
in `tokens.json` rather than the set of names the CSS actually consumes.

Fixing it is an engine change: either define the eight tokens per theme, or give
each reference a fallback, or add a lint that diffs referenced names against
defined ones. The last option is the one that would keep the class of bug from
returning.

## Verification

- `variety_lint.py` `__main__` self-check passes, with every new code exercised.
- The widened lint runs clean across all 16 committed reference exemplars.
- `uv run python scripts/evals/run_evals.py` shows no regression.
