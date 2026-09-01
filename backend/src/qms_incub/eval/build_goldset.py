"""Build the retrieval gold set from the synthetic-corpus Q&A markdown.

The source of truth is ``synthetic-corpus/rag_policy_compliance_qa.md`` (110
Q&A pairs). This script turns each pair into a graded relevance judgement
over the chunks that are *actually ingested in Qdrant*, and writes:

- ``backend/evals/retrieval_goldset.json`` — the gold set the eval harness
  loads. Relevance is keyed ``"<document_title>::<chunk_index>"`` (both
  stable across re-ingestion, unlike the per-upload ``document_id``).
- ``backend/evals/chunk_map.json`` — an audit trail: for every policy,
  which chunk_index each section resolved to, and anything that didn't
  resolve. Not consumed by the harness; kept so the mapping is reviewable.

How a Q&A pair maps to chunks:

1. The ``### QA-xxx — §4.1; POL-006 §4.2`` header is the test-set author's
   own citation. Those ``(policy, section)`` pairs are the primary gold
   (grade 2 for the pair's own policy, grade 1 for a cross-referenced one).
2. Any ``POL-0NN`` named only in the Expected-answer prose is added as a
   grade-1 cross-reference, resolved to its best-overlapping chunk.
3. ``(policy, section) -> {chunk_index}`` alignment is by matching each
   section's source paragraphs (from ``synthetic-corpus/documents/POL-*.json``)
   against the ingested chunk text, plus a heading-scan fallback.

Run from ``backend/`` with Qdrant up (``make up``)::

    uv run python -m qms_incub.eval.build_goldset
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient

from qms_incub.config import settings

REPO_ROOT = Path(__file__).resolve().parents[4]
QA_MD = REPO_ROOT / "synthetic-corpus" / "rag_policy_compliance_qa.md"
DOCS_DIR = REPO_ROOT / "synthetic-corpus" / "documents"
EVALS_DIR = REPO_ROOT / "backend" / "evals"
GOLDSET_OUT = EVALS_DIR / "retrieval_goldset.json"
CHUNK_MAP_OUT = EVALS_DIR / "chunk_map.json"

GRADE_PRIMARY = 2
GRADE_XREF = 1

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


# --------------------------------------------------------------------------
# 1. Parse the Q&A markdown
# --------------------------------------------------------------------------


@dataclass
class QAPair:
    query_id: str
    primary_policy: str  # "POL-001"
    query: str
    expected: str
    difficulty: str
    guardrail: bool
    # (policy, section) citations parsed from the "### QA-xxx — ..." header
    header_refs: list[tuple[str, str]] = field(default_factory=list)
    # extra POL ids named only in the expected-answer prose
    prose_policies: list[str] = field(default_factory=list)


_POL_HEADING = re.compile(r"^##\s+(POL-\d{3})\s+—")
_QA_HEADING = re.compile(r"^###\s+(QA-\d{3})\s+—\s+(.*)$")
_FIELD = re.compile(
    r"^\*\*(Persona|Question|Expected answer|Policy artifacts/records|Difficulty|Tags):"
    r"\*\*\s*(.*)$"
)
_POL_ID = re.compile(r"POL-\d{3}")
_SECTION_TOKEN = re.compile(r"§\s*(\d+(?:\.\d+)?)")
_TABLE_TOKEN = re.compile(r"Table\s+(\d+)", re.IGNORECASE)


def _parse_header_refs(primary: str, header: str) -> list[tuple[str, str]]:
    """Parse '§4.2; POL-006 §4.2' -> [('POL-001','4.2'), ('POL-006','4.2')].

    A token naming a POL id attaches its section (or 'ALL') to that policy;
    a bare §x attaches to the pair's own policy. 'Table N' -> 'TableN'.
    """
    refs: list[tuple[str, str]] = []
    for raw in header.split(";"):
        tok = raw.strip()
        if not tok:
            continue
        pol_match = _POL_ID.search(tok)
        policy = pol_match.group(0) if pol_match else primary
        sec_match = _SECTION_TOKEN.search(tok)
        tbl_match = _TABLE_TOKEN.search(tok)
        if sec_match:
            refs.append((policy, sec_match.group(1)))
        elif tbl_match:
            refs.append((policy, f"Table{tbl_match.group(1)}"))
        elif pol_match:
            # e.g. "POL-001" with no section -> whole policy
            refs.append((policy, "ALL"))
    # de-dup, keep order
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def parse_qa_md(path: Path) -> list[QAPair]:
    pairs: list[QAPair] = []
    current_policy = ""
    cur: dict[str, str] | None = None
    cur_id = ""
    cur_header = ""

    def flush() -> None:
        nonlocal cur
        if cur is None:
            return
        difficulty = cur.get("Difficulty", "").strip()
        guardrail = difficulty == "unanswerable-detail"
        expected = cur.get("Expected answer", "").strip()
        header_refs = _parse_header_refs(current_policy, cur_header)
        prose_pols = sorted(
            {m for m in _POL_ID.findall(expected + " " + cur.get("Policy artifacts/records", ""))}
            - {current_policy}
            - {p for p, _ in header_refs}
        )
        pairs.append(
            QAPair(
                query_id=cur_id,
                primary_policy=current_policy,
                query=cur.get("Question", "").strip(),
                expected=expected,
                difficulty=difficulty,
                guardrail=guardrail,
                header_refs=header_refs,
                prose_policies=prose_pols,
            )
        )
        cur = None

    for line in path.read_text().splitlines():
        pol_h = _POL_HEADING.match(line)
        if pol_h:
            flush()
            current_policy = pol_h.group(1)
            continue
        qa_h = _QA_HEADING.match(line)
        if qa_h:
            flush()
            cur_id = qa_h.group(1)
            cur_header = qa_h.group(2).strip()
            cur = {}
            continue
        if cur is not None:
            fld = _FIELD.match(line.strip())
            if fld:
                cur[fld.group(1)] = fld.group(2)
    flush()
    return pairs


# --------------------------------------------------------------------------
# 2. Section -> source paragraphs, from the policy block-model JSON
# --------------------------------------------------------------------------

_SEC_NUM = re.compile(r"^(\d+(?:\.\d+)?)[.\s]")


def load_policy_sections(doc_id: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Returns (sections, table_to_section).

    sections: {'4.1': [para, ...], '2': [...], 'Table1': ['caption + cells']}
    table_to_section: {'Table2': '4.1'} — which section each table sits under.
    """
    blocks = json.loads((DOCS_DIR / f"{doc_id}.json").read_text())["blocks"]
    sections: dict[str, list[str]] = {}
    table_to_section: dict[str, str] = {}
    current = "0"
    for b in blocks:
        btype = b.get("type")
        if btype == "text" and b.get("style") in ("h1", "h2", "h3"):
            m = _SEC_NUM.match(b["content"].strip())
            current = m.group(1) if m else current
            continue
        if btype == "text":
            sections.setdefault(current, []).append(b["content"])
        elif btype == "table":
            cap = b.get("caption", "")
            tbl_m = _TABLE_TOKEN.search(cap)
            cells = " ".join(b.get("headers", []) + [c for row in b.get("rows", []) for c in row])
            blob = f"{cap} {cells}"
            sections.setdefault(current, []).append(blob)
            if tbl_m:
                key = f"Table{tbl_m.group(1)}"
                sections.setdefault(key, []).append(blob)
                table_to_section[key] = current
        elif btype == "swimlane":
            cap = b.get("caption", "")
            labels = " ".join(s.get("label", "") for s in b.get("steps", []))
            sections.setdefault(current, []).append(f"{cap} {labels}")
    return sections, table_to_section


# --------------------------------------------------------------------------
# 3. Load ingested chunks from Qdrant
# --------------------------------------------------------------------------


def load_chunks() -> dict[str, list[tuple[int, str]]]:
    """{'POL-001.pdf': [(0, text), (1, text), ...]} sorted by chunk_index."""
    client = QdrantClient(url=settings.qdrant_url)
    points, _ = client.scroll(
        settings.qdrant_collection, limit=10_000, with_payload=True, with_vectors=False
    )
    by_doc: dict[str, list[tuple[int, str]]] = {}
    for p in points:
        pl = p.payload or {}
        node = json.loads(pl["_node_content"])
        by_doc.setdefault(pl["qms_document_title"], []).append(
            (int(pl["chunk_index"]), node.get("text", ""))
        )
    for rows in by_doc.values():
        rows.sort()
    return by_doc


# --------------------------------------------------------------------------
# 4. Align (policy, section) -> {chunk_index}
# --------------------------------------------------------------------------


_CHUNK_HEADING = re.compile(r"#{1,4}\s*(\d+(?:\.\d+)?)[.\s]+[A-Z]")


def align_sections(chunks: list[tuple[int, str]]) -> dict[str, list[int]]:
    """Map each section number to the chunk(s) that contain its text.

    Driven by the ``## 4.1 ...`` headings Docling preserves in the chunk
    text, with carry-forward: a chunk that opens mid-prose (the usual case
    with SentenceSplitter) continues whatever section was open at the end
    of the previous chunk, so a section that straddles a chunk boundary is
    credited to both chunks.
    """
    covers: dict[str, set[int]] = {}
    open_sec: str | None = None
    for idx, text in chunks:  # chunks arrive sorted by chunk_index
        matches = list(_CHUNK_HEADING.finditer(text))
        # Carry the previous section into this chunk only if the chunk
        # actually opens with prose — a chunk that starts on a heading is a
        # fresh section, not a continuation.
        starts_fresh = bool(matches) and matches[0].start() < 60
        if open_sec is not None and not starts_fresh:
            covers.setdefault(open_sec, set()).add(idx)
        for m in matches:
            h = m.group(1)
            covers.setdefault(h, set()).add(idx)
            open_sec = h
    return {sec: sorted(idxs) for sec, idxs in covers.items()}


_STOP = set(
    "the a an and or of to for in on at by is are be as it its that this with which "
    "must should may not no any before after each every from than when who what".split()
)


def _overlap_best(text: str, chunks: list[tuple[int, str]], top: int = 2) -> list[int]:
    """Chunk indices sharing the most word trigrams with `text`; falls back
    to content-word overlap so short answers still resolve."""

    def trigrams(s: str) -> set[str]:
        w = _norm(s).split()
        return {" ".join(w[i : i + 3]) for i in range(len(w) - 2)}

    def words(s: str) -> set[str]:
        return {w for w in _norm(s).split() if w not in _STOP and len(w) > 2}

    tg, tw = trigrams(text), words(text)
    scored = sorted(
        (
            (len(tg & trigrams(c)) * 10 + len(tw & words(c)), idx)
            for idx, c in chunks
        ),
        reverse=True,
    )
    return [idx for score, idx in scored[:top] if score > 0]


# --------------------------------------------------------------------------
# 5. Assemble the gold set
# --------------------------------------------------------------------------


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    pairs = parse_qa_md(QA_MD)
    chunks_by_doc = load_chunks()
    known_titles = set(chunks_by_doc)

    loaded = {doc.stem: load_policy_sections(doc.stem) for doc in DOCS_DIR.glob("POL-*.json")}
    sections_by_pol = {p: s for p, (s, _) in loaded.items()}
    table_sec_by_pol = {p: t for p, (_, t) in loaded.items()}
    align_by_pol = {
        pol: align_sections(chunks_by_doc[f"{pol}.pdf"])
        for pol in sections_by_pol
        if f"{pol}.pdf" in chunks_by_doc
    }

    def sec_chunks(pol: str, sec: str) -> list[int]:
        """Resolve one (policy, section) citation to chunk indices."""
        align = align_by_pol.get(pol, {})
        if sec in align:
            return align[sec]
        # "Table2" -> the section that table sits under
        tbl_sec = table_sec_by_pol.get(pol, {}).get(sec)
        if tbl_sec and tbl_sec in align:
            return align[tbl_sec]
        # bare "§4" cross-ref -> the whole procedure (all 4.x chunks)
        if sec in {"4", "ALL"}:
            wide = sorted({i for s, idxs in align.items() if s.startswith("4") for i in idxs})
            if wide:
                return wide
        return []

    chunk_map = {
        pol: {
            "chunk_count": len(chunks_by_doc[f"{pol}.pdf"]),
            "section_to_chunks": align_by_pol[pol],
            "unresolved_sections": sorted(
                s
                for s in sections_by_pol[pol]
                if s not in align_by_pol[pol]
                and not s.startswith("Table")
                and s != "0"
            ),
        }
        for pol in align_by_pol
    }

    queries = []
    problems: list[str] = []
    for qa in pairs:
        relevant: dict[str, int] = {}

        def add(pol: str, idxs: list[int], grade: int) -> None:
            title = f"{pol}.pdf"
            if title not in known_titles:
                problems.append(f"{qa.query_id}: {title} not ingested")
                return
            for i in idxs:
                key = f"{title}::{i}"
                relevant[key] = max(relevant.get(key, 0), grade)

        for pol, sec in qa.header_refs:
            grade = GRADE_PRIMARY if pol == qa.primary_policy else GRADE_XREF
            idxs = sec_chunks(pol, sec)
            if idxs:
                add(pol, idxs, grade)
            else:
                add(pol, _overlap_best(qa.expected, chunks_by_doc[f"{pol}.pdf"]), grade)
                problems.append(f"{qa.query_id}: {pol} §{sec} unresolved, used overlap fallback")

        # A POL id named only in the answer prose is a real cross-reference
        # for genuinely multi-document questions; for 'direct' questions the
        # header citation is the whole answer, so skip the prose sweep.
        if qa.difficulty in {"multi-hop", "edge-case"}:
            for pol in qa.prose_policies:
                if f"{pol}.pdf" in known_titles:
                    best = _overlap_best(qa.expected, chunks_by_doc[f"{pol}.pdf"], top=1)
                    add(pol, best, GRADE_XREF)

        if not relevant:
            add(
                qa.primary_policy,
                _overlap_best(
                    qa.expected or qa.query, chunks_by_doc[f"{qa.primary_policy}.pdf"]
                ),
                GRADE_PRIMARY,
            )
            problems.append(f"{qa.query_id}: no citations resolved, used expected-answer overlap")

        if not relevant:
            problems.append(f"{qa.query_id}: STILL EMPTY")

        queries.append(
            {
                "query_id": qa.query_id,
                "query": qa.query,
                "difficulty": qa.difficulty,
                "guardrail": qa.guardrail,
                "primary_policy": qa.primary_policy,
                "sections": [f"{p} §{s}" for p, s in qa.header_refs],
                "relevant": relevant,
                "relevant_documents": sorted({k.split("::")[0] for k in relevant}),
            }
        )

    goldset: dict[str, Any] = {
        "meta": {
            "source": "synthetic-corpus/rag_policy_compliance_qa.md",
            "collection": settings.qdrant_collection,
            "relevance_key": "document_title::chunk_index",
            "grades": {"primary": GRADE_PRIMARY, "cross_reference": GRADE_XREF},
            "counts": {
                "total": len(queries),
                "answerable": sum(1 for q in queries if not q["guardrail"]),
                "guardrail": sum(1 for q in queries if q["guardrail"]),
            },
        },
        "queries": queries,
    }
    goldset["meta"]["build_problems"] = problems
    return goldset, chunk_map


def main() -> int:
    goldset, chunk_map = build()
    EVALS_DIR.mkdir(parents=True, exist_ok=True)
    GOLDSET_OUT.write_text(json.dumps(goldset, indent=2) + "\n")
    CHUNK_MAP_OUT.write_text(json.dumps(chunk_map, indent=2) + "\n")

    m = goldset["meta"]["counts"]
    print(f"wrote {GOLDSET_OUT.relative_to(REPO_ROOT)}")
    print(f"  queries: {m['total']}  (answerable {m['answerable']}, guardrail {m['guardrail']})")
    empties = [q["query_id"] for q in goldset["queries"] if not q["relevant"]]
    print(f"  queries with 0 gold chunks: {len(empties)} {empties or ''}")
    gsz = [len(q["relevant"]) for q in goldset["queries"]]
    print(f"  gold chunks/query: min {min(gsz)}  max {max(gsz)}  mean {sum(gsz) / len(gsz):.1f}")
    probs = goldset["meta"]["build_problems"]
    print(f"  build problems: {len(probs)}")
    for p in probs:
        print(f"    - {p}")
    print(f"wrote {CHUNK_MAP_OUT.relative_to(REPO_ROOT)}")
    for pol, info in sorted(chunk_map.items()):
        if info["unresolved_sections"]:
            print(f"  {pol}: unresolved sections {info['unresolved_sections']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
