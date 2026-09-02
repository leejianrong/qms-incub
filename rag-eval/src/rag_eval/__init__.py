"""Retrieval evaluation harness.

Runs BM25 retrieval (+ reranker) over a gold set derived from the
synthetic-corpus Q&A markdown and reports NDCG@k, Recall@k, and MRR at
document and chunk granularity, k=3 by default.

Two steps, both run from ``rag-eval/`` with Qdrant up and the corpus
ingested:

    uv run python -m rag_eval.build_goldset   # (re)build the gold set
    uv run python -m rag_eval                 # score retrieval
"""
