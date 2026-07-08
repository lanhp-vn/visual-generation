from visgen.brand_lint import lint_html, lint_render_report, lint

CLEAN = '<style>:root{--navy:#001669}</style><p style="font-family:Be Vietnam Pro">Cất Cánh $150K</p>'


def test_clean_html_no_violations():
    assert lint_html(CLEAN, required_strings=["$150K", "Cất Cánh"]) == []


def test_offbrand_hex_flagged():
    v = lint_html('<div style="color:#ff0000"></div>')
    assert any(x["code"] == "offbrand-hex" for x in v)


def test_em_dash_flagged():
    v = lint_html("<p>a — b</p>")
    assert any(x["code"] == "em-dash" for x in v)


def test_missing_required_string_flagged():
    v = lint_html("<p>hello</p>", required_strings=["$150K"])
    assert any(x["code"] == "missing-required" and "$150K" in x["detail"] for x in v)


def test_offbrand_font_flagged():
    v = lint_html('<p style="font-family:Comic Sans MS">x</p>')
    assert any(x["code"] == "offbrand-font" for x in v)


def test_overflow_flagged():
    report = {"page_px": [1920, 1080],
              "slides": [{"index": 1, "overflow": True, "width": 1920, "height": 1080}]}
    v = lint_render_report(report, expected_page_px=[1920, 1080])
    assert any(x["code"] == "overflow" for x in v)


def test_lint_aggregates_passed_flag():
    res = lint(CLEAN, required_strings=["Cất Cánh"])
    assert res["passed"] is True and res["violations"] == []
