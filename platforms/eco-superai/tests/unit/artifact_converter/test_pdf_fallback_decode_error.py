"""Cover pdf_parser.py lines 125-126: fallback decode exception handler."""
from __future__ import annotations

from pathlib import Path


class TestPdfFallbackDecodeError:
    """Cover lines 125-126: _parse_fallback catches decode exception."""

    def test_parse_fallback_decode_exception(self):
        """Lines 125-126 – _parse_fallback catches exception from content.decode."""
        from src.artifact_converter.parsers.pdf_parser import PdfParser

        class _BadBytes:
            """Bytes-like object whose decode() always raises."""

            def decode(self, encoding: str) -> str:
                raise UnicodeDecodeError(encoding, b"", 0, 1, "test decode error")

        result = PdfParser._parse_fallback(_BadBytes(), Path("test.pdf"))

        # Should return a ParseResult with empty body (decode failed)
        assert result.metadata.get("_fallback") is True
        assert result.body == ""
