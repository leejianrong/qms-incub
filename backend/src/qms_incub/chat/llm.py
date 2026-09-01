"""LLM client, provider-swappable (Q37, QUESTIONS.md): Ollama for local
dev/testing (no key), OpenRouter as ADR-0003's decided default, or ZenMux
as a promotional-window-only alternative (Q39, 2026-09-01 through
2026-09-05). All three are OpenAI-compatible endpoints, so one client
type serves any of them."""

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

    if settings.llm_provider == "zenmux":
        if not settings.zenmux_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=zenmux but ZENMUX_API_KEY is unset — "
                "set it in backend/.env."
            )
        client = OpenAI(
            api_key=settings.zenmux_api_key,
            base_url=settings.zenmux_base_url,
        )
        return client, settings.zenmux_model

    # Ollama's OpenAI-compatible endpoint accepts any non-empty api_key.
    client = OpenAI(api_key="ollama", base_url=settings.ollama_base_url)
    return client, settings.ollama_model
