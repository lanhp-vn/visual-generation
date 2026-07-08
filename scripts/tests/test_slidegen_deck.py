import json
from pathlib import Path
from visgen.html_render import render_document

DOC = json.loads((Path(__file__).resolve().parents[2] /
                  "scripts/evals/references/pitch-deck.content.json").read_text(encoding="utf-8"))


def test_deck_has_five_slides():
    assert len(DOC["slides"]) == 5
    html = render_document(DOC)
    assert html.count('class="slide') == 5


def test_deck_key_facts_present():
    html = render_document(DOC)
    for fact in ["Cất Cánh (Takeoff) Fellowship Introduction",
                 "6-Month Accelerator Program", "Tiered Financial Support",
                 "Transformative Impact", "Partner With Us",
                 "$70,000", "$200,000", "$50,000+", "501(c)(3)"]:
        assert fact in html, fact
