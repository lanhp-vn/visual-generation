"""Deterministic brand conformance checks on generated slide HTML + render report.
Grades the produced artifact, not the path that produced it.

Off-brand hex / font checks run on the AUTHORED markup only: vendored <style>
blocks (base.css default tokens, the VISEMI theme, embedded fonts) and vendored
<svg> artwork (logos, icons — which carry the official logo's own hex stops),
plus the decoration sparkles (<svg class="spark">) and the .qrbox QR module SVG,
are trusted and stripped before scanning, so only inline styles in the slide
body are linted. Inlined <script> content (e.g. the vendored Paged.js polyfill
embedded in M2 document HTML) is likewise trusted, non-authored markup and is
stripped like <style>: script content is behavior, not brand surface, and
brand values live in tokens/CSS by convention, never in JS.

Palette: every hex named in brand/tokens.json (all theme token values) plus its
extra_allowed_hexes; any other hex is flagged. Em dash (U+2014) and en dash
(U+2013) in visible text are flagged; full Vietnamese diacritics are required
(they pass through untouched)."""
import re

from visgen.tokens import palette

BRAND_HEX = palette()
ALLOWED_FONTS = {"be vietnam pro", "inter", "sans-serif"}
_STYLE = re.compile(r"<style\b[^>]*>.*?</style>", re.S | re.I)
# Inlined <script> (vendored Paged.js polyfill in M2 doc HTML) is trusted like
# <style>: it's behavior, not brand surface, so its hex/font/dash content
# (library internals, not authored content) must not reach the scan below.
_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)
_SVG = re.compile(r"<svg\b[^>]*>.*?</svg>", re.S | re.I)
# Decoration sparkles and the QR module SVG carry their own (non-brand) hexes and
# are not part of the authored brand surface; exempt them explicitly so a future
# narrowing of the generic <svg> strip can't regress the palette scan on them.
_SPARK_SVG = re.compile(r'<svg\b[^>]*class="[^"]*\bspark\b[^"]*"[^>]*>.*?</svg>', re.S | re.I)
_QRBOX = re.compile(r'<div\b[^>]*class="[^"]*\bqrbox\b[^"]*"[^>]*>.*?</div>', re.S | re.I)
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
_FONT = re.compile(r"font-family\s*:\s*([^;\"'}]+)", re.I)
_TAGS = re.compile(r"<[^>]+>")


def lint_html(html, required_strings=(), forbidden_strings=()):
    violations = []
    # Drop trusted, non-authored markup before the palette/font scan:
    # vendored CSS (<style>), inlined <script> (vendored Paged.js polyfill),
    # all SVG artwork (logos/icons/sparkles/QR), and the .qrbox QR container
    # (decoration sparkles and the QR module SVG explicitly).
    authored = _QRBOX.sub("", _SPARK_SVG.sub("", _SVG.sub("", _SCRIPT.sub("", _STYLE.sub("", html)))))
    for hx in set(_HEX.findall(authored)):
        if hx.lower() not in BRAND_HEX:
            violations.append({"code": "offbrand-hex", "detail": hx})
    for decl in _FONT.findall(authored):
        families = [f.strip().strip("\"'").lower() for f in decl.split(",")]
        for fam in families:
            if fam and fam not in ALLOWED_FONTS:
                violations.append({"code": "offbrand-font", "detail": fam})
    text = _TAGS.sub("", authored)
    if "—" in text:  # em dash
        violations.append({"code": "em-dash", "detail": "em dash in visible text"})
    if "–" in text:  # en dash
        violations.append({"code": "en-dash", "detail": "en dash in visible text"})
    for s in required_strings:
        if s not in html:
            violations.append({"code": "missing-required", "detail": s})
    for s in forbidden_strings:
        if s in text:
            violations.append({"code": "forbidden-present", "detail": s})
    return violations


def lint_render_report(report, expected_page_px=None):
    violations = []
    if expected_page_px and report.get("page_px") != list(expected_page_px):
        violations.append({"code": "wrong-page-size",
                           "detail": f'{report.get("page_px")} != {expected_page_px}'})
    for s in report.get("pages", report.get("slides", [])):
        if s.get("overflow"):
            violations.append({"code": "overflow", "detail": f'slide {s.get("index")}'})
    return violations


def lint(html, report=None, required_strings=(), forbidden_strings=(), expected_page_px=None):
    v = lint_html(html, required_strings, forbidden_strings)
    if report is not None:
        v += lint_render_report(report, expected_page_px)
    return {"passed": not v, "violations": v}
