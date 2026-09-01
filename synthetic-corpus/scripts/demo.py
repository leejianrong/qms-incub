#!/usr/bin/env python3
"""Slice 1 demo: render the hand-written demo document (one lane-free
flowchart, one 3-lane swim-lane) to PDF for visual inspection.

Run from `synthetic-corpus/`: `uv run python scripts/demo.py`
"""

from __future__ import annotations

from pathlib import Path

from synthetic_corpus.demo import build_demo_document
from synthetic_corpus.render.document import export_document_pdf

_OUTPUT_PATH = Path(__file__).parent.parent / "output" / "demo.pdf"


def main() -> None:
    document = build_demo_document()
    export_document_pdf(document, _OUTPUT_PATH)
    print(f"Wrote {_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
