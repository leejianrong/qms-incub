"""Integration (SLICES.md § V10): needs a running Postgres. Confirms the
fixed ProcessStep set is seeded, `GET /process-steps` serves it in order,
and todo generation (S2) assigns each TodoItem the `process_step_id` of
its generating Requirement in the same transaction that creates it."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from qms_incub.compliance.models import Clause, ComplianceStandard, Project, Requirement, TodoItem
from qms_incub.db import get_session
from qms_incub.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def test_process_steps_are_seeded_and_served_in_order() -> None:
    response = client.get("/process-steps")
    assert response.status_code == 200
    steps = response.json()

    ids = [s["id"] for s in steps]
    assert ids == ["initiation", "design", "build", "test", "deploy", "closure"]
    assert [s["ordering"] for s in steps] == sorted(s["ordering"] for s in steps)


@pytest.fixture
def seeded_requirement_on_build_step() -> Iterator[dict[str, str]]:
    standard = client.post(
        "/standards", json={"name": "Build Process Step Fixture", "description": ""}
    ).json()
    clause = client.post(
        f"/standards/{standard['id']}/clauses", json={"ordering": 1, "text": "Clause 1"}
    ).json()
    requirement = client.post(
        f"/clauses/{clause['id']}/requirements",
        json={
            "description": "Peer-reviewed code before merge",
            "risk_tiers": ["low", "medium", "high"],
            "process_step_id": "build",
        },
    ).json()

    project_ids: list[str] = []
    yield {
        "clause_id": clause["id"],
        "requirement_id": requirement["id"],
        "_project_ids": project_ids,  # type: ignore[dict-item]
    }

    with get_session() as session:
        for project_id in project_ids:
            for todo in session.query(TodoItem).filter(TodoItem.project_id == project_id).all():
                session.delete(todo)
            project = session.get(Project, project_id)
            if project is not None:
                session.delete(project)
        req = session.get(Requirement, requirement["id"])
        if req is not None:
            session.delete(req)
        clause_row = session.get(Clause, clause["id"])
        if clause_row is not None:
            session.delete(clause_row)
        standard_row = session.get(ComplianceStandard, standard["id"])
        if standard_row is not None:
            session.delete(standard_row)


def test_requirement_process_step_id_is_persisted(seeded_requirement_on_build_step: dict) -> None:
    clause_id = seeded_requirement_on_build_step["clause_id"]
    requirement_id = seeded_requirement_on_build_step["requirement_id"]
    fetched = client.get(f"/clauses/{clause_id}/requirements").json()
    match = next(r for r in fetched if r["id"] == requirement_id)
    assert match["process_step_id"] == "build"


def test_classify_copies_process_step_id_onto_generated_todo_in_same_transaction(
    seeded_requirement_on_build_step: dict,
) -> None:
    project = client.post("/projects", json={"name": "Process step test project"}).json()
    seeded_requirement_on_build_step["_project_ids"].append(project["id"])

    response = client.post(
        f"/projects/{project['id']}/classify",
        json={
            "answers": {
                "data_sensitivity_high": True,
                "customer_facing": True,
                "regulatory_exposure": True,
            }
        },
    )
    assert response.status_code == 200
    body = response.json()

    requirement_id = seeded_requirement_on_build_step["requirement_id"]
    todo = next(t for t in body["todos"] if t["requirement_id"] == requirement_id)
    assert todo["process_step_id"] == "build"

    # persisted, not just echoed back from the POST
    with get_session() as session:
        row = session.get(TodoItem, todo["id"])
        assert row is not None
        assert row.process_step_id == "build"
