import pytest

from visgen.schema import validate_frontmatter, SchemaError
from visgen.document import parse_frontmatter, markdown_to_html, DOC_EXTENSIONS


def test_validate_frontmatter_accepts_report_and_handbook():
    validate_frontmatter({"template": "report", "title": "X"})
    validate_frontmatter({"template": "handbook", "title": "X", "lang": "vi"})


def test_validate_frontmatter_rejects_unknown_template():
    with pytest.raises(SchemaError, match="template"):
        validate_frontmatter({"template": "flyer", "title": "X"})


def test_validate_frontmatter_requires_nonempty_title():
    with pytest.raises(SchemaError, match="title"):
        validate_frontmatter({"template": "report"})
    with pytest.raises(SchemaError, match="title"):
        validate_frontmatter({"template": "report", "title": "  "})


def test_validate_frontmatter_rejects_bad_lang():
    with pytest.raises(SchemaError, match="lang"):
        validate_frontmatter({"template": "report", "title": "X", "lang": "fr"})


def test_parse_frontmatter_splits_yaml_and_body():
    text = "---\ntemplate: report\ntitle: Hello\n---\n\n# Section\n\nBody text.\n"
    meta, body = parse_frontmatter(text)
    assert meta["template"] == "report"
    assert meta["title"] == "Hello"
    assert body.lstrip().startswith("# Section")


def test_parse_frontmatter_requires_fence():
    with pytest.raises(SchemaError):
        parse_frontmatter("# no front-matter here\n")


def test_parse_frontmatter_rejects_non_mapping():
    with pytest.raises(SchemaError):
        parse_frontmatter("---\n- a\n- b\n---\nbody\n")
    with pytest.raises(SchemaError):
        parse_frontmatter("---\nfalse\n---\nbody\n")


def test_parse_frontmatter_empty_block_still_returns_empty_dict():
    meta, body = parse_frontmatter("---\n\n---\nbody\n")
    assert meta == {}
    assert body == "body\n"


def test_doc_extensions_value():
    assert DOC_EXTENSIONS == ["extra", "toc", "admonition"]


def test_markdown_to_html_tables_headings_toc():
    body_html, toc_html = markdown_to_html(
        "# Intro\n\n## Sub\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert "<table>" in body_html
    assert 'id="intro"' in body_html      # toc extension slugs + ids headings
    assert 'href="#intro"' in toc_html    # toc nav links to it


def test_markdown_to_html_admonition_callout():
    body_html, _ = markdown_to_html('!!! warning "Heads up"\n    Be careful.\n')
    assert 'class="admonition warning"' in body_html


def test_markdown_to_html_no_smart_dashes():
    """extra/toc/admonition must not turn -- / --- into en/em dashes (no smarty)."""
    body_html, _ = markdown_to_html("A range 10--20 and a break --- like so.\n")
    assert "–" not in body_html  # en dash
    assert "—" not in body_html  # em dash
