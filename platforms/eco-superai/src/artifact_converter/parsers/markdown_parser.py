"""Markdown parser with YAML frontmatter support.

Splits a Markdown document into metadata (frontmatter) and body, then
extracts heading-based sections.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import structlog
import yaml

from . import BaseParser, ParseResult

logger = structlog.get_logger(__name__)

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<frontmatter>.*?)\n---\s*\n",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+)", re.MULTILINE)


class MarkdownParser(BaseParser):
    """Parser for Markdown (``.md``, ``.markdown``) files."""

    def parse(self, content: str | bytes, source_path: Path | None = None) -> ParseResult:
        text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
        logger.debug("markdown_parse_start", length=len(text), source=str(source_path))

        metadata, body = self._split_frontmatter(text)
        sections = self._extract_sections(body)

        return ParseResult(
            body=body.strip(),
            metadata=metadata,
            sections=sections,
            raw=text,
        )

    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
        """Separate YAML frontmatter from the Markdown body."""
        match = _FRONTMATTER_RE.match(text)
        if not match:
            return {}, text

        raw_fm = match.group("frontmatter")
        body = text[match.end() :]

        try:
            metadata = yaml.safe_load(raw_fm)
            if not isinstance(metadata, dict):
                logger.warning("markdown_frontmatter_not_dict", type=type(metadata).__name__)
                return {}, text
            logger.debug("markdown_frontmatter_parsed", keys=list(metadata.keys()))
            return metadata, body
        except yaml.YAMLError as exc:
            logger.warning("markdown_frontmatter_invalid", error=str(exc))
            return {}, text

    @staticmethod
    def _extract_sections(body: str) -> list[dict[str, Any]]:
        """Split the Markdown body into sections at heading boundaries."""
        sections: list[dict[str, Any]] = []
        matches = list(_HEADING_RE.finditer(body))

        if not matches:
            if body.strip():
                sections.append({"heading": "", "level": 0, "content": body.strip()})
            return sections

        # Content before the first heading
        preamble = body[: matches[0].start()].strip()
        if preamble:
            sections.append({"heading": "", "level": 0, "content": preamble})

        for i, match in enumerate(matches):
            level = len(match.group("hashes"))
            title = match.group("title").strip()
            next_start = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            content = body[match.end() : next_start].strip()
            sections.append({
                "heading": title,
                "level": level,
                "content": content,
            })

        return sections
