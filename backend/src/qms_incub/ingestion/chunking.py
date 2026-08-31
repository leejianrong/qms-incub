"""Text chunking (S6, ADR-0009) — pure function, no infra, fast-tested."""

from __future__ import annotations

from llama_index.core.node_parser import SentenceSplitter

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    if not text.strip():
        return []
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)
