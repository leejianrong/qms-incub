"""AOR structured-field extraction (S10, Q40): a project's own intake
document, Docling-parsed then LLM-extracted into a fixed, small set of
fields. Extraction of the document's existing content, not authoring new
content — stays inside ADR-0012's boundary. Kept pure (prompt assembly,
response parsing) so it's unit-testable without a live LLM call."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

FIELDS = (
    "criticality_tier",
    "data_classification",
    "external_dependencies",
    "in_house_rationale",
)

SYSTEM_PROMPT = (
    "You extract structured fields from a project intake document (an AOR). "
    'Respond with ONLY a JSON object with exactly these keys: "criticality_tier" '
    '(string), "data_classification" (string), "external_dependencies" (array of '
    'strings), "in_house_rationale" (string). Use "unknown" (or an empty array for '
    "external_dependencies) for any field the document doesn't state. Do not "
    "include any other text before or after the JSON object."
)


@dataclass(frozen=True)
class AorFields:
    criticality_tier: str
    data_classification: str
    external_dependencies: list[str]
    in_house_rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "criticality_tier": self.criticality_tier,
            "data_classification": self.data_classification,
            "external_dependencies": self.external_dependencies,
            "in_house_rationale": self.in_house_rationale,
        }


def build_extraction_messages(document_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Intake document:\n\n{document_text}"},
    ]


def parse_extraction_response(raw: str) -> AorFields:
    """Raises ValueError if the response isn't JSON, or is missing any of
    the four fixed fields — an incomplete extraction is rejected outright
    rather than silently defaulting a real field."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in extraction response: {raw!r}")

    data = json.loads(match.group(0))
    missing = [field for field in FIELDS if field not in data]
    if missing:
        raise ValueError(f"Extraction response missing field(s): {missing}")

    external_dependencies = data["external_dependencies"]
    if isinstance(external_dependencies, str):
        external_dependencies = [external_dependencies]

    return AorFields(
        criticality_tier=str(data["criticality_tier"]),
        data_classification=str(data["data_classification"]),
        external_dependencies=[str(dep) for dep in external_dependencies],
        in_house_rationale=str(data["in_house_rationale"]),
    )
