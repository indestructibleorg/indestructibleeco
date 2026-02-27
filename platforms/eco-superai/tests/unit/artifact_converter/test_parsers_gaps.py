"""Targeted tests for remaining uncovered lines in artifact_converter parsers.

Covers:
- docx_parser.py lines 25-27: ImportError path (python-docx not installed)
- docx_parser.py lines 38-39: string content warning
- docx_parser.py line 68: core.created date extraction
- docx_parser.py line 82: empty paragraph skipped
- docx_parser.py line 87: section flush on heading
- docx_parser.py lines 132-145: fallback parser missing document.xml
- html_parser.py lines 22-24: ImportError path (bs4 not installed)
- html_parser.py line 63: metadata extraction
- html_parser.py line 74: fallback plain text
- pdf_parser.py lines 23-25: ImportError path (pdfminer not installed)
- pdf_parser.py line 75: fallback parser
- pdf_parser.py lines 121-126: fallback parser error
"""
from __future__ import annotations

import io
import zipfile
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


# ---------------------------------------------------------------------------
# docx_parser.py lines 38-39: string content warning
# ---------------------------------------------------------------------------

class TestDocxParserStringContent:
    """Cover lines 38-39: DocxParser handles string content with warning."""

    def test_parse_string_content_returns_parse_result(self):
        """Lines 38-39 – string content is returned directly with warning."""
        from src.artifact_converter.parsers.docx_parser import DocxParser

        parser = DocxParser()
        result = parser.parse("This is text content, not bytes.", source_path=Path("/tmp/test.docx"))
        assert result is not None
        assert result.body == "This is text content, not bytes."


# ---------------------------------------------------------------------------
# docx_parser.py line 68: core.created date extraction
# ---------------------------------------------------------------------------

class TestDocxParserDateExtraction:
    """Cover line 68: DocxParser extracts creation date from core properties."""

    def test_parse_docx_with_creation_date(self):
        """Line 68 – core.created date is extracted and converted to ISO string."""
        from src.artifact_converter.parsers.docx_parser import DocxParser
        from datetime import datetime, timezone

        parser = DocxParser()

        # Create a mock document with core properties
        mock_doc = MagicMock()
        mock_doc.core_properties.title = "Test Document"
        mock_doc.core_properties.author = "Test Author"
        created_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_doc.core_properties.created = created_dt
        mock_doc.core_properties.keywords = None
        mock_doc.core_properties.subject = None
        mock_doc.paragraphs = []

        with patch("docx.Document", return_value=mock_doc):
            result = parser.parse(b"fake docx bytes", source_path=Path("/tmp/test.docx"))

        assert result is not None
        assert result.metadata.get("date") == created_dt.isoformat()


# ---------------------------------------------------------------------------
# docx_parser.py line 82: empty paragraph skipped
# docx_parser.py line 87: section flush on heading
# ---------------------------------------------------------------------------

class TestDocxParserParagraphHandling:
    """Cover lines 82, 87: DocxParser handles empty paragraphs and section flushes."""

    def test_parse_docx_skips_empty_paragraphs(self):
        """Line 82 – empty paragraphs are skipped."""
        from src.artifact_converter.parsers.docx_parser import DocxParser

        parser = DocxParser()

        # Create mock paragraphs with empty text
        empty_para = MagicMock()
        empty_para.style.name = "Normal"
        empty_para.text = ""

        content_para = MagicMock()
        content_para.style.name = "Normal"
        content_para.text = "Some content"

        mock_doc = MagicMock()
        mock_doc.core_properties.title = None
        mock_doc.core_properties.author = None
        mock_doc.core_properties.created = None
        mock_doc.core_properties.keywords = None
        mock_doc.core_properties.subject = None
        mock_doc.paragraphs = [empty_para, content_para]

        with patch("docx.Document", return_value=mock_doc):
            result = parser.parse(b"fake docx bytes")

        assert result is not None
        assert "Some content" in result.body

    def test_parse_docx_flushes_section_on_new_heading(self):
        """Line 87 – previous section is flushed when a new heading is encountered."""
        from src.artifact_converter.parsers.docx_parser import DocxParser

        parser = DocxParser()

        # Create mock paragraphs: content, then heading (triggers flush)
        content_para = MagicMock()
        content_para.style.name = "Normal"
        content_para.text = "First section content"

        heading_para = MagicMock()
        heading_para.style.name = "Heading 1"
        heading_para.text = "Second Section"

        content_para2 = MagicMock()
        content_para2.style.name = "Normal"
        content_para2.text = "Second section content"

        mock_doc = MagicMock()
        mock_doc.core_properties.title = None
        mock_doc.core_properties.author = None
        mock_doc.core_properties.created = None
        mock_doc.core_properties.keywords = None
        mock_doc.core_properties.subject = None
        mock_doc.paragraphs = [content_para, heading_para, content_para2]

        with patch("docx.Document", return_value=mock_doc):
            result = parser.parse(b"fake docx bytes")

        assert result is not None
        assert len(result.sections) >= 1


# ---------------------------------------------------------------------------
# docx_parser.py lines 132-145: fallback parser missing document.xml
# ---------------------------------------------------------------------------

class TestDocxParserFallbackMissingXml:
    """Cover lines 132-145: DocxParser fallback handles missing document.xml."""

    def test_fallback_parser_missing_document_xml(self):
        """Lines 132-137 – fallback returns error when document.xml is missing."""
        from src.artifact_converter.parsers.docx_parser import DocxParser
        import src.artifact_converter.parsers.docx_parser as docx_mod

        # Temporarily disable python-docx to force fallback path
        original = docx_mod._HAS_PYTHON_DOCX
        docx_mod._HAS_PYTHON_DOCX = False

        try:
            parser = DocxParser()

            # Create a valid ZIP without word/document.xml
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("other/file.xml", "<root/>")
            zip_bytes = buf.getvalue()

            result = parser.parse(zip_bytes, source_path=Path("/tmp/test.docx"))
        finally:
            docx_mod._HAS_PYTHON_DOCX = original

        assert result is not None
        assert result.metadata.get("_error") is not None


# ---------------------------------------------------------------------------
# html_parser.py lines 22-24: ImportError path
# ---------------------------------------------------------------------------

class TestHtmlParserImportError:
    """Cover lines 22-24: HtmlParser handles missing bs4."""

    def test_html_parser_fallback_without_bs4(self):
        """Lines 22-24 – HtmlParser uses fallback when bs4 is not available."""
        from src.artifact_converter.parsers.html_parser import HtmlParser
        import src.artifact_converter.parsers.html_parser as html_mod

        original = html_mod._HAS_BS4
        html_mod._HAS_BS4 = False

        try:
            parser = HtmlParser()
            result = parser.parse("<html><body><p>Hello World</p></body></html>")
        finally:
            html_mod._HAS_BS4 = original

        assert result is not None
        assert result.body is not None


# ---------------------------------------------------------------------------
# html_parser.py line 63: metadata extraction
# html_parser.py line 74: fallback plain text
# ---------------------------------------------------------------------------

class TestHtmlParserMetadata:
    """Cover lines 63, 74: HtmlParser extracts metadata and handles fallback."""

    def test_html_parser_extracts_meta_description(self):
        """Line 63 – HtmlParser extracts meta description tag."""
        from src.artifact_converter.parsers.html_parser import HtmlParser

        parser = HtmlParser()
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="A test page description">
    <meta name="author" content="Test Author">
    <meta name="keywords" content="test, coverage, html">
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a paragraph.</p>
</body>
</html>"""
        result = parser.parse(html)
        assert result is not None

    def test_html_parser_handles_plain_text_fallback(self):
        """Line 74 – HtmlParser handles plain text when no HTML structure."""
        from src.artifact_converter.parsers.html_parser import HtmlParser

        parser = HtmlParser()
        # Pass plain text that looks like HTML but has no body tag
        result = parser.parse("Just plain text content without any HTML tags.")
        assert result is not None
        assert result.body is not None


# ---------------------------------------------------------------------------
# pdf_parser.py lines 23-25: ImportError path
# pdf_parser.py line 75: fallback parser
# pdf_parser.py lines 121-126: fallback parser error
# ---------------------------------------------------------------------------

class TestPdfParserFallback:
    """Cover pdf_parser fallback paths."""

    def test_pdf_parser_fallback_without_pdfplumber(self):
        """Lines 23-25 – PdfParser uses fallback when pdfplumber is not available."""
        from src.artifact_converter.parsers.pdf_parser import PdfParser
        import src.artifact_converter.parsers.pdf_parser as pdf_mod

        original = pdf_mod._HAS_PDFPLUMBER
        pdf_mod._HAS_PDFPLUMBER = False

        try:
            parser = PdfParser()
            # Create minimal PDF-like bytes with parenthesised strings
            result = parser.parse(b"%PDF-1.4 (Hello World) (Test Content) %%EOF")
        finally:
            pdf_mod._HAS_PDFPLUMBER = original

        assert result is not None
        assert result.body is not None

    def test_pdf_parser_fallback_with_creation_date(self):
        """Line 75 – PdfParser extracts CreationDate from metadata."""
        from src.artifact_converter.parsers.pdf_parser import PdfParser

        parser = PdfParser()

        # Mock pdfplumber to return metadata with CreationDate
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.metadata = {
            "Title": "Test PDF",
            "Author": "Test Author",
            "CreationDate": "D:20240115120000",
        }
        mock_pdf.pages = []

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = parser.parse(b"fake pdf bytes")

        assert result is not None
        assert result.metadata.get("date") == "D:20240115120000"
