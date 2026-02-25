"""Parser registry for the artifact converter.

Each parser implements the :class:`BaseParser` protocol and is registered
against one or more :class:`~artifact_converter.config.InputFormat` values.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from ..config import InputFormat

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Parser result
# ---------------------------------------------------------------------------


@dataclass
class ParseResult:
    """Normalised output of any parser."""

    body: str
    """The extracted plain-text / stripped content."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Metadata fields extracted by the parser (e.g. YAML frontmatter)."""

    sections: list[dict[str, Any]] = field(default_factory=list)
    """Optional list of document sections (heading, content pairs)."""

    raw: str = ""
    """The original raw content before any processing."""


# ---------------------------------------------------------------------------
# Base parser
# ---------------------------------------------------------------------------


class BaseParser(ABC):
    """Abstract base for all format-specific parsers."""

    @abstractmethod
    def parse(self, content: str | bytes, source_path: Path | None = None) -> ParseResult:
        """Parse *content* and return a :class:`ParseResult`."""

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return file extensions this parser handles (e.g. ``['.md', '.markdown']``)."""


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[InputFormat, BaseParser] = {}


def register_parser(fmt: InputFormat, parser: BaseParser) -> None:
    """Register *parser* for the given :class:`InputFormat`."""
    _REGISTRY[fmt] = parser
    logger.debug("parser_registered", format=fmt.value, parser=type(parser).__name__)


def get_parser(fmt: InputFormat) -> BaseParser:
    """Return the registered parser for *fmt*, raising on miss."""
    parser = _REGISTRY.get(fmt)
    if parser is None:
        raise ValueError(
            f"No parser registered for format '{fmt.value}'. "
            f"Available: {[f.value for f in _REGISTRY]}"
        )
    return parser


def available_parsers() -> dict[str, str]:
    """Return a mapping of format name to parser class name."""
    return {fmt.value: type(p).__name__ for fmt, p in _REGISTRY.items()}


# ---------------------------------------------------------------------------
# Auto-register built-in parsers on import
# ---------------------------------------------------------------------------


def _auto_register() -> None:
    """Import and register all built-in parsers."""
    from .docx_parser import DocxParser
    from .html_parser import HtmlParser
    from .markdown_parser import MarkdownParser
    from .pdf_parser import PdfParser
    from .txt_parser import TxtParser

    register_parser(InputFormat.TXT, TxtParser())
    register_parser(InputFormat.MARKDOWN, MarkdownParser())
    register_parser(InputFormat.PDF, PdfParser())
    register_parser(InputFormat.DOCX, DocxParser())
    register_parser(InputFormat.HTML, HtmlParser())


_auto_register()
