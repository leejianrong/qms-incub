"""Publishing rules for V6's admin-authored corpus content."""

from __future__ import annotations


class PublishValidationError(ValueError):
    """The draft is missing content required for publication."""


def validate_blog_publish(title: str, body: str) -> None:
    if not title.strip():
        raise PublishValidationError("Blog post title is required to publish.")
    if not body.strip():
        raise PublishValidationError("Blog post body is required to publish.")


def validate_faq_publish(question: str, answer: str) -> None:
    if not question.strip():
        raise PublishValidationError("FAQ question is required to publish.")
    if not answer.strip():
        raise PublishValidationError("FAQ answer is required to publish.")


def faq_corpus_text(question: str, answer: str) -> str:
    """Keep each Q&A pair intelligible when its chunk is retrieved alone."""
    return f"Question: {question.strip()}\n\nAnswer: {answer.strip()}"
