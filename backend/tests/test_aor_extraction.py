"""Unit (SLICES.md § V9): AOR extraction prompt assembly and response
parsing are pure functions, tested without a DB or a live LLM call."""

from __future__ import annotations

import json

import pytest

from qms_incub.aor.extraction import (
    FIELDS,
    build_extraction_messages,
    parse_extraction_response,
)


def test_build_extraction_messages_requests_exactly_the_four_fields() -> None:
    messages = build_extraction_messages("Some intake document text.")
    roles = [m["role"] for m in messages]
    assert roles == ["system", "user"]
    for field in FIELDS:
        assert field in messages[0]["content"]
    assert "Some intake document text." in messages[1]["content"]


def test_parse_extraction_response_returns_all_fields() -> None:
    raw = json.dumps(
        {
            "criticality_tier": "high",
            "data_classification": "confidential",
            "external_dependencies": ["Vendor A", "Vendor B"],
            "in_house_rationale": "Existing in-house expertise.",
        }
    )
    fields = parse_extraction_response(raw)
    assert fields.criticality_tier == "high"
    assert fields.data_classification == "confidential"
    assert fields.external_dependencies == ["Vendor A", "Vendor B"]
    assert fields.in_house_rationale == "Existing in-house expertise."


def test_parse_extraction_response_tolerates_surrounding_text() -> None:
    raw = (
        "Here is the extraction:\n"
        + json.dumps(
            {
                "criticality_tier": "low",
                "data_classification": "public",
                "external_dependencies": [],
                "in_house_rationale": "n/a",
            }
        )
        + "\nDone."
    )
    fields = parse_extraction_response(raw)
    assert fields.criticality_tier == "low"


def test_parse_extraction_response_rejects_a_response_missing_a_field() -> None:
    raw = json.dumps(
        {
            "criticality_tier": "high",
            "data_classification": "confidential",
            "external_dependencies": [],
            # in_house_rationale missing
        }
    )
    with pytest.raises(ValueError, match="in_house_rationale"):
        parse_extraction_response(raw)


def test_parse_extraction_response_rejects_non_json() -> None:
    with pytest.raises(ValueError):
        parse_extraction_response("not json at all")
