"""Canvas formats registry — the sizes from the design kit's output specs
(references/visemi-internal/design-kit-visemi/04-output-specs.md). Every canvas
render resolves its stage size here; nothing else hardcodes pixel dimensions."""

FORMATS = {
    # slides / one-pagers
    "deck-16x9": (1920, 1080),
    "one-pager-landscape": (1920, 1080),
    # social posts
    "square": (1080, 1080),
    "portrait": (1080, 1350),
    "story": (1080, 1920),
    "link": (1200, 627),
    # posters / event graphics
    "poster-a": (1240, 1748),
    "banner-wide": (2048, 1448),
    "email-header": (1200, 400),
}


def page_px(fmt: str) -> tuple[int, int]:
    try:
        return FORMATS[fmt]
    except KeyError:
        raise ValueError(f"unknown format {fmt!r}; known: {sorted(FORMATS)}") from None
