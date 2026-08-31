"""Prompt assembly (S8) — a pure function so it's fast-testable without
retrieval or an LLM call."""

from __future__ import annotations

from qms_incub.chat.retrieval import RetrievedChunk

SYSTEM_PROMPT = (
    "You are a QMS policy assistant. Answer the user's question using ONLY "
    "the policy context provided below. If the answer is not present in the "
    "context, say you don't know rather than guessing. Be concise."
)


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no relevant context found)"
    return "\n\n".join(
        f"[{i}] Source: {chunk.document_title}\n{chunk.text}"
        for i, chunk in enumerate(chunks, start=1)
    )


def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    context = build_context_block(chunks)
    user_prompt = (
        f"Policy context:\n{context}\n\nQuestion: {question}\n\n"
        "Answer using only the context above."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
