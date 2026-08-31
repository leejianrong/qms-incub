"""Local CLI for V5 synthetic batch generation (SLICES.md § V5).

Deliberately NOT exposed through the web app (no HTTP endpoint, no UI):
the app itself is a QMS platform for uploading and querying real policy
documents. Synthetic generation exists only to exercise the RAG pipeline
locally while real QMS documents aren't available (they're sensitive).
Run with `make batch` or directly, e.g.:

    uv run python -m qms_incub.batch_v5 --count 20 --seed 1
"""

from __future__ import annotations

import argparse

from qms_incub.documents.batch import run_batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5, help="number of documents to generate")
    parser.add_argument("--seed", type=int, default=0, help="random seed, for reproducibility")
    parser.add_argument("--table-row-min", type=int, default=2)
    parser.add_argument("--table-row-max", type=int, default=6)
    parser.add_argument("--flowchart-step-min", type=int, default=2)
    parser.add_argument("--flowchart-step-max", type=int, default=6)
    args = parser.parse_args()

    results = run_batch(
        count=args.count,
        seed=args.seed,
        table_row_range=(args.table_row_min, args.table_row_max),
        flowchart_step_range=(args.flowchart_step_min, args.flowchart_step_max),
    )

    succeeded = [r for r in results if r.status == "embedded"]
    failed = [r for r in results if r.status != "embedded"]

    for r in results:
        detail = f"{r.chunk_count} chunk(s)" if r.status == "embedded" else (r.error or "")
        print(f"  [{r.status:>8}] {r.document_id}  {detail}")

    print(f"\n{len(succeeded)}/{len(results)} processed successfully.")
    if failed:
        print(f"{len(failed)} failed — see errors above.")


if __name__ == "__main__":
    main()
