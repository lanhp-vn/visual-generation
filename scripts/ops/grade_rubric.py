#!/usr/bin/env python3
"""LLM-as-judge rubric grader. One isolated judge per dimension; 0-5 + justification;
"Unknown" allowed (the way out). Grades the rendered images, not the path taken.

Dimensions (theme-agnostic: a deck may be light or dark, both correct):
  brand   - brand fidelity (palette, font, logo, diacritics, no emoji/em-dash)
  layout  - layout, spacing, and overflow on the 1920x1080 stage
  content - content fidelity to the task brief (facts present, nothing invented)
  polish  - visual polish / overall craft

Model is claude-opus-4-8. Each dimension reads scripts/evals/rubrics/<dimension>.md.

Usage: uv run python scripts/ops/grade_rubric.py OUTDIR --task TASK.json [--model claude-opus-4-8]
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

DIMENSIONS = ["brand", "layout", "content", "polish"]
DOC_DIMENSIONS = ["doc-pagination", "toc-usefulness"]

RUBRIC_DIR = Path(__file__).resolve().parents[1] / "evals/rubrics"
SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "string", "enum": ["0", "1", "2", "3", "4", "5", "Unknown"]},
        "justification": {"type": "string"},
    },
    "required": ["score", "justification"],
    "additionalProperties": False,
}


def _parse(resp):
    text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
    return json.loads(text)


def build_prompt_content(image_b64_list, rubric_text, dimension, task_desc,
                         surface="slides", theme_note=True):
    """Build the user-message content blocks for one dimension's judge.

    Pure / client-free so prompt construction can be verified without an API key.
    Defaults reproduce the slide prompt exactly; documents pass surface="document
    pages", theme_note=False.
    """
    content = [{"type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64}}
               for b64 in image_b64_list]
    lead = f"You are grading the '{dimension}' dimension of generated Cất Cánh {surface}.\n"
    theme = ("The deck may use the light or the dark theme; both are correct, so judge "
             "against the theme the slides actually use.\n") if theme_note else ""
    content.append({"type": "text", "text":
        lead + theme +
        f"Task: {task_desc}\n\nRubric:\n{rubric_text}\n\n"
        "Return JSON {score, justification}. Use \"Unknown\" if you cannot tell."})
    return content


def load_rubrics(dimensions=DIMENSIONS, rubric_dir=RUBRIC_DIR):
    """Read each dimension's rubric Markdown. Raises if a file is missing."""
    return {d: (rubric_dir / f"{d}.md").read_text(encoding="utf-8") for d in dimensions}


def grade_dimension(client, model, image_b64_list, rubric_text, dimension, task_desc,
                    surface="slides", theme_note=True):
    content = build_prompt_content(image_b64_list, rubric_text, dimension, task_desc,
                                   surface=surface, theme_note=theme_note)
    resp = client.messages.create(
        model=model, max_tokens=1024,
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": SCORE_SCHEMA}},
    )
    out = _parse(resp)
    return {"dimension": dimension, "score": out["score"],
            "justification": out["justification"]}


def grade(client, model, image_b64_list, rubrics, task_desc, dimensions=DIMENSIONS,
          surface="slides", theme_note=True):
    dims, scores = {}, {}
    for d in dimensions:
        r = grade_dimension(client, model, image_b64_list, rubrics[d], d, task_desc,
                            surface=surface, theme_note=theme_note)
        dims[d] = r
        scores[d] = None if r["score"] == "Unknown" else int(r["score"])
    return {"dimensions": dims, "scores": scores}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--dry-run", action="store_true",
                    help="Load rubrics and construct prompts without calling the API "
                         "(no ANTHROPIC_API_KEY required).")
    args = ap.parse_args()

    out = Path(args.outdir)
    pngs = sorted((out / "png").glob("page-*.png"))
    imgs = [base64.standard_b64encode(p.read_bytes()).decode() for p in pngs]
    rubrics = load_rubrics()
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    task_desc = task.get("description", "")

    if args.dry_run:
        prompts = {d: build_prompt_content(imgs, rubrics[d], d, task_desc) for d in DIMENSIONS}
        print(json.dumps({
            "dry_run": True,
            "model": args.model,
            "dimensions": DIMENSIONS,
            "images": len(imgs),
            "prompt_text_blocks": {d: blocks[-1]["text"][:120] for d, blocks in prompts.items()},
        }, indent=2, ensure_ascii=False))
        return

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        sys.stderr.write(
            "ANTHROPIC_API_KEY is not set; the rubric grader needs it to call the judge.\n"
            "Set ANTHROPIC_API_KEY, or re-run with --dry-run to verify rubric/prompt "
            "construction without an API call.\n")
        sys.exit(2)

    import anthropic
    res = grade(anthropic.Anthropic(), args.model, imgs, rubrics, task_desc)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
