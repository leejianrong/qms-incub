# ADR-0009: Revised MVP stack — Python/FastAPI, Svelte+Vite, PostgreSQL, Qdrant, LlamaIndex + Docling for RAG

- Status: Accepted
- Date: 2026-08-31
- Deciders: engineering team (backend/frontend/DB/vector-DB/RAG-tooling choice); leejianrong (relayed to agent); agent (PDF-rendering follow-up, records the gap rather than deciding it)
- Supersedes: the technology choices in ADR-0005 (Next.js/React, pgvector, Puppeteer). ADR-0005's actual decision — run everything locally via Docker Compose + a one-command Makefile, no cloud deploy target — is unaffected and still stands.

## Context

ADR-0005 picked a stack by default in the absence of a stated team
preference: a single Next.js/React app, pgvector inside the same Postgres
database (explicitly rejecting a dedicated vector DB as unwarranted
infrastructure), and Puppeteer for PDF export. The team has since made its
own stack decision, independent of that default: a Python backend (most
likely FastAPI), a Svelte + Vite frontend, PostgreSQL for relational data,
and Qdrant as a dedicated vector database. For the RAG pipeline (ingestion
— S6, retrieval — S8), the team is leaning on LlamaIndex (RAG
orchestration: document loading, chunking, embedding, query engines) and
Docling (document parsing, notably strong at extracting table and layout
structure from PDFs) rather than the hand-rolled pipeline PLAN.md
originally sketched.

## Decision

- **Backend**: Python, most likely FastAPI, serving a REST API.
- **Frontend**: Svelte + Vite, a separate SPA talking to the backend over
  HTTP. The local stack is now two application processes (not one combined
  Next.js app as ADR-0005 assumed), both still brought up by a single
  `make up` — ADR-0005's local-only/Makefile decision is unaffected by
  this split, it just now orchestrates more services.
- **Relational data**: PostgreSQL, unchanged from ADR-0005 — `Project`,
  `TodoItem`, `Artifact`, `PolicyDocument`, `ComplianceStandard`/`Clause`/
  `Requirement` (ADR-0008), `BlogPost`, `FAQEntry`.
- **Vector store**: Qdrant, a dedicated vector database, replacing
  pgvector. This reverses ADR-0005's original reasoning against a
  dedicated vector DB — the team is accepting a second stateful service in
  exchange for Qdrant's purpose-built vector search (filtering, payload
  indexing, more scaling headroom than pgvector). Qdrant's self-hosted
  distribution is open source (Apache 2.0) and runs in Docker, so this
  doesn't compromise the local-only, no-cloud constraint (ADR-0005) —
  nothing requires Qdrant Cloud.
- **RAG pipeline**: LlamaIndex orchestrates ingestion (S6) and retrieval
  (S8) — document loading, chunk/node parsing, embedding calls, and
  querying Qdrant via LlamaIndex's Qdrant integration — replacing the
  bespoke "chunk → embed → store" pipeline PLAN.md originally sketched.
  Docling handles parsing for both generated PDFs (S4/S5's output) and
  imported PDFs (S7), chosen specifically because it preserves table
  structure and document layout during extraction — directly serving this
  project's stated premise of stress-testing ingestion on table- and
  flowchart-heavy documents (PLAN.md, Open risks). Both are open source
  (LlamaIndex: MIT; Docling: MIT, IBM) and run offline once their models
  are downloaded, aside from whatever embedding/LLM API calls the pipeline
  itself makes (OpenRouter, per ADR-0003, is unaffected by this decision).

**Local bring-up (ADR-0005 unchanged, now orchestrating four services).**
`make up` starts Postgres and Qdrant (Docker Compose), runs DB migrations,
seeds demo data, and starts both the FastAPI backend (`uvicorn`) and the
Svelte/Vite dev server. `make down` stops the containers. `make seed`
re-seeds demo data. `make test` runs the fast, no-infra test layer for
both backend and frontend.

## Open follow-up (not decided here)

**PDF rendering engine (S4).** ADR-0005 chose Puppeteer, a Node.js
library — inconsistent with a Python backend. The team didn't specify a
replacement, so this isn't decided in this ADR. Recorded as Q35 in
QUESTIONS.md with an assumed default (Python-native rendering, e.g.
WeasyPrint or Playwright's Python bindings) that should be confirmed, not
silently treated as settled.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Keep Next.js/React as a combined frontend+API app | Team specifically wants a Python backend (FastAPI) and a Svelte frontend — not a stack preference the plan should override |
| Keep pgvector instead of adding Qdrant | Team decision overrides ADR-0005's original simplicity trade-off; Qdrant's purpose-built vector search is what they want, at the cost of a second stateful local service |
| Hand-rolled ingestion/retrieval pipeline (original S6/S8 design) | Team is leaning on LlamaIndex + Docling for the same mechanism instead of custom code — less code to maintain, and Docling's table/layout-aware parsing is a direct fit for this project's own ingestion-testing goal |

## Consequences

Gains: FastAPI + Svelte is a well-supported, fast-iterating combination;
Qdrant is a mature, purpose-built vector database with first-class
LlamaIndex support; Docling's table/layout extraction directly serves a
project whose explicit premise is testing RAG ingestion on structurally
complex PDFs — likely a better test of real ingestion behavior than a
hand-rolled chunker would have been. Costs: the local stack now has four
services instead of two (Postgres, Qdrant, the FastAPI backend, the Vite
dev server) — `make up` (ADR-0005) has to orchestrate all four as one
command, more moving parts than the original single-app design. The
PDF-rendering engine is left as an open gap rather than resolved here.
Forecloses: pgvector as this milestone's vector store — moving back to a
single-database design later would mean migrating off Qdrant, not just
flipping a config flag.
