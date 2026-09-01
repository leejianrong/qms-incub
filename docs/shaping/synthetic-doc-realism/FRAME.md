---
shaping: true
---

# Realistic Synthetic QMS Documents — Frame

## Source

> i would like to kick off a planning phase for the synthetic document
> generation. i want more documents to be generated, and the documents
> should be longer. I want about 10 documents of around 10 pages each (can
> be in the range of 5-15 pages). more importantly, i want these QMS
> documents to be realistic. They should cross reference one another as
> well as external sources (can be web links, etc.). also, the document
> should look and feel like QMS policy documents from a large software
> company. they should use times new roman font, appropriate font size for
> headers, sub headers, and text, include flow chart diagrams, swim lane
> diagrams, workflow diagrams, etc. they should also include headers and
> footers.

> also worth noting: i don't need these documents to keep changing or
> evolve. just a golden set of 10 documents is fine for now

> but in the future i do want to extend this synthetic document generator
> to cover other domains. these quality management system policy documents
> may be extended in the future to cover other business functions in the
> company (not just software, think of a more generic company or a
> conglomerate etc.)

> no, hold on. we need to clean up the docs. there's been a mistake. there
> shouldn't be any synthetic generation inside the backend at all. the QMS
> platform or web app is just meant for ingesting documents. the synthetic
> generation of documents is a completely separate thing, just meant to
> test the backend's RAG capabilities.

> the synthetic generation tool and the backend (web app) are two
> completely different and separate products. the backend (web app) should
> just expose functionality for users to upload documents. in the backend,
> the documents are ingested with docling etc (RAG ingestion pipeline) and
> then users can query for information and it will be retrieved from a
> vector database and an answer will be synthesized by an LLM (openrouter
> api).

> the synthetic document tool doesn't even have to communicate with the
> backend. it just has to generate the pdfs and save them to local
> directory.

## Problem

Two separate problems got tangled together earlier in this planning
session, and it's worth being explicit that they're now untangled:

1. **The old V5 synthetic batch generator lived inside the backend and
   reused its document-composition engine.** That engine has since been
   deleted from the backend entirely (a separate, larger correction — see
   `docs/adr/0012-*`) — the qms-incub web app is ingestion-and-chat only,
   full stop. It never composed documents, so there's nothing left inside
   the backend for a synthetic generator to reuse or plug into.
2. **The content itself wasn't realistic.** Every document repeated the
   same boilerplate sentence with an index swapped in, a table sampled
   from ~7 roles / 8 names / 5 canned responsibility strings, and a
   flowchart with labels from a fixed 9-item list. Nothing
   cross-referenced anything else, and the visual output (generic
   sans-serif, no running headers/footers, one heading level) didn't read
   like a real corporate QMS document.

The synthetic-document tool is now understood to be a **fully independent
product**, sharing no code with the backend and not even calling it — its
only job is producing realistic-looking QMS PDFs on disk. Testing the
backend's actual RAG effectiveness with those PDFs is a separate, manual
step outside this tool's scope.

## Outcome

A fixed **golden set of ~10 synthetic QMS policy documents** (5-15 pages
each), generated once by this independent tool (not required to be
regenerable byte-identically on every future run), written to a local
output directory, that:

- Read like real large-software-company QMS policies — multi-section
  prose (Purpose/Scope/Roles/Procedure/References-style structure), not
  templated mad-libs.
- Cross-reference each other (e.g. "see Policy POL-014 §3.2") and
  external sources (web links / standards citations).
- Look the part: Times New Roman, a real heading hierarchy, page
  headers/footers with page numbers.
- Include flowchart, swim-lane, and workflow diagrams.

Once the PDFs exist, a person can manually feed them to the running
backend (its `POST /documents` upload endpoint) and ask it realistic
questions — including ones that require following a cross-reference from
one document to another — to judge whether ingestion/retrieval actually
work on QMS-shaped content, not just on the old mad-libs test data. That
manual check is outside this tool's own scope; the tool's job ends at
"realistic PDFs exist on disk."
