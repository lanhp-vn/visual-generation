# visual-generation

VISEMI / Cất Cánh visual-generation studio: brand-locked **slides, documents,
social posts, and posters** authored as data and rendered to pixel-exact PNG/PDF
via headless Chromium, with a shared engine, brand tokens, and an eval/grader
stack. It is three things at once:

- a **standalone studio** (works from this repo's root), and
- a **Claude Code plugin** (`skills/`, `agents/`, `.claude-plugin/`), and
- a **git submodule** you drop into any working repo and drive from there.

Skills: `/generate-slides`, `/generate-doc`, `/generate-social-post`,
`/generate-poster`, plus `/visgen-setup` (bootstrap) and `/knowledge-update`
(end-of-session doc sweep). Agent: `visual-designer` (brief to rendered visual,
end to end). Facts always come from your brief, never invented; a visual is done
only when it renders with no overflow, brand-lint passes, and the PNG was
eyeballed.

## Add to a new project

From the root of the working repo you want to use it in, paste the prompt below
to Claude Code. It adds the submodule, enables the plugin, puts the studio on a
dedicated project branch, and verifies a render. (It reads the `visgen-setup`
skill file directly, so it works before the plugin's skills are registered.)

```text
Set up the VISEMI visual-generation studio in this repo as a plugin-submodule,
then verify it. Do this end to end:

1. Add the submodule at ./visual-generation (skip if it already exists):
   git submodule add https://github.com/lanhp-vn/visual-generation.git visual-generation

2. Enable the plugin in this repo's .claude/settings.json. MERGE these two keys
   in, preserving any existing permissions/hooks/enabledPlugins (create the file
   with exactly this if it does not exist):
   {
     "extraKnownMarketplaces": {
       "visual-generation": { "source": { "source": "directory", "path": "./visual-generation" } }
     },
     "enabledPlugins": { "visual-generation@visual-generation": true }
   }

3. Read visual-generation/skills/visgen-setup/SKILL.md and follow it exactly. It:
   - creates a dedicated project branch in the submodule and pushes it (ASK me
     for the branch name, e.g. my-project; never leave the submodule on
     master/main - renders are refused there),
   - scaffolds a brand/ override ONLY if this is a non-VISEMI project (for a
     VISEMI project, skip it and use the studio's default theme),
   - ensures output/ is git-ignored,
   - primes the submodule's uv environment.

4. Verify: render any existing content brief through the plugin from THIS repo's
   root (CWD = this repo). If none exists yet, render the studio's own sample:
   PYTHONIOENCODING=utf-8 uv run --project visual-generation python \
     visual-generation/scripts/ops/render_canvas.py \
     visual-generation/scripts/evals/references/kickoff.content.json \
     --format both --out output/_setup-check
   PYTHONIOENCODING=utf-8 uv run --project visual-generation python \
     visual-generation/scripts/ops/grade_brand.py output/_setup-check
   Confirm render_report.json shows overflow:false and the grade prints
   "passed": true, then open output/_setup-check/png/page-01.png and eyeball it.

5. Report: the project branch now in use, whether a brand/ override was created,
   and the sample render result. Remind me to RELOAD Claude Code so the plugin's
   skills (/generate-slides, /generate-doc, /generate-social-post,
   /generate-poster, /visgen-setup, /knowledge-update) and the visual-designer
   agent register in this workspace.

Ask me anything you need (branch name, VISEMI vs custom brand) before changing files.
```

After the reload, the skills and the `visual-designer` agent are available in
that workspace.

## Using it

Content lives with your program (e.g. `programs/<name>/<name>.content.json` for
canvas, `programs/<name>/<name>.md` for documents); rendered output goes to
`<repo>/output/<name>/` (git-ignored). Invoke a skill (`/generate-slides`, etc.)
or the `visual-designer` agent and describe the brief, or drive the engine
directly. The canonical commands (run from the working repo root):

```bash
# VG = plugin root (the submodule). Slides/docs/social/posters all go through
# render_canvas.py or render_doc.py; social/poster add --skill-dir.
VG="visual-generation"

# Slides / one-pagers
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  CONTENT.json --format both --out output/<name> --brand brand

# Social posts / posters (point --skill-dir at the matching skill)
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  CONTENT.json --format both --out output/<name> --brand brand \
  --skill-dir "$VG/skills/generate-social-post"   # or .../generate-poster

# Documents (report / handbook)
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_doc.py" \
  CONTENT.md --out output/<name> --brand brand

# Grade (deterministic brand-lint / doc-lint; must print "passed": true)
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/grade_brand.py" output/<name> --brand brand
```

`--brand brand` uses the working repo's `brand/` override; omit it to use the
studio's default VISEMI theme. Each skill's `SKILL.md` documents its layouts,
required fields, writing rules, and Anti-patterns.

## Brand and branches

- **Brand is one source of truth.** All colors, fonts, logos, and icons come from
  the active `brand/tokens.json` + `brand/` assets, resolved through
  `active_brand_dir()` (order: `VISGEN_BRAND` env / `--brand` flag, then
  `<cwd>/brand` if present, then the studio default). Render and brand-lint always
  resolve the same brand, so they can never disagree. No hardcoded hexes outside
  `brand/`; Be Vietnam Pro only; no em/en dashes or emojis; full Vietnamese
  diacritics.
- **Permanent per-project branch.** `master` is the blessed seed. Each project
  branches once (e.g. `visemi-catcanh`), diverges, and stays. A pre-flight guard
  **refuses to render when the submodule is on `master`/`main`** inside a working
  repo, pointing you to `visgen-setup`. Sharing an upgrade back is a manual
  cherry-pick/merge to `master`; other projects pick it up by merging `master`.

## Standalone / development

```bash
uv run pytest scripts/tests -q            # unit + schema + brand-injection + guard tests
uv run python scripts/evals/run_evals.py  # render + grade every reference exemplar (pass@k / pass^k)
```

## Layout

```
.claude-plugin/   plugin + local marketplace manifests
skills/           generate-slides | generate-doc | generate-social-post | generate-poster | visgen-setup | knowledge-update
agents/           visual-designer.md
brand/            canonical brand source (tokens.json, fonts, logos, icons) - the default VISEMI theme
scripts/lib/visgen/   shared engine (render, brand resolver, lint, schema, formats)
scripts/ops/          CLIs (render_canvas, render_doc, grade_brand, grade_doc, grade_rubric)
scripts/evals/        runner, tasks, rubrics, reference exemplars
output/           git-ignored rendered output
```

Design docs: `docs/superpowers/specs/` and `docs/superpowers/plans/`.
