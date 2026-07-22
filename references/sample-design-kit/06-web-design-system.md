# 06 - Web Design System (how the VISEMI / Cất Cánh websites are built)

This is the **web-implementation** chapter of the design kit. Chapters `01`
(philosophy / feel) and `02` (exact brand values) are the shared brand
foundation and remain the single source of truth for palette, type, and logo.
This file adds the layer they do not cover: how that brand is expressed as
real web pages - CSS tokens, the page skeleton, component recipes with class
names, the motion system, the bilingual mechanism, and the engineering
conventions - so you can build new website pages that look and behave like the
two sites already shipped.

It synthesizes both live codebases (they share one brand; they differ in
tooling and maturity). Where they diverge, this doc names the preferred
convention for new work. Read `01` and `02` first for the "why"; this file is
the "how".

**Source codebases (path aliases used below):**

- `WEB` = `references/visemi/visemi-website/website-codebase/` - the main
  visemi.org site (Hugo + hugoplate + Tailwind v4). The broadest, most mature
  component and motion library.
- `HUB` = `programs/cat-canh-info-hub/` - the public Cất Cánh Handbook site
  (Hugo + hugoplate module). The cleanest token discipline and the mature
  bilingual system (EN default plus `/vi/` plus the `#en`/`#vn` handbook hash).

Both are read-only references here. Build new pages inside whichever repo owns
the page; follow that repo's stack (do not import the other's).

---

## 0. The one-line brief (from `01`)

> **Credible tech polish, mission-driven warmth.** Intel/Stripe-grade restraint
> (clean grids, generous white space, confident navy, sparing green energy)
> applied to a hopeful, human story about Vietnamese students taking off into
> global careers.

The web expression of that brief is five reflexes:

1. **Light by default, dark for impact.** Most surfaces are white or very light
   gray. The dark navy-to-purple gradient is reserved for feature moments: the
   hero, one stat band, the closing CTA. The contrast is the design.
2. **Structured, generous grids.** 3-up card rows, clear margins, fluid vertical
   rhythm with `clamp()`. Never crowd.
3. **Green is energy, not wallpaper.** Green marks momentum only (CTAs, active
   states, key figures, accent rules). Navy carries authority and structure.
   Green stays roughly 10-20% of any layout.
4. **One idea per surface.** Big headline, short support line, one visual or
   stat per section.
5. **Subtle motion, never gimmick.** Gentle fade-and-rise reveals, a soft glow
   behind a hero headline, numbers that count up. Everything gated by
   `prefers-reduced-motion`. Nothing spins or bounces.

---

## 1. Tokens (the web foundation)

All brand values live in exactly one file per repo and are consumed only as
`var(--...)`. **Never type a raw hex outside the token file.** On `WEB` the SSOT
is `data/theme.json` (compiled by `scripts/themeGenerator.js` into an `@theme`
block); on `HUB` it is `assets/css/tokens.css`. `02-brand-guidelines.md` is the
authority for the values themselves.

### 1.1 Color

**Core brand (identical across both sites):**

| Role | Hex | Notes |
|---|---|---|
| Brand navy (anchor / authority / headings) | `#001669` | The structural color. Footer band, headings on light, "The Gaps" side. |
| Body text (dark purple) | `#262538` | Default text color on light surfaces. |
| Brand green (energy / action) | `#01B68B` | CTAs, links, active states, key figures, "The Bridge" side, accent rules. |
| Green hover | `#019974` | Darker green for hover/pressed. |
| White | `#FFFFFF` | Primary background; text on dark. |
| Off-white surface | `#F6F6F6` | Alternate section background, hairline borders. |
| Border | `#EAEAEA` | Default hairline. |
| Muted text | `#717171` | Captions, metadata on light (AA at ~4.88:1 on white). |
| Accent cyan | `#00E5FF` | Tech sparkle ONLY: gradient-stripe end, hero-halo glow. Never text, never large fills. |

**Cất Cánh-hub-only status accent:** gold `#F5B433` (plus its muted-on-navy
pair). Used solely for the "upcoming" workshop status badge on `HUB`. It is not
part of the master brand in `02`; do not reach for it as a general accent.

**Ramps.** Use `02-brand-guidelines.md` as the canonical ramp reference (navy,
purple, green each with 100-900 tints; green hover `#019974`). On `WEB` these
exist twice: as Tailwind-generated `--color-primary-*` / `--color-blue-*` /
`--color-purple-*` (from `theme.json`) and as the semantic aliases
`--color-dark-blue-*` / `--color-green-*` / `--color-dark-purple-*` used
pervasively in the section CSS. On `HUB` only the base tokens plus the gradient
stops live in `tokens.css`. For a new page: reference the semantic tokens, and
if you need a tint that is not tokenized yet, add it to the token file (not
inline).

**Signature gradient (dark feature sections, heroes, CTA bands):**

```
linear-gradient(135deg, #000F4D 0%, #001669 50%, #1A1929 100%)
```

Optional bottom accent stripe: `linear-gradient(90deg, #01B68B, #00E5FF, #01B68B)`.
A common 2-stop hero variant is `linear-gradient(135deg, #001669 0%, #000C3D 100%)`;
either is on-brand. The extra stops `#000F4D`, `#1A1929`, `#000C3D` exist only
inside these gradients.

**Glass / scrim recipes (rgba, appear only in effect layers):**

| Use | Value |
|---|---|
| Scrolled header frost | `rgba(255,255,255,0.65)` + `backdrop-filter: saturate(160%) blur(18px)`; opaque `0.92` fallback |
| Header border / shadow | `rgba(0,22,105,0.08)` / `0 4px 20px rgba(0,22,105,0.06)` |
| Modal backdrop (all modals) | `rgba(0,15,74,0.72)` + `blur(6px)` |
| Dark-glass card (on dark) | bg `rgba(255,255,255,0.04-0.06)`, border `rgba(255,255,255,0.10-0.12)`, `blur(8-10px)` |
| Hero photo scrim | vertical navy `rgba(0,22,105,0.85)` to `rgba(0,9,50,0.92)`, plus radial green `rgba(1,182,139,0.22)` at ~15% 25% and steel `rgba(77,98,153,0.25)` at ~85% 75% |
| Eyebrow pill (glass) | bg `rgba(1,182,139,0.10-0.18)`, border `rgba(1,182,139,0.35-0.40)` |
| Card hover shadow | `0 14px 34px rgba(0,22,105,0.12)` |

**Usage rules:** light surfaces are the default; green is roughly 10-20% of any
layout; body text stays >= 4.5:1 (WCAG AA); white or `#CCF2E7`-light text on dark
gradients, navy/purple on light; `#717171` for captions.

### 1.2 Typography

**Be Vietnam Pro for everything** (chosen for full Vietnamese diacritic support).
Fallback stack: `"Be Vietnam Pro", Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
Weights 400 / 500 / 600 / 700. Base 16px, modular scale ratio 1.25.

Weight roles: 500 = nav links; 600 = buttons, eyebrows, language toggle; 700 =
headings, card titles, big figures.

**Fluid heading sizes (the web idiom - use `clamp()`):**

| Element | Size | Extras |
|---|---|---|
| Hero H1 (home) | `clamp(2.25rem, 1.25rem + 4vw, 3.75rem)` | `line-height: 1.1; letter-spacing: -0.02em` |
| Hero H1 (interior / banner) | `clamp(2.25rem, 5.2vw, 4rem)` | same |
| Display 2xl (cover numbers) | `4.768rem` desktop / `3.2rem` mobile | `line-height: 1.1; letter-spacing: -0.02em` |
| Section heading | `1.5rem` (or `clamp(2rem, 4.5vw, 3.5rem)` for a big section title) | |
| Card title | `1.35rem` | 700, navy |
| Eyebrow / kicker | `0.8125-0.875rem` | UPPERCASE, `letter-spacing: 0.12em`, weight 600, green |
| Body | `1rem`, `line-height: 1.6-1.72` | measure ~40-70 chars (`52-56rem` / `~56ch` cap) |

The `02` display scale (Display 2xl ~76 down to Text xs ~12) maps onto these;
on the web, prefer the `clamp()` recipes so type is fluid. Big stat figures use
`font-variant-numeric: tabular-nums`, weight 800, `letter-spacing: -0.03em`.

Rules: hierarchy by size and weight, not color; keep most text navy/purple and
use green only for emphasis words; never below 12px.

### 1.3 Space, radius, shadow, z-index, breakpoints

**Vertical rhythm** is fluid `clamp()`: sections `clamp(2.5rem, 4.5vw, 3.75rem)`
to `clamp(4rem, 8vw, 7rem)` top/bottom; heroes `7-9rem` top (to clear the fixed
header) and `4-6rem` bottom.

**Radius tiers:**

| Use | Radius |
|---|---|
| Buttons, pills, chips, status badges | `9999px` |
| Small icon badges | `8-16px` |
| Cards | `12px` (tech) / `16-20px` (feature) |
| Large cards, panels, modals | `24px` |
| Impact / ambassador panels | `28px` |

**Shadows** are soft, navy-tinted, large-offset "lift" shadows (never hard/gray):

- Card resting: `0 2px 12px rgba(0,22,105,0.04-0.05)`
- Card hover: `0 16px 40px rgba(0,22,105,0.10-0.12)`
- Panel drop: `0 30px 70px -32px rgba(0,22,105,0.55)`
- Modal: `0 40px 80px -20px rgba(0,0,0,0.45)`
- Green CTA glow: `0 10px 30px -10px rgba(1,182,139,0.6)`

**Z-index** is deliberately shallow and local. Heroes layer with negative z
(`-2` bg image, `-1` scrim, content on top) under `isolation: isolate`. The
fixed header sits at the top of the stack (`WEB` uses `position: fixed`; `HUB`
uses `z-index: 30`).

**Content measure / container:** panels and grids cap around `1040-1260px`;
prose and lead text cap `52-56rem`; single cards `860-880px`; hero copy
`640-720px`. Use the theme `.container` for page width. `WEB` exposes one global
layout token `--site-header-height: 4.5rem`.

**Breakpoints:** there is no single scale; section CSS uses bespoke `max-width`
stops. The load-bearing ones: `640px` (mobile), `768px` (tablet / footer
collapse), `900px` (grids drop to 1-up), `1024px`, `1100px`, `1280px`. Design
mobile-first-safe: 3-up grids collapse to 1-up by `900px`, 4-up steps 4 -> 2 ->
1 at `1100px` then `640px`.

### 1.4 Accessibility baseline (a convention, not an option)

- Minimum touch target `44x44px` for nav, social, and coarse-pointer links.
- `focus-visible` outline `2-3px solid var(--color-green)` with `2px` offset on
  every interactive element.
- `.sr-only` utility for screen-reader-only labels.
- Every motion block ends with `@media (prefers-reduced-motion: reduce)` that
  zeroes transitions and shows the final state.
- Target Lighthouse a11y >= 0.9.

---

## 2. Page anatomy (the reusable skeleton)

Every page follows the same top-to-bottom rhythm:

**Fixed glass header -> full-bleed dark hero -> alternating light/tinted feature
sections -> one dark impact or CTA panel -> dark navy footer.**

- The theme `baseof.html` supplies the header and footer; a page template just
  defines `main`. Wrap page body in `{{ define "main" }} ... {{ end }}`.
- `main` gets `padding-top` equal to the header height; a hero-first page pulls
  its hero up under the transparent header with a negative top margin (an
  explicit allowlist of hero classes on `WEB`).
- Alternate section backgrounds white `#FFFFFF` <-> tinted `#F7F8FB` /
  `#F4F6FB` / `#FBFBFD` for adjacent light sections. Hero-adjacent sections may
  carry a faint radial-glow or dot/grid overlay; dark feature sections use a
  masked tech-grid overlay (`background-size: 56px 56px`) with a radial mask.

### 2.1 The hero (most reused device)

Recipe: `position: relative; isolation: isolate; overflow: hidden`, signature
navy gradient base, optional cover photo at `opacity 0.82-0.95` with
`filter: saturate(1.08) contrast(1.1)`, a gradient scrim `::after`, and radial
brand glows via `::before`. Inside a centered `.container`: eyebrow pill ->
H1 (with an optional green accent span carrying `text-shadow: 0 0 24px rgba(1,182,139,0.45)`)
-> lead paragraph (optionally in a translucent glass "copybox") -> a wrapping
row of pill buttons.

### 2.2 Grid patterns

| Pattern | Columns | Collapse |
|---|---|---|
| Feature 3-up | `repeat(3, 1fr); gap: 1.5rem; max-width: 1100px` | 1fr at `<=900px` |
| Pillars / advisors 4-up | `repeat(4, 1fr)` | 2-up at `<=1100px`, 1fr at `<=640px` |
| Auto-fit cards | `repeat(auto-fit, minmax(320px, 1fr))` | natural |
| Gallery (HUB) | `repeat(2, minmax(0,1fr)); gap: 1.75rem` | 1-up at `<=900px` |
| Split with sticky rail | `minmax(0,1fr) 330px`, rail `position: sticky; top: 6rem` | stack |

---

## 3. Component recipes (class names + treatment)

Reuse these before inventing anything. Class names are the ones already in the
codebases; keep the BEM-ish kebab-case naming (`block`, `block__element`,
`block--modifier`).

### 3.1 Buttons (pill system)

All buttons are pills (`border-radius: 9999px`, `padding: ~0.625rem 1.5rem`,
weight 600, `~0.2s ease`). Variants:

| Class (WEB / HUB) | Treatment | Where |
|---|---|---|
| `.btn-primary` / `.btn--primary` | Filled green, white text, soft green shadow; hover `#019974` + `translateY(-1px)` | Primary CTA |
| `.btn-outline-primary` / `.btn--outline-navy` | Navy border+text; hover fills navy | Secondary on light |
| `.btn-outline-green` / `.btn--outline-green` | Green border+text; hover fills green | Secondary on light |
| `.btn-white` | White fill, navy text | On dark bg |
| `.btn-ghost-light` / `.btn--outline-light` / `.btn--ghost` | Transparent, `2px rgba(255,255,255,0.35-0.40)` border, white; hover soft white fill | On dark photo heroes |

CTAs are `inline-flex; align-items: center; gap: 0.5rem` with an SVG that nudges
`translateX(3px)` on hover.

### 3.2 Eyebrow / kicker

`.eyebrow` / `.heading-eyebrow`: inline-block, UPPERCASE, `letter-spacing: 0.12em`,
weight 600, green (`--color-primary-400`; on dark use `--color-primary-200`),
`~0.8125rem`. The fastest way to add brand polish above a heading. A glass-pill
variant (`.hero__eyebrow`) is used inside heroes.

### 3.3 Cards

The dominant feature card: white, `1px rgba(0,22,105,0.08)` border, radius
`16-20px`, resting shadow `0 2px 12px rgba(0,22,105,0.04)`, transition `~240ms
ease`; on hover `translateY(-4px)` + border shifts to `rgba(1,182,139,0.3)` +
shadow deepens. Common embellishments:

- **Top accent bar:** `::before` `height: 4px`, `linear-gradient(90deg, #01b68b, transparent)` at the card top.
- **Left accent bar:** `4px` vertical green-to-transparent gradient (story cards).
- **Dark variant:** translucent frosted glass on dark sections.
- Base classes: `.card-tech` (`WEB`, radius 12px) and `.card` / `.gallery-card`
  (feature/gallery).

### 3.4 Stat tiles / bands

Big figure (green or navy), short label, thin accent rule. Figure
`clamp(2.5rem, 5vw, 3.5-4rem)`, weight 800, `tabular-nums`, optional
`decimal-leading-zero` index via `::after`. On dark impact panels the tile is
`rgba(255,255,255,0.06)` glass. Numbers come from the brief, never hardcoded.

### 3.5 Glass header (signature)

Fixed bar, two cross-faded states (`~300ms`):

- **Top:** fully transparent bg + transparent border + no shadow, white logo and
  nav (sits over the dark hero).
- **Scrolled** (`.is-scrolled`, toggled past ~60px by an rAF-throttled scroll
  listener in `header.html`): `rgba(255,255,255,0.65)` + `saturate(160%) blur(18px)`,
  navy logo and nav, faint navy border, soft shadow. `@supports not
  (backdrop-filter)` falls back to opaque white `0.92`.

Logo swaps between a white mark (`logo-darkmode.png`, shown at top) and the color
mark (`logo.png`, shown scrolled) via `.header-logo--light` / `.header-logo--dark`.
Nav links: white/500 over the hero, navy when scrolled, green on hover/active.

### 3.6 Modals (native `<dialog>`, one shared recipe)

Reset dialog chrome; `[open] { display: flex; }` centered; `::backdrop`
`rgba(0,15,74,0.72)` + `blur(6px)`. Card `width: min(720-1200px, 100%)`,
`max-height: min(90-92vh, ...)`, radius `24px`, shadow `0 40px 80px -20px
rgba(0,0,0,0.45)`, entrance `translateY(16px) scale(0.97 -> 1)` over
`~0.32-0.42s cubic-bezier(0.2,0.8,0.2,1)`. Close button `44x44` pill, hover
`rotate(90deg)`. Lock scroll with `body.has-modal-open { overflow: hidden }`.
Full-screen (radius 0) on mobile. Prefer `<dialog>` over any JS lightbox
library (the sites dropped Swiper/glightbox for it).

### 3.7 Other cataloged devices (reach for these before building new)

- **CTA band:** signature-gradient section, radius `1.5rem`, `3rem 2rem`,
  centered white headline + one pill button.
- **Timelines:** horizontal connector line with gradient-filled circular
  markers (reverts to a vertical left-rail at `<=768px`); or a sticky vertical
  rail whose connector `scaleY(0 -> 1)` on reveal, with a final pulsing node.
- **Partner logo marquee:** pure-CSS infinite scroll (two duplicated sets,
  `translate(-50%)`), pauses on hover/focus-within, edge-fade masks, logos
  `grayscale(40%) opacity 0.85` -> full color on hover; reduced-motion shows a
  static grid. Normalize logos to a common box (e.g. 480x200).
- **Countdown:** gradient card, digit segments with `tabular-nums`, green colon
  dividers, uppercase labels, a pulsing LIVE badge when live.
- **Icon badges:** rounded-square chips `48-72px`, radius `12-18px`, bg
  `rgba(1,182,139,0.08-0.14)`, green line icon.

---

## 4. Motion system

**Philosophy:** subtle, brand-tinted, non-blocking. No animation library. An
`IntersectionObserver` (`scroll-reveal.js`, threshold ~0.12, rootMargin
`0px 0px -40px 0px`) toggles `.is-visible` / `.fade-up` on scroll. Shared
primitives live in `motion-utils.js` (`WEB`); per-page motion CSS/JS builds on
them.

**Core reveal `.fade-up`:** `opacity: 0; translateY(20px)` -> visible over
`0.6s ease-out`, `will-change: opacity, transform`.

**Easing tokens (keep consistent):**

- Soft decel (default): `cubic-bezier(0.22, 0.61, 0.36, 1)`
- Overshoot (for count-ups / pop): `cubic-bezier(0.34, 1.56, 0.64, 1)`

**Signature animations (use sparingly, for hero/feature moments only):**

- **Headline word-rise:** JS splits the H1 into `.word` spans; each rises from
  `translateY(24px) + blur(6px)` with `delay = index * 80ms + 180ms` over `0.85s`.
- **Accent rule-grow:** an underline `scaleX(0 -> 1)` over `1.2s`, green-to-cyan.
- **Drifting hero orbs / breathing grid:** two gradient orbs on
  `22s / 28s ease-in-out infinite alternate`; a soft `6s` halo pulse.
- **Count-up numerals:** on reveal, figures rise and count up (JS parses ranges
  like "1.8K-4K", "7x-20x").
- **CTA shimmer sweep:** a diagonal white gradient `::after` sweeps `-120% ->
  120%` on hover over `~0.85s`.
- **Card hover vocabulary (universal):** `translateY(-3px to -6px)` + deepened
  navy/green shadow + border shift to green; inner images `scale(1.03-1.06)`;
  arrows nudge `translateX(2-4px)`; durations `0.2-0.45s`.

**Non-negotiable:** every animated element degrades under
`prefers-reduced-motion: reduce`. Motion is polish, never a prerequisite for
reading the page.

---

## 5. Bilingual system

The sites take two different approaches. For **any new bilingual page, prefer
the HUB model** - it is the mature, correct one.

**HUB model (recommended):**

- Two languages configured with EN default at `/` and VI at `/vi/`
  (`defaultContentLanguage = 'en'`, `defaultContentLanguageInSubdir = false`).
- Four translation layers, each with one home:
  1. **UI strings** in `i18n/en.yaml` / `i18n/vi.yaml`, looked up with `T "key"`.
     Templates never hardcode display strings.
  2. **Page body** in per-language `content/` front-matter and markdown.
  3. **Menus** in per-language `menus.en.toml` / `menus.vi.toml`.
  4. **Data-driven titles** carry both fields (e.g. `title_en` + `title_vi`);
     the template picks by current language.
- **Site-to-handbook hash coupling:** links append `#en` (default) or `#vn`; the
  target page reads `location.hash` and the hash beats a stored
  `localStorage` preference. Note the intentional quirk: the URL/lang code is
  `vi` but the handbook hash is `#vn`.
- Language toggle renders the current language as a bracketed non-link
  (`[EN]`) and the other as a link (`[VI]`).

**WEB model (current reality):** an EN-only build; Vietnamese appears inline
inside English content and full `vi` scaffolding is aspirational. Do not scaffold
a `vi` tree on `WEB` without asking. If a new `WEB` page must be bilingual, port
the HUB i18n approach rather than inventing a third scheme.

Voice and diacritics: see `03-voice-and-copy.md`. The program name is always
**Cất Cánh** with full diacritics ("(Takeoff)" on first English mention);
"VISEMI Foundation" is never translated.

---

## 6. Engineering conventions

- **Token discipline (iron law).** No hex outside the token file. Extend by
  adding a token, never an inline literal. On `WEB` edit `data/theme.json`
  (then the generator runs); on `HUB` edit `assets/css/tokens.css`.
- **DRY / single source of truth.** Any fact, URL, or label used in 2+ places
  lives in one data file (`data/*.toml`, `data/*.json`) and is referenced from
  templates. Editing a value must never require touching a template. Absence of
  a field can encode state (HUB: no `youtube_id` renders an "upcoming" card).
- **Content vs. presentation.** Facts in `data/`, UI strings in `i18n/`, body
  copy in `content/`, layout in templates, brand in the token file. Keep them
  separated.
- **Do not edit the theme.** Both sites vendor hugoplate; override in
  `assets/css/` and `layouts/`, never in `themes/`. On `HUB`, do not restyle
  theme components (accordions/tabs/modals) that are not on the page. On `WEB`,
  do not reorder the `custom.css` `@import`s without checking specificity, and
  do not consolidate the dual partial trees (`layouts/_partials/` overrides vs
  `layouts/partials/` project).
- **Do not hand-edit built artifacts.** `HUB` serves the four handbooks verbatim
  from `static/handbooks/<slug>/`; they are copied from the workspace's
  `generate-handbook` output. Re-copy, never edit in place.
- **CSS file layout.** `WEB`: one file per page under `assets/css/sections/`,
  all `@import`ed into `custom.css` (with `tech-theme.css` first so its
  utilities are available downstream). `HUB`: a single `custom.css` override
  layer plus `tokens.css`. For a new page, follow the host repo's pattern (add a
  `sections/<page>.css` on `WEB`; extend `custom.css` on `HUB`).
- **Fonts.** Be Vietnam Pro, loaded via Google Fonts, async with
  `display=optional` (weights 400/500/600/700).
- **Logo and OG.** Color logo (`logo.png`) on light, white logo
  (`logo-darkmode.png`) on dark/photo. Alt text "VISEMI Foundation". Keep clear
  space >= the diamond mark; wordmark >= ~120px wide. `WEB` keeps a gate-enforced
  1200x630 `og-image.png`.
- **Deploy.** Push to the deploy branch triggers a GitHub Actions build (Hugo
  Extended, `--gc --minify`) to GitHub Pages. On `WEB`, branch from `develop` as
  `<task-type>/<topic>` and run the deploy-readiness gate before any PR to
  `main`. On `HUB`, pushing `main` deploys.

---

## 7. When the two sites diverge, do this

You chose to synthesize both. Here is the decision table for new pages.

| Concern | WEB (visemi.org) | HUB (info-hub) | Do for a new page |
|---|---|---|---|
| Token SSOT | `data/theme.json` -> generated `@theme` + semantic aliases in `custom.css` | `tokens.css` (hex + font) + `custom.css` overrides | Keep one token file as SSOT in the host repo; never hardcode hex. |
| CSS framework | Tailwind v4 via Hugo Pipes | hugoplate defaults + `custom.css` | Follow the host repo's stack; do not introduce a new one. |
| Bilingual | EN-only, `vi` inline/aspirational | True EN-default + `/vi/` + i18n + per-lang menus + `#en/#vn` | Use the HUB model for anything bilingual. |
| Section CSS | Per-page file in `sections/*`, `@import`ed | Single `custom.css` | Match the host repo. |
| Motion | Rich per-page (word-rise, orbs, count-ups) | Header scroll + basic reveals | Start with `.fade-up` + glass header; add signature motion only for hero/feature moments. |
| Radius | Full tier (12 / 16-20 / 24 / 28 + pills) | 16px cards + pills | Use the tiered scale: cards 16-20, panels/modals 24-28, buttons pills. |
| Gold accent | Not present | `#F5B433` status only | Gold is a HUB status color only, not a general brand accent. |
| Component depth | Broad (modals, timelines, marquee, countdown, stat bands) | Lean (hero, gallery cards, glass header, footer) | Borrow the richer WEB recipes; they are the fuller library. |

**Rule of thumb:** brand values, palette, type, glass header, hero treatment,
pill buttons, card lift, and reduced-motion reveals are shared and canonical -
use them everywhere. Tooling, CSS-file layout, and bilingual scaffolding follow
the repo the page lives in. Prefer the WEB component library for richness and
the HUB conventions for token discipline and bilingual correctness.

---

## 8. Build-a-new-page checklist

1. **Confirm the brief.** Page purpose, audience, language(s), the facts you are
   given (never invent numbers/dates/names; put shared facts in `data/`).
2. **Pick the repo and stack.** Build in the repo that owns the page; follow its
   token file, CSS layout, and (if bilingual) the HUB i18n approach.
3. **Lay the skeleton.** `{{ define "main" }}`: dark hero -> alternating
   light/tinted feature sections -> one dark impact/CTA panel -> footer (header
   and footer come from the theme).
4. **Compose from existing recipes.** Eyebrow pill, `clamp()` H1 with a green
   accent span, `.container` width, feature cards (top green accent, hover
   lift), pill buttons, stat tiles, CTA band. Reach for a cataloged device
   (timeline, marquee, modal, countdown) before writing a new one.
5. **Color by intent.** Navy structure, green ~10-20% on momentum only, cyan a
   whisper. Light by default; the dark gradient for one or two impact moments.
6. **Add motion last, gently.** `.fade-up` reveals on sections; word-rise or
   count-ups only on the hero or a stat band; wire the reduced-motion block.
7. **Check the baseline.** 44x44 targets, green focus rings, AA contrast,
   grids collapse cleanly at 900/768/640, no horizontal overflow at 390px, no
   console errors.
8. **Verify against the brand.** Be Vietnam Pro throughout, no off-brand hex, no
   emojis, no em/en dashes in copy, full Vietnamese diacritics, "Cất Cánh" and
   "VISEMI Foundation" spelled correctly, logo variant matches the background.

---

*This chapter mirrors the two live codebases as of its last edit. If either
site's tokens change (`WEB data/theme.json`, `HUB assets/css/tokens.css`),
refresh sections 1 and 7 here, and refresh `02-brand-guidelines.md` if the
brand values themselves move.*
