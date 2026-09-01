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

## V9: AOR Intake & Structured Extraction

A UI/UX engineer's design mock (`ui-reference/QMS Console.dc.html`) shows
a project-creation wizard that opens with an "AOR" (Approval of
Requirement) document upload, then shows fields the system claims to have
"read from the pack." This slice is the real version of that: a new,
project-scoped upload path distinct from V4's QA-author corpus upload,
whose only job is answering "what does this project's own intake document
say" — not adding anything to the RAG corpus.

**Delivers:** new — not in PLAN.md's original R-list; a Q40 addition

**Build plan**

1. `POST /projects/{id}/aor`: multipart upload (PDF/DOCX/XLSX), stores the
   file against the `Project`, distinct from `PolicyDocumentRow` (V4) —
   this document never enters the Qdrant corpus.
2. Docling parses the upload; an LLM call (same OpenRouter client as S8)
   extracts a fixed, small set of structured fields (criticality tier,
   data classification, external dependencies, in-house rationale) into a
   JSON column on the project's intake record. Extraction only — no new
   content is authored, per ADR-0012 (Q40).
3. Wizard UI: drag-drop/click uploader, then a read-only "read from the
   pack" panel showing the extracted fields before the 3 classification
   questions (V2).

**Demo:** Upload a real intake document with a stated criticality tier and
external dependency, see both values appear correctly in the "read from
the pack" panel before answering the wizard's questions.

**Rests on assumptions:** Q40 (extraction, not authoring, stays inside
ADR-0012) — if extraction quality is too unreliable to trust unattended,
the fields become PM-editable suggestions rather than authoritative
inputs, which doesn't change the mechanism, only whether its output is
locked.

### Test plan

#### End-to-end

- Uploading an intake document with known values for all four fields
  produces an extraction result matching each value, shown in the wizard
  before the classification questions.

#### Integration

- `POST /projects/{id}/aor` stores the file, runs extraction, and persists
  the structured result on the project's intake record in one request; the
  document does not appear in `GET /documents` or the Qdrant corpus.

#### Unit

- Extraction-prompt assembly, given fixed Docling output, requests exactly
  the four defined fields and rejects a response missing one.

## V10: QMS Plan Navigator (Process-Step Grouping)

V2's dashboard is a flat todo list. The design mock groups todos into a
small set of fixed process phases (Initiation/Design/Build/Test/Deploy/
Closure or similar) shown as a collapsible step/sub-step navigator. This
slice adds that grouping without touching how todos are generated.

**Delivers:** new — not in PLAN.md's original R-list; a Q41 addition

**Build plan**

1. `ProcessStep` table: fixed, config-seeded rows (id, title, ordering) —
   not user-authored, not a regulatory concept (Q41). Seeded once, same
   for every org.
2. `TodoItem` gains a `process_step_id`, assigned at generation time (S2)
   by a fixed mapping from `Requirement` to phase.
3. Project detail UI: two-pane layout — a collapsible left-hand navigator
   (steps → their todos, done/total + progress bar per step) and a right-
   hand panel for the selected todo.

**Demo:** Complete the wizard, land on the project detail view, see the
generated todos grouped correctly under their process steps with an
accurate per-step done-count, collapse the navigator to its icon rail and
back.

**Rests on assumptions:** Q41 (fixed `ProcessStep` grouping doesn't reopen
ADR-0008) — if a future need arises for org-specific phase sets, that's a
new decision, not a resurrection of a hardcoded regulatory schema.

### Test plan

#### End-to-end

- Completing the wizard shows every generated todo under its correct
  process step, with each step's done-count and progress bar matching the
  underlying `TodoItem` statuses.

#### Integration

- Todo generation (S2) assigns a `process_step_id` to every created
  `TodoItem` in the same transaction that creates it.

#### Unit

- Requirement-to-`ProcessStep` mapping returns the expected step for each
  seeded `Requirement`.

## V11: Approval-State Schema

The design mock shows a full PM → QA Office → Authority approval route per
todo (submitted/approved/returned, SLA, "chase the approver"). ADR-0002
decided self-attestation only, with a reviewer gate deferred as a named
future feature. This slice adds the schema so the UI can render that
route now, without building the second role or the gate itself (Q42).

**Delivers:** new — extends R3/V3; a Q42 addition

**Build plan**

1. `TodoItem` gains `approval_state` (`not_required`/`not_started`/
   `submitted`/`approved`/`returned`), `approval_authority` (free text),
   `sla_target`, `decided_at`.
2. Self-attestation (V3) sets `approval_state` to `submitted` then
   `approved` in the same action, still driven entirely by the PM's own
   upload — no second user, no gate.
3. Todo detail UI: an approval-route card (3-node flow, current state
   highlighted, authority + SLA shown) sourced from these fields.

**Demo:** Upload an artifact against a todo requiring approval, see it
move through `submitted` → `approved` in the UI's approval-route card,
authority and SLA text populated from seed data — all driven by the same
single self-attesting action.

**Rests on assumptions:** Q42 (schema-only, additive to ADR-0002, not a
reversal) — if a real reviewer role and gate get built later, this slice's
fields are exactly what that work extends, not fields to migrate away
from.

### Test plan

#### End-to-end

- Self-attesting a todo with `approval_state != not_required` shows the
  approval-route card transition to `approved` with the correct authority
  and SLA text.

#### Integration

- Self-attestation (V3's upload handler) sets `approval_state` and
  `decided_at` in the same transaction as the `Artifact` row and the
  `Complied` status flip.

#### Unit

- Approval-route card view-model, given each `approval_state` value,
  renders the correct node highlighted and correct status text.

## V12: Frontend Design System — shadcn-svelte Adoption

Infrastructure slice: before V10/V11/V13's screens can be built, the
frontend needs the component primitives and design tokens the
`ui-reference/` mock uses (ADR-0013). No new product behavior — this
slice ends in a component showcase, not a user-facing feature.

**Delivers:** none (R-list) — enabling work for V9–V11's UI and V13

**Build plan**

1. Add Tailwind CSS + its Vite plugin, and shadcn-svelte's CLI, to
   `frontend/` (ADR-0013).
2. Port `ui-reference/`'s design tokens (accent color, radius, shadow,
   typography) into Tailwind theme config / CSS custom properties.
3. Pull in the shadcn-svelte components the mock actually uses: button,
   input, select, card, dialog, dropdown-menu, tabs/stepper primitives,
   badge/tag.
4. A local-only component showcase route (not shipped) exercising each
   component against the ported tokens, for visual comparison against the
   mock.

**Demo:** Open the showcase route side-by-side with `ui-reference/QMS
Console.dc.html` and confirm button, input, card, and tag styling matches
(accent color, radius, shadow) at a glance.

**Rests on assumptions:** none — ADR-0013 already settled the library
choice.

### Test plan

#### Integration

- `npm run build` succeeds with Tailwind + shadcn-svelte wired in, and the
  showcase route renders every adopted component without a console error.

#### Unit

- Design-token values (accent color, radius) match `ui-reference/`'s
  `:root` custom properties exactly, asserted from the ported Tailwind
  config.

## V13: Frontend — Console UI (Dashboard, Wizard, Plan Navigator)

Wires V12's components to the backend surfaces from V2/V3/V9/V10/V11,
replacing the frontend's current chat-panel-only state (CLAUDE.md build
status) with the console experience `ui-reference/` depicts — scoped to
the core workflow only. Blog/FAQ (V6), notifications, favourites, mentions,
the floating AI assistant, and the per-todo "contact the owner" chat are
explicitly out of this slice, to be planned separately once this core
lands.

**Delivers:** frontend surface for R1, R2, R3 plus V9/V10/V11's new backend
work

**Build plan**

1. Project dashboard: list + status (no notifications/favourites/mentions
   panels).
2. Create-project wizard: step 1 (details + AOR upload, V9), step 2 (3
   classification questions, V2), step 3 (generated todo/plan preview).
3. Project detail: progress header, V10's collapsible plan navigator.
4. Todo detail panel: gist, artifact upload (V3), V11's approval-route
   card, comment thread.
5. Chat panel (V8) surfaced on the project detail view, project-aware.

**Demo:** Create a project end to end through the real UI — upload an AOR,
answer the 3 questions, land on a generated plan grouped by process step,
self-attest one todo requiring approval and watch its approval-route card
update — with no step of this flow touching a script or a fixture.

**Rests on assumptions:** none new — this is the UI for mechanisms V2,
V3, V9, V10, and V11 already define; a change to any of those changes this
slice's screens, not its own logic.

### Test plan

#### End-to-end

- The full create-project → wizard → generated plan → self-attest flow,
  driven through the UI, produces the same state V2/V3/V9/V10/V11's own
  end-to-end tests assert for their backend surfaces.

#### Integration

- Each screen's data-fetching wires to the correct endpoint and renders a
  loading/error state when that endpoint fails.

#### Unit

- Wizard step-validation (can't advance without a name, date, AOR, and all
  3 answers) matches V2/V9's stated preconditions.
