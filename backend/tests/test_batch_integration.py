"""Integration (SLICES.md § V5): needs Postgres (migrated) and Qdrant."""

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny

from qms_incub.config import settings
from qms_incub.documents.batch import run_batch
from qms_incub.documents.repository import delete_by_id, list_all

pytestmark = pytest.mark.integration


def test_run_batch_ingests_every_document_and_records_status() -> None:
    results = run_batch(count=3, seed=2026, table_row_range=(2, 3), flowchart_step_range=(2, 3))
    document_ids = [r.document_id for r in results]

    try:
        assert len(results) == 3
        assert all(r.status == "embedded" for r in results)
        assert all((r.chunk_count or 0) >= 1 for r in results)

        statuses = {row.id: row for row in list_all()}
        for result in results:
            row = statuses[result.document_id]
            assert row.status == "embedded"
            assert row.is_synthetic is True
            assert row.chunk_count == result.chunk_count
    finally:
        for document_id in document_ids:
            delete_by_id(document_id)
        client = QdrantClient(url=settings.qdrant_url)
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=Filter(
                must=[FieldCondition(key="qms_document_id", match=MatchAny(any=document_ids))]
            ),
        )
