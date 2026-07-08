#!/usr/bin/env python3
"""Eval harness: run each task's content through render + graders for k trials,
record transcripts, aggregate pass@k / pass^k. Anthropic-style: grade the output,
clean isolated dir per trial, read the transcripts.

Usage: uv run python scripts/evals/run_evals.py [--trials N] [--judge] [--out DIR]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
from visgen.brand_lint import lint  # noqa: E402
from visgen.formats import page_px  # noqa: E402


def metrics(per_trial_pass, k):
    passes = list(per_trial_pass)[:k]
    return {"pass_at_k": 1.0 if any(passes) else 0.0,
            "pass_caret_k": 1.0 if passes and all(passes) else 0.0}


def _render(content_path, out_dir):
    subprocess.run([sys.executable, str(ROOT / "scripts/ops/render_canvas.py"),
                    str(ROOT / content_path), "--format", "both", "--out", str(out_dir)],
                   check=True, cwd=str(ROOT))


def run_task(task, k, out_root, judge=False):
    trial_results = []
    for t in range(1, k + 1):
        trial_dir = out_root / task["id"] / f"trial-{t:02d}"
        trial_dir.mkdir(parents=True, exist_ok=True)
        _render(task["content"], trial_dir)
        html = (trial_dir / "index.html").read_text(encoding="utf-8")
        report = json.loads((trial_dir / "render_report.json").read_text(encoding="utf-8"))
        brand = lint(html, report,
                     required_strings=task.get("required_strings", []),
                     forbidden_strings=task.get("forbidden_strings", []),
                     expected_page_px=task.get("expected_page_px"))
        transcript = {"task": task["id"], "trial": t, "brand": brand}
        if judge:
            transcript["rubric"] = _judge(task, trial_dir)
        (trial_dir / "transcript.json").write_text(
            json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
        trial_results.append(brand["passed"])
    return {"task": task["id"], "trials": k, "brand_pass": trial_results,
            **metrics(trial_results, k)}


def _judge(task, trial_dir):
    import base64
    import importlib.util
    spec = importlib.util.spec_from_file_location("grade_rubric", ROOT / "scripts/ops/grade_rubric.py")
    gr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gr)
    import anthropic
    pngs = sorted((trial_dir / "png").glob("page-*.png"))
    imgs = [base64.standard_b64encode(p.read_bytes()).decode() for p in pngs]
    rubric_dir = ROOT / "scripts/evals/rubrics"
    rubrics = {d: (rubric_dir / f"{d}.md").read_text(encoding="utf-8") for d in gr.DIMENSIONS}
    return gr.grade(anthropic.Anthropic(), "claude-opus-4-8", imgs, rubrics, task["description"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", action="append", help="Task file(s); default: all in scripts/evals/tasks/.")
    ap.add_argument("--trials", type=int, default=None, help="Override the task's trial count.")
    ap.add_argument("--judge", action="store_true", help="Also run the LLM-judge rubric.")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.task:
        task_files = [Path(t) for t in args.task]
    else:
        # Discover both the donor tasks (*.task.json) and the event-deck tasks
        # (event-*.json), excluding the _fixtures/ content used by the latter.
        tasks_dir = ROOT / "scripts/evals/tasks"
        task_files = sorted(
            {p for p in (*tasks_dir.glob("*.task.json"), *tasks_dir.glob("event-*.json"))}
        )
    out_root = Path(args.out) if args.out else ROOT / "scripts" / "evals" / "runs" / "latest"
    out_root.mkdir(parents=True, exist_ok=True)

    tasks = [json.loads(tf.read_text(encoding="utf-8")) for tf in task_files]

    # Regression-cover every reference exemplar. Donor references are already
    # exercised through their *.task.json descriptors; for any reference without
    # an explicit task (e.g. the kickoff light/dark exemplars), synthesize a
    # brand-only regression task so it is rendered + brand-linted alongside the
    # donor ones.
    if not args.task:
        covered = {Path(t["content"]).as_posix() for t in tasks}
        for ref in sorted((ROOT / "scripts/evals/references").glob("*.content.json")):
            rel = ref.relative_to(ROOT).as_posix()
            if rel in covered:
                continue
            doc_meta = json.loads(ref.read_text(encoding="utf-8"))["meta"]
            tasks.append({
                "id": f"ref-{ref.name[:-len('.content.json')]}",
                "description": f"Regression: render + brand-lint reference exemplar {ref.name}.",
                "content": rel,
                "expected_page_px": list(page_px(doc_meta["format"])),
                "trials": 1,
            })

    agg = []
    for task in tasks:
        k = args.trials or task.get("trials", 1)
        agg.append(run_task(task, k, out_root, judge=args.judge))
    (out_root / "aggregate.json").write_text(json.dumps(agg, indent=2, ensure_ascii=False),
                                             encoding="utf-8")
    print(json.dumps(agg, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
