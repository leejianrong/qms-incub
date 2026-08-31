from qms_incub.documents.blocks import FlowchartBlock, TableBlock, TextBlock
from qms_incub.documents.seed import (
    APPROVING_AUTHORITY_NAME,
    APPROVING_AUTHORITY_ROLE,
    build_seed_document,
)


def test_seed_document_combines_text_table_and_flowchart_blocks() -> None:
    document = build_seed_document()
    block_types = {block.type for block in document.blocks}
    assert block_types == {"text", "table", "flowchart"}
    assert any(isinstance(b, TextBlock) for b in document.blocks)
    assert any(isinstance(b, TableBlock) for b in document.blocks)
    assert any(isinstance(b, FlowchartBlock) for b in document.blocks)


def test_approving_authority_fact_lives_inside_the_table() -> None:
    document = build_seed_document()
    table = next(b for b in document.blocks if isinstance(b, TableBlock))

    matching_rows = [
        row
        for row in table.rows
        if APPROVING_AUTHORITY_ROLE in row and APPROVING_AUTHORITY_NAME in row
    ]
    assert len(matching_rows) == 1
