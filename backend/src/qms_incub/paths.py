"""Shared filesystem paths, gitignored (backend/var/)."""

from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOADED_DOCUMENTS_DIR = BACKEND_ROOT / "var" / "documents"
