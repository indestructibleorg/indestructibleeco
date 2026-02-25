"""Structured Markdown output generator.

Produces a Markdown document with YAML frontmatter containing metadata, and
heading-structured body sections.
"""

from __future__ import annotations

from typing import Any

import structlog
import yaml

from ..metadata import ArtifactMetadata
from . import BaseGenerator

logger = structlog.get_logger(__name__)


class MarkdownGenerator(BaseGenerator):
    """Generate structured Markdown artifact output."""

    def generate(
        self,
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
        *,
        template_text: str | None = None,
    ) -> str:
        if template_text is not None:
            logger.debug("markdown_gen_using_template")
            return template_text

        parts: list[str] = []

        # YAML frontmatter
        frontmatter = self._build_frontmatter(metadata)
        if frontmatter:
            fm_yaml = yaml.dump(
                frontmatter,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            ).strip()
            parts.append(f"---\n{fm_yaml}\n---\n")

        # Body
        if sections:
            for sec in sections:
                heading = sec.get("heading", "")
                level = sec.get("level", 2)
                content = sec.get("content", "")

                if heading:
                    prefix = "#" * max(1, min(level, 6))
                    parts.append(f"{prefix} {heading}\n")
                if content:
                    parts.append(f"{content}\n")
        elif body:
            parts.append(body)

        output = "\n".join(parts).strip() + "\n"
        logger.debug("markdown_gen_done", chars=len(output))
        return output

    def file_extension(self) -> str:
        return ".md"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_frontmatter(metadata: ArtifactMetadata) -> dict[str, Any]:
        """Build a frontmatter dictionary from metadata."""
        fm: dict[str, Any] = {}
        if metadata.title:
            fm["title"] = metadata.title
        if metadata.author:
            fm["author"] = metadata.author
        if metadata.date:
            fm["date"] = metadata.date
        if metadata.tags:
            fm["tags"] = metadata.tags
        if metadata.description:
            fm["description"] = metadata.description
        if metadata.source_path:
            fm["source"] = metadata.source_path
        if metadata.source_format:
            fm["source_format"] = metadata.source_format
        fm["word_count"] = metadata.word_count
        if metadata.extra:
            fm["extra"] = metadata.extra
        return fm
