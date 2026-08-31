"""Integration (SLICES.md § V1): needs a running Qdrant plus a first-run
embedding-model download. Excluded from the default `make test` / pre-push
run; wired into CI's backend job via a Qdrant service container."""

import uuid
from pathlib import Path

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from qms_incub.config import settings
from qms_incub.documents.pdf import html_to_pdf
from qms_incub.documents.render import render_document_html
from qms_incub.documents.seed import SEED_DOCUMENT_TITLE, build_seed_document
from qms_incub.ingestion.pipeline import ingest_pdf

pytestmark = pytest.mark.integration


def test_publishing_a_document_produces_chunks_referencing_its_id(tmp_path: Path) -> None:
    # Unique per run so this test never collides with, or leaks into, the
    # real seed document's data in the shared local Qdrant collection.
    document_id = f"test-doc-{uuid.uuid4()}"
    document = build_seed_document()
    html = render_document_html(document)
    pdf_bytes = html_to_pdf(html)

    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(pdf_bytes)

    client = QdrantClient(url=settings.qdrant_url)
    id_filter = Filter(
        must=[FieldCondition(key="qms_document_id", match=MatchValue(value=document_id))]
    )
    try:
        chunk_count = ingest_pdf(
            pdf_path, document_id=document_id, document_title=SEED_DOCUMENT_TITLE
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
