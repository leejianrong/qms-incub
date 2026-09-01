"""Unit + demo tests for the domain profile and corpus plan (Slice 3 test
plan): the validator catches a dangling cross-reference and a duplicate ID,
and the committed corpus-plan.json itself is valid."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from synthetic_corpus.corpus_plan import CorpusPlan, load_corpus_plan, load_domain_profile

_REPO_ROOT = Path(__file__).parent.parent
_EXPECTED_ENTRY_COUNT = 10


def test_committed_corpus_plan_has_ten_unique_ids_and_resolvable_cross_references() -> None:
    plan = load_corpus_plan(_REPO_ROOT / "corpus-plan.json")

    assert len(plan.entries) == _EXPECTED_ENTRY_COUNT
    doc_ids = [entry.doc_id for entry in plan.entries]
    assert len(doc_ids) == len(set(doc_ids))


def test_committed_domain_profile_loads() -> None:
    profile = load_domain_profile(_REPO_ROOT / "domain-profile.json")

    assert profile.business_function
    assert profile.roles
    assert profile.policy_topics
    assert profile.standards_bodies


def test_validator_catches_dangling_cross_reference() -> None:
    with pytest.raises(ValidationError, match="POL-999"):
        CorpusPlan.model_validate(
            {
                "entries": [
                    {
                        "doc_id": "POL-001",
                        "title": "A",
                        "topic": "T",
                        "cross_references": ["POL-999"],
                    },
                    {"doc_id": "POL-002", "title": "B", "topic": "T", "cross_references": []},
                ]
            }
        )


def test_validator_catches_duplicate_doc_id() -> None:
    with pytest.raises(ValidationError, match="POL-001"):
        CorpusPlan.model_validate(
            {
                "entries": [
                    {"doc_id": "POL-001", "title": "A", "topic": "T", "cross_references": []},
                    {"doc_id": "POL-001", "title": "B", "topic": "T", "cross_references": []},
                ]
            }
        )
