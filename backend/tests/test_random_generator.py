from qms_incub.documents.blocks import FlowchartBlock, TableBlock
from qms_incub.documents.random_generator import generate_batch


def test_generate_batch_produces_requested_count() -> None:
    docs = generate_batch(count=5, seed=1)
    assert len(docs) == 5
    assert all(doc.is_synthetic for doc in docs)


def test_generate_batch_is_deterministic_for_a_given_seed() -> None:
    first = generate_batch(count=4, seed=123)
    second = generate_batch(count=4, seed=123)
    assert [doc.model_dump() for doc in first] == [doc.model_dump() for doc in second]


def test_generate_batch_produces_unique_document_ids() -> None:
    docs = generate_batch(count=10, seed=7)
    ids = {doc.id for doc in docs}
    assert len(ids) == len(docs)


def test_generate_batch_respects_complexity_ranges() -> None:
    docs = generate_batch(
        count=20,
        seed=99,
        table_row_range=(3, 5),
        flowchart_step_range=(2, 3),
    )
    for doc in docs:
        table = next(b for b in doc.blocks if isinstance(b, TableBlock))
        flowchart = next(b for b in doc.blocks if isinstance(b, FlowchartBlock))
        assert 3 <= len(table.rows) <= 5
        assert 2 <= len(flowchart.steps) <= 3
