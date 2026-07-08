from visgen.doc_lint import lint_pagination


def test_pagination_flags_all_defect_classes():
    report = {
        "pages": [{"index": 1, "overflow": False}, {"index": 2, "overflow": True}],
        "orphan_headings": [{"text": "Lonely", "page": 3}],
        "toc": [{"href": "#a", "targetPage": 2, "shownPage": 9},
                {"href": "#b", "targetPage": None, "shownPage": None}],
        "chrome": [{"page": 1, "hasHeader": False, "hasFooterNum": False},
                   {"page": 2, "hasHeader": True, "hasFooterNum": True},
                   {"page": 3, "hasHeader": False, "hasFooterNum": True}],
    }
    codes = {v["code"] for v in lint_pagination(report)}
    assert "page-overflow" in codes
    assert "orphan-heading" in codes
    assert "toc-page-mismatch" in codes     # #a shows 9 but target on 2
    assert "toc-dangling" in codes          # #b has no target page
    assert "missing-header" in codes        # page 3 lacks a running header
    # cover (page 1) is exempt from the header/footer requirement:
    assert not any("page 1" in v.get("detail", "") for v in lint_pagination(report))


def test_pagination_clean_report_passes():
    report = {
        "pages": [{"index": 1, "overflow": False}, {"index": 2, "overflow": False}],
        "orphan_headings": [],
        "toc": [{"href": "#a", "targetPage": 2, "shownPage": 2}],
        "chrome": [{"page": 1, "hasHeader": False, "hasFooterNum": False},
                   {"page": 2, "hasHeader": True, "hasFooterNum": True}],
    }
    assert lint_pagination(report) == []


def test_toc_mismatch_only_when_shown_is_a_number():
    """If Paged.js does not surface the shown number, targetPage alone must not trip
    the mismatch check."""
    report = {"pages": [{"index": 1, "overflow": False}], "orphan_headings": [],
              "chrome": [], "toc": [{"href": "#a", "targetPage": 4, "shownPage": None}]}
    assert lint_pagination(report) == []
