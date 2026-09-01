"""Classify one or more AOR PDFs without running the API or UI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qms_incub.aor_routing.classifier import classify_aor_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path, help="AOR PDF file(s) to classify")
    args = parser.parse_args()

    for pdf in args.pdfs:
        result = classify_aor_pdf(pdf)
        print(
            json.dumps(
                {
                    "file": str(pdf),
                    "route": result.route,
                    "label": {"rt": "R&T", "ssd": "SSD"}[result.route],
                    "scores": result.scores,
                    "confidence": result.confidence,
                    "needs_review": result.needs_review,
                    "evidence_excerpt": result.evidence_excerpt,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
