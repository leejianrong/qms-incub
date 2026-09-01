# ADR-0015: A CLI as a thin client over the existing FastAPI backend

- Status: Accepted — for the **next milestone**, alongside ADR-0014. Not
  built as part of the current MVP (V1–V13).
- Date: 2026-09-01
- Deciders: leejianrong (user); agent (agents/MCP/CLI/identity research
  session)

## Context

`make seed` already does an informal, single-purpose version of this: a
script that uploads a fixture PDF through `POST /documents` directly. A
real QMS rollout needs more than one fixture uploaded once — a QA-author
bootstrapping a company's actual `ComplianceStandard`/`Clause`/
`Requirement` tree (ADR-0008) and uploading a batch of real policy
documents is naturally a scripted, repeatable operation, not a sequence of
manual form submissions. Separately, the MCP server planned in ADR-0016
needs some non-browser way to call the backend's logic, and CI needs a
scriptable path for any future automated seeding or verification step.

## Decision

Build a CLI that talks to the **same FastAPI endpoints** a human uses
through the browser — no parallel code path, no direct database or ORM
access. It authenticates as a machine client per ADR-0014
(client-credentials grant against the Keycloak realm). Initial scope:

- `documents upload <path>` / `documents list` — mirrors
  `POST /documents` / `GET /documents`.
- `standards seed <file>` — bulk-creates a `Standard`/`Clause`/
  `Requirement` tree from a structured file, for loading a real QMS's
  initial content in one pass instead of one form submission per row.

`make seed` gets rewritten to call this CLI instead of maintaining its own
ad hoc upload script — one implementation of "upload a document
programmatically," not two. The CLI is not a PM-facing tool: the wizard,
todo list, and artifact upload stay a web-only flow, matching PLAN.md's
console-first framing for that persona.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Direct DB/ORM access from the CLI | Bypasses ingestion side effects (S6's chunking/embedding, status tracking) that only happen when a document goes through the real upload path, and duplicates validation logic that already lives in the API layer |
| A CLI generated wholesale from the OpenAPI schema | Left as an implementation detail, not a separate decision — doesn't change what surface or scope this ADR commits to |
| No CLI; MCP server calls the backend's HTTP API directly instead | Works, but then the CLI's future scripting/CI use case has no home, and the MCP server's tool handlers end up as the only implementation of "call this backend programmatically" — worth having as a reusable client library either way |

## Consequences

Gains: a scriptable, CI-friendly surface for QA-author bulk operations,
with zero business logic duplicated outside the FastAPI layer. Gives
ADR-0016's MCP server a client library to call instead of reimplementing
request logic a third time.

Costs: every new backend capability now has a CLI-surface question
attached to it (build it, or explicitly decide not to) alongside its API
design, going forward.

Forecloses: nothing — the CLI is additive to the existing API, not a
replacement for it.
