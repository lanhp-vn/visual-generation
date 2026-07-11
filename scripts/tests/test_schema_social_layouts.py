import pytest
from visgen.schema import validate_document, SchemaError


def _doc(layout, content):
    return {"meta": {"format": "square", "theme": "light", "title": "t"},
            "pages": [{"layout": layout, "content": content}]}


def test_social_hero_requires_headline():
    with pytest.raises(SchemaError):
        validate_document(_doc("social-hero", {}))


def test_social_hero_valid():
    validate_document(_doc("social-hero", {"headline": "Cất Cánh", "sub": "x"}))


def test_social_stat_requires_stat_and_label():
    with pytest.raises(SchemaError):
        validate_document(_doc("social-stat", {"stat": "65"}))
    validate_document(_doc("social-stat", {"stat": "65", "label": "Fellows"}))


def test_social_quote_requires_quote():
    with pytest.raises(SchemaError):
        validate_document(_doc("social-quote", {}))
    validate_document(_doc("social-quote", {"quote": "x"}))


def test_social_announce_requires_headline_and_detail():
    with pytest.raises(SchemaError):
        validate_document(_doc("social-announce", {"headline": "h"}))
    validate_document(_doc("social-announce", {"headline": "h", "detail": "d"}))


def test_social_cta_requires_headline_and_cta():
    with pytest.raises(SchemaError):
        validate_document(_doc("social-cta", {"headline": "h"}))
    validate_document(_doc("social-cta", {"headline": "h", "cta": "Apply"}))
