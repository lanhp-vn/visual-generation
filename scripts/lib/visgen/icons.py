"""Brand icon set: semantic names mapped to vendored Lucide SVGs, recolored
via currentColor so the surrounding CSS controls navy/green."""
import re
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parents[3] / "brand/icons"

ICONS = {
    "globe": "globe", "grad-cap": "graduation-cap", "alert": "triangle-alert",
    "target": "target", "grad-cap-dollar": "graduation-cap", "network": "share-2",
    "flywheel": "recycle", "rocket": "rocket", "clipboard": "clipboard-list",
    "presentation": "presentation", "users": "users", "chip": "cpu",
    # Event-deck semantic icons (Lucide-style stroke SVGs).
    "message": "message-square", "chat": "message-square",
    "calendar": "calendar", "compass": "compass", "flag": "flag",
}

_OPEN_SVG = re.compile(r"<svg\b[^>]*>")


def render_icon(name: str, css_class: str = "icon") -> str:
    """Return the icon as an inline <svg> with the given class. KeyError if unknown."""
    stem = ICONS[name]  # raises KeyError on unknown name
    raw = (ICONS_DIR / f"{stem}.svg").read_text(encoding="utf-8")
    # Force our class onto the root <svg>; strip width/height/fill/stroke so the
    # .icon CSS (1em, currentColor) governs sizing and color.
    new_open = f'<svg class="{css_class}" aria-hidden="true" focusable="false"'
    raw = _OPEN_SVG.sub(lambda m: _rewrite_open(m.group(0), new_open), raw, count=1)
    return raw.strip()


def _rewrite_open(tag: str, new_open: str) -> str:
    keep = ""
    m = re.search(r'viewBox="[^"]*"', tag)
    if m:
        keep = " " + m.group(0)
    return f"{new_open}{keep}>"
