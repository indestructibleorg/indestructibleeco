"""PDF parser with graceful fallback.

Uses ``pdfplumber`` when available; otherwise falls back to a best-effort
binary-text extraction that warns the user about reduced fidelity.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import structlog

from . import BaseParser, ParseResult

logger = structlog.get_logger(__name__)

try:
    import pdfplumber  # type: ignore[import-untyped]

    _HAS_PDFPLUMBER = True
except ImportError:  # pragma: no cover
    _HAS_PDFPLUMBER = False
    logger.info(
        "pdfplumber_not_installed",
        hint="Install pdfplumber for full PDF support: pip install pdfplumber",
    )


class PdfParser(BaseParser):
    """Parser for PDF documents.

    Falls back gracefully when ``pdfplumber`` is not installed.
    """

    def parse(self, content: str | bytes, source_path: Path | None = None) -> ParseResult:
        if isinstance(content, str):
            # Caller already read the file as text -- unusual for PDFs but we handle it
            logger.warning("pdf_received_text_content", source=str(source_path))
            return ParseResult(body=content, raw=content)

        if _HAS_PDFPLUMBER:
            return self._parse_with_pdfplumber(content, source_path)

        return self._parse_fallback(content, source_path)

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    # ------------------------------------------------------------------
    # pdfplumber-based extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_with_pdfplumber(
        content: bytes, source_path: Path | None
    ) -> ParseResult:
        import io

        logger.debug("pdf_pdfplumber_start", source=str(source_path))

        pages_text: list[str] = []
        metadata: dict[str, Any] = {}
        sections: list[dict[str, Any]] = []

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            # Extract document-level metadata
            if pdf.metadata:
                for key in ("Title", "Author", "Subject", "Creator", "Producer"):
                    val = pdf.metadata.get(key)
                    if val:
                        metadata[key.lower()] = val
                if pdf.metadata.get("CreationDate"):
                    metadata["date"] = pdf.metadata["CreationDate"]

            metadata["page_count"] = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages_text.append(text)
                sections.append({
                    "heading": f"Page {i + 1}",
                    "content": text.strip(),
                })

        body = "\n\n".join(pages_text)
        logger.debug(
            "pdf_pdfplumber_done",
            pages=len(pages_text),
            chars=len(body),
        )

        return ParseResult(
            body=body.strip(),
            metadata=metadata,
            sections=sections,
            raw=body,
        )

    # ------------------------------------------------------------------
    # Fallback extraction (no pdfplumber)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_fallback(content: bytes, source_path: Path | None) -> ParseResult:
        logger.warning(
            "pdf_fallback_extraction",
            hint="Install pdfplumber for accurate PDF parsing.",
            source=str(source_path),
        )

        # Best-effort: extract readable ASCII/UTF-8 strings from the binary
        # This is obviously lossy but provides *something* when pdfplumber
        # is missing.
        text_fragments: list[str] = []
        try:
            decoded = content.decode("latin-1")
            # Extract parenthesised text strings (PDF literal strings)
            for match in re.finditer(r"\(([^)]{2,})\)", decoded):
                fragment = match.group(1)
                # Filter out binary noise
                if fragment.isprintable() and len(fragment.strip()) > 1:
                    text_fragments.append(fragment.strip())
        except Exception:
            logger.warning("pdf_fallback_decode_failed", source=str(source_path))

        body = "\n".join(text_fragments)
        return ParseResult(
            body=body,
            metadata={"_fallback": True, "_warning": "pdfplumber not installed; text is approximate"},
            sections=[{"heading": "", "content": body}] if body else [],
            raw=body,
        )
