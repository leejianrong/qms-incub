# ADR-0002: Compliance artifacts are self-attested in v1, no reviewer gate

- Status: Accepted
- Date: 2026-08-31
- Deciders: leejianrong (user), agent (plan-new-project skill, round-2 fork F7)

## Context

A QMS normally has someone other than the PM confirm that a submitted
artifact actually satisfies the required practice. But this milestone's
stated focus is the PM's own UI/UX and workflow, and no reviewer persona
was named in the idea. Building a review/approval surface means a second
role, a second set of screens, and a second workflow state — real scope,
not incidental to add.

## Decision

A `TodoItem` has two states relevant here: `Pending` and `Complied`.
Uploading an `Artifact` against a `Pending` item flips it straight to
`Complied` — the PM's upload is treated as sufficient proof, with no
intermediate `Pending Review` state and no reviewer role in this milestone.
This is an explicitly named next-iteration feature, not a rejected one (see
QUESTIONS.md F7).

## Alternatives considered

| Option | Why not |
|--------|---------|
| QA-reviewer approval gate now | Doubles the actor model and the surface area for this milestone; the user explicitly deferred it rather than asking for it |
| Silent no-op upload with no status change | Defeats the point of the todo list — a PM couldn't tell what's actually done |

## Consequences

Gains: the compliance workflow ships in one slice (V3) instead of two, and
stays scoped to the PM persona the idea names as primary. Costs: the
self-attestation is unverified — there is no check that an uploaded
artifact actually satisfies the practice, which weakens the system's
credibility as a real QMS tool. Forecloses nothing structurally: adding a
`Pending Review` state and a reviewer role later is additive to the
`TodoItem` state machine, not a rework of it.
