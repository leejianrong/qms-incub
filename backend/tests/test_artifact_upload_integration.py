"""Integration (SLICES.md § V3): needs a running Postgres. Uploading a
file against a todo self-attests it straight to Complied (ADR-0002), in
one HTTP request."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from qms_incub.compliance.models import (
    Artifact,
    Clause,
    ComplianceStandard,
    Project,
    Requirement,
    TodoItem,
)
from qms_incub.db import get_session
from qms_incub.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


@pytest.fixture
def seeded_project() -> Iterator[dict[str, str]]:
    standard = client.post(
        "/standards", json={"name": "Artifact Test Standard", "description": ""}
    ).json()
    clause = client.post(
        f"/standards/{standard['id']}/clauses", json={"ordering": 1, "text": "Clause 1"}
    ).json()
    requirement = client.post(
        f"/clauses/{clause['id']}/requirements",
        json={"description": "Upload proof of testing", "risk_tiers": ["low", "medium", "high"]},
    ).json()
    project = client.post("/projects", json={"name": "Artifact Test Project"}).json()
    project_body = client.post(
        f"/projects/{project['id']}/classify",
        json={
            "answers": {
                "data_sensitivity_high": False,
                "customer_facing": False,
                "regulatory_exposure": False,
            },
        },
    ).json()
    todo = next(
        t for t in project_body["todos"] if t["requirement_id"] == requirement["id"]
    )

    yield {"project_id": project_body["project"]["id"], "todo_id": todo["id"]}

    with get_session() as session:
        todo_ids = [
            t.id
            for t in session.query(TodoItem)
            .filter(TodoItem.project_id == project_body["project"]["id"])
            .all()
        ]
        for a in session.query(Artifact).filter(Artifact.todo_item_id.in_(todo_ids)).all():
            session.delete(a)
        for t in session.query(TodoItem).filter(TodoItem.id.in_(todo_ids)).all():
            session.delete(t)
        project_row = session.get(Project, project_body["project"]["id"])
        if project_row is not None:
            session.delete(project_row)
        req_row = session.get(Requirement, requirement["id"])
        if req_row is not None:
            session.delete(req_row)
        clause_row = session.get(Clause, clause["id"])
        if clause_row is not None:
            session.delete(clause_row)
        standard_row = session.get(ComplianceStandard, standard["id"])
        if standard_row is not None:
            session.delete(standard_row)


def test_uploading_an_artifact_self_attests_the_todo_to_complied(
    seeded_project: dict[str, str],
) -> None:
    todo_id = seeded_project["todo_id"]

    response = client.post(
        f"/todos/{todo_id}/artifacts",
        files={"file": ("evidence.pdf", b"fake pdf bytes", "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["artifact"]["filename"] == "evidence.pdf"
    assert body["todo"]["id"] == todo_id
    assert body["todo"]["status"] == "complied"
    assert body["todo"]["approval_state"] == "approved"
    assert body["todo"]["decided_at"] is not None

    fetched = client.get(f"/projects/{seeded_project['project_id']}").json()
    fetched_todo = next(t for t in fetched["todos"] if t["id"] == todo_id)
    assert fetched_todo["status"] == "complied"
    assert fetched_todo["approval_state"] == "approved"
    assert fetched_todo["decided_at"] is not None


def test_generated_todo_starts_not_started_with_seeded_authority_and_sla(
    seeded_project: dict[str, str],
) -> None:
    fetched = client.get(f"/projects/{seeded_project['project_id']}").json()
    todo = next(t for t in fetched["todos"] if t["id"] == seeded_project["todo_id"])
    assert todo["approval_state"] == "not_started"
    assert todo["approval_authority"] == "QA Office"
    assert todo["sla_target"] is not None
    assert todo["decided_at"] is None


def test_uploading_against_an_unknown_todo_returns_404() -> None:
    response = client.post(
        "/todos/does-not-exist/artifacts",
        files={"file": ("evidence.pdf", b"fake pdf bytes", "application/pdf")},
    )
    assert response.status_code == 404
