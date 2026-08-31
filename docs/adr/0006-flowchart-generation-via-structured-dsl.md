# ADR-0006: Flowcharts are generated from structured step data, not drawn freehand

- Status: Accepted
- Date: 2026-08-31
- Deciders: agent (plan-new-project skill, assumed default Q7)

## Context

The idea asks for policy documents that "include tables, flowcharts, text"
and can be "generated" — including, in the synthetic batch mode (ADR-0001),
programmatically with no human in the loop. A freeform diagram editor
(canvas, drag-and-drop shapes, arbitrary connectors) cannot be driven
programmatically to produce N random variants, and is a substantially
larger feature — its own data model, its own editing UX, its own
serialization format — than what a document *generator* needs.

## Decision

A `flowchart` block stores a structured, ordered list of process steps
(and simple branch/decision points). The authoring UI presents this as a
step-list editor with a live preview, not a drawing canvas. Rendering (both
for on-screen preview and for PDF export) compiles the step list to a
Mermaid-style diagram definition and renders it server-side to SVG. The
synthetic batch generator (ADR-0001) produces flowchart blocks by
generating randomized step lists of a given length, using the identical
render path.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Freeform diagram/canvas editor (arbitrary shapes and connectors) | Can't be driven programmatically for batch generation; a much larger feature (its own editing UX and data model) than the block model needs; explicitly named as out of scope in PLAN.md |
| Static image upload for flowcharts | Not generatable at all — defeats the synthetic batch generation requirement (R5) entirely |

## Consequences

Gains: one rendering path serves human authoring, PDF export, and
synthetic batch generation, and flowchart content is structured data that
downstream ingestion (S6) can chunk meaningfully rather than an opaque
image. Costs: a QA-author is limited to linear/branching step sequences —
they cannot draw an arbitrary diagram (e.g. a network topology) with this
block type. Forecloses arbitrary-diagram support under this block type; a
future freeform diagram type would be a new, separate block kind.
