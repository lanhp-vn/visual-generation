"""Brand-lint palette upgrade tests (Task 17).

The event-deck system sanctions the gold accent (#F5B433 and its token shades)
and a dark theme (deep-navy token hexes). The deterministic brand-lint must:
  - allow the gold hexes and the dark-theme token hexes in authored markup,
  - exempt decoration sparkles (<svg class="spark">) and the .qrbox QR SVG and
    any vendored <style>/<svg> from the off-brand-hex scan,
  - KEEP the em/en-dash, emoji, off-brand-font and (elsewhere) page-size /
    overflow / diacritics checks.

The real public entry point is `lint_html` (the plan's `check_palette` was a
placeholder name). `_offbrand_hexes` is a thin helper around it that returns the
off-brand hex violations only, so the palette assertions read cleanly.
"""

from visgen.brand_lint import lint_html


def _offbrand_hexes(html):
    """Off-brand-hex violation details for `html` (palette scan only)."""
    return [v["detail"] for v in lint_html(html) if v["code"] == "offbrand-hex"]


def _codes(html):
    return {v["code"] for v in lint_html(html)}


# ---- gold accent is sanctioned --------------------------------------------

def test_gold_fill_is_allowed():
    assert _offbrand_hexes('<span style="color:#F5B433">x</span>') == []


def test_gold_shades_are_allowed():
    for hx in ("#D99A1F", "#FBD27A"):
        assert _offbrand_hexes(f'<span style="color:{hx}">x</span>') == [], hx


# ---- dark-theme token hexes are sanctioned --------------------------------

def test_dark_bg_hex_allowed():
    assert _offbrand_hexes('<div style="background:#000B26"></div>') == []


def test_dark_theme_token_hexes_allowed():
    for hx in ("#001152", "#00091F", "#0d2156", "#0a2470", "#EAF0FF", "#B9C4E0", "#8FA0C8"):
        assert _offbrand_hexes(f'<div style="background:{hx}"></div>') == [], hx


# ---- decoration / QR SVG are exempt from the palette scan ------------------

def test_spark_decoration_svg_is_exempt():
    # An off-palette hex inside a decoration sparkle must NOT be flagged.
    spark = '<svg class="spark" viewBox="0 0 24 24"><path fill="#123456" d="M0 0Z"/></svg>'
    assert "offbrand-hex" not in _codes(spark)


def test_qrbox_qr_svg_is_exempt():
    # The QR module SVG (navy modules) lives in .qrbox and must be exempt.
    qr = ('<div class="qrbox"><svg viewBox="0 0 100 100">'
          '<rect fill="#001669" width="10" height="10"/></svg></div>')
    assert "offbrand-hex" not in _codes(qr)


def test_vendored_style_block_is_exempt():
    # A <style> block (vendored theme CSS) is never palette-scanned.
    assert _offbrand_hexes('<style>:root{--x:#ABCDEF}</style>') == []


# ---- non-brand colour is still flagged ------------------------------------

def test_random_color_flagged():
    assert "#FF00AA" in _offbrand_hexes('<span style="color:#FF00AA">x</span>')


# ---- text-quality checks are preserved ------------------------------------

def test_em_dash_still_flagged():
    assert "em-dash" in _codes("<p>Hello — world</p>")  # U+2014 em dash


def test_en_dash_still_flagged():
    assert "en-dash" in _codes("<p>2024 – 2025</p>")  # U+2013 en dash


def test_lint_palette_is_tokens_palette():
    """Lint allowlist and theme tokens cannot drift: same function, same set."""
    from visgen.brand_lint import BRAND_HEX
    from visgen.tokens import palette
    assert BRAND_HEX == palette()

def test_gold_and_house_hexes_allowed():
    from visgen.brand_lint import lint_html
    ok = '<div style="color:#01B68B;background:#F5B433;border-color:#001669">x</div>'
    assert lint_html(ok) == []
    bad = '<div style="color:#FF00AA">x</div>'
    assert any(v["code"] == "offbrand-hex" for v in lint_html(bad))
