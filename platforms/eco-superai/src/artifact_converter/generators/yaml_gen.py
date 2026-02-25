"""YAML output generator.

Produces a structured YAML document containing metadata and content sections.
"""

from __future__ import annotations

from typing import Any

import structlog
import yaml

from ..metadata import ArtifactMetadata
from . import BaseGenerator

logger = structlog.get_logger(__name__)


class YamlGenerator(BaseGenerator):
    """Generate YAML artifact output."""

    def generate(
        self,
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
        *,
        template_text: str | None = None,
    ) -> str:
        if template_text is not None:
            logger.debug("yaml_gen_using_template")
            return template_text

        document = self._build_document(body, metadata, sections)

        output = yaml.dump(
            document,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=100,
        )
        logger.debug("yaml_gen_done", chars=len(output))
        return output

    def file_extension(self) -> str:
        return ".yaml"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_document(
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble the YAML document structure."""
        doc: dict[str, Any] = {"artifact": {"version": "1.0"}}

        # Metadata block
        meta_block: dict[str, Any] = {}
        if metadata.title:
            meta_block["title"] = metadata.title
        if metadata.author:
            meta_block["author"] = metadata.author
        if metadata.date:
            meta_block["date"] = metadata.date
        if metadata.tags:
            meta_block["tags"] = metadata.tags
        if metadata.description:
            meta_block["description"] = metadata.description
        if metadata.source_path:
            meta_block["source"] = metadata.source_path
        if metadata.source_format:
            meta_block["format"] = metadata.source_format
        meta_block["word_count"] = metadata.word_count
        if metadata.extra:
            meta_block["extra"] = metadata.extra

        doc["artifact"]["metadata"] = meta_block

        # Sections
        if sections:
            doc["artifact"]["sections"] = [
                {
                    "heading": sec.get("heading", ""),
                    "level": sec.get("level", 0),
                    "content": sec.get("content", ""),
                }
                for sec in sections
            ]
        else:
            doc["artifact"]["body"] = body

        return doc
