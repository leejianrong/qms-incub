"""Pure functions for the classification wizard (S1) and todo generation's
Requirement-to-tier matching (S2). No DB access here — kept pure so the
mapping is unit-testable independent of persistence (Q8, ADR-0008)."""

from __future__ import annotations

from dataclasses import dataclass

from qms_incub.compliance.models import RiskTier


def score_risk_tier(
    *, data_sensitivity_high: bool, customer_facing: bool, regulatory_exposure: bool
) -> RiskTier:
    """3 fixed boolean dimensions (Q8) -> a risk tier. The count of "risky"
    answers drives the tier: 0 -> low, 1-2 -> medium, 3 -> high."""
    risky_count = sum([data_sensitivity_high, customer_facing, regulatory_exposure])
    if risky_count == 0:
        return "low"
    if risky_count == 3:
        return "high"
    return "medium"


@dataclass(frozen=True)
class RequirementSummary:
    id: str
    risk_tiers: list[str]


def filter_requirements_by_tier(
    requirements: list[RequirementSummary], tier: RiskTier
) -> list[RequirementSummary]:
    """Which Requirements a Project at this risk tier must generate a
    TodoItem for — exactly the Requirements tagged with this tier."""
    return [r for r in requirements if tier in r.risk_tiers]
