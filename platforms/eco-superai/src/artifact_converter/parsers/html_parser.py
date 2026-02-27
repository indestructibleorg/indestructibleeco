"""HTML parser using BeautifulSoup.

Extracts text content, metadata (``<meta>`` tags, ``<title>``), and
heading-based sections from HTML documents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from . import BaseParser, ParseResult

logger = structlog.get_logger(__name__)

try:
    from bs4 import BeautifulSoup, Tag  # type: ignore[import-untyped]

    _HAS_BS4 = True
except ImportError:  # pragma: no cover
    _HAS_BS4 = False
    logger.info(
        "beautifulsoup4_not_installed",
        hint="Install beautifulsoup4 for full HTML support: pip install beautifulsoup4",
    )


class HtmlParser(BaseParser):
    """Parser for HTML (``.html``, ``.htm``) documents."""

    def parse(self, content: str | bytes, source_path: Path | None = None) -> ParseResult:
        text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
        logger.debug("html_parse_start", length=len(text), source=str(source_path))

        if not _HAS_BS4:
            return self._parse_fallback(text, source_path)

        return self._parse_with_bs4(text, source_path)

    def supported_extensions(self) -> list[str]:
        return [".html", ".htm"]

    # ------------------------------------------------------------------
    # BeautifulSoup extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_with_bs4(text: str, source_path: Path | None) -> ParseResult:
        soup = BeautifulSoup(text, "html.parser")

        metadata: dict[str, Any] = {}

        # <title>
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            metadata["title"] = title_tag.string.strip()

        # <meta> tags
        for meta_tag in soup.find_all("meta"):
            if not isinstance(meta_tag, Tag):
                continue
            name = (meta_tag.get("name") or meta_tag.get("property") or "").lower()
            content_val = meta_tag.get("content", "")
            if name and content_val:
                if name in ("author", "description"):
                    metadata[name] = content_val
                elif name == "keywords":
                    metadata["tags"] = [t.strip() for t in str(content_val).split(",") if t.strip()]
                elif name.startswith("og:"):
                    metadata.setdefault("opengraph", {})[name] = content_val
                else:
                    metadata[name] = content_val

        # Extract body text
        body_tag = soup.find("body")
        target = body_tag if body_tag else soup
        body_text = target.get_text(separator="\n", strip=True)

        # Extract heading-based sections
        sections = _extract_html_sections(soup)

        logger.debug(
            "html_bs4_done",
            chars=len(body_text),
            sections=len(sections),
            meta_keys=list(metadata.keys()),
        )

        return ParseResult(
            body=body_text,
            metadata=metadata,
            sections=sections,
            raw=text,
        )

    # ------------------------------------------------------------------
    # Fallback (no BeautifulSoup)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_fallback(text: str, source_path: Path | None) -> ParseResult:
        import re

        logger.warning(
            "html_fallback_extraction",
            hint="Install beautifulsoup4 for accurate HTML parsing.",
            source=str(source_path),
        )

        # Strip tags
        clean = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        # Attempt title extraction
        metadata: dict[str, Any] = {}
        title_match = re.search(r"<title[^>]*>(.+?)</title>", text, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        metadata["_fallback"] = True
        metadata["_warning"] = "beautifulsoup4 not installed; structure may be lost"

        return ParseResult(
            body=clean,
            metadata=metadata,
            sections=[{"heading": "", "content": clean}] if clean else [],
            raw=text,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_html_sections(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Walk the DOM and group content under ``<h1>``..``<h6>`` headings."""
    heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}
    sections: list[dict[str, Any]] = []
    current_heading = ""
    current_level = 0
    current_parts: list[str] = []

    body = soup.find("body") or soup

    for element in body.children:
        if not isinstance(element, Tag):
            text = str(element).strip()
            if text:
                current_parts.append(text)
            continue

        tag_name = element.name.lower() if element.name else ""

        if tag_name in heading_tags:
            # Flush previous section
            if current_heading or current_parts:
                sections.append({
                    "heading": current_heading,
                    "level": current_level,
                    "content": "\n".join(current_parts).strip(),
                })
            current_heading = element.get_text(strip=True)
            current_level = int(tag_name[1])
            current_parts = []
        else:
            text = element.get_text(separator="\n", strip=True)
            if text:
                current_parts.append(text)

    # Flush final section
    if current_heading or current_parts:
        sections.append({
            "heading": current_heading,
            "level": current_level,
            "content": "\n".join(current_parts).strip(),
        })

    return sections
