from qms_incub.chat.compliance_context import ArtifactState, ComplianceState, TodoState
from qms_incub.chat.prompt import build_compliance_state_block, build_context_block, build_messages
from qms_incub.chat.retrieval import RetrievedChunk

_CHUNKS = [
    RetrievedChunk(
        text="The approving authority is Dr. Elena Vasquez.",
        document_id="policy-1",
        document_title="Software Change Management Policy",
        source_type="policy_document",
        score=0.91,
    )
]

_STATE = ComplianceState(
    project_id="project-1",
    project_name="Customer Portal",
    risk_tier="high",
    todos=[
        TodoState(
            id="todo-1",
            requirement_description="Maintain an access review record.",
            status="complied",
            artifacts=[
                ArtifactState(id="artifact-1", todo_item_id="todo-1", filename="review.pdf")
            ],
        ),
        TodoState(
            id="todo-2",
            requirement_description="Complete a risk assessment.",
            status="pending",
            artifacts=[],
        ),
    ],
)


def test_build_context_block_includes_source_and_text() -> None:
    context = build_context_block(_CHUNKS)
    assert "Software Change Management Policy" in context
    assert "Dr. Elena Vasquez" in context


def test_build_context_block_handles_no_chunks() -> None:
    assert "no relevant context" in build_context_block([])


def test_build_compliance_state_block_includes_project_todos_and_artifacts() -> None:
    state = build_compliance_state_block(_STATE)
    assert '"project_name": "Customer Portal"' in state
    assert "Maintain an access review record." in state
    assert '"filename": "review.pdf"' in state


def test_build_messages_has_system_and_user_roles_with_question() -> None:
    messages = build_messages("Who is the approving authority?", _CHUNKS, _STATE)
    roles = [m["role"] for m in messages]
    assert roles == ["system", "user"]
    assert "Who is the approving authority?" in messages[1]["content"]
    assert "Dr. Elena Vasquez" in messages[1]["content"]
    assert "Policy Knowledge (retrieved corpus chunks)" in messages[1]["content"]
    assert "Your Compliance State (direct database state)" in messages[1]["content"]
    assert "Customer Portal" in messages[1]["content"]
