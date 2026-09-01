#!/usr/bin/env python3
"""Slice 3 demo: confirm corpus-plan.json has exactly 10 entries, unique doc
IDs, and every cross-reference resolves to a real doc ID in the same plan.

Run from `synthetic-corpus/`: `uv run python scripts/validate_corpus_plan.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError

from synthetic_corpus.corpus_plan import load_corpus_plan

_CORPUS_PLAN_PATH = Path(__file__).parent.parent / "corpus-plan.json"
_EXPECTED_ENTRY_COUNT = 10


def main() -> int:
    try:
        plan = load_corpus_plan(_CORPUS_PLAN_PATH)
    except ValidationError as exc:
        print(f"corpus-plan.json is invalid:\n{exc}", file=sys.stderr)
        return 1

    if len(plan.entries) != _EXPECTED_ENTRY_COUNT:
        print(
            f"expected exactly {_EXPECTED_ENTRY_COUNT} entries, "
            f"found {len(plan.entries)}",
            file=sys.stderr,
        )
        return 1

    print(
        f"corpus-plan.json OK: {len(plan.entries)} entries, unique IDs, "
        f"all cross-references resolve."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
