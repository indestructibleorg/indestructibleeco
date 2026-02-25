"""Python module code generator.

Produces a self-contained Python module containing:
- A ``dataclass`` representing the artifact metadata.
- String constants for each section body.
- A ``SECTIONS`` list for structured access.
"""

from __future__ import annotations

import keyword
import re
import textwrap
from typing import Any

import structlog

from ..metadata import ArtifactMetadata
from . import BaseGenerator

logger = structlog.get_logger(__name__)

_IDENTIFIER_RE = re.compile(r"[^a-zA-Z0-9_]")


def _to_identifier(text: str) -> str:
    """Convert arbitrary text to a valid Python identifier."""
    ident = _IDENTIFIER_RE.sub("_", text.strip().lower())
    ident = re.sub(r"_+", "_", ident).strip("_")
    if not ident or ident[0].isdigit():
        ident = f"section_{ident}"
    if keyword.iskeyword(ident):
        ident = f"{ident}_"
    return ident


def _escape_triple_quotes(text: str) -> str:
    """Escape triple-quote sequences inside a string."""
    return text.replace('"""', '\\"\\"\\"')


class PythonGenerator(BaseGenerator):
    """Generate a Python module artifact."""

    def generate(
        self,
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
        *,
        template_text: str | None = None,
    ) -> str:
        if template_text is not None:
            logger.debug("python_gen_using_template")
            return template_text

        lines: list[str] = []

        # Module docstring
        title = metadata.title or "Artifact"
        lines.append(f'"""Auto-generated artifact module: {title}.')
        lines.append("")
        lines.append("This module was produced by the SuperAI Artifact Converter.")
        if metadata.source_path:
            lines.append(f"Source: {metadata.source_path}")
        lines.append('"""')
        lines.append("")
        lines.append("from __future__ import annotations")
        lines.append("")
        lines.append("from dataclasses import dataclass, field")
        lines.append("from typing import Any")
        lines.append("")
        lines.append("")

        # Metadata dataclass
        lines.append("@dataclass(frozen=True)")
        lines.append("class ArtifactMetadata:")
        lines.append('    """Metadata for this artifact."""')
        lines.append("")
        lines.append(f"    title: str = {_py_repr(metadata.title or '')}")
        lines.append(f"    author: str = {_py_repr(metadata.author or '')}")
        lines.append(f"    date: str = {_py_repr(metadata.date or '')}")
        lines.append(f"    tags: tuple[str, ...] = {_py_repr(tuple(metadata.tags))}")
        lines.append(f"    description: str = {_py_repr(metadata.description or '')}")
        lines.append(f"    source_path: str = {_py_repr(metadata.source_path or '')}")
        lines.append(f"    source_format: str = {_py_repr(metadata.source_format or '')}")
        lines.append(f"    word_count: int = {metadata.word_count}")
        lines.append("")
        lines.append("")

        # Constants
        lines.append("# " + "-" * 72)
        lines.append("# Constants")
        lines.append("# " + "-" * 72)
        lines.append("")
        lines.append(f"METADATA = ArtifactMetadata()")
        lines.append("")

        # Section dataclass
        lines.append("")
        lines.append("@dataclass(frozen=True)")
        lines.append("class Section:")
        lines.append('    """A single content section."""')
        lines.append("")
        lines.append("    heading: str")
        lines.append("    level: int = 0")
        lines.append("    content: str = ''")
        lines.append("")
        lines.append("")

        # Section constants
        if sections:
            seen_identifiers: set[str] = set()
            section_var_names: list[str] = []

            for i, sec in enumerate(sections):
                heading = sec.get("heading", "")
                level = sec.get("level", 0)
                content = sec.get("content", "")

                base_ident = _to_identifier(heading) if heading else f"section_{i}"
                ident = base_ident
                counter = 2
                while ident in seen_identifiers:
                    ident = f"{base_ident}_{counter}"
                    counter += 1
                seen_identifiers.add(ident)
                var_name = ident.upper()
                section_var_names.append(var_name)

                escaped_content = _escape_triple_quotes(content)
                lines.append(f'{var_name} = Section(')
                lines.append(f'    heading={_py_repr(heading)},')
                lines.append(f'    level={level},')
                lines.append(f'    content="""{escaped_content}""",')
                lines.append(f')')
                lines.append("")

            lines.append("")
            lines.append("SECTIONS: tuple[Section, ...] = (")
            for var_name in section_var_names:
                lines.append(f"    {var_name},")
            lines.append(")")
        else:
            escaped_body = _escape_triple_quotes(body)
            lines.append(f'BODY: str = """{escaped_body}"""')
            lines.append("")
            lines.append("SECTIONS: tuple[Section, ...] = (")
            lines.append("    Section(heading='', content=BODY),")
            lines.append(")")

        lines.append("")

        # Convenience functions
        lines.append("")
        lines.append("def get_section_by_heading(heading: str) -> Section | None:")
        lines.append('    """Return the first section matching *heading* (case-insensitive)."""')
        lines.append("    lower = heading.lower()")
        lines.append("    for section in SECTIONS:")
        lines.append("        if section.heading.lower() == lower:")
        lines.append("            return section")
        lines.append("    return None")
        lines.append("")
        lines.append("")
        lines.append("def all_text() -> str:")
        lines.append('    """Return the full text of all sections concatenated."""')
        lines.append('    return "\\n\\n".join(s.content for s in SECTIONS if s.content)')
        lines.append("")

        output = "\n".join(lines)
        logger.debug("python_gen_done", chars=len(output))
        return output

    def file_extension(self) -> str:
        return ".py"


def _py_repr(value: Any) -> str:
    """Return a Python-repr-safe string for a value."""
    return repr(value)
