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
- **Keep recorded knowledge portable.** This plugin is consumed as a submodule by
  repos that know nothing about any one project. Docs, code comments, rubrics, and
  test fixtures must therefore describe the *shape* of a thing, never a specific
  project's content: "a three-part event metadata strip", not the actual event
  name, topic, and date from an exemplar. Real content belongs only in
  `scripts/evals/references/` exemplars, which are data, not knowledge. Generic
  fixtures also stay honest about the brand rules (a placeholder must not ship
  stripped diacritics just because it is a test).

## Brand (non-negotiable)

- Palette: navy `#001669`, dark purple `#262538`, green `#01B68B`, white, the
  token ramps, accent cyan `#00E5FF` (very sparing), gold `#F5B433` (sparing
  accent). No other hexes; no hardcoded hexes outside `brand/`.
- Status colors `--warn` `#F5A524` (amber), `--bad` `#DC2626` (red), and `--good`
  (green) are functional-only: use them for document callouts, status and
  validation states, and data encodings that carry meaning; never as decorative
  fills or as a brand accent (navy, green, and gold carry the brand). They stay
  brand-lint-allowed because their use is functional, not decorative.
- Type: Be Vietnam Pro only (400/500/600/700).
- No em/en dashes, no emojis; Vietnamese keeps full diacritics ("Cất Cánh",
  never "Cat Canh").
- Facts come from the operator's brief — never invented.
- A visual is done only when it renders (no overflow), brand-lint passes, and
  the PNGs were eyeballed.

## Layout

- `brand/` — canonical machine-readable brand source (tokens, fonts, logos, icons)
- `scripts/lib/visgen/` — shared engine; `scripts/ops/` — CLIs; `scripts/evals/` — runner/rubrics/tasks/references
- `skills/generate-*` — thin skills; `agents/visual-designer.md`
- `.claude-plugin/` — plugin + local marketplace manifests
- `output/` — git-ignored rendered output; never commit it
- `references/` — 18 read-only submodules + `sample-design-kit/` design kit. Before
  harvesting one, read the ledger in
  `docs/superpowers/specs/2026-07-24-reference-harvest-design.md`: several of them
  instruct things that contradict this repo's non-negotiables (add noise to flat
  design, swap the font, collapse to one accent), and it records what was
  deliberately rejected and why.

This repo is a Claude Code plugin (`skills/<name>/SKILL.md`, `agents/<name>.md`,
manifests in `.claude-plugin/`). It is also consumed as a git submodule inside a
working repo, pinned to a permanent per-project branch (never `master`/`main`).
The working repo supplies its own theme via a `brand/` override resolved through
`active_brand_dir()` (`VISGEN_BRAND` env / `--brand` flag / `<cwd>/brand` /
studio default); rendered output lands in the working repo's git-ignored
`output/`. Scripts anchor to `__file__`, so they run from any CWD.
