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

Separately, whoever builds this system's RAG-backed chatbot needs a way to
prove that ingestion and retrieval actually work — table and flowchart
content is exactly what tends to break naive RAG chunking — before
trusting the pipeline with real policy content. That proof comes from a
tool outside this product entirely (see below), not from anything the QMS
app itself builds.

## Solution

A web app where a PM runs a short classification wizard for their software
project, gets an auto-generated todo list of the QMS practices they must
follow, and uploads their own artifacts as proof of compliance against each
item. A persistent chatbot (OpenRouter-backed LLM) answers questions
grounded in the company's policy corpus *and* the asking PM's own
compliance state — "who is the approving authority for X" as much as "am I
compliant yet". The policy corpus itself grows by one mechanism only: a
QA-author uploads a PDF. The app never authors, composes, or generates
document content of any kind (ADR-0012) — it ingests whatever it's handed
and answers questions about it. Blog posts and FAQ entries are
lighter-weight content feeding the same knowledge base as the chatbot.

Real company QMS documents are sensitive and unavailable during this
build, so a separate local tool (`synthetic-corpus/`, its own product, no
shared code with this backend) generates realistic QMS-policy-shaped PDFs
for exercising the pipeline by hand before real content is ever uploaded.
See `docs/shaping/synthetic-doc-realism/` for that tool's own planning —
it isn't part of this plan.

The console's look and workflow follow a UI/UX engineer's design mock at
`ui-reference/QMS Console.dc.html` (a static reference, not shipped code).
Where that mock implied scope beyond what's decided here — a full
multi-role approval workflow, an AI-authored blog post, a hardcoded
regulatory-schema-shaped plan tree — those were resolved against the
existing ADRs rather than adopted wholesale; see Q40–Q44.

## Users and actors

- **Project Manager (PM)** — primary. Runs the wizard, works the todo list,
  uploads compliance artifacts, asks the chatbot.
- **QA-author** — secondary. Uploads policy documents and authors blog
  posts and FAQ entries.
- **RAG ingestion pipeline** — non-human actor, runs on every upload.
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
- Document upload: a QA-author uploads a PDF, which is the only way a
  policy document enters the corpus (ADR-0012).
- Project intake document ("AOR") upload: parsed and LLM-extracted into a
  fixed set of structured fields that inform the wizard — extraction of an
  uploaded document's own content, not corpus ingestion and not authoring
  (Q40).
- Todos grouped for navigation under a small, fixed set of process-phase
  steps (Q41) — a display grouping, not a change to how todos are
  generated or to `Requirement`'s user-authored hierarchy (ADR-0008).
- Approval-state fields on a todo (state/authority/SLA), set by the PM's
  own self-attestation action — schema only, no reviewer role or gate
  (Q42).
- AOR route classification: an uploaded AOR is classified as R&T or SSD
  by semantic similarity against two labeled reference descriptions,
  independent of the Project/wizard flow — a standalone check, not part
  of project intake (Q51).
- RAG ingestion pipeline for uploaded policy documents, blog posts, and
  FAQ entries.
- RAG chatbot (OpenRouter): grounded answers from the ingested corpus plus
  the asking PM's own project/todo/artifact state, with citations.
- Blog section and FAQ section, admin-authored.

**Out.**

- QA-reviewer approval gate on submitted artifacts. Confirmed as a wanted
  next-iteration feature (not cut, deferred) — F7 in QUESTIONS.md. The
  data model gains approval-state fields this milestone (Q42), but no
  second role or real gate does.
- Any content the backend authors, drafts, or generates on its own,
  including an AI-drafted blog post — the backend ingests and answers
  questions, it doesn't write (ADR-0012, Q43). A completed project's
  history is available as a chat answer (V8), never as a publishable
  artifact.
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
- Any form of in-app document authoring or composition — text editors,
  block composers, diagram tools, PDF export. The app ingests documents;
  it doesn't make them (ADR-0012). A QA-author who wants a new policy
  document in the corpus writes or sources the PDF elsewhere and uploads
  it.
- Mapping policy content to a real external regulatory standard (ISO,
  FDA, etc.). Policy content is the company's own generic text.

## Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | A PM can classify their project, get a compliance todo list, act on it, and ask a chatbot about the process and their own status | Core goal |
| R1 | Wizard classifies a project into a risk tier from a small fixed question set | Must-have |
| R2 | Todo list is auto-generated from the risk tier | Must-have |
| R3 | PM can upload an artifact against a todo item; it self-attests to Complied | Must-have |
| R4 | QA-author uploads a PDF, which is ingested and added to the corpus — the only way a policy document enters the system (ADR-0012) | Must-have |
| R5 | *(retired — see ADR-0012)* Synthetic batch generation now lives entirely outside this product, as its own tool (`synthetic-corpus/`) | — |
| R6 | Uploaded policy documents, blog posts, and FAQ entries are ingested automatically | Must-have |
| R7 | Chatbot answers grounded questions using the corpus plus the asking PM's own compliance state, with citations | Must-have |
| R8 | Blog and FAQ sections exist as simple admin-authored content | Must-have |
| R9 | A project's intake document is parsed and its declared attributes extracted to inform classification (Q40) | Must-have |
| R10 | Todos are grouped for navigation under a small, fixed set of process-phase steps (Q41) | Must-have |
| R11 | A todo surfaces an approval-route status (state/authority/SLA), even though only self-attestation gates completion this milestone (Q42) | Must-have |
| R12 | An uploaded AOR can be classified as R&T or SSD, standalone from project intake (Q51) | Must-have |

## Shape

| Part | Mechanism | ADR |
|------|-----------|-----|
| S1 | Classification wizard: fixed question set → deterministic scoring function → risk tier | |
| S2 | Todo generation: risk tier → matching `Requirement` rows (under user-defined Standard → Clause) → TodoItem rows on the Project, each linked back to its Requirement | ADR-0008 |
| S3 | Artifact compliance: upload → Artifact record linked to TodoItem → status flips to Complied (self-attestation, no gate) | ADR-0002 |
| S4 | Document upload: QA-author uploads a PDF → stored as a `PolicyDocumentRow`, status `pending` → S6 ingests its extracted text directly. The only way a document enters the corpus (ADR-0012, folds in what was S7) | ADR-0012 |
| S5 | *(retired — see ADR-0012)* | |
| S6 | RAG ingestion: on upload (policy doc, blog post, or FAQ entry) → chunk → embed → store with source-type + doc-id metadata | ADR-0003 |
| S7 | *(retired — merged into S4, see ADR-0012)* | |
| S8 | RAG chatbot: query → vector retrieval (top-k) + structured injection of the asking PM's project/todo/artifact state → OpenRouter LLM prompt → grounded answer with citations | ADR-0003 |
| S9 | Blog/FAQ CMS: simple admin-authored content list; publish triggers S6 | |
| S10 | AOR intake: project-scoped upload → Docling parse → LLM structured-field extraction → stored on the `Project`, never enters the corpus | ADR-0012 |
| S11 | Process-step grouping: fixed, config-seeded `ProcessStep` rows; todo generation (S2) assigns each `TodoItem` a step | ADR-0008 |
| S12 | Approval-state fields: `TodoItem` carries state/authority/SLA, set by S3's self-attestation action, no reviewer role | ADR-0002 |
| S13 | AOR route classification: extracted AOR text → embedded with the RAG pipeline's own model → cosine similarity against two labeled reference descriptions (R&T, SSD) → route + confidence + `needs_review` flag. No Project/wizard linkage, no corpus write | ADR-0012 |

## Affordances

**UI.**

| Affordance | Place | Wires to |
|------------|-------|----------|
| Standard / Clause / Requirement editor | QA-author tools | S2 (ADR-0008) |
| AOR upload + extracted-fields panel | New project flow, wizard step 1 | S10 |
| Classification wizard (multi-step form) | New project flow | S1, S2 |
| QMS plan navigator (steps → todos) | Project detail | S11 |
| Todo list + compliance % | PM dashboard | S2, S3 |
| Artifact upload control | Todo item row | S3 |
| Approval-route card | Todo detail | S12 |
| Upload document | QA-author tools | S4 |
| Blog list + post view | Blog section | S9 |
| FAQ list | FAQ section | S9 |
| Chat panel with citations | Persistent panel on PM dashboard | S8 |

**Non-UI.**

| Affordance | Kind | Wires to |
|------------|------|----------|
| Ingestion worker | runs synchronously on upload | S6 |
| Vector store (Qdrant) | store | S6, S8 |
| Docling parser | service (invoked by LlamaIndex ingestion) | S4, S6 |
| LlamaIndex ingestion/query pipeline | library, orchestrates S6/S8 | S6, S8 |
| OpenRouter API client | handler | S8 |
| `make up` / `make seed` (Makefile) | one-command local bring-up; `make seed` uploads a fixture PDF through the real endpoint | all — ADR-0005 |
| `POST /aor/classify` + `scripts/classify_aor.py` | endpoint and CLI, both call the same classifier | S13 |

## Implementation decisions

- Stack: Python/FastAPI backend, Svelte+Vite frontend, PostgreSQL,
  Qdrant vector store, LlamaIndex + Docling for the RAG pipeline
  (ADR-0009, supersedes ADR-0005's original stack defaults). No PDF
  rendering engine in the backend at all — there's nothing left to render
  (ADR-0012 supersedes ADR-0010). Frontend components come from
  shadcn-svelte, copied into the repo and themed to match `ui-reference/`
  (ADR-0013).
- Core entities: `ComplianceStandard` (name, description), `Clause` (belongs
  to a Standard, ordering, text), `Requirement` (belongs to a Clause,
  description, applicable risk tiers) — user-authored, no hardcoded
  regulatory schema (ADR-0008). `Project` (owner=PM, risk tier), `ProcessStep`
  (fixed, config-seeded phase — a display grouping, not user-authored;
  Q41), `TodoItem` (project, the `Requirement` it traces to, its
  `ProcessStep`, status, and approval-state fields — `approval_state`/
  `approval_authority`/`sla_target`/`decided_at`, set by self-attestation
  alone this milestone; Q42), `Artifact` (todo item,
  file, uploader), `PolicyDocument` (id, title, ingestion status
  pending/embedded/failed, chunk count, error) — a record of an uploaded
  file's progress through ingestion, not document content; the app stores
  no document content or structure of its own, only what Docling/LlamaIndex
  derive from the PDF at ingestion time. `BlogPost`, `FAQEntry`,
  `IngestedChunk` (source type, source id, embedding, text). All carry an
  org-scoping column per ADR-0004 even though v1 is single-org.
- Todo generation (S2) walks `Requirement`s tagged with the project's risk
  tier and creates one `TodoItem` per match, each pointing back at its
  `Requirement` — the traceability chain is Standard → Clause →
  Requirement → TodoItem → Artifact, not a flat practice string
  (ADR-0008).
- Uploaded documents are stored as-is; there's no authoring step to skip
  (ADR-0012) — the PDF's extracted text goes straight into S6's ingestion
  pipeline the moment it's uploaded.
- OpenRouter is a hosted, internet-dependent LLM gateway (Terms of Service
  apply per-model; no self-hosted fallback in v1). If it's unreachable, the
  chat panel shows an explicit error state rather than failing silently or
  retrying indefinitely (per the failure-behaviour default, Q26).
- `PolicyDocument` has no Draft/Published lifecycle at all (a simpler
  outcome than ADR-0002's original "no approval state" call, once there's
  no authoring step before ingestion) — an upload is ingested immediately,
  status tracks pipeline progress (`pending`/`embedded`/`failed`), not
  editorial review.
- Chat context assembly (S8) builds two distinct sections in the LLM prompt:
  retrieved corpus chunks, and a fixed-shape JSON block of the asking PM's
  own `Project`/`TodoItem`/`Artifact` rows — kept separate so citations can
  point at "policy corpus" vs. "your current status" distinctly.
- Classification wizard uses three fixed dimensions — data sensitivity,
  customer-facing vs. internal, regulatory exposure — mapped to Low/Medium/
  High. This is a content default (Q8), not architecture; changing the
  dimensions later only touches the mapping config, not the mechanism.

## Testing approach

Highest-value seams: the wizard-to-todo mapping (pure function), ingestion
(does an uploaded document produce chunks that actually cover its table
and flowchart content, not just its prose), and chatbot grounding (does a
question with a known answer in the corpus get answered correctly, with
the right citation). The chatbot's exact wording is never asserted — only
that the expected fact appears and the citation points at the right
source. Per-slice test plans live in SLICES.md.

## Assumed defaults

| ID | Assumed | Cost if wrong |
|----|---------|---------------|
| Q9 | Chatbot is retrieval-QA only, no agentic actions on the wizard/todos | Low — extending to agentic actions adds tool-calling to S8 without changing S1–S6 |
| Q11 | *(superseded — see ADR-0009)* | |
| Q7, Q35 | *(superseded — see ADR-0012; there's no flowchart rendering or PDF export left in the backend to have an engine for)* | |
| Q15 | Chatbot grounding is hybrid: vector retrieval over the corpus plus direct structured injection of the asking user's own state (not vectorized) | Medium — if user state needs to be searchable/cross-referenced at scale later, S8's context assembly is rebuilt but S6 (ingestion) is unaffected |

## Open risks

- **LLM grounding quality.** OpenRouter-backed chat could still hallucinate
  despite retrieval. Slice 1 (the RAG spike) is the earliest point this
  shows up.
- **Uploaded PDFs are structurally unpredictable.** Real-world QMS
  documents vary wildly in layout, and Docling's text extraction may
  produce messier chunks for some documents than others — this is true
  from the very first upload, not a risk that shows up later. The
  `synthetic-corpus/` tool exists precisely to probe this by hand before
  real content is ever uploaded.
- **Self-attestation may read as too weak for a QMS demo.** No reviewer
  contests a PM's claim of compliance in this milestone — explicitly
  deferred (F7), earliest visible in Slice 3.
