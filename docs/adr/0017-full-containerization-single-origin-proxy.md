# ADR-0017: Full Docker Compose containerization, single-origin reverse proxy

- Status: Accepted
- Date: 2026-09-02
- Deciders: leejianrong (user); agent
- Supersedes: ADR-0005's "fully containerized app" alternative, which was
  explicitly considered there and rejected in favor of containerizing only
  the stateful services (Postgres) with the app itself running on the
  host. ADR-0005's actual decision — everything runs locally, no cloud
  deploy target — is unaffected, as are ADR-0009's stack choices.

## Context

ADR-0005 explicitly considered running the whole app in Docker, not just
Postgres, and rejected it: "slower iteration loop for a project still
being actively built." That trade-off held while the app was one Next.js
process and, later, two host-run dev servers (`uvicorn`, `vite`) beside
two containerized stateful services (Postgres, Qdrant — ADR-0009).

In practice, that split created a recurring, annoying failure mode: the
frontend's dev-server port (`:5173`) is hardcoded into the backend's CORS
allow-list (`backend/src/qms_incub/main.py`) with no fallback wiring, and
Vite is pinned with `strictPort: true` so a `:5173` already held by an
unrelated process fails `make up` outright instead of degrading. Relaxing
`strictPort` would only trade one failure for a worse one — Vite silently
moving to `:5174` while the backend's CORS allow-list still only permits
`:5173`, turning a loud port conflict into a confusing CORS error. The
actual problem was structural: the frontend and backend are two different
origins on the host, at all, whenever a port is negotiable.

## Decision

Backend and frontend now run as containers on the same Docker Compose
network as Postgres and Qdrant, alongside a new nginx reverse-proxy
service that is the *only* container publishing a port to the host
(`APP_PORT`, default `5173`, read from a new root `.env`/`.env.example`
by both `docker-compose.yml` and the Makefile). The proxy serves the Vite
dev server — HMR passed through via a websocket-upgrade location block —
at `/`, and forwards `/api/*` to the FastAPI backend, stripping the
prefix. The browser therefore only ever talks to one origin.
`frontend/src/lib/api.ts`'s single `resolveApiBase()` entry point meant
this needed no per-call-site changes — only `VITE_API_BASE`, set to `/api`
for the Dockerized frontend in `docker-compose.yml`, changed.
`backend/src/qms_incub/main.py`'s CORS middleware is untouched — it's
still needed for the host-only `backend-dev`/`frontend-dev` escape hatch,
where the two dev servers remain two origins — but the Dockerized path
never exercises it.

Both containers run in dev mode: `uvicorn --reload` and Vite's own dev
server, with the working tree bind-mounted in (venv and `node_modules`
kept out of the mount's way — an external `UV_PROJECT_ENVIRONMENT` for
the backend, an anonymous volume over `node_modules` for the frontend) so
editing code on the host is picked up immediately. Nothing rebuilds for a
source change, only for a dependency change
(`pyproject.toml`/`uv.lock` or `package.json`/`package-lock.json`). This
is what removes the trade-off ADR-0005 was protecting against: full
containerization only cost iteration speed when the alternative was a
from-scratch image rebuild per edit, and dev-mode bind mounts avoid that
entirely.

`make up` now means `docker compose up --build` for the whole stack
(Postgres, Qdrant, a one-shot Alembic-migration service, backend,
frontend, proxy) instead of the previous hybrid of two containers plus
two foreground host processes with a hand-rolled port-availability
bash loop. `backend-dev`/`frontend-dev` remain as host-only Makefile
targets for anyone who wants a native debugger attached, or needs
`ollama` (below).

**Ollama is not part of the Docker network.** The Dockerized backend has
no route to a host-run Ollama instance — wiring `host.docker.internal`,
or containerizing Ollama itself, were both considered and declined (this
project already treats `openrouter`/`zenmux` as the standing default for
anything beyond quick local iteration, per Q37/Q39). `backend/.env.example`'s
default `LLM_PROVIDER` changes from `ollama` to `openrouter` accordingly:
a fresh clone's `make up` now needs a real `OPENROUTER_API_KEY` (or
`ZENMUX_API_KEY` during the Q39 promotional window) before `/chat` works.
`ollama` still works, unchanged, for the host-only `backend-dev` path.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Two published ports, made configurable (`FRONTEND_PORT`/`BACKEND_PORT` in `.env`) instead of a proxy | Turns a hard failure into a one-line config edit, but doesn't remove CORS — two origins still exist, and both ports still need to be free (twice the collision surface of one) |
| Route Ollama into the container network (`host.docker.internal`) | The team's preference is to standardize on `openrouter`/`zenmux` rather than keep a host-networking special case for one provider |
| Containerize Ollama itself | Re-pulls models into a container volume and adds GPU-passthrough configuration for comparable performance, for a provider the team doesn't want as the default path anyway |
| Production-style build (nginx serving a static Vite build, no dev server) | Would lose HMR/hot-reload during active development — the exact iteration-speed cost ADR-0005 was protecting against. Dev-mode containers with bind mounts get the same speed without that cost |
| Prefix every backend route with `/api` in FastAPI itself | The proxy strips the prefix instead, so no backend route or frontend call site needed to change — smaller diff, same result |

## Consequences

Gains: one command, one port, one origin. `make up` brings up the entire
stack; a busy port is a one-line `.env` edit; CORS is structurally
unreachable on the Dockerized path rather than configured around it.
Backend and frontend reach Postgres/Qdrant by service name inside the
compose network, so those two ports also stop mattering to application
wiring — their host-side publishing is now only for direct
`psql`/Qdrant-dashboard access.

Costs: the Dockerized path requires a real LLM API key from a fresh
clone — no more zero-config `ollama` default — offset by keeping
`backend-dev` as a host-only path where `ollama` still works. nginx
config is a new piece of infrastructure to maintain, and Vite's HMR
websocket proxying is a known-fiddly integration point worth checking
first if hot-reload ever stops updating live.
