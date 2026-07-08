# Cất Cánh Design Kit — for the Claude "Cat-Canh-Design" project

This folder is the **design brain** for a Claude.ai Project that generates VISEMI
Cất Cánh marketing & communication assets — slides, social posts, recruitment
graphics, and one-pagers — in Canva.

It deliberately holds **design guidance only, not program facts.** You supply the
content (numbers, dates, names, copy) each time you brief a design. The kit tells
Claude *how* a Cất Cánh piece should look, read, and assemble — never *what the
Year-1 target is*. That keeps it from baking in stale figures.

---

## What's in here

| File | Purpose | Where it goes in the Project |
|---|---|---|
| `00-PROJECT-INSTRUCTIONS.md` | The short, always-on operating brief. | **Paste into the Project's custom-instructions box.** |
| `01-design-philosophy.md` | Theme, philosophy, and style — pulled from the live visemi.org site + the Cất Cánh "Takeoff" motif. | Upload as Project knowledge. |
| `02-brand-guidelines.md` | Palette (with full ramps), typography scale, logo rules, iconography, imagery, component recipes. | Upload as Project knowledge. |
| `03-voice-and-copy.md` | Bilingual voice/tone, diacritics, naming, the `{LANG} \| {AUDIENCE} \| {TYPE}` convention, glossary, on-slide copy patterns. | Upload as Project knowledge. |
| `04-output-specs.md` | Exact dimensions per channel, mapped to the existing Canva canon to clone. | Upload as Project knowledge. |
| `05-canva-and-drive-workflow.md` | How to drive the Canva + Drive connectors: which brand kit, clone-don't-autofill, "layout from canon, numbers from the brief." | Upload as Project knowledge. |
| `assets/` | Logos (color + white, SVG + PNG), partner logos + `Sponsor List.csv`, the official Colors/Typography reference images. | Upload the files you need as attachments. |
| `Visemi - Cat Canh - Pitch Deck.pdf` | Canonical donor pitch deck — the gold-standard layout reference. | Upload as Project knowledge. |
| `Official Cat Canh Webinar slide.pdf` | Canonical webinar slide deck — second layout reference. | Upload as Project knowledge. |

---

## One-time setup (Claude.ai)

1. **Create a Project** named `Cat-Canh-Design` (or similar).
2. **Connect the tools** in the Project's connector settings:
   - **Canva** — so Claude can read the Visemi brand kit, search/clone existing
     designs, and export.
   - **Google Drive** — so Claude can pull copy, photos, and source files you
     point it at.
   - (Connectors are configured in the Project UI, **not** in these files.)
3. **Paste** the entire contents of `00-PROJECT-INSTRUCTIONS.md` into the
   Project's custom-instructions / "What should Claude know" box.
4. **Upload as Project knowledge:** `01`–`05`, both reference PDFs, and the two
   reference images in `assets/reference/`.
5. **Keep `assets/logos/` and `assets/partner-logos/` handy** to attach to a
   chat when a design needs a real logo file (Canva also has them in the brand
   kit, but having the source files is a safe fallback).

## How you'll use it

In any chat in that Project, brief Claude like:

> "Make a square Instagram post announcing Cất Cánh applications are open.
> Deadline 30 June. Headline VI + EN. Clone the look of `Register Post - Square`."

Claude reads the kit, applies the brand, pulls layout from the named canon,
drops in **your** supplied facts, and produces or autofills the Canva design.

## Keeping it current

- **Brand or website style changed?** Update `01`/`02` and re-upload.
- **New canonical design worth cloning?** Add it to the canon table in `04`.
- This kit mirrors the visemi.org design system as of its last edit; if the live
  site's tokens (`website-codebase/data/theme.json`) change, refresh `02`.
