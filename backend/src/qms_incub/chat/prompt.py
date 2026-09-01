"""Prompt assembly (S8) — a pure function so it's fast-testable without
retrieval or an LLM call."""

from __future__ import annotations

import json

from qms_incub.chat.compliance_context import ComplianceState
from qms_incub.chat.retrieval import RetrievedChunk

SYSTEM_PROMPT = (
    "You are a QMS policy assistant. Answer from the supplied Policy Knowledge "
    "and/or Your Compliance State only. Policy Knowledge is the only source for "
    "policy claims; Your Compliance State is current project-specific status, not "
    "policy. Never present compliance-state data as a policy citation. If the "
    "answer is not present, say you don't know. Be concise."
)


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no relevant context found)"
    return "\n\n".join(
        f"[{i}] Source: {chunk.document_title}\n{chunk.text}"
        for i, chunk in enumerate(chunks, start=1)
    )


def build_compliance_state_block(state: ComplianceState) -> str:
    """Serialize direct database state separately from retrieved policy text."""
    return json.dumps(state.to_dict(), indent=2, sort_keys=True)


def build_messages(
    question: str, chunks: list[RetrievedChunk], compliance_state: ComplianceState
) -> list[dict[str, str]]:
    policy_context = build_context_block(chunks)
    state_context = build_compliance_state_block(compliance_state)
    user_prompt = (
        f"Policy Knowledge (retrieved corpus chunks):\n{policy_context}\n\n"
        f"Your Compliance State (direct database state):\n{state_context}\n\n"
        f"Question: {question}\n\n"
        "Use the labeled source appropriate to the question."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
