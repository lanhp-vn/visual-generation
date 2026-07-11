---
name: visgen-setup
description: Bootstrap the visual-generation studio inside a working repo. Use once after adding visual-generation as a submodule, or whenever the submodule is on master/main and needs a dedicated project branch. Creates the project branch, scaffolds the brand/ override and output/ gitignore, and enables the plugin. Also use when a render was refused with a "create a dedicated project branch" message.
---

# visgen-setup

Bootstraps the `visual-generation` studio inside a working repo after the plugin
is enabled. Run it once when the submodule is first added, and again any time a
render is refused because the submodule is sitting on `master`/`main`.

Run every step from the WORKING REPO root (the repo that contains the
`visual-generation/` submodule). The submodule path is `visual-generation/`
unless you added it elsewhere; substitute your path throughout if so.

## Step 1 - Dedicated project branch (required; never leave it on master/main)

The studio refuses to render as a submodule while it is on `master`/`main`, so
every project gets its own permanent branch seeded from `master`.

```bash
SUB="visual-generation"            # submodule path
git -C "$SUB" rev-parse --abbrev-ref HEAD    # current branch
```

If the current branch is `master` or `main`, STOP and ask the user for a project
branch name (e.g. `visemi-catcanh`), then create and publish it:

```bash
BRANCH="<project-branch>"          # ask the user; e.g. visemi-catcanh
git -C "$SUB" checkout -b "$BRANCH"
git -C "$SUB" push -u origin "$BRANCH"
```

If it is already on a project branch, leave it and continue.

## Step 2 - Brand override (optional; only for a non-VISEMI theme)

The studio ships the VISEMI theme as its default, resolved automatically. A
working repo only needs its own `brand/` if it wants a DIFFERENT theme. To start
from the VISEMI brand as an editable base:

```bash
# Only if this working repo needs a non-VISEMI theme and has no brand/ yet:
mkdir -p brand && cp -r "$SUB"/brand/* brand/
# then edit brand/tokens.json (palette), brand/logos/, brand/fonts/ as needed.
```

For a VISEMI repo (e.g. cat-canh) skip this: omit `--brand` on renders and the
studio default is used. When a working-repo `brand/` exists, pass `--brand brand`
(or set `VISGEN_BRAND`); the engine and brand-lint both resolve the same root.

## Step 3 - Git-ignore rendered output

Rendered output goes to `<working-repo>/output/<name>/` and must never be
committed.

```bash
grep -qxF "output/" .gitignore 2>/dev/null || echo "output/" >> .gitignore
```

## Step 4 - Enable the plugin in committed project settings

Ensure `<working-repo>/.claude/settings.json` registers the local marketplace
and enables the plugin. If the file does not exist, create it with exactly:

```json
{
  "extraKnownMarketplaces": {
    "visual-generation": { "source": { "source": "directory", "path": "./visual-generation" } }
  },
  "enabledPlugins": { "visual-generation@visual-generation": true }
}
```

If `settings.json` already exists, ASK before editing it, then MERGE these two
keys in (add, never overwrite existing `permissions`/`hooks`/`enabledPlugins`
entries; keep any other enabled plugins such as `playwright@claude-plugins-official`).

## Step 5 - Prime the submodule Python env

Make sure the studio's dependencies (Playwright/Chromium) are importable through
the submodule's `uv` project:

```bash
uv run --project "$SUB" python -c "import playwright; print('playwright ok')"
# if that fails: uv sync --project "$SUB"
```

## Step 6 - Ready summary

Report to the user: the project branch now in use, whether a `brand/` override
was created (or the VISEMI default is active), that `output/` is git-ignored, and
that the plugin is enabled. Include a sample render they can run from the working
repo root (CWD = working repo):

```bash
VG="visual-generation"
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/render_canvas.py" \
  programs/<name>/<name>.content.json --format both --out output/<name>
PYTHONIOENCODING=utf-8 uv run --project "$VG" python "$VG/scripts/ops/grade_brand.py" output/<name>
```

Now the `generate-slides`, `generate-doc`, `generate-social-post`,
`generate-poster`, and `knowledge-update` skills plus the `visual-designer`
agent are ready to use from this working repo.
