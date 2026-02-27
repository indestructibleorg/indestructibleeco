"""Metadata extraction from source documents.

Extracts structured metadata (title, author, date, tags, description, and
custom key-value pairs) from various input formats.  Parsers may supply
pre-extracted metadata; this module normalises and enriches it.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Metadata model
# ---------------------------------------------------------------------------


class ArtifactMetadata(BaseModel):
    """Normalised metadata for a single artifact."""

    title: str | None = Field(default=None, description="Document title.")
    author: str | None = Field(default=None, description="Author name.")
    date: str | None = Field(
        default=None,
        description="ISO-8601 date string of the document's creation or last modification.",
    )
    tags: list[str] = Field(default_factory=list, description="List of keyword tags.")
    description: str | None = Field(default=None, description="Short summary.")
    source_path: str | None = Field(
        default=None,
        description="Absolute path to the original source file.",
    )
    source_format: str | None = Field(
        default=None,
        description="Input format identifier (e.g. 'markdown').",
    )
    word_count: int = Field(default=0, description="Approximate word count of the body.")
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary extra metadata supplied by the parser.",
    )

    def merge(self, other: "ArtifactMetadata") -> "ArtifactMetadata":
        """Return a new ``ArtifactMetadata`` with *other*'s non-empty fields overlaid."""
        merged = self.model_copy()
        for field_name in ArtifactMetadata.model_fields:
            other_val = getattr(other, field_name)
            if field_name == "extra":
                merged.extra = {**self.extra, **other.extra}
            elif field_name == "tags":
                merged.tags = list(dict.fromkeys(self.tags + other.tags))
            elif other_val not in (None, 0, "", []):
                setattr(merged, field_name, other_val)
        return merged


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

_TITLE_HEADING_RE = re.compile(r"^#{1,2}\s+(.+)", re.MULTILINE)
_HTML_TITLE_RE = re.compile(r"<title[^>]*>(.+?)</title>", re.IGNORECASE | re.DOTALL)


def extract_metadata(
    content: str,
    *,
    source_path: Path | None = None,
    source_format: str | None = None,
    parser_metadata: dict[str, Any] | None = None,
) -> ArtifactMetadata:
    """Build an ``ArtifactMetadata`` from raw content and optional hints.

    Parameters
    ----------
    content:
        The raw text body (after parsing).
    source_path:
        Path to the original file (used for fallback title and date).
    source_format:
        The input format identifier.
    parser_metadata:
        Pre-extracted metadata from the format-specific parser (e.g.
        YAML frontmatter fields from a Markdown file).
    """
    meta = ArtifactMetadata(
        source_format=source_format,
        word_count=len(content.split()) if content else 0,
    )

    if source_path is not None:
        meta.source_path = str(source_path.resolve())
        if meta.title is None:
            meta.title = source_path.stem.replace("_", " ").replace("-", " ").title()
        try:
            stat = source_path.stat()
            meta.date = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            logger.debug("metadata_stat_failed", path=str(source_path))

    # Attempt to pull a heading-based title from the content
    heading_title = _extract_heading_title(content, source_format)
    if heading_title:
        meta.title = heading_title

    # Overlay parser-supplied metadata
    if parser_metadata:
        meta = meta.merge(_metadata_from_dict(parser_metadata))

    logger.debug(
        "metadata_extracted",
        title=meta.title,
        tags=meta.tags,
        word_count=meta.word_count,
    )
    return meta


def _extract_heading_title(content: str, source_format: str | None) -> str | None:
    """Try to extract a title from the first heading in *content*."""
    if not content:
        return None

    if source_format in ("markdown", "txt"):
        match = _TITLE_HEADING_RE.search(content)
        if match:
            return match.group(1).strip()

    if source_format == "html":
        match = _HTML_TITLE_RE.search(content)
        if match:
            return match.group(1).strip()

    return None


def _metadata_from_dict(data: dict[str, Any]) -> ArtifactMetadata:
    """Coerce a flat dictionary into ``ArtifactMetadata``.

    Recognised keys (case-insensitive): title, author, date, tags,
    description.  Everything else is placed into ``extra``.
    """
    known_keys = {"title", "author", "date", "tags", "description"}
    normalised: dict[str, Any] = {}
    extra: dict[str, Any] = {}

    for key, value in data.items():
        lower = key.lower().strip()
        if lower in known_keys:
            if lower == "tags" and isinstance(value, str):
                normalised["tags"] = [t.strip() for t in value.split(",") if t.strip()]
            elif lower == "date" and isinstance(value, datetime):
                normalised["date"] = value.isoformat()
            else:
                normalised[lower] = value
        else:
            extra[key] = value

    normalised["extra"] = extra
    return ArtifactMetadata.model_validate(normalised)
