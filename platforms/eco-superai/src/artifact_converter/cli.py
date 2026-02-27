"""CLI entry-point for the artifact converter.

Usage::

    superai-artifact convert input.md --format yaml --output ./out
    superai-artifact batch ./docs --format json --output ./artifacts
    superai-artifact watch ./docs --format yaml --output ./artifacts
    superai-artifact info input.md
    superai-artifact formats
"""

from __future__ import annotations

import sys
from pathlib import Path

import structlog
import typer

from .config import ConverterConfig, InputFormat, OutputFormat

logger = structlog.get_logger(__name__)

app = typer.Typer(
    name="superai-artifact",
    help="SuperAI Artifact Converter — transform documents between formats.",
    add_completion=False,
)


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------


@app.command()
def convert(
    source: Path = typer.Argument(..., help="Path to the source file."),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format."),
    output: Path = typer.Option(Path("artifacts"), "--output", "-o", help="Output directory."),
    template: str | None = typer.Option(None, "--template", "-t", help="Jinja2 template name."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable conversion cache."),
) -> None:
    """Convert a single source file to the target format."""
    if not source.exists():
        typer.echo(f"Error: source file not found: {source}", err=True)
        raise typer.Exit(1)

    cfg = ConverterConfig.load()
    if no_cache:
        cfg.cache.enabled = False

    try:
        from . import convert_file

        out_path = convert_file(
            str(source),
            output_format=format,
            output_dir=str(output),
            config=cfg,
        )
        typer.echo(f"Converted: {source} -> {out_path}")
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


# ---------------------------------------------------------------------------
# batch
# ---------------------------------------------------------------------------


@app.command()
def batch(
    directory: Path = typer.Argument(..., help="Directory containing source files."),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format."),
    output: Path = typer.Option(Path("artifacts"), "--output", "-o", help="Output directory."),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="Recurse into subdirectories."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable conversion cache."),
) -> None:
    """Batch-convert all supported files in a directory."""
    if not directory.is_dir():
        typer.echo(f"Error: not a directory: {directory}", err=True)
        raise typer.Exit(1)

    cfg = ConverterConfig.load()
    if no_cache:
        cfg.cache.enabled = False

    supported_exts = set()
    for fmt in InputFormat:
        if fmt == InputFormat.TXT:
            supported_exts.update({".txt", ".text"})
        elif fmt == InputFormat.DOCX:
            supported_exts.add(".docx")
        elif fmt == InputFormat.PDF:
            supported_exts.add(".pdf")
        elif fmt == InputFormat.MARKDOWN:
            supported_exts.update({".md", ".markdown"})
        elif fmt == InputFormat.HTML:
            supported_exts.update({".html", ".htm"})

    pattern = "**/*" if recursive else "*"
    files = [
        p for p in directory.glob(pattern)
        if p.is_file() and p.suffix.lower() in supported_exts
    ]

    if not files:
        typer.echo("No supported files found.")
        raise typer.Exit(0)

    from . import convert_file

    success = 0
    errors = 0
    for src in sorted(files):
        try:
            out_path = convert_file(
                str(src),
                output_format=format,
                output_dir=str(output),
                config=cfg,
            )
            typer.echo(f"  OK: {src} -> {out_path}")
            success += 1
        except Exception as exc:
            typer.echo(f"  FAIL: {src} — {exc}", err=True)
            errors += 1

    typer.echo(f"\nBatch complete: {success} converted, {errors} failed.")
    if errors > 0:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------


@app.command()
def watch(
    directory: Path = typer.Argument(..., help="Directory to watch for changes."),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format."),
    output: Path = typer.Option(Path("artifacts"), "--output", "-o", help="Output directory."),
) -> None:
    """Watch a directory and auto-convert files on change."""
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        typer.echo("Error: watchdog is required for watch mode (pip install watchdog)", err=True)
        raise typer.Exit(1)

    cfg = ConverterConfig.load()

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            src = Path(event.src_path)
            try:
                InputFormat.from_extension(src.suffix)
            except ValueError:
                return
            try:
                from . import convert_file

                out_path = convert_file(
                    str(src),
                    output_format=format,
                    output_dir=str(output),
                    config=cfg,
                )
                typer.echo(f"  Auto-converted: {src} -> {out_path}")
            except Exception as exc:
                typer.echo(f"  Watch error: {src} — {exc}", err=True)

    observer = Observer()
    observer.schedule(_Handler(), str(directory), recursive=True)
    observer.start()
    typer.echo(f"Watching {directory} for changes (Ctrl+C to stop)...")
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    typer.echo("Watch stopped.")


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------


@app.command()
def info(
    source: Path = typer.Argument(..., help="Path to the source file."),
) -> None:
    """Display metadata extracted from a source file."""
    if not source.exists():
        typer.echo(f"Error: file not found: {source}", err=True)
        raise typer.Exit(1)

    from .config import InputFormat
    from .metadata import extract_metadata
    from .parsers import get_parser

    try:
        in_fmt = InputFormat.from_extension(source.suffix)
        parser = get_parser(in_fmt)
        raw = source.read_bytes() if in_fmt == InputFormat.DOCX else source.read_text(encoding="utf-8")
        result = parser.parse(raw, source_path=source)
        meta = extract_metadata(
            result.body,
            source_path=source,
            source_format=in_fmt.value,
            parser_metadata=result.metadata,
        )
        import json

        typer.echo(json.dumps(meta.model_dump(mode="json"), indent=2, default=str))
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


# ---------------------------------------------------------------------------
# formats
# ---------------------------------------------------------------------------


@app.command()
def formats() -> None:
    """List all supported input and output formats."""
    from .generators import available_generators
    from .parsers import available_parsers

    typer.echo("Input formats:")
    for fmt, cls in sorted(available_parsers().items()):
        typer.echo(f"  {fmt:<12} ({cls})")

    typer.echo("\nOutput formats:")
    for fmt, cls in sorted(available_generators().items()):
        typer.echo(f"  {fmt:<12} ({cls})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()  # pragma: no cover
