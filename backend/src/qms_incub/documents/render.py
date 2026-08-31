"""Block model -> HTML (ADR-0001). Flowchart blocks resolve to inline SVG
(ADR-0006) before this HTML ever reaches the PDF exporter (ADR-0010)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from qms_incub.documents.blocks import PolicyDocument
from qms_incub.documents.flowchart import render_flowchart_svg

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_document_html(document: PolicyDocument) -> str:
    rendered_blocks: list[dict[str, Any]] = []
    for block in document.blocks:
        if block.type == "flowchart":
            rendered_blocks.append(
                {"type": "flowchart", "svg": render_flowchart_svg(block.steps)}
            )
        else:
            rendered_blocks.append(block.model_dump())

    template = _env.get_template("document.html.jinja")
    return template.render(title=document.title, blocks=rendered_blocks)
