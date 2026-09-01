"""Unit (SLICES.md § V3): compliance % is a pure function of todo
statuses."""

import pytest

from qms_incub.compliance.metrics import compliance_percentage


@pytest.mark.parametrize(
    "statuses,expected",
    [
        ([], 0.0),
        (["pending", "pending"], 0.0),
        (["complied", "complied"], 100.0),
        (["complied", "pending"], 50.0),
        (["complied", "pending", "pending", "pending"], 25.0),
    ],
)
def test_compliance_percentage(statuses: list[str], expected: float) -> None:
    assert compliance_percentage(statuses) == expected
