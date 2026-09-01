import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from qms_incub.aor_routing.classifier import classify_aor_pdf
from qms_incub.chat.service import ProjectNotFoundError, answer_question
from qms_incub.compliance.api import router as compliance_router
from qms_incub.ingestion.pipeline import ingest_pdf
from qms_incub.ingestion.repository import create_pending, list_all, mark_embedded, mark_failed
from qms_incub.paths import AOR_UPLOADS_DIR, UPLOADED_DOCUMENTS_DIR

app = FastAPI(title="QMS Incub API")
app.include_router(compliance_router)

# Local dev only: the Svelte/Vite dev server (default port 5173) is a
# different origin than the API (port 8000), so the browser needs an
# explicit CORS allow. Revisit before this is ever deployed anywhere.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class DocumentStatusOut(BaseModel):
    id: str
    title: str
    status: str
    chunk_count: int | None
    error: str | None


@app.post("/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)) -> DocumentStatusOut:
    """Upload a PDF; it's parsed, chunked, embedded, and stored in Qdrant
    (S6) so it becomes queryable via /chat. The only way a document enters
    the corpus — the backend never composes or generates document content
    itself."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    document_id = str(uuid.uuid4())
    title = file.filename or document_id

    UPLOADED_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = UPLOADED_DOCUMENTS_DIR / f"{document_id}.pdf"
    pdf_path.write_bytes(await file.read())

    create_pending(document_id, title)
    try:
        chunk_count = ingest_pdf(pdf_path, document_id=document_id, document_title=title)
    except Exception as exc:
        mark_failed(document_id, str(exc))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    mark_embedded(document_id, chunk_count)
    return DocumentStatusOut(
        id=document_id, title=title, status="embedded", chunk_count=chunk_count, error=None
    )


@app.get("/documents")
def list_documents() -> list[DocumentStatusOut]:
    return [
        DocumentStatusOut(
            id=d.id, title=d.title, status=d.status, chunk_count=d.chunk_count, error=d.error
        )
        for d in list_all()
    ]


class AorClassificationOut(BaseModel):
    route: str
    label: str
    scores: dict[str, float]
    confidence: float
    needs_review: bool
    evidence_excerpt: str


@app.post("/aor/classify")
async def classify_aor(file: UploadFile = File(...)) -> AorClassificationOut:
    """Classify an AOR without adding it to the policy/chat corpus."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    AOR_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = AOR_UPLOADS_DIR / f"{uuid.uuid4()}.pdf"
    pdf_path.write_bytes(await file.read())
    try:
        result = classify_aor_pdf(pdf_path)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AOR classification failed: {exc}") from exc

    return AorClassificationOut(
        route=result.route,
        label={"rt": "R&T", "ssd": "SSD"}[result.route],
        scores=result.scores,
        confidence=result.confidence,
        needs_review=result.needs_review,
        evidence_excerpt=result.evidence_excerpt,
    )


class ChatRequest(BaseModel):
    question: str
    project_id: str


class CitationOut(BaseModel):
    document_id: str
    document_title: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = answer_question(request.question, request.project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationOut(document_id=c.document_id, document_title=c.document_title)
            for c in result.citations
        ],
    )
