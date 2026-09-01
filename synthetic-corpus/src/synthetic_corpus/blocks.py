"""Block model for synthetic QMS documents.

Own dataclasses/Pydantic models, not shared with (or imported from)
`qms_incub` — see ADR-0012 and docs/shaping/synthetic-doc-realism/SHAPING.md
(C2). A document is a flat list of blocks; headings are `TextBlock`s with a
heading `style`, not a separate section wrapper.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

TextStyle = Literal["h1", "h2", "h3", "body"]


class TextBlock(BaseModel):
    """A heading or a paragraph of prose, distinguished by `style`."""

    type: Literal["text"] = "text"
    style: TextStyle = "body"
    content: str


class TableBlock(BaseModel):
    type: Literal["table"] = "table"
    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None

    @model_validator(mode="after")
    def _rows_match_headers(self) -> TableBlock:
        for row in self.rows:
            if len(row) != len(self.headers):
                raise ValueError(
                    f"table row has {len(row)} cells, expected {len(self.headers)} "
                    f"(one per header)"
                )
        return self


class DiagramStep(BaseModel):
    id: str
    label: str
    lane: str | None = None


DiagramTransition = tuple[str, str]


class FlowchartBlock(BaseModel):
    """A lane-free, top-to-bottom sequence of steps."""

    type: Literal["flowchart"] = "flowchart"
    caption: str | None = None
    steps: list[DiagramStep]
    transitions: list[DiagramTransition] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_lanes_and_valid_transitions(self) -> FlowchartBlock:
        for step in self.steps:
            if step.lane is not None:
                raise ValueError(
                    f"flowchart step {step.id!r} has a lane — flowchart blocks are "
                    f"lane-free; use a swimlane block for lane-assigned steps"
                )
        _validate_transitions(self.steps, self.transitions)
        return self


class SwimLaneBlock(BaseModel):
    """Steps assigned to named lanes, rendered as columns."""

    type: Literal["swimlane"] = "swimlane"
    caption: str | None = None
    lanes: list[str]
    steps: list[DiagramStep]
    transitions: list[DiagramTransition] = Field(default_factory=list)

    @model_validator(mode="after")
    def _lanes_and_transitions_valid(self) -> SwimLaneBlock:
        if len(self.lanes) < 2:
            raise ValueError("swimlane block needs at least 2 lanes — use flowchart otherwise")
        lane_set = set(self.lanes)
        for step in self.steps:
            if step.lane is None:
                raise ValueError(f"swimlane step {step.id!r} has no lane assigned")
            if step.lane not in lane_set:
                raise ValueError(
                    f"swimlane step {step.id!r} references lane {step.lane!r}, "
                    f"not one of {self.lanes!r}"
                )
        _validate_transitions(self.steps, self.transitions)
        return self


def _validate_transitions(steps: list[DiagramStep], transitions: list[DiagramTransition]) -> None:
    step_ids = {step.id for step in steps}
    for from_id, to_id in transitions:
        for step_id in (from_id, to_id):
            if step_id not in step_ids:
                raise ValueError(f"transition references unknown step id {step_id!r}")


Block = Annotated[
    TextBlock | TableBlock | FlowchartBlock | SwimLaneBlock,
    Field(discriminator="type"),
]


class DocumentMeta(BaseModel):
    doc_id: str
    title: str
    version: str = "1.0"
    effective_date: str | None = None
    owner: str | None = None


class Document(BaseModel):
    meta: DocumentMeta
    blocks: list[Block]
