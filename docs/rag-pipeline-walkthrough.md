# How the RAG pipeline actually works

This is a walkthrough for anyone new to the repo who wants to understand what
happens between "there's a PDF" and "the chat panel answers a question about
it," in enough detail to actually work on the pipeline rather than just run
it. It covers three stages: generating test PDFs, ingesting them, and
retrieving from them. For how to spin up the app and run any of this
yourself, see the [root README](../README.md).

## Why there's a synthetic corpus at all

The backend never authors or generates document content (ADR-0012). It only
ingests and chats over documents someone gives it, and there's no real QMS
content lying around that's safe to test with. So `synthetic-corpus/` exists
as a separate tool that manufactures a small, fixed set of realistic
QMS-policy-shaped PDFs on disk. It shares no code with `backend/` and never
calls it over HTTP: its job stops the moment the PDFs exist.

## Stage 1: generating the PDFs

The actual ground truth for the corpus lives as JSON, not PDF. Each of the
ten documents is a block-model file at `synthetic-corpus/documents/POL-*.json`,
built from prose, table, and diagram blocks. Two more files give it shape:
`corpus-plan.json` decides up front which documents cross-reference which
(so citations across documents are correct by construction, not by luck),
and `domain-profile.json` sets the business domain the corpus is themed
around: roles, policy topics, standards bodies to cite.

```bash
cd synthetic-corpus
uv sync
uv run python scripts/generate.py
```

This reads the JSON and renders each document to `output/POL-*.pdf`. That
output directory is gitignored on purpose: nothing about the PDFs needs to
be byte-identical across runs, since they're always regenerated from the
committed JSON.

The one design choice worth understanding here: generation deliberately goes
*through* a rendered PDF rather than handing the block-model JSON straight to
the ingestion pipeline. If it skipped the PDF, it would only ever test
whether the backend can chunk and embed clean, pre-structured text, which
is the easy case. Going through a real PDF forces the same render, then
Docling re-extract round trip that a real uploaded policy document would go
through, so table and diagram content actually has to survive it. That's
the fidelity risk the project cares about, and skipping the PDF step would
quietly stop testing it.

## Stage 2: ingesting into Qdrant

`POST /documents` is the only way a document enters the corpus (ADR-0012).
It's a synchronous multipart upload, and every PDF in `synthetic-corpus/output/`
goes through it the same way a real policy document would:

```bash
for f in synthetic-corpus/output/POL-*.pdf; do
  curl -sf -F "file=@$f" http://localhost:8000/documents
done
```

Behind that endpoint, `ingestion/pipeline.py` does four things, in order:

1. **Parse.** Docling extracts text from the PDF (`docling_parse.py`), not
   from the original JSON. This is the point where a poorly-surviving table
   or diagram would show up as garbled or missing text.
2. **Chunk.** The extracted text is split into passages (`chunking.py`, a
   LlamaIndex `SentenceSplitter` under the hood).
3. **Embed.** Each chunk is embedded via whichever provider `EMBEDDING_PROVIDER`
   names (`rag_clients.py`): `local` (default) runs a HuggingFace model,
   `BAAI/bge-small-en-v1.5`, in-process — no API key, this step never leaves
   the machine. `openrouter`/`zenmux` instead call a hosted OpenAI-compatible
   `/embeddings` endpoint, for a machine you'd rather not run a local model on.
4. **Store.** Each chunk becomes a `TextNode` in Qdrant's `qms_incub_corpus`
   collection, carrying `qms_document_id`, `qms_document_title`,
   `source_type`, and `chunk_index` as metadata. That metadata is what makes
   citations possible later.

One detail that matters if you're going to re-run ingestion repeatedly,
which `rag-eval/` (below) does: it's idempotent per `document_id`.
Re-ingesting the same ID deletes its existing chunks first, so running the
upload loop twice doesn't leave duplicate vectors sitting in Qdrant.
`GET /documents` lists every document's ingestion status and chunk count,
which is the quickest way to confirm all ten landed before querying
anything.

## Stage 3: retrieval and chat

`POST /chat` takes a `{"question": "..."}` body and walks through four
files in `backend/src/qms_incub/chat/`:

- **`retrieval.py`** fetches candidates via `RETRIEVAL_MODE` — `bm25`
  (sparse lexical, the default) or `vector` (dense similarity, embedding the
  question with the same embedding provider used at ingestion time) —
  against the same Qdrant collection either way, then optionally reranks
  (`rerank.py`, `RERANKER_PROVIDER`) down to the requested top-k (four by
  default). Each result comes back as a `RetrievedChunk`: text, document id
  and title, source type, and a score.
- **`prompt.py`** builds the messages sent to the model. The system prompt
  is deliberately narrow: answer only from the context given, and say you
  don't know rather than guess if the answer isn't there.
- **`llm.py`** makes the actual call. The provider is swappable through
  `LLM_PROVIDER` in `backend/.env`: `ollama` for local, free dev and
  testing, `openrouter` as the project's decided default (ADR-0003), or
  `zenmux` during its current promotional window. All three speak the same
  OpenAI-compatible API, so one client handles all of them.
- **`service.py`** expands each retrieved chunk's source document to its
  full text (rather than handing the model only the matched passages —
  retrieval picks *which documents* are relevant, not which excerpts),
  then assembles the final answer.

The detail that matters most if you're building anything that grades this
pipeline's output: citations are derived from the chunks that were actually
retrieved, not parsed out of whatever the model wrote in its answer. That
means citation accuracy doesn't depend on the model reliably following a
citation format. A weaker or differently-prompted model can still produce
answers whose citations are correct, because the citations never came from
the model in the first place.

## Scoring retrieval quality: `rag-eval/`

Once the corpus above is ingested, `rag-eval/` (a standalone tool at the
repo root, not part of `backend/`) scores retrieval against a 110-question
gold set derived from `synthetic-corpus/rag_policy_compliance_qa.md`:

```bash
cd rag-eval
uv run python -m rag_eval.build_goldset   # (re)build the gold set, if the corpus/chunking changed
uv run python -m rag_eval                 # score retrieval: NDCG@k, Recall@k, MRR
```

It depends on `qms_incub` (a local `uv` path dependency on `backend/`) so
it scores the real `RetrievalPort` implementation rather than a copy —
unlike `synthetic-corpus/`, which shares no code with the backend at all.

## Where to look next

The files named above are the real source of truth; this document is meant
to orient you before you go read them, not replace them. For a working set
of test questions and the last manual run against them, including one
question that specifically requires pulling from two different documents,
see
[`docs/shaping/synthetic-doc-realism/RAG-SPOT-CHECK.md`](shaping/synthetic-doc-realism/RAG-SPOT-CHECK.md).
