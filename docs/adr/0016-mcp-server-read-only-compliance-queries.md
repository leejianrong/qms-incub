# ADR-0016: An MCP server exposing read-only compliance queries, next to the chat pipeline

- Status: Accepted — for the **next milestone**, alongside ADR-0014 and
  ADR-0015. Not built as part of the current MVP (V1–V13).
- Date: 2026-09-01
- Deciders: leejianrong (user); agent (agents/MCP/CLI/identity research
  session)

## Context

ADR-0003 deliberately kept a PM's own compliance state out of the vector
store — it's small, structured, and changes on every write, so it's
injected directly into the chat prompt instead of embedded. That ADR's
Consequences section named the thing that doesn't fit that pipeline at
all: a query that reads *across* many PMs' state ("which projects are
non-compliant") is "a different mechanism... not covered by this
decision," i.e. a reporting feature, not a chat extension.

Separately, external agents — a PM's own Claude Code session, an internal
ops agent doing compliance triage, a CI job — currently have no way to ask
this backend anything at all except by going through a human who then
uses the web UI. Q9 keeps the product's own chatbot retrieval-only and
non-agentic; that assumption is about the *product's* chat feature, not
about whether an external tool-calling agent can query the same
underlying data through a different, narrower door.

## Decision

Build an MCP server that runs alongside the FastAPI backend and calls it
the same way the CLI does (ADR-0015's client library — not a third
reimplementation of request logic). It authenticates as required by the
MCP spec for a remote server: OAuth 2.1 resource-server validation against
the Keycloak realm from ADR-0014.

Its first tool set is deliberately narrow and read-only:

- `ask_policy` — the same corpus retrieval `POST /chat` does, no per-user
  state injected. Answers static policy questions.
- `get_project_status` — a given project's own todo/artifact state,
  scoped to whatever org/role the caller's token actually carries.

**Explicitly not decided here:** a tool that reads across every PM's
data (the `list_noncompliant_projects` idea ADR-0003 gestured at). That
needs a role with organization-wide read, which is a different authz
shape from everything else in this app — every other surface, including
the two tools above, is scoped to the caller's own state. Left open as
QUESTIONS.md Q49 rather than assumed. Also explicitly out: any tool that
authors or acts on the PM's behalf (drafts a Requirement, submits an
artifact) — that's Q9 and ADR-0012's boundary, unchanged by this ADR.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Fold cross-project reporting into this same server now, since the retrieval logic is similar | Conflates a decided, narrow-scope tool with an undecided authz shape (org-wide read vs. self-scoped read). Better to ship the settled half and leave the harder question open than block on it |
| Skip MCP; a CLI alone is enough | A CLI serves scripting and CI, not an agent's tool-call surface — Claude Code, Claude Desktop, and similar clients need MCP specifically to reach this data inside their own sessions |
| Extend `POST /chat` itself to serve MCP clients directly | Chat's grounding model (ADR-0003) is tuned for a conversational answer with citations; MCP tools want a structured, typed response instead — worth a separate surface rather than overloading one endpoint's contract |

## Consequences

Gains: an agent-facing query surface without touching ADR-0003's chat
pipeline, and without reopening Q9 — nothing here authors anything, it
only reads what already exists. Gives Claude Code / Claude Desktop /
similar clients a way to answer a PM's compliance questions inside their
own working session, not just inside the product's own chat panel.

Costs: a second place, alongside `POST /chat`, that has to stay
consistent with the corpus's retrieval behavior — worth watching for
drift once both exist. Whether a team-facing MCP server counts as the
"external API for third-party integration" Q17 deferred is its own open
question (QUESTIONS.md Q48), not resolved by building this.

Forecloses: nothing structural. Cross-project reporting and any
action-taking tool remain open, separate decisions (Q49, Q50), not things
this ADR rules out — just things it doesn't include yet.
