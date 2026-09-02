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
| V1/V4: document upload (S4/S6) | QA-author upload/status control plus `POST /documents` — multipart PDF upload, ingested synchronously; `GET /documents` lists ingestion status. The only way a document enters the corpus (ADR-0012) |
| V1: ingestion (S6) | `make seed` uploads a fixture PDF (`backend/tests/fixtures/sample_policy_document.pdf`) through `POST /documents`, which Docling-parses it, chunks (LlamaIndex `SentenceSplitter`), embeds (local HF `BAAI/bge-small-en-v1.5`), and stores in Qdrant. Idempotent per document ID — re-ingesting the same ID clears old chunks first (`ingestion/pipeline.py`) |
| V1: chat (S8) | `POST /chat` — retrieval + LLM call, citations derived from retrieved chunks (not parsed from model output). LLM provider swappable, see Secrets/Q37. Retrieval mode is `RETRIEVAL_MODE=bm25` (default, sparse lexical) or `vector` (dense embedding similarity) — both query the same Qdrant collection, ingestion writes both vector types so switching needs no re-ingest; a fused hybrid mode combining both signals is deferred (issue #53). An optional rerank pass sits in front of `/chat` and the debug `POST /retrieve` endpoint, provider-selectable via `RERANKER_PROVIDER`: `none` (default, passthrough), `zenmux` (ZenMux's dedicated rerank endpoint), or `llm` (prompts whichever `LLM_PROVIDER` is already configured, reusing `chat/llm.get_llm_client()`). `chat/retrieval.fetch_document` currently expands each matched chunk to its entire source document for LLM context rather than a bounded window — tracked as a scale risk in issue #54 |
| V2: compliance wizard + todos (S1/S2) | `POST /standards` / `/clauses` / `/requirements` (QA-author editor, ADR-0008). Project creation and classification are two separate steps (see V9 row below) — classification scores a 3-boolean-question wizard (Q8, `compliance/scoring.py`) into a Low/Medium/High tier and generates one `TodoItem` per matching `Requirement` in one transaction. `GET /projects/{id}` for the dashboard |
| V3: artifact upload + self-attestation (S3, ADR-0002) | `POST /todos/{todo_id}/artifacts` — uploading a file against a `TodoItem` self-attests it straight to `complied`, no reviewer gate. `Artifact` table added |
| V8: compliance-aware chat | `POST /chat` injects the asking PM's `project_id`'s `Project`/`TodoItem`/`Artifact` state as structured context alongside the vector-retrieved chunks, in separate labeled sections so citations stay accurate (Q15, ADR-0003; landed via "Ground chat in project compliance state", predating this table's earlier per-slice rows). Frontend: the chat UI is a persistent panel on the project detail view (`ProjectDetail.svelte`), project-aware, not a standalone page — this half of V8's build plan landed with V13's console shell |
| V9: AOR intake & structured extraction (S10, Q40) | `POST /projects` now takes just `{name}` (`risk_tier` starts null); `POST /projects/{id}/aor` — multipart upload, Docling-parsed then LLM-extracted into 4 fixed fields (criticality tier, data classification, external dependencies, in-house rationale), persisted on the `Project`, never enters the document/RAG corpus (ADR-0012); `POST /projects/{id}/classify` — the old wizard-submit step (3 questions → tier → `TodoItem`s), now separate from creation. Pure extraction logic lives in `aor/extraction.py`, orchestration in `aor/service.py` |
| V10: QMS plan navigator / process-step grouping (Q41) | Fixed, config-seeded `ProcessStep` set (Initiation/Design/Build/Test/Deploy/Closure), seeded by migration. `Requirement` gains `process_step_id` (QA-author's fixed choice at authoring time, same shape as `risk_tiers`; `POST /clauses/{id}/requirements` accepts it, defaults to `initiation`). `TodoItem` inherits it from its generating Requirement in `classify_project`'s existing transaction. `GET /process-steps` serves the fixed ordered set. `/project?id=` is now a two-pane layout: a collapsible left-hand navigator (steps → todos, done/total + progress bar per step, collapses to an icon rail) and a right-hand detail panel for the selected todo |
| V11: approval-state schema (Q42, ADR-0002 unchanged) | `TodoItem` gains `approval_state` (`not_required`/`not_started`/`submitted`/`approved`/`returned`), `approval_authority`, `sla_target`, `decided_at` — set at generation time (`classify_project`) with seed defaults, no per-Requirement signal yet. Self-attestation (V3's `upload_artifact`) flips `approval_state` to `approved` and stamps `decided_at` in the same transaction as the Complied status change, when `approval_state != "not_required"`. Schema-only: no reviewer role or approval gate exists. Frontend: `approvalRouteViewModel` (`lib/approvalRoute.ts`) renders a 3-node route card (Submitted → QA Office → Authority) in the todo detail panel |
| V6: blog + FAQ (S9) | Admin-authored blog posts and FAQ Q&A pairs: draft, edit, list/detail, and publish APIs. Publishing immediately chunks, embeds, and adds content to the corpus with `source_type=blog` or `faq`; `/content` is the QA-author editor |
| V13: console shell (Q52) | Wires V2/V3/V9/V10/V11/V8 into one PM-facing console under a persistent shell (`lib/components/Shell.svelte` + `Console.svelte`), with real client-side routing (`lib/router.svelte.ts` — pushState/popstate, no library) instead of a full page reload per navigation. `/` is now `ProjectsDashboard.svelte` (project list + risk tier + compliance %, replacing the old fallback-to-document-upload root); `/project?id=` is the renamed `ProjectDetail.svelte` (was `ProjectDashboard.svelte`), now reactive to the route's `id` instead of reading it once at mount. Todo-detail comment thread (named in SLICES.md's V13 build plan) is scoped out — no backend model for it exists and this was a frontend-only slice, see Q52 |
| Wizard plan preview (frontend-only demo, no backend classify) | `Wizard.svelte`'s `/wizard` create flow no longer calls `POST /projects/{id}/classify` at all — it's 2 steps (details+AOR, then a preview), and the step-3 "QMS plan" (steps/sub-steps) is picked client-side from the AOR filename (`PLAN_A`/`PLAN_B` in `Wizard.svelte`) and stashed in `sessionStorage` (`lib/wizardPlan.ts`), not generated by the backend. `risk_tier` therefore stays `null` for every project made this way — `ProjectDetail.svelte`'s navigator, `ProjectsDashboard`/`Favourites`'s cards, and `Shell.svelte`'s notifications all treat "has a stashed wizard plan" as equivalent to "classified" for display purposes (`wizardPlanToSteps`/`wizardPlanToTodos` in `lib/wizardPlan.ts`, `hasWizardPlan` in `lib/projectCards.ts`) so it doesn't show as a "Draft" forever, but this only works in the same browser tab — `sessionStorage` isn't visible from a different tab or a shared link. The old wizard-submit `POST /projects/{id}/classify` endpoint (V9's row above) still exists and works; nothing in this flow calls it |
| Frontend (Svelte+Vite) | Tailwind + shadcn-svelte (V12, ADR-0013). V13's console shell (above) covers the core PM workflow; QA-author tools stay separate one-shot routes outside the shell: `/editor` (Standard/Clause/Requirement), `/content` (Blog/FAQ admin editor), `/documents` (V1's original document-upload/health-check page, moved off `/` to make room for the console) |
| Database (PostgreSQL) | `policy_documents` (V1/V4), V6's `blog_posts`/`faq_entries`, plus V2's `compliance_standards`/`clauses`/`requirements`/`projects`/`todo_items`, V3's `artifacts`, V9's `projects.aor_filename`/`aor_extracted_fields` (`projects.risk_tier` now nullable), V10's `process_steps` table plus `requirements.process_step_id`/`todo_items.process_step_id`, and V11's `todo_items.approval_state`/`approval_authority`/`sla_target`/`decided_at` — Alembic-managed, see `backend/migrations/` |
| Vector store (Qdrant) | In real use since V1 — collection `qms_incub_corpus`, see `qms_incub.rag_clients` |
| `synthetic-corpus/` | Independent tool generating realistic QMS-policy-shaped PDFs to manually test the backend's RAG pipeline. No shared code with `backend/`, no HTTP call to it either — its output is PDF files on disk; testing them against the backend is a manual upload-and-ask step. See `docs/shaping/synthetic-doc-realism/` for its own planning |
| Local infra: full containerization (ADR-0017) | Backend, frontend, Postgres, and Qdrant all run in Docker Compose, plus an nginx proxy (`nginx/default.conf`) that's the only container publishing a port to the host (`APP_PORT`) — routes `/` to the Vite dev server (HMR passed through) and `/api/*` to the backend, so the browser only ever sees one origin and CORS never comes into play. `make up` = `docker compose up --build` for the whole stack. `backend-dev`/`frontend-dev` remain as host-only Makefile targets (native debugger, or `ollama` — see Stack, below) |
| Everything else in PLAN.md / SLICES.md | **Not built yet.** |

If you're about to implement a slice, check this table (and `git log`)
before trusting a stale claim elsewhere that something is "done."

## Stack

Python/FastAPI backend, Svelte+Vite frontend, PostgreSQL, Qdrant, LlamaIndex
+ Docling for the RAG pipeline. Decided in ADR-0009 (supersedes ADR-0005's
original defaults). No PDF rendering library in the backend — it ingests
PDFs, it doesn't produce them (ADR-0012 supersedes ADR-0010). Embeddings are
provider-swappable via `EMBEDDING_PROVIDER` (Q36): `local` (default, a
HuggingFace model, no API key, no GPU needed) or a hosted OpenAI-compatible
`/embeddings` endpoint (`openrouter`/`zenmux`) for a machine you'd rather
not run a local model on. LLM is provider-swappable — Ollama for local dev,
OpenRouter as ADR-0003's decided default otherwise (Q37) — see Secrets
below. **`ollama` only works via the host-only `make backend-dev` path**
— the Dockerized `make up` backend has no route to a host-run Ollama
(ADR-0017), so `backend/.env.example`'s default is `openrouter`.

**2026-09-01 through 2026-09-05 only (Q39):** prefer `LLM_PROVIDER=zenmux`
— a ZenMux API key was distributed to the team separately for this
promotional window. This lapses automatically from 2026-09-06; go back to
`openrouter` after that date, same as before this note existed. Doesn't
change Q37's decision or ADR-0003.

## Secrets

`backend/.env` (gitignored) holds real local secrets — currently
`OPENROUTER_API_KEY` and, during the Q39 window only, `ZENMUX_API_KEY`.
`rag-eval/.env` (also gitignored) holds its own copy of the same
provider settings, since `rag-eval` doesn't read `backend/.env` (see
Layout, above). **Never read either `.env` file with a file-read tool** —
and note that `grep`/`cat`/`sed` etc. via Bash expose secrets just as much
as a file-read tool would, as does copying the file wholesale; the rule is
about not exposing the values, not about which specific tool is used.
Access values only the proper way: through `qms_incub.config.settings`
(loaded automatically by `pydantic-settings`) in app code, or by letting
the user tell you a value directly. `backend/.env.example` and
`rag-eval/.env.example` document every variable and are safe to read.

## Commands

Run from the repo root unless noted.

- `make install` — `uv sync` (backend) + `npm install` (frontend), plus a
  one-time `make env` (below). Safe to run repeatedly.
- `make env` — copies each `.env.example` to its real `.env`
  (root `.env`, `backend/.env`, `frontend/.env.local`, `rag-eval/.env`)
  wherever one doesn't already exist yet; never overwrites a real one.
  Root `.env` just sets `APP_PORT` (default `5173`). `backend/.env`'s
  default `LLM_PROVIDER=openrouter` needs a real `OPENROUTER_API_KEY` (or
  `ZENMUX_API_KEY` during the Q39 window) before `/chat` works — see
  Stack, above, and ADR-0017. `make install` and `make up` both depend on
  this, so you rarely need to run it directly.
- `make install-hooks` — symlinks `scripts/git-hooks/pre-push` into
  `.git/hooks/pre-push`. Run this once per clone.
- `make up` — `docker compose up --build` for the whole stack: Postgres,
  Qdrant, a one-shot Alembic-migration service, the FastAPI backend, the
  Vite dev server, and an nginx proxy (`nginx/default.conf`), in the
  foreground (ADR-0017). The proxy is the *only* container publishing a
  port to the host — `APP_PORT` (root `.env`, default `5173`) — routing
  `/` to the frontend (HMR included) and `/api/*` to the backend, so the
  browser only ever sees one origin and CORS never comes into play. A
  port already taken is a one-line `APP_PORT` edit, not a code change.
  Ctrl+C stops everything; `make down` also removes the containers.
- `make down` — stop all containers; their data volumes are kept.
- `make reset` — `docker compose down -v`: stop the containers **and**
  wipe their data volumes. Needed when a pull changes Qdrant's (or
  Postgres's) schema and a volume from before that change is still on
  disk — ingestion suddenly 500ing with a Qdrant error like `Not existing
  vector name` is exactly this, since `make down` alone deliberately
  leaves volumes in place. Re-seed afterwards.
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
  `POST /documents` endpoint (via the proxy's `/api` prefix), proving
  local ingestion+chat work. Needs `make up` running — first run also
  downloads the embedding model.
- `make seed-corpus` — generates the 10-doc synthetic policy corpus
  (`synthetic-corpus/`) and ingests every PDF through the real
  `POST /documents` endpoint, the same path `synthetic-corpus/README.md`
  and `docs/rag-pipeline-walkthrough.md` describe by hand. Needs `make up`
  running. Not idempotent by document identity — re-running adds a fresh
  copy of each document, same as running the manual curl loop twice would.
- `make seed-demo` — seeds a QMS standard/clauses/requirements, five demo
  projects shaped like `ui-reference/QMS Console.dc.html` at varied risk
  tiers and completion states, and a few published blog posts/FAQ entries
  (`backend/scripts/seed_demo.py`), all through the real API. Idempotent —
  matches existing records by name, so re-running is a safe no-op. Needs
  `make up` running.
- `make seed-all` — `seed` + `seed-corpus` + `seed-demo` in one command,
  for the full demo experience from a clean database.
- `make migrate` — runs the `migrate` service (`docker compose run --rm
  migrate`) to apply Alembic migrations against Postgres by hand, without
  restarting the stack. `make up` already runs this automatically, once,
  before the backend starts (`migrate` service in `docker-compose.yml`,
  ADR-0017).

Backend-only, from `backend/`: `uv run alembic revision --autogenerate -m
"..."` after changing a model in `models.py`, then `uv run alembic upgrade
head` — review the generated migration before committing it, autogenerate
doesn't catch everything (renames, some constraint changes).

Backend-only, from `backend/`: `uv run pytest -q`, `uv run ruff check .`,
`uv run mypy src`, `uv run uvicorn qms_incub.main:app --reload --port 8000`
(the last one is what `make backend-dev` runs — host-only, e.g. for a
native debugger or `LLM_PROVIDER=ollama`, see Stack above).

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
rag-eval/         Scores the backend's retrieval quality (NDCG/Recall/MRR)
                  against a gold set derived from synthetic-corpus's Q&A
                  pairs (`uv run python -m rag_eval`). Unlike
                  synthetic-corpus, this *does* depend on qms_incub — a
                  local `uv` path dependency on backend/ (see its
                  pyproject.toml), since it scores the real RetrievalPort
                  implementation rather than a stand-in. Reads its own
                  `rag-eval/.env`, not `backend/.env` — keep them in sync;
                  see `docs/rag-pipeline-walkthrough.md`.
docs/adr/         Architecture decision records, numbered sequentially
ui-reference/     Static design mock (QMS Console.dc.html) from the UI/UX
                  engineer — look-and-feel + workflow reference for the
                  console frontend (SLICES.md V9-V13). Not shipped code.
scripts/          git-hooks/pre-push — the fast local gate
nginx/            default.conf — the single-origin dev proxy `make up`
                  runs in front of everything (ADR-0017).
docker-compose.yml  Postgres, Qdrant, backend, frontend, migrate, proxy —
                    the whole local stack, brought up by `make up`.
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
