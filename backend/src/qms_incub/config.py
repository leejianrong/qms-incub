"""Runtime configuration, read from the environment / backend/.env.

LLM provider is swappable (Q37, QUESTIONS.md): `ollama` for local dev/
testing with no API key, or `openrouter` — the ADR-0003-decided default
for anything beyond local dev. `zenmux` is a third option, preferred only
during a promotional API-key window, 2026-09-01 through 2026-09-05 (Q39)
— see README.md/CLAUDE.md. All three are OpenAI-compatible endpoints, so
one client implementation serves any of them (see chat/llm.py).
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: Literal["ollama", "openrouter", "zenmux"] = "ollama"

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5:7b-instruct-q4_K_M"

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Cheap by default (ADR-0003 decides OpenRouter; cost-consciousness is
    # a running-cost preference, not an architectural decision) — override
    # via OPENROUTER_MODEL for anything else on OpenRouter's catalog.
    openrouter_model: str = "deepseek/deepseek-chat"

    # Q39: promotional-window provider (2026-09-01 through 2026-09-05 only).
    zenmux_api_key: str | None = None
    zenmux_base_url: str = "https://zenmux.ai/api/"
    zenmux_model: str = "deepseek/deepseek-chat"

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "qms_incub_corpus"

    # Matches docker-compose.yml's postgres service (ADR-0005/ADR-0009).
    database_url: str = "postgresql+psycopg://qms_incub:qms_incub@localhost:5433/qms_incub"


settings = Settings()
