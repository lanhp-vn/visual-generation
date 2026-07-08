import pytest
from visgen.formats import FORMATS, page_px

def test_registry_matches_output_specs():
    assert page_px("deck-16x9") == (1920, 1080)
    assert page_px("one-pager-landscape") == (1920, 1080)
    assert page_px("square") == (1080, 1080)
    assert page_px("portrait") == (1080, 1350)
    assert page_px("story") == (1080, 1920)
    assert page_px("link") == (1200, 627)
    assert page_px("poster-a") == (1240, 1748)
    assert page_px("banner-wide") == (2048, 1448)
    assert page_px("email-header") == (1200, 400)
    assert len(FORMATS) == 9

def test_unknown_format_raises_with_known_keys():
    with pytest.raises(ValueError, match="deck-16x9"):
        page_px("a3-poster")
