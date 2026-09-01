"""CRUD for the compliance hierarchy (Standard -> Clause -> Requirement,
ADR-0008) and for Project/TodoItem creation (S2). Todo generation happens
in `create_project_with_todos`, in one transaction with the Project
insert, per SLICES.md V2's integration test plan."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from qms_incub.compliance.models import (
    Artifact,
    Clause,
    ComplianceStandard,
    Project,
    Requirement,
    RiskTier,
    TodoItem,
)
from qms_incub.compliance.scoring import RequirementSummary, filter_requirements_by_tier
from qms_incub.db import get_session


@dataclass
class StandardOut:
    id: str
    name: str
    description: str


@dataclass
class ClauseOut:
    id: str
    standard_id: str
    ordering: int
    text: str


@dataclass
class RequirementOut:
    id: str
    clause_id: str
    description: str
    risk_tiers: list[str]


@dataclass
class ProjectOut:
    id: str
    name: str
    risk_tier: str


@dataclass
class TodoItemOut:
    id: str
    project_id: str
    requirement_id: str
    requirement_description: str
    clause_text: str
    standard_name: str
    status: str


@dataclass
class ArtifactOut:
    id: str
    todo_item_id: str
    filename: str


def _todo_out(session: Session, todo: TodoItem) -> TodoItemOut:
    requirement = session.get(Requirement, todo.requirement_id)
    clause = session.get(Clause, requirement.clause_id) if requirement else None
    standard = session.get(ComplianceStandard, clause.standard_id) if clause else None
    return TodoItemOut(
        id=todo.id,
        project_id=todo.project_id,
        requirement_id=todo.requirement_id,
        requirement_description=requirement.description if requirement else "",
        clause_text=clause.text if clause else "",
        standard_name=standard.name if standard else "",
        status=todo.status,
    )


def create_standard(name: str, description: str) -> StandardOut:
    with get_session() as session:
        row = ComplianceStandard(name=name, description=description)
        session.add(row)
        session.flush()
        return StandardOut(id=row.id, name=row.name, description=row.description)


def list_standards() -> list[StandardOut]:
    with get_session() as session:
        rows = session.query(ComplianceStandard).order_by(ComplianceStandard.created_at).all()
        return [StandardOut(id=r.id, name=r.name, description=r.description) for r in rows]


def create_clause(standard_id: str, ordering: int, text: str) -> ClauseOut:
    with get_session() as session:
        row = Clause(standard_id=standard_id, ordering=ordering, text=text)
        session.add(row)
        session.flush()
        return ClauseOut(
            id=row.id, standard_id=row.standard_id, ordering=row.ordering, text=row.text
        )


def list_clauses(standard_id: str) -> list[ClauseOut]:
    with get_session() as session:
        rows = (
            session.query(Clause)
            .filter(Clause.standard_id == standard_id)
            .order_by(Clause.ordering)
            .all()
        )
        return [
            ClauseOut(id=r.id, standard_id=r.standard_id, ordering=r.ordering, text=r.text)
            for r in rows
        ]


def create_requirement(clause_id: str, description: str, risk_tiers: list[str]) -> RequirementOut:
    with get_session() as session:
        row = Requirement(clause_id=clause_id, description=description, risk_tiers=risk_tiers)
        session.add(row)
        session.flush()
        return RequirementOut(
            id=row.id,
            clause_id=row.clause_id,
            description=row.description,
            risk_tiers=row.risk_tiers,
        )


def list_requirements(clause_id: str) -> list[RequirementOut]:
    with get_session() as session:
        rows = session.query(Requirement).filter(Requirement.clause_id == clause_id).all()
        return [
            RequirementOut(
                id=r.id, clause_id=r.clause_id, description=r.description, risk_tiers=r.risk_tiers
            )
            for r in rows
        ]


def create_project_with_todos(
    name: str, risk_tier: RiskTier
) -> tuple[ProjectOut, list[TodoItemOut]]:
    """Wizard submit (S1+S2): create the Project, then one TodoItem per
    Requirement tagged for `risk_tier`, in a single transaction."""
    with get_session() as session:
        project = Project(name=name, risk_tier=risk_tier)
        session.add(project)
        session.flush()

        all_requirements = session.query(Requirement).all()
        summaries = [RequirementSummary(id=r.id, risk_tiers=r.risk_tiers) for r in all_requirements]
        matching_ids = {r.id for r in filter_requirements_by_tier(summaries, risk_tier)}
        matching_requirements = [r for r in all_requirements if r.id in matching_ids]

        todos: list[TodoItemOut] = []
        for requirement in matching_requirements:
            todo = TodoItem(project_id=project.id, requirement_id=requirement.id, status="pending")
            session.add(todo)
            session.flush()
            todos.append(_todo_out(session, todo))

        return ProjectOut(id=project.id, name=project.name, risk_tier=project.risk_tier), todos


def list_projects() -> list[ProjectOut]:
    with get_session() as session:
        rows = session.query(Project).order_by(Project.created_at.desc()).all()
        return [ProjectOut(id=r.id, name=r.name, risk_tier=r.risk_tier) for r in rows]


def get_project(project_id: str) -> ProjectOut | None:
    with get_session() as session:
        row = session.get(Project, project_id)
        if row is None:
            return None
        return ProjectOut(id=row.id, name=row.name, risk_tier=row.risk_tier)


def list_todos_for_project(project_id: str) -> list[TodoItemOut]:
    with get_session() as session:
        rows = session.query(TodoItem).filter(TodoItem.project_id == project_id).all()
        return [_todo_out(session, todo) for todo in rows]


def get_todo(todo_item_id: str) -> TodoItemOut | None:
    with get_session() as session:
        todo = session.get(TodoItem, todo_item_id)
        if todo is None:
            return None
        return _todo_out(session, todo)


def upload_artifact(todo_item_id: str, filename: str) -> tuple[ArtifactOut, TodoItemOut] | None:
    """Self-attestation (S3, ADR-0002): recording an Artifact against a
    TodoItem and flipping it to Complied happen in one transaction — no
    intermediate review state."""
    with get_session() as session:
        todo = session.get(TodoItem, todo_item_id)
        if todo is None:
            return None

        artifact = Artifact(todo_item_id=todo_item_id, filename=filename)
        session.add(artifact)
        todo.status = "complied"
        session.flush()

        return (
            ArtifactOut(
                id=artifact.id, todo_item_id=artifact.todo_item_id, filename=artifact.filename
            ),
            _todo_out(session, todo),
        )
