from types import SimpleNamespace

import pytest

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
    monkeypatch.setattr("qms_incub.chat.service.retrieve_top_k", lambda *_args, **_kwargs: chunks)
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
