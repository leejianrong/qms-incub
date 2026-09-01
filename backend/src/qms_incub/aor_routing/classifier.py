"""Semantic AOR routing using the same local embeddings as the RAG pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from qms_incub.ingestion.chunking import chunk_text
from qms_incub.ingestion.docling_parse import extract_pdf_text
from qms_incub.paths import AOR_REFERENCE_DIR
from qms_incub.rag_clients import get_embed_model

ROUTE_FILES = {"rt": "rt.txt", "ssd": "ssd.txt"}
REVIEW_MARGIN = 0.03


class EmbeddingModel(Protocol):
    def get_text_embedding(self, text: str) -> list[float]: ...


@dataclass(frozen=True)
class RouteClassification:
    route: str
    scores: dict[str, float]
    confidence: float
    needs_review: bool
    evidence_excerpt: str


def _cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _mean(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise ValueError("Cannot average an empty list of embeddings")
    dimensions = len(vectors[0])
    if any(len(vector) != dimensions for vector in vectors):
        raise ValueError("Embedding dimensions do not match")
    return [sum(vector[i] for vector in vectors) / len(vectors) for i in range(dimensions)]


def _embed_chunks(text: str, model: EmbeddingModel) -> tuple[list[str], list[list[float]]]:
    chunks = chunk_text(text, chunk_size=256, chunk_overlap=30)
    if not chunks:
        raise ValueError("Document contains no extractable text")
    return chunks, [model.get_text_embedding(chunk) for chunk in chunks]


def classify_text(
    aor_text: str,
    *,
    reference_dir: Path = AOR_REFERENCE_DIR,
    embed_model: EmbeddingModel | None = None,
) -> RouteClassification:
    """Classify extracted AOR text against the two labeled route descriptions."""
    model = embed_model or get_embed_model()
    aor_chunks, aor_embeddings = _embed_chunks(aor_text, model)
    aor_centroid = _mean(aor_embeddings)

    scores: dict[str, float] = {}
    reference_embeddings: dict[str, list[list[float]]] = {}
    for route, filename in ROUTE_FILES.items():
        path = reference_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing AOR route reference: {path}")
        _, embeddings = _embed_chunks(path.read_text(encoding="utf-8"), model)
        reference_embeddings[route] = embeddings
        scores[route] = _cosine(aor_centroid, _mean(embeddings))

    ranked = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]
    route, runner_up = ranked
    margin = scores[route] - scores[runner_up]

    selected_references = reference_embeddings[route]
    evidence_index = max(
        range(len(aor_embeddings)),
        key=lambda i: max(_cosine(aor_embeddings[i], ref) for ref in selected_references),
    )
    return RouteClassification(
        route=route,
        scores={name: round(score, 4) for name, score in scores.items()},
        # Heuristic until a larger labeled AOR set is available for
        # calibration; `needs_review` is the actual routing guardrail.
        confidence=round(0.5 + margin / (2 * (margin + 0.05)), 4),
        needs_review=margin < REVIEW_MARGIN,
        evidence_excerpt=aor_chunks[evidence_index][:500],
    )


def classify_aor_pdf(
    pdf_path: Path,
    *,
    reference_dir: Path = AOR_REFERENCE_DIR,
    embed_model: EmbeddingModel | None = None,
) -> RouteClassification:
    return classify_text(
        extract_pdf_text(pdf_path), reference_dir=reference_dir, embed_model=embed_model
    )
