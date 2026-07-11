import pytest
from visgen.schema import validate_document, SchemaError


def _doc(layout, content, fmt="poster-a"):
    return {"meta": {"format": fmt, "theme": "light", "title": "t"},
            "pages": [{"layout": layout, "content": content}]}


def test_poster_event_requires_title_when_where():
    with pytest.raises(SchemaError):
        validate_document(_doc("poster-event", {"title": "x", "when": "y"}))
    validate_document(_doc("poster-event", {"title": "x", "when": "y", "where": "z"}))


def test_banner_headline_requires_headline():
    with pytest.raises(SchemaError):
        validate_document(_doc("banner-headline", {}, fmt="banner-wide"))
    validate_document(_doc("banner-headline", {"headline": "Cất Cánh"}, fmt="banner-wide"))


def test_email_header_requires_headline():
    with pytest.raises(SchemaError):
        validate_document(_doc("email-header", {}, fmt="email-header"))
    validate_document(_doc("email-header", {"headline": "h"}, fmt="email-header"))
