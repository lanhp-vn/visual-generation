---
name: author-brand
description: Derive a working repo's brand/ override for the visual-generation studio - palette as named token roles, type scale, fonts, logos, and icons - from a brand brief or reference material, then verify it by rendering. Use when a working repo needs a NON-VISEMI theme, when visgen-setup Step 2 says a brand override is needed, when the operator says "set up our brand", "add our colors and fonts", "make it use our branding", or when a render looks off-brand because tokens.json still carries another brand's values. Produces tokens.json plus the fonts/, logos/, and icons/ assets, and confirms brand-lint palette closure. Does not invent brand facts; asks when the brief is silent.
---

# author-brand

Fills a working repo's `brand/` override so every generator in the studio renders
in that repo's brand instead of the VISEMI default. This is the creative half of
what `visgen-setup` Step 2 used to hand-wave: `visgen-setup` does the plumbing
(project branch, `output/` gitignore, plugin enable), this decides the theme.

Run once per working repo. A VISEMI repo (e.g. cat-canh) does not need this at
all: omit `--brand` and the studio default is used.

## The one rule that governs everything here

**Token KEY NAMES are the template contract. A new brand re-values keys; it never
renames or drops them.**

The Jinja2 templates and CSS reference brand token names directly, not just
semantic roles: `var(--navy)`, `var(--green)`, `var(--purple)`, `var(--gold-fill)`,
`var(--green-deep)`, `var(--navy-100)`, `var(--caption)`, `var(--line)` and so on.
If your brand has no navy, `--navy` must still exist, carrying whatever your
deepest brand ink is. Drop a key and every template that uses it renders with an
invalid value and no error.

So the workflow is always: **copy the studio's `tokens.json`, then re-value every
entry in place.** Never author one from scratch.

```bash
SUB="visual-generation"          # submodule path
mkdir -p brand && cp -r "$SUB"/brand/* brand/
```

## Step 1 - Infer the brand strategy before touching a hex

Read the brief, existing site, deck, or logo files the operator supplies. Write
down, in one line each:

- **Category** and what the organization actually does
- **Audience** and what they need to feel to act
- **Emotional promise** in three adjectives
- **Trust level** required (clinical and regulated reads very differently from
  consumer and playful)
- **What the brand must avoid** - the adjacent look it must not be mistaken for

Facts come from the operator. If the brief is silent on something that changes a
color or a font, ask one focused question rather than inventing a brand.

## Step 2 - Palette as named roles, not swatches

For every color, record three things: **descriptive name**, **hex**, and
**functional role**. A palette without roles cannot be linted or reasoned about.

Map onto the semantic contract that already exists in `tokens.json`:

| Role keys | What they carry |
| --- | --- |
| `--bg`, `--bg-soft`, `--surface`, `--surface-2` | page and panel grounds |
| `--text-1`, `--text-2`, `--text-3` | primary, secondary, muted ink |
| `--accent`, `--accent-2`, `--accent-3` | the brand's action and emphasis tiers |
| `--border`, `--border-strong` | hairlines and defined edges |
| `--good`, `--warn`, `--bad` | functional status only, never decoration |
| `--grad`, `--grad-soft`, `--grad-feature` | brand gradients, or flat fills if the brand is flat |
| `--radius`, `--radius-sm`, `--radius-lg` | one corner-radius system |

Then re-value the brand-private aliases and ramps in the same file (`--navy`,
`--purple`, `--green`, ramp steps like `--navy-100`, `--green-800`) to your
brand's equivalents, keeping the key names per the rule above.

Constraints worth keeping from the reference material: one consistent gray
family, no pure `#000000` as a ground, and status colors reserved for meaning.

**Divergence from the vendored `stitch-skill`, on purpose:** it mandates a single
accent color. This token contract deliberately carries `--accent`, `--accent-2`,
`--accent-3` plus a gold, because the generators use accent tiers to build
hierarchy across dense layouts. Do not collapse them to one.

## Step 3 - Type

- **One family**, four weights (400/500/600/700). The generators use weight for
  hierarchy, so a family shipping only 400 and 700 will flatten every layout.
- Keep the existing `type_scale` unless the brand has a real reason to change it;
  it is tuned to the fixed canvas sizes and A4.
- Body measure around 65 characters; negative tracking on display sizes.
- If the brand serves a language with diacritics, the font **must** ship that
  subset. This is not cosmetic: stripped diacritics fail brand-lint.

Set `font_stack` and both `--font-sans` and `--font-display`.

## Step 4 - Assets

Into the working repo's `brand/`:

- `fonts/` - woff2, one file per weight, per subset (latin plus any language
  subset), and wire them in `fonts.css`
- `logos/` - a color mark, a white/reversed mark, and a square mark for tight
  slots. The engine resolves the color and reversed marks through the top-level
  `logos` group in `tokens.json`. It defaults to
  `logos/visemi-logo-color.svg` and `logos/visemi-logo-white.svg`; a brand using
  its own filenames declares them there:
  `"logos": { "color": "logos/acme-logo.svg", "white": "logos/acme-logo-white.svg" }`
- `icons/` - monoline SVG, one concept per file, matching the set of names already
  in the studio's `brand/icons/` that templates reference

When the operator has no assets to hand, the vendored link index at
`references/design-inspiration/design-resources-for-developers/readme.md` is the
sourcing starting point: Fonts, Colors, Icons, and Logos sections. Check the
license on anything you pull, and never ship a placeholder logo as if it were the
brand's.

## Step 5 - Write the brand's own anti-patterns

Record, in the working repo (its `CLAUDE.md` or `brand/README.md`), the handful of
things this brand must never do: banned color combinations, the look it must not
be mistaken for, copy tics to avoid. The generators cannot infer these, and the
next session will not remember them.

## Step 6 - Verify by rendering

There is no separate token-build step: `tokens.css` is generated live from
`tokens.json` at render time and written to `<brand>/generated/`, and the
brand-lint palette allowlist is derived from the same file, so theme and lint
cannot drift apart.

Render an existing exemplar through the new brand and grade it:

```bash
VG="visual-generation"
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  "$VG/scripts/evals/references/pitch-deck.content.json" --format both \
  --out output/brand-check --brand brand
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/grade_brand.py" \
  output/brand-check --brand brand
```

Require `overflow: false` on every page and brand-lint `passed: true`, then Read
the PNGs. A palette that lints clean can still look wrong; contrast and ink
weight only show up in the render.

**Known open issue, not yours to fix here:** eight token names are referenced by
CSS but defined in no `tokens.json`, including the studio default. Do not chase
them while authoring a brand; they are recorded, with the options for fixing them,
under "Found, not fixed" in
`docs/superpowers/specs/2026-07-24-reference-harvest-design.md`.

## Anti-patterns

- Renaming or dropping a token key because the name does not fit your brand. The
  key is the template contract; re-value it instead.
- Authoring `tokens.json` from scratch rather than copying and re-valuing the
  studio's, which silently loses ramps and aliases the templates need.
- Inventing brand facts (a color the operator never approved, a font the brand
  does not own a license for) instead of asking.
- Collapsing the accent tiers to one color because a reference skill says so.
- Shipping a font without the diacritic subset the brand's language needs.
- Hardcoding any hex outside `brand/`. Content and templates carry no colors.
- Using `--good`, `--warn`, or `--bad` as decorative fills; they are functional.
- Declaring the brand done without rendering an exemplar through it and reading
  the PNGs.
