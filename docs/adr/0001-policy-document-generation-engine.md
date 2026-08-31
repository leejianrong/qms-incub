# ADR-0001: One block-based document engine serves both authoring and synthetic batch generation

- Status: Accepted
- Date: 2026-08-31
- Deciders: leejianrong (user), agent (plan-new-project skill, round-2 fork F6)

## Context

The project needs two things that look different on the surface: a way for
a QA-author to compose real QMS policy documents (text, tables, flowcharts),
and a way to produce synthetic test PDFs to validate the RAG ingestion
pipeline. Building these as two separate tools risks the synthetic
generator drifting from what real documents actually look like, which
would make it a weak test of ingestion. Building only a hand-authoring tool
leaves no answer for "generate N variants" at all.

## Decision

Build one document engine around a block model (`text`, `table`,
`flowchart`, `image` block types). A QA-author composes a document by adding and
arranging blocks through an authoring UI. A separate "generate N variants"
batch mode reuses the same block model and rendering path, but populates
blocks programmatically with randomized content and complexity (table row
counts, flowchart step counts) instead of human input, and flags the
resulting documents `is_synthetic = true`. Both paths render through the
same HTML → PDF export and the same publish → ingest pipeline.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Separate WYSIWYG editor and separate synthetic-PDF script | Synthetic documents would drift from real document structure, weakening them as an ingestion test; duplicate rendering/PDF code to maintain |
| Synthetic generation only, no authoring UI | Doesn't satisfy the stated need for QA-authors to publish real policy content |
| Freeform document editor (arbitrary rich text, no block typing) | Can't be driven programmatically for batch generation, and loses the structured flowchart/table distinction the RAG-testing use case needs |

## Consequences

Gains: one rendering and ingestion path to test and maintain; synthetic
documents are structurally representative of real ones by construction.
Costs: the authoring UI is constrained to the block model rather than
freeform rich text, so a QA-author can't do things like inline-format
arbitrary prose beyond what the `text` block supports — acceptable for QMS
policy documents but would need revisiting for open-ended content types.
Forecloses: a future freeform WYSIWYG editor would need its own
block-to-rich-text bridge rather than being a drop-in replacement.
