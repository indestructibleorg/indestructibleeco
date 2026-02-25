"""Generator registry for the artifact converter.

Each generator implements the :class:`BaseGenerator` protocol and is
registered against one or more :class:`~artifact_converter.config.OutputFormat`
values.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

from ..config import OutputFormat
from ..metadata import ArtifactMetadata

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Base generator
# ---------------------------------------------------------------------------


class BaseGenerator(ABC):
    """Abstract base for all output-format generators."""

    @abstractmethod
    def generate(
        self,
        body: str,
        metadata: ArtifactMetadata,
        sections: list[dict[str, Any]],
        *,
        template_text: str | None = None,
    ) -> str:
        """Produce the output text from parsed content.

        Parameters
        ----------
        body:
            The full plain-text body from the parser.
        metadata:
            Normalised metadata.
        sections:
            Heading/content section list from the parser.
        template_text:
            Optional pre-rendered Jinja2 template output that the generator
            may incorporate or use as the primary output.
        """

    @abstractmethod
    def file_extension(self) -> str:
        """Return the canonical file extension (e.g. ``'.yaml'``)."""


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[OutputFormat, BaseGenerator] = {}


def register_generator(fmt: OutputFormat, generator: BaseGenerator) -> None:
    """Register *generator* for the given :class:`OutputFormat`."""
    _REGISTRY[fmt] = generator
    logger.debug("generator_registered", format=fmt.value, generator=type(generator).__name__)


def get_generator(fmt: OutputFormat) -> BaseGenerator:
    """Return the registered generator for *fmt*, raising on miss."""
    gen = _REGISTRY.get(fmt)
    if gen is None:
        raise ValueError(
            f"No generator registered for format '{fmt.value}'. "
            f"Available: {[f.value for f in _REGISTRY]}"
        )
    return gen


def available_generators() -> dict[str, str]:
    """Return a mapping of format name to generator class name."""
    return {fmt.value: type(g).__name__ for fmt, g in _REGISTRY.items()}


# ---------------------------------------------------------------------------
# Auto-register built-in generators on import
# ---------------------------------------------------------------------------


def _auto_register() -> None:
    """Import and register all built-in generators."""
    from .json_gen import JsonGenerator
    from .markdown_gen import MarkdownGenerator
    from .python_gen import PythonGenerator
    from .typescript_gen import TypeScriptGenerator
    from .yaml_gen import YamlGenerator

    register_generator(OutputFormat.YAML, YamlGenerator())
    register_generator(OutputFormat.JSON, JsonGenerator())
    register_generator(OutputFormat.MARKDOWN, MarkdownGenerator())
    register_generator(OutputFormat.PYTHON, PythonGenerator())
    register_generator(OutputFormat.TYPESCRIPT, TypeScriptGenerator())


_auto_register()
