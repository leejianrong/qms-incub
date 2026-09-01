"""Persistence operations for V6 blog posts and FAQ entries."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from qms_incub.db import get_session
from qms_incub.models import BlogPost, FAQEntry


@dataclass
class BlogPostOut:
    id: str
    title: str
    body: str
    published_at: datetime.datetime | None
    chunk_count: int | None


@dataclass
class FAQEntryOut:
    id: str
    question: str
    answer: str
    published_at: datetime.datetime | None
    chunk_count: int | None


def _blog_out(row: BlogPost) -> BlogPostOut:
    return BlogPostOut(row.id, row.title, row.body, row.published_at, row.chunk_count)


def _faq_out(row: FAQEntry) -> FAQEntryOut:
    return FAQEntryOut(row.id, row.question, row.answer, row.published_at, row.chunk_count)


def create_blog(title: str, body: str) -> BlogPostOut:
    with get_session() as session:
        row = BlogPost(title=title, body=body)
        session.add(row)
        session.flush()
        return _blog_out(row)


def list_blogs() -> list[BlogPostOut]:
    with get_session() as session:
        rows = session.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
        return [_blog_out(r) for r in rows]


def get_blog(post_id: str) -> BlogPostOut | None:
    with get_session() as session:
        row = session.get(BlogPost, post_id)
        return _blog_out(row) if row else None


def update_blog(post_id: str, title: str, body: str) -> BlogPostOut | None:
    with get_session() as session:
        row = session.get(BlogPost, post_id)
        if row is None:
            return None
        row.title, row.body = title, body
        session.flush()
        return _blog_out(row)


def mark_blog_published(post_id: str, chunk_count: int) -> BlogPostOut | None:
    with get_session() as session:
        row = session.get(BlogPost, post_id)
        if row is None:
            return None
        row.published_at = datetime.datetime.now(datetime.UTC)
        row.chunk_count = chunk_count
        session.flush()
        return _blog_out(row)


def create_faq(question: str, answer: str) -> FAQEntryOut:
    with get_session() as session:
        row = FAQEntry(question=question, answer=answer)
        session.add(row)
        session.flush()
        return _faq_out(row)


def list_faqs() -> list[FAQEntryOut]:
    with get_session() as session:
        rows = session.query(FAQEntry).order_by(FAQEntry.created_at.desc()).all()
        return [_faq_out(r) for r in rows]


def get_faq(entry_id: str) -> FAQEntryOut | None:
    with get_session() as session:
        row = session.get(FAQEntry, entry_id)
        return _faq_out(row) if row else None


def update_faq(entry_id: str, question: str, answer: str) -> FAQEntryOut | None:
    with get_session() as session:
        row = session.get(FAQEntry, entry_id)
        if row is None:
            return None
        row.question, row.answer = question, answer
        session.flush()
        return _faq_out(row)


def mark_faq_published(entry_id: str, chunk_count: int) -> FAQEntryOut | None:
    with get_session() as session:
        row = session.get(FAQEntry, entry_id)
        if row is None:
            return None
        row.published_at = datetime.datetime.now(datetime.UTC)
        row.chunk_count = chunk_count
        session.flush()
        return _faq_out(row)
