---
name: knowledge-update
description: End-of-session knowledge sweep for this visual-generation repo. Reviews git status/diff plus the conversation to find everything built, fixed, or learned this session, then propagates each durable piece of knowledge into its single correct home - the owning skill's SKILL.md (usage + Anti-patterns), inline code comments in document.css/templates/scripts, docstrings in scripts/lib/visgen/, agent definitions in .claude/agents/, eval reference exemplars in scripts/evals/references/ so new capabilities get regression coverage instead of only ever running against a private/uncommitted input, and CLAUDE.md only for genuine repo-wide conventions. Re-renders and re-grades any exemplar it touches so the repo is left in a verified-passing state, then reports a summary - never commits. Always use this at the end of a session that touched .claude/skills/, scripts/lib/visgen/, scripts/ops/, scripts/evals/, .claude/agents/, or brand/, or whenever the user says "update the docs with what we learned", "record this session's knowledge", "make sure this doesn't get lost", "knowledge-update", or invokes /knowledge-update - even if they don't spell out exactly what changed, since this skill figures that out from the repo diff and conversation itself.
---

# knowledge-update

Runs an end-of-session sweep so nothing built or learned in the conversation
stays *only* in the conversation. CLAUDE.md says the repo should get more
capable with every task done in it - this skill is how that actually happens,
instead of staying an aspiration that quietly lapses once the chat ends.

## When to run

At the end of a session that touched `.claude/skills/`, `scripts/lib/visgen/`,
`scripts/ops/`, `scripts/evals/`, `.claude/agents/`, `brand/`, or `CLAUDE.md` -
or whenever the user asks to record/update what was learned, or runs
`/knowledge-update`. Optional scope argument (e.g. "just generate-doc",
"everything since <commit>") - default is the whole current session.

## Step 1 - Reconstruct what actually happened

`git status` / `git diff` show WHAT changed; they don't show WHY. Walk the
diff alongside the conversation and pull out, for each substantive change:

- A new capability (front-matter field, CSS component, CLI flag, agent,
  grader check) - what it does, how to invoke it.
- A bug or hazard caught mid-session - something that worked for the one case
  tested but would break on different input - and whether it's actually fixed
  yet or just noticed.
- A design decision with a non-obvious reason (why this CSS trick, why this
  file split, why this default). The reason is the part worth keeping; the
  code alone won't carry it forward to the next session.
- Anything the user corrected you on, or explicitly confirmed was right -
  both are signal, not just the corrections.

If nothing durable happened (pure Q&A, a one-off fix with no reusable shape),
say so and stop. Don't manufacture busywork to justify having been invoked.

## Step 2 - Route each item to its single home

This repo's DRY / Single Source of Truth rule applies to knowledge, not just
code: find the ONE place an idea belongs and put it there, instead of leaving
it scattered across a commit message, a memory, and your own head.

| Kind of knowledge | Home |
|---|---|
| How to use a new field/component, and its caveats | The owning skill's `SKILL.md` (usage section, and its Anti-patterns list if it's a footgun) |
| Why a CSS/template rule exists (a constraint, a workaround, a fragile interaction) | An inline comment next to the rule - not a separate doc that will drift from the code |
| A new function/module capability | Its docstring |
| A behavior change in a script/CLI | That script's own docstring/help, plus any skill that tells users to run it |
| A new agent, or a scope change to one | The agent's own definition file |
| A repo-wide convention (not one skill's detail) | `CLAUDE.md` - but see the guard below |
| Project state (who's doing what, deadlines) | Not this sweep - that's conversational memory, not a repo artifact |

**Guard on CLAUDE.md**: only touch it for something that changes how EVERY
skill/script in the repo should behave. A single skill's field or a CSS
detail belongs in that skill's `SKILL.md`, not `CLAUDE.md` - `CLAUDE.md` loads
into every session's context, so bloating it costs every future session, not
just this one.

## Step 3 - Make sure new capabilities are exercised, not just documented

A feature that only ever ran against a private, uncommitted input (a
scratchpad file with real PII, a one-off asset outside the repo) has no
regression coverage - the next change to that code path can break it silently.

- Prefer enriching an existing reference exemplar
  (`scripts/evals/references/*.md`) over adding a new one - it stays inside
  the regression sweep `run_evals.py` already runs.
- Use facts already present in that exemplar's own body text; don't invent
  new numbers just to fill a field.
- If a field needs an asset (an image path, a logo) and no clean, on-brand,
  already-committed asset exists, don't force a mediocre example in just for
  coverage - a bad example that technically "passes" lint but looks wrong is
  worse than no example. Document the caveat in the skill's Anti-patterns
  instead (what goes wrong, why lint won't catch it) and leave the exemplar
  honest rather than padded.
- Same logic for rubrics/graders: if a new dimension of quality now matters,
  check whether an existing rubric already covers it before writing a new one.

## Step 4 - Verify, don't just edit

Re-render whatever reference exemplar(s) you touched and run the deterministic
grader (`grade_doc.py` for documents, the canvas equivalent for slides) before
calling this done. If you touched more than one exemplar, or want the full
sweep, run `uv run python scripts/evals/run_evals.py`. An edited doc with an
unverified claim of "done" is exactly the failure mode this skill exists to
prevent - the same "verify by rendering" rule the individual skills already
hold themselves to applies here, one level up.

## Step 5 - Report, don't commit

Summarize what you found and where you put it - one line per file/change - so
the user can review before committing. Never `git add` / `git commit` as part
of this skill; the user commits when they're ready to.
