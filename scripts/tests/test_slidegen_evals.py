import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("run_evals", ROOT / "scripts/evals/run_evals.py")
re_ = importlib.util.module_from_spec(spec)
spec.loader.exec_module(re_)


def test_metrics_all_pass():
    m = re_.metrics([True, True, True], k=3)
    assert m["pass_at_k"] == 1.0 and m["pass_caret_k"] == 1.0


def test_metrics_partial():
    m = re_.metrics([True, False, False], k=3)
    assert m["pass_at_k"] == 1.0 and m["pass_caret_k"] == 0.0


def test_metrics_none():
    m = re_.metrics([False, False], k=2)
    assert m["pass_at_k"] == 0.0 and m["pass_caret_k"] == 0.0
