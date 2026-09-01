"""V6 integration: published admin content reaches Qdrant with its source type."""

import uuid

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from qms_incub.config import settings
from qms_incub.ingestion.pipeline import ingest_text

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("source_type", "text"),
    [
        ("blog", "A release note explains the change-control process."),
        ("faq", "Question: Who approves?\n\nAnswer: The QA Office approves."),
    ],
)
def test_ingesting_content_text_preserves_its_source_type(source_type: str, text: str) -> None:
    document_id = f"test-{source_type}-{uuid.uuid4()}"
    client = QdrantClient(url=settings.qdrant_url)
    id_filter = Filter(
        must=[FieldCondition(key="qms_document_id", match=MatchValue(value=document_id))]
    )
    try:
        chunk_count = ingest_text(text, document_id, "V6 test content", source_type)
        found, _ = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=id_filter,
            limit=10,
        )
        assert len(found) == chunk_count
        assert {point.payload["source_type"] for point in found} == {source_type}
    finally:
        if client.collection_exists(settings.qdrant_collection):
            client.delete(collection_name=settings.qdrant_collection, points_selector=id_filter)
