"""Fast tests for POST /retrieve (retrieval pipeline is stubbed — no
Qdrant, no reranker network call)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from qms_incub import main
from qms_incub.chat.retrieval import RetrievedChunk

client = TestClient(main.app)


def _chunk(doc_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        text=f"text for {doc_id}",
        document_id=doc_id,
        document_title=doc_id.title(),
        source_type="policy_document",
        score=score,
        chunk_id=f"{doc_id}-0",
        chunk_index=0,
    )


def test_retrieve_returns_ranked_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def _fake_retrieve(query: str, *, k: int, rerank: bool, candidate_k):
        captured.update(query=query, k=k, rerank=rerank, candidate_k=candidate_k)
        return [_chunk("doc-a", 0.9), _chunk("doc-b", 0.4)]

    monkeypatch.setattr(main, "retrieve", _fake_retrieve)

    response = client.post("/retrieve", json={"query": "who approves changes?", "k": 2})
    assert response.status_code == 200

    body = response.json()
    assert body["mode"] == "bm25"
    assert body["rerank"] is True
    assert body["k"] == 2
    assert [c["document_id"] for c in body["chunks"]] == ["doc-a", "doc-b"]
    assert body["chunks"][0]["score"] == 0.9
    assert captured == {
        "query": "who approves changes?",
        "k": 2,
        "rerank": True,
        "candidate_k": None,
    }


def test_retrieve_passes_through_rerank_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def _fake_retrieve(query: str, *, k: int, rerank: bool, candidate_k):
        captured.update(rerank=rerank)
        return []

    monkeypatch.setattr(main, "retrieve", _fake_retrieve)

    response = client.post("/retrieve", json={"query": "q", "rerank": False})
    assert response.status_code == 200
    assert response.json()["mode"] == "bm25"
    assert captured == {"rerank": False}


def test_retrieve_maps_backend_error_to_502(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_a: object, **_kw: object) -> list[RetrievedChunk]:
        raise RuntimeError("collection 'qms_incub_corpus' has no sparse vectors")

    monkeypatch.setattr(main, "retrieve", _boom)

    response = client.post("/retrieve", json={"query": "q"})
    assert response.status_code == 502
    assert "sparse vectors" in response.json()["detail"]
