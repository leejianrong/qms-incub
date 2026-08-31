# ADR-0007: The document corpus is grown by both generating and importing, sharing one ingestion pipeline

- Status: Accepted
- Date: 2026-08-31
- Deciders: leejianrong (user), agent (plan-new-project skill, round 4)

## Context

Synthetic documents (ADR-0001) are good for exercising the ingestion
pipeline in a controlled, repeatable way, but they aren't real QMS policy
text. The user wants the corpus to also be grown from existing open-source
QMS documents — real PDFs sourced from elsewhere — with a way to switch
between the two methods of adding a document.

## Decision

`PolicyDocument` gains an `origin` field: `generated` or `imported`. A
generated document is composed through the block engine (ADR-0001) and
rendered to PDF by the app. An imported document is a PDF a QA-author
uploads directly, along with a `source_attribution` field (URL or license
note, since these are described as open-source documents) — it has no
blocks and is not rendered by the app, since it already exists as a
finished PDF. Both origins are just rows in the same `PolicyDocument` table
and document list; a toggle in the document-list toolbar switches the
"add document" flow between "Generate" and "Import". Both flow into the
same S6 ingestion pipeline: for a generated document, ingestion chunks the
HTML/PDF text the app produced; for an imported one, ingestion extracts and
chunks text from the uploaded PDF directly.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Separate `ImportedDocument` entity/table | Splits the document list and ingestion trigger logic into two parallel paths for no real benefit — both are conceptually "a document in the corpus", just sourced differently |
| Convert imported PDFs into the block model (parse tables/flowcharts back into blocks) | Unnecessary and fragile — reverse-engineering an arbitrary PDF's structure into the app's own block schema isn't needed just to ingest it for RAG |
| Import only via URL fetch, no direct upload | Narrower than what "open source... already existing" documents implies; direct upload is the simpler, more general case and a URL-based fetch can be layered on later without changing this decision |

## Consequences

Gains: one document list and one ingestion pipeline serve both content
sources, which is exactly what "switch between the methods" asks for, and
imported real-world documents give the ingestion pipeline more structurally
varied test material than synthetic generation alone. Costs: imported PDFs
are unpredictable in layout and extraction quality compared to the app's
own generated HTML — flagged as an open risk in PLAN.md, first visible in
the import slice. Forecloses: nothing structural — a future URL-fetch
import path or bulk-import feature is additive to `origin = imported`, not
a rework of it.
