"""Shared filesystem paths, gitignored (backend/var/)."""

from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOADED_DOCUMENTS_DIR = BACKEND_ROOT / "var" / "documents"
AOR_ROUTING_DIR = BACKEND_ROOT / "var" / "aor-routing"
AOR_REFERENCE_DIR = BACKEND_ROOT / "resources" / "aor-routing"
AOR_UPLOADS_DIR = AOR_ROUTING_DIR / "uploads"
UPLOADED_ARTIFACTS_DIR = BACKEND_ROOT / "var" / "artifacts"
