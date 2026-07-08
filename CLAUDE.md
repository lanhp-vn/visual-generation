# visual-generation

Suite of VISEMI visual-generation skills (slides, docs/handbooks, social posts,
posters) rendered from HTML to pixel-exact PNG/PDF, with shared engine, brand
tokens, and eval/grader stack. Design spec:
`docs/superpowers/specs/2026-07-08-visual-generation-skills-design.md`.

## Conventions (all tools/scripts/docs/skills/agents/engines/evals/graders)

- **DRY / Single Source of Truth.** Anything needed twice lives once, shared:
  brand values only in `brand/tokens.json` (generates `tokens.css` + the lint
  palette); render/grade logic only in `scripts/lib/visgen/`; schemas only in
  `schema.py`; rubrics only in `scripts/evals/rubrics/`. Skills and agents
  reference these — never carry private copies.
- **Build for reuse.** When a task needs a script/helper/skill/agent that a
  future task could plausibly need again, create or improve the shared one
  instead of writing a throwaway. The repo should get more capable with every
  task done in it.

## Brand (non-negotiable)

- Palette: navy `#001669`, dark purple `#262538`, green `#01B68B`, white, the
  token ramps, accent cyan `#00E5FF` (very sparing), gold `#F5B433` (sparing
  accent). No other hexes; no hardcoded hexes outside `brand/`.
- Type: Be Vietnam Pro only (400/500/600/700).
- No em/en dashes, no emojis; Vietnamese keeps full diacritics ("Cất Cánh",
  never "Cat Canh").
- Facts come from the operator's brief — never invented.
- A visual is done only when it renders (no overflow), brand-lint passes, and
  the PNGs were eyeballed.

## Layout

- `brand/` — canonical machine-readable brand source (tokens, fonts, logos, icons)
- `scripts/lib/visgen/` — shared engine; `scripts/ops/` — CLIs; `scripts/evals/` — runner/rubrics/tasks/references
- `.claude/skills/generate-*` — thin skills; `.claude/agents/visual-designer.md`
- `output/` — git-ignored rendered output; never commit it
- `references/` — 20 read-only submodules + `visemi-internal/` design kit
