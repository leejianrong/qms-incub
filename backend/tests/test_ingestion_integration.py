"""Integration (SLICES.md § V1): needs a running Qdrant plus a first-run
embedding-model download. Excluded from the default `make test` / pre-push
run; wired into CI's backend job via a Qdrant service container."""

import uuid
from pathlib import Path

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from qms_incub.config import settings
from qms_incub.ingestion.pipeline import ingest_pdf

pytestmark = pytest.mark.integration

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_policy_document.pdf"


def test_ingesting_a_document_produces_chunks_referencing_its_id() -> None:
    # Unique per run so this test never collides with, or leaks into, any
    # other data in the shared local Qdrant collection.
    document_id = f"test-doc-{uuid.uuid4()}"

    client = QdrantClient(url=settings.qdrant_url)
    id_filter = Filter(
        must=[FieldCondition(key="qms_document_id", match=MatchValue(value=document_id))]
    )
    try:
        chunk_count = ingest_pdf(
            FIXTURE_PDF, document_id=document_id, document_title="Software Change Management Policy"
        )
        assert chunk_count >= 1

        found, _ = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=id_filter,
            limit=10,
        )
        assert len(found) == chunk_count
    finally:
        client.delete(collection_name=settings.qdrant_collection, points_selector=id_filter)
