"""HTTP API for V6's plain-text blog and FAQ CMS."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from qms_incub.content import repository
from qms_incub.content.service import (
    PublishValidationError,
    faq_corpus_text,
    validate_blog_publish,
    validate_faq_publish,
)
from qms_incub.rag.factory import get_ingestion_port

router = APIRouter()


class BlogPostIn(BaseModel):
    title: str = ""
    body: str = ""


class BlogPostOut(BaseModel):
    id: str
    title: str
    body: str
    published_at: datetime.datetime | None
    chunk_count: int | None


class FAQEntryIn(BaseModel):
    question: str = ""
    answer: str = ""


class FAQEntryOut(BaseModel):
    id: str
    question: str
    answer: str
    published_at: datetime.datetime | None
    chunk_count: int | None


def _blog_out(row: repository.BlogPostOut) -> BlogPostOut:
    return BlogPostOut(**row.__dict__)


def _faq_out(row: repository.FAQEntryOut) -> FAQEntryOut:
    return FAQEntryOut(**row.__dict__)


def _publish_error(exc: PublishValidationError) -> None:
    raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/blog-posts", status_code=201)
def create_blog(body: BlogPostIn) -> BlogPostOut:
    return _blog_out(repository.create_blog(body.title, body.body))


@router.get("/blog-posts")
def list_blogs() -> list[BlogPostOut]:
    return [_blog_out(row) for row in repository.list_blogs()]


@router.get("/blog-posts/{post_id}")
def get_blog(post_id: str) -> BlogPostOut:
    row = repository.get_blog(post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return _blog_out(row)


@router.put("/blog-posts/{post_id}")
def update_blog(post_id: str, body: BlogPostIn) -> BlogPostOut:
    row = repository.update_blog(post_id, body.title, body.body)
    if row is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return _blog_out(row)


@router.post("/blog-posts/{post_id}/publish")
def publish_blog(post_id: str) -> BlogPostOut:
    row = repository.get_blog(post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    try:
        validate_blog_publish(row.title, row.body)
    except PublishValidationError as exc:
        _publish_error(exc)
    chunk_count = get_ingestion_port().ingest_text(row.body, row.id, row.title, source_type="blog")
    published = repository.mark_blog_published(post_id, chunk_count)
    assert published is not None
    return _blog_out(published)


@router.post("/faq-entries", status_code=201)
def create_faq(body: FAQEntryIn) -> FAQEntryOut:
    return _faq_out(repository.create_faq(body.question, body.answer))


@router.get("/faq-entries")
def list_faqs() -> list[FAQEntryOut]:
    return [_faq_out(row) for row in repository.list_faqs()]


@router.get("/faq-entries/{entry_id}")
def get_faq(entry_id: str) -> FAQEntryOut:
    row = repository.get_faq(entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail="FAQ entry not found")
    return _faq_out(row)


@router.put("/faq-entries/{entry_id}")
def update_faq(entry_id: str, body: FAQEntryIn) -> FAQEntryOut:
    row = repository.update_faq(entry_id, body.question, body.answer)
    if row is None:
        raise HTTPException(status_code=404, detail="FAQ entry not found")
    return _faq_out(row)


@router.post("/faq-entries/{entry_id}/publish")
def publish_faq(entry_id: str) -> FAQEntryOut:
    row = repository.get_faq(entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail="FAQ entry not found")
    try:
        validate_faq_publish(row.question, row.answer)
    except PublishValidationError as exc:
        _publish_error(exc)
    chunk_count = get_ingestion_port().ingest_text(
        faq_corpus_text(row.question, row.answer), row.id, row.question, source_type="faq"
    )
    published = repository.mark_faq_published(entry_id, chunk_count)
    assert published is not None
    return _faq_out(published)
