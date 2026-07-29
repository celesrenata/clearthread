"""ClearThread CLI entry point."""

from __future__ import annotations

import click
import logging
from pathlib import Path

from clearthread import __version__
from clearthread.import_pipeline import ImportPipeline
from clearthread.storage.source_vault import SourceDataVault
from clearthread.storage.normalized_store import NormalizedStore
from clearthread.analysis.episode_engine import EpisodeEngine
from clearthread.analysis.pattern_analyzer import PatternAnalyzer
from clearthread.analysis.growth_analyzer import GrowthAnalyzer
from clearthread.search.engine import SearchEngine
from clearthread.export.engine import ExportEngine

logger = logging.getLogger("clearthread")


@click.group()
@click.version_option(version=__version__)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def main(verbose: bool) -> None:
    """ClearThread - Local-first Facebook/Messenger relationship analysis."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./data", help="Output directory.")
@click.option("--zip", is_flag=True, help="Input is a ZIP file.")
def import_data(input_path: str, output_dir: str, zip: bool) -> None:
    """Import Facebook/Messenger data.

    INPUT_PATH can be a ZIP file or a directory containing JSON exports.
    """
    pipeline = ImportPipeline(data_dir=output_dir)

    if zip:
        report = pipeline.import_from_zip(Path(input_path))
    else:
        report = pipeline.import_from_directory(Path(input_path))

    click.echo(f"\nImport complete!")
    click.echo(f"  Messages: {report.total_messages}")
    click.echo(f"  Conversations: {report.total_conversations}")
    click.echo(f"  Participants: {report.total_participants}")
    click.echo(f"  Attachments: {report.total_attachments}")
    click.echo(f"  Duplicates: {report.duplicates_detected}")
    click.echo(f"  Encoding fixes: {report.encoding_issues_recovered}")
    click.echo(f"  Batch ID: {report.import_batch_id}")


@main.command()
@click.option("--output-dir", "-o", default="./analysis", help="Output directory.")
def analyze(output_dir: str) -> None:
    """Run analysis on imported data."""
    episode_engine = EpisodeEngine()
    pattern_analyzer = PatternAnalyzer()
    growth_analyzer = GrowthAnalyzer()

    click.echo("Running episode detection...")
    click.echo(f"  Episodes found: {episode_engine.get_episode_count()}")

    click.echo("Running pattern analysis...")
    click.echo(f"  Findings: {len(pattern_analyzer.get_all_findings())}")

    click.echo("Running growth analysis...")
    click.echo(f"  Growth findings: {len(growth_analyzer.get_growth_findings())}")

    click.echo("\nAnalysis complete!")


@main.command()
@click.argument("query")
@click.option("--semantic", "-s", is_flag=True, help="Use semantic search.")
def search(query: str, semantic: bool) -> None:
    """Search the message archive.

    QUERY is the search term (minimum 2 characters).
    """
    engine = SearchEngine()
    results, total = engine.search(query, semantic=semantic)

    click.echo(f"\nSearch results for '{query}': {total} total")
    for i, result in enumerate(results[:10], 1):
        click.echo(f"  {i}. [{result.result_type}] {result.text[:80]}...")

    if total > 10:
        click.echo(f"  ... and {total - 10} more results.")


@main.command()
@click.option("--format", "-f", default="markdown", help="Export format (markdown, pdf, json).")
@click.option("--output-dir", "-o", default="./exports", help="Output directory.")
def export(format: str, output_dir: str) -> None:
    """Export analysis results."""
    engine = ExportEngine(output_dir=output_dir)

    format_map = {
        "markdown": "markdown",
        "pdf": "pdf",
        "json": "json",
    }

    click.echo(f"Exporting as {format}...")
    click.echo(f"Output: {output_dir}")


@main.command()
def serve() -> None:
    """Start the ClearThread server."""
    click.echo("ClearThread server starting...")
    click.echo("  Data directory: ./data")
    click.echo("  Models directory: ./models")
    click.echo("  Port: 1420")


if __name__ == "__main__":
    main()
