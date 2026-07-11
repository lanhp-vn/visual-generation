---
name: generate-slides
description: Build brand-locked HTML slides and one-pagers for the Cất Cánh (Takeoff) Fellowship from a structured content JSON, render them to pixel-exact 1920x1080 PNG and PDF via headless Chromium (Playwright), then grade them (deterministic brand-lint + optional LLM-judge rubric). Use whenever the operator wants a Cất Cánh / VISEMI slide deck, pitch deck, one-pager, info-session deck, event deck, or any "make slides / make a one-pager" task, even if they do not say "HTML". Content lives in JSON (facts from the brief, never invented); layout lives in a fixed Jinja2 template library; brand lives in one VISEMI theme (light or dark). Output is html-ppt-compatible. Local only - no Gmail, Drive, or Zoom.
---

# generate-slides

Produces VISEMI / Cất Cánh slides and one-pagers in the house brand: navy `#001669`, green `#01B68B` accent, gold `#F5B433` (sparing), Be Vietnam Pro, on a fixed 1920x1080 stage. It separates three concerns - **content** (a JSON file), **layout** (Jinja2 templates), **brand** (the VISEMI theme, light or dark) - so output is repeatable, gradeable, and on-brand.

> **Workspace note.** Templates are vendored under this skill
> (`skills/generate-slides/templates/`). Brand assets - fonts, logos,
> icons, tokens - are the single source of truth in `brand/` (`brand/tokens.json`
> generates both theme CSS files and the brand-lint palette). The render/grade
> machinery lives in `scripts/ops/` and `scripts/lib/visgen/`. The reference
> exemplars in `scripts/evals/references/` are the canonical examples - open their
> rendered output as visual references.

## Three rules that define this skill

1. **Facts from the brief; never invent.** Every number, date, name, and dollar
   amount in the content JSON must come from the operator's brief. If a fact is    missing, ask - do not guess or copy a stale figure from an old deck. (This is    the design-kit's golden rule: layout from the canon, content from the brief.)

2. **Brand is locked.** Only the VISEMI palette (navy, green, gold used sparingly,
   plus the defined token shades) and Be Vietnam Pro. No off-brand colors, no    other fonts, no em dashes, no en dashes, no emojis. Vietnamese keeps full    diacritics ("Cất Cánh", never "Cat Canh"); the program name is    "Cất Cánh (Takeoff) Fellowship". The deterministic brand-lint enforces this.

3. **Verify by rendering.** A slide is not done until it renders cleanly (no
   overflow) and you have eyeballed the PNG against the intent. CSS fidelity is    iterative against the live render.

## Workflow

### Step 1 - Author / confirm the content JSON

Write a content file (see `scripts/evals/references/*.content.json` for full examples). Shape:

```json
{ "meta": { "lang": "en", "audience": "fellows", "format": "deck-16x9",
            "theme": "light", "title": "..." },
  "pages": [ { "layout": "<layout>", "content": { ... } } ] }
```

- `format`: `deck-16x9` or `one-pager-landscape` (both render at 1920x1080).
- `theme`: `light` (default, omit it) or `dark`. The same layouts render under
  either theme. Never hardcode a hex in content; styling comes from the theme.
- `decor`: boolean, default `true` (the dot-grid plus green glow background).
  Set `false` for a plain background.
- `pages`: the content array key (`"slides"` is accepted as a legacy alias).
  `layout`: one of the 11 event layouts or 6 donor layouts (see "Layout library"
  below). Each layout's required fields are defined in   `scripts/lib/visgen/schema.py` (`LAYOUTS`); validation runs on render.
- Icons are semantic names from `scripts/lib/visgen/icons.py`: `globe`,
  `grad-cap`, `network`, `rocket`, `target`, `clipboard`, `presentation`,   `users`, `chip`, `message` / `chat`, `calendar`, `compass`, `flag`, plus the   donor-deck icons `alert`, `grad-cap-dollar`, `flywheel`. Use only these names.
- Inline emphasis in text fields: `<span class="hl">...</span>` (green),
  `<span class="gold">...</span>` (gold, sparingly), `<b>...</b>`, and   `<span class="muted">...</span>`. No other HTML or inline styles.

### Step 2 - Render

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/render_canvas.py CONTENT.json --format both --out output/<name>
```

Writes `output/<name>/{index.html, png/page-NN.png, pdf/<name>.pdf, render_report.json}`. The renderer reads `meta.theme` and inlines the matching theme CSS (light or dark), picks the theme-appropriate logo (color on light, white on dark), and pre-renders any `cta-qr` QR from its `url`. Check `render_report.json` shows `overflow: false` for every slide. `output/` is git-ignored; never commit rendered output.

### Step 3 - Grade

```bash
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_brand.py output/<name>          # deterministic
PYTHONIOENCODING=utf-8 uv run python scripts/ops/grade_rubric.py output/<name> --task TASK.json   # LLM judge (needs ANTHROPIC_API_KEY)
```

Brand-lint must pass (`"passed": true`). The rubric grader scores **brand / layout / content / polish** 0-5 per dimension with justifications (model `claude-opus-4-8`; "Unknown" allowed) - read them, don't trust the score blindly. For a full suite over the seed tasks plus every reference exemplar: `uv run python scripts/evals/run_evals.py` (reports pass@k / pass^k).

## Layout library

Layouts live in `templates/layouts/`, built from the macro library in `templates/components.html.j2` (decoration background, theme-aware logo, page number, cards, icon circles, avatars, stat cards, sparkles, and the donor-deck primitives). Output is html-ppt-compatible (`<div class="deck">` wrapping `<section class="slide">`) and uses the vendored `base.css` utilities, so it also opens as a navigable deck in a browser via the vendored `runtime.js`.

### Event layouts (light + dark capable)

Eleven general-purpose layouts for program events (kickoff, webinar, info session, team and mentor calls). Required `content` fields in parentheses; open the matching fixture in `scripts/evals/tasks/_fixtures/` for the full shape (each has a light and a `-dark` variant).

| Layout | Required fields | Use it for |
| --- | --- | --- |
| `hero` | `title` | Opening / closing title slide. Optional `eyebrow`, `kicker`, `date`, `sub`, `sub_gold`, `tagline`, `title_size`, `sparkles[]` (`{x,y,size,tone}`). |
| `stat-grid` | `title`, `stats` | A grid of 2 to 6 numbers. Each stat `{num, unit?, label}`. Optional `eyebrow`. |
| `agenda` | `title`, `items` | A numbered run of show. Each item `{text, sub?}`. Optional `eyebrow`. |
| `icon-cards` | `title`, `cards` | 2 to 4 reason / feature cards. Each card `{icon, heading, body?}`. Optional `eyebrow`, `pullquote`. |
| `people` | `title`, `people` | Speaker / team / mentor cards. Each person `{name, role, creds?[], photo?}`. |
| `timeline-phases` | `title`, `phases` | A multi-phase journey. Each phase `{tag, title, bullets[]` or `body, outcome?}`. Optional `notes[]`. |
| `columns` | `title`, `columns` | 2 to 4 parallel roles / ideas. Each column `{icon?, heading, body}`. Optional `spirit` strip. |
| `cta-qr` | `title`, `blocks`, `qr` | Closing call to action with a QR code. `blocks[]` is `{text, sub?}`; `qr` is `{url, caption?, label?}`. Optional `heading`, `footer`, `closing`. |
| `quote` | `quote` | A single large pull quote. Optional `attribution`, `eyebrow`. |
| `section-divider` | `title` | A section break. Optional `eyebrow`. |
| `freeform` | `blocks` | Escape hatch when no named layout fits (see below). |

### Donor / pitch layouts (original set)

Six bespoke layouts kept untouched for donor and pitch material; prefer the event layouts above for program events.

| Layout | Required fields |
| --- | --- |
| `title` | `title`, `subtitle_vi`, `subtitle_en`, `footer` |
| `gaps-bridge` | `title`, `gaps`, `bridge` |
| `pillars-tiers` | `title`, `pillars`, `tiers` |
| `impact-roi` | `title`, `stats`, `flow` |
| `donor-tiers` | `title`, `tiers`, `footer` |
| `one-pager-3col` | `header`, `gaps`, `bridge`, `impacts` |

## Themes (light default / dark)

Themes are assembled, not vendored as static files: `brand/fonts.css` (Be Vietnam Pro, base64-embeddable) plus `brand/tokens.json` (via `visgen.tokens`, generating the light or dark `:root` token block for `meta.theme`) plus this skill's `assets/components.css` (the shared helper classes, fully tokenized - no literal hex). Layouts and component macros reference CSS tokens only and never hardcode a hex, so one layout renders correctly under either theme. The renderer (`scripts/lib/visgen/html_render.py`) reads `meta.theme`, assembles the matching theme CSS (fonts base64-embedded so renders are offline-deterministic), and selects the logo by theme (color mark on light, white mark on dark). Set `meta.theme: "dark"` only when the operator asks for a dark deck.

## Decoration layer

`meta.decor` (default `true`) draws the brand decoration: a faint dot-grid, a soft green glow, and optional per-slide `sparkles` on `hero`. The decoration stays fully inside the 1920x1080 box (no negative offsets that would inflate `scrollHeight` and trip the overflow check). Set `meta.decor: false` for a plain background.

## Gold accent rule

Gold (`#F5B433` and its token shades) is a sanctioned brand color but is used **sparingly** - a single highlighted figure, a date, or one emphasis span per slide, not as a fill. Navy and green carry the deck; gold is the spark. Apply it with `<span class="gold">...</span>` or fields such as `hero.sub_gold`. The brand-lint allows the gold hexes but overuse is a polish problem the rubric grader will flag.

## Avatars (initials / photo)

The `people` layout renders each person through the avatar macro. When a person has a `photo` (a path or data URI), it shows the photo; otherwise it derives initials from `name` on a tinted token background. So a people slide works with no images at all - just `name`, `role`, and optional `creds[]`.

## QR codes (cta-qr + qr.py)

The `cta-qr` layout takes a `qr: {url, caption?, label?}`. On render, the engine calls `scripts/lib/visgen/qr.py` `qr_svg(url)` (backed by the `segno` dependency) to produce a responsive, self-contained SVG (navy modules, a `viewBox`, `width="100%" height="100%"`) and injects it into the slide's QR card. No external network call and no pre-generated asset file: the QR is built from the URL at render time. Any other slide carrying a `qr` field gets the same injection.

## Freeform escape hatch

When no named layout fits, use `freeform`: its `content.blocks` is a non-empty ordered list of typed blocks rendered in sequence, reusing the same component macros. Block types: `heading`, `paragraph`, `bullets`, `card-grid`, `stat-row`, `person-row`, `qr-card`, `image`, `spacer`. See `scripts/evals/tasks/_fixtures/freeform.content.json`. Reach for a named layout first; `freeform` is the deliberate exception, not the default.

## One-pager composition

The theme-aware logo is fixed in a top corner of every page, so on a dense `one-pager-landscape` the header band is the easy place to get an awkward result: a `heading` block whose eyebrow runs a decorative rule across the top will visually collide with that corner logo, and the collision reads as clutter rather than structure. The cleaner pattern the brand wants is a balanced top band - the logo in one corner and the page's identifying line (organization / date / "founded" meta) set as its own quiet element in the opposite corner or on the line below, never a full-width rule butting into the logo. Keep the headline and intro as a left-column hero, group supporting numbers as a compact card cluster rather than a full-width row, and reserve any horizontal rule for interior section breaks well clear of the logo. When the content is a header plus contrasting sections, prefer the `one-pager-3col` layout, which already encodes this structure, over improvising the whole page in `freeform`.

## Graders & exemplars

- **Brand-lint** (`scripts/ops/grade_brand.py`, logic in
  `scripts/lib/visgen/brand_lint.py`): deterministic. Allows the navy / green   house hexes and token shades, the sanctioned gold, and the dark-theme token   hexes; flags any other hex. Exempts vendored `<style>` / `<svg>`, the   decoration sparkles, and the `.qrbox` QR module SVG from the palette scan.   Still flags em / en dashes, off-brand fonts, the wrong page size, overflow, and   "Cat Canh" without diacritics.
- **Rubric grader** (`scripts/ops/grade_rubric.py`, rubrics in
  `scripts/evals/rubrics/{brand,layout,content,polish}.md`): one isolated LLM judge per   dimension over the rendered PNGs, 0-5 plus justification, "Unknown" allowed,   theme-agnostic (light or dark both acceptable). Model `claude-opus-4-8`; needs   `ANTHROPIC_API_KEY`.
- **Exemplars** in `scripts/evals/references/`: `kickoff.content.json` (light event deck)
  and `kickoff-dark.content.json` (the same content under the dark theme) are the   event references; `pitch-deck.content.json` and `one-pager.content.json` are the   donor references. The seed tasks `scripts/evals/tasks/event-{welcome,agenda,people,cta-qr}.json`   plus the donor `*.task.json` drive `scripts/evals/run_evals.py`, which also synthesizes a   task per reference so every exemplar is regression-covered.

## Ecosystem follow-on (decks beyond the exemplars)

For decks the layout library does not cover, reuse the vendored MIT toolkits rather than building every layout from scratch:

- **Layouts/themes:** `references/presentation-frameworks/html-ppt-skill` (31 layouts,
  animations) and `references/presentation-frameworks/beautiful-html-templates` (35 branded   templates) - apply the VISEMI theme (`brand/fonts.css` plus `brand/tokens.json` via   `visgen.tokens`, plus this skill's `assets/components.css`); `brand/tokens.json` is written   in html-ppt's token format, so it drops in directly.

Vendored MIT assets are attributed in `assets/THIRD_PARTY_LICENSES`.

## Anti-patterns

- Inventing or reusing a number/date/name not in the brief.
- Any off-brand color or non-Be-Vietnam-Pro font; em dashes, en dashes, or
  emojis; stripped Vietnamese diacritics.
- Hardcoding a hex or inline style in the content JSON, or in a layout template /
  component macro; styling lives in the theme tokens.
- Overusing gold as a fill instead of a sparing accent.
- Declaring a slide done without rendering it and checking `overflow: false`.
- Hand-editing `scripts/evals/references/*.content.json` figures (they are reference
  solutions / the regression suite) without re-verifying against the source.
- Committing anything under `output/` (git-ignored output).
- Reaching for reveal.js / slidev - rejected for this use (heavy runtimes, weak
  pixel-exact export).
