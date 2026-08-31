# ADR-0010: PDF export renders via WeasyPrint (resolves Q35)

- Status: Accepted
- Date: 2026-08-31
- Deciders: agent (V1 RAG spike slice), leejianrong (owns this slice)

## Context

ADR-0005 originally picked Puppeteer for HTML-to-PDF export; ADR-0009
dropped Puppeteer as Node-only once the backend became Python, and left
the replacement as an open follow-up (Q35 in QUESTIONS.md), naming
WeasyPrint and Playwright's Python bindings as candidates. V1 (the RAG
spike, SLICES.md) needs this resolved to export its seeded document
(text + table + flowchart-as-SVG blocks) to PDF before ingestion.

The document engine (ADR-0001) renders structured blocks — not arbitrary
web pages — to HTML, and flowchart blocks are pre-rendered to inline SVG
server-side (ADR-0006) before the PDF export step ever runs. So the PDF
step needs solid static HTML/CSS/SVG-embedding support, not JS execution
or pixel-perfect browser rendering. V5's synthetic batch generation
(SLICES.md) will also call this same export path N times per batch run,
so process weight and startup cost per document matter.

## Decision

Use WeasyPrint (pure Python, BSD-licensed) for HTML-to-PDF export. The
render pipeline stays: blocks → HTML (server-rendered, flowchart blocks
already resolved to inline SVG) → WeasyPrint → PDF. No browser process,
no JS execution, no browser binary download.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Playwright (Python bindings) | Full Chromium gives pixel-perfect rendering the block model doesn't need (no JS, no complex layout); requires downloading and managing browser binaries (~300MB+), which adds a heavier, flakier dependency to `make up` (ADR-0009 already flagged the local stack's growing service count) and to V5's batch generation (spinning up a browser context per document is slower and more resource-hungry than a pure-Python render call) |
| Puppeteer | Node-only; the whole point of Q35 is that the backend is now Python (ADR-0009) |
| wkhtmltopdf | Unmaintained upstream, weaker modern-CSS support than WeasyPrint, no clear advantage for this use case |

## Consequences

Gains: no browser subprocess to manage or fail; fast, deterministic
renders suited to V5's batch mode; pure-Python dependency fits the rest
of the backend stack. Costs: WeasyPrint's CSS support, while solid for
document-style layouts (this project's actual need), is not a full
browser engine — no JS, and some modern CSS layout features lag behind
Chromium. Not a concern for block-model output (text/table/flowchart-SVG/
image), which is intentionally simple, structured layout (ADR-0001).
Forecloses: nothing structural — swapping the PDF library later only
touches S4's implementation (PLAN.md's own assessment of Q35's risk),
not the block model or the render pipeline's shape.
