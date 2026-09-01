"""Integration (SLICES.md § V9): needs a running Postgres. Exercises the
real `POST /projects/{id}/aor` HTTP path. The LLM extraction call is
monkeypatched (this marker's tests don't require a live LLM, unlike
`e2e`) — what's under test here is that the endpoint persists the
extracted fields onto the Project in one request, and that the AOR never
enters the document/RAG corpus (ADR-0012)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from qms_incub.aor.extraction import AorFields
from qms_incub.compliance import api as compliance_api
from qms_incub.compliance.models import Project
from qms_incub.db import get_session
from qms_incub.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)

_FIELDS = AorFields(
    criticality_tier="high",
    data_classification="confidential",
    external_dependencies=["Vendor A"],
    in_house_rationale="Existing in-house expertise.",
)


@pytest.fixture
def project() -> Iterator[dict[str, str]]:
    body = client.post("/projects", json={"name": "AOR Intake Test Project"}).json()
    yield body
    with get_session() as session:
        row = session.get(Project, body["id"])
        if row is not None:
            session.delete(row)


@pytest.fixture
def stub_extraction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        compliance_api, "extract_aor_fields_from_document", lambda _path: _FIELDS
    )


def test_uploading_an_aor_persists_and_returns_extracted_fields(
    project: dict[str, str], stub_extraction: None
) -> None:
    response = client.post(
        f"/projects/{project['id']}/aor",
        files={"file": ("intake.pdf", b"fake pdf bytes", "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["aor_filename"] == "intake.pdf"
    assert body["aor_extracted_fields"] == _FIELDS.to_dict()

    fetched = client.get(f"/projects/{project['id']}").json()
    assert fetched["project"]["aor_extracted_fields"] == _FIELDS.to_dict()


def test_aor_upload_never_enters_the_document_corpus(
    project: dict[str, str], stub_extraction: None
) -> None:
    before = client.get("/documents").json()
    client.post(
        f"/projects/{project['id']}/aor",
        files={"file": ("intake.pdf", b"fake pdf bytes", "application/pdf")},
    )
    after = client.get("/documents").json()
    assert after == before
    assert all("intake.pdf" != d.get("title") for d in after)


def test_aor_upload_against_an_unknown_project_returns_404(stub_extraction: None) -> None:
    response = client.post(
        "/projects/does-not-exist/aor",
        files={"file": ("intake.pdf", b"fake pdf bytes", "application/pdf")},
    )
    assert response.status_code == 404
