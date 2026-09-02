# qms-incub

A compliance console for project managers at a large company: classify a
software project, get a generated QMS todo list grouped by build phase,
upload evidence, track approval routing, and ask a policy chatbot grounded
in both the uploaded document corpus and the project's own compliance
state. Internal incubation project — the plan is still evolving, see
[Read this first](#read-this-first) before you assume anything about scope
is final.

## Screens

| Project console — plan navigator + grounded chat | PM dashboard |
|---|---|
| ![Project console with the compliance plan navigator and the Ask QMS Assistant chat widget open, showing a grounded answer with citations](docs/images/project-console.png) | ![PM dashboard listing projects by risk tier and approval status](docs/images/dashboard.png) |

More screens (project intake wizard, QA-author standard/clause/requirement
editor, blog/FAQ admin, document ingestion status) are in
[`docs/images/`](docs/images/).

## Read this first

**The plan is still in flux.** Before opening a PR, read, in this order:

1. [`PLAN.md`](PLAN.md) — problem, solution, requirements, scope.
2. [`docs/adr/`](docs/adr/) — why each architectural decision was made,
   and what was rejected.
3. [`SLICES.md`](SLICES.md) — the build plan, one vertical slice at a time.
4. [`QUESTIONS.md`](QUESTIONS.md) — every decision made so far: decided,
   assumed (with the cost if the assumption is wrong), or deliberately
   deferred.

Those docs describe *intent*. For what's actually built right now, see
[`AGENTS.md`](AGENTS.md)'s build-status table — it's kept current in the
same PR that changes what's built, and takes priority over stale claims
elsewhere. `AGENTS.md` is also the machine/agent-oriented counterpart to
this README (exact commands, workflow conventions); `CLAUDE.md` just
imports it, so Claude Code and any other agent read the same file.

If something looks off, wrong, or missing — say so. Disagreement on any of
this is welcome; nothing here is locked in.

## Shape of the stack

```mermaid
flowchart LR
    subgraph Browser
        FE[Svelte + Vite<br/>:5173]
    end
    subgraph "Local host / Docker (make up)"
        FE -->|HTTP| BE[FastAPI<br/>:8000+]
        BE --> PG[(PostgreSQL<br/>:5433)]
        BE --> QD[(Qdrant<br/>:6333)]
        BE -->|RAG + LLM| LLM[OpenRouter / Ollama / ZenMux]
    end
```

The backend only ever ingests documents and answers questions grounded in
them and in a project's compliance state — it never authors or generates
document content of any kind (ADR-0012). Real company QMS documents are
sensitive and not available yet, so a fully separate tool,
`synthetic-corpus/`, generates realistic QMS-shaped PDFs to exercise the
same pipeline — it shares no code with the backend and doesn't call it
over HTTP either.

## Quick start

Requires Docker, [`uv`](https://docs.astral.sh/uv/), and Node 22+.

```bash
git clone https://github.com/leejianrong/qms-incub.git
cd qms-incub
make install        # backend + frontend deps, plus a local .env for each from its .env.example
make install-hooks  # pre-push hook — run once
make up              # Postgres + Qdrant (Docker), backend, frontend :5173, in the foreground
```

`make install`'s `.env` files default to `ollama`/local-embeddings/`bm25`/
no-rerank — no API key needed, so this works out of the box on a fresh
clone. Fill in `OPENROUTER_API_KEY` etc. afterwards if you want a hosted
provider (see Configuration).

`make up` prints which port it put the backend on — it tries `:8000` first
and falls back to `:8001`, `:8002`, ... if something else on your machine
already owns it (watch for a line like `Backend will run on port 8001`).
It wires the frontend's `VITE_API_BASE` to match automatically, so
`:5173` keeps working either way. `Ctrl+C` stops both dev servers;
`make down` also stops the Postgres/Qdrant containers.

> **Frontend port must stay `:5173`.** The backend's CORS is currently
> locked to `http://localhost:5173` (see `backend/src/qms_incub/main.py`)
> — there's no equivalent fallback wiring for the *frontend's* port, so
> `make up` checks `:5173` before touching Docker and refuses immediately
> with an actionable message if something else already holds it, rather
> than starting everything else first and letting Vite fail later. Free
> the port (`lsof -i :5173` / stop the other process) and re-run.

In another terminal, seed the demo data (needs `make up` running):

```bash
make seed-all   # the fixture doc, the 10-doc synthetic corpus, and the compliance/blog/FAQ demo data
```

Open http://localhost:5173 — the dashboard already has five demo projects
at different risk tiers and stages of completion. Open one and use the
floating **Ask QMS Assistant** widget — chat is project-scoped (V8), so it
always needs a project to ground against, even for a document-only
question.

`make seed-all` runs three independent, idempotent-ish steps you can also
run on their own — `make seed` (the single fixture doc), `make seed-corpus`
(the 10-doc synthetic corpus), `make seed-demo` (the compliance/blog/FAQ
data — genuinely idempotent, safe to re-run any time). See `make help` for
the full target list.

## Try the full workflow

`make seed-all` above already ingested the 10-document synthetic policy
corpus and seeded five classified demo projects. In the console, open one
of them and ask the chat widget a question that spans two policies, e.g.:

> If a proposed change requires provisioning new access to a system
> storing Confidential data, which policies apply and what does each one
> require?

It should cite both the Access Control (POL-006) and Data Classification
(POL-007) policies. Full walkthrough of what happens under the hood —
parsing, chunking, embedding, retrieval, reranking — is in
[`docs/rag-pipeline-walkthrough.md`](docs/rag-pipeline-walkthrough.md);
generating and using the synthetic corpus specifically is in
[`synthetic-corpus/README.md`](synthetic-corpus/README.md).

Other things worth trying once a project and the corpus exist: the QA-author
tools at `/editor` (author Standards → Clauses → Requirements) and
`/content` (draft and publish a blog post or FAQ entry — publishing adds
it to the same chat corpus as the PDFs); uploading a file against a todo
at `/project?id=...` to see self-attestation flip its approval state; and
the debug `POST /retrieve` endpoint to inspect raw retrieved chunks
without spending any LLM tokens.

Separately, `POST /aor/classify` routes an AOR PDF to R&T or SSD by
embedding-similarity against two reference descriptions — no LLM, Qdrant,
or Postgres involved, and it never touches the chat corpus. See
[`docs/aor-routing.md`](docs/aor-routing.md) for file layout and testing
it without the UI.

## Scoring retrieval quality

`rag-eval/` is a standalone tool (no HTTP dependency on the backend, but a
local `uv` path dependency on it) that scores retrieval — NDCG@k,
Recall@k, MRR — against a 110-question gold set derived from the
synthetic corpus:

```bash
cd rag-eval   # make install already created rag-eval/.env — keep its values identical to backend/.env
uv run python -m rag_eval.build_goldset   # (re)build the gold set, only if the corpus/chunking changed
uv run python -m rag_eval                 # score retrieval: NDCG@k, Recall@k, MRR
```

See [`docs/rag-pipeline-walkthrough.md`](docs/rag-pipeline-walkthrough.md#scoring-retrieval-quality-rag-eval)
for how to read the report, a config gotcha specific to this tool
(it reads its *own* `.env`, not `backend/.env`), and how to point it at
ZenMux embeddings/reranking instead of the local/BM25 defaults.

## Configuration

> **2026-09-01 through 2026-09-05 only:** prefer `LLM_PROVIDER=zenmux` — a
> ZenMux API key was sent to the team separately for this promotional
> window (Q39, `QUESTIONS.md`). From 2026-09-06, this lapses automatically;
> go back to `openrouter` (preferred) or `ollama`, whichever you'd use
> normally.

Every variable is documented where it's read: `backend/.env.example` for
the backend and `rag-eval/.env.example` for the eval tool (a subset of the
same settings — no `DATABASE_URL`, since `rag-eval` never touches
Postgres). The ones worth knowing about up front:

| Variable | Where | Default | Purpose |
|----------|-------|---------|---------|
| `VITE_API_BASE` | `frontend/.env.local` (see `.env.example`) | `http://localhost:8000` | Where the frontend looks for the backend — `make up` sets this for you |
| `LLM_PROVIDER` | `backend/.env` | `ollama` | `ollama` (local, no key), `openrouter` (ADR-0003's decided default — needs `OPENROUTER_API_KEY`), or `zenmux` (needs `ZENMUX_API_KEY` — promotional window only, see above) |
| `EMBEDDING_PROVIDER` | `backend/.env` | `local` | `local` runs a small HuggingFace model in-process, no key needed. `openrouter`/`zenmux` call a hosted `/embeddings` endpoint instead. **Switching this requires re-ingesting the corpus** — it changes vector dimensionality, unlike `RETRIEVAL_MODE` |
| `RETRIEVAL_MODE` | `backend/.env` | `bm25` | `bm25` (sparse lexical) or `vector` (dense, via `EMBEDDING_PROVIDER`) — hot-swappable, no re-ingest needed |
| `RERANKER_PROVIDER` | `backend/.env` | `none` | `none`, `zenmux` (hosted cross-encoder), or `llm` (prompts whichever `LLM_PROVIDER` is already set) |
| `OPENROUTER_API_KEY` / `ZENMUX_API_KEY` | `backend/.env` | unset | Required only when the matching provider above is selected |

Postgres and Qdrant ports (`5433`, `6333`) are set in `docker-compose.yml`;
5433 rather than Postgres's usual 5432 to avoid colliding with a Postgres
already running on your machine.

## Troubleshooting

**`/documents` or `/chat` suddenly 500s after pulling latest, with Qdrant
logging something like `Not existing vector name`.** A schema-changing
pull (e.g. a renamed vector field) landed on top of a Qdrant volume from
before that change — `make down` deliberately keeps Postgres/Qdrant data
around, so an old collection schema can outlive the code that created it.
Fix: `make reset` (wipes both volumes) then `make up` and re-seed
(`make seed-all`).

**Chat returns a 500 with `openai.NotFoundError: invalid_model`.** Your
`backend/.env`'s model name for the active `LLM_PROVIDER` is stale — most
often `ZENMUX_MODEL` left at a retired alias. Check the current default in
`backend/.env.example` and update your `.env` to match.

## Contributing

Branch per slice, PR-only, pre-push hook mirrors CI — see
[`AGENTS.md`](AGENTS.md) for the exact conventions and commands rather
than duplicating them here.

## Status

Internal project, not for external distribution.
