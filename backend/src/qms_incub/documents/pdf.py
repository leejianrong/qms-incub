"""HTML -> PDF export via WeasyPrint (ADR-0010, resolves Q35)."""

from __future__ import annotations

from weasyprint import HTML


def html_to_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()  # type: ignore[no-any-return]
