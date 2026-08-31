# QMS Incub: Kanban

Tracks the 8 vertical slices from [SLICES.md](SLICES.md) as epics. One card
per slice. Backlog is kept in build order — pull from the top. Move a card
by cutting it from one column and pasting it under another; keep the card
body intact so history isn't lost.

## Backlog

- [ ] **V1 — RAG Spike — Generate, Ingest, Ask**
  Delivers: R4 (partial), R6 (partial), R7 (partial). Seed one document
  with text/table/flowchart, PDF export, ingest, chatbot answers a
  question grounded in the table content. The riskiest mechanism in the
  whole plan — pull this first. Rests on: Q7, Q11. See SLICES.md.

- [ ] **V2 — Compliance Requirements + Project Classification + Todo List**
  Delivers: R1, R2. Standard/Clause/Requirement editor, 3-question wizard,
  risk-tier scoring, auto-generated todo list traced to Requirements.
  Rests on: Q8. See SLICES.md.

- [ ] **V3 — Artifact Upload + Self-Attestation**
  Delivers: R3. Upload flips a todo to Complied; dashboard compliance %.
  Rests on: ADR-0002 (self-attestation, no review gate). See SLICES.md.

- [ ] **V4 — Policy Document Composer**
  Delivers: R4 (partial — generation path; import closes it in V7).
  Block-based editor (text/table/flowchart/image), Draft→Published,
  publish triggers ingestion, PDF export. See SLICES.md.

- [ ] **V5 — Synthetic Batch Generation**
  Delivers: R5, R6 (breadth). "Generate N variants" panel, randomized
  block composition, ingestion status dashboard. See SLICES.md.

- [ ] **V6 — Blog + FAQ**
  Delivers: R8, R6 (breadth). Admin-authored blog/FAQ, publish triggers
  ingestion tagged by source type. See SLICES.md.

- [ ] **V7 — Import Existing QMS Documents**
  Delivers: R4 (closes), R6 (breadth). Upload a real PDF + attribution,
  `origin = imported`, ingested directly. Rests on: ADR-0007. See SLICES.md.

- [ ] **V8 — Compliance-Aware Chat**
  Delivers: R0 (closes), R7 (closes). Chat context = retrieved corpus
  chunks + the asking PM's own project/todo/artifact state. Rests on: Q15.
  See SLICES.md.

## In Progress

_(empty)_

## Done

_(empty)_
