#!/usr/bin/env python3
"""Slice 2 CLI: render every JSON fixture in `documents/` to a PDF in
`output/`.

Run from `synthetic-corpus/`: `uv run python scripts/generate.py`
"""

from __future__ import annotations

from synthetic_corpus.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
