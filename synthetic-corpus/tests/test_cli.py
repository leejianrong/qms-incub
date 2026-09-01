"""Slice 2 test plan: loading a fixture round-trips through render -> export
and produces a valid, non-empty PDF; a fixture missing a required field
fails loudly rather than being silently skipped."""

from __future__ import annotations

import json
from pathlib import Path

import pypdf
import pytest
from pydantic import ValidationError

from synthetic_corpus.cli import generate_all

_VALID_FIXTURE = {
    "meta": {"doc_id": "TEST-001", "title": "Test Document"},
    "blocks": [{"type": "text", "style": "h1", "content": "Hello"}],
}


def test_generate_all_round_trips_a_fixture_to_a_valid_pdf(tmp_path: Path) -> None:
    documents_dir = tmp_path / "documents"
    output_dir = tmp_path / "output"
    documents_dir.mkdir()
    (documents_dir / "test-001.json").write_text(json.dumps(_VALID_FIXTURE))

    output_paths = generate_all(documents_dir=documents_dir, output_dir=output_dir)

    assert output_paths == [output_dir / "TEST-001.pdf"]
    assert output_paths[0].exists()
    assert output_paths[0].stat().st_size > 0
    reader = pypdf.PdfReader(str(output_paths[0]))
    assert len(reader.pages) >= 1


def test_generate_all_fails_loudly_on_a_fixture_missing_a_required_field(tmp_path: Path) -> None:
    documents_dir = tmp_path / "documents"
    output_dir = tmp_path / "output"
    documents_dir.mkdir()
    invalid_fixture = {"meta": {"doc_id": "TEST-002"}}  # missing required "blocks"
    (documents_dir / "test-002.json").write_text(json.dumps(invalid_fixture))

    with pytest.raises(ValidationError, match="blocks"):
        generate_all(documents_dir=documents_dir, output_dir=output_dir)

    assert not output_dir.exists() or list(output_dir.iterdir()) == []
