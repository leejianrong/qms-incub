.PHONY: help up down reset migrate env seed seed-corpus seed-demo seed-all test lint typecheck install install-hooks backend-dev frontend-dev

# Bare `make` shows available targets instead of running the first one.
.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  install        Install backend/frontend dependencies and create local .env files"
	@echo "  install-hooks  Symlink the pre-push git hook"
	@echo "  up             Start Postgres+Qdrant, then backend and frontend dev servers"
	@echo "  down           Stop the Postgres/Qdrant containers (keeps their data)"
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
	@echo "  backend-dev    Run only the backend dev server"
	@echo "  frontend-dev   Run only the frontend dev server"

# Creates each local .env from its .env.example if one doesn't already
# exist — never overwrites a real one. Defaults (ollama/local-embeddings/
# bm25/no-rerank) need no API key, so a fresh clone works out of the box;
# fill in OPENROUTER_API_KEY etc. afterwards if you want a hosted provider.
env:
	@[ -f backend/.env ] || { cp backend/.env.example backend/.env; echo "created backend/.env"; }
	@[ -f frontend/.env.local ] || { cp frontend/.env.example frontend/.env.local; echo "created frontend/.env.local"; }
	@[ -f rag-eval/.env ] || { cp rag-eval/.env.example rag-eval/.env; echo "created rag-eval/.env"; }

install: env
	cd backend && uv sync
	cd frontend && npm install

install-hooks:
	ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
	@echo "pre-push hook installed."

# One-command local bring-up (ADR-0005, ADR-0009): Postgres + Qdrant in
# Docker, FastAPI backend and Svelte/Vite frontend on the host. Ctrl+C stops
# both dev servers; run `make down` to also stop the containers.
#
# The frontend port has no fallback (backend CORS is hardcoded to
# http://localhost:5173, see backend/src/qms_incub/main.py) and Vite is
# pinned with strictPort (frontend/vite.config.ts) so a taken :5173 fails
# loudly instead of silently moving to :5174 and breaking every API call
# with a CORS error that doesn't look port-related. Checked up front, before
# touching Docker, so a busy port fails in under a second instead of after
# Postgres/Qdrant/the backend have all already started.
up: env
	@if ss -ltn "( sport = :5173 )" 2>/dev/null | grep -q LISTEN; then \
	   echo "Port 5173 is already in use — the frontend needs this exact port for CORS."; \
	   echo "Free it (lsof -i :5173) and re-run 'make up'."; \
	   exit 1; \
	 fi
	docker compose up -d postgres qdrant
	@echo "Waiting for Postgres and Qdrant to be healthy..."
	@until [ "$$(docker compose ps -q postgres | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do sleep 1; done
	$(MAKE) migrate
	@port=8000; \
	 while ss -ltn "( sport = :$$port )" 2>/dev/null | grep -q LISTEN; do \
	   echo "Port $$port is already in use, trying $$((port + 1))..."; \
	   port=$$((port + 1)); \
	 done; \
	 if [ "$$port" != 8000 ]; then \
	   echo "Backend will run on port $$port (8000 was busy)"; \
	 fi; \
	 echo $$port > .backend-port.local; \
	 trap 'kill 0' EXIT INT TERM; \
	 (cd backend && uv run uvicorn qms_incub.main:app --reload --port $$port) & \
	 (cd frontend && VITE_API_BASE="http://localhost:$$port" npm run dev) & \
	 wait

down:
	docker compose down

# Full reset for when a pull changes Qdrant's (or Postgres's) schema and a
# volume from before that change is still sitting on disk — e.g. ingestion
# suddenly 500ing with "Not existing vector name" is exactly this, because
# `down` alone only stops containers and deliberately keeps their volumes.
# Destroys all local Postgres/Qdrant data; re-seed afterwards.
reset:
	docker compose down -v

# V5: applies Alembic migrations (needs Postgres up — `make up` calls this
# automatically before starting the dev servers).
migrate:
	cd backend && uv run alembic upgrade head

# V1 (SLICES.md § V1): uploads the sample fixture PDF through the real
# /documents endpoint, the same path any real user's upload takes. Requires
# `make up` running (backend + Qdrant) and, for embeddings, a first-run
# HuggingFace model download. Targets whichever port `make up` actually
# picked (.backend-port.local, written by `up` — falls back to 8000 if
# that file doesn't exist, e.g. `backend-dev` was used instead of `up`).
seed:
	@port=$$(cat .backend-port.local 2>/dev/null || echo 8000); \
	 curl -sf -F "file=@backend/tests/fixtures/sample_policy_document.pdf" "http://localhost:$$port/documents" | tee /dev/stderr | grep -q '"status":"embedded"'

# Wraps the README's "Try the full workflow" steps: generates the 10
# synthetic QMS-policy PDFs (no shared code/HTTP with the backend,
# ADR-0012) and ingests every one of them through the real /documents
# endpoint, the same path a real upload takes. Requires `make up` running.
seed-corpus:
	cd synthetic-corpus && uv sync && uv run python scripts/generate.py
	@port=$$(cat .backend-port.local 2>/dev/null || echo 8000); \
	 for f in synthetic-corpus/output/POL-*.pdf; do \
	   echo "Ingesting $$f..."; \
	   curl -sf -F "file=@$$f" "http://localhost:$$port/documents" | tee /dev/stderr | grep -q '"status":"embedded"' || exit 1; \
	 done

# Seeds a QMS standard, five demo projects, and blog/FAQ content shaped
# like ui-reference/QMS Console.dc.html, through the real API (backend/
# scripts/seed_demo.py). Idempotent — safe to re-run. Requires `make up`.
seed-demo:
	@port=$$(cat .backend-port.local 2>/dev/null || echo 8000); \
	 cd backend && uv run python scripts/seed_demo.py --api-base "http://localhost:$$port"

# Everything above in one go: the single fixture doc, the 10-doc synthetic
# corpus, and the compliance/blog/FAQ demo data. Requires `make up` running.
seed-all: seed seed-corpus seed-demo

# Fast, no-infra layer only — see dev-playbook (layered-testing.md).
test:
	cd backend && uv run pytest -q
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy src
	cd frontend && npm run check

backend-dev:
	cd backend && uv run uvicorn qms_incub.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev
