# ADR-0008: Compliance Standard → Clause → Requirement is user-defined data, not a hardcoded schema

- Status: Accepted
- Date: 2026-08-31
- Deciders: leejianrong (user, round 5); agent (plan-new-project skill — formalizes assumed default Q2)

## Context

Q2 already assumed the compliance framework would be generic, in-app
content rather than a hardcoded external standard (ISO 13485, 21 CFR Part
11, etc.). The user confirmed this directly and gave it a concrete shape:
a three-level hierarchy — Compliance Standard → Clause → Requirement —
entered and maintained by the QA-author as ordinary application data, not
baked into the schema or code as a fixed regulatory model. This is the
entity the traceability matrix is actually built on: a `Requirement`
(under a `Clause`, under a `Standard`) is the thing a `TodoItem` traces
back to, and the thing an uploaded `Artifact` is proof of compliance
against.

## Decision

Three new entities, all user-authored, all org-scoped (ADR-0004):
`ComplianceStandard` (name, description), `Clause` (belongs to a Standard,
ordering, text), `Requirement` (belongs to a Clause, description, and the
attributes that drive todo generation — e.g. which risk tiers it applies
to). `TodoItem` (from the wizard flow, S2) is generated from the set of
`Requirement`s applicable to a project's risk tier, rather than from an
opaque "practice" string in a flat mapping config. This makes the
traceability chain concrete and queryable end to end: Standard → Clause →
Requirement → TodoItem → Artifact. No field in this hierarchy assumes or
references a real external standard's structure (no clause-numbering
scheme, no regulatory citation format) — it's freeform text the QA-author
defines.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Hardcode a real standard's structure (e.g. ISO 13485 clause numbering) | Explicitly rejected by the user; also forecloses using the tool for any other standard without a schema change |
| Keep the flat tier-to-practices mapping config (round-1/2 default) | Works for generating todos but gives no traceability object to point an `Artifact` at beyond a string — weaker than what "traceability" implies |
| Free-text requirements with no Standard/Clause grouping | Loses the hierarchy the user explicitly asked for, and makes "which standard does this project need to comply with" unanswerable as a query |

## Consequences

Gains: the traceability matrix is now a real, queryable chain rather than
a config table joined to opaque strings, and QA-authors can define
multiple standards (or revise one) without a code change. Costs: the
wizard's classification-to-todo mapping (PLAN §Implementation decisions,
originally "3 fixed dimensions → tier → mapping config") now needs
`Requirement` rows tagged with the risk tiers they apply to, which is a
small but real addition to the classification wizard's build (V2 in
SLICES.md). Forecloses hardcoding any real regulatory schema later without
a deliberate, separate decision.
