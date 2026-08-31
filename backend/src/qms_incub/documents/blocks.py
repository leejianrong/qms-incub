"""Block model for policy documents (ADR-0001, ADR-0006).

A `PolicyDocument` is an ordered list of typed blocks. This is the single
model shared by hand-authoring (V4) and synthetic batch generation (V5);
V1 seeds one document directly in Python since the composer UI doesn't
exist yet.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    content: str


class TableBlock(BaseModel):
    type: Literal["table"] = "table"
    headers: list[str]
    rows: list[list[str]]


class FlowchartStep(BaseModel):
    id: str
    label: str
    # IDs of steps that follow this one. More than one entry models a
    # branch/decision point (ADR-0006); empty means a terminal step.
    next: list[str] = Field(default_factory=list)


class FlowchartBlock(BaseModel):
    type: Literal["flowchart"] = "flowchart"
    steps: list[FlowchartStep]


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    alt_text: str
    # Embedded directly (data: URI) so the document has no external file
    # dependency at render/export time.
    data_uri: str


Block = Annotated[
    TextBlock | TableBlock | FlowchartBlock | ImageBlock,
    Field(discriminator="type"),
]


class PolicyDocument(BaseModel):
    id: str
    title: str
    blocks: list[Block]
    origin: Literal["generated", "imported"] = "generated"
    is_synthetic: bool = False
    source_attribution: str | None = None
