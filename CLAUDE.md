# qms-incub — agent brief

**Trust this file and the code over the planning docs where they disagree,
and update whichever one is stale in the same PR that noticed it.** The
planning docs (below) describe intent; this file describes what's actually
built and how to work in the repo day to day.

## Build status

The backend is ingestion-and-chat only — it never authors, composes, or
generates document content, real or synthetic (ADR-0012). Synthetic
document generation for testing the RAG pipeline lives entirely outside
this product now, in `synthetic-corpus/` — its own tool, no shared code,
no HTTP dependency on the backend either.

| Area | Status |
|------|--------|
| Backend (FastAPI) | V1 (RAG spike) built and exposed via the API |
| V1/V4: document upload (S4/S6) | `POST /documents` — multipart PDF upload, ingested synchronously. `GET /documents` lists ingestion status. The only way a document enters the corpus (ADR-0012) |
| V1: ingestion (S6) | `make seed` uploads a fixture PDF (`backend/tests/fixtures/sample_policy_document.pdf`) through `POST /documents`, which Docling-parses it, chunks (LlamaIndex `SentenceSplitter`), embeds (local HF `BAAI/bge-small-en-v1.5`), and stores in Qdrant. Idempotent per document ID — re-ingesting the same ID clears old chunks first (`ingestion/pipeline.py`) |
| V1: chat (S8) | `POST /chat` — vector retrieval + LLM call, citations derived from retrieved chunks (not parsed from model output). LLM provider swappable, see Secrets/Q37 |
| V2: compliance wizard + todos (S1/S2) | `POST /standards` / `/clauses` / `/requirements` (QA-author editor, ADR-0008). Project creation and classification are two separate steps (see V9 row below) — classification scores a 3-boolean-question wizard (Q8, `compliance/scoring.py`) into a Low/Medium/High tier and generates one `TodoItem` per matching `Requirement` in one transaction. `GET /projects/{id}` for the dashboard |
| V3: artifact upload + self-attestation (S3, ADR-0002) | `POST /todos/{todo_id}/artifacts` — uploading a file against a `TodoItem` self-attests it straight to `complied`, no reviewer gate. `Artifact` table added |
| V9: AOR intake & structured extraction (S10, Q40) | `POST /projects` now takes just `{name}` (`risk_tier` starts null); `POST /projects/{id}/aor` — multipart upload, Docling-parsed then LLM-extracted into 4 fixed fields (criticality tier, data classification, external dependencies, in-house rationale), persisted on the `Project`, never enters the document/RAG corpus (ADR-0012); `POST /projects/{id}/classify` — the old wizard-submit step (3 questions → tier → `TodoItem`s), now separate from creation. Pure extraction logic lives in `aor/extraction.py`, orchestration in `aor/service.py` |
| V17: AOR route classification (R&T/SSD) | `POST /aor/classify` — embeds an uploaded AOR's extracted text with the RAG pipeline's own model, cosine-compares against two labeled reference descriptions, returns route + confidence + `needs_review`. Standalone from the `Project`/wizard flow, not part of V9's AOR intake — see Q51. `scripts/classify_aor.py` is the same classifier as a CLI |
| Frontend (Svelte+Vite) | V1's chat panel, plus Tailwind + shadcn-svelte (V12, ADR-0013) and V2/V9's routes: `/editor` (Standard/Clause/Requirement), `/wizard` (2-phase: name + optional AOR upload with a "read from the pack" panel, then the 3 classification questions), `/project?id=` (todo dashboard). No unified console shell yet — that's V13 |
| Database (PostgreSQL) | `policy_documents` (V1/V4) plus V2's `compliance_standards`/`clauses`/`requirements`/`projects`/`todo_items`, V3's `artifacts`, and V9's `projects.aor_filename`/`aor_extracted_fields` (`projects.risk_tier` now nullable) — Alembic-managed, see `backend/migrations/`. No `ProcessStep` or approval-state columns yet (V10/V11) |
| Vector store (Qdrant) | In real use since V1 — collection `qms_incub_corpus`, see `qms_incub.rag_clients` |
| `synthetic-corpus/` | Independent tool generating realistic QMS-policy-shaped PDFs to manually test the backend's RAG pipeline. No shared code with `backend/`, no HTTP call to it either — its output is PDF files on disk; testing them against the backend is a manual upload-and-ask step. See `docs/shaping/synthetic-doc-realism/` for its own planning |
| Everything else in PLAN.md / SLICES.md (V6, V8, V10, V11, V13) | **Not built yet.** |

If you're about to implement a slice, check this table (and `git log`)
before trusting a stale claim elsewhere that something is "done."

## Stack

Python/FastAPI backend, Svelte+Vite frontend, PostgreSQL, Qdrant, LlamaIndex
+ Docling for the RAG pipeline. Decided in ADR-0009 (supersedes ADR-0005's
original defaults). No PDF rendering library in the backend — it ingests
PDFs, it doesn't produce them (ADR-0012 supersedes ADR-0010). Embeddings
are a local HuggingFace model, no API key (Q36). LLM is provider-swappable
— Ollama for local dev, OpenRouter as ADR-0003's decided default otherwise
(Q37) — see Secrets below.

**2026-09-01 through 2026-09-05 only (Q39):** prefer `LLM_PROVIDER=zenmux`
— a ZenMux API key was distributed to the team separately for this
promotional window. This lapses automatically from 2026-09-06; go back to
`openrouter` (preferred) or `ollama` after that date, same as before this
note existed. Doesn't change Q37's decision or ADR-0003.

## Secrets

`backend/.env` (gitignored) holds real local secrets — currently
`OPENROUTER_API_KEY` and, during the Q39 window only, `ZENMUX_API_KEY`.
**Never read `backend/.env` with a file-read tool** — and note that
`grep`/`cat`/`sed` etc. via Bash expose secrets just as much as a
file-read tool would; the rule is about not exposing the values, not
about which specific tool is used. Access its values only the proper
way: through `qms_incub.config.settings`
(loaded automatically by `pydantic-settings`) in app code, or by letting
the user tell you a value directly. `backend/.env.example` documents every
variable and is safe to read.

## Commands

Run from the repo root unless noted.

- `make up` — start Postgres + Qdrant (Docker), then the FastAPI backend
  (`:8000`, falling back to `:8001`, `:8002`, ... if that port's already
  taken — watch the output for which port it picked, and the Vite dev
  server's `VITE_API_BASE` is wired to match automatically) and the Vite
  dev server (`:5173`) in the foreground. Ctrl+C stops both dev servers;
  containers stay running.
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
- `make seed` — uploads a fixture PDF
  (`backend/tests/fixtures/sample_policy_document.pdf`) through the real
  `POST /documents` endpoint, proving local ingestion+chat work. Needs
  `make up` running (backend + Qdrant) — first run also downloads the
  embedding model.
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
- **Parallel sub-agents that write files: always give each one its own
  git worktree, never a shared working directory.** Two or more agents
  editing files in the same working tree race with each other and with
  any `git stash`/`checkout`/`rebase` the coordinator runs meanwhile —
  this has already silently wiped a batch of in-progress sub-agent edits
  once. Use the `treehouse` CLI to manage the worktree pool: `treehouse
  get --lease --lease-holder <label>` to acquire one (prints its path;
  `--lease` makes it durable/non-interactive, so it survives across the
  agent's whole run rather than just one subshell), `treehouse return
  <path>` to release it when the agent is done, `treehouse status` to
  see what's currently leased. Have each agent commit its own work on its
  own branch inside its worktree; the coordinator merges/rebases branches
  together afterward, never mid-flight while agents are still writing.

## Layout

```
backend/          FastAPI app (src/qms_incub/), pytest tests/
frontend/         Svelte + Vite app (src/), vitest tests colocated as *.test.ts
synthetic-corpus/ Independent tool generating synthetic QMS-policy-shaped PDFs
                  to manually test the backend's RAG pipeline (ADR-0012).
                  Shares no code with backend/, doesn't call it over HTTP either.
docs/adr/         Architecture decision records, numbered sequentially
ui-reference/     Static design mock (QMS Console.dc.html) from the UI/UX
                  engineer — look-and-feel + workflow reference for the
                  console frontend (SLICES.md V9-V13). Not shipped code.
scripts/          git-hooks/pre-push — the fast local gate
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
