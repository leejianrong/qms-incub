---
shaping: true
---

# Realistic Synthetic QMS Documents — Shaping

See [FRAME.md](./FRAME.md) for source/problem/outcome.

## Requirements (R)

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | Produce a fixed golden corpus of ~10 QMS policy documents, 5-15 pages each, realistic enough (content + look) to meaningfully judge RAG ingestion/retrieval effectiveness | Core goal |
| R1 | Documents cross-reference each other with specific, checkable citations (e.g. "see Policy POL-014 §3.2") | Must-have |
| R2 | Documents cite external sources (web links / standards references) | Must-have |
| R3 | Visual formatting matches large-company QMS convention: Times New Roman, a real heading-level hierarchy (H1/H2/H3 distinct sizes), running page headers and footers with page numbers | Must-have |
| R4 | Documents include flowchart, swim-lane, and workflow diagrams | Must-have |
| R5 | The golden set is generated once and then kept fixed — no requirement to regenerate byte-identically from a seed on every future run | Must-have |
| 🟡 R6 | 🟡 The tool renders documents to PDF using its own independent code (block model, diagram renderers, HTML→PDF export) — there is no backend engine left to reuse; nothing here imports `qms_incub` | 🟡 Must-have |
| R7 | Tooling constraints | |
| 🟡 R7.1 | 🟡 Lives entirely in its own top-level folder (`synthetic-corpus/`), sharing no code with the backend and not calling it over HTTP or any other interface — its output is PDF files on disk, nothing more | 🟡 Must-have (decided) |
| R7.2 | The golden documents (or the source content that produces them) are stored/versioned so the corpus doesn't need regenerating and is available to anyone who clones the repo | Undecided |
| R8 | The generation mechanism is extensible to other business domains beyond software (HR, finance, legal, manufacturing, etc. — a generic conglomerate, not just a software company) without rewriting the generator — domain-specific content (topics, roles, standards bodies) must be swappable/configurable, not hardcoded into the corpus-plan or prompting logic | Must-have |

## The fork: how is realistic prose actually produced?

### A: Hand-authored content banks (procedural, offline)

A generator with much larger banks of section templates, sentence
fragments, role/name/topic vocab, and hand-wired cross-reference logic (a
corpus plan of 10 doc IDs/titles that the templates deterministically
stitch citations from). No network calls, ever. This would be new code
written from scratch inside `synthetic-corpus/` — there's no backend
generator left to extend.

### B: One-time LLM-assisted generation — REJECTED

Would have prompted an LLM (OpenRouter) once per document during authoring.
**Rejected per user direction**: OpenRouter/Ollama are reserved for the RAG
step (ingestion/querying) only — not for producing the synthetic documents
themselves.

### C: Agent-authored golden corpus (no network call at all) — SELECTED

Claude Code (this session, or a forked sub-agent per document/batch of
documents) authors the corpus plan and all 10 documents' content directly —
prose, tables, diagram step/lane lists — as static block-model JSON
fixtures, using its own reasoning rather than calling any LLM API from
code. A small render script inside `synthetic-corpus/` (its own Jinja2
template + WeasyPrint call + a from-scratch flowchart/swim-lane SVG
renderer — none of it shared with, or imported from, the backend) turns
that JSON into the final PDFs. No `OPENROUTER_API_KEY` or network
dependency anywhere in this path, one-time or otherwise — resolving R7.1
even more strongly than B did. Extending to a new domain later (R8) means
running this same authoring process again for a new domain profile — a
repeatable task for a future coding session, not a code rewrite.

## Fit Check

| Req | Requirement | Status | A | C |
|-----|-------------|--------|---|---|
| R0 | Produce a fixed golden corpus of ~10 QMS policy documents, 5-15 pages each, realistic enough (content + look) to meaningfully judge RAG ingestion/retrieval effectiveness | Core goal | ❌ | ✅ |
| R1 | Documents cross-reference each other with specific, checkable citations | Must-have | ✅ | ✅ |
| R2 | Documents cite external sources | Must-have | ✅ | ✅ |
| R3 | Visual formatting (fonts, heading hierarchy, headers/footers) | Must-have | ✅ | ✅ |
| R4 | Swim-lane and workflow diagrams | Must-have | ✅ | ✅ |
| R5 | Golden, fixed, not required to regenerate | Must-have | ✅ | ✅ |
| R6 | Own independent render/export code, no backend dependency | Must-have | ✅ | ✅ |
| R7.1 | Fully separate tool, no backend coupling | Must-have | ✅ | ✅ |
| R7.2 | Golden output stored/versioned | Undecided | ✅ | ✅ |
| R8 | Extensible to other business domains without rewriting the generator | Must-have | ❌ | ✅ |

**Notes:**
- A fails R0: getting genuinely realistic, varied, multi-page prose (not
  recognizably templated) out of hand-authored content banks means writing
  a very large amount of bespoke fake-policy text by hand — the mad-libs
  problem just gets bigger, not solved.
- A fails R8: extending to a new domain (HR, finance, legal...) means
  writing an entirely new set of hand-authored content banks per domain —
  the same authoring cost as building the software one, repeated for every
  domain, with no shared mechanism beyond the block-model plumbing.
- C satisfies R1 by construction — the author (Claude/sub-agent) has the
  full corpus plan in context while writing every document, so citations
  are correct at write time rather than needing a drift-detection pass. A
  regression test (C5 below) still asserts this stays true over time.
- R3/R4 are orthogonal to this decision — CSS/template and new-block-type
  work applies identically either way.

**Decided: C** — agent-authored, zero network dependency, matches the
user's explicit direction that LLM APIs are reserved for the RAG step
only.

## Other components

Everything below lives inside `synthetic-corpus/`, a self-contained tool
with its own dependencies (Jinja2, WeasyPrint) and zero imports from
`qms_incub`. It has no HTTP client code and never talks to the backend.

| Part | Mechanism | Flag |
|------|-----------|:----:|
| **C0** | **Domain profile** — a small data artifact (business function name, typical roles/titles, typical policy topics, standards bodies to cite) that the authoring process (an agent) is briefed with; "Software Engineering / IT" is the first profile. A future domain (HR, Finance, Legal...) means authoring a new profile + corpus and running the same unchanged code path — not touching the generator (R8) | |
| **C1** | **Corpus plan** — 10 doc IDs/titles/topics/relationships decided up front (from the domain profile), authored before the full documents so cross-references (R1) are correct by construction | |
| **C2** | **Block model + renderers, written from scratch** — a small `text`/`table`/`flowchart`/`swim-lane` content model (own dataclasses/Pydantic models, not shared with anything), plus SVG renderers for flowchart and swim-lane diagrams (lanes = columns, steps assigned to a lane). "Workflow diagram" reads as the same primitive as flowchart (steps + transitions) — no third block type planned unless you had something more specific in mind | |
| **C3** | **PDF styling** — an HTML template + WeasyPrint `@page` CSS, owned by this tool: Times New Roman, H1/H2/H3 sizing, running header/footer via CSS Paged Media (`position: running()` + page-number counters) | |
| **C4** | **Golden-corpus storage** — commit each document's block-model JSON under `synthetic-corpus/documents/*.json`; rendered PDFs land in a gitignored `synthetic-corpus/output/` directory, regenerated on demand from the committed JSON (decided, R7.2) | |
| **C5** | **Corpus-consistency regression test** — asserts every cross-reference string in the golden set actually names a real doc ID in the corpus plan, so a future edit can't silently break a citation | |
| **C6** | **CLI entry point** (e.g. `synthetic-corpus/generate.py` or a small Makefile of its own) — loads the committed JSON fixtures, renders, and writes PDFs to `synthetic-corpus/output/`. That's the entire job: no ingest step, no backend call, no network access at all | |
| **C7** | **Repo layout** — new top-level `synthetic-corpus/` directory holds everything: domain profile, corpus plan, per-document block-model JSON, the render code, and its own dependency manifest. Nothing lives in or touches `backend/`. CLAUDE.md's Layout table gets a `synthetic-corpus/` entry | |
| **C8** | **Manual RAG spot-check (outside this tool)** — once PDFs exist in `synthetic-corpus/output/`, a person uploads them to the running backend (`POST /documents`, same path `make seed` uses) and asks it questions, including ones that require following a cross-reference from one document to another. This is a documented procedure, not code this tool ships | |
