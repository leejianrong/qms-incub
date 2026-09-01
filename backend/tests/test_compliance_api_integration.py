"""Integration (SLICES.md § V2): needs a running Postgres. Exercises the
real wizard-submit HTTP path — Standard/Clause/Requirement editor, then
completing the wizard with three representative answer sets and checking
the generated todo list traces back to the correct Requirements.

Assertions check for presence/absence of *this test's own* requirement
IDs among a project's todos, rather than exact totals — V2's todo
generation matches against every Requirement in the shared compliance
corpus (ADR-0008 names no project-to-standard scoping), so another
concurrent session's seed data must not make this test flaky."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from qms_incub.compliance.models import Clause, ComplianceStandard, Project, Requirement, TodoItem
from qms_incub.db import get_session
from qms_incub.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


@pytest.fixture
def seeded_hierarchy() -> Iterator[dict[str, str]]:
    standard = client.post(
        "/standards", json={"name": "Change Management", "description": "test fixture"}
    ).json()
    clause = client.post(
        f"/standards/{standard['id']}/clauses", json={"ordering": 1, "text": "Clause 1"}
    ).json()
    r_low = client.post(
        f"/clauses/{clause['id']}/requirements",
        json={"description": "Log every change", "risk_tiers": ["low", "medium", "high"]},
    ).json()
    r_medium = client.post(
        f"/clauses/{clause['id']}/requirements",
        json={"description": "Get sign-off from a lead", "risk_tiers": ["medium", "high"]},
    ).json()
    r_high = client.post(
        f"/clauses/{clause['id']}/requirements",
        json={"description": "External security audit", "risk_tiers": ["high"]},
    ).json()

    project_ids: list[str] = []
    yield {
        "standard_id": standard["id"],
        "clause_id": clause["id"],
        "standard_name": standard["name"],
        "clause_text": clause["text"],
        "r_low": r_low["id"],
        "r_medium": r_medium["id"],
        "r_high": r_high["id"],
        "_project_ids": project_ids,  # type: ignore[dict-item]
    }

    with get_session() as session:
        for project_id in project_ids:
            for todo in session.query(TodoItem).filter(TodoItem.project_id == project_id).all():
                session.delete(todo)
            project = session.get(Project, project_id)
            if project is not None:
                session.delete(project)
        for req_id in (r_low["id"], r_medium["id"], r_high["id"]):
            req = session.get(Requirement, req_id)
            if req is not None:
                session.delete(req)
        clause_row = session.get(Clause, clause["id"])
        if clause_row is not None:
            session.delete(clause_row)
        standard_row = session.get(ComplianceStandard, standard["id"])
        if standard_row is not None:
            session.delete(standard_row)


def _submit(name: str, **answers: bool) -> dict:
    project = client.post("/projects", json={"name": name}).json()
    response = client.post(f"/projects/{project['id']}/classify", json={"answers": answers})
    assert response.status_code == 200
    return response.json()


def test_low_answers_generate_only_the_low_tagged_todo(seeded_hierarchy: dict) -> None:
    body = _submit(
        "Low risk project",
        data_sensitivity_high=False,
        customer_facing=False,
        regulatory_exposure=False,
    )
    seeded_hierarchy["_project_ids"].append(body["project"]["id"])

    assert body["project"]["risk_tier"] == "low"
    requirement_ids = {t["requirement_id"] for t in body["todos"]}
    assert seeded_hierarchy["r_low"] in requirement_ids
    assert seeded_hierarchy["r_medium"] not in requirement_ids
    assert seeded_hierarchy["r_high"] not in requirement_ids


def test_medium_answers_generate_low_and_medium_todos(seeded_hierarchy: dict) -> None:
    body = _submit(
        "Medium risk project",
        data_sensitivity_high=False,
        customer_facing=False,
        regulatory_exposure=True,
    )
    seeded_hierarchy["_project_ids"].append(body["project"]["id"])

    assert body["project"]["risk_tier"] == "medium"
    requirement_ids = {t["requirement_id"] for t in body["todos"]}
    assert seeded_hierarchy["r_low"] in requirement_ids
    assert seeded_hierarchy["r_medium"] in requirement_ids
    assert seeded_hierarchy["r_high"] not in requirement_ids


def test_high_answers_generate_every_todo_with_full_traceability(seeded_hierarchy: dict) -> None:
    body = _submit(
        "High risk project",
        data_sensitivity_high=True,
        customer_facing=True,
        regulatory_exposure=True,
    )
    project_id = body["project"]["id"]
    seeded_hierarchy["_project_ids"].append(project_id)

    assert body["project"]["risk_tier"] == "high"
    requirement_ids = {t["requirement_id"] for t in body["todos"]}
    assert seeded_hierarchy["r_low"] in requirement_ids
    assert seeded_hierarchy["r_medium"] in requirement_ids
    assert seeded_hierarchy["r_high"] in requirement_ids

    high_todo = next(t for t in body["todos"] if t["requirement_id"] == seeded_hierarchy["r_high"])
    assert high_todo["standard_name"] == seeded_hierarchy["standard_name"]
    assert high_todo["clause_text"] == seeded_hierarchy["clause_text"]
    assert high_todo["requirement_description"] == "External security audit"
    assert high_todo["status"] == "pending"

    # persisted, not just echoed back from the POST
    fetched = client.get(f"/projects/{project_id}").json()
    fetched_requirement_ids = {t["requirement_id"] for t in fetched["todos"]}
    assert seeded_hierarchy["r_high"] in fetched_requirement_ids
