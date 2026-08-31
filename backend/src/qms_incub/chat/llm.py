"""LLM client, provider-swappable (Q37, QUESTIONS.md): Ollama for local
dev/testing (no key), OpenRouter as ADR-0003's decided default otherwise.
Both are OpenAI-compatible endpoints, so one client type serves either."""

from __future__ import annotations

from openai import OpenAI

from qms_incub.config import settings


def get_llm_client() -> tuple[OpenAI, str]:
    """Returns (client, model) for the configured LLM provider."""
    if settings.llm_provider == "openrouter":
        if not settings.openrouter_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=openrouter but OPENROUTER_API_KEY is unset — "
                "set it in backend/.env."
            )
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        return client, settings.openrouter_model

    # Ollama's OpenAI-compatible endpoint accepts any non-empty api_key.
    client = OpenAI(api_key="ollama", base_url=settings.ollama_base_url)
    return client, settings.ollama_model
