"""Unit (SLICES.md § V10): the Requirement-to-ProcessStep mapping is a
fixed choice the QA-author makes at authoring time from the fixed
ProcessStep set (Q41) — like risk_tiers, not a computed heuristic. These
test the default/override behavior of that mapping without a DB."""

from qms_incub.compliance.api import RequirementIn
from qms_incub.compliance.models import DEFAULT_PROCESS_STEP_ID


def test_requirement_in_defaults_to_the_fixed_default_process_step() -> None:
    body = RequirementIn(description="Log every change", risk_tiers=["low"])
    assert body.process_step_id == DEFAULT_PROCESS_STEP_ID == "initiation"


def test_requirement_in_accepts_an_explicit_process_step_id() -> None:
    body = RequirementIn(
        description="Run a security scan", risk_tiers=["high"], process_step_id="build"
    )
    assert body.process_step_id == "build"
