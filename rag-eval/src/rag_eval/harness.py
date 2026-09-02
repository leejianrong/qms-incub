"""Run BM25 retrieval over the gold set and score it at a single cutoff.

Fixed to ``mode="bm25"`` — the reranker reorders the same candidate set
regardless of how it was fetched, so dense/hybrid gave identical numbers
here; BM25 is the cheapest way to feed it.

Two granularities per query:

- **document** (headline) — did retrieval surface the right policy/policies,
  and how highly ranked. Robust: one ~2.5k-char chunk spans several policy
  sections, so chunk identity is fuzzy but document identity is not.
- **chunk** (secondary) — did it surface the specific passage. Noisier,
  reported for completeness.

Metrics at cutoff k: NDCG@k, Recall@k, MRR (rank of first hit). Aggregated
over the answerable queries, broken out by difficulty; the guardrail
queries (corpus deliberately doesn't specify the answer) are reported
separately as document recall only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qms_incub.rag.factory import get_retrieval_port

from rag_eval.dataset import EvalQuery
from rag_eval.metrics import ndcg_at_k, recall_at_k, reciprocal_rank

MODE = "bm25"  # the retrieval port is BM25-only; kept as a label for the report
DEFAULT_K = 3


@dataclass
class QueryReport:
    query_id: str
    difficulty: str
    guardrail: bool
    expected_docs: list[str]
    retrieved_docs: list[str]
    retrieved_chunks: list[str]
    doc_ndcg: float = 0.0
    doc_recall: float = 0.0
    doc_mrr: float = 0.0
    chunk_ndcg: float = 0.0
    chunk_recall: float = 0.0
    chunk_mrr: float = 0.0


@dataclass
class EvalReport:
    k: int
    mode: str
    rerank: bool
    n_answerable: int
    n_guardrail: int
    # {"doc"|"chunk": {"ndcg": float, "recall": float, "mrr": float}}
    answerable: dict[str, Any] = field(default_factory=dict)
    # {difficulty: {"n": int, "doc": {...}, "chunk": {...}}}
    by_difficulty: dict[str, Any] = field(default_factory=dict)
    guardrail: dict[str, Any] = field(default_factory=dict)  # {"doc_recall": float}
    per_query: list[QueryReport] = field(default_factory=list)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _score(
    ranked: list[str], relevant: dict[str, float], k: int
) -> tuple[float, float, float]:
    rel_set = set(relevant)
    gains = [relevant.get(item, 0.0) for item in ranked]
    ideal = list(relevant.values())
    return (
        ndcg_at_k(gains, ideal, k),
        recall_at_k(ranked, rel_set, k),
        reciprocal_rank(ranked, rel_set),
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _aggregate(reports: list[QueryReport]) -> dict[str, Any]:
    return {
        level: {
            "ndcg": _mean([getattr(r, f"{level}_ndcg") for r in reports]),
            "recall": _mean([getattr(r, f"{level}_recall") for r in reports]),
            "mrr": _mean([getattr(r, f"{level}_mrr") for r in reports]),
        }
        for level in ("doc", "chunk")
    }


def evaluate(
    goldset: list[EvalQuery], k: int = DEFAULT_K, *, rerank: bool = True
) -> EvalReport:
    per_query: list[QueryReport] = []

    for q in goldset:
        chunks = get_retrieval_port().retrieve(q.query, k=k, rerank=rerank)
        ranked_docs = _dedupe([c.document_title for c in chunks])
        ranked_chunks = [f"{c.document_title}::{c.chunk_index}" for c in chunks]

        d_ndcg, d_recall, d_mrr = _score(ranked_docs, q.relevant_docs, k)
        c_ndcg, c_recall, c_mrr = _score(ranked_chunks, q.relevant_chunks, k)

        per_query.append(
            QueryReport(
                query_id=q.query_id,
                difficulty=q.difficulty,
                guardrail=q.guardrail,
                expected_docs=sorted(q.relevant_docs),
                retrieved_docs=ranked_docs,
                retrieved_chunks=ranked_chunks,
                doc_ndcg=d_ndcg,
                doc_recall=d_recall,
                doc_mrr=d_mrr,
                chunk_ndcg=c_ndcg,
                chunk_recall=c_recall,
                chunk_mrr=c_mrr,
            )
        )

    answerable = [r for r in per_query if not r.guardrail]
    guardrail = [r for r in per_query if r.guardrail]

    by_difficulty: dict[str, Any] = {}
    for diff in sorted({r.difficulty for r in answerable}):
        bucket = [r for r in answerable if r.difficulty == diff]
        by_difficulty[diff] = {"n": len(bucket), **_aggregate(bucket)}

    return EvalReport(
        k=k,
        mode=MODE,
        rerank=rerank,
        n_answerable=len(answerable),
        n_guardrail=len(guardrail),
        answerable=_aggregate(answerable),
        by_difficulty=by_difficulty,
        guardrail={"doc_recall": _mean([r.doc_recall for r in guardrail])},
        per_query=per_query,
    )
