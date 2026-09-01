---
shaping: true
---

# Manual RAG Effectiveness Spot-Check — Results

See [SLICES.md](./SLICES.md#slice-5-manual-rag-effectiveness-spot-check) for
what this covers (C8) and why it's a documented procedure rather than code
this tool ships — qualitative, not a scored benchmark (QUESTIONS.md Q19
stays deferred).

## Procedure

1. `make up` (or start Postgres/Qdrant + the backend directly) so `POST
   /documents` and `POST /chat` are live.
2. Upload all 10 rendered PDFs from `synthetic-corpus/output/` (run
   `synthetic-corpus`'s CLI first if `output/` is empty:
   `uv run python scripts/generate.py`):
   ```
   for f in synthetic-corpus/output/POL-*.pdf; do
     curl -sf -F "file=@$f" http://localhost:8000/documents
   done
   ```
3. Ask `/chat` a fixed list of questions (below), including several that
   require following a cross-reference from one document to another, and
   check each answer and its citations by hand.

## Run performed

- Date: 2026-09-01.
- LLM provider: Ollama (`qwen2.5:7b-instruct-q4_K_M`), not OpenRouter — a
  free/local run costs nothing and is sufficient for a qualitative check.
- All 10 PDFs uploaded via `POST /documents`; all reached `status:
  "embedded"` (4-5 chunks each).

## Question list and results

| # | Question | Verdict | Notes |
|---|----------|:-------:|-------|
| 1 | What is the standard review cadence for access grants under the Access Control and Least Privilege Policy? | ✅ | Correct: quarterly. Cited POL-006 plus some retrieval noise (POL-003, POL-010) that didn't affect the answer. |
| 2 | According to the Software Change Management Policy, what must happen to an emergency change made during an active incident? | ✅ | Correct, matches POL-001 verbatim: logged retroactively within one business day, reviewed by CAB at next session. |
| 3 | Which policy governs service account credentials, and how often must production-write service accounts rotate? | ✅ | Correct: POL-006, every 90 days. |
| 4 | **(cross-reference)** If a change requires provisioning access to a system storing Confidential data, which policies apply and what does each require? | ✅ | Correctly synthesized POL-006 (access control, least privilege, elevated approval chain §4.2) *and* POL-007 (Confidential classification, encryption at rest/in transit) in one answer — the target multi-hop case. |
| 5 | **(cross-reference)** Under Access Control, what additional approval is required for Confidential/Restricted data per Data Classification? | ✅ | Correct: elevated approval chain, POL-006 §4.2, tied back to POL-007's classification. |
| 6 | What triggers Business Continuity/DR plan activation, and who declares a DR event? | ✅ | Correct and detailed: on-call responder escalates a Tier-1/region-level disruption; Incident Commander declares the DR event (POL-009). |
| 7 | **(cross-reference)** Per Vendor and Third-Party Risk Management, which other policy governs data classification for vendor access? | ✅ | Correct: POL-007. |
| 8 | **(cross-reference)** Per Code Review and Change Management, what must be true about code changes before a change request reaches the CAB? | 🟡 | Substantively correct (must pass review + quality gates) but generic — didn't explicitly name-check POL-003 in the answer text the way POL-001's source prose does. Citations were still correct (POL-001, POL-003). |
| 9 | **(negative control)** What is the company's policy on remote work stipends? | ✅ | Correctly answered "I don't know" — no hallucination on a question the corpus doesn't cover. |
| 10 | **(cross-reference)** Per IT Onboarding/Offboarding, who provisions new-employee access, and which other policy governs its scope? | ✅ | Correct: IT Support Analyst; scope governed by POL-006 §4. |

## Verdict

9/10 fully correct with accurate citations, including four genuine
cross-document questions (#4, #5, #7, #10) answered by combining retrieved
chunks from two different policies rather than just one — the original
motivating question ("does retrieval actually follow a cross-reference from
one document to another") checks out. One answer (#8) was correct in
substance but less precise than the source text. The negative-control
question (#9) correctly declined rather than hallucinating.

This was run against a free local model (Ollama); an OpenRouter run would
likely sharpen #8's precision further, but wasn't necessary to reach a
verdict here — retrieval, not generation quality, was what this slice set
out to judge.
