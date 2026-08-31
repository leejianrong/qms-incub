# ADR-0011: Synthetic batch generation is local developer tooling, not a web app feature (resolves Q38)

- Status: Accepted
- Date: 2026-08-31
- Deciders: leejianrong (user), agent (V5 slice)

## Context

V5 was originally built (SLICES.md, PLAN.md's Affordances table) as a
QA-author-facing feature: a "Generate N variants" panel and an ingestion
status dashboard inside the web app, calling a `POST /documents/batch`
endpoint. That framing assumed synthetic generation was part of the
product's day-to-day content-authoring workflow, alongside the block
composer (S4) and real document import (S7).

The user corrected this mid-build: the web app is a QMS platform for
uploading and querying real policy documents. Real company QMS documents
exist but are sensitive and not available during this build. Synthetic
generation exists purely so the RAG pipeline (S6) can be exercised and
validated locally before any real policy content is ingested — it isn't
something an actual QA-author should see or trigger from the product UI.

## Decision

Synthetic batch generation is a local CLI only (`qms_incub.batch_v5`, run
via `make batch COUNT=N SEED=S`). It reuses V1/V4's exact block model,
render, PDF export, and ingest path (ADR-0001) and tracks per-document
status in the same `PolicyDocumentRow` table V5 introduced — but none of
it is reachable through the running web app: no `POST /documents/batch`
or `GET /documents` endpoint, no frontend panel. The CLI prints a
per-document status summary to the terminal instead of a dashboard.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Keep the web app endpoints, just don't build a UI for them | Still exposes synthetic-generation and ingestion-status surface area on the running app for no product reason — the app's job is upload-and-query over real documents, not generating fake ones |
| Gate the feature behind a QA-author role/permission | Adds an access-control mechanism this milestone doesn't otherwise have (PLAN.md's Scope has no auth), to protect a feature that shouldn't exist in the product at all |

## Consequences

Gains: the web app's surface area matches what it's actually for
(`/health`, `/chat` — upload/query features land later per PLAN.md); no
risk of a real user finding and triggering synthetic-document generation
by accident; the CLI is simpler than building and maintaining a UI for a
developer-only workflow. Costs: none of V5's local tooling doubles as a
demo-able in-app feature — the ingestion-status dashboard as originally
scoped in SLICES.md doesn't exist as a UI, only as CLI output. Forecloses:
nothing structural — if a real in-app ingestion-status view is wanted
later (e.g. once V7's document import exists), it would be a new feature
built against the same `PolicyDocumentRow` data, not a resurrection of
this CLI's UI.
