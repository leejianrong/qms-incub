# AOR routing: R&T or SSD

This feature classifies an uploaded AOR against two labeled reference
descriptions using the backend's existing local embedding model. It does not
add the AOR to the policy/chat corpus and does not require an LLM, Qdrant, or
PostgreSQL.

## File layout

The synthetic reference descriptions and demo PDFs are committed so every
developer can run the same classifier check:

```text
backend/
├── resources/aor-routing/
│   ├── rt.txt
│   └── ssd.txt
├── tests/fixtures/aor-routing/
│   ├── demo_rt.pdf
│   └── demo_ssd.pdf
└── var/aor-routing/uploads/ # Real API uploads; gitignored
```

The `.txt` files are labeled reference prose, not serialized numeric
embeddings. The application embeds them with `BAAI/bge-small-en-v1.5`, the same
model already used by the RAG pipeline. Only synthetic AORs belong in test
fixtures; real API uploads remain under the gitignored `backend/var/` tree.

## Test without the UI

From `backend/`, classify one or more files directly:

```bash
uv run python scripts/classify_aor.py \
  tests/fixtures/aor-routing/demo_rt.pdf \
  tests/fixtures/aor-routing/demo_ssd.pdf
```

The first run may download Docling/OCR and Hugging Face model files. Later runs
reuse the local model cache.

To test through HTTP, start the app with `make up`, then run from the repository
root:

```bash
curl -sS -F "file=@backend/tests/fixtures/aor-routing/demo_rt.pdf" \
  http://localhost:8000/aor/classify
```

The JSON response contains the selected `route`, both similarity `scores`, a
heuristic `confidence`, an evidence excerpt, and `needs_review`. A close score
margin sets `needs_review` to `true`; that result should not be auto-routed.

The current threshold is an initial engineering default. Calibrate it against a
larger labeled AOR set before relying on unattended production routing.
