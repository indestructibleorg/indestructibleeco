"""Artifact Converter — transform documents between formats.

Supports parsing TXT, DOCX, PDF, Markdown, and HTML sources and generating
YAML, JSON, Markdown, Python, and TypeScript outputs.  Features include
Jinja2 template rendering, JSON Schema validation, content-hash caching,
file-system watch mode, and a lightweight preview server.
"""

from __future__ import annotations

from .cache import ConversionCache
from .config import ConverterConfig, InputFormat, OutputFormat
from .generators import BaseGenerator, available_generators, get_generator
from .metadata import ArtifactMetadata, extract_metadata
from .parsers import BaseParser, ParseResult, available_parsers, get_parser

__all__ = [
    "ArtifactMetadata",
    "BaseGenerator",
    "BaseParser",
    "ConversionCache",
    "ConverterConfig",
    "InputFormat",
    "OutputFormat",
    "ParseResult",
    "available_generators",
    "available_parsers",
    "extract_metadata",
    "get_generator",
    "get_parser",
]


def convert_file(
    source_path: str,
    *,
    output_format: str | OutputFormat | None = None,
    output_dir: str | None = None,
    config: ConverterConfig | None = None,
) -> str:
    """High-level convenience: parse a file and generate output.

    Parameters
    ----------
    source_path:
        Path to the source document.
    output_format:
        Target format.  Defaults to ``config.default_output_format``.
    output_dir:
        Directory for the output file.  Defaults to ``config.output_dir``.
    config:
        Converter configuration.  Uses defaults when ``None``.

    Returns
    -------
    str
        The absolute path of the written output file.
    """
    from pathlib import Path

    cfg = config or ConverterConfig()
    src = Path(source_path)

    # Resolve formats
    in_fmt = InputFormat.from_extension(src.suffix)
    out_fmt = (
        OutputFormat(output_format)
        if isinstance(output_format, str)
        else output_format or cfg.default_output_format
    )

    # Parse
    parser = get_parser(in_fmt)
    raw = src.read_bytes() if in_fmt == InputFormat.DOCX else src.read_text(encoding="utf-8")
    result = parser.parse(raw, source_path=src)

    # Metadata
    meta = extract_metadata(
        result.body,
        source_path=src,
        source_format=in_fmt.value,
        parser_metadata=result.metadata,
    )

    # Cache check
    cache = ConversionCache(cfg.cache)
    if cache.enabled:
        from .cache import CacheKey

        content_hash = cache.content_hash(result.body)
        key = CacheKey(content_hash=content_hash, output_format=out_fmt.value)
        cached = cache.get(key)
        if cached is not None:
            out_dir = Path(output_dir) if output_dir else cfg.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / (src.stem + get_generator(out_fmt).file_extension())
            out_path.write_text(cached.output_text, encoding="utf-8")
            return str(out_path.resolve())

    # Generate
    generator = get_generator(out_fmt)
    output_text = generator.generate(
        body=result.body,
        metadata=meta,
        sections=result.sections,
    )

    # Write
    out_dir = Path(output_dir) if output_dir else cfg.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (src.stem + generator.file_extension())
    out_path.write_text(output_text, encoding="utf-8")

    # Cache store
    if cache.enabled:
        from .cache import CacheEntry, CacheKey

        content_hash = cache.content_hash(result.body)
        key = CacheKey(content_hash=content_hash, output_format=out_fmt.value)
        cache.put(CacheEntry(key=key, output_text=output_text, source_path=str(src)))

    return str(out_path.resolve())
