"""Fast unit tests for the retrieval eval metrics + gold-set loading
(no Qdrant, no LLM)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from qms_incub.eval.dataset import load_goldset
from qms_incub.eval.metrics import dcg, ndcg_at_k, recall_at_k, reciprocal_rank


def test_dcg_matches_manual_computation() -> None:
    expected = 3 / math.log2(2) + 2 / math.log2(3) + 3 / math.log2(4)
    assert dcg([3.0, 2.0, 3.0]) == pytest.approx(expected)


def test_ndcg_perfect_ranking_is_one() -> None:
    assert ndcg_at_k([2.0, 1.0, 0.0], [2.0, 1.0, 0.0], k=3) == pytest.approx(1.0)


def test_ndcg_reversed_ranking_is_between_zero_and_one() -> None:
    score = ndcg_at_k([0.0, 1.0, 2.0], [2.0, 1.0, 0.0], k=3)
    assert 0.0 < score < 1.0


def test_ndcg_is_zero_when_no_relevant_items() -> None:
    assert ndcg_at_k([0.0, 0.0], [], k=2) == 0.0


def test_ndcg_penalises_low_recall_via_ideal_gains() -> None:
    # One relevant doc retrieved at rank 1, but the gold set knows about
    # three relevant docs -> IDCG covers all three, so NDCG < 1.
    score = ndcg_at_k([2.0], [2.0, 2.0, 2.0], k=4)
    assert score < 1.0


def test_recall_at_k_counts_gold_hits_in_topk() -> None:
    retrieved = ["a", "b", "c", "d"]
    assert recall_at_k(retrieved, {"b", "d", "z"}, k=4) == pytest.approx(2 / 3)
    assert recall_at_k(retrieved, {"b", "d"}, k=1) == pytest.approx(0.0)


def test_recall_at_k_is_zero_without_relevant_items() -> None:
    assert recall_at_k(["a"], set(), k=1) == 0.0


def test_reciprocal_rank_uses_first_hit() -> None:
    assert reciprocal_rank(["a", "b", "c"], {"b", "c"}) == pytest.approx(0.5)
    assert reciprocal_rank(["a", "b"], {"z"}) == 0.0


def test_load_goldset_parses_queries_and_derives_doc_relevance(tmp_path: Path) -> None:
    path = tmp_path / "gold.json"
    path.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "QA-1",
                        "query": "hi",
                        "difficulty": "multi-hop",
                        "guardrail": False,
                        "relevant": {"POL-001.pdf::3": 2, "POL-001.pdf::4": 1, "POL-006.pdf::2": 1},
                        "relevant_documents": ["POL-001.pdf", "POL-006.pdf"],
                    }
                ]
            }
        )
    )
    q = load_goldset(path)[0]
    assert q.query_id == "QA-1"
    assert q.difficulty == "multi-hop"
    assert q.relevant_chunks == {
        "POL-001.pdf::3": 2.0,
        "POL-001.pdf::4": 1.0,
        "POL-006.pdf::2": 1.0,
    }
    # doc grade is the max over that doc's chunk grades
    assert q.relevant_docs == {"POL-001.pdf": 2.0, "POL-006.pdf": 1.0}


def test_load_goldset_rejects_empty(tmp_path: Path) -> None:
    path = tmp_path / "gold.json"
    path.write_text(json.dumps({"queries": []}))
    with pytest.raises(ValueError, match="no queries"):
        load_goldset(path)
