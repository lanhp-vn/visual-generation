import pytest
from visgen.schema import validate_document, SchemaError, LAYOUTS, VALID_FORMATS

GOOD = {
    "meta": {"lang": "en", "audience": "donors", "format": "deck-16x9", "title": "T"},
    "slides": [
        {"layout": "title", "content": {"title": "X", "subtitle_vi": "a",
                                        "subtitle_en": "b", "footer": "f"}},
    ],
}


def test_good_document_passes():
    validate_document(GOOD)  # no raise


def test_unknown_format_raises():
    # "square" was invalid in the donor's 2-format set; visgen's FORMATS registry
    # (Task 1-4) legitimizes it for social posts, so use a format unknown everywhere.
    bad = {**GOOD, "meta": {**GOOD["meta"], "format": "a3-poster"}}
    with pytest.raises(SchemaError, match="format"):
        validate_document(bad)


def test_unknown_layout_raises():
    bad = {"meta": GOOD["meta"], "slides": [{"layout": "nope", "content": {}}]}
    with pytest.raises(SchemaError, match="layout"):
        validate_document(bad)


def test_missing_required_field_raises():
    bad = {"meta": GOOD["meta"],
           "slides": [{"layout": "title", "content": {"title": "X"}}]}
    with pytest.raises(SchemaError, match="subtitle_vi"):
        validate_document(bad)


def test_no_slides_raises():
    with pytest.raises(SchemaError, match="slides"):
        validate_document({"meta": GOOD["meta"], "slides": []})


def test_donor_layouts_registered():
    # The original donor deck / one-pager layouts must stay registered untouched.
    assert {"title", "gaps-bridge", "pillars-tiers",
            "impact-roi", "donor-tiers", "one-pager-3col"} <= set(LAYOUTS)


def test_event_layouts_registered():
    # Event-deck layouts added by the visgen upgrade.
    assert {"hero", "stat-grid", "agenda", "icon-cards", "people",
            "timeline-phases", "columns", "cta-qr", "quote",
            "section-divider", "freeform"} <= set(LAYOUTS)


def test_pages_key_preferred_and_slides_alias_accepted():
    from visgen.schema import validate_document, document_pages
    base = {"meta": {"format": "deck-16x9"},
            "pages": [{"layout": "hero", "content": {"title": "Hi"}}]}
    validate_document(base)  # no raise
    legacy = {"meta": {"format": "deck-16x9"},
              "slides": [{"layout": "hero", "content": {"title": "Hi"}}]}
    validate_document(legacy)  # no raise
    assert document_pages(base) == base["pages"]
    assert document_pages(legacy) == legacy["slides"]
