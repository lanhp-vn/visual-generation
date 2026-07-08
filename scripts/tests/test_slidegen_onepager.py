import json
from pathlib import Path
from visgen.html_render import render_document

DOC = json.loads((Path(__file__).resolve().parents[2] /
                  "scripts/evals/references/one-pager.content.json").read_text(encoding="utf-8"))


def test_onepager_renders():
    html = render_document(DOC)
    assert html.count('class="slide') == 1


def test_key_facts_present():
    html = render_document(DOC)
    for fact in ["The Gaps", "The Bridge", "The Impacts", "7x to 20x ROI",
                 "15", "150", "$15K", "Cất Cánh (Takeoff) Fellowship"]:
        assert fact in html, fact
