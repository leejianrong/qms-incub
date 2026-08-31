# ADR-0003: Chatbot grounds on vector retrieval plus direct injection of the user's own state, via OpenRouter

- Status: Accepted
- Date: 2026-08-31
- Deciders: leejianrong (user), agent (plan-new-project skill, round 3)

## Context

The user asked for a chatbot that answers both static process questions
("who is the approving authority") and personal-status questions ("am I
compliant so far"), backed by an LLM reached through the OpenRouter API.
The first kind of question is answerable from the ingested policy/blog/FAQ
corpus via standard RAG retrieval. The second kind depends on data that is
specific to the asking PM and changes constantly (their project's todo and
artifact state) — putting that into the same vector store as static policy
content would mean re-embedding on every todo status change, for a tiny
amount of data that doesn't benefit from similarity search in the first
place.

## Decision

The chat request handler builds the LLM prompt from two distinct sources:
(1) the top-k chunks retrieved by vector similarity search over the
ingested corpus (policy documents, blog posts, FAQ entries), and (2) a
directly-injected, fixed-shape JSON block containing the asking PM's own
current `Project`, `TodoItem`, and `Artifact` rows, pulled straight from
the database. The two are kept in separate, labeled sections of the prompt
so the model — and the citation logic — can distinguish "this is policy
knowledge" from "this is your status". The LLM call goes through the
OpenRouter API.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Vectorize and retrieve user compliance state alongside corpus chunks | Per-user state is small, structured, and changes on every todo update — re-embedding on every write is unnecessary cost for data that doesn't need similarity search, it needs exact lookup |
| Two separate chat features (one for policy Q&A, one for status Q&A) | The user asked for both to be answerable "to see if they're compliant... query about the process... " in one chatbot experience, not two |
| Direct LLM provider (OpenAI/Anthropic API) instead of OpenRouter | User specified OpenRouter directly |

## Consequences

Gains: personal status answers are always current (no staleness from an
embedding refresh cycle), and the retrieval pipeline (S6) stays focused on
content that actually benefits from semantic search. Costs: the prompt
template has to keep the two sections cleanly separated, and if a future
need arises to search *across* many PMs' compliance state (e.g. "which
projects are non-compliant"), that's a different mechanism (a structured
query, not RAG) not covered by this decision. Forecloses building a
"search across all users' state" feature on top of this chat pipeline
directly — that would be a reporting feature, not a chat extension.
