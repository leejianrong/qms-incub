# QMS Incub: Slices

Vertical increments. Each ends in something you can demonstrate. Slice 1
confronts the riskiest unknown: whether the RAG pipeline can meaningfully
ingest and answer from a document containing tables and flowcharts — the
premise the whole "synthetic PDFs test RAG ingestion" idea rests on.

## V1: RAG Spike — Generate, Ingest, Ask

**Delivers:** R4 (partial — one hardcoded document, not the composer), R6
(partial — policy documents only), R7 (partial — corpus grounding only, no
per-user state yet)

**Build plan**

1. Minimal block model: `text`, `table`, `flowchart` block types; seed one
   policy document combining all three, with a fact (e.g. an approving
   authority's name) placed inside the table.
2. HTML-to-PDF export of that document (engine per Q35, not yet
   confirmed); the flowchart block renders via a Mermaid-style DSL to SVG,
   embedded before export (ADR-0006).
3. Ingestion pipeline: Docling parses the document, LlamaIndex chunks and
   embeds it, stored in Qdrant with source-type/doc-id metadata (ADR-0003,
   ADR-0009).
4. Chat endpoint (FastAPI): given a question, retrieve top-k chunks via
   LlamaIndex's Qdrant query engine, call the OpenRouter LLM with the
   retrieved context, return an answer + citation.
5. Minimal chat UI (Svelte): single input box, answer, citation — no auth
   or wizard yet.

**Demo:** Ask the chatbot "who is the approving authority for this
policy?" and see a correct answer citing the seeded document, where the
answer's fact lives inside a table cell.

**Rests on assumptions:** Q7 (flowcharts auto-render via a structured DSL)
— if wrong, this slice's PDF-generation step needs a different rendering
approach. Q35 (PDF engine, unconfirmed) — this slice can't finish until
that's picked.

### Test plan

#### End-to-end

- Seeded document with a fact inside a table → asking "who is the
  approving authority?" returns an answer containing the correct name and
  a citation to that document.

#### Integration

- Publishing a document triggers ingestion and produces at least one chunk
  row referencing that document's ID.
- Exporting a document with one table block and one flowchart block
  produces a PDF whose extracted text includes both blocks' content.

#### Unit

- Flowchart-DSL-to-Mermaid render function returns valid SVG for a 3-step
  process definition.
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

## V4: Policy Document Composer

**Delivers:** R4 (partial — generation path only; import path closes it in V7)

**Build plan**

1. Block-based document editor UI: add/reorder text, table, flowchart, and
   image blocks (ADR-0001).
2. Flowchart block editor: structured step-list input with a live Mermaid
   preview (ADR-0006), not a drawing canvas.
3. Draft → Published lifecycle, no approval step (ADR-0002).
4. Publish triggers V1's ingestion pipeline.
5. PDF export button reusing V1's export mechanism.

**Demo:** Author a new 3-block document in the composer, publish it, then
ask the chatbot a question only answerable from that new document.

**Rests on assumptions:** none new — this generalizes V1's hardcoded
document into the real authoring surface.

### Test plan

#### End-to-end

- Authoring and publishing a document, then asking the chatbot a fact only
  present in it, returns a grounded, correctly-cited answer.

#### Integration

- Publishing a document from the composer produces the same ingestion
  result shape as V1's seeded document.

#### Unit

- Block reordering preserves block content and bumps the document version.

## V5: Synthetic Batch Generation

**Delivers:** R5, R6 (breadth)

**Build plan**

1. "Generate N variants" panel: pick block templates, a count N, and a
   complexity range (table row count, flowchart step count) (ADR-0001).
2. Batch job produces N `PolicyDocument` rows with randomized block
   composition, flagged `is_synthetic = true`, auto-published.
3. Ingestion status dashboard: per-document status (chunked, embedded,
   failed) so a QA-author can see if any synthetic document broke the
   pipeline.

**Demo:** Generate 20 synthetic variants with tables/flowcharts, watch the
ingestion dashboard confirm 20/20 processed (or flag the ones that
didn't).

**Rests on assumptions:** Q7 carried forward — batch generation needs the
same programmatic block model V1/V4 already assume.

### Test plan

#### End-to-end

- Triggering a 20-document batch generation shows the ingestion dashboard
  at 20/20 processed with no unexplained failures.

#### Integration

- A generated synthetic document with a randomly-sized table still
  produces at least one chunk covering that table's content.

#### Unit

- Random block-composition generator respects the requested complexity
  range.

## V6: Blog + FAQ

**Delivers:** R8, R6 (breadth)

**Build plan**

1. Blog post list + detail view, admin-authored (plain text editor — no
   block/table/flowchart composer needed here).
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

## V7: Import Existing QMS Documents

**Delivers:** R4 (closes), R6 (breadth)

**Build plan**

1. "Import document" flow alongside the composer: upload a PDF, provide a
   `source_attribution` (URL or license note) (ADR-0007).
2. Store as a `PolicyDocument` with `origin = imported`, no blocks, PDF
   stored as-is (no HTML render step, unlike generated documents).
3. Publish triggers V1's ingestion pipeline directly on the uploaded PDF's
   extracted text.
4. Document-list toolbar toggle: Generate vs. Import, both landing in the
   same list built in V4.

**Demo:** Upload a real open-source QMS PDF, publish it, and ask the
chatbot a question answerable only from that imported document, alongside
one answerable from a generated document — both cited correctly.

**Rests on assumptions:** the open risk noted in PLAN.md — imported PDFs
are structurally unpredictable, so ingestion quality may vary more than it
does for the app's own generated documents.

### Test plan

#### End-to-end

- Uploading and publishing a real QMS PDF, then asking the chatbot a
  question answerable only from it, returns a correctly-cited answer.

#### Integration

- Publishing an imported document triggers ingestion on its extracted PDF
  text and produces chunks tagged `origin = imported`.

#### Unit

- Attribution field is required before an imported document can be
  published.

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
