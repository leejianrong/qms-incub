"""V1's one hardcoded seed document (SLICES.md § V1).

Combines text, table, and flowchart blocks, with a fact (the approving
authority's name) placed inside a table cell — the fact V1's chat endpoint
must retrieve and cite correctly.

The ground-truth fact is kept here as the canonical source, not recovered
by re-parsing the PDF/ingested chunks later: tests assert ingestion and
chat output against these constants directly.
"""

from __future__ import annotations

from qms_incub.documents.blocks import (
    FlowchartBlock,
    FlowchartStep,
    PolicyDocument,
    TableBlock,
    TextBlock,
)

SEED_DOCUMENT_ID = "policy-software-change-management-v1"
SEED_DOCUMENT_TITLE = "Software Change Management Policy"

APPROVING_AUTHORITY_ROLE = "Approving Authority"
APPROVING_AUTHORITY_NAME = "Dr. Elena Vasquez"


def build_seed_document() -> PolicyDocument:
    return PolicyDocument(
        id=SEED_DOCUMENT_ID,
        title=SEED_DOCUMENT_TITLE,
        blocks=[
            TextBlock(
                content=(
                    "This policy defines how software changes are proposed, "
                    "reviewed, and approved before implementation. It applies to "
                    "all project teams delivering software changes of Medium "
                    "risk tier or above."
                )
            ),
            TextBlock(
                content=(
                    "The table below lists the roles involved in the change "
                    "management process and their responsibilities."
                )
            ),
            TableBlock(
                headers=["Role", "Name", "Responsibility"],
                rows=[
                    [
                        "Change Requestor",
                        "Project Manager (per project)",
                        "Submits the change request with a description and "
                        "risk assessment.",
                    ],
                    [
                        "Technical Reviewer",
                        "QA Lead",
                        "Reviews the change for technical soundness and test "
                        "coverage.",
                    ],
                    [
                        APPROVING_AUTHORITY_ROLE,
                        APPROVING_AUTHORITY_NAME,
                        "Gives final sign-off on all change requests of "
                        "Medium risk tier or above before implementation.",
                    ],
                ],
            ),
            TextBlock(
                content=(
                    "The diagram below shows the end-to-end change request "
                    "process, including the rejection path."
                )
            ),
            FlowchartBlock(
                steps=[
                    FlowchartStep(id="s1", label="Submit Change Request", next=["s2"]),
                    FlowchartStep(id="s2", label="Technical Review", next=["s3", "s4"]),
                    FlowchartStep(
                        id="s3", label="Approving Authority Sign-off", next=["s5"]
                    ),
                    FlowchartStep(id="s4", label="Request Rejected", next=[]),
                    FlowchartStep(id="s5", label="Implement Change", next=[]),
                ]
            ),
        ],
    )
