"""Pure compliance-percentage calculation (S3), kept separate from
persistence so it's unit-testable against a plain list of statuses."""

from __future__ import annotations


def compliance_percentage(statuses: list[str]) -> float:
    if not statuses:
        return 0.0
    complied = sum(1 for status in statuses if status == "complied")
    return 100.0 * complied / len(statuses)
