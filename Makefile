.PHONY: help up down migrate seed test lint typecheck install install-hooks backend-dev frontend-dev

# Bare `make` shows available targets instead of running the first one.
.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  up             Start Postgres+Qdrant, then backend and frontend dev servers"
	@echo "  down           Stop and remove the Postgres/Qdrant containers"
	@echo "  migrate        Apply Alembic migrations against Postgres"
	@echo "  seed           Upload the sample fixture PDF, proving local ingestion+chat work"
	@echo "  install        Install backend and frontend dependencies"
	@echo "  install-hooks  Symlink the pre-push git hook"
	@echo "  test           Run backend and frontend fast/no-infra tests"
	@echo "  lint           Run backend and frontend linters"
	@echo "  typecheck      Run backend and frontend type checkers"
	@echo "  backend-dev    Run only the backend dev server"
	@echo "  frontend-dev   Run only the frontend dev server"

# One-command local bring-up (ADR-0005, ADR-0009): Postgres + Qdrant in
# Docker, FastAPI backend and Svelte/Vite frontend on the host. Ctrl+C stops
# both dev servers; run `make down` to also stop the containers.
up:
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
	 trap 'kill 0' EXIT INT TERM; \
	 (cd backend && uv run uvicorn qms_incub.main:app --reload --port $$port) & \
	 (cd frontend && VITE_API_BASE="http://localhost:$$port" npm run dev) & \
	 wait

down:
	docker compose down

# V5: applies Alembic migrations (needs Postgres up — `make up` calls this
# automatically before starting the dev servers).
migrate:
	cd backend && uv run alembic upgrade head

# V1 (SLICES.md § V1): uploads the sample fixture PDF through the real
# /documents endpoint, the same path any real user's upload takes. Requires
# `make up` running (backend + Qdrant) and, for embeddings, a first-run
# HuggingFace model download.
seed:
	curl -sf -F "file=@backend/tests/fixtures/sample_policy_document.pdf" http://localhost:8000/documents | tee /dev/stderr | grep -q '"status":"embedded"'

install:
	cd backend && uv sync
	cd frontend && npm install

install-hooks:
	ln -sf ../../scripts/git-hooks/pre-push .git/hooks/pre-push
	@echo "pre-push hook installed."

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
