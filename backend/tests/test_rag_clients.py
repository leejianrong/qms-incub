"""Fast unit tests for the embedding-provider abstraction (no network)."""

from __future__ import annotations

import pytest

from qms_incub import rag_clients as rag_clients_mod
from qms_incub.rag_clients import _build_embed_model, _OpenAICompatibleEmbedding


class _FakeEmbeddingsResource:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def create(self, *, model: str, input: str) -> object:  # noqa: A002
        self.requests.append({"model": model, "input": input})

        class _Data:
            embedding = [0.1, 0.2, 0.3]

        class _Response:
            data = [_Data()]

        return _Response()


class _FakeClient:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddingsResource()


def test_openai_compatible_embedding_calls_embeddings_endpoint() -> None:
    client = _FakeClient()
    model = _OpenAICompatibleEmbedding(client=client, model="m")  # type: ignore[arg-type]

    assert model.get_text_embedding("hello") == [0.1, 0.2, 0.3]
    assert model.get_query_embedding("world") == [0.1, 0.2, 0.3]
    assert client.embeddings.requests == [
        {"model": "m", "input": "hello"},
        {"model": "m", "input": "world"},
    ]


def test_factory_default_is_local_provider() -> None:
    from qms_incub.config import Settings

    assert Settings().embedding_provider == "local"


def test_factory_local_provider_builds_huggingface_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    monkeypatch.setattr(rag_clients_mod.settings, "embedding_provider", "local")
    assert isinstance(_build_embed_model(), HuggingFaceEmbedding)


def test_factory_openrouter_provider_builds_hosted_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_clients_mod.settings, "embedding_provider", "openrouter")
    monkeypatch.setattr(rag_clients_mod.settings, "openrouter_api_key", "k")
    assert isinstance(_build_embed_model(), _OpenAICompatibleEmbedding)


def test_factory_openrouter_provider_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_clients_mod.settings, "embedding_provider", "openrouter")
    monkeypatch.setattr(rag_clients_mod.settings, "openrouter_api_key", None)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        _build_embed_model()


def test_factory_zenmux_provider_builds_hosted_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_clients_mod.settings, "embedding_provider", "zenmux")
    monkeypatch.setattr(rag_clients_mod.settings, "zenmux_api_key", "k")
    assert isinstance(_build_embed_model(), _OpenAICompatibleEmbedding)


def test_factory_zenmux_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rag_clients_mod.settings, "embedding_provider", "zenmux")
    monkeypatch.setattr(rag_clients_mod.settings, "zenmux_api_key", None)
    with pytest.raises(RuntimeError, match="ZENMUX_API_KEY"):
        _build_embed_model()
