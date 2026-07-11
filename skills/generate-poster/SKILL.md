---
name: generate-poster
description: Build brand-locked VISEMI / Cất Cánh posters, event graphics, banners, and email headers from a structured content JSON, render them to pixel-exact PNG/PDF via headless Chromium, then grade them with the deterministic brand-lint. Use whenever the operator wants a poster, event graphic, flyer, wide banner, or email header image, even if they do not say HTML. Content lives in JSON (facts from the brief, never invented); layout is a fixed set of dense, hierarchy-first templates; brand lives in brand/tokens.json. Local only.
---

# generate-poster

Produces VISEMI / Cất Cánh posters, banners, and email headers in the house brand
(navy, green, gold, Be Vietnam Pro). Same engine, brand, and grader as
`generate-slides`; templates tuned for a print-style poster with a denser
information hierarchy (title, when/where, details, QR) than a social post. It
separates content (a JSON file), layout (the poster templates), and brand
(`brand/tokens.json`) so output is repeatable, gradeable, and on-brand.

> **Workspace note.** Templates are vendored under this skill
> (`skills/generate-poster/templates/`), built on the shared macro library.
> Brand assets (fonts, logos, icons, tokens) are the single source of truth in
> `brand/`. Render/grade machinery lives in `scripts/ops/` and
> `scripts/lib/visgen/`. The reference exemplar
> `scripts/evals/references/poster-event.content.json` is the canonical example.

## Sizes (meta.format)

| Format | Pixels | Use it for |
| --- | --- | --- |
| `poster-a` | 1240 x 1748 | Vertical event poster / flyer (A-series ratio) |
| `banner-wide` | 2048 x 1448 | Wide banner / cover image |
| `email-header` | 1200 x 400 | Email header strip (short and wide) |

## Writing rules

- **Hierarchy first.** A poster is scanned: one dominant title, then the
  essentials (when, where), then supporting detail. Keep detail lines short.
- **Facts from the brief, never invented.** Every date, time, place, and name
  comes from the operator's source. Ask when a fact is missing.
- **Brand is locked.** Be Vietnam Pro only; palette and rules live in
  `brand/tokens.json` and are enforced by the brand-lint. No hex or inline style
  in content; no emojis; no em or en dashes; full diacritics ("Cất Cánh").
- Inline emphasis in text fields: `<span class="hl">` (green),
  `<span class="gold">` (sparingly), `<b>`. Nothing else.

## Content shape

```json
{ "meta": { "format": "poster-a", "theme": "light", "title": "...", "lang": "vi" },
  "pages": [ { "layout": "<layout>", "content": { ... } } ] }
```

## Layout library

| Layout | Required | Optional | Use it for |
| --- | --- | --- | --- |
| `poster-event` | `title`, `when`, `where` | `eyebrow`, `details` (list of lines), `qr {url, caption?}`, `foot` | A full event poster (`poster-a`). |
| `banner-headline` | `headline` | `eyebrow`, `sub`, `cta`, `sparkles` | A wide banner / cover (`banner-wide`). |
| `email-header` | `headline` | `sub` | A short wide email header (`email-header`); text left, brand mark right. |

Required `content` fields are enforced by `scripts/lib/visgen/schema.py`
(`LAYOUTS`); `when`/`where` render with calendar/location icons; a QR SVG is
generated from `content.qr.url` when present.

## Step 1 - Render

```bash
# VG = plugin root; works standalone (CWD = studio) or from a working repo.
VG="${CLAUDE_SKILL_DIR}/../.."
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  CONTENT.json --format both --out output/<name> --brand brand \
  --skill-dir "$VG/skills/generate-poster"
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

- **No photo band on `poster-event`.** A `poster-a` (1240x1748) cannot stack a
  cover photo on top of a title, when/where, details, and a QR foot without
  overflowing (a photo band alone pushed it ~430px over). A photo poster needs
  an overlay design (text over the image), which this layout does not do, so
  `poster-event` intentionally has no `photo` field. Do not add one back.
- **Long titles/details.** The poster foot (brand line + QR) is anchored to the
  bottom, so an over-long title or too many detail lines push into it and
  overflow. Keep the title tight and details to a few short lines; the grader
  flags overflow.
- **Reintroducing the deck-sized QR.** The shared `.qrbox` is sized for a 1920
  deck; the poster CSS scales it down (`.slide.poster .qrbox`) to leave foot
  headroom. Do not hardcode it larger.
- **Off-brand content.** No hex or inline styles in the content JSON; no emojis;
  no em/en dashes; full diacritics ("Cất Cánh", never "Cat Canh"). The
  brand-lint enforces all of these.
