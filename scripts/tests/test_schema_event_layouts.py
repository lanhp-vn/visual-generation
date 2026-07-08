import sys; sys.path.insert(0, "scripts/lib")
import pytest
from visgen.schema import validate_document, SchemaError


def _doc(layout, content, meta=None):
    return {"meta": {**{"format": "deck-16x9", "title": "t"}, **(meta or {})},
            "slides": [{"layout": layout, "content": content}]}


def test_hero_requires_title():
    with pytest.raises(SchemaError):
        validate_document(_doc("hero", {"eyebrow": "E"}))  # missing title
    validate_document(_doc("hero", {"title": "T"}))  # ok


def test_theme_must_be_valid():
    with pytest.raises(SchemaError):
        validate_document(_doc("hero", {"title": "T"}, {"theme": "blue"}))
    validate_document(_doc("hero", {"title": "T"}, {"theme": "dark"}))


def test_freeform_requires_blocks():
    with pytest.raises(SchemaError):
        validate_document(_doc("freeform", {}))
    validate_document(_doc("freeform", {"blocks": [{"type": "heading", "text": "x"}]}))
