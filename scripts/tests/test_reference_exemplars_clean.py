import re
from pathlib import Path

REFS = Path(__file__).resolve().parents[2] / "scripts/evals/references"


def _doc_exemplars():
    return sorted(REFS.glob("*.md"))


def test_at_least_two_doc_exemplars_present():
    assert len(_doc_exemplars()) >= 2  # cohort report + fellow handbook


def test_no_unresolved_tk_markers():
    """Gated-placeholder rule: a committed exemplar must carry no [TK: ...] markers."""
    offenders = {}
    for md in _doc_exemplars():
        hits = re.findall(r"\bTK:[^\]\n]*", md.read_text(encoding="utf-8"))
        if hits:
            offenders[md.name] = hits
    assert not offenders, f"unresolved TK markers: {offenders}"


def test_no_forbidden_dashes_in_exemplars():
    for md in _doc_exemplars():
        text = md.read_text(encoding="utf-8")
        assert "—" not in text, f"em dash in {md.name}"
        assert "–" not in text, f"en dash in {md.name}"


def test_diacritics_preserved():
    """The program name must keep its diacritics; 'Cat Canh' (stripped) is a defect."""
    for md in _doc_exemplars():
        text = md.read_text(encoding="utf-8")
        assert "Cat Canh" not in text
