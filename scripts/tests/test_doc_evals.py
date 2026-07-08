import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_doc_dimensions_and_rubric_files():
    gr = _load("grade_rubric", "scripts/ops/grade_rubric.py")
    assert gr.DOC_DIMENSIONS == ["doc-pagination", "toc-usefulness"]
    for d in gr.DOC_DIMENSIONS:
        assert (ROOT / f"scripts/evals/rubrics/{d}.md").is_file()


def test_doc_prompt_drops_theme_and_names_documents():
    gr = _load("grade_rubric", "scripts/ops/grade_rubric.py")
    doc_blocks = gr.build_prompt_content(["QQ=="], "RUBRIC", "toc-usefulness", "task",
                                         surface="document pages", theme_note=False)
    text = doc_blocks[-1]["text"]
    assert "document pages" in text
    assert "dark theme" not in text
    # slide default is unchanged (M1 behavior preserved):
    slide_blocks = gr.build_prompt_content(["QQ=="], "RUBRIC", "layout", "task")
    assert "generated Cất Cánh slides" in slide_blocks[-1]["text"]
    assert "the dark theme" in slide_blocks[-1]["text"]


def test_run_evals_grades_a_doc_task(tmp_path):
    ev = _load("run_evals", "scripts/evals/run_evals.py")
    task = {"id": "doc-tiny", "renderer": "doc",
            "content": "scripts/tests/fixtures/docs/tiny.md",
            "description": "Regression: tiny report renders + doc-lint.", "trials": 1}
    res = ev.run_task(task, 1, tmp_path)
    assert res["pass_at_k"] == 1.0
    assert res["brand_pass"] == [True]
