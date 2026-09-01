# ADR-0012: The backend only ingests and answers — no document authoring, generated or synthetic, lives here

- Status: Accepted
- Date: 2026-09-01
- Deciders: leejianrong (user), agent (post-hoc correction)

## Context

ADR-0001 built one block-based engine to serve two jobs at once: a
QA-author composing real policy documents by hand, and a synthetic batch
generator producing test PDFs for the RAG pipeline. Sharing that engine
looked like the right call at the time — synthetic documents would stay
structurally honest to real ones, and there'd be only one render/export
path to maintain. ADR-0006, ADR-0007, and ADR-0010 all built on top of
that same premise: a flowchart DSL, a generate/import toggle, a WeasyPrint
export step.

The premise itself was wrong. The user corrected it directly: this
product's job is to ingest whatever documents it's given and answer
questions about them — nothing about *producing* those documents, real or
synthetic, belongs in this backend at all. A QA-author doesn't compose a
policy in the app; they upload one, the same way they'd upload a scanned
paper form. And proving the RAG pipeline works on realistic content is a
job for a tool that lives entirely outside this product, not a mode of
the app itself.

## Decision

The backend exposes exactly three document-related surfaces:
`POST /documents` (upload a PDF, ingest it immediately), `GET /documents`
(ingestion status), and `POST /chat` (query the corpus). That's the whole
document story. No block model, no HTML template, no PDF export, no
flowchart renderer, no Draft/Published lifecycle, no generated-vs-imported
distinction — every document the backend knows about arrived the same
way, through upload.

Synthetic document generation moves to `synthetic-corpus/`, a fully
independent tool in its own top-level folder. It shares no code with
`backend/` — it doesn't import `qms_incub`, and it doesn't call the
backend over HTTP either. Its only job is producing PDF files on a local
disk. Testing those PDFs against the backend's RAG pipeline is a manual
step someone does afterward, using the same upload endpoint a real user
would.

This supersedes ADR-0001, ADR-0006, ADR-0007, and ADR-0010 — each was a
decision about how the (now nonexistent) document engine should work.
ADR-0011 gets narrowed rather than reversed: it already said synthetic
generation shouldn't be a web feature; this decision goes the rest of the
way and removes it from the repo's shared code entirely.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Keep the composer for real QA-authored documents only, drop just the synthetic-generation half | No stated product need was ever separate from "upload an existing document" — nothing in this milestone asks a QA-author to compose from scratch inside the app, so the composer had no remaining job to justify its own data model, UI, and render pipeline |
| Synthetic tool calls the backend's upload endpoint directly, as an HTTP client | Rejected per explicit user direction — the two are meant to be completely separate products with zero coupling, not client and server |
| Keep the block model in the backend as a reusable library, even with no in-app UI for it | Dead code with no consumer; if a future authoring feature is ever built, it'll be designed against whatever's actually needed then, not resurrected from an engine built for a different job |

## Consequences

Gains: a much smaller backend — no WeasyPrint, no Jinja2, no block model,
no flowchart SVG renderer; roughly 800 lines removed across `documents/`,
`batch_v5.py`, `seed_v1.py`, and their tests. The generated/imported/synthetic
distinction disappears from `PolicyDocumentRow` entirely, since every
document is just "uploaded." `POST /documents` is a real product surface
now instead of being simulated by CLI scripts calling `ingest_pdf`
directly.

Costs: there's no in-app way for a QA-author to compose a document from
nothing — if that's ever wanted, it's new work, designed fresh, not a
restart of ADR-0001's engine. `source_attribution` (ADR-0007) is gone with
no replacement; provenance tracking on an upload would be a new decision
if it's ever needed.

Forecloses: nothing structural for ingestion or chat — `POST /chat`,
Docling parsing, and the Qdrant/LlamaIndex pipeline are untouched by this
decision.
