from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qms_incub.chat.service import answer_question
from qms_incub.documents.batch import run_batch
from qms_incub.documents.repository import list_all

app = FastAPI(title="QMS Incub API")

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


class ChatRequest(BaseModel):
    question: str


class CitationOut(BaseModel):
    document_id: str
    document_title: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    result = answer_question(request.question)
    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationOut(document_id=c.document_id, document_title=c.document_title)
            for c in result.citations
        ],
    )


class BatchRequest(BaseModel):
    count: int = Field(default=5, gt=0, le=100)
    seed: int = 0
    table_row_min: int = Field(default=2, gt=0)
    table_row_max: int = Field(default=6, gt=0)
    flowchart_step_min: int = Field(default=2, gt=0)
    flowchart_step_max: int = Field(default=6, gt=0)


class BatchStartedResponse(BaseModel):
    status: str
    count: int


@app.post("/documents/batch")
def start_batch(request: BatchRequest, background_tasks: BackgroundTasks) -> BatchStartedResponse:
    # Runs in the background (Starlette's threadpool) rather than blocking
    # the request — a 20+ document batch (each doc: render, PDF export,
    # Docling parse, embed) takes well over a typical request timeout. The
    # ingestion status dashboard (GET /documents) is what you watch instead.
    background_tasks.add_task(
        run_batch,
        count=request.count,
        seed=request.seed,
        table_row_range=(request.table_row_min, request.table_row_max),
        flowchart_step_range=(request.flowchart_step_min, request.flowchart_step_max),
    )
    return BatchStartedResponse(status="started", count=request.count)


class PolicyDocumentStatusOut(BaseModel):
    id: str
    title: str
    origin: str
    is_synthetic: bool
    status: str
    chunk_count: int | None
    error: str | None


@app.get("/documents")
def get_documents() -> list[PolicyDocumentStatusOut]:
    return [
        PolicyDocumentStatusOut(
            id=d.id,
            title=d.title,
            origin=d.origin,
            is_synthetic=d.is_synthetic,
            status=d.status,
            chunk_count=d.chunk_count,
            error=d.error,
        )
        for d in list_all()
    ]
