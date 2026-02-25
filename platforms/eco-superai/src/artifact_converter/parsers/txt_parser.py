"""Plain-text parser.

Handles ``.txt`` and ``.text`` files.  Extracts rudimentary structure by
detecting lines that look like headings (ALL CAPS or underline-decorated).
"""

from __future__ import annotations

import re
from pathlib import Path

import structlog

from . import BaseParser, ParseResult

logger = structlog.get_logger(__name__)

_UNDERLINE_HEADING_RE = re.compile(
    r"^(?P<title>.+)\n(?P<underline>[=\-]{3,})\s*$", re.MULTILINE
)
_CAPS_HEADING_RE = re.compile(r"^(?P<title>[A-Z][A-Z \t]{2,})$", re.MULTILINE)


class TxtParser(BaseParser):
    """Parser for plain-text documents."""

    def parse(self, content: str | bytes, source_path: Path | None = None) -> ParseResult:
        text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
        logger.debug("txt_parse_start", length=len(text), source=str(source_path))

        sections = self._extract_sections(text)

        return ParseResult(
            body=text.strip(),
            metadata={},
            sections=sections,
            raw=text,
        )

    def supported_extensions(self) -> list[str]:
        return [".txt", ".text"]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_sections(text: str) -> list[dict[str, str]]:
        """Detect heading-like lines and split text into sections."""
        sections: list[dict[str, str]] = []

        # Strategy 1: underline-decorated headings (RST-style)
        parts = _UNDERLINE_HEADING_RE.split(text)
        if len(parts) > 1:
            # parts: [preamble, title1, underline1, body1, title2, ...]
            idx = 0
            if parts[0].strip():
                sections.append({"heading": "", "content": parts[0].strip()})
            idx = 1
            while idx + 2 < len(parts):
                title = parts[idx].strip()
                # parts[idx+1] is the underline characters
                body = parts[idx + 2].strip() if idx + 2 < len(parts) else ""
                sections.append({"heading": title, "content": body})
                idx += 3
            if sections:
                return sections

        # Strategy 2: ALL-CAPS headings
        matches = list(_CAPS_HEADING_RE.finditer(text))
        if matches:
            prev_end = 0
            for i, match in enumerate(matches):
                preamble = text[prev_end : match.start()].strip()
                if preamble:
                    sections.append({"heading": "", "content": preamble})
                heading = match.group("title").strip()
                next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                body = text[match.end() : next_start].strip()
                sections.append({"heading": heading, "content": body})
                prev_end = next_start
            return sections

        # Fallback: no structure detected
        if text.strip():
            sections.append({"heading": "", "content": text.strip()})
        return sections
