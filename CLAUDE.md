# qms-incub — agent brief

**Trust this file and the code over the planning docs where they disagree,
and update whichever one is stale in the same PR that noticed it.** The
planning docs (below) describe intent; this file describes what's actually
built and how to work in the repo day to day.

## Build status

| Area | Status |
|------|--------|
| Backend (FastAPI) | Walking skeleton — one `/health` endpoint, no data model, no auth, no ingestion pipeline yet |
| Frontend (Svelte+Vite) | Walking skeleton — one page that calls `/health` and shows the result |
| Database (PostgreSQL) | Runs via `make up`, no migrations/schema yet |
| Vector store (Qdrant) | Runs via `make up`, unused so far |
| Everything in PLAN.md / SLICES.md | **Not built yet.** V1 (the RAG spike) is the first real slice — see SLICES.md |

If you're about to implement a slice, check this table (and `git log`)
before trusting a stale claim elsewhere that something is "done."

## Stack

Python/FastAPI backend, Svelte+Vite frontend, PostgreSQL, Qdrant, LlamaIndex
+ Docling for the RAG pipeline. Decided in ADR-0009 (supersedes ADR-0005's
original defaults). PDF-rendering engine is **not yet decided** — see
QUESTIONS.md Q35 before touching S4 (document generation).

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
- `make seed` — currently a stub; there's no schema to seed yet.

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
