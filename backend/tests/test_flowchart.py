import xml.etree.ElementTree as ET

from qms_incub.documents.blocks import FlowchartStep
from qms_incub.documents.flowchart import render_flowchart_svg, steps_to_mermaid

_THREE_STEPS = [
    FlowchartStep(id="a", label="Start", next=["b"]),
    FlowchartStep(id="b", label="Middle", next=["c"]),
    FlowchartStep(id="c", label="End", next=[]),
]


def test_steps_to_mermaid_includes_all_steps_and_edges() -> None:
    mermaid = steps_to_mermaid(_THREE_STEPS)
    assert mermaid.startswith("flowchart TD")
    assert 'a["Start"]' in mermaid
    assert 'b["Middle"]' in mermaid
    assert 'c["End"]' in mermaid
    assert "a --> b" in mermaid
    assert "b --> c" in mermaid


def test_render_flowchart_svg_returns_valid_svg_for_three_steps() -> None:
    svg = render_flowchart_svg(_THREE_STEPS)

    # Valid XML/SVG the PDF exporter can embed.
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")

    assert svg.count("<rect") == 3
    assert "Start" in svg
    assert "Middle" in svg
    assert "End" in svg


def test_render_flowchart_svg_handles_a_branch() -> None:
    steps = [
        FlowchartStep(id="a", label="Review", next=["b", "c"]),
        FlowchartStep(id="b", label="Approved", next=[]),
        FlowchartStep(id="c", label="Rejected", next=[]),
    ]
    svg = render_flowchart_svg(steps)

    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert svg.count("<rect") == 3
    assert svg.count("<line") == 2
