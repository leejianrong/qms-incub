"""Ranking metrics for retrieval evaluation. Pure functions, no infra —
fast-testable in isolation."""

from __future__ import annotations

from math import log2


def dcg(gains: list[float]) -> float:
    """Discounted cumulative gain for a ranked list of relevance gains.

    Position i (0-indexed) is discounted by ``log2(i + 2)`` so the first
    result has discount ``log2(2) == 1``.
    """
    return sum(gain / log2(i + 2) for i, gain in enumerate(gains))


def ndcg_at_k(ranked_gains: list[float], ideal_gains: list[float], k: int) -> float:
    """NDCG@k.

    ``ranked_gains`` — relevance gain of each retrieved item, in the order
    they were retrieved (0 for retrieved-but-irrelevant items).
    ``ideal_gains`` — the gains of *all* known-relevant items for the
    query (from the gold set), used to build the ideal ranking. Passing
    the full set here (not just what was retrieved) makes NDCG penalise
    low recall.

    Returns 0.0 when there are no relevant items (IDCG == 0).
    """
    idcg = dcg(sorted(ideal_gains, reverse=True)[:k])
    if idcg == 0.0:
        return 0.0
    return dcg(ranked_gains[:k]) / idcg


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the gold-relevant items that appear in the top-k.

    Returns 0.0 when the query has no relevant items.
    """
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """1 / rank of the first relevant item (0.0 if none retrieved)."""
    for i, item in enumerate(retrieved):
        if item in relevant:
            return 1.0 / (i + 1)
    return 0.0
