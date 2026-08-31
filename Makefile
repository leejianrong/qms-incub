.PHONY: up down seed test lint typecheck install install-hooks backend-dev frontend-dev

# One-command local bring-up (ADR-0005, ADR-0009): Postgres + Qdrant in
# Docker, FastAPI backend and Svelte/Vite frontend on the host. Ctrl+C stops
# both dev servers; run `make down` to also stop the containers.
up:
	docker compose up -d postgres qdrant
	@echo "Waiting for Postgres and Qdrant to be healthy..."
	@until [ "$$(docker compose ps -q postgres | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do sleep 1; done
	@trap 'kill 0' EXIT INT TERM; \
	 (cd backend && uv run uvicorn qms_incub.main:app --reload --port 8000) & \
	 (cd frontend && npm run dev) & \
	 wait

down:
	docker compose down

# Stub until the data model (PLAN.md, ADR-0008) has migrations to seed.
seed:
	@echo "No schema/migrations yet — nothing to seed."

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
