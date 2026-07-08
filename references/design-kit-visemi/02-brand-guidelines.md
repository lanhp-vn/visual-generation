# 02 — Brand Guidelines (Palette · Type · Logo · Components)

Exact, copy-pasteable brand values. These mirror the live site's single source of
truth (`website-codebase/data/theme.json`) and the official brand sheets in
`assets/reference/Colors.png` and `assets/reference/Typography.png`. **Never invent a
hex or a font.**

---

## 1. Color palette

### Core brand colors
| Name | Hex | Role |
|---|---|---|
| **Dark Blue** | `#001669` | Primary brand anchor — authority, structure, headings on light, "The Gaps" side. |
| **Dark Purple** | `#262538` | Default body-text color; deep neutral backgrounds. |
| **Green** | `#01B68B` | Energy & action — CTAs, momentum, "The Bridge" side, key stat figures, accents. |
| **White** | `#FFFFFF` | Primary background; text on dark. |

### Tint & shade ramps (use for backgrounds, fills, depth — not new hues)
**Dark Blue ramp**
`#000F4D` (900) · `#001259` (800) · **`#001669` (base)** · `#4D6299` (300) · `#99A8C9` (200) · `#CCD4E4` (100)

**Dark Purple ramp**
`#1A1929` (800) · **`#262538` (base)** · `#6B6A7D` (300) · `#A9A8B5` (200) · `#D4D4DA` (100)

**Green ramp**
`#018A6A` (900) · `#019578` (800) · **`#01B68B` (base)** · `#4DD4AF` (300) · `#99E5CF` (200) · `#CCF2E7` (100)
> Green hover/darker state on the site = `#019974`.

### Accent
| Name | Hex | Role |
|---|---|---|
| **Accent Cyan** | `#00E5FF` | Tech sparkle only — gradient stripe end, hero-halo glow. Use very sparingly; never for text or large fills. |

### Signature gradient (dark feature sections)
A 135° diagonal blend of deep blue → blue → deep purple:
`linear-gradient(135deg, #000F4D 0%, #001669 50%, #1A1929 100%)`
Optional bottom accent stripe: `linear-gradient(90deg, #01B68B, #00E5FF, #01B68B)`.

### Usage rules
- **Light surfaces are the default.** White / `#F6F6F6` backgrounds, navy headings,
  `#262538` body text. Reserve the dark gradient for impact moments.
- **Green ≈ 10–20% of any layout.** It's the spotlight, not the room.
- **Contrast:** white or `#CCF2E7`-light text on dark gradients; navy/purple text on
  light. Keep body text ≥ 4.5:1 contrast (WCAG AA).
- **Text-light gray** (`#717171`) for captions/metadata on light backgrounds.

---

## 2. Typography

**Typeface: Be Vietnam Pro** — for *everything* (full Vietnamese diacritic support is
exactly why it's the brand font). Weights: **400 Regular · 500 Medium · 600 Semibold ·
700 Bold.** If Be Vietnam Pro is unavailable in a tool, fall back to Inter, then a
system sans-serif — but in Canva it's in the brand kit, so use it.

### Scale (from the official Typography sheet; type scale factor 1.25)
| Token | Use | Weight guidance |
|---|---|---|
| **Display 2xl** (~76px) | Hero headline numbers / cover titles | Bold |
| **Display xl** (~60px) | Slide / poster titles | Bold or Semibold |
| **Display lg** (~48px) | Section titles | Semibold/Bold |
| **Display md** (~38px) | Sub-section / card headers | Semibold |
| **Display sm** (~30px) | Large supporting headers | Medium/Semibold |
| **Display xs** (~25px) | Lead-in lines | Medium |
| **Text xl** (~20px) | Lead body / standfirst | Regular/Medium |
| **Text lg** (~18px) | Body copy | Regular |
| **Text md** (~16px) | Default body / captions on slides | Regular |
| **Text sm / xs** (~14/12px) | Footnotes, metadata, source lines | Regular |

### Type rules
- **Headlines:** Bold, tight leading (~1.1), letter-spacing slightly negative
  (`-0.02em`) on large display sizes.
- **Eyebrow / kicker:** ~14px, UPPERCASE, letter-spacing `+0.12em`, **green**, sits
  above a headline. A signature brand polish move.
- **Body:** Regular, ~1.5 leading, generous measure (40–70 chars/line). Don't go
  below 12px on any output.
- **Hierarchy by size + weight, not color.** Keep most text navy/purple; use green
  for emphasis words, not whole paragraphs.
- **Numbers as heroes:** big stat figures in Display 2xl/xl, bold, green or navy,
  with a small label beneath.

---

## 3. Logo

Files in `assets/logos/`:
- `visemi-logo-color.svg` / `.png` — full color (navy + green diamond + wordmark) — for **light** backgrounds.
- `visemi-logo-white.svg` / `.png` — all-white — for **dark / photo** backgrounds.
- `visemi-mark-320.png` — square diamond mark only — for avatars, favicons, tight corners.

**Rules**
- Use the **white** logo on dark gradient / photo headers, the **color** logo on light.
- **Clear space:** keep padding ≥ the height of the diamond mark around the logo.
- **Minimum size:** wordmark ≥ ~120px wide on screen; don't render it so small the
  "FOUNDATION" line is illegible.
- **Never** recolor, stretch, rotate, add effects, or place on a low-contrast/busy
  background without a scrim.
- On Cất Cánh pieces the VISEMI logo is the org mark; "Cất Cánh (Takeoff) Fellowship"
  is set in **type**, not as a separate logo.

---

## 4. Iconography

- **Style:** clean, **line / outline icons**, 1.5–2px stroke, rounded joins, mostly
  **green** (or navy on green fills). Matches the pitch-deck icon set (rocket, globe,
  graduation cap, network nodes, handshake).
- **Signature icon:** the **rocket** = Cất Cánh / takeoff / acceleration.
- Keep icons consistent in weight and size within a layout. One icon per concept.
- Source set lives in the website repo (`media-assets/icons-and-graphics/`): rocket,
  connection/network, global, impact, leadership, skill-improve, contribution. Reuse
  these rather than mixing in a different icon family.

## 5. Imagery & photography

- **Prefer real people:** Vietnamese students, fellows, cohorts, events, mentors —
  authentic and aspirational, not generic stock.
- **Treatment:** natural, bright, optimistic. On dark sections, add a navy gradient
  scrim so white text stays legible.
- **Crops:** circular headshots for people (as in the founding-team strip); wide
  cover-crops for hero banners.
- Partner / university / sponsor logos live in `assets/partner-logos/`
  (`Sponsor List.csv` is the partner reference). Display them in a tidy monochrome or
  full-color row on a light band; keep equal optical sizing.

## 6. Component recipes (reusable building blocks)

- **Stat card / band:** big bold figure (green or navy) + short label; thin accent
  rule; 2×3 or single row. Numbers from the brief.
- **Numbered column:** large green/navy `01 02 03` + heading + 1–2 lines. The
  "Who we are / Key initiatives / Why we exist" layout.
- **Pillar card:** icon + bold heading + one support line; white card on a navy
  offset shadow-block. Used for the 3 program pillars.
- **Gaps → Bridge split:** two columns (navy problem | green solution) + green arrow.
- **Tier ladder:** descending stepped bars (navy → green) for tiered funding levels.
- **CTA band:** dark gradient section, white headline, one pill button + QR code
  (Cất Cánh QR codes live in Canva).
- **Buttons:** **pill-shaped** (fully rounded). Variants: filled green (primary CTA),
  outlined navy, outlined green, white/ghost (on dark). Semibold label, comfortable
  padding.
