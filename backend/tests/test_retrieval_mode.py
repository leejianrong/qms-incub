"""Fast unit tests for RETRIEVAL_MODE dispatch (no real Qdrant)."""

from __future__ import annotations

import pytest

from qms_incub.chat import retrieval as retrieval_mod


class _FakeNode:
    def __init__(self, text: str, meta: dict) -> None:
        self._text = text
        self.metadata = meta
        self.node_id = meta.get("chunk_id", "n")

    def get_content(self) -> str:
        return self._text


class _FakeResult:
    def __init__(self, nodes: list[_FakeNode], similarities: list[float]) -> None:
        self.nodes = nodes
        self.similarities = similarities


def _fake_node(doc_id: str) -> _FakeNode:
    return _FakeNode(f"text-{doc_id}", {"qms_document_id": doc_id, "chunk_index": 0})


def test_candidates_dispatches_to_bm25_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retrieval_mod.settings, "retrieval_mode", "bm25")

    captured: dict = {}

    class _FakeStore:
        def query(self, q):
            captured["mode"] = q.mode
            captured["sparse_top_k"] = q.sparse_top_k
            return _FakeResult([_fake_node("a")], [0.5])

    monkeypatch.setattr(retrieval_mod, "get_vector_store", lambda: _FakeStore())

    out = retrieval_mod._candidates("query", 3)
    assert [c.document_id for c in out] == ["a"]
    assert captured["sparse_top_k"] == 3


def test_candidates_dispatches_to_vector_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retrieval_mod.settings, "retrieval_mode", "vector")

    captured: dict = {}

    class _FakeStore:
        def query(self, q):
            captured["query_embedding"] = q.query_embedding
            captured["similarity_top_k"] = q.similarity_top_k
            return _FakeResult([_fake_node("b")], [0.7])

    class _FakeEmbedModel:
        def get_query_embedding(self, query: str) -> list[float]:
            captured["embedded_query"] = query
            return [0.1, 0.2]

    monkeypatch.setattr(retrieval_mod, "get_vector_store", lambda: _FakeStore())
    monkeypatch.setattr(retrieval_mod, "get_embed_model", lambda: _FakeEmbedModel())

    out = retrieval_mod._candidates("query", 3)
    assert [c.document_id for c in out] == ["b"]
    assert captured["embedded_query"] == "query"
    assert captured["query_embedding"] == [0.1, 0.2]
    assert captured["similarity_top_k"] == 3
