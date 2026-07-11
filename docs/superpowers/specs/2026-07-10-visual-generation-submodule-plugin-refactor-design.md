# Visual Generation as a Portable Plugin-Submodule Studio — Design

**Date:** 2026-07-10
**Repo:** `visual-generation`
**Status:** Approved by lanph@visemi.org (interview + section review)
**Supersedes nothing** — extends `2026-07-08-visual-generation-skills-design.md`
(the studio build) with a portability/consumption layer and completes M3/M4.

## Goal

Make `visual-generation` consumable from inside any working repo as a git
submodule, discoverable there as a Claude Code plugin, themeable per working
repo without touching the shared code, upgradable from within a working session,
and complete (all four generators ship). The vision: pull this repo as a
submodule into a workspace, create a dedicated branch for that project, and use
its tools/scripts/skills/agents/evals/graders as if they were native — while the
studio itself gets better over time from the work done in each project.

## Decisions (interview summary)

| Question | Decision |
|---|---|
| Per-repo theming | **Brand override from the working repo.** `master` stays generic; the working repo supplies its own `brand/` outside the submodule. No brand is ever committed to the submodule. |
| Skill/agent discovery | **Claude Code plugin.** The submodule carries a plugin manifest; the working repo enables it from the local path. Skills + agents auto-register. |
| Git model | **Permanent per-project branches.** `master` is the blessed seed. Each project branches once (e.g. `visemi-catcanh`), diverges, and stays put. Promotion to `master` is optional, never forced. |
| Branch enforcement | **Always required.** A pre-flight guard refuses to render when the submodule is on `master` inside a working repo, directing the user to create a project branch (via `visgen-setup`). |
| Output location | **`<working-repo>/output/<name>/`**, gitignored — one mental model matching the submodule's own `output/`. |
| Parent's frozen copies | **Retire** cat-canh's `.claude/skills/generate-slides` + `slide-designer` agent once the plugin is live (they collide by name). |
| Scope | Plugin plumbing + CWD-independent scripts + brand injection + `visual-designer` agent + `visgen-setup` bootstrap + **complete M3 (`generate-social-post`) and M4 (`generate-poster`)** so the plugin ships complete. |
| Modularization | Brand becomes an injected dependency (one shared resolver); existing DRY module boundaries preserved, upgrades stay additive. No speculative rewrite. |

## Architecture

One repo plays three roles at once, with no duplication:

1. **A standalone studio** — works exactly as today when CWD is the repo root.
2. **A Claude Code plugin** — `.claude-plugin/plugin.json` + a single-plugin
   local `marketplace.json` (source `.`) expose the skills and the agent.
3. **A git submodule** — added at a working repo's root; the working repo enables
   the plugin from that local path.

The seam that makes per-repo themes possible is **brand injection**: the engine
and the brand-lint both resolve their brand source (tokens, fonts, logos,
palette allowlist) through one shared resolver instead of hardcoding `brand/`.

## Repo layout (after)

```
visual-generation/
  .claude-plugin/
    plugin.json            # NEW manifest (name, version, description)
    marketplace.json       # NEW single-plugin marketplace, source "."
  skills/                  # MOVED from .claude/skills/ (plugin convention)
    generate-slides/
    generate-doc/
    generate-social-post/  # NEW (M3)
    generate-poster/       # NEW (M4)
    knowledge-update/
    visgen-setup/          # NEW bootstrap skill
  agents/
    visual-designer.md     # NEW ported end-to-end agent
  brand/                   # unchanged — DEFAULT (VISEMI) theme + lint source
  scripts/
    lib/visgen/            # engine — brand resolver added, root anchored to __file__
    ops/                   # CLIs — CWD-independent, accept --brand, branch pre-flight
    evals/                 # references/, tasks/, rubrics/ — +social +poster exemplars
    tests/
  .claude/settings.json    # enables the local plugin for STANDALONE use
  docs/  references/        # unchanged
  output/                   # gitignored (standalone default)
```

`.claude/skills/generate-slides-workspace/` stays gitignored scratch; not shipped.

## Consumption model (discovery)

- The submodule is added at the working repo root: `<working-repo>/visual-generation/`.
- The working repo's `.claude/settings.json` registers the local marketplace and
  enables the plugin (`extraKnownMarketplaces` → local path; `enabledPlugins`).
  Result: `/generate-slides`, `/generate-doc`, `/generate-social-post`,
  `/generate-poster`, `/visgen-setup`, and the `visual-designer` agent are
  available while working in the working repo.
- Standalone use is preserved: the submodule's own `.claude/settings.json`
  enables the same local plugin, so CWD = submodule root also has the skills.
  One source (the plugin) serves both contexts — no duplicated skill copies.

## Brand injection

One resolver in `scripts/lib/visgen/` (call it `brand.py`) returns the active
brand root. Resolution order:

1. `--brand <path>` CLI flag (per-invocation override)
2. `VISGEN_BRAND` environment variable
3. `<working-repo>/brand/` if it exists (working-repo default theme)
4. `<submodule>/brand/` (default VISEMI theme)

Both the renderers and `brand_lint.py` consume this resolver, so the lint's
palette allowlist is generated from whichever `tokens.json` won — the lint can
never enforce a theme the render didn't use. For cat-canh the override mirrors
VISEMI (effectively a no-op); a future non-VISEMI working repo swaps `brand/` and
everything re-themes with no code change.

## CWD-independent scripts

Every `scripts/ops/` CLI and the engine resolve the repo root from
`Path(__file__).resolve().parents[N]`, never `getcwd()`. This is what lets a
skill invoked from the working repo (CWD = working repo) still find templates,
default brand, and its own modules. Output and brand are passed in explicitly
(`--out`, `--brand`); nothing is read relative to CWD.

SKILL.md invocation commands are updated to be location-independent. Preferred
form uses `$CLAUDE_PLUGIN_ROOT` (set by Claude Code for plugin-provided skills);
documented fallback is `uv run --project <submodule> python <submodule>/scripts/...`
with the submodule path recorded by `visgen-setup`. Which form ships is decided
by the pre-implementation spike below.

## Content / brand / output in a working repo

- **Content briefs** live with the program: `programs/<name>/*.content.json` (canvas)
  and `programs/<name>/*.md` (documents), plus `programs/<name>/images-for-slides/`
  for photo slots. This matches the existing cat-canh pattern.
- **Brand override** lives at `<working-repo>/brand/` (tokens.json + fonts/ + logos/).
- **Rendered output** goes to `<working-repo>/output/<name>/`, gitignored.

## Git / branch workflow

- The submodule is pinned to a permanent per-project branch (e.g. `visemi-catcanh`),
  seeded from `master`. The branch diverges and stays; it is never force-merged
  back. Studio upgrades learned during sessions (new layouts, fixes,
  `knowledge-update` edits) commit on that branch and push to origin.
- Cross-project sharing is optional and manual: cherry-pick or PR a broadly useful
  upgrade to `master`; other projects pick it up by merging `master` into their branch.
- **Branch enforcement (always asked):** a shared pre-flight in the render CLIs
  detects "running as a submodule inside a working repo" AND "submodule HEAD is on
  `master`", and refuses to render, printing the exact `visgen-setup` next step.
  This is one guard at the shared entry point, not per-skill prose.

### `visgen-setup` bootstrap skill

Runs after the plugin is enabled in a new working repo. It:

1. Verifies/creates the dedicated project branch in the submodule (prompts for a
   name if none given; refuses to leave it on `master`).
2. Scaffolds `<working-repo>/brand/` (seeded from the submodule's VISEMI brand as
   a starting point to edit).
3. Ensures `<working-repo>/.gitignore` has `output/` and the settings.json plugin
   entry exists.
4. Prints a short "you're ready" summary with the render commands.

The one-time "add the submodule + write the settings.json plugin entry" is
documented in the plugin README/quickstart and can be done by Claude on request;
`visgen-setup` handles everything after the plugin is live.

## `visual-designer` agent

`agents/visual-designer.md` generalizes cat-canh's `slide-designer`:
brief → pick skill + format → author content (facts from brief only, never
invented) → render → grade (brand-lint always; rubric if `ANTHROPIC_API_KEY`) →
fix and re-render (cap 4 iterations) → eyeball PNGs → report output paths +
verification results + any facts it had to ask about. It routes across all four
generators (slides, docs, social, poster) via the format the brief implies.

## M3 — `generate-social-post`

New skill over the existing canvas renderer + formats registry (sizes already
registered: `square`, `portrait`, `story`, `link`). Ships:

- `skills/generate-social-post/SKILL.md` — workflow, size table, feed-legibility
  writing rules (bigger type floors, one message per canvas, photo-background and
  graphic-background variants, QR/CTA variants).
- `skills/generate-social-post/templates/layouts/` — social-tuned layouts (photo
  hero + scrim, quote card, stat card, announcement, CTA/QR). Built from the shared
  `components.html.j2` macro library; tokens only, no hardcoded hexes.
- `schema.py` layout entries for the new layouts (required fields).
- One reference exemplar in `scripts/evals/references/` + a synthesized eval task
  so it is regression-covered.

## M4 — `generate-poster`

New skill over the same renderer (sizes already registered: `poster-a`,
`banner-wide`, `email-header`). Ships:

- `skills/generate-poster/SKILL.md` — workflow, size table, poster/banner density
  and hierarchy rules; shares canvas layouts with social posts where sensible,
  differs in size and density.
- `skills/generate-poster/templates/layouts/` — poster, wide banner, QR card,
  email header. Shared macro library; tokens only.
- `schema.py` layout entries + one reference exemplar + a synthesized eval task.

## Parent (working-repo) changes for cat-canh

- Add `visual-generation` as a submodule at repo root.
- Add the plugin marketplace + enable entry to `.claude/settings.json`.
- Run `visgen-setup`: create `visemi-catcanh` branch, scaffold `brand/`, ensure
  `output/` is gitignored.
- **Retire** the frozen `.claude/skills/generate-slides` (411K) and the
  `slide-designer` agent — they collide by name with the plugin. Existing content
  briefs under `programs/` are unaffected and re-render through the plugin.

## Knowledge growth from working sessions

`knowledge-update` (now shipped in the plugin) runs at session end from within the
working repo, targeting the submodule's files (each kind of knowledge to its single
correct home, as it already documents), re-rendering and re-grading any exemplar it
touches, and leaving changes staged on the project branch for the user to commit
and push. This is the mechanism by which the studio improves over time per project.

## Verification / acceptance

- **Portability:** with the plugin enabled from cat-canh, `/generate-slides` on an
  existing cat-canh content JSON renders to `<working-repo>/output/…`, brand-lint
  green, PNGs eyeballed — with CWD = cat-canh (not the submodule).
- **Brand injection:** a throwaway `brand/` override in the working repo changes
  the rendered palette and the lint allowlist together; removing it falls back to
  VISEMI. A dedicated test asserts render and lint resolve the same brand root.
- **Branch guard:** rendering with the submodule on `master` inside a working repo
  is refused with the `visgen-setup` message; on a project branch it proceeds.
- **Standalone unbroken:** the existing test suite + `run_evals.py` pass with CWD =
  submodule root; all existing exemplars re-render and pass.
- **M3/M4:** the social and poster exemplars render at their sizes, lint green,
  appear in `run_evals.py` (pass@k / pass^k reported).

## Implementation risk (spike first)

Whether `$CLAUDE_PLUGIN_ROOT` is reliably exported to the Bash environment for
plugin-provided *skills* (as opposed to hooks/commands). Resolve this with a
one-command spike before finalizing SKILL.md invocation syntax; the fallback
(`uv run --project <submodule> …` with the path recorded by `visgen-setup`) is
ready if it is not.

## Out of scope

- Canva/Drive integration; photo sourcing or AI image generation (placement only);
  reveal.js/slidev runtimes; animated/video outputs.
- Changes to the 20 read-only reference submodules.
- Any engine feature change beyond the brand-injection seam and the CWD anchoring.

## Milestones

1. **P1 — Plugin + submodule plumbing.** Manifests, layout move to `skills/` +
   `agents/`, standalone `.claude/settings.json`, CWD-independent scripts, spike on
   `$CLAUDE_PLUGIN_ROOT`. Standalone tests + evals green.
2. **P2 — Brand injection.** `brand.py` resolver wired into renderers + lint; test
   asserting render/lint share the resolved root; VISEMI fallback intact.
3. **P3 — Bootstrap + branch guard.** `visgen-setup` skill; shared pre-flight guard;
   wire cat-canh (submodule add, settings entry, `visemi-catcanh` branch, scaffold,
   retire frozen copies). Portability acceptance test green from cat-canh.
4. **P4 — `visual-designer` agent.** Ported and routing across generators.
5. **P5 — M3 `generate-social-post`** — skill, layouts, schema, exemplar, eval task.
6. **P6 — M4 `generate-poster`** — skill, layouts, schema, exemplar, eval task.

Each milestone ends verified: exemplars render, lint green, eval runner green,
PNGs eyeballed.
