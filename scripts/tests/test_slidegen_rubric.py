import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("grade_rubric", ROOT / "scripts/ops/grade_rubric.py")
gr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gr)


class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text):
        self.content = [_Block(text)]


class FakeClient:
    """Returns a canned score; records how many create() calls were made."""
    def __init__(self, text):
        self._text = text
        self.calls = 0

        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.calls += 1
                return _Resp(outer._text)

        self.messages = _Messages()


def test_grade_dimension_parses_score():
    fake = FakeClient(json.dumps({"score": "4", "justification": "good"}))
    out = gr.grade_dimension(fake, "claude-opus-4-8", ["AAAA"], "rubric", "brand", "task")
    assert out["dimension"] == "brand" and out["score"] == "4"


def test_unknown_is_allowed():
    fake = FakeClient(json.dumps({"score": "Unknown", "justification": "cannot tell"}))
    out = gr.grade_dimension(fake, "claude-opus-4-8", ["AAAA"], "rubric", "layout", "task")
    assert out["score"] == "Unknown"


def test_grade_runs_one_call_per_dimension():
    fake = FakeClient(json.dumps({"score": "5", "justification": "ok"}))
    rubrics = {d: "r" for d in gr.DIMENSIONS}
    res = gr.grade(fake, "claude-opus-4-8", ["AAAA"], rubrics, "task")
    assert fake.calls == len(gr.DIMENSIONS)
    assert res["scores"]["brand"] == 5
    assert set(res["dimensions"]) == set(gr.DIMENSIONS)
