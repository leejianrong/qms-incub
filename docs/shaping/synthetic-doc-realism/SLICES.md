---
shaping: true
---

# Realistic Synthetic QMS Documents — Slices

See [SHAPING.md](./SHAPING.md) for requirements, shape decision (C: agent-
authored, zero network dependency, fully separate from the backend), and
components C0-C8.

## Slice 1: `synthetic-corpus/` skeleton — block model, renderers, PDF styling

**Covers:** C2 (block model + renderers, written from scratch), C3 (PDF
styling), C7 (repo layout)

The first slice of this tool's own code, independent of the backend
(which no longer has any document-composition engine to extend — see
`docs/adr/0012-*`). New top-level `synthetic-corpus/` directory: its own
dependency manifest (Jinja2, WeasyPrint), a small block model (text/table/
flowchart/swim-lane), an SVG renderer for flowchart and swim-lane diagrams
(lanes = columns), an HTML template, and WeasyPrint `@page` CSS — Times
New Roman, distinct H1/H2/H3 sizes, running header/footer with page
numbers via CSS Paged Media.

**Demo:** Render a small hand-written test document containing one
lane-free flowchart and one 3-lane swim-lane block to PDF; visually confirm
Times New Roman body text, distinct heading sizes, a running footer with
page numbers, and a swim-lane diagram with 3 labeled columns.

### Test plan

- Unit: lane-aware SVG layout places steps under the correct lane column
  header for a fixed 3-lane, 6-step input.
- Unit: lane-free flowchart input renders as a single top-to-bottom flow
  (no lane columns).
- Integration: exporting a document with headers/footers produces a
  multi-page PDF whose extracted text includes the running footer content
  on more than one page.

## Slice 2: CLI entry point

**Covers:** C6 (CLI), part of C4 (loading JSON fixtures — writing the real
fixtures is Slice 4)

A CLI (e.g. `synthetic-corpus/generate.py`) that loads block-model JSON
fixtures from `synthetic-corpus/documents/*.json`, renders them, and
writes PDFs to a gitignored `synthetic-corpus/output/` directory. Nothing
else — no ingestion, no network call, no dependency on the backend being
up or even installed.

**Demo:** With one placeholder JSON fixture committed, running the CLI
produces a matching PDF in `synthetic-corpus/output/`.

### Test plan

- Integration: loading a fixture JSON document round-trips through
  render → export and produces a valid, non-empty PDF file.
- Unit: a JSON fixture missing a required field fails loudly with a clear
  validation error, not a silent skip.

## Slice 3: Domain profile + corpus plan

**Covers:** C0 (domain profile), C1 (corpus plan)

Author `synthetic-corpus/domain-profile.json` (business function,
roles/titles, policy topics, standards bodies to reference) and
`corpus-plan.json` (10 doc IDs, titles, topics, and which other doc IDs
each one is planned to cross-reference) — the blueprint the full documents
get written from in Slice 4. No document prose yet.

**Demo:** `corpus-plan.json` lists exactly 10 entries with unique IDs; a
validation script confirms every planned cross-reference in the plan
points at another ID that actually exists in the same plan.

### Test plan

- Unit: corpus-plan validator catches a dangling cross-reference (an ID
  that doesn't exist in the plan) and a duplicate ID.

## Slice 4: Author the 10 golden documents

**Covers:** C1 (realized), C4 (JSON fixtures committed), C5 (consistency
test)

The bulk of the work: write all 10 documents as block-model JSON under
`synthetic-corpus/documents/`, following the Slice 3 corpus plan —
multi-section prose (Purpose/Scope/Roles/Procedure/References-style
structure), tables, flowcharts, swim-lane diagrams, in-corpus
cross-references (R1), and external citations (R2), sized to land each
document in the 5-15 page range once rendered. Given the volume, this is
split across up to 3 parallel sub-agent forks (CLAUDE.md's cap), each
authoring a subset of documents from the same shared corpus plan so
cross-references stay consistent.

**Demo:** The Slice 2 CLI, now pointed at real content, renders all 10
documents to PDF in `synthetic-corpus/output/`; each document's page count
lands in the 5-15 range.

### Test plan

- Integration: the CLI reports 10/10 documents rendered, no failures.
- Regression (C5): every cross-reference string in the golden set
  resolves to a real doc ID from the corpus plan — fails loudly if a
  future edit breaks a citation.
- Manual: spot-check 2-3 rendered PDFs for prose quality, correct
  Times New Roman/heading/header-footer styling, and that page counts
  land in range.

## Slice 5: Manual RAG effectiveness spot-check

**Covers:** C8 — the original motivating goal, done as a documented
procedure rather than as code this tool ships (the tool's job stops at
"PDFs exist on disk").

With the backend running (`make up`), upload each PDF in
`synthetic-corpus/output/` through the existing `POST /documents` endpoint
(the same path `make seed` already exercises), then ask `/chat` a small
fixed set of questions — including at least a few only answerable by
following a cross-reference (R1) from one document to another — and check
the answers and citations by hand. This is a qualitative spot-check, not a
scored precision/recall harness (that stays deferred per QUESTIONS.md
Q19).

**Demo:** Following the documented steps — upload all 10 PDFs, ask the
question list — produces correct answers with correct citations,
including at least one cross-reference question answered correctly.

### Test plan

- This is a manual procedure, not an automated test — reviewed by hand,
  same constraint as the existing `e2e`-marked backend tests (needs a
  live LLM + Qdrant).
