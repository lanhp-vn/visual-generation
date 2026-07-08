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


def test_script_content_is_exempt_but_body_still_scanned():
    # Forbidden dash tokens built via chr() (U+2014, U+2013) so this file
    # stays free of raw em/en dash characters.
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)

    # Off-brand hex, off-brand font, and em/en dash inside a <script> block
    # (vendored Paged.js polyfill internals) must NOT be flagged...
    script_html = (
        "<script>"
        "var c = '#00ff00';"
        "var f = 'font-family: <family-name> | unset';"
        f"var s = 'a {em_dash} b, c {en_dash} d';"
        "</script>"
    )
    v = lint_html(script_html)
    codes = {x["code"] for x in v}
    assert codes.isdisjoint({"offbrand-hex", "offbrand-font", "em-dash", "en-dash"})

    # ...but the same tokens outside a script, in authored markup, still are.
    body_html = f'<div style="color:#00ff00">a {em_dash} b</div>'
    v2 = lint_html(body_html)
    codes2 = {x["code"] for x in v2}
    assert "offbrand-hex" in codes2
    assert "em-dash" in codes2
