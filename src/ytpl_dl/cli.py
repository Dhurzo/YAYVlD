from pathlib import Path
from typing import Annotated

import typer

from ytpl_dl.config import DownloadConfig
from ytpl_dl.errors import YtplDlError
from ytpl_dl.logging import setup_logging
from ytpl_dl.playlist import DownloadSummary, PlaylistDownloader

app = typer.Typer(
    name="ytpl-dl",
    help="Download all videos from a YouTube playlist in maximum quality.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.command()
def download(
    playlist_url: Annotated[str, typer.Argument(help="YouTube playlist URL")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(
        "downloads"
    ),
    fmt: Annotated[
        str, typer.Option("--format", "-f", help="yt-dlp format string")
    ] = "bestvideo+bestaudio/best",
    merge_format: Annotated[
        str, typer.Option("--merge-format", "-m", help="Merge output format")
    ] = "mkv",
    concurrent: Annotated[
        int, typer.Option("--concurrent", "-c", help="Concurrent fragment downloads", min=1, max=16)
    ] = 8,
    retries: Annotated[int, typer.Option("--retries", "-r", help="Download retries", min=0)] = 10,
    proxy: Annotated[str | None, typer.Option("--proxy", "-p", help="HTTP/HTTPS proxy URL")] = None,
    no_archive: Annotated[
        bool, typer.Option("--no-archive", help="Disable download archive (no resume)")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Overwrite existing files")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
    ] = False,
    json_log: Annotated[
        bool, typer.Option("--json-log", help="Output structured JSON logs")
    ] = False,
) -> None:
    """Download all videos from a YouTube playlist."""
    setup_logging(verbose=verbose, json_output=json_log)
    config = DownloadConfig(
        output_dir=output,
        format=fmt,
        merge_output_format=merge_format,
        concurrent_fragments=concurrent,
        retries=retries,
        download_archive=None if no_archive else output / ".download_archive",
        overwrite=overwrite,
        proxy=proxy,
        verbose=verbose,
    )
    try:
        downloader = PlaylistDownloader(config)
        summary = downloader.download(playlist_url)
    except YtplDlError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    _print_summary(summary)

    if summary.failed > 0:
        raise typer.Exit(code=1)


def _print_summary(summary: DownloadSummary) -> None:
    typer.echo("")
    typer.echo("Download Complete")
    typer.echo(f"  Total videos:  {summary.total}")
    typer.echo(f"  Succeeded:     {summary.succeeded}")
    typer.echo(f"  Failed:        {summary.failed}")
    typer.echo(f"  Skipped:       {summary.skipped}")
    typer.echo(f"  Success rate:  {summary.success_rate:.1f}%")
    if summary.errors:
        typer.echo("Errors:")
        for err in summary.errors[:5]:
            typer.echo(f"  - {err}")
        if len(summary.errors) > 5:
            remaining = len(summary.errors) - 5
            typer.echo(f"  ... and {remaining} more")
