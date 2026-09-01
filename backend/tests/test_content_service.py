import pytest

from qms_incub.content.service import (
    PublishValidationError,
    faq_corpus_text,
    validate_blog_publish,
    validate_faq_publish,
)


@pytest.mark.parametrize("title,body", [("", "Body"), ("Title", "   ")])
def test_blog_publish_requires_title_and_body(title: str, body: str) -> None:
    with pytest.raises(PublishValidationError):
        validate_blog_publish(title, body)


@pytest.mark.parametrize("question,answer", [("", "Answer"), ("Question", "")])
def test_faq_publish_requires_question_and_answer(question: str, answer: str) -> None:
    with pytest.raises(PublishValidationError):
        validate_faq_publish(question, answer)


def test_faq_corpus_text_keeps_question_and_answer_together() -> None:
    assert faq_corpus_text("Who approves?", "The QA Office.") == (
        "Question: Who approves?\n\nAnswer: The QA Office."
    )
