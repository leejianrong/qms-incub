"""Synthetic batch generation (S5, ADR-0001, SLICES.md § V5).

Reuses V1's exact block model and render/export/ingest path — a batch
document is just a `PolicyDocument` whose blocks were populated
programmatically instead of by hand, flagged `is_synthetic=True`. A `seed`
makes a batch reproducible (worth carrying forward from
synthetic_pdf_bench's deterministic-seed pattern), which matters for a
generator whose whole job is being a repeatable ingestion stress test.
"""

from __future__ import annotations

import random

from qms_incub.documents.blocks import (
    FlowchartBlock,
    FlowchartStep,
    PolicyDocument,
    TableBlock,
    TextBlock,
)

_ROLES = [
    "Change Requestor",
    "Technical Reviewer",
    "Approving Authority",
    "Compliance Officer",
    "Release Manager",
    "Security Reviewer",
    "Documentation Lead",
]

_NAMES = [
    "Dr. Elena Vasquez",
    "Marcus Chen",
    "Priya Natarajan",
    "Tomasz Kowalski",
    "Aisha Bello",
    "Liam O'Connor",
    "Sofia Rinaldi",
    "Kenji Watanabe",
]

_RESPONSIBILITIES = [
    "Reviews and signs off on submissions for this process.",
    "Verifies compliance with the applicable risk tier before approval.",
    "Coordinates with stakeholders to resolve open questions.",
    "Maintains the audit trail for every decision made under this policy.",
    "Escalates exceptions that fall outside standard criteria.",
]

_STEP_LABELS = [
    "Submit Request",
    "Initial Review",
    "Risk Assessment",
    "Technical Review",
    "Compliance Check",
    "Approving Authority Sign-off",
    "Implementation",
    "Verification",
    "Closure",
]


def _random_table(rng: random.Random, row_count: int) -> TableBlock:
    rows = [
        [
            rng.choice(_ROLES),
            rng.choice(_NAMES),
            rng.choice(_RESPONSIBILITIES),
        ]
        for _ in range(row_count)
    ]
    return TableBlock(headers=["Role", "Name", "Responsibility"], rows=rows)


def _random_flowchart(rng: random.Random, step_count: int) -> FlowchartBlock:
    step_count = max(step_count, 1)
    labels = [rng.choice(_STEP_LABELS) for _ in range(step_count)]
    steps = [
        FlowchartStep(
            id=f"s{i + 1}",
            label=label,
            next=[f"s{i + 2}"] if i + 1 < step_count else [],
        )
        for i, label in enumerate(labels)
    ]
    return FlowchartBlock(steps=steps)


def generate_random_document(
    rng: random.Random,
    index: int,
    table_row_range: tuple[int, int],
    flowchart_step_range: tuple[int, int],
) -> PolicyDocument:
    row_count = rng.randint(*table_row_range)
    step_count = rng.randint(*flowchart_step_range)
    suffix = rng.randint(100000, 999999)

    return PolicyDocument(
        id=f"synthetic-{index:04d}-{suffix}",
        title=f"Synthetic Policy Document {index}",
        is_synthetic=True,
        blocks=[
            TextBlock(
                content=(
                    f"This is synthetic policy document #{index}, generated "
                    "to stress-test the RAG ingestion pipeline. It is not a "
                    "real policy."
                )
            ),
            _random_table(rng, row_count),
            TextBlock(content="The diagram below shows the process for this policy."),
            _random_flowchart(rng, step_count),
        ],
    )


def generate_batch(
    count: int,
    seed: int,
    table_row_range: tuple[int, int] = (2, 6),
    flowchart_step_range: tuple[int, int] = (2, 6),
) -> list[PolicyDocument]:
    rng = random.Random(seed)
    return [
        generate_random_document(rng, index, table_row_range, flowchart_step_range)
        for index in range(1, count + 1)
    ]
