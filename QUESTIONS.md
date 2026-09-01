# Questions

Statuses: `DECIDED` (user answered) · `ASSUMED` (default taken, correct it if
wrong) · `FORK` (waiting on the user) · `DEFERRED` (not needed this milestone).

Source idea: README.md's one-line description, expanded across three rounds
of user replies into the detail captured below. No prior planning artifacts
existed (fresh mode).

## Open forks

Q48, Q49, Q50 — surfaced by the 2026-09-01 agents/MCP/CLI/identity
research session (ADR-0014/0015/0016); none block the current milestone.
All three rounds of the original interview are closed.

## Register

| ID | Question | Status | Answer or default | Landed |
|----|----------|--------|-------------------|--------|
| Q1 | What is qms-incub for? | DECIDED | A QMS product for large-company project managers to classify software projects and comply with company QMS policy | PLAN §Problem/Solution |
| Q2 | Which compliance framework does the corpus map to? | DECIDED | Generic, user-defined `ComplianceStandard → Clause → Requirement` hierarchy, no hardcoded ISO/CFR schema | ADR-0008 |
| Q3 | MVP module scope | DECIDED | Wizard, todo generation, artifact upload, document upload, RAG chatbot, blog, FAQ. *(Corrected: the original scope conflated a document-composition engine with the actual product need — no document generator or PDF export lives in this repo at all; synthetic generation moved out entirely to its own tool. See ADR-0012.)* | PLAN §Scope |
| Q4 | Single-org vs multi-tenant | DECIDED | Single-org v1, with an org-scoping column on every table (user reconfirmed round 5) | ADR-0004 |
| Q5 | Deployment target | DECIDED | No deploy target at all — local-only, brought up with `make up` for a laptop demo (user corrected round 5; originally assumed cloud-hosted) | ADR-0005 |
| Q6 | Is the synthetic-PDF RAG test corpus the same pipeline as the product chatbot's? | ASSUMED | Yes — one shared ingestion/retrieval pipeline, dogfooded | PLAN §Shape (S6) |
| Q7 | How are flowcharts produced? | ASSUMED | *(superseded)* Moot now — the backend renders no flowcharts at all | ADR-0006, ADR-0012 |
| Q8 | Classification wizard dimensions | ASSUMED | 3 fixed dimensions (data sensitivity, customer-facing, regulatory exposure) → Low/Medium/High tier | PLAN §Implementation decisions |
| Q9 | Is the chatbot agentic (can it act on the wizard/todos)? | ASSUMED | No — retrieval-QA only in v1 | PLAN §Shape (S7) |
| Q10 | Who authors blog/FAQ, and do they feed the RAG corpus? | ASSUMED | Admin-authored simple CMS content, ingested alongside policy documents | PLAN §Shape (S8) |
| Q11 | Tech stack | DECIDED | *(superseded)* Python/FastAPI, Svelte+Vite, PostgreSQL, Qdrant, LlamaIndex + Docling — team decision, round 6 | ADR-0009 |
| Q12 (F6) | Policy document generation: one authoring surface, or an engine serving both authoring and synthetic batch generation? | SUPERSEDED | *(was: one block-based engine, two modes)* — the premise didn't hold up. The backend authors nothing; it only ingests. Synthetic generation is a separate tool with its own, independent code | ADR-0012 |
| Q13 (F7) | Compliance artifact workflow: self-attestation or QA-reviewer approval gate? | DECIDED | Self-attestation in v1; reviewer approval gate confirmed as a wanted next-iteration feature, not cut | ADR-0002 |
| Q14 | LLM provider | DECIDED | OpenRouter API | ADR-0003 |
| Q15 | Chatbot grounding scope: corpus only, or corpus + the asking user's own compliance state? | ASSUMED | Hybrid — vector retrieval over the corpus, plus direct structured injection of the asking PM's own project/todo/artifact state | ADR-0003 |
| Q16 | QA-reviewer approval surface | DEFERRED | Named next-iteration feature, not this milestone | PLAN §Scope (Out) |
| Q17 | External REST API for third-party integration | DEFERRED | Not needed this milestone | PLAN §Scope (Out) |
| Q18 | SSO / external identity provider | DEFERRED | Not needed this milestone | PLAN §Scope (Out); next-milestone mechanism decided at Q45 (ADR-0014), not yet activated |
| Q19 | RAG retrieval evaluation/benchmarking harness | DEFERRED | v1 needs ingestion/retrieval to work and be demoable, not rigorously tuned | PLAN §Scope (Out) |
| Q20 | On-prem / air-gapped deployment | DEFERRED | Cloud-hosted only this milestone | PLAN §Scope (Out) |
| Q21 | Multi-tenant SaaS | DEFERRED | Single-org this milestone (see Q4) | PLAN §Scope (Out) |
| Q22 | Core data model and entities | ASSUMED | Project, TodoItem, Artifact, PolicyDocument (ingestion-status record, not content — no `Block` entity exists), BlogPost, FAQEntry, IngestedChunk | PLAN §Implementation decisions |
| Q23 | State and storage | ASSUMED | Postgres as source of truth; documents versioned | ADR-0005 |
| Q24 | Concurrency / document lifecycle | ASSUMED | *(revised)* No Draft/Published lifecycle at all — an upload is ingested immediately. Status tracks pipeline progress (pending/embedded/failed), not editorial review (ties to Q13) | ADR-0002, ADR-0012, PLAN §Implementation decisions |
| Q25 | Interfaces and contracts | ASSUMED | Web UI only, single write path, no external API in v1 (see Q17) | PLAN §Affordances |
| Q26 | Failure behaviour | ASSUMED | Invalid state transitions hard-rejected; traceability/compliance gaps surfaced as flagged status, not errors | PLAN §Testing approach |
| Q27 | Security and secrets | ASSUMED | No PHI/PII modeled in v1; document content may be confidential but not personal data | PLAN §Scope (Out) |
| Q28 | Versioning and migration | ASSUMED | Document revisioning is core product behavior, not a migration afterthought; app schema migrations follow normal practice | PLAN §Implementation decisions |
| Q29 | Measurable success | ASSUMED | Stated per-slice as concrete counts/procedures in SLICES.md, not adjectives | SLICES.md |
| Q30 | How does document import work relative to generation? | SUPERSEDED | There's no generation to work "relative to" anymore — upload is the only entry point, full stop | ADR-0012 |
| Q31 | Do imported documents need a source/attribution field? | SUPERSEDED | Dropped rather than kept optional — `PolicyDocumentRow` has no attribution field at all now. If provenance tracking is wanted later, it's a new decision, not a resurrection of this one | ADR-0012 |
| Q32 | Image block type | ASSUMED | *(superseded)* Moot — there's no block model in the backend for a fourth type to join | ADR-0001, ADR-0012 |
| Q33 | Data model for Q2/Q3's compliance hierarchy | DECIDED | `ComplianceStandard`/`Clause`/`Requirement` entities, user-authored; `TodoItem` traces to a `Requirement` instead of a flat practice string | ADR-0008 |
| Q34 | Local one-command bring-up | DECIDED | `make up` starts Postgres + Qdrant (Docker Compose), runs migrations, seeds demo data, starts the FastAPI backend and the Svelte/Vite dev server — per `dev-playbook` principle 17 | ADR-0005, ADR-0009 |
| Q35 | PDF rendering engine, given the backend is now Python (Puppeteer is Node-only) | DECIDED | *(superseded)* WeasyPrint — moot now; the backend doesn't render PDFs at all | ADR-0010, ADR-0012 |
| Q36 | Embedding model for RAG ingestion/retrieval (S6/S8) — OpenRouter is a chat/completion gateway, not an embeddings provider | ASSUMED | Local HuggingFace sentence-embedding model (BAAI/bge-small-en-v1.5) via LlamaIndex's `HuggingFaceEmbedding`, run in-process — no API key, no extra paid dependency, offline-capable | V1 implementation |
| Q37 | LLM provider for local dev/testing vs. the ADR-0003-decided OpenRouter default | ASSUMED | Chat client is provider-swappable (`LLM_PROVIDER` env var) via an OpenAI-compatible client pointed at either Ollama (`http://localhost:11434/v1`, local, no key — used for dev/testing per user request) or OpenRouter (ADR-0003's decided default for anything beyond local dev). Not a reversal of ADR-0003 — Ollama is a local convenience, OpenRouter stays the recorded decision | ADR-0003, V1 implementation |
| Q38 | Is synthetic batch generation (S5) a QA-author-facing web app feature, or local dev tooling? | DECIDED | Neither, as it turns out — it isn't even a question about *this repo's backend* anymore. Synthetic generation is a fully separate tool (`synthetic-corpus/`), no shared code, no HTTP call to the backend at all. ADR-0011's local-CLI framing was a first correction; ADR-0012 is the complete one | ADR-0011, ADR-0012 |
| Q39 | Temporary LLM provider preference for a promotional API-key window | DECIDED | From 2026-09-01 through 2026-09-05, prefer `LLM_PROVIDER=zenmux` (a ZenMux API key was distributed to the team separately for this window). From 2026-09-06 onward, this lapses automatically — OpenRouter (ADR-0003's decided default) or Ollama are both fine again, OpenRouter preferred. Does not change Q37's decision or the code default, which stays `openrouter` throughout | Q37 |
| Q40 | `ui-reference/QMS Console.dc.html` (a UI/UX engineer's design mock) shows a project-intake "AOR" upload feeding the classification wizard — does that need a new document-upload path? | DECIDED | Yes — distinct from V4's QA-author corpus upload. The AOR is Docling-parsed and then LLM-extracted into a fixed set of structured fields (criticality tier, data classification, external dependencies, in-house rationale) that pre-fill wizard context. This is extraction of an uploaded document's existing content, not authoring new content, so it stays inside ADR-0012's boundary | new slice, SLICES.md V9 |
| Q41 | The mock groups `TodoItem`s into a small set of fixed process phases with a collapsible step/sub-step navigator — does a fixed grouping layer reopen ADR-0008's rejection of a hardcoded regulatory schema? | DECIDED | No. `ProcessStep` is a fixed, config-seeded PM-workflow grouping label (e.g. Initiation/Design/Build/Test/Deploy/Closure) — organizing UI, not regulatory content. `Requirement`s stay fully user-authored per ADR-0008; only the *display grouping* of the `TodoItem`s they generate is fixed | ADR-0008 (unchanged), new slice, SLICES.md V10 |
| Q42 | The mock shows a full PM → QA Office → Authority approval route (submitted/approved/returned, SLA). ADR-0002 decided self-attestation only, reviewer gate deferred — should `TodoItem` gain approval-state fields now? | DECIDED | Yes, schema-only. Add `approval_state`/`approval_authority`/`sla_target`/`decided_at` now so the UI can render the approval-route pill from the mock, but the PM's own self-attestation action sets them in this milestone — no second role, no auth gate. Matches ADR-0002's Consequences ("adding a reviewer role later is additive... not a rework"); does not reopen or reverse ADR-0002 | ADR-0002 (unchanged), new slice, SLICES.md V11 |
| Q43 | The mock auto-offers an AI-drafted "project learnings" blog post on project completion, for the PM to publish — does the backend author it? | DECIDED | No — drafting new document content, even unpublished, is exactly what ADR-0012 forbids, and collides with V6's admin-authored blog scope. Replaced with a chat capability: the PM can ask V8's compliance-aware chatbot to summarize a completed project as a chat answer — never a publishable or authored artifact | ADR-0012 (unchanged), V8 (unchanged) |
| Q44 | ADR-0009 picked Svelte + Vite for the frontend but never a component library — replicating the mock's dashboard/wizard/navigator needs a consistent set of primitives (steppers, dropdowns, modals, cards). Which library? | DECIDED | shadcn-svelte, components copied into the repo and themed to the mock's tokens rather than pulled in as an opaque dependency. Brings Tailwind CSS and Bits UI into the frontend toolchain for the first time | ADR-0013 |
| Q45 | A research session mapped agents, MCP, a CLI, and auth onto this project (2026-09-01) — what identity provider and mechanism back human login and machine-agent auth for that work, whenever it starts? | DECIDED | Keycloak, one self-hosted realm, backing OIDC human login, OAuth2 client-credentials machine auth (CLI, CI), and the MCP server's spec-required OAuth 2.1 resource-server flow. Decided for the **next milestone**, not activated in V1–V13 | ADR-0014, SLICES.md V14 |
| Q46 | Should QA-authors get a scriptable path (bulk document upload, Standard/Clause/Requirement seeding) alongside the web UI? | DECIDED | Yes — a CLI as a thin client over the same FastAPI endpoints the browser uses, no parallel logic path. Next-milestone, not V1–V13 | ADR-0015, SLICES.md V15 |
| Q47 | How should external agents (a PM's own Claude Code session, an internal ops agent, CI) query this backend's data? | DECIDED | A narrow, read-only MCP server (`ask_policy`, `get_project_status`) running alongside the chat pipeline, not inside it. Next-milestone, not V1–V13 | ADR-0016, SLICES.md V16 |
| Q48 | Does a team-facing MCP server (Q47/ADR-0016) count as the "external REST API for third-party integration" Q17 deferred? | FORK | Not yet decided. Q17 was framed around third-party integration; an MCP surface for the org's own agents is a narrower audience, but it's still a new network-exposed surface with its own auth story | *(open)* |
| Q49 | Does org-wide compliance reporting ("which projects are non-compliant," named but not decided in ADR-0003's Consequences) need a role beyond PM/QA-author? | FORK | Not yet decided. This is a different authz shape — organization-wide read — from everything else in the app, which is scoped to the asking user's own state. Deliberately excluded from ADR-0016's first MCP tool set | *(open)* |
| Q50 | If Q9 (agentic chat) is ever reopened, does an agent acting on a PM's behalf need its own audit trail distinct from self-attestation? | FORK | Not yet decided. ADR-0002's self-attestation model assumes the PM is the one who acted; an agent acting on their behalf blurs that unless every agent action is attributed back to the human who authorized it | *(open)* |
| Q51 | A route classifier for uploaded AORs (R&T vs. SSD) landed via PR #40, decided in a conversation that wasn't recorded in these docs at the time — does this fold into V9's AOR-intake/wizard flow, or stay separate? | DECIDED (mechanism) / FORK (integration) | The classifier itself (`POST /aor/classify`, embedding-similarity against two labeled reference descriptions) is in scope and documented retroactively, SLICES.md V17. Whether its output should ever feed into V9's wizard/AOR-upload flow, or stay a fully standalone endpoint, is **not yet decided** — recorded as a fork rather than silently picked, per this repo's convention. Current behavior (standalone, no `Project`/wizard linkage) is the default until someone decides otherwise | SLICES.md V17, PR #40 |
| Q52 | SLICES.md's V13 build plan item 4 names a "comment thread" on the todo detail panel, alongside gist/artifact-upload/approval-route. V13 was scoped as pure frontend integration (all mechanisms it wires — V2/V3/V9/V10/V11 — already existed on the backend); no `Comment` entity, table, or endpoint exists anywhere | SUPERSEDED | *(was: scoped out of V13 entirely, "not silently faked with client-only state")* — held for V13, but revisited at Q53 for the V18 console visual-rework | Q53, SLICES.md V13, V18 |
| Q53 | Q52 held the line against faking comment threads with client-only state. The V18 console visual-rework (matching `ui-reference/`'s Discussion panel, Blog comments, notifications, and favourites — none backed by a real data model) raised the same question again for those four surfaces | DECIDED | Cross it, deliberately, for demo/visual fidelity: build the Discussion thread (todo sub-steps), Blog post comments, notifications, and favourites/starring with local-only, non-persistent client state, so the console visually matches `ui-reference/` end to end. Each gets a tracked backend follow-up so the gap isn't silently forgotten — issues #57 (todo comment threads), #58 (blog comments), #59 (notifications), #60 (favourites), all logged on the QMS Incub GitHub Projects board rather than built now | SLICES.md V18, GitHub issues #57–#60 |

## Coverage

| Category | Covered by |
|----------|-----------|
| Primary user and actors | Q1 |
| Scope boundary | Q2, Q3, Q16, Q17, Q18, Q19, Q20, Q21, Q38, Q40, Q43, Q52, Q53 |
| Data model and identity | Q22, Q30, Q31, Q32, Q33, Q41, Q42 |
| State and storage | Q23 |
| Concurrency and conflict | Q13, Q24 |
| Interfaces and contracts | Q25, Q30 |
| Failure behaviour | Q26 |
| External dependencies | Q11, Q14, Q35, Q36, Q37, Q39, Q44 |
| Runtime and deployment | Q5, Q34 |
| Measurable success | Q29 |
| Security and secrets | Q27 |
| Versioning and migration | Q28 |
| Agents, MCP, CLI, and identity (next milestone) | Q45, Q46, Q47, Q48, Q49, Q50 |
