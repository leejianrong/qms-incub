"""Unit tests for the SVG diagram layout (Slice 1 test plan)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from synthetic_corpus.blocks import DiagramStep, FlowchartBlock, SwimLaneBlock
from synthetic_corpus.render.diagrams import (
    _COL_WIDTH,
    _MARGIN,
    render_flowchart_svg,
    render_swimlane_svg,
)

_SVG_NS = "{http://www.w3.org/2000/svg}"
_STEP_BOX_FILL = "#fff"
_LANE_HEADER_FILL = "#e8e8e8"


def _step_box_x_positions(svg: str) -> list[float]:
    root = ET.fromstring(svg)
    return [
        float(rect.get("x"))  # type: ignore[arg-type]
        for rect in root.iter(f"{_SVG_NS}rect")
        if rect.get("fill") == _STEP_BOX_FILL
    ]


def _lane_header_count(svg: str) -> int:
    root = ET.fromstring(svg)
    return sum(1 for rect in root.iter(f"{_SVG_NS}rect") if rect.get("fill") == _LANE_HEADER_FILL)


def test_swimlane_places_steps_under_correct_lane_column() -> None:
    steps = [
        DiagramStep(id="s1", label="Submit request", lane="Requester"),
        DiagramStep(id="s2", label="Triage request", lane="Reviewer"),
        DiagramStep(id="s3", label="Approve request", lane="Approver"),
        DiagramStep(id="s4", label="Reject request", lane="Approver"),
        DiagramStep(id="s5", label="Notify requester", lane="Reviewer"),
        DiagramStep(id="s6", label="Close request", lane="Requester"),
    ]
    block = SwimLaneBlock(
        lanes=["Requester", "Reviewer", "Approver"],
        steps=steps,
        transitions=[
            ("s1", "s2"),
            ("s2", "s3"),
            ("s2", "s4"),
            ("s3", "s5"),
            ("s4", "s5"),
            ("s5", "s6"),
        ],
    )

    svg = render_swimlane_svg(block)
    xs = _step_box_x_positions(svg)

    assert len(xs) == 6
    lane_index = {"Requester": 0, "Reviewer": 1, "Approver": 2}
    for step, x in zip(steps, xs, strict=True):
        assert x == _MARGIN + lane_index[step.lane] * _COL_WIDTH  # type: ignore[index]
    assert _lane_header_count(svg) == 3


def test_flowchart_renders_single_top_to_bottom_column_with_no_lanes() -> None:
    steps = [DiagramStep(id=f"s{i}", label=f"Step {i}") for i in range(4)]
    block = FlowchartBlock(
        steps=steps,
        transitions=[(f"s{i}", f"s{i + 1}") for i in range(3)],
    )

    svg = render_flowchart_svg(block)
    xs = _step_box_x_positions(svg)

    assert xs == [_MARGIN] * 4
    assert _lane_header_count(svg) == 0
