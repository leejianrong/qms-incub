# QMS Incub: Slices

Vertical increments. Each ends in something you can demonstrate. Slice 1
confronts the riskiest unknown: whether the RAG pipeline can meaningfully
ingest and answer from a document containing structured content like
tables, given that the backend only ever sees a PDF someone handed it
(ADR-0012) — it never gets to control how that PDF was made. Table and
flowchart content is exactly what tends to break naive RAG chunking; the
`synthetic-corpus/` tool exists to probe that further with richer documents
than V1's one fixture.

## V1: RAG Spike — Upload, Ingest, Ask

**Delivers:** R4 (partial — a static fixture PDF, uploaded through the real
endpoint), R6 (partial — policy documents only), R7 (partial — corpus
grounding only, no per-user state yet)

**Build plan**

1. A fixture PDF (`backend/tests/fixtures/sample_policy_document.pdf`) with
   prose and a table, with a fact (an approving authority's name) placed
   inside the table. Baked once outside the app — the backend doesn't
   render or compose this, it just receives it (ADR-0012).
2. `POST /documents`: accepts a PDF upload, stores it, and ingests it
   immediately.
3. Ingestion pipeline: Docling parses the document, LlamaIndex chunks and
   embeds it, stored in Qdrant with source-type/doc-id metadata (ADR-0003,
   ADR-0009).
4. Chat endpoint (FastAPI): given a question, retrieve top-k chunks via
   LlamaIndex's Qdrant query engine, call the OpenRouter LLM with the
   retrieved context, return an answer + citation.
5. Minimal chat UI (Svelte): single input box, answer, citation — no auth
   or wizard yet.

**Demo:** Upload the fixture PDF via `make seed`, then ask the chatbot "who
is the approving authority for this policy?" and see a correct answer
citing the uploaded document, where the answer's fact lives inside a table
cell.

**Rests on assumptions:** none — ADR-0012 already settled how a document
gets into the backend.

### Test plan

#### End-to-end

- Uploading the fixture document with a fact inside a table, then asking
  "who is the approving authority?", returns an answer containing the
  correct name and a citation to that document.

#### Integration

- Uploading a document through `POST /documents` triggers ingestion and
  produces at least one chunk row referencing that document's ID; `GET
  /documents` shows it as `embedded`.
- The fixture PDF's extracted text includes its table content, proving the
  ingestion pipeline can chunk more than plain prose.

#### Unit

- Chunking function splits document text into chunks under the target
  token size.

## V2: Compliance Requirements + Project Classification + Todo List

**Delivers:** R1, R2

**Build plan**

1. Standard / Clause / Requirement editor (QA-author): create a
   `ComplianceStandard`, add `Clause`s under it, add `Requirement`s under
   each clause, each tagged with the risk tier(s) it applies to (ADR-0008).
2. Wizard UI: 3-question form (data sensitivity / customer-facing /
   regulatory exposure).
3. Scoring function: answers → Low/Medium/High tier (pure function).
4. On wizard submit: create a `Project` row and generate one `TodoItem`
   per matching `Requirement` for that tier, each linked back to its
   `Requirement`.
5. PM dashboard: list todos, status `Pending`.

**Demo:** Seed a Standard with a handful of tiered Requirements, complete
the wizard with a high-risk answer set, land on a dashboard showing a todo
list matching exactly the High-tier Requirements — each todo traceable
back to its Requirement, Clause, and Standard.

**Rests on assumptions:** Q8 (fixed 3-dimension classification scheme) — if
wrong, only the wizard questions and Requirement tagging change, not the
mechanism.

### Test plan

#### End-to-end

- Completing the wizard with each of three representative answer sets
  shows the correct tier and the matching todo list, traceable back to the
  seeded Requirements, on the dashboard.

#### Integration

- Submitting the wizard persists a `Project` row and one `TodoItem` per
  matching `Requirement` in one transaction.

#### Unit

- Scoring function maps each of the 8 answer combinations to the expected
  tier.
- Requirement-to-tier matching returns exactly the Requirements tagged for
  a given tier.

## V3: Artifact Upload + Self-Attestation

**Delivers:** R3

**Build plan**

1. Upload control on a todo item.
2. On upload: create an `Artifact` row linked to the `TodoItem`; flip its
   status to `Complied` (ADR-0002).
3. Dashboard shows compliance % (Complied / total todos).

**Demo:** Upload a file against a `Pending` todo, see it flip to
`Complied` and the dashboard's compliance % update.

**Rests on assumptions:** F7/ADR-0002 (self-attestation, no review gate) —
if this changes, the slice needs an added `Pending Review` state and a
reviewer surface, which is explicitly out of scope for this milestone.

### Test plan

#### End-to-end

- Uploading a file against a todo shows it as `Complied` and the
  compliance % increases by the expected amount.

#### Integration

- Uploading an artifact persists the file reference and updates
  `TodoItem` status in one transaction.

#### Unit

- Compliance % calculation given a set of todo statuses.

## V4: Document Upload

**Delivers:** R4 (closes)

**Build plan**

1. `POST /documents`: multipart PDF upload, generates a document ID,
   stores the file, and ingests it synchronously (ADR-0012). This is the
   real version of what V1's `make seed` already exercises against a
   fixture.
2. `PolicyDocumentRow` (Postgres, Alembic-managed — the first slice to
   touch the relational data model) tracks status (`pending`/`embedded`/
   `failed`), chunk count, and error per document.
3. `GET /documents`: lists every uploaded document's status.
4. Frontend: an upload control wired to `POST /documents`, replacing V1's
   fixture-only path with a real one a QA-author can use.

**Demo:** Upload a real QMS PDF through the UI, then ask the chatbot a
question only answerable from that new document.

**Rests on assumptions:** none new — this generalizes V1's fixture upload
into the real authoring surface a QA-author actually uses.

### Test plan

#### End-to-end

- Uploading a document through the UI, then asking the chatbot a fact only
  present in it, returns a grounded, correctly-cited answer.

#### Integration

- `POST /documents` produces the same ingestion result shape as V1's
  fixture upload; `GET /documents` reflects the new document's status.

#### Unit

- Upload handler rejects a non-PDF file with a clear error before any
  ingestion is attempted.

## V5: *(retired)*

Synthetic batch generation used to live here as local CLI tooling
(ADR-0011). It's been moved out of this product entirely — see ADR-0012.
It's now `synthetic-corpus/`, an independent tool with its own planning
docs under `docs/shaping/synthetic-doc-realism/`; it shares no code with
this backend and doesn't call it over HTTP. What it produces (PDF files on
disk) gets tested against this backend the same way any real document
would: by hand, through V4's upload endpoint.

## V6: Blog + FAQ

**Delivers:** R8, R6 (breadth)

**Build plan**

1. Blog post list + detail view, admin-authored (plain text editor).
2. FAQ list, admin-authored Q&A pairs.
3. Publish action for both triggers V1's ingestion pipeline, tagged
   `source_type = blog` / `faq`.

**Demo:** Publish an FAQ entry answering a process question, ask the
chatbot that exact question, see it answer using the FAQ entry as its
cited source.

**Rests on assumptions:** none new.

### Test plan

#### End-to-end

- Publishing an FAQ entry, then asking the chatbot the matching question,
  returns an answer citing that FAQ entry.

#### Integration

- Publishing a blog post or FAQ entry produces chunks tagged with the
  correct `source_type`.

#### Unit

- Blog/FAQ publish validation (required fields).

## V7: *(merged into V4)*

This slice used to add an "import a real PDF" path alongside a composer —
a "Generate / Import" toggle (ADR-0007). Once there's no composer left to
switch away from (ADR-0012), uploading a PDF *is* the only path; there's
nothing left here that V4 doesn't already cover.

## V8: Compliance-Aware Chat

**Delivers:** R0 (closes), R7 (closes)

**Build plan**

1. Extend V1's chat endpoint: inject the asking PM's `Project`/`TodoItem`/
   `Artifact` state as structured context alongside the vector-retrieved
   chunks (ADR-0003).
2. Prompt template keeps "policy knowledge" (retrieved chunks) and "your
   compliance state" (structured injection) in separate labeled sections
   so citations stay accurate.
3. Chat UI moves from V1's standalone page into a persistent panel on the
   PM dashboard.

**Demo:** On a dashboard with 2 of 5 todos `Complied`, ask "am I compliant
yet?" and get an answer naming the correct 2 completed and 3 outstanding
items — then ask a policy question in the same session and get a corpus-
grounded answer.

**Rests on assumptions:** Q15 (hybrid retrieval + structured injection) —
if user state instead needs to be searchable/cross-referenced at scale
(e.g. "which projects are non-compliant" reporting), that's a different,
unbuilt mechanism (ADR-0003's Consequences).

### Test plan

#### End-to-end

- With a known set of Complied/Pending todos, asking "am I compliant?"
  returns an answer whose named items match the actual todo statuses.

#### Integration

- The chat request handler assembles a prompt containing both retrieved
  chunks and the requesting user's current todo/artifact state.

#### Unit

- Prompt-assembly function, given a fixed retrieval result and fixed user
  state, produces the expected structured sections.
