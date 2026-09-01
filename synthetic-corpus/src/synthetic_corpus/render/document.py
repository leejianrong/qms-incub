"""HTML template rendering + WeasyPrint PDF export.

Own template + CSS (Times New Roman, H1/H2/H3 sizes, running header/footer
via CSS Paged Media `@top-center`/`@bottom-center`/`@bottom-left`) — no code
shared with the backend, which has none of this left (ADR-0012).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from synthetic_corpus.blocks import (
    Document,
    FlowchartBlock,
    SwimLaneBlock,
    TableBlock,
    TextBlock,
)
from synthetic_corpus.render.diagrams import render_flowchart_svg, render_swimlane_svg

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_TEXT_TAGS = {"h1": "h1", "h2": "h2", "h3": "h3", "body": "p"}


def _cssescape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=False)
_env.filters["cssescape"] = _cssescape


def render_document_html(document: Document) -> str:
    template = _env.get_template("document.html.jinja")
    body_html = "".join(_render_block(block) for block in document.blocks)
    return template.render(meta=document.meta, body_html=body_html)


def export_document_pdf(document: Document, output_path: Path) -> None:
    html = render_document_html(document)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(output_path))


def _render_block(block: Any) -> str:
    if isinstance(block, TextBlock):
        tag = _TEXT_TAGS[block.style]
        return f"<{tag}>{_escape(block.content)}</{tag}>"
    if isinstance(block, TableBlock):
        return _render_table(block)
    if isinstance(block, FlowchartBlock):
        return _render_figure(render_flowchart_svg(block), block.caption)
    if isinstance(block, SwimLaneBlock):
        return _render_figure(render_swimlane_svg(block), block.caption)
    raise TypeError(f"unknown block type: {type(block)!r}")


def _render_table(block: TableBlock) -> str:
    thead = "".join(f"<th>{_escape(header)}</th>" for header in block.headers)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{_escape(cell)}</td>" for cell in row) + "</tr>"
        for row in block.rows
    )
    caption = f"<figcaption>{_escape(block.caption)}</figcaption>" if block.caption else ""
    return (
        f'<figure class="table-figure">'
        f"<table><thead><tr>{thead}</tr></thead><tbody>{body_rows}</tbody></table>"
        f"{caption}</figure>"
    )


def _render_figure(svg: str, caption: str | None) -> str:
    caption_html = f"<figcaption>{_escape(caption)}</figcaption>" if caption else ""
    return f'<figure class="diagram-figure">{svg}{caption_html}</figure>'


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
