"""Domain profile + corpus plan models (SHAPING.md C0/C1).

The corpus plan is the blueprint the full documents (Slice 4) get written
from: it fixes each document's ID, title, topic, and which other doc IDs it
is planned to cross-reference, so citations are correct by construction
before any prose is written.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class StandardsBody(BaseModel):
    name: str
    url: str


class DomainProfile(BaseModel):
    """Briefs the authoring process (SHAPING.md C0): what business function
    this corpus is for, who its typical roles are, what it typically writes
    policies about, and which external standards it cites."""

    business_function: str
    roles: list[str]
    policy_topics: list[str]
    standards_bodies: list[StandardsBody]


class CorpusPlanEntry(BaseModel):
    doc_id: str
    title: str
    topic: str
    owner_role: str | None = None
    cross_references: list[str] = Field(default_factory=list)


class CorpusPlan(BaseModel):
    entries: list[CorpusPlanEntry]

    @model_validator(mode="after")
    def _unique_ids_and_resolvable_cross_references(self) -> CorpusPlan:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for entry in self.entries:
            if entry.doc_id in seen:
                duplicates.add(entry.doc_id)
            seen.add(entry.doc_id)
        if duplicates:
            raise ValueError(f"duplicate doc IDs in corpus plan: {sorted(duplicates)!r}")

        known_ids = seen
        for entry in self.entries:
            for ref in entry.cross_references:
                if ref not in known_ids:
                    raise ValueError(
                        f"{entry.doc_id!r} cross-references {ref!r}, "
                        f"which is not a doc ID in this corpus plan"
                    )
        return self


def load_domain_profile(path: Path) -> DomainProfile:
    return DomainProfile.model_validate(json.loads(path.read_text()))


def load_corpus_plan(path: Path) -> CorpusPlan:
    return CorpusPlan.model_validate(json.loads(path.read_text()))
