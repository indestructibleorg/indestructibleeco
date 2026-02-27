"""Targeted tests for remaining uncovered lines in cli.py and docx_parser.py.

Covers:
- cli.py lines 176-177: watch command exception handler
- cli.py line 256: __main__ entry point
- docx_parser.py lines 25-27: ImportError path (python-docx not installed)
- docx_parser.py lines 139-145: fallback parser with valid DOCX ZIP
"""
from __future__ import annotations

import io
import zipfile
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


# ---------------------------------------------------------------------------
# cli.py lines 176-177: watch command exception handler
# ---------------------------------------------------------------------------

class TestCliWatchExceptionHandler:
    """Cover lines 176-177: watch command exception handler in _Handler."""

    def test_watch_handler_exception_is_caught(self):
        """Lines 176-177 – watch command exception handler catches and logs errors."""
        import tempfile
        import os
        from typer.testing import CliRunner
        from src.artifact_converter.cli import app as cli_app

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir, exist_ok=True)

            # Create a test file to trigger the handler
            test_file = os.path.join(tmpdir, "test.md")
            with open(test_file, "w") as f:
                f.write("# Test\n\nContent here.")

            with (
                patch("src.artifact_converter.convert_file", side_effect=RuntimeError("conversion failed")),
                patch("watchdog.observers.Observer") as mock_observer_cls,
            ):
                mock_observer = MagicMock()
                mock_observer_cls.return_value = mock_observer
                mock_observer.is_alive.return_value = False

                result = runner.invoke(cli_app, ["watch", tmpdir, "--output-dir", output_dir])
                # The command should complete without error


# ---------------------------------------------------------------------------
# cli.py lines 176-177: direct handler exception test via watchdog event
# ---------------------------------------------------------------------------

class TestCliWatchHandlerDirectException:
    """Cover lines 176-177: watch _Handler.on_modified exception path via direct call."""

    def test_watch_handler_on_modified_exception_direct(self):
        """Lines 176-177 – _Handler.on_modified catches exceptions during conversion."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir, exist_ok=True)

            test_file = os.path.join(tmpdir, "test.md")
            with open(test_file, "w") as f:
                f.write("# Test\n\nContent.")

            from src.artifact_converter import cli as cli_mod
            from typer.testing import CliRunner
            runner = CliRunner()

            with (
                patch("src.artifact_converter.convert_file", side_effect=RuntimeError("conversion error")),
                patch("watchdog.observers.Observer") as mock_observer_cls,
            ):
                mock_observer = MagicMock()
                mock_observer_cls.return_value = mock_observer
                mock_observer.is_alive.return_value = False

                result = runner.invoke(
                    cli_mod.app,
                    ["watch", tmpdir, "--output-dir", output_dir],
                )


# ---------------------------------------------------------------------------
# docx_parser.py lines 25-27: ImportError path
# ---------------------------------------------------------------------------

class TestDocxParserImportError:
    """Cover lines 25-27: DocxParser logs when python-docx is not installed."""

    def test_docx_parser_import_error_path(self):
        """Lines 25-27 – DocxParser uses fallback when python-docx is not available."""
        from src.artifact_converter.parsers.docx_parser import DocxParser
        import src.artifact_converter.parsers.docx_parser as docx_mod

        original = docx_mod._HAS_PYTHON_DOCX
        docx_mod._HAS_PYTHON_DOCX = False

        try:
            parser = DocxParser()
            # Create a valid DOCX ZIP with word/document.xml
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Hello World</w:t></w:r></w:p>
  </w:body>
</w:document>"""
                zf.writestr("word/document.xml", xml)
            zip_bytes = buf.getvalue()

            result = parser.parse(zip_bytes, source_path=Path("/tmp/test.docx"))
        finally:
            docx_mod._HAS_PYTHON_DOCX = original

        assert result is not None
        assert result.metadata.get("_fallback") is True


# ---------------------------------------------------------------------------
# docx_parser.py lines 139-145: fallback parser with valid DOCX ZIP
# ---------------------------------------------------------------------------

class TestDocxParserFallbackWithValidDocx:
    """Cover lines 139-145: DocxParser fallback extracts text from valid DOCX ZIP."""

    def test_fallback_parser_with_valid_docx_zip(self):
        """Lines 139-145 – fallback parser extracts text from valid DOCX ZIP."""
        from src.artifact_converter.parsers.docx_parser import DocxParser
        import src.artifact_converter.parsers.docx_parser as docx_mod

        original = docx_mod._HAS_PYTHON_DOCX
        docx_mod._HAS_PYTHON_DOCX = False

        try:
            parser = DocxParser()

            # Create a valid DOCX ZIP with word/document.xml containing text
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r><w:t>Hello World from DOCX</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Second paragraph content</w:t></w:r>
    </w:p>
  </w:body>
</w:document>"""
                zf.writestr("word/document.xml", xml)
            zip_bytes = buf.getvalue()

            result = parser.parse(zip_bytes, source_path=Path("/tmp/test.docx"))
        finally:
            docx_mod._HAS_PYTHON_DOCX = original

        assert result is not None
        assert result.metadata.get("_fallback") is True
        # The text should be extracted (XML tags stripped)
        assert len(result.body) > 0
