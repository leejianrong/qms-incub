"""Fast tests for the chat service (no Qdrant, no LLM): BM25 retrieval +
whole-document expansion, and project compliance-state passthrough."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from qms_incub.chat import service
from qms_incub.chat.compliance_context import ComplianceState, TodoState
from qms_incub.chat.retrieval import RetrievedChunk
from qms_incub.chat.service import ProjectNotFoundError, answer_question


def _state() -> ComplianceState:
    return ComplianceState(
        project_id="project-1",
        project_name="Customer Portal",
        risk_tier="high",
        todos=[
            TodoState(
                id="todo-1",
                requirement_description="Complete access review",
                status="complied",
                artifacts=[],
            )
        ],
    )


def _chunk(doc_id: str, idx: int, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        text=f"passage {idx} of {doc_id}",
        document_id=doc_id,
        document_title=f"{doc_id} title",
        source_type="policy_document",
        score=score,
        chunk_id=f"{doc_id}-{idx}",
        chunk_index=idx,
    )


def test_expand_to_documents_dedupes_and_keeps_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _fake_fetch(document_id: str, *, score: float) -> RetrievedChunk:
        calls.append(document_id)
        return RetrievedChunk(
            text=f"FULL TEXT of {document_id}",
            document_id=document_id,
            document_title=f"{document_id} title",
            source_type="policy_document",
            score=score,
            chunk_id="full-document",
            chunk_index=-1,
        )

    monkeypatch.setattr(
        service, "get_retrieval_port", lambda: SimpleNamespace(fetch_document=_fake_fetch)
    )

    retrieved = [
        _chunk("doc-a", 2, 0.9),
        _chunk("doc-a", 5, 0.7),  # same doc — must not fetch twice
        _chunk("doc-b", 0, 0.4),
    ]
    docs = service._expand_to_documents(retrieved)

    assert calls == ["doc-a", "doc-b"]  # one fetch per distinct doc, in order
    assert [d.document_id for d in docs] == ["doc-a", "doc-b"]
    assert docs[0].text == "FULL TEXT of doc-a"
    assert docs[0].score == 0.9  # score carried from the first matching chunk


def test_expand_to_documents_falls_back_to_chunk_when_fetch_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service,
        "get_retrieval_port",
        lambda: SimpleNamespace(fetch_document=lambda *_a, **_kw: None),
    )

    retrieved = [_chunk("doc-a", 1, 0.5)]
    docs = service._expand_to_documents(retrieved)

    assert len(docs) == 1
    assert docs[0].text == "passage 1 of doc-a"


def test_dedupe_citations_one_per_document() -> None:
    citations = service._dedupe_citations(
        [_chunk("doc-a", 0, 0.9), _chunk("doc-a", 1, 0.8), _chunk("doc-b", 0, 0.5)]
    )
    assert [(c.document_id, c.document_title) for c in citations] == [
        ("doc-a", "doc-a title"),
        ("doc-b", "doc-b title"),
    ]


def test_answer_question_sends_separate_policy_and_project_state_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    chunks = [
        RetrievedChunk(
            text="The authority is the QA Office.",
            document_id="policy-1",
            document_title="Approval Policy",
            source_type="policy_document",
            score=0.9,
        )
    ]

    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]
            )

    monkeypatch.setattr("qms_incub.chat.service.get_compliance_state", lambda _: _state())
    # No real store in this fast test — fall back to the retrieved chunk
    # itself, which already carries the text asserted on below.
    fake_port = SimpleNamespace(
        retrieve=lambda *_args, **_kwargs: chunks,
        fetch_document=lambda *_a, **_kw: None,
    )
    monkeypatch.setattr("qms_incub.chat.service.get_retrieval_port", lambda: fake_port)
    monkeypatch.setattr(
        "qms_incub.chat.service.get_llm_client",
        lambda: (
            SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())),
            "test-model",
        ),
    )

    answer = answer_question("Am I compliant?", "project-1")

    assert answer.answer == "answer"
    assert [citation.document_id for citation in answer.citations] == ["policy-1"]
    prompt = (captured["messages"])[1]["content"]  # type: ignore[index]
    assert "Policy Knowledge (retrieved corpus chunks)" in prompt
    assert "The authority is the QA Office." in prompt
    assert "Your Compliance State (direct database state)" in prompt
    assert "Complete access review" in prompt


def test_answer_question_rejects_unknown_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("qms_incub.chat.service.get_compliance_state", lambda _: None)
    with pytest.raises(ProjectNotFoundError):
        answer_question("Am I compliant?", "missing")
