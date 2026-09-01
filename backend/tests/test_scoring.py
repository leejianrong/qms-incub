"""Unit (SLICES.md § V2): the wizard scoring function and Requirement-to-
tier matching are pure functions, tested without a DB."""

import pytest

from qms_incub.compliance.scoring import (
    RequirementSummary,
    filter_requirements_by_tier,
    score_risk_tier,
)


@pytest.mark.parametrize(
    "data_sensitivity_high,customer_facing,regulatory_exposure,expected",
    [
        (False, False, False, "low"),
        (True, False, False, "medium"),
        (False, True, False, "medium"),
        (False, False, True, "medium"),
        (True, True, False, "medium"),
        (True, False, True, "medium"),
        (False, True, True, "medium"),
        (True, True, True, "high"),
    ],
)
def test_score_risk_tier_all_combinations(
    data_sensitivity_high: bool, customer_facing: bool, regulatory_exposure: bool, expected: str
) -> None:
    assert (
        score_risk_tier(
            data_sensitivity_high=data_sensitivity_high,
            customer_facing=customer_facing,
            regulatory_exposure=regulatory_exposure,
        )
        == expected
    )


def test_filter_requirements_by_tier_returns_exact_matches() -> None:
    requirements = [
        RequirementSummary(id="r-low", risk_tiers=["low", "medium", "high"]),
        RequirementSummary(id="r-medium-high", risk_tiers=["medium", "high"]),
        RequirementSummary(id="r-high-only", risk_tiers=["high"]),
    ]

    assert {r.id for r in filter_requirements_by_tier(requirements, "low")} == {"r-low"}
    assert {r.id for r in filter_requirements_by_tier(requirements, "medium")} == {
        "r-low",
        "r-medium-high",
    }
    assert {r.id for r in filter_requirements_by_tier(requirements, "high")} == {
        "r-low",
        "r-medium-high",
        "r-high-only",
    }
