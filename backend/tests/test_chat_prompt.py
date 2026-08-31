from qms_incub.chat.prompt import build_context_block, build_messages
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


def test_build_context_block_includes_source_and_text() -> None:
    context = build_context_block(_CHUNKS)
    assert "Software Change Management Policy" in context
    assert "Dr. Elena Vasquez" in context


def test_build_context_block_handles_no_chunks() -> None:
    assert "no relevant context" in build_context_block([])


def test_build_messages_has_system_and_user_roles_with_question() -> None:
    messages = build_messages("Who is the approving authority?", _CHUNKS)
    roles = [m["role"] for m in messages]
    assert roles == ["system", "user"]
    assert "Who is the approving authority?" in messages[1]["content"]
    assert "Dr. Elena Vasquez" in messages[1]["content"]
