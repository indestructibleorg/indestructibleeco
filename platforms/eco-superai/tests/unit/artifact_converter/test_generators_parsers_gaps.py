"""Targeted tests for remaining uncovered lines in artifact_converter generators and parsers.

Covers:
- markdown_gen.py lines 32-33: template_text path
- markdown_gen.py line 61: body fallback (no sections)
- markdown_gen.py line 68: file_extension()
- markdown_gen.py lines 83, 87, 89, 91, 94: _build_frontmatter optional fields
- python_gen.py lines 33, 54-55, 65, 125-126: various generator paths
- typescript_gen.py lines 38, 59-60, 72, 136-137: various generator paths
- generators/__init__.py line 75: available_generators()
- parsers/__init__.py line 77: available_parsers()
- parsers/markdown_parser.py lines 64-65: frontmatter parsing
- parsers/txt_parser.py line 76: file_extension()
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# MarkdownGenerator – template_text path (lines 32-33)
# ---------------------------------------------------------------------------

class TestMarkdownGeneratorTemplate:
    """Cover lines 32-33: generate() returns template_text when provided."""

    def test_generate_returns_template_when_provided(self):
        """Lines 32-33 – template_text is returned directly."""
        from src.artifact_converter.generators.markdown_gen import MarkdownGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = MarkdownGenerator()
        meta = ArtifactMetadata()
        result = gen.generate(
            body="ignored body",
            metadata=meta,
            sections=[],
            template_text="# Custom Template\n\nContent here.\n",
        )
        assert result == "# Custom Template\n\nContent here.\n"


# ---------------------------------------------------------------------------
# MarkdownGenerator – body fallback (line 61)
# ---------------------------------------------------------------------------

class TestMarkdownGeneratorBodyFallback:
    """Cover line 61: generate() uses body when no sections provided."""

    def test_generate_uses_body_when_no_sections(self):
        """Line 61 – body is used when sections is empty."""
        from src.artifact_converter.generators.markdown_gen import MarkdownGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = MarkdownGenerator()
        meta = ArtifactMetadata()
        result = gen.generate(
            body="This is the body content.",
            metadata=meta,
            sections=[],
        )
        assert "This is the body content." in result


# ---------------------------------------------------------------------------
# MarkdownGenerator – file_extension (line 68)
# ---------------------------------------------------------------------------

class TestMarkdownGeneratorFileExtension:
    """Cover line 68: file_extension() returns '.md'."""

    def test_file_extension_returns_md(self):
        """Line 68 – file_extension() returns '.md'."""
        from src.artifact_converter.generators.markdown_gen import MarkdownGenerator

        gen = MarkdownGenerator()
        assert gen.file_extension() == ".md"


# ---------------------------------------------------------------------------
# MarkdownGenerator – _build_frontmatter optional fields (lines 83, 87, 89, 91, 94)
# ---------------------------------------------------------------------------

class TestMarkdownGeneratorFrontmatter:
    """Cover lines 83, 87, 89, 91, 94: _build_frontmatter with all optional fields."""

    def test_build_frontmatter_with_all_optional_fields(self):
        """Lines 83, 87, 89, 91, 94 – all optional metadata fields are included."""
        from src.artifact_converter.generators.markdown_gen import MarkdownGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = MarkdownGenerator()
        meta = ArtifactMetadata(
            title="Test Document",
            author="Test Author",
            date="2024-01-01",
            tags=["test", "coverage"],
            description="A test document",
            source_path="/tmp/test.md",
            source_format="markdown",
            word_count=100,
            extra={"custom_key": "custom_value"},
        )
        result = gen.generate(body="", metadata=meta, sections=[])
        assert "Test Document" in result
        assert "Test Author" in result
        assert "2024-01-01" in result
        assert "test" in result
        assert "A test document" in result
        assert "/tmp/test.md" in result
        assert "markdown" in result
        assert "custom_value" in result


# ---------------------------------------------------------------------------
# generators/__init__.py – available_generators (line 75)
# ---------------------------------------------------------------------------

class TestAvailableGenerators:
    """Cover line 75: available_generators() returns all registered generators."""

    def test_available_generators_returns_dict(self):
        """Line 75 – available_generators() returns a non-empty dict."""
        from src.artifact_converter.generators import available_generators

        result = available_generators()
        assert isinstance(result, dict)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# parsers/__init__.py – available_parsers (line 77)
# ---------------------------------------------------------------------------

class TestAvailableParsers:
    """Cover line 77: available_parsers() returns all registered parsers."""

    def test_available_parsers_returns_dict(self):
        """Line 77 – available_parsers() returns a non-empty dict."""
        from src.artifact_converter.parsers import available_parsers

        result = available_parsers()
        assert isinstance(result, dict)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# parsers/markdown_parser.py – frontmatter parsing (lines 64-65)
# ---------------------------------------------------------------------------

class TestMarkdownParserFrontmatter:
    """Cover lines 64-65: markdown parser handles frontmatter."""

    def test_parse_markdown_with_frontmatter(self):
        """Lines 64-65 – markdown with YAML frontmatter is parsed correctly."""
        from src.artifact_converter.parsers.markdown_parser import MarkdownParser

        parser = MarkdownParser()
        content = """---
title: Test Document
author: Test Author
date: 2024-01-01
tags:
  - test
  - coverage
---

# Hello World

This is the body.
"""
        result = parser.parse(content)
        assert result is not None
        assert result.body is not None


# ---------------------------------------------------------------------------
# parsers/txt_parser.py – file_extension (line 76)
# ---------------------------------------------------------------------------

class TestTxtParserPreamble:
    """Cover line 76: txt_parser preamble section before first heading."""

    def test_parse_txt_with_preamble_before_heading(self):
        """Line 76 – preamble text before a heading is added as a section."""
        from src.artifact_converter.parsers.txt_parser import TxtParser

        parser = TxtParser()
        # Content with preamble text before the first ALL-CAPS heading
        content = """This is preamble text before any heading.

INTRODUCTION

This is the introduction section.

CONCLUSION

This is the conclusion.
"""
        result = parser.parse(content)
        assert result is not None
        # The preamble section should be included
        assert len(result.sections) >= 1


# ---------------------------------------------------------------------------
# python_gen.py – uncovered lines 33, 54-55, 65, 125-126
# ---------------------------------------------------------------------------

class TestPythonGeneratorGaps:
    """Cover uncovered lines in python_gen.py."""

    def test_generate_with_template_text(self):
        """Line 33 – template_text is returned directly."""
        from src.artifact_converter.generators.python_gen import PythonGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = PythonGenerator()
        meta = ArtifactMetadata()
        result = gen.generate(
            body="ignored",
            metadata=meta,
            sections=[],
            template_text="# Custom Python template\n",
        )
        assert result == "# Custom Python template\n"

    def test_file_extension_returns_py(self):
        """Line 65 – file_extension() returns '.py'."""
        from src.artifact_converter.generators.python_gen import PythonGenerator

        gen = PythonGenerator()
        assert gen.file_extension() == ".py"

    def test_generate_with_sections_no_content(self):
        """Lines 54-55 – sections with no content are handled."""
        from src.artifact_converter.generators.python_gen import PythonGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = PythonGenerator()
        meta = ArtifactMetadata(title="Test Module")
        sections = [
            {"heading": "Section Without Content", "content": ""},
        ]
        result = gen.generate(body="", metadata=meta, sections=sections)
        assert result is not None

    def test_generate_with_metadata_description(self):
        """Lines 125-126 – metadata with description generates docstring."""
        from src.artifact_converter.generators.python_gen import PythonGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = PythonGenerator()
        meta = ArtifactMetadata(
            title="My Module",
            description="A module with a description.",
            author="Test Author",
        )
        result = gen.generate(body="x = 1", metadata=meta, sections=[])
        assert result is not None


# ---------------------------------------------------------------------------
# typescript_gen.py – uncovered lines 38, 59-60, 72, 136-137
# ---------------------------------------------------------------------------

class TestTypeScriptGeneratorGaps:
    """Cover uncovered lines in typescript_gen.py."""

    def test_generate_with_template_text(self):
        """Line 38 – template_text is returned directly."""
        from src.artifact_converter.generators.typescript_gen import TypeScriptGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = TypeScriptGenerator()
        meta = ArtifactMetadata()
        result = gen.generate(
            body="ignored",
            metadata=meta,
            sections=[],
            template_text="// Custom TypeScript template\n",
        )
        assert result == "// Custom TypeScript template\n"

    def test_file_extension_returns_ts(self):
        """Line 72 – file_extension() returns '.ts'."""
        from src.artifact_converter.generators.typescript_gen import TypeScriptGenerator

        gen = TypeScriptGenerator()
        assert gen.file_extension() == ".ts"

    def test_generate_with_sections_no_content(self):
        """Lines 59-60 – sections with no content are handled."""
        from src.artifact_converter.generators.typescript_gen import TypeScriptGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = TypeScriptGenerator()
        meta = ArtifactMetadata(title="Test Module")
        sections = [
            {"heading": "Section Without Content", "content": ""},
        ]
        result = gen.generate(body="", metadata=meta, sections=sections)
        assert result is not None

    def test_generate_with_metadata_description(self):
        """Lines 136-137 – metadata with description generates JSDoc comment."""
        from src.artifact_converter.generators.typescript_gen import TypeScriptGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = TypeScriptGenerator()
        meta = ArtifactMetadata(
            title="MyModule",
            description="A TypeScript module.",
            author="Test Author",
        )
        result = gen.generate(body="const x = 1;", metadata=meta, sections=[])
        assert result is not None
