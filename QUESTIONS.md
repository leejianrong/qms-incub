# Questions

Statuses: `DECIDED` (user answered) · `ASSUMED` (default taken, correct it if
wrong) · `FORK` (waiting on the user) · `DEFERRED` (not needed this milestone).

Source idea: README.md's one-line description, expanded across three rounds
of user replies into the detail captured below. No prior planning artifacts
existed (fresh mode).

## Open forks

<empty — all three rounds closed>

## Register

| ID | Question | Status | Answer or default | Landed |
|----|----------|--------|-------------------|--------|
| Q1 | What is qms-incub for? | DECIDED | A QMS product for large-company project managers to classify software projects and comply with company QMS policy | PLAN §Problem/Solution |
| Q2 | Which compliance framework does the corpus map to? | DECIDED | Generic, user-defined `ComplianceStandard → Clause → Requirement` hierarchy, no hardcoded ISO/CFR schema | ADR-0008 |
| Q3 | MVP module scope | DECIDED | Wizard, todo generation, artifact upload, policy doc generator + PDF export, synthetic batch generation, document import, RAG chatbot, blog, FAQ — **reopened round 5, see below** | PLAN §Scope |
| Q4 | Single-org vs multi-tenant | DECIDED | Single-org v1, with an org-scoping column on every table (user reconfirmed round 5) | ADR-0004 |
| Q5 | Deployment target | DECIDED | No deploy target at all — local-only, brought up with `make up` for a laptop demo (user corrected round 5; originally assumed cloud-hosted) | ADR-0005 |
| Q6 | Is the synthetic-PDF RAG test corpus the same pipeline as the product chatbot's? | ASSUMED | Yes — one shared ingestion/retrieval pipeline, dogfooded | PLAN §Shape (S6) |
| Q7 | How are flowcharts produced? | ASSUMED | Auto-composed from structured step data (Mermaid-style DSL), not hand-drawn | ADR-0006 |
| Q8 | Classification wizard dimensions | ASSUMED | 3 fixed dimensions (data sensitivity, customer-facing, regulatory exposure) → Low/Medium/High tier | PLAN §Implementation decisions |
| Q9 | Is the chatbot agentic (can it act on the wizard/todos)? | ASSUMED | No — retrieval-QA only in v1 | PLAN §Shape (S7) |
| Q10 | Who authors blog/FAQ, and do they feed the RAG corpus? | ASSUMED | Admin-authored simple CMS content, ingested alongside policy documents | PLAN §Shape (S8) |
| Q11 | Tech stack | DECIDED | *(superseded)* Python/FastAPI, Svelte+Vite, PostgreSQL, Qdrant, LlamaIndex + Docling — team decision, round 6 | ADR-0009 |
| Q12 (F6) | Policy document generation: one authoring surface, or an engine serving both authoring and synthetic batch generation? | DECIDED | One block-based engine, two modes (author + batch-generate) | ADR-0001 |
| Q13 (F7) | Compliance artifact workflow: self-attestation or QA-reviewer approval gate? | DECIDED | Self-attestation in v1; reviewer approval gate confirmed as a wanted next-iteration feature, not cut | ADR-0002 |
| Q14 | LLM provider | DECIDED | OpenRouter API | ADR-0003 |
| Q15 | Chatbot grounding scope: corpus only, or corpus + the asking user's own compliance state? | ASSUMED | Hybrid — vector retrieval over the corpus, plus direct structured injection of the asking PM's own project/todo/artifact state | ADR-0003 |
| Q16 | QA-reviewer approval surface | DEFERRED | Named next-iteration feature, not this milestone | PLAN §Scope (Out) |
| Q17 | External REST API for third-party integration | DEFERRED | Not needed this milestone | PLAN §Scope (Out) |
| Q18 | SSO / external identity provider | DEFERRED | Not needed this milestone | PLAN §Scope (Out) |
| Q19 | RAG retrieval evaluation/benchmarking harness | DEFERRED | v1 needs ingestion/retrieval to work and be demoable, not rigorously tuned | PLAN §Scope (Out) |
| Q20 | On-prem / air-gapped deployment | DEFERRED | Cloud-hosted only this milestone | PLAN §Scope (Out) |
| Q21 | Multi-tenant SaaS | DEFERRED | Single-org this milestone (see Q4) | PLAN §Scope (Out) |
| Q22 | Core data model and entities | ASSUMED | Project, TodoItem, Artifact, PolicyDocument, Block, BlogPost, FAQEntry, IngestedChunk | PLAN §Implementation decisions |
| Q23 | State and storage | ASSUMED | Postgres as source of truth; documents versioned | ADR-0005 |
| Q24 | Concurrency / document lifecycle | ASSUMED | Draft → Published only, no approval state (ties to Q13) | ADR-0002, PLAN §Implementation decisions |
| Q25 | Interfaces and contracts | ASSUMED | Web UI only, single write path, no external API in v1 (see Q17) | PLAN §Affordances |
| Q26 | Failure behaviour | ASSUMED | Invalid state transitions hard-rejected; traceability/compliance gaps surfaced as flagged status, not errors | PLAN §Testing approach |
| Q27 | Security and secrets | ASSUMED | No PHI/PII modeled in v1; document content may be confidential but not personal data | PLAN §Scope (Out) |
| Q28 | Versioning and migration | ASSUMED | Document revisioning is core product behavior, not a migration afterthought; app schema migrations follow normal practice | PLAN §Implementation decisions |
| Q29 | Measurable success | ASSUMED | Stated per-slice as concrete counts/procedures in SLICES.md, not adjectives | SLICES.md |
| Q30 | How does document import work relative to generation? | ASSUMED | Second entry point on the same document list/corpus, not a separate module; both flow into one ingestion pipeline | ADR-0007 |
| Q31 | Do imported documents need a source/attribution field? | ASSUMED | Yes — `source_attribution` required before publish, since these are "open source" documents | ADR-0007, PLAN §Implementation decisions |
| Q32 | Image block type | ASSUMED | Added as a fourth block type alongside text/table/flowchart | ADR-0001 |
| Q33 | Data model for Q2/Q3's compliance hierarchy | DECIDED | `ComplianceStandard`/`Clause`/`Requirement` entities, user-authored; `TodoItem` traces to a `Requirement` instead of a flat practice string | ADR-0008 |
| Q34 | Local one-command bring-up | DECIDED | `make up` starts Postgres + Qdrant (Docker Compose), runs migrations, seeds demo data, starts the FastAPI backend and the Svelte/Vite dev server — per `dev-playbook` principle 17 | ADR-0005, ADR-0009 |
| Q35 | PDF rendering engine, given the backend is now Python (Puppeteer is Node-only) | DECIDED | WeasyPrint — pure Python, no browser process, fits V5's batch-generation call volume | ADR-0010 |
| Q36 | Embedding model for RAG ingestion/retrieval (S6/S8) — OpenRouter is a chat/completion gateway, not an embeddings provider | ASSUMED | Local HuggingFace sentence-embedding model (BAAI/bge-small-en-v1.5) via LlamaIndex's `HuggingFaceEmbedding`, run in-process — no API key, no extra paid dependency, offline-capable | V1 implementation |
| Q37 | LLM provider for local dev/testing vs. the ADR-0003-decided OpenRouter default | ASSUMED | Chat client is provider-swappable (`LLM_PROVIDER` env var) via an OpenAI-compatible client pointed at either Ollama (`http://localhost:11434/v1`, local, no key — used for dev/testing per user request) or OpenRouter (ADR-0003's decided default for anything beyond local dev). Not a reversal of ADR-0003 — Ollama is a local convenience, OpenRouter stays the recorded decision | ADR-0003, V1 implementation |
| Q38 | Is synthetic batch generation (S5) a QA-author-facing web app feature, or local dev tooling? | DECIDED | Local dev tooling only — a CLI (`make batch`), no HTTP endpoint, no UI. Real company QMS documents exist but are sensitive and unavailable during this build; synthetic generation exists solely to validate the RAG pipeline before real content is ingested, not as a product feature | ADR-0011 |

## Coverage

| Category | Covered by |
|----------|-----------|
| Primary user and actors | Q1 |
| Scope boundary | Q2, Q3, Q16, Q17, Q18, Q19, Q20, Q21, Q38 |
| Data model and identity | Q22, Q30, Q31, Q32, Q33 |
| State and storage | Q23 |
| Concurrency and conflict | Q13, Q24 |
| Interfaces and contracts | Q25, Q30 |
| Failure behaviour | Q26 |
| External dependencies | Q11, Q14, Q35, Q36, Q37 |
| Runtime and deployment | Q5, Q34 |
| Measurable success | Q29 |
| Security and secrets | Q27 |
| Versioning and migration | Q28 |
