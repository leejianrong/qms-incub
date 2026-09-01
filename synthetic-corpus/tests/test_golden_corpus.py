"""Slice 4 test plan: the CLI reports 10/10 documents rendered with no
failures, and the C5 regression test — every cross-reference string in the
golden set resolves to a real doc ID from the corpus plan, and every
cross-reference declared in corpus-plan.json is actually cited in that
document's prose."""

from __future__ import annotations

import re
from pathlib import Path

import pypdf

from synthetic_corpus.cli import generate_all
from synthetic_corpus.corpus_plan import load_corpus_plan

_REPO_ROOT = Path(__file__).parent.parent
_DOCUMENTS_DIR = _REPO_ROOT / "documents"
_DOC_ID_PATTERN = re.compile(r"POL-\d{3}")
_EXPECTED_DOCUMENT_COUNT = 10


def test_ten_of_ten_golden_documents_render_in_page_range(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    output_paths = generate_all(documents_dir=_DOCUMENTS_DIR, output_dir=output_dir)

    assert len(output_paths) == _EXPECTED_DOCUMENT_COUNT
    for output_path in output_paths:
        page_count = len(pypdf.PdfReader(str(output_path)).pages)
        assert 5 <= page_count <= 15, f"{output_path.name}: {page_count} pages, expected 5-15"


def test_every_cross_reference_string_resolves_to_a_real_doc_id() -> None:
    plan = load_corpus_plan(_REPO_ROOT / "corpus-plan.json")
    known_ids = {entry.doc_id for entry in plan.entries}

    for fixture_path in sorted(_DOCUMENTS_DIR.glob("*.json")):
        text = fixture_path.read_text()
        found_ids = set(_DOC_ID_PATTERN.findall(text))
        unknown = found_ids - known_ids
        assert not unknown, f"{fixture_path.name} cites unknown doc ID(s): {sorted(unknown)}"


def test_every_planned_cross_reference_is_cited_in_its_documents_prose() -> None:
    plan = load_corpus_plan(_REPO_ROOT / "corpus-plan.json")

    for entry in plan.entries:
        fixture_path = _DOCUMENTS_DIR / f"{entry.doc_id}.json"
        assert fixture_path.exists(), f"no fixture for planned doc {entry.doc_id!r}"
        text = fixture_path.read_text()
        for referenced_id in entry.cross_references:
            assert referenced_id in text, (
                f"{entry.doc_id} is planned to cross-reference {referenced_id} "
                f"(corpus-plan.json) but its prose never mentions it"
            )
