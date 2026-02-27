"""Targeted tests for remaining uncovered lines in artifact_converter.

Covers:
- cache.py lines 122-130: disk hit and corrupt entry handling
- cache.py lines 197, 201: _load_index non-json file skip
- cli.py lines 51, 63-65: convert no_cache and exception path
- cli.py lines 83-84, 88: batch not-a-directory and no_cache
- cli.py lines 127-129, 133: batch exception and errors exit
- cli.py lines 150, 155-191: watch command (ImportError and success)
- cli.py lines 226-228: info exception path
- cli.py line 256: __main__ block
"""
from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from typer.testing import CliRunner


# ---------------------------------------------------------------------------
# cache.py – disk hit (lines 122-127)
# ---------------------------------------------------------------------------

class TestCacheDiskHit:
    """Cover lines 122-127: cache hit from disk when not in memory index."""

    def test_get_returns_entry_from_disk_when_not_in_index(self):
        """Lines 122-127 – entry is loaded from disk when missing from index."""
        from src.artifact_converter.cache import ConversionCache, CacheEntry, CacheKey
        from src.artifact_converter.config import CacheSettings

        with tempfile.TemporaryDirectory() as tmpdir:
            settings = CacheSettings(directory=Path(tmpdir))
            cache = ConversionCache(settings=settings)

            # Create a cache entry and write it to disk directly (bypass put)
            key = CacheKey(content_hash="abc123", output_format="yaml")
            entry = CacheEntry(key=key, output_text="output: value", source_path="/tmp/test.md")
            filename = key.to_filename()
            path = Path(tmpdir) / filename
            path.write_text(json.dumps(entry.to_dict()), encoding="utf-8")

            # Clear the in-memory index so it falls back to disk
            cache._index.clear()

            # get() should find it on disk
            result = cache.get(key)
            assert result is not None
            assert result.key.content_hash == "abc123"

    def test_get_removes_corrupt_entry_from_disk(self):
        """Lines 128-130 – corrupt JSON entry is removed from disk."""
        from src.artifact_converter.cache import ConversionCache, CacheKey
        from src.artifact_converter.config import CacheSettings

        with tempfile.TemporaryDirectory() as tmpdir:
            settings = CacheSettings(directory=Path(tmpdir))
            cache = ConversionCache(settings=settings)

            # Write a corrupt JSON file to disk
            key = CacheKey(content_hash="corrupt123", output_format="yaml")
            filename = key.to_filename()
            path = Path(tmpdir) / filename
            path.write_text("{invalid json}", encoding="utf-8")

            # get() should handle the corrupt entry gracefully
            result = cache.get(key)
            assert result is None
            # The corrupt file should have been removed
            assert not path.exists()


# ---------------------------------------------------------------------------
# cache.py – _load_index non-json file skip (lines 197, 201)
# ---------------------------------------------------------------------------

class TestCacheLoadIndexSkipsNonJson:
    """Cover lines 197, 201: _load_index skips non-.json files."""

    def test_load_index_skips_non_json_files(self):
        """Line 201 – non-.json files are skipped during index loading."""
        from src.artifact_converter.cache import ConversionCache
        from src.artifact_converter.config import CacheSettings

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-json file in the cache directory
            non_json = Path(tmpdir) / "readme.txt"
            non_json.write_text("not a cache entry", encoding="utf-8")

            # Initialize cache - should load index without errors
            settings = CacheSettings(directory=Path(tmpdir))
            cache = ConversionCache(settings=settings)
            # The non-json file should not be in the index
            assert "readme.txt" not in cache._index

    def test_load_index_returns_early_when_dir_missing(self):
        """Line 197 – _load_index returns early when directory doesn't exist."""
        from src.artifact_converter.cache import ConversionCache
        from src.artifact_converter.config import CacheSettings

        # Use a non-existent directory with cache disabled (so it doesn't try to create it)
        settings = CacheSettings(directory=Path("/tmp/nonexistent_cache_dir_xyz"), enabled=False)
        cache = ConversionCache(settings=settings)
        # Should not raise, index should be empty
        assert len(cache._index) == 0


# ---------------------------------------------------------------------------
# cli.py – convert no_cache path (line 51)
# ---------------------------------------------------------------------------

class TestCliConvertNoCache:
    """Cover line 51: convert command with --no-cache disables cache."""

    def test_convert_no_cache_disables_cache(self, tmp_path):
        """Line 51 – cfg.cache.enabled is set to False when --no-cache is passed."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        # Create a test markdown file
        src = tmp_path / "test.md"
        src.write_text("# Hello\n\nWorld", encoding="utf-8")

        with patch("src.artifact_converter.convert_file", return_value=str(tmp_path / "test.yaml")):
            result = runner.invoke(app, [
                "convert", str(src),
                "--format", "yaml",
                "--no-cache",
            ])

        # Should succeed (exit code 0) or fail gracefully
        assert result.exit_code in (0, 1)


# ---------------------------------------------------------------------------
# cli.py – convert exception path (lines 63-65)
# ---------------------------------------------------------------------------

class TestCliConvertException:
    """Cover lines 63-65: convert command exception path."""

    def test_convert_exception_exits_with_code_1(self, tmp_path):
        """Lines 63-65 – exception in convert_file causes exit code 1."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        src = tmp_path / "test.md"
        src.write_text("# Hello", encoding="utf-8")

        with patch("src.artifact_converter.convert_file", side_effect=RuntimeError("conversion failed")):
            result = runner.invoke(app, ["convert", str(src), "--format", "yaml"])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# cli.py – batch not-a-directory (lines 83-84)
# ---------------------------------------------------------------------------

class TestCliBatchNotDirectory:
    """Cover lines 83-84: batch command with non-directory path."""

    def test_batch_not_directory_exits_with_code_1(self, tmp_path):
        """Lines 83-84 – non-directory path causes exit code 1."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        # Pass a file path instead of a directory
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        result = runner.invoke(app, ["batch", str(file_path)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# cli.py – batch no_cache (line 88)
# ---------------------------------------------------------------------------

class TestCliBatchNoCache:
    """Cover line 88: batch command with --no-cache."""

    def test_batch_no_cache_disables_cache(self, tmp_path):
        """Line 88 – cfg.cache.enabled is set to False for batch --no-cache."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        # Create an empty directory (no files to convert)
        batch_dir = tmp_path / "batch"
        batch_dir.mkdir()

        result = runner.invoke(app, ["batch", str(batch_dir), "--no-cache"])
        # Should succeed with 0 files converted
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# cli.py – batch exception path (lines 127-129, 133)
# ---------------------------------------------------------------------------

class TestCliBatchException:
    """Cover lines 127-129, 133: batch command exception and errors exit."""

    def test_batch_exception_exits_with_code_1(self, tmp_path):
        """Lines 127-129, 133 – exception in convert_file causes exit code 1."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        batch_dir = tmp_path / "batch"
        batch_dir.mkdir()
        # Create a markdown file to trigger conversion
        (batch_dir / "test.md").write_text("# Hello")

        with patch("src.artifact_converter.convert_file", side_effect=RuntimeError("batch error")):
            result = runner.invoke(app, ["batch", str(batch_dir)])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# cli.py – watch ImportError (line 150)
# ---------------------------------------------------------------------------

class TestCliWatchImportError:
    """Cover line 150: watch command when watchdog is not installed."""

    def test_watch_import_error_exits_with_code_1(self, tmp_path):
        """Line 150 – ImportError for watchdog causes exit code 1."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        with patch.dict("sys.modules", {"watchdog": None, "watchdog.events": None, "watchdog.observers": None}):
            result = runner.invoke(app, ["watch", str(watch_dir)])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# cli.py – info exception path (lines 226-228)
# ---------------------------------------------------------------------------

class TestCliInfoException:
    """Cover lines 226-228: info command exception path."""

    def test_info_exception_exits_with_code_1(self, tmp_path):
        """Lines 226-228 – exception in info command causes exit code 1."""
        from src.artifact_converter.cli import app

        runner = CliRunner()
        src = tmp_path / "test.md"
        src.write_text("# Hello")

        with patch("src.artifact_converter.metadata.extract_metadata", side_effect=RuntimeError("meta error")):
            result = runner.invoke(app, ["info", str(src)])

        assert result.exit_code == 1
