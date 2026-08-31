# QMS Incub: Plan

Status: draft · Milestone: MVP

## Problem

Project managers at large companies must comply with the company's QMS
(quality management system) policies before and during a software project,
but there is no tool that tells a PM which policies apply to *their*
project, what they need to produce as proof, or whether they're actually
compliant so far. Policies live scattered across documents; a PM typically
doesn't know who the approving authority is for a given practice without
asking around.

Separately, whoever builds this system's RAG-backed chatbot needs a
realistic way to generate policy-shaped test documents — ones containing
tables and flowcharts, the content types that most often break naive RAG
chunking — to validate that ingestion and retrieval actually work before
trusting it with real policy content.

## Solution

A web app where a PM runs a short classification wizard for their software
project, gets an auto-generated todo list of the QMS practices they must
follow, and uploads their own artifacts as proof of compliance against each
item. A persistent chatbot (OpenRouter-backed LLM) answers questions
grounded in the company's policy corpus *and* the asking PM's own
compliance state — "who is the approving authority for X" as much as "am I
compliant yet". A QA-author role composes the canonical policy documents
(text, tables, flowcharts, images) through a block-based generator that
exports PDF, and the same generator can batch-produce synthetic variant
documents to stress-test the RAG ingestion pipeline. The same corpus can
also be grown by importing existing open-source QMS documents — real PDFs
sourced from elsewhere — so the QA-author can switch between generating
synthetic content and ingesting real-world documents as needed. Blog posts
and FAQ entries are lighter-weight content feeding the same knowledge base
as the chatbot.

## Users and actors

- **Project Manager (PM)** — primary. Runs the wizard, works the todo list,
  uploads compliance artifacts, asks the chatbot.
- **QA-author** — secondary. Authors policy documents, blog posts, and FAQ
  entries; triggers synthetic batch generation for RAG testing.
- **RAG ingestion pipeline** — non-human actor, runs on every publish.
- **OpenRouter LLM** — non-human actor, answers chat queries.
- No reviewer/approver actor exists yet (see Out). Where that would create a
  conflict — PM says compliant, nobody checks — the PM's self-attestation is
  authoritative for this milestone; see ADR-0002.

## Scope

**In this milestone.**

- Project classification wizard: a small fixed set of questions → a
  Low/Medium/High risk tier (Q8).
- Auto-generated compliance todo list from the risk tier, each item naming
  a required practice and, where applicable, a required artifact type.
- Artifact upload against a todo item; self-attestation flips the item to
  Complied.
- PM dashboard: todo list, compliance %, uploaded artifacts.
- Block-based policy document composer (text / table / flowchart / image
  blocks) for the QA-author role, with PDF export.
- Synthetic batch generation mode: produce N variant documents from the
  same composer for the RAG test corpus.
- Import existing open-source QMS documents (real PDFs) into the same
  corpus, with a switch between generating and importing (ADR-0007).
- RAG ingestion pipeline for published policy documents (generated or
  imported), blog posts, and FAQ entries.
- RAG chatbot (OpenRouter): grounded answers from the ingested corpus plus
  the asking PM's own project/todo/artifact state, with citations.
- Blog section and FAQ section, admin-authored.

**Out.**

- QA-reviewer approval gate on submitted artifacts. Confirmed as a wanted
  next-iteration feature (not cut, deferred) — F7 in QUESTIONS.md.
- Multi-tenant SaaS (multiple companies in one deployment). Single-org for
  this milestone; data model carries an org-scoping column so this isn't
  expensive to add later (ADR-0004).
- SSO / external identity provider integration.
- Any deployment target at all. This milestone runs locally only, brought
  up with a single `make up` (ADR-0005) for demoing from a laptop — no
  cloud hosting, no on-prem/air-gap story, no CI deploy gate.
- A general external REST API for third-party integration.
- RAG retrieval evaluation/benchmarking tooling (precision/recall metrics).
  This milestone needs ingestion and retrieval to *work and be demoable*,
  not to be rigorously tuned.
- A freeform diagram/canvas editor. Flowcharts are generated from
  structured step data, not hand-drawn (ADR-0006) — a reader might expect a
  drawing tool given "generate flowcharts", so this is called out
  explicitly.
- Mapping policy content to a real external regulatory standard (ISO,
  FDA, etc.). Policy content is the company's own generic text.

## Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | A PM can classify their project, get a compliance todo list, act on it, and ask a chatbot about the process and their own status | Core goal |
| R1 | Wizard classifies a project into a risk tier from a small fixed question set | Must-have |
| R2 | Todo list is auto-generated from the risk tier | Must-have |
| R3 | PM can upload an artifact against a todo item; it self-attests to Complied | Must-have |
| R4 | QA-author adds a policy document to the corpus either by composing it from text/table/flowchart/image blocks and exporting PDF, or by importing an existing open-source QMS PDF, switching between the two | Must-have |
| R5 | QA-author triggers synthetic batch generation of N variant documents for the RAG test corpus | Must-have |
| R6 | Published policy documents (generated or imported), blog posts, and FAQ entries are ingested automatically | Must-have |
| R7 | Chatbot answers grounded questions using the corpus plus the asking PM's own compliance state, with citations | Must-have |
| R8 | Blog and FAQ sections exist as simple admin-authored content | Must-have |

## Shape

| Part | Mechanism | ADR |
|------|-----------|-----|
| S1 | Classification wizard: fixed question set → deterministic scoring function → risk tier | |
| S2 | Todo generation: risk tier → matching `Requirement` rows (under user-defined Standard → Clause) → TodoItem rows on the Project, each linked back to its Requirement | ADR-0008 |
| S3 | Artifact compliance: upload → Artifact record linked to TodoItem → status flips to Complied (self-attestation, no gate) | ADR-0002 |
| S4 | Document generation engine: block model (text/table/flowchart/image) → HTML render → HTML-to-PDF export; flowchart blocks render via a structured DSL to SVG before export | ADR-0001, ADR-0006 |
| S5 | Synthetic batch mode: parametrized generator reuses S4's block engine to produce N randomized documents, flagged synthetic, auto-published | ADR-0001 |
| S6 | RAG ingestion: on publish (policy doc / blog post / FAQ entry, generated or imported) → chunk → embed → store with source-type + doc-id metadata | ADR-0003 |
| S7 | Document import: QA-author uploads an existing PDF + attribution → stored as a `PolicyDocument` with `origin = imported` (no blocks) → S6 ingests its extracted text directly | ADR-0007 |
| S8 | RAG chatbot: query → vector retrieval (top-k) + structured injection of the asking PM's project/todo/artifact state → OpenRouter LLM prompt → grounded answer with citations | ADR-0003 |
| S9 | Blog/FAQ CMS: simple admin-authored content list; publish triggers S6 | |

## Affordances

**UI.**

| Affordance | Place | Wires to |
|------------|-------|----------|
| Standard / Clause / Requirement editor | QA-author tools | S2 (ADR-0008) |
| Classification wizard (multi-step form) | New project flow | S1, S2 |
| Todo list + compliance % | PM dashboard | S2, S3 |
| Artifact upload control | Todo item row | S3 |
| Block-based document composer | QA-author document editor | S4 |
| PDF export button | Document composer | S4 |
| "Generate synthetic variants" panel | QA-author tools | S5 |
| Import document (upload PDF + attribution) | QA-author tools, same document list as composer | S7 |
| Generate / Import switch | Document list toolbar | S4, S7 |
| Ingestion status dashboard | QA-author tools | S6 |
| Blog list + post view | Blog section | S9 |
| FAQ list | FAQ section | S9 |
| Chat panel with citations | Persistent panel on PM dashboard | S8 |

**Non-UI.**

| Affordance | Kind | Wires to |
|------------|------|----------|
| Ingestion worker | job, runs on publish | S6 |
| Vector store (pgvector) | store | S6, S8 |
| OpenRouter API client | handler | S8 |
| HTML-to-PDF renderer | service | S4, S5 |
| `make up` / `make seed` (Makefile) | one-command local bring-up | all — ADR-0005 |

## Implementation decisions

- Core entities: `ComplianceStandard` (name, description), `Clause` (belongs
  to a Standard, ordering, text), `Requirement` (belongs to a Clause,
  description, applicable risk tiers) — user-authored, no hardcoded
  regulatory schema (ADR-0008). `Project` (owner=PM, risk tier), `TodoItem`
  (project, the `Requirement` it traces to, status), `Artifact` (todo item,
  file, uploader), `PolicyDocument` (id, version, status Draft/Published,
  `origin`: generated/imported, blocks[] — empty for imported,
  `is_synthetic`, `source_attribution` — set for imported), `Block` (type:
  text/table/flowchart/image, content), `BlogPost`, `FAQEntry`,
  `IngestedChunk` (source type, source id, embedding, text). All carry an
  org-scoping column per ADR-0004 even though v1 is single-org.
- Todo generation (S2) walks `Requirement`s tagged with the project's risk
  tier and creates one `TodoItem` per match, each pointing back at its
  `Requirement` — the traceability chain is Standard → Clause →
  Requirement → TodoItem → Artifact, not a flat practice string
  (ADR-0008).
- Imported documents skip the block model and HTML render entirely (ADR-0007):
  the uploaded PDF is stored as-is and its extracted text goes straight into
  S6's ingestion pipeline.
- OpenRouter is a hosted, internet-dependent LLM gateway (Terms of Service
  apply per-model; no self-hosted fallback in v1). If it's unreachable, the
  chat panel shows an explicit error state rather than failing silently or
  retrying indefinitely (per the failure-behaviour default, Q26).
- `PolicyDocument` lifecycle is Draft → Published only (no approval state) —
  simpler than a four-state document lifecycle because there is no reviewer
  actor in this milestone; see ADR-0002.
- Chat context assembly (S8) builds two distinct sections in the LLM prompt:
  retrieved corpus chunks, and a fixed-shape JSON block of the asking PM's
  own `Project`/`TodoItem`/`Artifact` rows — kept separate so citations can
  point at "policy corpus" vs. "your current status" distinctly.
- Classification wizard uses three fixed dimensions — data sensitivity,
  customer-facing vs. internal, regulatory exposure — mapped to Low/Medium/
  High. This is a content default (Q8), not architecture; changing the
  dimensions later only touches the mapping config, not the mechanism.

## Testing approach

Highest-value seams: the wizard-to-todo mapping (pure function), document
generation → PDF (does the exported PDF actually contain the table and
flowchart content), ingestion (does a published document produce chunks),
and chatbot grounding (does a question with a known answer in the corpus
get answered correctly, with the right citation). The chatbot's exact
wording is never asserted — only that the expected fact appears and the
citation points at the right source. Per-slice test plans live in
SLICES.md.

## Assumed defaults

| ID | Assumed | Cost if wrong |
|----|---------|---------------|
| Q7 | Flowcharts are auto-composed from structured step data (Mermaid-style DSL), not hand-drawn | High if wrong — a freeform diagram editor is a different feature with different UI, data model, and PDF-rendering path |
| Q9 | Chatbot is retrieval-QA only, no agentic actions on the wizard/todos | Low — extending to agentic actions adds tool-calling to S8 without changing S1–S6 |
| Q11 | Stack: Next.js/React, Postgres+pgvector, Puppeteer for PDF, Mermaid for flowcharts | Medium — swapping the vector store or PDF engine touches S4–S8's implementations but not their shape |
| Q15 | Chatbot grounding is hybrid: vector retrieval over the corpus plus direct structured injection of the asking user's own state (not vectorized) | Medium — if user state needs to be searchable/cross-referenced at scale later, S8's context assembly is rebuilt but S6 (ingestion) is unaffected |

## Open risks

- **LLM grounding quality.** OpenRouter-backed chat could still hallucinate
  despite retrieval. Slice 1 (the RAG spike) is the earliest point this
  shows up.
- **PDF-to-ingestion fidelity for tables/flowcharts.** The whole synthetic-
  corpus premise assumes the ingestion pipeline can meaningfully chunk
  table and flowchart content, not just prose. Slice 1 confronts this
  directly.
- **Self-attestation may read as too weak for a QMS demo.** No reviewer
  contests a PM's claim of compliance in this milestone — explicitly
  deferred (F7), earliest visible in Slice 3.
- **Imported PDFs are structurally unpredictable.** Unlike generated
  documents, real-world QMS PDFs vary wildly in layout, and text extraction
  may produce messier chunks than the app's own generated HTML. Earliest
  visible in the import slice (V7).
