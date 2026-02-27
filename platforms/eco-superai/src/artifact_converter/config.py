"""Configuration model for the artifact converter.

Defines all conversion rules, output directories, caching settings, and
server configuration using Pydantic v2 models.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import structlog
from pydantic import BaseModel, Field, field_validator, model_validator

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class InputFormat(str, Enum):
    """Supported input formats."""

    TXT = "txt"
    DOCX = "docx"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"

    @classmethod
    def from_extension(cls, ext: str) -> "InputFormat":
        """Resolve an ``InputFormat`` from a file extension string."""
        mapping: dict[str, InputFormat] = {
            ".txt": cls.TXT,
            ".text": cls.TXT,
            ".docx": cls.DOCX,
            ".pdf": cls.PDF,
            ".md": cls.MARKDOWN,
            ".markdown": cls.MARKDOWN,
            ".html": cls.HTML,
            ".htm": cls.HTML,
        }
        normalized = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        result = mapping.get(normalized)
        if result is None:
            raise ValueError(
                f"Unsupported input extension '{ext}'. "
                f"Supported: {', '.join(sorted(mapping.keys()))}"
            )
        return result


class OutputFormat(str, Enum):
    """Supported output formats."""

    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    PYTHON = "python"
    TYPESCRIPT = "typescript"

    @classmethod
    def extension(cls, fmt: "OutputFormat") -> str:
        """Return the canonical file extension for *fmt*."""
        return {
            cls.YAML: ".yaml",
            cls.JSON: ".json",
            cls.MARKDOWN: ".md",
            cls.PYTHON: ".py",
            cls.TYPESCRIPT: ".ts",
        }[fmt]


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class CacheSettings(BaseModel):
    """Settings for the incremental conversion cache."""

    enabled: bool = Field(default=True, description="Enable content-hash caching.")
    directory: Path = Field(
        default=Path(".artifact_cache"),
        description="Directory for cache storage.",
    )
    max_entries: int = Field(
        default=10_000,
        ge=1,
        description="Maximum number of cached entries before eviction.",
    )
    hash_algorithm: str = Field(
        default="sha256",
        description="Hash algorithm used for content fingerprinting.",
    )


class WatchSettings(BaseModel):
    """Settings for file-system watch mode."""

    debounce_seconds: float = Field(
        default=0.5,
        ge=0.0,
        description="Seconds to debounce rapid file-change events.",
    )
    recursive: bool = Field(default=True, description="Watch directories recursively.")
    ignore_patterns: list[str] = Field(
        default_factory=lambda: ["*.pyc", "__pycache__", ".git", ".artifact_cache"],
        description="Glob patterns of paths to ignore.",
    )


class ServerSettings(BaseModel):
    """Settings for the preview server."""

    host: str = Field(default="127.0.0.1", description="Bind address.")
    port: int = Field(default=8080, ge=1, le=65535, description="Bind port.")
    reload: bool = Field(default=True, description="Auto-reload on artifact changes.")


class ConversionRule(BaseModel):
    """A single input-to-output conversion rule."""

    input_format: InputFormat
    output_format: OutputFormat
    template: str | None = Field(
        default=None,
        description="Optional Jinja2 template name to use for output rendering.",
    )
    schema_path: str | None = Field(
        default=None,
        description="Optional JSON Schema path to validate the output against.",
    )


class ParallelSettings(BaseModel):
    """Settings for parallel/async batch processing."""

    max_workers: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Maximum number of concurrent conversion workers.",
    )
    chunk_size: int = Field(
        default=10,
        ge=1,
        description="Number of files per processing chunk.",
    )


# ---------------------------------------------------------------------------
# Root configuration
# ---------------------------------------------------------------------------


class ConverterConfig(BaseModel):
    """Root configuration for the artifact converter."""

    output_dir: Path = Field(
        default=Path("artifacts"),
        description="Default output directory for converted artifacts.",
    )
    template_dir: Path = Field(
        default=Path("templates"),
        description="Directory containing Jinja2 templates.",
    )
    default_output_format: OutputFormat = Field(
        default=OutputFormat.YAML,
        description="Default output format when none is specified.",
    )
    rules: list[ConversionRule] = Field(
        default_factory=list,
        description="Explicit conversion rules (override defaults).",
    )
    cache: CacheSettings = Field(default_factory=CacheSettings)
    watch: WatchSettings = Field(default_factory=WatchSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    parallel: ParallelSettings = Field(default_factory=ParallelSettings)
    metadata_extract: bool = Field(
        default=True,
        description="Automatically extract metadata from source files.",
    )
    strict_validation: bool = Field(
        default=False,
        description="Fail conversion if schema validation fails (otherwise warn).",
    )

    @field_validator("output_dir", "template_dir", mode="before")
    @classmethod
    def _coerce_path(cls, value: Any) -> Path:
        return Path(value) if not isinstance(value, Path) else value

    @model_validator(mode="after")
    def _log_config(self) -> "ConverterConfig":
        logger.debug("converter_config_loaded", output_dir=str(self.output_dir))
        return self

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    CONFIG_FILENAME: ClassVar[str] = ".artifact_converter.json"

    def save(self, directory: Path | None = None) -> Path:
        """Persist configuration to *directory* / ``.artifact_converter.json``."""
        target_dir = directory or Path.cwd()
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / self.CONFIG_FILENAME
        path.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        logger.info("config_saved", path=str(path))
        return path

    @classmethod
    def load(cls, directory: Path | None = None) -> "ConverterConfig":
        """Load configuration from *directory* / ``.artifact_converter.json``.

        Falls back to defaults when the file does not exist.
        """
        target_dir = directory or Path.cwd()
        path = target_dir / cls.CONFIG_FILENAME
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            logger.info("config_loaded_from_file", path=str(path))
            return cls.model_validate(data)
        logger.info("config_using_defaults")
        return cls()

    @classmethod
    def default_json(cls) -> str:
        """Return a pretty-printed JSON string of default settings."""
        return json.dumps(cls().model_dump(mode="json"), indent=2, default=str)
