"""Gold-set loading for retrieval evaluation.

The gold set is generated from ``synthetic-corpus/rag_policy_compliance_qa.md``
by ``rag_eval.build_goldset`` and lives at
``rag-eval/evals/retrieval_goldset.json``. Shape::

    {
      "meta": {...},
      "queries": [
        {
          "query_id": "QA-005",
          "query": "...",
          "difficulty": "multi-hop",
          "guardrail": false,
          "relevant": {"POL-001.pdf::3": 2, "POL-006.pdf::2": 1},
          "relevant_documents": ["POL-001.pdf", "POL-006.pdf"]
        }
      ]
    }

Relevance grades: 2 = the pair's own policy, 1 = a cross-referenced one,
0 = anything not listed. Judgements are keyed ``"<document_title>::<chunk_index>"``
— both stable across re-ingestion, unlike the per-upload ``document_id``.
``relevant_documents`` is the doc-level view (drop the ``::chunk_index``);
it's the headline scoring granularity because chunk boundaries here span
several policy sections, so chunk-level labels are necessarily fuzzy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalQuery:
    query_id: str
    query: str
    difficulty: str = ""
    guardrail: bool = False
    # "POL-001.pdf::3" -> grade
    relevant_chunks: dict[str, float] = field(default_factory=dict)
    # "POL-001.pdf" -> grade (max grade over that doc's relevant chunks)
    relevant_docs: dict[str, float] = field(default_factory=dict)


def load_goldset(path: Path) -> list[EvalQuery]:
    raw = json.loads(path.read_text())
    queries: list[EvalQuery] = []
    for item in raw.get("queries", []):
        relevant_chunks = {str(k): float(v) for k, v in item.get("relevant", {}).items()}
        relevant_docs: dict[str, float] = {}
        for key, grade in relevant_chunks.items():
            doc = key.split("::", 1)[0]
            relevant_docs[doc] = max(relevant_docs.get(doc, 0.0), grade)
        # Trust an explicit relevant_documents list for docs, if present.
        for doc in item.get("relevant_documents", []):
            relevant_docs.setdefault(str(doc), max(relevant_docs.values(), default=1.0))
        queries.append(
            EvalQuery(
                query_id=str(item["query_id"]),
                query=str(item["query"]),
                difficulty=str(item.get("difficulty", "")),
                guardrail=bool(item.get("guardrail", False)),
                relevant_chunks=relevant_chunks,
                relevant_docs=relevant_docs,
            )
        )
    if not queries:
        raise ValueError(f"no queries found in gold set: {path}")
    return queries
