import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "skills/generate-doc/SKILL.md"


def test_skill_present_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^name:\s*generate-doc\s*$", text, re.M)
    assert "description:" in text


def test_skill_documents_contract_and_commands():
    text = SKILL.read_text(encoding="utf-8")
    for token in ("template", "report", "handbook", "front-matter",
                  "scripts/ops/render_doc.py", "scripts/ops/grade_doc.py",
                  "admonition", "brand/tokens.json"):
        assert token in text, f"SKILL.md should mention {token!r}"


def test_skill_has_no_forbidden_dashes():
    text = SKILL.read_text(encoding="utf-8")
    assert "—" not in text and "–" not in text  # no em/en dash
