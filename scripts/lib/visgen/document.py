"""Render a Markdown+front-matter document to an A4 PDF + per-page PNGs via a
vendored, inlined Paged.js polyfill in headless Chromium. Second renderer on the
shared engine: it reuses visgen.tokens / html_render theme assembly / brand_lint
and the Playwright pattern from visgen.canvas. Local-only; no credentials.

This module is import-safe without a browser: Playwright is imported lazily
inside render_doc (added in a later task), so parse_frontmatter / markdown_to_html
can be used and tested standalone."""
import re

import markdown
import yaml

from visgen.schema import SchemaError

DOC_EXTENSIONS = ["extra", "toc", "admonition"]

_FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a leading `--- yaml --- ` block. Returns (meta, body_markdown)."""
    m = _FRONT_MATTER.match(text)
    if not m:
        raise SchemaError("document must start with a YAML front-matter block delimited by '---'")
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise SchemaError("front-matter must be a mapping")
    return meta, text[m.end():]


def markdown_to_html(body_md: str) -> tuple[str, str]:
    """Convert body Markdown to (body_html, toc_html). toc_html is python-markdown's
    <div class="toc"> nav; Paged.js fills its real page numbers via target-counter."""
    md = markdown.Markdown(
        extensions=DOC_EXTENSIONS,
        extension_configs={"toc": {"toc_depth": "1-3"}},
        output_format="html5",
    )
    body_html = md.convert(body_md)
    toc_html = getattr(md, "toc", "") or ""
    return body_html, toc_html
