"""Integration (SLICES.md § V1): needs a running Qdrant plus Postgres, and
exercises the actual HTTP path a real user's upload takes — not just
`ingest_pdf` directly. Excluded from the default `make test` run."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from qms_incub.config import settings
from qms_incub.ingestion.repository import delete_by_id
from qms_incub.main import app

pytestmark = pytest.mark.integration

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_policy_document.pdf"

client = TestClient(app)


def test_uploading_a_document_ingests_it_and_lists_its_status() -> None:
    with FIXTURE_PDF.open("rb") as f:
        response = client.post(
            "/documents",
            files={"file": ("sample_policy_document.pdf", f, "application/pdf")},
        )
    assert response.status_code == 201
    body = response.json()
    document_id = body["id"]

    qdrant = QdrantClient(url=settings.qdrant_url)
    id_filter = Filter(
        must=[FieldCondition(key="qms_document_id", match=MatchValue(value=document_id))]
    )
    try:
        assert body["status"] == "embedded"
        assert body["chunk_count"] >= 1

        listed = client.get("/documents").json()
        assert any(d["id"] == document_id and d["status"] == "embedded" for d in listed)
    finally:
        qdrant.delete(collection_name=settings.qdrant_collection, points_selector=id_filter)
        delete_by_id(document_id)
