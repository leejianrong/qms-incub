"""Chat endpoint's request handler (S8): retrieve -> expand to whole
documents -> prompt (with project compliance state) -> LLM -> answer +
citations.

The LLM is given the *entire* policy documents the retrieved chunks came
from, not just the matched passages — retrieval picks which documents are
relevant, then the full text of each is handed over as context, alongside
the requesting project's compliance state (V8) so the model can answer
project-specific questions without treating that state as a policy
citation. Citations are derived from the retrieved documents, not parsed
from the model's own output, so they stay accurate regardless of how well
the model follows citation formatting."""

from __future__ import annotations

from dataclasses import dataclass

from qms_incub.chat.compliance_context import get_compliance_state
from qms_incub.chat.llm import get_llm_client
from qms_incub.chat.prompt import build_messages
from qms_incub.chat.retrieval import RetrievedChunk, fetch_document, retrieve


@dataclass
class Citation:
    document_id: str
    document_title: str


@dataclass
class ChatAnswer:
    answer: str
    citations: list[Citation]


def _expand_to_documents(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Replace the retrieved chunks with the full text of each distinct
    source document, keeping retrieval order. Falls back to the chunk
    itself if the document can't be re-fetched."""
    seen: set[str] = set()
    docs: list[RetrievedChunk] = []
    for chunk in chunks:
        if chunk.document_id in seen:
            continue
        seen.add(chunk.document_id)
        full = fetch_document(chunk.document_id, score=chunk.score)
        docs.append(full if full is not None else chunk)
    return docs


def _dedupe_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    seen: set[str] = set()
    citations: list[Citation] = []
    for chunk in chunks:
        if chunk.document_id in seen:
            continue
        seen.add(chunk.document_id)
        citations.append(
            Citation(document_id=chunk.document_id, document_title=chunk.document_title)
        )
    return citations


class ProjectNotFoundError(ValueError):
    pass


def answer_question(question: str, project_id: str, top_k: int = 4) -> ChatAnswer:
    compliance_state = get_compliance_state(project_id)
    if compliance_state is None:
        raise ProjectNotFoundError(project_id)

    # Retrieval (BM25 + rerank) selects the relevant documents; the LLM
    # then gets each of those documents in full.
    chunks = retrieve(question, k=top_k)
    documents = _expand_to_documents(chunks)
    messages = build_messages(question, documents, compliance_state)

    client, model = get_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.0,
    )
    answer_text = response.choices[0].message.content or ""

    return ChatAnswer(answer=answer_text, citations=_dedupe_citations(documents))
