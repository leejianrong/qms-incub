from fastapi.testclient import TestClient

from qms_incub.chat.service import ChatAnswer, Citation, ProjectNotFoundError
from qms_incub.main import app

client = TestClient(app)


def test_chat_handler_passes_the_project_id_and_returns_policy_only_citations(monkeypatch) -> None:
    def fake_answer(question: str, project_id: str) -> ChatAnswer:
        assert question == "Am I compliant?"
        assert project_id == "project-1"
        return ChatAnswer(
            answer="You have one completed item.",
            citations=[Citation(document_id="policy-1", document_title="Approval Policy")],
        )

    monkeypatch.setattr("qms_incub.main.answer_question", fake_answer)
    response = client.post("/chat", json={"question": "Am I compliant?", "project_id": "project-1"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "You have one completed item.",
        "citations": [{"document_id": "policy-1", "document_title": "Approval Policy"}],
    }


def test_chat_handler_returns_404_for_an_unknown_project(monkeypatch) -> None:
    def missing_project(_question: str, _project_id: str) -> ChatAnswer:
        raise ProjectNotFoundError("missing")

    monkeypatch.setattr("qms_incub.main.answer_question", missing_project)
    response = client.post("/chat", json={"question": "Am I compliant?", "project_id": "missing"})
    assert response.status_code == 404
