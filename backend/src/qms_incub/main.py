from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from qms_incub.chat.service import answer_question

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
