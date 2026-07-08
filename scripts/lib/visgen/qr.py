"""URL -> responsive QR SVG (segno).

Renders a URL to a self-contained SVG string with navy modules, then post-processes
it into a responsive shape: strips the XML declaration, adds a viewBox derived from
the intrinsic width/height, and sets width/height to 100% so the QR fills whatever
box the layout gives it. Mirrors the regex post-processing in the original
programs/kickoff-meeting/slides/render_kickoff.py.
"""
import io
import re

import segno

from visgen.tokens import load_tokens

_OPEN_SVG = re.compile(r"<svg\b([^>]*)>")
_XMLDECL = re.compile(r"<\?xml[^>]*\?>\s*")


def qr_svg(url: str, dark: str | None = None, scale: int = 12, border: int = 2) -> str:
    """Return a responsive, self-contained QR SVG for ``url``.

    ``dark`` colours the QR modules (navy from brand/tokens.json by default);
    ``scale`` and ``border`` control the intrinsic module size and quiet-zone.
    The returned <svg> carries a viewBox and width="100%" height="100%" so it
    scales to its container.
    """
    if dark is None:
        dark = load_tokens()["themes"]["light"]["--navy"]
    qr = segno.make(url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, border=border, dark=dark, xmldecl=False)
    svg = buf.getvalue().decode("utf-8")

    # Strip any leftover XML declaration.
    svg = _XMLDECL.sub("", svg)

    # Rewrite the opening <svg ... width="N" height="N"> into a responsive tag:
    # keep all other attributes, drop the literal width/height, add a viewBox
    # derived from them, and set width/height to 100%.
    m = _OPEN_SVG.search(svg)
    if m:
        attrs = m.group(1)
        wm = re.search(r'width="(\d+)"', attrs)
        hm = re.search(r'height="(\d+)"', attrs)
        if wm and hm:
            attrs2 = re.sub(r'(width|height)="\d+"', "", attrs)
            attrs2 += f' viewBox="0 0 {wm.group(1)} {hm.group(1)}" width="100%" height="100%"'
            svg = svg.replace(m.group(0), f"<svg{attrs2}>", 1)

    return svg.strip()
