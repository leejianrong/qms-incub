.PHONY: help up down reset migrate env seed seed-corpus seed-demo seed-all test lint typecheck install install-hooks backend-dev frontend-dev

# Bare `make` shows available targets instead of running the first one.
.DEFAULT_GOAL := help

# Read by the curl-based seed targets below, so they hit the same port
# docker-compose.yml publishes (ADR-0017) — one place to change if 5173 is
# already taken on your machine, no code edit needed on either side.
-include .env
APP_PORT ?= 5173

help:
	@echo "Available targets:"
	@echo "  install        Install backend/frontend dependencies and create local .env files"
	@echo "  install-hooks  Symlink the pre-push git hook"
	@echo "  up             Start the full stack (Postgres, Qdrant, backend, frontend, proxy) via Docker Compose"
	@echo "  down           Stop all containers (keeps their data)"
	@echo "  reset          Stop containers AND wipe their data volumes — needed after a"
	@echo "                 pull changes Qdrant's schema and ingestion starts 500ing"
	@echo "  migrate        Apply Alembic migrations against Postgres"
	@echo "  seed           Upload the sample fixture PDF, proving local ingestion+chat work"
	@echo "  seed-corpus    Generate + ingest the 10-doc synthetic policy corpus"
	@echo "  seed-demo      Seed demo standard/projects/blog/FAQ content (ui-reference-shaped)"
	@echo "  seed-all       seed + seed-corpus + seed-demo, in one go"
	@echo "  test           Run backend and frontend fast/no-infra tests"
	@echo "  lint           Run backend and frontend linters"
	@echo "  typecheck      Run backend and frontend type checkers"
	@echo "  backend-dev    Run only the backend dev server, natively on the host"
	@echo "  frontend-dev   Run only the frontend dev server, natively on the host"

# Creates each local .env from its .env.example if one doesn't already
# exist -- never overwrites a real one. Root .env carries APP_PORT for
# Docker Compose/this Makefile; backend's default LLM_PROVIDER needs a
# real OPENROUTER_API_KEY or ZENMUX_API_KEY (ADR-0017 -- the Dockerized
# backend has no route to a host-run Ollama). `make install` and `make up`
# both depend on this, so you rarely need to run it directly.
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env"; }
	@[ -f backend/.env ] || { cp backend/.env.example backend/.env; echo "created backend/.env"; }
	@[ -f frontend/.env.local ] || { cp frontend/.env.example frontend/.env.local; echo "created frontend/.env.local"; }
	@[ -f rag-eval/.env ] || { cp rag-eval/.env.example rag-eval/.env; echo "created rag-eval/.env"; }

install: env
	cd backend && uv sync
	cd frontend && npm install

install-hooks:
	ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
	@echo "pre-push hook installed."

# One-command local bring-up (ADR-0005/ADR-0009/ADR-0017): the whole stack
# -- Postgres, Qdrant, a one-shot Alembic-migration service, the FastAPI
# backend, the Svelte/Vite frontend, and an nginx proxy -- runs in Docker
# Compose. The proxy is the only container publishing a port to the host
# (APP_PORT, default 5173, set in .env) and routes / to the frontend dev
# server (HMR included) and /api/* to the backend, so the browser only
# ever sees one origin -- a busy port is a one-line .env edit, and CORS
# never comes into play (see nginx/default.conf). Ctrl+C stops everything;
# run `make down` afterwards to also remove the containers.
up: env
	docker compose up --build

down:
	docker compose down

# Full reset for when a pull changes Qdrant's (or Postgres's) schema and a
# volume from before that change is still sitting on disk -- e.g. ingestion
# suddenly 500ing with "Not existing vector name" is exactly this, because
# `down` alone only stops containers and deliberately keeps their volumes.
# Destroys all local Postgres/Qdrant data; re-seed afterwards.
reset:
	docker compose down -v

# Applies Alembic migrations. `make up` runs this automatically (the
# `migrate` service in docker-compose.yml) before the backend starts; this
# target is for running it again by hand without restarting the stack.
migrate:
	docker compose run --rm migrate

# V1 (SLICES.md S1): uploads the sample fixture PDF through the real
# /documents endpoint (behind the proxy's /api prefix, ADR-0017), the same
# path any real user's upload takes. Requires `make up` running and, for
# embeddings, a first-run HuggingFace model download.
seed:
	curl -sf -F "file=@backend/tests/fixtures/sample_policy_document.pdf" "http://localhost:$(APP_PORT)/api/documents" | tee /dev/stderr | grep -q '"status":"embedded"'

# Wraps the README's "Try the full workflow" steps: generates the 10
# synthetic QMS-policy PDFs (no shared code/HTTP with the backend,
# ADR-0012) and ingests every one of them through the real /documents
# endpoint, the same path a real upload takes. Requires `make up` running.
seed-corpus:
	cd synthetic-corpus && uv sync && uv run python scripts/generate.py
	@for f in synthetic-corpus/output/POL-*.pdf; do \
	   echo "Ingesting $$f..."; \
	   curl -sf -F "file=@$$f" "http://localhost:$(APP_PORT)/api/documents" | tee /dev/stderr | grep -q '"status":"embedded"' || exit 1; \
	 done

# Seeds a QMS standard, five demo projects, and blog/FAQ content shaped
# like ui-reference/QMS Console.dc.html, through the real API (backend/
# scripts/seed_demo.py). Idempotent -- safe to re-run. Requires `make up`.
seed-demo:
	cd backend && uv run python scripts/seed_demo.py --api-base "http://localhost:$(APP_PORT)/api"

# Everything above in one go: the single fixture doc, the 10-doc synthetic
# corpus, and the compliance/blog/FAQ demo data. Requires `make up` running.
seed-all: seed seed-corpus seed-demo

# Fast, no-infra layer only -- see dev-playbook (layered-testing.md). Runs
# against the host's own uv/npm, not the Docker images -- no `make up`
# needed.
test:
	cd backend && uv run pytest -q
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy src
	cd frontend && npm run check

# Host-only escape hatches for anyone who wants a native debugger attached,
# or needs LLM_PROVIDER=ollama (only reachable from a host process, not
# the Dockerized backend -- ADR-0017). Point backend/.env's DATABASE_URL/
# QDRANT_URL at their localhost ports (the defaults in .env.example) and
# bring up just `postgres`/`qdrant` first: `docker compose up -d postgres qdrant`.
backend-dev:
	cd backend && uv run uvicorn qms_incub.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev
