# qms-incub — agent brief

**Trust this file and the code over the planning docs where they disagree,
and update whichever one is stale in the same PR that noticed it.** The
planning docs (below) describe intent; this file describes what's actually
built and how to work in the repo day to day.

## Build status

| Area | Status |
|------|--------|
| Backend (FastAPI) | V1 (RAG spike) + V5 (synthetic batch generation) built — see below |
| V1: document engine (S4) | Block model (text/table/flowchart/image), Jinja2 HTML render, flowchart step-list → SVG (hand-rolled, no Mermaid CLI), WeasyPrint PDF export. One hardcoded seed document (`qms_incub.documents.seed`) — no composer UI yet (V4) |
| V1: ingestion (S6) | `make seed` renders the seed doc, exports PDF, Docling-parses it, chunks (LlamaIndex `SentenceSplitter`), embeds (local HF `BAAI/bge-small-en-v1.5`), stores in Qdrant. Idempotent per document ID — re-running clears old chunks first (`ingestion/pipeline.py`) |
| V1: chat (S8) | `POST /chat` — vector retrieval + LLM call, citations derived from retrieved chunks (not parsed from model output). LLM provider swappable, see Secrets/Q37 |
| V5: batch generation (S5) | `qms_incub.documents.random_generator` produces N randomized documents (seeded, reproducible) from V1's exact block model/render/ingest path, flagged `is_synthetic`. `POST /documents/batch` kicks off a batch as a FastAPI background task |
| V5: ingestion status (S6 dashboard) | `GET /documents` lists every `PolicyDocumentRow` (pending/embedded/failed, chunk count, error) — the first slice to touch the relational data model. Frontend dashboard polls this while anything is pending |
| Frontend (Svelte+Vite) | Chat panel (V1) + "Generate synthetic variants" panel and status dashboard (V5, `lib/BatchDashboard.svelte`) |
| Database (PostgreSQL) | `policy_documents` table only (V5) — Alembic-managed, see `backend/migrations/`. Not the full `Project`/`TodoItem`/`Standard`/`Clause`/`Requirement` model yet (V2/ADR-0008) |
| Vector store (Qdrant) | In real use since V1 — collection `qms_incub_corpus`, see `qms_incub.rag_clients` |
| Everything else in PLAN.md / SLICES.md (V2–V4, V6–V8) | **Not built yet.** |

If you're about to implement a slice, check this table (and `git log`)
before trusting a stale claim elsewhere that something is "done."

## Stack

Python/FastAPI backend, Svelte+Vite frontend, PostgreSQL, Qdrant, LlamaIndex
+ Docling for the RAG pipeline. Decided in ADR-0009 (supersedes ADR-0005's
original defaults). PDF export is WeasyPrint (ADR-0010, resolves Q35).
Embeddings are a local HuggingFace model, no API key (Q36). LLM is
provider-swappable — Ollama for local dev, OpenRouter as ADR-0003's
decided default otherwise (Q37) — see Secrets below.

## Secrets

`backend/.env` (gitignored) holds real local secrets — currently
`OPENROUTER_API_KEY`. **Never read `backend/.env` with a file-read tool.**
Access its values only the proper way: through `qms_incub.config.settings`
(loaded automatically by `pydantic-settings`) in app code, or by letting
the user tell you a value directly. `backend/.env.example` documents every
variable and is safe to read.

## Commands

Run from the repo root unless noted.

- `make up` — start Postgres + Qdrant (Docker), then the FastAPI backend
  (`:8000`) and the Vite dev server (`:5173`) in the foreground. Ctrl+C
  stops both dev servers; containers stay running.
- `make down` — stop and remove the Postgres/Qdrant containers.
- `make install` — `uv sync` (backend) + `npm install` (frontend).
- `make install-hooks` — symlinks `scripts/git-hooks/pre-push` into
  `.git/hooks/pre-push`. Run this once per clone.
- `make lint` — `ruff check` (backend) + `eslint` (frontend).
- `make typecheck` — `mypy` (backend) + `svelte-check`/`tsc` (frontend).
- `make test` — `pytest` (backend) + `vitest run` (frontend). Fast, no-infra
  layer only — this is what the pre-push hook and CI's fast jobs run.
  Backend `integration` (needs Qdrant, wired into CI via a service
  container) and `e2e` (needs a live LLM too — local-only) tests are
  excluded by default; run explicitly with `uv run pytest -m integration`
  or `-m e2e` from `backend/`.
- `make seed` — builds V1's one hardcoded seed policy document, exports it
  to PDF, and ingests it into Qdrant. Needs `make up` running (Qdrant) —
  first run also downloads the embedding model.
- `make migrate` — applies Alembic migrations against Postgres. `make up`
  runs this automatically once Postgres is healthy, before starting the
  dev servers.

Backend-only, from `backend/`: `uv run alembic revision --autogenerate -m
"..."` after changing a model in `models.py`, then `uv run alembic upgrade
head` — review the generated migration before committing it, autogenerate
doesn't catch everything (renames, some constraint changes).

Backend-only, from `backend/`: `uv run pytest -q`, `uv run ruff check .`,
`uv run mypy src`, `uv run uvicorn qms_incub.main:app --reload --port 8000`.

Frontend-only, from `frontend/`: `npm run test`, `npm run lint`,
`npm run check`, `npm run dev`, `npm run build`.

## Workflow conventions

- **Branch per slice, PR-only.** One branch per `SLICES.md` vertical slice
  (or a clear sub-piece of one), cut from fresh `main`. No direct pushes to
  `main` by convention — this isn't yet enforced by GitHub branch
  protection, so it's on you to follow it.
- **Pre-push hook mirrors CI's fast checks** (lint, typecheck, test). Run
  `make install-hooks` once after cloning. Scoped exception: `git push
  --no-verify` for a genuine one-off (e.g. a docs-only change).
- **CI** (`.github/workflows/ci.yml`) runs `backend` and `frontend` jobs in
  parallel, each covering lint/typecheck/test/build for its side. Both are
  the actual gate until branch protection is turned on.
- **A change that touches the data model** (once one exists) lands alone,
  not stacked with an unrelated change.
- **Commit messages explain why**, not just what.
- Every finished bug fix or flake gets a regression test — see
  `dev-playbook`'s `layered-testing.md` for the pattern (fast/no-infra
  tests are the default; integration/e2e stay containerized and CI-only).
- **Sub-agents: hard cap of 3 running in parallel at any one time.** Don't
  spin one up unless the task genuinely needs the parallelism — most work
  in this repo is a single sequential thread.

## Layout

```
backend/    FastAPI app (src/qms_incub/), pytest tests/
frontend/   Svelte + Vite app (src/), vitest tests colocated as *.test.ts
docs/adr/   Architecture decision records, numbered sequentially
scripts/    git-hooks/pre-push — the fast local gate
```

## Docs map — read these before planning new work

The plan is still in flux and is the source of truth for *what* to build,
in this order of authority:

1. **`PLAN.md`** — problem, solution, requirements, shape, scope. Start
   here.
2. **`docs/adr/*.md`** — one architectural decision per file, numbered.
   Read the ones cited by the part of PLAN.md you're touching.
3. **`SLICES.md`** — the vertical build plan, one slice at a time, each
   with a demo and a test plan. This is the actual work breakdown.
4. **`QUESTIONS.md`** — the full decision register: what's decided, what's
   assumed (and the cost if the assumption is wrong), what's deferred.
   Check this before assuming a gap is an oversight — it might be a
   recorded, deliberate default.

If something here conflicts with those docs, or those docs conflict with
each other, say so rather than picking one silently — the plan is still
being iterated on.
