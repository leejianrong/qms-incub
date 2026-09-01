# ADR-0014: Keycloak as the identity provider for humans and machine agents

- Status: Accepted — for the **next milestone**, not this one. PLAN.md's
  Scope > Out ("SSO / external identity provider integration") and Q18
  (DEFERRED) still hold for the current MVP; this ADR decides the
  mechanism for when that work starts, without pulling it into V1–V13.
- Date: 2026-09-01
- Deciders: leejianrong (user); agent (agents/MCP/CLI/identity research
  session)

## Context

Every endpoint the backend exposes today (`POST /documents`,
`GET /documents`, `POST /chat`) runs with no `Depends()`, no session, no
notion of who's asking — there is no identity concept anywhere in the
code. ADR-0004 put an `org_id` column on every table for a multi-tenant
future, but nothing enforces it yet, because there's nothing to enforce it
against.

A research session mapping agents, MCP, a CLI, and auth onto this
project's architecture (see the `docs/adr/0015`/`0016` companions and
QUESTIONS.md Q45–Q50) surfaced that "auth for humans and agents" is
actually two distinct problems: a human (PM, QA-author, and eventually a
Reviewer per F7) needs a browser login and a session; a machine (the CLI,
an MCP client, a CI job) needs a token with nobody in the loop at all.
Both need to end up carrying the same role and `org_id` claim, or the two
surfaces drift apart over time.

Separately, the MCP protocol's own authorization spec requires a remote
MCP server to act as an OAuth 2.1 resource server — so whatever backs
human login also needs to be able to back that, or the project ends up
running two identity systems side by side.

## Decision

Stand up **Keycloak**, self-hosted, as one more service in
`docker-compose.yml` (alongside Postgres and Qdrant), with a single realm
for the org. That realm backs all of the following, once the next
milestone starts building against it:

1. **Human login** — the Svelte console redirects an unauthenticated
   visitor through Keycloak's OIDC authorization-code-with-PKCE flow,
   coming back with a session. Roles: `pm`, `qa-author`, and a placeholder
   `reviewer` (seeded but unused until F7's reviewer-gate feature is
   actually built).
2. **Human authz** — the backend validates the realm's JWTs and reads the
   role and `org_id` claims off them; `org_id` (ADR-0004) becomes a real
   enforced filter for the first time instead of a column nothing checks.
3. **Machine-to-machine auth** — the CLI (ADR-0015) and any CI job
   authenticate via an OAuth2 client-credentials grant against the same
   realm, getting a service-account token scoped the same way a human's
   token is.
4. **MCP's own auth requirement** — the MCP server (ADR-0016) satisfies
   its spec-mandated OAuth 2.1 resource-server role against this same
   realm, rather than a bespoke implementation.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Roll a bespoke JWT auth layer | Reinvents session handling, password storage, and token issuance that Keycloak already solves, and still needs a second flow built for machine clients — exactly the drift this decision exists to prevent |
| A managed IdP (Auth0, Okta, Clerk) | Reopens ADR-0005's local-only, no-cloud-account posture for a laptop demo. Keycloak runs as one more container `make up` already knows how to bring up; a managed IdP adds an external account and network dependency the rest of the stack doesn't have |
| Separate mechanisms per surface — cookies for the web, API keys for the CLI/MCP | Multiplies where roles and org scoping are defined; the whole point of this decision is one source of truth, not three that drift |

## Consequences

Gains: one realm defines roles and org scoping for every surface —
browser, CLI, MCP, CI — instead of four bespoke mechanisms. A straight
line to F7's deferred reviewer role: it's a third realm role added later,
not a new subsystem. `org_id` (ADR-0004) finally has something enforcing
it.

Costs: another container in `docker-compose.yml` and `make up`. Every
existing endpoint needs an auth guard added when this milestone starts —
a real, if mechanical, change to backend code that currently has none.
Local dev needs a seeded realm/client/demo-user config committed
alongside the Postgres/Qdrant seed data.

Forecloses: nothing structural. Keycloak is swappable for another OIDC
provider later without touching how the app validates tokens, since the
integration is standard OIDC/OAuth2, not Keycloak-specific. Does **not**
reopen Q18 or PLAN.md's current-milestone scope — see the Status line
above.
