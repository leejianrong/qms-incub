"""HTTP surface for the compliance hierarchy (QA-author editor, ADR-0008),
project creation + AOR intake + the classification wizard (S1, S2, S10),
and self-attestation (S3)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from qms_incub.aor.service import extract_aor_fields_from_document
from qms_incub.compliance import repository
from qms_incub.compliance.metrics import compliance_percentage
from qms_incub.compliance.scoring import score_risk_tier
from qms_incub.paths import UPLOADED_AOR_DIR, UPLOADED_ARTIFACTS_DIR

router = APIRouter()


# --- QA-author: Standard / Clause / Requirement editor (ADR-0008) ---


class StandardIn(BaseModel):
    name: str
    description: str = ""


class StandardOut(BaseModel):
    id: str
    name: str
    description: str


@router.post("/standards", status_code=201)
def create_standard(body: StandardIn) -> StandardOut:
    result = repository.create_standard(body.name, body.description)
    return StandardOut(id=result.id, name=result.name, description=result.description)


@router.get("/standards")
def list_standards() -> list[StandardOut]:
    return [
        StandardOut(id=s.id, name=s.name, description=s.description)
        for s in repository.list_standards()
    ]


class ClauseIn(BaseModel):
    ordering: int = 0
    text: str


class ClauseOut(BaseModel):
    id: str
    standard_id: str
    ordering: int
    text: str


@router.post("/standards/{standard_id}/clauses", status_code=201)
def create_clause(standard_id: str, body: ClauseIn) -> ClauseOut:
    result = repository.create_clause(standard_id, body.ordering, body.text)
    return ClauseOut(
        id=result.id, standard_id=result.standard_id, ordering=result.ordering, text=result.text
    )


@router.get("/standards/{standard_id}/clauses")
def list_clauses(standard_id: str) -> list[ClauseOut]:
    return [
        ClauseOut(id=c.id, standard_id=c.standard_id, ordering=c.ordering, text=c.text)
        for c in repository.list_clauses(standard_id)
    ]


class RequirementIn(BaseModel):
    description: str
    risk_tiers: list[str]


class RequirementOut(BaseModel):
    id: str
    clause_id: str
    description: str
    risk_tiers: list[str]


@router.post("/clauses/{clause_id}/requirements", status_code=201)
def create_requirement(clause_id: str, body: RequirementIn) -> RequirementOut:
    result = repository.create_requirement(clause_id, body.description, body.risk_tiers)
    return RequirementOut(
        id=result.id,
        clause_id=result.clause_id,
        description=result.description,
        risk_tiers=result.risk_tiers,
    )


@router.get("/clauses/{clause_id}/requirements")
def list_requirements(clause_id: str) -> list[RequirementOut]:
    return [
        RequirementOut(
            id=r.id, clause_id=r.clause_id, description=r.description, risk_tiers=r.risk_tiers
        )
        for r in repository.list_requirements(clause_id)
    ]


# --- Project creation, AOR intake, and the classification wizard (S1, S2, S10) ---


class WizardAnswers(BaseModel):
    data_sensitivity_high: bool
    customer_facing: bool
    regulatory_exposure: bool


class ProjectIn(BaseModel):
    name: str


class ClassifyIn(BaseModel):
    answers: WizardAnswers


class TodoItemOut(BaseModel):
    id: str
    project_id: str
    requirement_id: str
    requirement_description: str
    clause_text: str
    standard_name: str
    status: str


class ProjectOut(BaseModel):
    id: str
    name: str
    risk_tier: str | None
    aor_filename: str | None
    aor_extracted_fields: dict[str, object] | None


class ProjectWithTodosOut(BaseModel):
    project: ProjectOut
    todos: list[TodoItemOut]
    compliance_percentage: float


def _todo_out(t: repository.TodoItemOut) -> TodoItemOut:
    return TodoItemOut(
        id=t.id,
        project_id=t.project_id,
        requirement_id=t.requirement_id,
        requirement_description=t.requirement_description,
        clause_text=t.clause_text,
        standard_name=t.standard_name,
        status=t.status,
    )


def _project_out(project: repository.ProjectOut) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        name=project.name,
        risk_tier=project.risk_tier,
        aor_filename=project.aor_filename,
        aor_extracted_fields=project.aor_extracted_fields,
    )


def _project_with_todos_out(
    project: repository.ProjectOut, todos: list[repository.TodoItemOut]
) -> ProjectWithTodosOut:
    return ProjectWithTodosOut(
        project=_project_out(project),
        todos=[_todo_out(t) for t in todos],
        compliance_percentage=compliance_percentage([t.status for t in todos]),
    )


@router.post("/projects", status_code=201)
def create_project(body: ProjectIn) -> ProjectOut:
    """Wizard step 1: create the Project from just a name. `risk_tier`
    starts null — an AOR can be attached (`POST /projects/{id}/aor`)
    before classification (`POST /projects/{id}/classify`, wizard step 2)."""
    return _project_out(repository.create_project(body.name))


@router.get("/projects")
def list_projects() -> list[ProjectOut]:
    return [_project_out(p) for p in repository.list_projects()]


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> ProjectWithTodosOut:
    project = repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    todos = repository.list_todos_for_project(project_id)
    return _project_with_todos_out(project, todos)


@router.post("/projects/{project_id}/aor", status_code=201)
async def upload_aor(project_id: str, file: UploadFile = File(...)) -> ProjectOut:
    """S10: Docling-parse + LLM-extract the project's own intake document
    into a fixed set of structured fields. Extraction only, never enters
    the Qdrant corpus or `GET /documents` (ADR-0012, Q40)."""
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    filename = file.filename or f"{project_id}-aor"
    UPLOADED_AOR_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOADED_AOR_DIR / f"{uuid.uuid4()}-{filename}"
    stored_path.write_bytes(await file.read())

    fields = extract_aor_fields_from_document(stored_path)

    result = repository.attach_aor(project_id, filename, fields.to_dict())
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_out(result)


@router.post("/projects/{project_id}/classify")
def classify_project(project_id: str, body: ClassifyIn) -> ProjectWithTodosOut:
    """Wizard step 2 (S1+S2): score the risk tier from the 3 fixed
    questions, then generate one TodoItem per matching Requirement."""
    tier = score_risk_tier(
        data_sensitivity_high=body.answers.data_sensitivity_high,
        customer_facing=body.answers.customer_facing,
        regulatory_exposure=body.answers.regulatory_exposure,
    )
    result = repository.classify_project(project_id, tier)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project, todos = result
    return _project_with_todos_out(project, todos)


# --- Artifact upload + self-attestation (S3, ADR-0002) ---


class ArtifactOut(BaseModel):
    id: str
    todo_item_id: str
    filename: str


class ArtifactUploadOut(BaseModel):
    artifact: ArtifactOut
    todo: TodoItemOut


@router.post("/todos/{todo_id}/artifacts", status_code=201)
async def upload_artifact(todo_id: str, file: UploadFile = File(...)) -> ArtifactUploadOut:
    """Uploading a file against a todo is self-attestation: it flips the
    TodoItem straight to Complied, no reviewer gate (ADR-0002)."""
    if repository.get_todo(todo_id) is None:
        raise HTTPException(status_code=404, detail="Todo item not found")

    filename = file.filename or f"{todo_id}-artifact"
    UPLOADED_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4()}-{filename}"
    (UPLOADED_ARTIFACTS_DIR / stored_name).write_bytes(await file.read())

    result = repository.upload_artifact(todo_id, filename)
    if result is None:
        raise HTTPException(status_code=404, detail="Todo item not found")
    artifact, todo = result
    return ArtifactUploadOut(
        artifact=ArtifactOut(
            id=artifact.id, todo_item_id=artifact.todo_item_id, filename=artifact.filename
        ),
        todo=_todo_out(todo),
    )
