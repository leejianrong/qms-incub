"""Hand-written demo document for Slice 1: one lane-free flowchart block and
one 3-lane swim-lane block, plus enough prose to span multiple pages — used
by both `scripts/demo.py` (visual check) and the PDF-export integration test.
"""

from __future__ import annotations

from synthetic_corpus.blocks import (
    DiagramStep,
    Document,
    DocumentMeta,
    FlowchartBlock,
    SwimLaneBlock,
    TableBlock,
    TextBlock,
)

_FILLER_PARAGRAPH = (
    "This section exists purely to push the demo document past a single page "
    "so the running header and footer can be checked on more than one page. "
    "It restates the same idea in slightly different words each time: a "
    "policy document of this length is typical for a large-company QMS "
    "procedure, and pagination should look correct throughout."
)


def build_demo_document() -> Document:
    blocks: list[TextBlock | TableBlock | FlowchartBlock | SwimLaneBlock] = [
        TextBlock(style="h1", content="Change Request Handling Policy (Demo)"),
        TextBlock(style="h2", content="1. Purpose"),
        TextBlock(
            style="body",
            content=(
                "This demo document exists to visually confirm Slice 1 of the "
                "synthetic-corpus tool: Times New Roman body text, a distinct "
                "H1/H2/H3 heading hierarchy, a running footer with page numbers, "
                "and both a lane-free flowchart and a 3-lane swim-lane diagram."
            ),
        ),
        TextBlock(style="h2", content="2. Roles"),
        TableBlock(
            headers=["Role", "Responsibility"],
            rows=[
                ["Requester", "Submits a change request with justification"],
                ["Reviewer", "Triages and routes to an approver"],
                ["Approver", "Approves or rejects the request"],
            ],
            caption="Table 1. Roles referenced by this procedure.",
        ),
        TextBlock(style="h2", content="3. Procedure Overview (flowchart)"),
        FlowchartBlock(
            caption="Figure 1. High-level request lifecycle.",
            steps=[
                DiagramStep(id="submit", label="Request submitted"),
                DiagramStep(id="triage", label="Request triaged"),
                DiagramStep(id="decide", label="Decision recorded"),
                DiagramStep(id="close", label="Request closed"),
            ],
            transitions=[
                ("submit", "triage"),
                ("triage", "decide"),
                ("decide", "close"),
            ],
        ),
        TextBlock(style="h2", content="4. Procedure Detail (swim-lane)"),
        SwimLaneBlock(
            caption="Figure 2. Swim-lane view across Requester/Reviewer/Approver.",
            lanes=["Requester", "Reviewer", "Approver"],
            steps=[
                DiagramStep(id="s1", label="Submit request", lane="Requester"),
                DiagramStep(id="s2", label="Triage request", lane="Reviewer"),
                DiagramStep(id="s3", label="Approve request", lane="Approver"),
                DiagramStep(id="s4", label="Reject request", lane="Approver"),
                DiagramStep(id="s5", label="Notify requester", lane="Reviewer"),
                DiagramStep(id="s6", label="Close request", lane="Requester"),
            ],
            transitions=[
                ("s1", "s2"),
                ("s2", "s3"),
                ("s2", "s4"),
                ("s3", "s5"),
                ("s4", "s5"),
                ("s5", "s6"),
            ],
        ),
        TextBlock(style="h2", content="5. Filler (multi-page padding)"),
    ]
    blocks.extend(
        TextBlock(style="h3", content=f"5.{i}. Padding subsection")
        if i % 5 == 0
        else TextBlock(style="body", content=f"{_FILLER_PARAGRAPH} (paragraph {i})")
        for i in range(1, 41)
    )
    return Document(
        meta=DocumentMeta(
            doc_id="DEMO-001",
            title="Change Request Handling Policy (Demo)",
            version="1.0",
            effective_date="2026-09-01",
            owner="QMS Program Office",
        ),
        blocks=blocks,
    )
