# Dev-mode image (ADR-0017): the working tree is bind-mounted over /app at
# runtime (see docker-compose.yml), so this build only needs to produce a
# venv with dependencies installed — source changes are picked up live via
# uvicorn --reload, no rebuild needed. Only a pyproject.toml/uv.lock change
# requires `docker compose build backend` again.
FROM python:3.12-slim

# libgl1/libglib2.0-0: opencv-python (pulled in by docling's layout/OCR
# models) links against libGL even though nothing here uses a GUI — import
# fails on a bare slim image without them. curl: container healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Keep the venv outside /app so the dev bind-mount (which overlays the
# whole /app directory with the host's working tree) doesn't shadow it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first, separately from the project itself, so
# editing application code doesn't invalidate this (slow) layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "qms_incub.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
