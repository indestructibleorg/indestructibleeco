"""JSON output generator with JSON Schema generation.

Produces a JSON artifact document and can also emit a companion JSON Schema
that describes the artifact structure.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from ..metadata import ArtifactMetadata
from . import BaseGenerator

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# JSON Schema for the artifact format
# ---------------------------------------------------------------------------

ARTIFACT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://superai.dev/schemas/artifact.json",
    "title": "SuperAI Artifact",
    "description": "Schema for converted artifact documents.",
    "type": "object",
    "required": ["artifact"],
    "properties": {
        "artifact": {
            "type": "object",
            "required": ["version", "metadata"],
            "properties": {
                "version": {"type": "string", "const": "1.0"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "author": {"type": "string"},
                        "date": {"type": "string", "format": "date-time"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "description": {"type": "string"},
                        "source": {"type": "string"},
                        "format": {"type": "string"},
                        "word_count": {"type": "integer", "minimum": 0},
                        "extra": {"type": "object"},
                    },
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heading": {"type": "string"},
                            "level": {"type": "integer", "minimum": 0},
                            "content": {"type": "string"},
                        },
                        "required": ["heading", "content"],
                    },
                },
                "body": {"type": "string"},
            },
        },
    },
}


class JsonGenerator(BaseGenerator):
    """Generate JSON artifact output with optional JSON Schema."""

    def generate(
        self,
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
        *,
        template_text: str | None = None,
    ) -> str:
        if template_text is not None:
            logger.debug("json_gen_using_template")
            return template_text

        document = self._build_document(body, metadata, sections)

        output = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        logger.debug("json_gen_done", chars=len(output))
        return output

    def file_extension(self) -> str:
        return ".json"

    @classmethod
    def generate_schema(cls) -> str:
        """Return the JSON Schema as a formatted string."""
        return json.dumps(ARTIFACT_JSON_SCHEMA, indent=2, ensure_ascii=False) + "\n"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_document(
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        doc: dict[str, Any] = {"artifact": {"version": "1.0"}}

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
