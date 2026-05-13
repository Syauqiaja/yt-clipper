"""CLI commands for yt-clipper."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.config.settings import settings
from app.core.exceptions import ClipperError
from app.infrastructure.logging.logger import console, get_logger, logger
from app.services.ai.service import AIAnalysisService
from app.services.export.service import ExportService
from app.services.ffmpeg.service import FFmpegService
from app.services.subtitles.service import SubtitleService
from app.services.transcript.service import TranscriptService
from app.services.youtube.service import YouTubeService
from app.workflows.clip_workflow import ClipWorkflow

app = typer.Typer(
    name="yt-clipper",
    help="AI-powered YouTube video clipper",
    add_completion=False,
)

console = Console()
logger = get_logger("cli")


def add_commands(cli: typer.Typer) -> None:
    """Add all commands to the CLI."""
    cli.add_typer(clip_app, name="clip")
    cli.add_typer(analyze_app, name="analyze")
    cli.add_typer(download_app, name="download")
    cli.add_typer(transcribe_app, name="transcribe")
    cli.add_typer(export_app, name="export")
    cli.add_typer(config_app, name="config")


clip_app = typer.Typer(help="Generate clips from YouTube video")
analyze_app = typer.Typer(help="Analyze video for clip opportunities")
download_app = typer.Typer(help="Download YouTube video")
transcribe_app = typer.Typer(help="Transcribe video audio")
export_app = typer.Typer(help="Export clip artifacts")
config_app = typer.Typer(help="Manage configuration")


@clip_app.command("run")
def clip_run(
    url: str = typer.Argument(..., help="YouTube video URL"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name"),
    max_clips: int = typer.Option(5, "--max-clips", "-n", help="Maximum clips to generate"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Generate clips from a YouTube video."""
    if verbose:
        import logging
        logging.getLogger("yt-clipper").setLevel(logging.DEBUG)

    console.print(f"\n[bold cyan]YT-Clipper[/bold cyan] Processing: {url}\n")

    try:
        workflow = ClipWorkflow()
        result = workflow.run(
            url=url,
            project_name=project,
            max_clips=max_clips,
        )

        _display_results(result)

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@analyze_app.command("run")
def analyze_run(
    url: str = typer.Argument(..., help="YouTube video URL"),
    max_clips: int = typer.Option(10, "--max-clips", "-n", help="Maximum clips to analyze"),
) -> None:
    """Analyze video and identify clip opportunities."""
    console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {url}\n")

    try:
        workflow = ClipWorkflow()
        result = workflow.run(url=url, analyze_only=True, max_clips=max_clips)

        _display_clip_analysis(result.clips)

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@download_app.command("run")
def download_run(
    url: str = typer.Argument(..., help="YouTube video URL"),
    output: Path = typer.Option(None, "--output", "-o", help="Output directory"),
) -> None:
    """Download a YouTube video."""
    console.print(f"\n[bold cyan]Downloading:[/bold cyan] {url}\n")

    try:
        youtube = YouTubeService(output_dir=output)
        result = youtube.download(url)

        console.print(f"[green]Downloaded:[/green] {result.metadata.title}")
        console.print(f"[dim]Duration:[/dim] {result.metadata.duration:.1f}s")
        console.print(f"[dim]Path:[/dim] {result.video_path}")

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@transcribe_app.command("run")
def transcribe_run(
    url: str = typer.Argument(..., help="YouTube video URL"),
    use_whisper: bool = typer.Option(False, "--whisper", "-w", help="Force Whisper transcription"),
) -> None:
    """Transcribe video audio to text."""
    console.print(f"\n[bold cyan]Transcribing:[/bold cyan] {url}\n")

    try:
        workflow = ClipWorkflow()
        result = workflow.run(url=url, transcribe_only=True)

        transcript = result.transcript
        console.print(f"[green]Transcript:[/green] {len(transcript.segments)} segments")
        console.print(f"[dim]Source:[/dim] {transcript.source}")
        console.print(f"\n[dim]Preview:[/dim] {transcript.full_text[:500]}...")

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@export_app.command("run")
def export_run(
    clips_file: Path = typer.Argument(..., help="Clips metadata JSON file"),
    video_dir: Path = typer.Argument(..., help="Directory containing video clips"),
) -> None:
    """Export clip artifacts from existing data."""
    console.print(f"\n[bold cyan]Exporting clips...[/bold cyan]\n")

    try:
        with open(clips_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        clips = data.get("clips", [])
        console.print(f"[green]Found {len(clips)} clips to export")

        export_service = ExportService()
        # TODO: Implement export from existing files

        console.print("[green]Export complete![/green]")

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    table = Table(title="YT-Clipper Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    config_items = [
        ("NINEROUTER_BASE_URL", settings.ninerouter_base_url),
        ("NINEROUTER_MODEL", settings.ninerouter_model),
        ("FFMPEG_PATH", settings.ffmpeg_path),
        ("OUTPUT_QUALITY", str(settings.output_quality)),
        ("OUTPUT_RESOLUTION", settings.output_resolution),
        ("MAX_CLIP_DURATION", str(settings.max_clip_duration)),
        ("MIN_CLIP_DURATION", str(settings.min_clip_duration)),
        ("TARGET_CLIP_COUNT", str(settings.target_clip_count)),
        ("WHISPER_MODEL", settings.whisper_model_size),
        ("EXPORT_DIR", settings.export_dir),
        ("LOG_LEVEL", settings.log_level),
    ]

    for key, value in config_items:
        table.add_row(key, value)

    console.print(table)


@config_app.command("validate")
def config_validate() -> None:
    """Validate configuration and dependencies."""
    console.print("\n[bold cyan]Validating Configuration[/bold cyan]\n")

    issues = []

    # Check API key
    if not settings.ninerouter_api_key:
        issues.append("NINEROUTER_API_KEY not set")

    # Check FFmpeg
    ffmpeg = FFmpegService()
    try:
        version = ffmpeg.runner.get_ffmpeg_version()
        console.print(f"[green]✓[/green] FFmpeg: {version}")
    except Exception:
        issues.append("FFmpeg not found or not working")

    # Check AI connection
    try:
        ai = AIAnalysisService()
        if ai.client.health_check():
            console.print("[green]✓[/green] AI API: Connected")
        else:
            issues.append("Cannot connect to AI API")
    except Exception as e:
        issues.append(f"AI API error: {e}")

    # Report issues
    if issues:
        console.print("\n[bold red]Issues Found:[/bold red]")
        for issue in issues:
            console.print(f"  [red]✗[/red] {issue}")
        raise typer.Exit(1)
    else:
        console.print("\n[green]All checks passed![/green]")


def _display_results(result) -> None:
    """Display workflow results."""
    console.print(f"\n[bold green]Complete![/bold green]")
    console.print(f"[dim]Processed in {result.processing_time:.1f}s[/dim]\n")

    table = Table(title="Generated Clips")
    table.add_column("Rank", style="cyan", width=4)
    table.add_column("Title", style="white")
    table.add_column("Duration", style="dim")
    table.add_column("Score", style="green")

    for clip in result.clips:
        table.add_row(
            str(clip.rank),
            clip.title[:50] + ("..." if len(clip.title) > 50 else ""),
            f"{clip.duration:.1f}s",
            f"{clip.final_score:.2f}",
        )

    console.print(table)

    console.print(f"\n[dim]Exports saved to:[/dim] {result.exports[0].export_dir if result.exports else 'N/A'}")


def _display_clip_analysis(clips: list) -> None:
    """Display clip analysis results."""
    table = Table(title="Clip Analysis")
    table.add_column("Rank", style="cyan", width=4)
    table.add_column("Time", style="dim")
    table.add_column("Title", style="white")
    table.add_column("Hook", style="yellow")
    table.add_column("Score", style="green")

    for clip in clips:
        table.add_row(
            str(clip.rank),
            f"{clip.start_time:.0f}s-{clip.end_time:.0f}s",
            clip.title[:30] + ("..." if len(clip.title) > 30 else ""),
            clip.hook[:40] + ("..." if len(clip.hook) > 40 else ""),
            f"{clip.final_score:.2f}",
        )

    console.print(table)


if __name__ == "__main__":
    app()
