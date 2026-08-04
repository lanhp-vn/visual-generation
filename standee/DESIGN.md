# VISEMI Foundation roll-up standee - design spec

One print-ready design for a retractable roll-up banner, authored as
self-contained HTML and printed to PDF via headless Chrome, in **two vendor
sizes**: the original 36 x 72 in and an 80 x 200 cm sibling.

Decided with the operator 2026-07-31. Every fact and every line of copy on the
banner traces to a cited source; nothing is invented.

The folder began with three variations (`standee-a/b/c`): A sparse and dark, B
light and carrying partner logos, C dark and content-complete. Only C survived
review; A and B were deleted and C was renamed `visemi-standee`. The scripts no
longer carry a variant list - `build_standee.py` globs `*.src.html` and
`check_standee.py` targets one stem - because a hard-coded list of names that no
longer exist is just somewhere for names to go stale. Sections below that still
say "the design" mean the surviving C.

## Deliverable

| File | Role |
| ---- | ---- |
| `visemi-standee.src.html` | **Edit this.** The 36 x 72 in authoring source. Images are `__A(path)__` placeholders, so opening it directly shows broken images. |
| `visemi-standee-80x200.src.html` | **Edit this too.** The 80 x 200 cm sibling. Same design, same copy, same assets; different page box and vertical rhythm. See "Two sizes" below, including what has to be carried across when copy changes. |
| `build_standee.py` | **Run this.** Inlines every placeholder as a base64 data URI, for every `*.src.html` it finds. `--self-test` proves both resolve roots work. |
| `make_chip_band.py` | Bakes `assets/chip.svg` into **one JPEG per entry in its `BANDS` table** (`chip-band-baked.jpg` at 19.2 in for the master, `chip-band-baked-24in.jpg` at 24 in for the 80 x 200), with the edge fade composited into the pixels. One Chrome rasterisation serves every band; only the crop and encode are per band. Run from the **repo root** (`uv run python visual-generation/standee/make_chip_band.py`); Pillow is in the working repo's env, not the plugin's. Slow (~117 MP). Re-run only if `chip.svg`, a band height, `DPI`, or the field colour change. |
| `check_standee.py` | The acceptance gate, run over **every** source found. Runs every text assertion against extracted visible text with data URIs stripped, so base64 cannot produce phantom matches, and measures each built PDF's page box. A new size must register in its `PAGE_SIZES` / `PAGE_PT` tables. Run it under the **working repo's** env, not the plugin's, or the PDF measurement skips for want of `pypdfium2`. |
| `normalize_partners.py` | Rebuilds `assets/partners-norm/` from `assets/partners/`. Equalizes logo optical weight on `sqrt(w*h)`, because the raw logos fill wildly different fractions of an identical canvas. **Unused by the current design** - partner logos were cut - kept only for a future variation that wants them. |
| `visemi-standee*.html` | **Never edit.** Generated, self-contained, zero external requests. This is what goes to the print vendor. |
| `visemi-standee.pdf` | Print master, 1 page, exactly 36 x 72 in. |
| `visemi-standee-80x200.pdf` | Print master, 1 page, exactly 80 x 200 cm. |

## Physical format

- **36 x 72 in** (3 x 6 ft) and **80 x 200 cm**, both portrait, both
  `@page{...;margin:0}`.
- Author **in inches** throughout. Do not use `px` for layout; the print is
  physical and inch units keep the artifact dimensionally exact.
- `print-color-adjust: exact` (and the `-webkit-` prefix) on `html` **and**
  `body`, or Chrome drops every background fill.
- No bleed, no crop marks. Roll-up vendors want exact-size artwork.

## Two sizes

80 x 200 cm is a taller, narrower aspect than the master (0.40 vs 0.50), so it is
a sibling source rather than a re-scale of the PDF.

**How the size is reached.** The 80 x 200 body is authored in the **same 36 in
wide coordinate system** as the master and scaled down with `body{zoom:.875}`, so
every horizontal value, every font size and every line break is identical to the
reviewed design: nothing rewraps, and the `&shy;` tuning, the `nowrap` headline
and the justified measures all still hold. `zoom` is a **layout** scale, not a
paint transform, so type stays type and the chart stays vector in the PDF; a
`transform: scale()` here would risk rasterisation on Chrome's print path. The
authoring canvas is therefore 36 x 90 in, and 36 x .875 = 31.5 in = 80.01 cm, so
the body overflows the page by 0.1 mm and `html{overflow:hidden}` clips it.
Erring 0.1 mm **large** is deliberate: erring small leaves a white hairline down
the edge of a print master.

**Where the extra 18 authoring inches went.** Not proportionally: a flat vertical
stretch nearly triples the physical gap between the headline and its own lead
line, which detaches them. In priority order after operator review:

1. **Into the leading**, not the gaps. A taller banner earns looser lines; wider
   gaps only push blocks apart. Headline `1.08` to `1.16`, lead `1.55` to `1.72`,
   program copy `1.72` to `1.9`, why-statement `1.14` to `1.24`, explainer `1.75`
   to `1.95`. `line-height` does not affect line *breaking*, so every block still
   sets to the same line count and the `&shy;` tuning is untouched.
2. **Into the chip band**, which is **24 in** here against the master's 19.2 in
   and therefore starts 4.8 in higher up the banner. A band has to reach the
   bottom edge, so growing it is the only way to move the chip up: opening the
   crop higher in the source just adds empty field above the apex. It is its own
   bake (`chip-band-baked-24in.jpg`) from the same rasterisation, and it puts the
   apex ~3 in higher than the 19.2 in band did while showing more of the chip's
   base above the roller cassette. The explainer's last line still lands 48% into
   its 6.24 in top fade, the depth the master uses.
3. The section breaks, the top margin, the scan card, and the gap *between* the
   four program rows (1 in, up from .52 in), in that order and last.

**Two type sizes are raised beyond parity**, because at `.875` zoom the master's
values print 12.5% smaller than they were tuned to read at: the section heads
(`.5in` to `.64in`) and the eyebrow badge (`.52/.36in` to `.64/.46in`). The badge
is right-aligned in a 14 in box ending at x 33.4 in, so its longer line sets to
~12.5 in and still starts clear of the logo, which ends at x 14.6 in. Past about
`.66in` the two collide.

The scan card is the one place a taller canvas does not simply help. **The QR is
width-limited, not height-limited** - the card is 13 in wide - so the card's extra
5.8 in cannot buy a bigger code. It went into the two navy bands instead, which
are content (the arrow band at 8.8 in with SCAN at 1.45 in, the URL bar at 4 in
with the URL at 2.1 in, both reading further than the master's), keeping the white
body slack under 1 in a side. Spending it as white space around the code is the
dead-band failure an earlier revision was already sent back for.

**Duplication, accepted knowingly.** The two sources share ~350 lines of markup
and copy. That is the boring trade for two print masters at two physical sizes,
and `check_standee.py` asserts the required copy on both, so a divergence in what
matters fails the build. **When editing copy, edit both files** and carry the
`&shy;` hyphens across. If a third vendor size ever appears, that trade flips:
hoist the vertical positions into `:root` custom properties and have
`build_standee.py` emit one built file per registered format from a single source.

## The zone map (load-bearing - do not rearrange)

A roll-up base sits about 2 in off the floor, so on the 36 x 72 in master content
`Y` inches from the top sits at **`74 - Y` inches above the floor**. That governs
the whole layout:

| Y from top | Above floor | Zone |
| --- | --- | --- |
| 0 - 3.5 in | 70.5 - 74 in | Top margin. No content. |
| 3.5 - 12.5 in | 61.5 - 70.5 in | **Eye level.** Logo + eyebrow. |
| 14 - 31 in | 43 - 60 in | **Prime read zone.** Headline + supporting line. |
| 31 - 42 in | 32 - 43 in | **Waist height.** QR + URL. Nobody crouches to scan. |
| 42 - 64 in | 10 - 32 in | Low value. Decorative or secondary only. |
| 64 - 72 in | <= 10 in | **Dead.** The roller mechanism eats this. Background only. |

Rules that follow from it:
- The **QR must sit with its centre near Y 35 in**. Never at the bottom.
- **Nothing readable below Y 64 in.** Eight inches of dead zone, deliberately
  more than the 4 - 6 in vendors quote.
- Logo and headline both live in the top 31 in, in that reading order.

On 80 x 200 cm the banner's top edge is at 205 cm, so the arithmetic differs but
the targets do not, and the 80 x 200 layout was tuned to land in the same places:
headline at **158 - 178 cm** above the floor, QR centre at **107 cm** (the master
puts it at 98 cm), explainer bottom at 51 cm. Re-derive these, not the inch
numbers above, if that layout is ever moved.

## Typography and distance legibility

Rule of thumb: **1 in of cap height reads at about 10 ft.** Expo aisle viewing
distance is 15 - 25 ft, so the headline needs 2 in+ of cap height.

| Element | Size | Cap height | Reads at |
| --- | --- | --- | --- |
| Headline | `2.62in`, weight 700, `line-height:1.08`, uppercase, `letter-spacing:-.015em` | ~1.89 in | ~19 ft |
| Eyebrow badge | `.52in`, weight 700, uppercase, `letter-spacing:.13em` | ~0.37 in | ~3.7 ft |
| Lead | `.76in`, weight 500, justified | ~0.55 in | ~5.5 ft |
| `SCAN` | `1.15in`, weight 700 | ~0.83 in | ~8 ft |
| URL (`visemi.org`) | `1.5in`, weight 700 | ~1.08 in | ~11 ft |
| Program names | `.74in`, weight 600 | ~0.53 in | ~5 ft |
| Why-statement | `1.28in`, weight 700 | ~0.92 in | ~9 ft |

**Width check.** Usable width is 30.8 in (36 in minus 2.6 in side margins).
`IN SEMICONDUCTORS` is the constraining line: 17 uppercase characters at roughly
`.62em` average advance, less `.015em` of tracking, is about `10.9em` - which at
`2.62in` is 28.5 in, inside 30.8 in with headroom. Headline lines carry
`white-space: nowrap` so an overflow shows up as a visible overrun in the render
instead of silently rewrapping. **If it ever overflows, reduce the headline size;
never narrow the side margins.**

The headline sits at `line-height:1.08`, raised twice from `.92` on operator
review. Tight leading looks purposeful on screen at thumbnail size and cramped at
2.6 in of cap height; when raising it, push the lead's `top` down by the same
amount rather than letting the block grow into it.

## Copy (verified - do not paraphrase)

| Slot | Text | Source |
| --- | --- | --- |
| Eyebrow badge | `A U.S. 501(C)(3) NONPROFIT` / `SILICON VALLEY, CALIFORNIA` | `website-codebase/content/english/sections/hero.md:54` |
| Headline | `UNLOCK` / `VIETNAM'S TALENTS` / `IN SEMICONDUCTORS` | `hero.md:3` and `hero.md:57` |
| Headline accent | `IN SEMICONDUCTORS` in green `#01B68B` | mirrors `accent: true` in `hero.md:61` |
| Lead | `VISEMI Foundation connects Vietnamese talent with the semiconductor industry through education, mentorship, and global industry collaboration.` | operator brief, `hero.md:68` |
| CTA | `SCAN` / `TO LEARN MORE ABOUT US`, then `visemi.org` | operator wording; URL from `data/site.toml` |
| Programs | `Demystifying Semiconductors`, `VISEMI Chip Chat`, `Cất Cánh (Takeoff) Fellowship`, `Cất Cánh Pathway`, each with a one-or-two-line description | the four live initiative pages |
| Why-statement | `Chip demand is surging.` / `Skilled talent is not.` (second line green) | condensed from the operator's "why we exist" paragraph |
| Explainer | `Industry needs and educational output have drifted apart. We close that distance with training built to industry requirements, so participants are ready to work in this critical sector.` | operator brief |

**No impact numbers on the banner.** The operator chose this deliberately:
every available statistic is either cumulative (`35.5K` views, `8` webinars) or
cohort-bound (`65` fellows, `$200K`), so printing any of them dates the print.
`check_standee.py` enforces the exclusion list.

There are also **no mission bullets** ("Empower the community" and the rest). The
operator cut them: the lead already carries the mission, and the row was competing
with the section heads directly below it.

Copy rules: full Vietnamese diacritics (`Cất Cánh`, never `Cat Canh`). No emoji.
No em or en dashes anywhere in the markup - house brand rule. Long words in the
justified blocks carry `&shy;`; see the justification notes below before editing
any of that copy.

## The design - dark, content-complete

Dark, and carrying the full pitch rather than one message: who we are, what we
do, why we exist, and where to scan. Requested with the partner logos
deliberately left out, so every inch buys content.

Background: navy field `#001C52` easing to a **held flat** `#000B2A` from 72%
down, plus a circuit-trace SVG over a 36x54 viewBox and two very low-opacity
radial blooms (cyan top-right, green mid-left). The bottom stop is held flat on
purpose: the baked chip band's fade resolves to one fixed colour, and a
still-moving gradient there leaves a visible seam.

| Y | Content |
| --- | --- |
| 0 - 0.18 in | Full-bleed accent stripe, green to cyan to green. Lifted from the site's `.section-tech--accent`. |
| 2.3 - 6.22 in | White logo SVG, 12 in wide. Right of it, the eyebrow badge: green `A U.S. 501(C)(3) NONPROFIT` over a dimmer `SILICON VALLEY, CALIFORNIA`. |
| 7.45 in | Hairline bus: one white 18% rule with three green nodes. Separates identity from message. |
| 8.15 - 15.58 in | Headline, 3 lines at `2.62in`, `IN SEMICONDUCTORS` in green |
| 17.9 - 20.26 in | Lead, `.76in` / `line-height:1.55`, justified, exactly two lines |
| 21.9 in | `What we do` section head, `.5in`, rule stops at the program column edge |
| 23.3 - 44.1 in | **Left 16.4 in:** the four programs, one per row, each a glass card with a green left rule, a `2.3in` green icon tile, a `.74in` name and a `.52in` / `line-height:1.72` description. **Right 13 in:** the scan card. |
| 45.9 in | `Why we exist` section head, rule spans the full width |
| 47.7 - 50.62 in | `Chip demand is surging.` / `Skilled talent is not.` (second line green), `1.28in`, both `nowrap` |
| 51.1 - 55.3 in | The explainer, `.6in` / `line-height:1.75`, in the same 16.4 in column |
| 47.7 - 55.3 in | Right column, aligned to the scan card above it: the divergence device on a glass card |
| 52.8 - 72 in | Chip band: `assets/chip-band-baked.jpg` full-bleed and opaque, fade already in the pixels, `z-index:0` |

**Where the air goes.** Every multi-line text block runs a loose leading
(`1.55` - `1.75`) and every heading sits *tight* to the paragraph it introduces
(`.prog h3` margin is `.15in`). That split is deliberate and was corrected once in
review: widening a heading's margin to create breathing room detaches the heading
from its own text and reads as a layout mistake, while the same space spent
between the lines of the paragraph just reads as care. If a block needs to be
airier, raise its `line-height`, never the margin above it.

**Body copy is justified** - the lead, the four program descriptions, and the
explainer. Justify is the easy half; keeping its word spacing even is the work,
and it took three passes. What the rule set means:

- **Never pair `text-wrap: balance` or `pretty` with justify.** Balance shortens
  the lines to equalise them, justify stretches them straight back to full
  measure, and the difference lands in the word gaps. Justify already removes the
  ragged edge those hints were there to fix.
- **`hyphens: manual` plus `&shy;` in the copy - never `hyphens: auto`.** A line's
  slack equals the first word that did *not* fit, shared between only a few
  spaces, so on the program descriptions' ~40-character measure an 11-letter word
  leaves a quarter of the line as slack. Breaking long words is the only real fix.
  But `auto` does nothing in headless Chrome, which ships no hyphenation
  dictionary - and it *would* work on a machine that has one, so the same source
  would set differently for whoever renders the master. `&shy;` needs no
  dictionary and is deterministic. Every word of 9+ letters in a justified block
  carries them, broken at English syllable boundaries. **Carry them across when
  editing the copy**, or the gaps come back.
- `check_standee.py`'s `visible_text` strips U+00AD, so the required-copy
  assertions still see whole words.
- **The lead is `.76in`, not `.84in`, and that is a typographic fix, not a taste
  call.** At `.84in` it ran to three lines whose middle one was only ~87% full, so
  justification stretched it; hyphenating to fill that line then left `tion.`
  alone on line three, which on a printed banner reads as a defect. Two full lines
  need neither. Its `top` was pushed down so the block still *ends* where it did
  and nothing below moved.
- Residual: the first two program descriptions still run slightly open on their
  first line. At a ~40-character measure the word that overflows is too long to
  hyphenate into the ~3 characters of room left, so the only further lever is a
  wider measure - widen the program column by narrowing the scan card. Left as is,
  since it costs QR size.

**The chip band** is `19.2in` at `top:52.8in` on the master and `24in` at
`top:66in` on the 80 x 200, and in both cases it is a **baked opaque JPEG** built
by `make_chip_band.py`, not the live SVG.

That indirection exists because of a bug that passes every check you would
normally run. The band used to be `assets/chip.svg` feathered into the field with
a stacked `linear-gradient` overlay carrying alpha. It rendered correctly in
Chrome, and correctly in pypdfium2, so it survived review twice. But Chrome emits
a **varying-alpha gradient as a PDF soft mask**, and a viewer that ignores soft
masks drops the overlay entirely and shows the raw artwork with a hard horizontal
seam across the banner. Flat `rgba()` fills are safe, because a constant alpha
becomes a plain `ExtGState` - which is why the glass cards render everywhere and
only this one broke.

There is no vector escape: feathering a raster into a background needs
transparency somewhere. So `make_chip_band.py` composites the fade against
`#000B2A` and ships pixels. Consequences to respect:

- **Do not reintroduce an overlay or `mask-image` on `.chip`.** `check_standee.py`
  fails the build if either appears, and if any source points at `chip.svg`
  directly.
- The baked fade resolves to `#000B2A`, so the banner's held bottom gradient stop
  must stay exactly that. Change one and change the other.
- A band shows only part of a square source's height (53% at 19.2 in, 67% at
  24 in), and it is aimed at the **top**: the chip package's apex sits at 25% of
  the source, and at `object-position-y 0.284` the 19.2 in crop opens at 13.3% so
  the corner emerges from the fade. An earlier `0.47` opened at 27.3% and sliced
  the corner off, which is what made the band read as an anonymous glow. The top
  fade is `0.26`, running *past* the apex on purpose so the corner emerges out of
  the blend at ~85% rather than at full strength the instant the fade ends.
- Build ramps at the output's own length and resize with `NEAREST`. Resampling a
  fixed-length ramp leaves the edge row at ~3/255 instead of 0, i.e. a thin strip
  of un-faded artwork sitting exactly on the seam you are trying to remove. The
  script's `--self-test` asserts this.
- Run it from the **repo root**, not `standee/`: Pillow is in the working repo's
  env, not the plugin's.
- `.chip` is `z-index:0`. The band now starts above where the why-block ends, so its
  first inches run behind the chart card. At `0` it paints over the background
  layers but under the glass card and all text, which is the correct order and
  reads as glass over artwork. At `1` it would paint *over* the card - same layer,
  later in source - and wash out its bottom border.
- Raising the band is the **only** way to move the chip up while keeping its
  corner. Opening the crop higher in the source just adds empty field above the
  apex and pushes the chip further down the band. So each "move it up" is a new
  height in `BANDS`, and its `object-position-y` has to be re-checked with it -
  which is exactly why the 80 x 200 has its own 24 in bake rather than the
  master's band placed higher. The `--self-test` asserts the apex survives every
  registered height, so a bad pairing fails there and not in a print proof.

Variations are retired by deleting their `.src.html`; `build_standee.py` and
`check_standee.py` both discover sources by glob and simply stop seeing it,
failing only if no source remains at all. As of 2026-07-31 A and B are gone, C is
the live design, and its two print formats are the two sources in this folder.

**The scan card.** `13 x 20.8in`, `.6in` radius, at `left:20.4in`, height slaved to
the program stack so both columns bottom out together. Card top is pinned so the
QR centre lands about **39 in above the floor**: no crouching. Three parts, top to
bottom:

1. A full-bleed **navy band that is itself the arrow** - `clip-path` corners at
   `46%` of its `6in`, so its bottom edge tapers `3.24in` to a point over the code.
   This replaced a separate small trace-arrow graphic beside the text: an arrow
   that has to stay small enough not to crowd the QR reads as an afterthought,
   whereas the pointed band both instructs and points. Shallower than about
   `2.5in` over this width and it stops reading as an arrow and starts reading as a
   banner with a notch.
2. Inside it, a two-tier lockup: `SCAN` at `1.15in` over a `.42in` /
   `letter-spacing:.22em` `TO LEARN MORE ABOUT US`. The verb carries at expo
   distance; the qualifier is subordinate. Tracked-out text needs the matching
   negative `margin-right`, or the trailing letter-space pushes the line
   off-centre.
3. A white **chevron** at `top:4.15in`, echoing the band's own point and sitting
   close to it. Positioned with an explicit `left`, not `translateX(-50%)`: the
   card is a fixed `13in` so the centre is known, and no transform has to survive
   the print path. Do not push it below about `4.4in` - the taper narrows to the
   glyph's own width by roughly `5.6in` and starts clipping it.
4. An `11.6in` QR, then a **navy footer bar** carrying `visemi.org` in white at
   `1.5in`. `overflow:hidden` on the card rounds the footer's bottom corners.

**Both bands are navy `#001669` with white text.** Brand green was tried here and
rejected by the operator. Navy is close in hue to the banner field, so the card
earns its separation from its white body and its hard edge rather than from hue -
check that separation on a proof rather than on screen. If green is ever revisited,
the text must flip to navy at the same time: white on `#01B68B` is only **2.3:1**
and fails even the 3:1 large-text floor, so the two are not an independent swap.

The footer bar is load-bearing, not decoration. The QR image ships its own
4-module quiet zone, so roughly `.9in` of the white a viewer sees sits *inside*
the image and cannot be recovered by tightening CSS. Distributing the card's
leftover height as flex gaps instead reads as a dead white band under the code,
which is exactly what an earlier version was sent back for.

**The divergence device** (the signature). The copy says industry needs and
educational output have "drifted apart", so the device is two traces that
literally diverge: gold `#F5B433` demand sweeping up, white-64% talent nearly
flat, the widening area between them filled at 7%, and a slim green double arrow
(`stroke-width:1.3`) closing the gap. Gold is a *data encoding* here, not
decoration, and it echoes the gold pins in the chip illustration below. `viewBox`
is `0 0 130 69`, one user unit to `.1in`, so stroke weights stay true to the print
scale. The card is *taller* than that aspect; `preserveAspectRatio` `meet` fits the
chart by width and centres it, so the surplus becomes even padding. Retune the
card height freely - the chart does not need redrawing to follow it.

Three traps, all learned from a render:
- **Label collisions are the whole difficulty of this device.** Each series label
  must clear *both* curves, not just its own: `SKILLED TALENT` right-aligned to
  the talent end point still reaches left across `.5in` of rising talent curve.
  Check every label against where the *other* curve runs under the label's full
  width. There is deliberately **no third label** - a 13 in column will not hold
  the curves, two series labels and a caption for the arrow, and the arrow reads
  on its own beside an explainer sentence that says we close the distance.
- **The explainer belongs in the wide column, not beside the statement.** Putting
  it in the narrow right column dropped it to 34 characters a line at `.48in`,
  and it read as fine print. At 16.4 in and `.62in` it is ~45 characters a line,
  a normal reading measure. The device takes the right column instead, where a
  graphic does not care about measure.
- Program rows are `flex:1 1 0`, so the stack's height is set by the **longest**
  description (three lines at this column width), not the average. Shorten the
  stack, or narrow the column, and that one row overflows while the other three
  look fine.

## Assets (all verified on disk)

Placeholder paths resolve against `standee/` first, then the
`cat-canh-program-management` repo root.

| Placeholder | Notes |
| --- | --- |
| `__A(visual-generation/brand/logos/visemi-logo-white.svg)__` | True vector, `viewBox 0 0 475 155`, no embedded raster |
| `__A(visual-generation/brand/logos/visemi-logo-color.svg)__` | Same, full colour. Unused: this design is dark throughout and takes the white logo. |
| `__A(visual-generation/brand/fonts/be-vietnam-pro-{latin,vietnamese}-{400,500,600,700}.woff2)__` | **Both** subsets required - the banner sets `Cất Cánh`. Copy the `unicode-range` pairs from `pitch.src.html:9-16`. |
| `__A(assets/qr-visemi.svg)__` | Vector QR for `https://visemi.org/`, navy modules, 4-module quiet zone, generated with `segno` via the existing `visgen/qr.py`. That quiet zone is why the white card looks roomier than its CSS says: ~0.9 in of the white a viewer sees is *inside* the image and no CSS can reclaim it. |
| `assets/chip-band.png` | 7029 x 3086 (4.8 MB), the retired variations' band. **Unwired.** Kept only as the historical asset; `Key Visual.png` (2520 px) and `Linkedin-1.png` (1128 px) were rejected as too small for 36 in and must not be used. |
| `__A(assets/chip.svg)__` | The chip band **source**, not the wired asset. Figma export, 1200 x 1200, with filters and a `foreignObject` backdrop-filter that only a browser resolves, which is why `make_chip_band.py` rasterises it through headless Chrome rather than any Python SVG library. Copied into `assets/` on purpose - the original lived in a git-ignored scratch path, which builds on one machine and nowhere else. |
| `__A(assets/chip-band-baked.jpg)__` | Generated from the above by `make_chip_band.py`: 5400 x 2880 (150 DPI, quality 98), opaque, fade already composited against `#000B2A`. What the **36 x 72 in** master wires. |
| `__A(assets/chip-band-baked-24in.jpg)__` | Same bake, 24 in tall (5400 x 3600). What the **80 x 200 cm** sibling wires, so its chip sits higher up the banner. Both come from one entry in `BANDS` and one rasterisation; rebuild after any change to `chip.svg`, a band height, or the field colour. |
| `__A(assets/partners/*.png\|.webp)__` | The 9 operator-selected partners; Marvell is `.webp` |

## Build and print

```bash
# From the REPO ROOT, and only when the band needs rebaking (slow: it rasterises
# the SVG at 10800px square, ~117 megapixels, to avoid upscaling).
uv run python visual-generation/standee/make_chip_band.py

cd D:/2-VISEMI/cat-canh-program-management/visual-generation/standee
uv run --project .. python build_standee.py --self-test
uv run --project .. python build_standee.py          # builds EVERY *.src.html

# One print per format. Both are the same command with the stem swapped.
for stem in visemi-standee visemi-standee-80x200; do
  "/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu \
    --user-data-dir="$TEMP/chrome-$stem" --no-pdf-header-footer --virtual-time-budget=8000 \
    --print-to-pdf="D:/2-VISEMI/cat-canh-program-management/visual-generation/standee/$stem.pdf" \
    "file:///D:/2-VISEMI/cat-canh-program-management/visual-generation/standee/$stem.html"
done

# Run the gate LAST, and from the repo root: it measures the built PDFs, and
# pypdfium2 is in the working repo's env, not the plugin's. Under `--project ..`
# the page-size check prints a skip line instead of running.
cd D:/2-VISEMI/cat-canh-program-management
uv run python visual-generation/standee/check_standee.py
```

Chrome needs an **absolute** `--print-to-pdf` path and its own
`--user-data-dir`; with a relative path or a shared profile it writes nothing and
still exits 0. To eyeball the result, render the PDF rather than screenshotting
the HTML (a 36 x 72 in page is 3456 x 6912 CSS px, too big for a viewport shot):

```bash
uv run python ../../scripts/ops/pdf_to_images.py visemi-standee.pdf --scale 0.2
```

Chrome prints unrelated `externally_managed_app_manager` and GCM registration
noise to stderr. The line that matters is `N bytes written to file`.

**What "high quality" means for this deliverable.** Everything except the chip
band is vector - type, logo, QR, the divergence chart - so it is
resolution-independent and prints as sharp as the press can hold. The band JPEG is
therefore the only thing that sets a ceiling, and Chrome's print path embeds a
JPEG **byte for byte** (verified: the PDF image dict is `/DCTDecode` with `/Length`
equal to the file size), so whatever `make_chip_band.py` writes is exactly what the
vendor receives and nothing downstream degrades it. Feeding a PNG instead would
only invite Chrome to re-encode. To verify a master:

```bash
uv run python -c "import pypdfium2 as p; d=p.PdfDocument('visemi-standee.pdf'); print(len(d), [x/72 for x in d[0].get_size()])"
```

Expect `1 [36.0, 72.0]`, and `1 [31.5, 78.74]` (80.01 x 199.99 cm) for the
80 x 200. `check_standee.py` now asserts exactly this, which is the **only**
automated check that catches a wrong `zoom` on the 80 x 200: its body is authored
at 36 x 90 in and scaled to the page, so a bad scale factor still produces a
plausible-looking HTML file and a silently wrong print master. A wrong page size
otherwise means `@page` was overridden or a `px` unit leaked into the layout.
150 DPI is the usual trade for large format, so raise or drop `DPI` in
`make_chip_band.py` if headroom or file size matters more.
