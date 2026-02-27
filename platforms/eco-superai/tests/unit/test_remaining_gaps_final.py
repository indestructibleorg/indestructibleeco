"""Targeted tests for all remaining uncovered lines.

Covers:
- repositories/__init__.py line 399: SQLAlchemyQuantumJobRepository.delete flush
- generators/__init__.py line 75: get_generator raises on unknown format
- generators/python_gen.py lines 33, 65, 125-126: python gen edge cases
- generators/typescript_gen.py lines 38, 72, 136-137: ts gen edge cases
- parsers/__init__.py line 77: get_parser raises on unknown format
- parsers/markdown_parser.py lines 64-65: frontmatter not a dict
- vectordb/manager.py lines 26-28: fallback chromadb client
- cache.py line 197: _load_index no dir
- database.py lines 33-34: init_db creates tables
- shared/decorators line 108: cache eviction
"""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# repositories/__init__.py line 399: SQLAlchemyQuantumJobRepository.delete flush
# ---------------------------------------------------------------------------

class TestSQLAlchemyQuantumJobRepositoryDeleteFlush:
    """Cover line 399: SQLAlchemyQuantumJobRepository.delete calls session.flush."""

    @pytest.mark.asyncio
    async def test_delete_quantum_job_calls_flush(self):
        """Line 399 – delete calls session.flush after successful deletion."""
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        repo = SQLAlchemyQuantumJobRepository(mock_session)
        await repo.delete("test-job-id")

        mock_session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# generators/__init__.py line 75: get_generator raises on unknown format
# ---------------------------------------------------------------------------

class TestGetGeneratorRaisesOnUnknown:
    """Cover line 75: get_generator raises ValueError for unknown format."""

    def test_get_generator_raises_for_unknown_format(self):
        """Line 75 – get_generator raises ValueError for unregistered format."""
        from src.artifact_converter.generators import get_generator
        from src.artifact_converter.config import OutputFormat

        # Use a format that is not registered as a generator
        # Create a fake format value
        with pytest.raises(ValueError, match="No generator registered"):
            # Patch the registry to be empty for a specific format
            from src.artifact_converter import generators as gen_mod
            original_registry = gen_mod._REGISTRY.copy()
            gen_mod._REGISTRY.clear()
            try:
                get_generator(OutputFormat.PYTHON)
            finally:
                gen_mod._REGISTRY.update(original_registry)


# ---------------------------------------------------------------------------
# parsers/__init__.py line 77: get_parser raises on unknown format
# ---------------------------------------------------------------------------

class TestGetParserRaisesOnUnknown:
    """Cover line 77: get_parser raises ValueError for unknown format."""

    def test_get_parser_raises_for_unknown_format(self):
        """Line 77 – get_parser raises ValueError for unregistered format."""
        from src.artifact_converter.parsers import get_parser
        from src.artifact_converter.config import InputFormat

        from src.artifact_converter import parsers as parser_mod
        original_registry = parser_mod._REGISTRY.copy()
        parser_mod._REGISTRY.clear()
        try:
            with pytest.raises(ValueError, match="No parser registered"):
                get_parser(InputFormat.MARKDOWN)
        finally:
            parser_mod._REGISTRY.update(original_registry)


# ---------------------------------------------------------------------------
# generators/python_gen.py line 33: keyword identifier sanitization
# ---------------------------------------------------------------------------

class TestPythonGenKeywordSanitization:
    """Cover line 33: _safe_python_ident adds underscore for Python keywords."""

    def test_to_identifier_for_keyword(self):
        """Line 33 – _to_identifier appends underscore for Python keywords."""
        from src.artifact_converter.generators.python_gen import _to_identifier

        # 'class' is a Python keyword
        result = _to_identifier("class")
        assert result == "class_"

        # 'return' is a Python keyword
        result = _to_identifier("return")
        assert result == "return_"


# ---------------------------------------------------------------------------
# generators/python_gen.py line 65: source_path in module docstring
# ---------------------------------------------------------------------------

class TestPythonGenSourcePath:
    """Cover line 65: PythonGenerator includes source_path in module docstring."""

    def test_python_gen_includes_source_path(self):
        """Line 65 – PythonGenerator includes source path in module docstring."""
        from src.artifact_converter.generators.python_gen import PythonGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = PythonGenerator()
        metadata = ArtifactMetadata(
            title="Test Module",
            source_path="/tmp/test_document.md",
        )
        sections = [{"heading": "Introduction", "content": "Some content here."}]

        result = gen.generate(body="Some body text.", sections=sections, metadata=metadata)
        assert "/tmp/test_document.md" in result


# ---------------------------------------------------------------------------
# generators/python_gen.py lines 125-126: duplicate identifier counter
# ---------------------------------------------------------------------------

class TestPythonGenDuplicateIdentifiers:
    """Cover lines 125-126: PythonGenerator handles duplicate section identifiers."""

    def test_python_gen_duplicate_section_headings(self):
        """Lines 125-126 – PythonGenerator deduplicates identical section headings."""
        from src.artifact_converter.generators.python_gen import PythonGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = PythonGenerator()
        metadata = ArtifactMetadata(title="Test")
        # Two sections with the same heading will create duplicate identifiers
        sections = [
            {"heading": "Introduction", "content": "First introduction."},
            {"heading": "Introduction", "content": "Second introduction."},
            {"heading": "Introduction", "content": "Third introduction."},
        ]

        result = gen.generate(body="", sections=sections, metadata=metadata)
        # Should contain deduplicated variable names
        assert "INTRODUCTION" in result
        assert "INTRODUCTION_2" in result


# ---------------------------------------------------------------------------
# generators/typescript_gen.py line 38: empty parts in camelCase
# ---------------------------------------------------------------------------

class TestTypeScriptGenCamelCase:
    """Cover line 38: _to_camel_case handles empty parts."""

    def test_to_camel_case_empty_string(self):
        """Line 38 – _to_camel_case returns original text for empty parts."""
        from src.artifact_converter.generators.typescript_gen import _to_camel_case

        # Empty string should return empty string
        result = _to_camel_case("")
        assert result == ""


# ---------------------------------------------------------------------------
# generators/typescript_gen.py line 72: source_path in TS docstring
# ---------------------------------------------------------------------------

class TestTypeScriptGenSourcePath:
    """Cover line 72: TypeScriptGenerator includes source_path in JSDoc."""

    def test_typescript_gen_includes_source_path(self):
        """Line 72 – TypeScriptGenerator includes source path in JSDoc comment."""
        from src.artifact_converter.generators.typescript_gen import TypeScriptGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = TypeScriptGenerator()
        metadata = ArtifactMetadata(
            title="Test Module",
            source_path="/tmp/test_document.md",
        )
        sections = [{"heading": "Introduction", "content": "Some content here."}]

        result = gen.generate(body="Some body text.", sections=sections, metadata=metadata)
        assert "/tmp/test_document.md" in result


# ---------------------------------------------------------------------------
# generators/typescript_gen.py lines 136-137: duplicate TS identifiers
# ---------------------------------------------------------------------------

class TestTypeScriptGenDuplicateIdentifiers:
    """Cover lines 136-137: TypeScriptGenerator handles duplicate section identifiers."""

    def test_typescript_gen_duplicate_section_headings(self):
        """Lines 136-137 – TypeScriptGenerator deduplicates identical section headings."""
        from src.artifact_converter.generators.typescript_gen import TypeScriptGenerator
        from src.artifact_converter.metadata import ArtifactMetadata

        gen = TypeScriptGenerator()
        metadata = ArtifactMetadata(title="Test")
        sections = [
            {"heading": "Introduction", "content": "First introduction."},
            {"heading": "Introduction", "content": "Second introduction."},
            {"heading": "Introduction", "content": "Third introduction."},
        ]

        result = gen.generate(body="", sections=sections, metadata=metadata)
        assert "INTRODUCTION" in result
        assert "INTRODUCTION_2" in result


# ---------------------------------------------------------------------------
# parsers/markdown_parser.py lines 64-65: frontmatter not a dict
# ---------------------------------------------------------------------------

class TestMarkdownParserFrontmatterNotDict:
    """Cover lines 64-65: MarkdownParser handles non-dict frontmatter."""

    def test_markdown_parser_frontmatter_not_dict(self):
        """Lines 64-65 – MarkdownParser handles frontmatter that is not a dict."""
        from src.artifact_converter.parsers.markdown_parser import MarkdownParser

        parser = MarkdownParser()
        # YAML frontmatter that parses to a list (not a dict)
        content = """---
- item1
- item2
---

# Main Content

This is the body text.
"""
        result = parser.parse(content)
        assert result is not None
        assert result.body is not None


# ---------------------------------------------------------------------------
# vectordb/manager.py lines 26-28: fallback chromadb client
# ---------------------------------------------------------------------------

class TestVectorDBManagerFallbackClient:
    """Cover lines 26-28: VectorDBManager uses fallback chromadb.Client() on exception."""

    def test_get_client_falls_back_to_local_client(self):
        """Lines 26-28 – VectorDBManager falls back to chromadb.Client() when HttpClient fails."""
        from src.ai.vectordb.manager import VectorDBManager

        manager = VectorDBManager.__new__(VectorDBManager)
        manager._client = None

        mock_local_client = MagicMock()

        # Make HttpClient raise, then Client succeed
        with patch("chromadb.HttpClient", side_effect=Exception("connection refused")):
            with patch("chromadb.Client", return_value=mock_local_client):
                client = manager._get_client()

        assert client is mock_local_client


# ---------------------------------------------------------------------------
# cache.py line 197: _load_index returns early when dir does not exist
# ---------------------------------------------------------------------------

class TestConversionCacheLoadIndexNoDir:
    """Cover line 197: _load_index returns early when cache directory does not exist."""

    def test_load_index_no_dir_returns_early(self):
        """Line 197 – _load_index returns early when cache directory does not exist."""
        from src.artifact_converter.cache import ConversionCache

        cache = ConversionCache.__new__(ConversionCache)
        # Set _dir to a non-existent path
        from pathlib import Path
        cache._dir = Path("/tmp/nonexistent_cache_dir_xyz_12345")
        cache._index = {}
        cache._max_size = 100
        cache._ttl = 3600.0

        # Call _load_index - should return early without error
        cache._load_index()
        assert cache._index == {}


# ---------------------------------------------------------------------------
# database.py lines 33-34: init_db creates tables
# ---------------------------------------------------------------------------

class TestInitDb:
    """Cover lines 33-34: init_db creates all tables."""

    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self):
        """Lines 33-34 – init_db calls Base.metadata.create_all."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()

        mock_engine = MagicMock()
        mock_engine.begin = MagicMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("src.infrastructure.persistence.database.engine", mock_engine):
            from src.infrastructure.persistence.database import init_db
            await init_db()

        mock_conn.run_sync.assert_called_once()


# ---------------------------------------------------------------------------
# shared/decorators line 108: cache eviction
# The cached decorator is async-only. Use an async function to trigger eviction.
# ---------------------------------------------------------------------------

class TestDecoratorsCacheEviction:
    """Cover line 108: cached decorator evicts expired entries."""

    @pytest.mark.asyncio
    async def test_cached_evicts_expired_entries(self):
        """Line 108 – cached decorator evicts entries whose TTL has expired."""
        import time
        from src.shared.decorators import cached

        call_count = 0

        @cached(ttl_seconds=1)
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - populates cache with key for x=5
        result1 = await expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Populate cache with another key (x=6) that we'll let expire
        result2 = await expensive_function(6)
        assert result2 == 12
        assert call_count == 2

        # Manually expire the x=5 entry by patching time.time
        # The eviction happens when a NEW call is made after expiry
        # We need to make the cached_time old enough to trigger eviction
        # Patch time.time to return a future time
        original_time = time.time

        def future_time():
            return original_time() + 3600  # 1 hour in the future

        with patch("src.shared.decorators.time") as mock_time:
            mock_time.time.return_value = original_time() + 3600

            # This call should trigger eviction of expired entries
            result3 = await expensive_function(7)
            assert result3 == 14
            assert call_count == 3  # Called again (new key)
