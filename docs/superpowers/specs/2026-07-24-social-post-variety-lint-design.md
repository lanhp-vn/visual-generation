# Social-post variety lint - design

Approved 2026-07-24. Makes the anti-repetition and decoration-tell rules that
govern a *set* of social posts mechanically checkable, the same way
`brand_lint.py` makes the brand rules mechanically checkable.

## Why

`generate-social-post` is strong on brand compliance and silent on composition.
Five layouts, no rule against using one of them for every post in a campaign, no
count on eyebrows, no cap on headline length before a render is spent. A twelve
post campaign authored today can be fully brand-lint-clean and still read as one
post repeated twelve times.

The rules that fix this came from `taste-skill` (vendored 2026-07-24 at
`references/claude-design-galleries/taste-skill`, upstream
`github.com/leonxlnx/taste-skill` @ `e988add`, MIT). Adapted specifically:

- `skills/taste-skill/SKILL.md` §4.7 (eyebrow restraint, section-layout
  repetition ban), §4.9 (content density, sub-paragraph word caps), §4.10 (quote
  length), §9.F (numbered eyebrows, version labels, middle-dot rationing), §14
  (the principle that a taste rule only holds if the check is mechanical).
- `skills/imagegen-frontend-web/SKILL.md` §2 (variation across a set), §10
  (section rhythm).

A section in their model maps to a post in ours: both are one composition a
reader meets in sequence.

## What is NOT taken

Most of that upstream contradicts our locked brand, and none of it is imported:

| Upstream advice | Why rejected |
| --- | --- |
| Geist / Satoshi / serif rotation | Be Vietnam Pro only (`brand/tokens.json`) |
| Accent rotation, banned palettes, one-accent-per-page | Palette is locked in `brand/tokens.json` |
| `MOTION_INTENSITY` 6-8, GSAP scroll-hijack, magnetic physics | Static renders; elderly-first accessibility in the working repo's `brand/flat-design.md` |
| Glassmorphism, mesh gradients, liquid glass | "No gradients of any kind" (`brand/flat-design.md`) |
| Real photography mandatory, picsum.photos placeholders | "No photography anywhere for now" (`brand/flat-design.md`) |
| React / Next / Tailwind / Motion stack and code skeletons | This engine is HTML to headless Chromium |
| Filler-verb and copy-phrasing bans | Voice has an owner (`brand/voice-and-tone.md`) and a reviewer (the working repo's `copy-reviewer` agent). A word list hardcoded in a lint is a voice rule waiting to drift |

## Design

Three files, one new lint module, one new CLI, one skill doc update.

### `scripts/lib/visgen/variety_lint.py` (new)

Third lint module beside `brand_lint.py` and `doc_lint.py`, same contract:
violations are `{"code", "detail"}` dicts, the entry point returns
`{"passed": bool, "violations": [...]}`.

It lints the **authored content JSON**, not rendered HTML. Layout names,
eyebrows, and text lengths all live in the content, so the check runs before a
render is spent. Reuses `schema.document_pages()` for the legacy `slides` alias.

Scope guard: only pages whose `layout` starts with `social-` are considered. A
deck legitimately repeats `stat-grid`; a campaign of posts does not legitimately
repeat `social-hero`. A JSON with no social pages passes with zero violations.

A batch is the social pages of all input JSONs concatenated in argument order,
so a campaign authored as one JSON with N pages and one authored as N JSONs
grade identically.

Checks:

| Code | Fires when | Source |
| --- | --- | --- |
| `layout-repeat-adjacent` | two consecutive posts share a layout | §4.7 repetition ban |
| `layout-monotony` | for n >= 4 posts, distinct layouts < `min(5, ceil(n/2))` | §4.7 (>= 4 families per 8 sections), capped at the 5 layouts that exist |
| `eyebrow-overuse` | more than `ceil(n/3)` posts carry an `eyebrow` | §4.7 eyebrow restraint |
| `middot-spam` | more than one `·` in one text field | §9.F middle-dot rationing |
| `numbered-eyebrow` | eyebrow leads with a number, or `No.` / `Phase` / `Stage` / `Step` / `Part` plus a digit | §9.F section-numbering ban |
| `version-label` | `v1.2`, `BETA`, `ALPHA`, `EARLY ACCESS`, `INVITE-ONLY` in an eyebrow or headline | §9.F version-label ban |
| `<field>-too-long` | word count over cap: `headline` 8, `sub` 20, `detail` 20, `quote` 25 | §4.9 content density, §4.10 quote length |

The word caps come from one table, so the four `-too-long` codes are generated
rather than written four times. Counts are taken after stripping the inline
markup the content fields are allowed to carry (`<span class="hl">`, `<b>`).

Self-check: a `__main__` assert block, matching the existing `tokens.py`
precedent. visgen carries no test files; `scripts/evals/` is the heavier tier.

### `scripts/ops/grade_variety.py` (new)

Mirrors `grade_brand.py`: takes one or more content JSON paths, prints the result
as JSON, exits 1 when it fails. No `--brand` flag; nothing here reads brand
values, which is the point.

### `skills/generate-social-post/SKILL.md`

Gains the batch-variation rules and the new grade command as its own step. Rules
state the workflow and point at owners; no brand or voice value is restated.

## Boundaries

Nothing else changes. `render_canvas.py` is untouched: the loop stays render then
grade, with one more grade command available. `brand_lint.py` keeps sole
ownership of palette, fonts, dashes, emojis, diacritics, page size, and overflow.

## Deferred

New layouts (split, editorial, color-block), explicit hero-scale variants, and a
read-only design-review agent are a second pass, tracked in the working repo's
`TODO.md`. The real unlock for composition variety is the flat illustration
masters, not more type-only layouts.
