"""CLI entry point for the retrieval eval harness (BM25, single cutoff).

    uv run python -m qms_incub.eval [evals/retrieval_goldset.json]
        [--k 3] [--no-rerank] [--json]

With no gold-set path, defaults to ``evals/retrieval_goldset.json``. Build
or refresh that file first with ``python -m qms_incub.eval.build_goldset``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from qms_incub.eval.dataset import load_goldset
from qms_incub.eval.harness import DEFAULT_K, evaluate

_DEFAULT_GOLDSET = Path("evals/retrieval_goldset.json")


def _row(label: str, m: dict[str, float]) -> str:
    return (
        f"  {label:<16}  NDCG {m['ndcg']:.3f}   "
        f"Recall {m['recall']:.3f}   MRR {m['mrr']:.3f}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qms_incub.eval")
    parser.add_argument(
        "goldset", type=Path, nargs="?", default=_DEFAULT_GOLDSET,
        help=f"path to the gold-set JSON (default: {_DEFAULT_GOLDSET})",
    )
    parser.add_argument("--k", type=int, default=DEFAULT_K, help=f"cutoff (default {DEFAULT_K})")
    parser.add_argument("--no-rerank", action="store_true", help="skip the reranker")
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = parser.parse_args(argv)

    goldset = load_goldset(args.goldset)
    report = evaluate(goldset, k=args.k, rerank=not args.no_rerank)

    if args.json:
        print(json.dumps(asdict(report), indent=2))
        return 0

    k = report.k
    print(f"gold set : {args.goldset}  "
          f"({report.n_answerable} answerable + {report.n_guardrail} guardrail)")
    print(f"retrieval: mode={report.mode}  rerank={report.rerank}  k={k}")
    print()
    print(f"ANSWERABLE ({report.n_answerable})   @k={k}")
    print(_row("document", report.answerable["doc"]))
    print(_row("chunk", report.answerable["chunk"]))
    print()
    print("  by difficulty (document level)")
    for diff, d in report.by_difficulty.items():
        print(_row(f"{diff} ({d['n']})", d["doc"]))
    print()
    print(f"GUARDRAIL ({report.n_guardrail})   document recall@{k} "
          f"(named policy surfaced): {report.guardrail['doc_recall']:.3f}")
    print()

    imperfect = [
        r for r in report.per_query
        if r.doc_ndcg < 0.999 or r.doc_recall < 0.999
    ]
    imperfect.sort(key=lambda r: (r.doc_recall, r.doc_ndcg))
    print(f"IMPERFECT DOCUMENT RETRIEVAL ({len(imperfect)} of {len(report.per_query)})")
    for r in imperfect:
        tag = "guard" if r.guardrail else r.difficulty
        got = [d.replace(".pdf", "") for d in r.retrieved_docs[:5]]
        print(
            f"  {r.query_id:<7} {tag:<10} ndcg@{k}={r.doc_ndcg:.3f} recall@{k}={r.doc_recall:.3f}  "
            f"expect={r.expected_docs}  got={got}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
