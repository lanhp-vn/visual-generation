---
name: generate-social-post
description: Build brand-locked VISEMI / Cất Cánh social posts (Instagram, Facebook, LinkedIn, story, feed graphic) from a structured content JSON, render them to pixel-exact PNG/PDF via headless Chromium, then grade them with the deterministic brand-lint. Use whenever the operator wants a social post, Instagram/Facebook/LinkedIn image, square/portrait/story graphic, announcement card, quote card, stat card, or any "make a post / feed graphic" task, even if they do not say HTML. Content lives in JSON (facts from the brief, never invented); layout is a fixed set of feed-legible templates; brand lives in brand/tokens.json. One message per canvas. Local only.
---

# generate-social-post

Produces VISEMI / Cất Cánh social posts in the house brand (navy, green, gold,
Be Vietnam Pro), one strong message per canvas, at feed sizes. Same engine, brand,
and grader as `generate-slides`; a different template set tuned for legibility in
a small feed thumbnail. It separates content (a JSON file), layout (the social
templates), and brand (`brand/tokens.json`) so output is repeatable, gradeable,
and on-brand.

> **Workspace note.** Templates are vendored under this skill
> (`skills/generate-social-post/templates/`), built on the shared macro library.
> Brand assets (fonts, logos, icons, tokens) are the single source of truth in
> `brand/`. Render/grade machinery lives in `scripts/ops/` and
> `scripts/lib/visgen/`. The reference exemplar
> `scripts/evals/references/social-square.content.json` is the canonical example.

## Sizes (meta.format)

| Format | Pixels | Use it for |
| --- | --- | --- |
| `square` | 1080 x 1080 | Instagram / Facebook feed post (default) |
| `portrait` | 1080 x 1350 | Instagram portrait (more vertical room) |
| `story` | 1080 x 1920 | Instagram / Facebook story, full-screen vertical |
| `link` | 1200 x 627 | Link-preview / LinkedIn shared image (wide) |

## Writing rules (feed legibility)

- **One message per canvas.** A post is read at thumbnail size; say one thing.
- **Big type, few words.** A headline is a phrase, not a sentence; a stat is one
  number. Trim ruthlessly rather than shrinking type. If it overflows, cut words.
- **Facts from the brief, never invented.** Every number, date, name, and place
  comes from the operator's source. Ask when a fact is missing.
- **Brand is locked.** Be Vietnam Pro only; palette and rules live in
  `brand/tokens.json` and are enforced by the brand-lint. No hex or inline style
  in content; no emojis; no em or en dashes; full diacritics ("Cất Cánh").
- Inline emphasis in text fields: `<span class="hl">` (green),
  `<span class="gold">` (sparingly), `<b>`. Nothing else.

## Content shape

```json
{ "meta": { "format": "square", "theme": "light", "title": "...", "lang": "en" },
  "pages": [ { "layout": "<layout>", "content": { ... } } ] }
```

`meta.theme`: `light` (default) or `dark`. `meta.decor`: dot-grid + glow
background, default `true`.

## Layout library

| Layout | Required | Optional | Use it for |
| --- | --- | --- | --- |
| `social-hero` | `headline` | `sub`, `cta`, `qr {url, caption?}`, `photo`, `foot`, `eyebrow` | The main announcement / hook. `photo` renders a cover image with a navy scrim, message bottom-left. |
| `social-quote` | `quote` | `attribution`, `photo`, `eyebrow` | A voice / testimonial card. |
| `social-stat` | `stat`, `label` | `unit`, `sub`, `foot`, `eyebrow` | One hero number (e.g. cohort size). |
| `social-announce` | `headline`, `detail` | `cta`, `qr`, `foot`, `eyebrow` | An announcement with a supporting line. |
| `social-cta` | `headline`, `cta` | `sub`, `qr {url, caption?}`, `foot`, `eyebrow` | A call to action, optionally with a QR. |

Required `content` fields are enforced by `scripts/lib/visgen/schema.py`
(`LAYOUTS`); a QR SVG is generated from `content.qr.url` when present.

## Step 1 - Render

```bash
# VG = plugin root; works standalone (CWD = studio) or from a working repo.
VG="${CLAUDE_SKILL_DIR}/../.."
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  CONTENT.json --format both --out output/<name> --brand brand \
  --skill-dir "$VG/skills/generate-social-post"
```

`CONTENT.json`, `--out`, and `--brand brand` resolve against the caller's current
directory; `--brand brand` uses the working repo's `brand/` (omit for the studio
default VISEMI theme). Output lands in the working repo's git-ignored `output/`.
Check `render_report.json` shows `overflow: false`.

## Step 2 - Grade

```bash
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/grade_brand.py" \
  output/<name> --brand brand
```

Brand-lint must pass (`"passed": true`): on-brand palette and fonts, no em/en
dashes, no emojis, correct page size, no overflow, full diacritics. Then open
`output/<name>/png/page-01.png` and confirm it matches the intent before
declaring it done. For the full regression suite: `uv run python
scripts/evals/run_evals.py`.

## Anti-patterns

- **Cramming a square.** `social-announce` and `social-cta` on a `square`
  (1080x1080) sit near the height ceiling once they carry a headline, a
  supporting line, a CTA, and a QR. Grow any of those (a long QR caption, a
  three-line sub) and the grader flags `overflow`. For a QR-forward post prefer
  `portrait` or `story` (taller), and keep the QR caption to one short line. One
  message per canvas is a size constraint, not just a style preference.
- **Reintroducing the deck-sized QR.** The shared `.qrbox` is sized for a 1920
  deck; the social CSS scales it down (`.slide.social .qrbox`). Do not hardcode
  a larger QR or a bigger caption back in - it will overflow the square.
- **Photo scrim via `color-mix()` with a CSS var.** The photo-hero scrim is a
  solid `var(--navy)` overlay at reduced `opacity`, on purpose: Chromium
  silently drops `color-mix(in srgb, var(--token) N%, transparent)`, which left
  white text on a bright photo. Also, `.social-photo` is deliberately excluded
  from the `.slide.evt >` child rule - that rule forces every child to
  `position:relative; z-index:2`, which collapses the full-bleed cover layer.
  Photo variants use the white logo for contrast on the navy scrim.
- **Off-brand content.** No hex or inline styles in the content JSON; no emojis;
  no em/en dashes; full diacritics ("Cất Cánh", never "Cat Canh"). The
  brand-lint enforces all of these - do not hand-wave it.
