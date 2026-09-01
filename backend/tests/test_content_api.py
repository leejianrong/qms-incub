import datetime

import pytest
from fastapi import HTTPException

from qms_incub.content import repository
from qms_incub.content.api import publish_blog, publish_faq


def test_publish_blog_sends_plain_text_to_ingestion_with_blog_source_type(monkeypatch) -> None:
    row = repository.BlogPostOut("blog-1", "Release notes", "Process update", None, None)
    monkeypatch.setattr(
        repository, "get_blog", lambda post_id: row if post_id == "blog-1" else None
    )
    captured: dict[str, str] = {}

    def fake_ingest(text: str, document_id: str, document_title: str, source_type: str) -> int:
        captured.update(
            text=text,
            document_id=document_id,
            document_title=document_title,
            source_type=source_type,
        )
        return 2

    monkeypatch.setattr("qms_incub.content.api.ingest_text", fake_ingest)
    monkeypatch.setattr(
        repository,
        "mark_blog_published",
        lambda post_id, chunk_count: repository.BlogPostOut(
            "blog-1",
            "Release notes",
            "Process update",
            datetime.datetime.now(datetime.UTC),
            chunk_count,
        ),
    )

    response = publish_blog("blog-1")

    assert response.chunk_count == 2
    assert captured == {
        "text": "Process update",
        "document_id": "blog-1",
        "document_title": "Release notes",
        "source_type": "blog",
    }


def test_publish_faq_sends_question_and_answer_with_faq_source_type(monkeypatch) -> None:
    row = repository.FAQEntryOut("faq-1", "Who approves?", "The QA Office.", None, None)
    monkeypatch.setattr(
        repository, "get_faq", lambda entry_id: row if entry_id == "faq-1" else None
    )
    captured: dict[str, str] = {}

    def fake_ingest(text: str, document_id: str, document_title: str, source_type: str) -> int:
        captured.update(
            text=text,
            document_id=document_id,
            document_title=document_title,
            source_type=source_type,
        )
        return 1

    monkeypatch.setattr("qms_incub.content.api.ingest_text", fake_ingest)
    monkeypatch.setattr(
        repository,
        "mark_faq_published",
        lambda entry_id, chunk_count: repository.FAQEntryOut(
            "faq-1",
            "Who approves?",
            "The QA Office.",
            datetime.datetime.now(datetime.UTC),
            chunk_count,
        ),
    )

    publish_faq("faq-1")

    assert captured["source_type"] == "faq"
    assert captured["text"] == "Question: Who approves?\n\nAnswer: The QA Office."


def test_publish_rejects_a_blog_draft_missing_required_content(monkeypatch) -> None:
    monkeypatch.setattr(
        repository,
        "get_blog",
        lambda post_id: repository.BlogPostOut("blog-1", "", "Body", None, None),
    )
    with pytest.raises(HTTPException) as exc_info:
        publish_blog("blog-1")
    assert exc_info.value.status_code == 422
    assert "title is required" in exc_info.value.detail
