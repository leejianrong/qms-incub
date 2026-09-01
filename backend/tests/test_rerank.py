"""Fast unit tests for the reranker abstraction (no network)."""

from __future__ import annotations

import pytest

from qms_incub.chat import rerank as rerank_mod
from qms_incub.chat.rerank import NoOpReranker, ZenMuxReranker, _build_reranker
from qms_incub.chat.retrieval import RetrievedChunk


def _chunk(doc_id: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        text=text,
        document_id=doc_id,
        document_title=doc_id,
        source_type="policy_document",
        score=0.0,
        chunk_id=doc_id,
    )


def test_noop_reranker_preserves_order_and_truncates() -> None:
    chunks = [_chunk("a", "x"), _chunk("b", "y"), _chunk("c", "z")]
    out = NoOpReranker().rerank("q", chunks, top_n=2)
    assert [c.document_id for c in out] == ["a", "b"]


def test_zenmux_reranker_builds_dashscope_request_and_reads_nested_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = [_chunk("a", "x"), _chunk("b", "y"), _chunk("c", "z")]
    sent: dict = {}

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            # ZenMux / DashScope nest results under "output".
            return {
                "output": {
                    "results": [
                        {"index": 2, "relevance_score": 0.9},
                        {"index": 0, "relevance_score": 0.5},
                    ]
                }
            }

    def _fake_post(url: str, *, json: dict, headers: dict, timeout: float) -> _Resp:
        sent["url"] = url
        sent["json"] = json
        sent["headers"] = headers
        return _Resp()

    monkeypatch.setattr(rerank_mod.httpx, "post", _fake_post)

    reranker = ZenMuxReranker(
        api_key="k", url="https://zenmux.ai/api/v1/rerank", model="m", timeout_s=1.0
    )
    out = reranker.rerank("q", chunks, top_n=2)

    assert sent["url"] == "https://zenmux.ai/api/v1/rerank"
    assert sent["headers"]["Authorization"] == "Bearer k"
    assert sent["json"] == {
        "model": "m",
        "input": {"query": "q", "documents": ["x", "y", "z"]},
        "parameters": {"top_n": 2, "return_documents": False},
    }
    assert [c.document_id for c in out] == ["c", "a"]
    assert out[0].score == 0.9


def test_zenmux_reranker_tolerates_flat_results(monkeypatch: pytest.MonkeyPatch) -> None:
    chunks = [_chunk("a", "x"), _chunk("b", "y")]

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"results": [{"index": 1, "relevance_score": 0.7}]}

    monkeypatch.setattr(rerank_mod.httpx, "post", lambda *a, **kw: _Resp())
    reranker = ZenMuxReranker(
        api_key="k", url="https://x/api/v1/rerank", model="m", timeout_s=1.0
    )
    out = reranker.rerank("q", chunks, top_n=2)
    assert [c.document_id for c in out] == ["b"]


def test_zenmux_reranker_empty_candidates_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_a: object, **_kw: object) -> object:
        raise AssertionError("should not call the API with no candidates")

    monkeypatch.setattr(rerank_mod.httpx, "post", _boom)
    reranker = ZenMuxReranker(
        api_key="k", url="https://x/api/v1/rerank", model="m", timeout_s=1.0
    )
    assert reranker.rerank("q", [], top_n=4) == []


def test_factory_falls_back_to_noop_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rerank_mod.settings, "reranker_provider", "zenmux")
    monkeypatch.setattr(rerank_mod.settings, "zenmux_api_key", None)
    assert isinstance(_build_reranker(), NoOpReranker)


def test_factory_none_provider_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rerank_mod.settings, "reranker_provider", "none")
    assert isinstance(_build_reranker(), NoOpReranker)
