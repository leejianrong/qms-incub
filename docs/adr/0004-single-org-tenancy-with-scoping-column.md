# ADR-0004: Single-org tenancy in v1, with an org-scoping column on every table

- Status: Accepted
- Date: 2026-08-31
- Deciders: agent (plan-new-project skill, assumed default Q4)

## Context

The idea describes project managers "in a large company" complying with
that company's QMS policies — one organization's internal tool, not a
product serving multiple companies from one deployment. Nothing in the
idea implies multi-tenant SaaS. But retrofitting an org boundary onto a
schema that was never scoped is expensive: every query gains a filter,
every table needs a migration, and any accidental cross-org data exposure
found late is a security incident, not just a bug.

## Decision

Ship v1 as a single-org tool — no org-switcher UI, no per-org billing or
signup flow. However, every table (`Project`, `PolicyDocument`, `BlogPost`,
`FAQEntry`, etc.) carries an `org_id` column from the start, defaulted to a
single seeded org row. Application queries filter by it even though there
is only one value in practice.

## Alternatives considered

| Option | Why not |
|--------|---------|
| No org column at all | Cheapest now, but adding multi-tenancy later means a schema migration across every table plus an audit of every query for missing scoping — the exact mistake this ADR exists to avoid |
| Full multi-tenant SaaS in v1 (org signup, switching, billing) | Not implied by the idea; the user's stated focus is UI/UX and workflows for one PM persona, not a SaaS business layer |

## Consequences

Gains: multi-tenancy becomes a UI and auth-layer feature later, not a data
migration. Costs: a small amount of unused-for-now complexity — every
query in v1 carries a filter that only ever matches one value. Nothing is
foreclosed; this is a low-cost hedge against a plausible future need
described directly in QUESTIONS.md.
