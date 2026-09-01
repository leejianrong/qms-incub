"""Read-only, project-scoped state used to ground V8 chat requests.

This deliberately reads relational compliance data directly instead of putting
it in Qdrant: project state is small, exact, and changes whenever a PM
attests an item (ADR-0003). The project state is sent to the configured LLM
provider only for this project-aware chat request; the user explicitly
approved that transfer for V8 on 2026-09-01.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from qms_incub.compliance import repository


@dataclass(frozen=True)
class ArtifactState:
    id: str
    todo_item_id: str
    filename: str


@dataclass(frozen=True)
class TodoState:
    id: str
    requirement_description: str
    status: str
    artifacts: list[ArtifactState]


@dataclass(frozen=True)
class ComplianceState:
    project_id: str
    project_name: str
    risk_tier: str | None
    todos: list[TodoState]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def get_compliance_state(project_id: str) -> ComplianceState | None:
    """Return the current project/todo/artifact state, or ``None`` if absent."""
    result = repository.get_chat_context(project_id)
    if result is None:
        return None

    project, todos, artifacts_by_todo = result
    return ComplianceState(
        project_id=project.id,
        project_name=project.name,
        risk_tier=project.risk_tier,
        todos=[
            TodoState(
                id=todo.id,
                requirement_description=todo.requirement_description,
                status=todo.status,
                artifacts=[
                    ArtifactState(
                        id=artifact.id,
                        todo_item_id=artifact.todo_item_id,
                        filename=artifact.filename,
                    )
                    for artifact in artifacts_by_todo.get(todo.id, [])
                ],
            )
            for todo in todos
        ],
    )
