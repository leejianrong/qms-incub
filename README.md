# qms-incub

A QMS tool for project managers at a large company: classify a software
project, get a generated compliance todo list, upload proof you've done
the work, and ask a chatbot grounded in the company's own policy
documents. Internal project — see below before you assume anything about
scope is final.

## Read this first

**The plan is still in early days and will change.** Before writing code
or opening a PR, read, in this order:

1. [`PLAN.md`](PLAN.md) — problem, solution, requirements, scope.
2. [`docs/adr/`](docs/adr/) — why each architectural decision was made,
   and what was rejected.
3. [`SLICES.md`](SLICES.md) — the actual build plan, one vertical slice at
   a time.
4. [`QUESTIONS.md`](QUESTIONS.md) — every decision made so far: decided,
   assumed (with the cost if the assumption is wrong), or deliberately
   deferred.

If something looks off, wrong, or missing — say so. Suggestions and
disagreement on any of this are welcome; nothing here is locked in.

[`CLAUDE.md`](CLAUDE.md) is the machine/agent-oriented counterpart to this
README: exact commands, build status, and workflow conventions, kept
current for whoever (human or agent) is about to work in the repo.

## Shape of the stack

```mermaid
flowchart LR
    subgraph Browser
        FE[Svelte + Vite<br/>:5173]
    end
    subgraph "Local host / Docker (make up)"
        FE -->|HTTP| BE[FastAPI<br/>:8000]
        BE --> PG[(PostgreSQL<br/>:5433)]
        BE --> QD[(Qdrant<br/>:6333)]
        BE -->|RAG| OR[OpenRouter LLM<br/>external]
    end
```

V1 (the RAG spike) is built: a policy document generated, exported to
PDF, ingested into Qdrant, and queryable through a chat panel with
citations. Real company QMS documents are sensitive and not available
yet, so V5 adds a local CLI (`make batch`) that generates synthetic
policy documents to exercise the same pipeline — deliberately not part
of the running app (ADR-0011). Everything else in PLAN.md/SLICES.md is
still ahead — see `CLAUDE.md`'s build-status table for exactly what
exists.

## Quick start

Requires Docker, [`uv`](https://docs.astral.sh/uv/), and Node 22+.

```bash
git clone https://github.com/leejianrong/qms-incub.git
cd qms-incub
make install        # backend + frontend dependencies
make install-hooks  # pre-push hook — run once
cp backend/.env.example backend/.env  # then fill in an OpenRouter key if you want it (see below)
make up              # Postgres + Qdrant (Docker), backend :8000, frontend :5173
```

In another terminal, seed V1's demo document (needs `make up` running):

```bash
make seed
```

Open http://localhost:5173, ask "Who is the approving authority for this
policy?", and you should get a grounded answer citing the seeded document.
`make down` stops the containers; Ctrl+C stops the dev servers.

To generate more test documents locally and stress-test ingestion
(without any real, sensitive QMS content — see ADR-0011), run:

```bash
make batch COUNT=20 SEED=1
```

This prints a per-document status summary; it's CLI-only, not reachable
through the app itself.

## Configuration

| Variable | Where | Default | Purpose |
|----------|-------|---------|---------|
| `VITE_API_BASE` | `frontend/.env.local` (see `.env.example`) | `http://localhost:8000` | Where the frontend looks for the backend |
| `LLM_PROVIDER` | `backend/.env` (see `.env.example`) | `ollama` | `ollama` (local, no key) or `openrouter` (ADR-0003's decided default — needs `OPENROUTER_API_KEY`) |
| `OPENROUTER_API_KEY` | `backend/.env` | unset | Required only when `LLM_PROVIDER=openrouter`. Get one at https://openrouter.ai/keys |

Postgres and Qdrant ports (`5433`, `6333`) are set in `docker-compose.yml`;
5433 rather than Postgres's usual 5432 to avoid colliding with a Postgres
already running on your machine.

## Contributing

Branch per slice, PR-only, pre-push hook mirrors CI — see `CLAUDE.md` for
the exact conventions and commands rather than duplicating them here.

## Status

Internal project, not for external distribution.
