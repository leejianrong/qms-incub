"""CLI entry point (SLICES.md Slice 2): loads block-model JSON fixtures from
`documents/*.json`, renders them, and writes PDFs to `output/`. Nothing
else — no ingestion, no network call, no dependency on the backend being up
or even installed (ADR-0012).
"""

from __future__ import annotations

from pathlib import Path

from synthetic_corpus.blocks import Document
from synthetic_corpus.render.document import export_document_pdf

_REPO_ROOT = Path(__file__).parent.parent.parent
_DOCUMENTS_DIR = _REPO_ROOT / "documents"
_OUTPUT_DIR = _REPO_ROOT / "output"


def generate_all(
    documents_dir: Path = _DOCUMENTS_DIR, output_dir: Path = _OUTPUT_DIR
) -> list[Path]:
    """Render every `*.json` fixture in `documents_dir` to a PDF in
    `output_dir`. A fixture that fails Document validation raises
    `pydantic.ValidationError` immediately — a bad fixture must fail loudly,
    never be silently skipped."""
    output_paths = []
    for fixture_path in sorted(documents_dir.glob("*.json")):
        document = Document.model_validate_json(fixture_path.read_text())
        output_path = output_dir / f"{document.meta.doc_id}.pdf"
        export_document_pdf(document, output_path)
        print(f"{fixture_path.name} -> {output_path}")
        output_paths.append(output_path)
    return output_paths


def main() -> int:
    output_paths = generate_all()
    print(f"rendered {len(output_paths)} document(s) to {_OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
