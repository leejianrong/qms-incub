"""Chat endpoint's request handler (S8): retrieve -> prompt -> LLM ->
answer + citations. Citations are derived from what was actually
retrieved, not parsed from the model's own output, so they stay accurate
regardless of how well the model follows citation formatting."""

from __future__ import annotations

from dataclasses import dataclass

from qms_incub.chat.llm import get_llm_client
from qms_incub.chat.prompt import build_messages
from qms_incub.chat.retrieval import RetrievedChunk, retrieve_top_k


@dataclass
class Citation:
    document_id: str
    document_title: str


@dataclass
class ChatAnswer:
    answer: str
    citations: list[Citation]


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


def answer_question(question: str, top_k: int = 4) -> ChatAnswer:
    chunks = retrieve_top_k(question, k=top_k)
    messages = build_messages(question, chunks)

    client, model = get_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        temperature=0.0,
    )
    answer_text = response.choices[0].message.content or ""

    return ChatAnswer(answer=answer_text, citations=_dedupe_citations(chunks))
