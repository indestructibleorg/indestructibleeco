"""TypeScript interface and type generator.

Produces a self-contained TypeScript module containing:
- An ``ArtifactMetadata`` interface.
- A ``Section`` interface.
- Typed constant exports for metadata, sections, and a convenience lookup.
"""

from __future__ import annotations

import json
import re
from typing import Any

import structlog

from ..metadata import ArtifactMetadata
from . import BaseGenerator

logger = structlog.get_logger(__name__)

_TS_IDENT_RE = re.compile(r"[^a-zA-Z0-9_$]")


def _to_ts_identifier(text: str) -> str:
    """Convert arbitrary text into a valid TypeScript identifier."""
    ident = _TS_IDENT_RE.sub("_", text.strip())
    ident = re.sub(r"_+", "_", ident).strip("_")
    if not ident or ident[0].isdigit():
        ident = f"section_{ident}"
    return ident


def _to_camel_case(text: str) -> str:
    """Convert a snake_case or space-separated string to camelCase."""
    parts = re.split(r"[\s_\-]+", text)
    if not parts:
        return text  # pragma: no cover
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def _ts_string_literal(value: str) -> str:
    """Produce a TypeScript string literal with proper escaping."""
    return json.dumps(value, ensure_ascii=False)


class TypeScriptGenerator(BaseGenerator):
    """Generate a TypeScript module artifact."""

    def generate(
        self,
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
        *,
        template_text: str | None = None,
    ) -> str:
        if template_text is not None:
            logger.debug("typescript_gen_using_template")
            return template_text

        lines: list[str] = []

        title = metadata.title or "Artifact"

        # File header
        lines.append("/**")
        lines.append(f" * Auto-generated artifact module: {title}")
        lines.append(" *")
        lines.append(" * Produced by the SuperAI Artifact Converter.")
        if metadata.source_path:
            lines.append(f" * Source: {metadata.source_path}")
        lines.append(" */")
        lines.append("")

        # Interfaces
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("// Interfaces")
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("")
        lines.append("export interface ArtifactMetadata {")
        lines.append("  readonly title: string;")
        lines.append("  readonly author: string;")
        lines.append("  readonly date: string;")
        lines.append("  readonly tags: readonly string[];")
        lines.append("  readonly description: string;")
        lines.append("  readonly sourcePath: string;")
        lines.append("  readonly sourceFormat: string;")
        lines.append("  readonly wordCount: number;")
        lines.append("}")
        lines.append("")
        lines.append("export interface Section {")
        lines.append("  readonly heading: string;")
        lines.append("  readonly level: number;")
        lines.append("  readonly content: string;")
        lines.append("}")
        lines.append("")

        # Metadata constant
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("// Metadata")
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("")
        lines.append("export const METADATA: ArtifactMetadata = {")
        lines.append(f"  title: {_ts_string_literal(metadata.title or '')},")
        lines.append(f"  author: {_ts_string_literal(metadata.author or '')},")
        lines.append(f"  date: {_ts_string_literal(metadata.date or '')},")
        tags_str = json.dumps(metadata.tags, ensure_ascii=False)
        lines.append(f"  tags: {tags_str},")
        lines.append(f"  description: {_ts_string_literal(metadata.description or '')},")
        lines.append(f"  sourcePath: {_ts_string_literal(metadata.source_path or '')},")
        lines.append(f"  sourceFormat: {_ts_string_literal(metadata.source_format or '')},")
        lines.append(f"  wordCount: {metadata.word_count},")
        lines.append("} as const;")
        lines.append("")

        # Sections
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("// Sections")
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("")

        if sections:
            seen_identifiers: set[str] = set()
            section_var_names: list[str] = []

            for i, sec in enumerate(sections):
                heading = sec.get("heading", "")
                level = sec.get("level", 0)
                content = sec.get("content", "")

                base_ident = _to_ts_identifier(heading) if heading else f"section_{i}"
                ident = base_ident
                counter = 2
                while ident.upper() in seen_identifiers:
                    ident = f"{base_ident}_{counter}"
                    counter += 1
                var_name = ident.upper()
                seen_identifiers.add(var_name)
                section_var_names.append(var_name)

                lines.append(f"export const {var_name}: Section = {{")
                lines.append(f"  heading: {_ts_string_literal(heading)},")
                lines.append(f"  level: {level},")
                lines.append(f"  content: {_ts_string_literal(content)},")
                lines.append("} as const;")
                lines.append("")

            lines.append(
                "export const SECTIONS: readonly Section[] = ["
            )
            for var_name in section_var_names:
                lines.append(f"  {var_name},")
            lines.append("] as const;")
        else:
            lines.append(f"export const BODY: string = {_ts_string_literal(body)};")
            lines.append("")
            lines.append("export const SECTIONS: readonly Section[] = [")
            lines.append('  { heading: "", level: 0, content: BODY },')
            lines.append("] as const;")

        lines.append("")

        # Convenience function
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("// Utilities")
        lines.append("// ---------------------------------------------------------------------------")
        lines.append("")
        lines.append("/**")
        lines.append(" * Find the first section whose heading matches (case-insensitive).")
        lines.append(" */")
        lines.append(
            "export function getSectionByHeading(heading: string): Section | undefined {"
        )
        lines.append("  const lower = heading.toLowerCase();")
        lines.append(
            "  return SECTIONS.find((s) => s.heading.toLowerCase() === lower);"
        )
        lines.append("}")
        lines.append("")
        lines.append("/**")
        lines.append(" * Concatenate all section content into a single string.")
        lines.append(" */")
        lines.append("export function allText(): string {")
        lines.append('  return SECTIONS.map((s) => s.content).filter(Boolean).join("\\n\\n");')
        lines.append("}")
        lines.append("")

        output = "\n".join(lines)
        logger.debug("typescript_gen_done", chars=len(output))
        return output

    def file_extension(self) -> str:
        return ".ts"
