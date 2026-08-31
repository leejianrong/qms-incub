# ADR-0005: Local-only stack via Docker Compose + Makefile — Next.js, Postgres+pgvector, Puppeteer for PDF

- Status: Accepted
- Date: 2026-08-31
- Deciders: agent (plan-new-project skill, assumed default Q11); leejianrong (user, round 5 — Q5 corrected: no cloud deploy, local demo only)

## Context

The app needs a vector store for RAG, an LLM client (OpenRouter —
user-specified), and a PDF export path capable of rendering
server-composed tables and Mermaid-style flowcharts identically regardless
of who triggers the export (a human author or the synthetic batch job,
which has no browser open). Round 1 assumed a cloud-hosted deployment
(Q5); the user corrected this directly — there is no deploy target for
this milestone at all. The only requirement is that the whole stack comes
up on the presenter's own laptop for a demo, with a single command
(`dev-playbook` principle 17: "a single command that brings the whole
stack up locally — the first thing a newcomer or agent runs").

## Decision

Single application, run locally only: Next.js/React for both UI and API
routes, Postgres with the `pgvector` extension as the single database
serving both relational data and vector search (no separate vector-DB
service), Puppeteer (headless Chromium) for HTML-to-PDF export, and
Mermaid rendered server-side to SVG for flowchart blocks before PDF
export. Postgres runs in Docker via `docker-compose.yml`; the app itself
runs directly on the host (`npm run dev`) against that container. A
Makefile is the single entry point:

- `make up` — starts Postgres (Docker Compose), runs migrations, seeds
  demo data (a sample compliance standard/clause/requirement tree and a
  couple of documents), and starts the Next.js dev server — one command
  from a clean checkout to a demoable app.
- `make down` — stops and removes the Postgres container.
- `make seed` — re-seeds demo data without restarting the stack.
- `make test` — runs the fast, no-infra test layer.

No cloud deployment target, CI deploy gate, or hosting decision is made in
this milestone — out of scope per PLAN.md.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Cloud-hosted deployment (round-1 default) | User corrected directly — no deploy needed, laptop demo only |
| Dedicated vector DB (Pinecone, Weaviate, etc.) | Extra infrastructure and an extra network dependency for a single-org, local-only MVP; pgvector is sufficient at this data scale and keeps the whole app on one database |
| External PDF rendering API/service | Adds a network dependency for a core, frequently-used feature (including the synthetic batch generator); works against "runs entirely on a laptop" |
| Fully containerized app (Next.js app itself in Docker too) | Slower iteration loop for a project still being actively built; only the stateful piece (Postgres) needs containerizing to satisfy the one-command bring-up |
| Multi-service architecture (separate ingestion worker service, separate API service) | Unwarranted operational complexity for a single-org, local-only tool |

## Consequences

Gains: `make up` is the entire onboarding story — no cloud account, no
deploy pipeline, no hosting cost, matching the "present to someone from my
laptop" requirement exactly. Costs: nothing here is a validated production
deployment; if a hosted demo or real user ever becomes necessary, this ADR
needs revisiting (the app itself has no cloud-specific code either way, so
that's a new decision, not a rework). pgvector's retrieval performance and
scale ceiling are lower than a dedicated vector database — irrelevant at
laptop-demo scale. Puppeteer's headless-Chromium footprint is heavier than
a lightweight PDF library, traded for rendering fidelity on tables and
Mermaid SVGs. Forecloses: nothing structurally — this is additive to add a
deploy target later, not a rework of the app.
