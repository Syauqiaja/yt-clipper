"""CLI commands for yt-clipper with Phase 2 enhancements."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.config.settings import settings
from app.core.exceptions import ClipperError
from app.infrastructure.logging.logger import console, get_logger, logger
from app.services.ai.service import AIAnalysisService
from app.services.captions.presets import CaptionPresets
from app.services.export.service import ExportService
from app.services.ffmpeg.service import FFmpegService
from app.services.formats.registry import FormatRegistry
from app.services.subtitles.service import SubtitleService
from app.services.templates.registry import TemplateRegistry
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
    cli.add_typer(formats_app, name="formats")
    cli.add_typer(templates_app, name="templates")
    cli.add_typer(captions_app, name="captions")


clip_app = typer.Typer(help="Generate clips from YouTube video")
analyze_app = typer.Typer(help="Analyze video for clip opportunities")
download_app = typer.Typer(help="Download YouTube video")
transcribe_app = typer.Typer(help="Transcribe video audio")
export_app = typer.Typer(help="Export clip artifacts")
config_app = typer.Typer(help="Manage configuration")
formats_app = typer.Typer(help="List and manage output formats")
templates_app = typer.Typer(help="List and manage render templates")
captions_app = typer.Typer(help="Manage caption styles and presets")


@clip_app.command("run")
def clip_run(
    url: str = typer.Argument(..., help="YouTube video URL"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name"),
    max_clips: int = typer.Option(5, "--max-clips", "-n", help="Maximum clips to generate"),
    format: str = typer.Option("shorts", "--format", "-f", help="Output format (shorts, square, landscape)"),
    template: str = typer.Option("shorts_fit", "--template", "-t", help="Render template"),
    captions: bool = typer.Option(False, "--captions", "-c", help="Generate auto captions"),
    caption_style: str = typer.Option("tiktok", "--caption-style", help="Caption style preset"),
    karaoke: bool = typer.Option(False, "--karaoke", help="Enable karaoke-style captions"),
    upload_to_drive: bool = typer.Option(False, "--upload-to-drive", help="Upload to Google Drive"),
    webhook: bool = typer.Option(True, "--webhook/--no-webhook", help="Send webhook notification"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Generate clips from a YouTube video with Phase 2 rendering."""
    if verbose:
        import logging
        logging.getLogger("yt-clipper").setLevel(logging.DEBUG)

    if not json_output:
        console.print(f"\n[bold cyan]YT-Clipper[/bold cyan] Processing: {url}\n")
        console.print(f"Format: {format} | Template: {template} | Captions: {captions}\n")

    try:
        workflow = ClipWorkflow()
        result = workflow.run(
            url=url,
            project_name=project,
            max_clips=max_clips,
            output_format=format,
            template=template,
            captions=captions,
            caption_style=caption_style,
            karaoke=karaoke,
            verbose=verbose,
            upload_to_drive=upload_to_drive,
            send_webhook=webhook,
        )

        if json_output:
            # Build clips with drive upload info
            clips_output = []
            for clip, export in zip(result.clips, result.exports):
                clip_data = {
                    "rank": clip.rank,
                    "title": clip.title,
                    "start_time": clip.start_time,
                    "end_time": clip.end_time,
                    "duration": clip.duration,
                    "final_score": clip.final_score,
                    "scores": clip.scores.model_dump(),
                    "title_id": clip.title_id,
                    "title_en": clip.title_en,
                    "description_id": clip.description_id,
                    "description_en": clip.description_en,
                    "local_path": export.video_path,
                    "metadata_path": export.metadata_path,
                }
                
                # Add drive upload info if available
                if result.drive_uploads:
                    matching_upload = next(
                        (u for u in result.drive_uploads if u["clip_rank"] == clip.rank),
                        None
                    )
                    if matching_upload:
                        clip_data["drive_file_id"] = matching_upload["file_id"]
                        clip_data["drive_file_name"] = matching_upload["file_name"]
                        clip_data["drive_view_link"] = matching_upload["view_link"]
                        clip_data["drive_download_link"] = matching_upload["download_link"]
                        clip_data["drive_thumbnail_link"] = matching_upload["thumbnail_link"]
                
                clips_output.append(clip_data)
            
            output = {
                "success": True,
                "video_url": result.video_url,
                "video_title": result.video_metadata.title,
                "video_metadata": result.video_metadata.model_dump(),
                "clips_generated": len(result.clips),
                "processing_time": result.processing_time,
                "clips": clips_output,
                "drive_uploads": result.drive_uploads,
            }
            print(json.dumps(output, indent=2))
        else:
            _display_results(result, verbose)

    except ClipperError as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@formats_app.command("list")
def formats_list() -> None:
    """List all available output formats."""
    console.print("\n[bold cyan]Available Output Formats[/bold cyan]\n")
    
    formats = FormatRegistry.get_all()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Resolution", style="green")
    table.add_column("Aspect Ratio", style="yellow")
    table.add_column("Type", style="blue")
    
    for name, fmt in formats.items():
        format_type = "Vertical" if fmt.is_vertical else "Horizontal" if fmt.is_horizontal else "Square"
        table.add_row(
            name,
            f"{fmt.width}x{fmt.height}",
            fmt.aspect_ratio,
            format_type,
        )
    
    console.print(table)
    console.print()


@templates_app.command("list")
def templates_list() -> None:
    """List all available render templates."""
    console.print("\n[bold cyan]Available Render Templates[/bold cyan]\n")
    
    templates = TemplateRegistry.get_all()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    
    for name, template in templates.items():
        table.add_row(name, template.description)
    
    console.print(table)
    console.print()


@captions_app.command("list")
def captions_list() -> None:
    """List all available caption presets."""
    console.print("\n[bold cyan]Available Caption Presets[/bold cyan]\n")
    
    presets = CaptionPresets.list_presets()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Font", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Style", style="blue")
    
    for preset_name in presets:
        preset = CaptionPresets.get_preset(preset_name)
        style_desc = "Bold" if preset.bold else "Regular"
        if preset.italic:
            style_desc += " Italic"
        
        table.add_row(
            preset_name,
            preset.font_name,
            str(preset.font_size),
            style_desc,
        )
    
    console.print(table)
    console.print()


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
    """Download YouTube video."""
    console.print(f"\n[bold cyan]Downloading:[/bold cyan] {url}\n")

    try:
        yt_service = YouTubeService()
        result = yt_service.download_video(url, output_dir=output)

        console.print(f"[green]✓[/green] Downloaded: {result.video_path}")
        console.print(f"[green]✓[/green] Title: {result.metadata.title}")
        console.print(f"[green]✓[/green] Duration: {result.metadata.duration:.1f}s\n")

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@transcribe_app.command("run")
def transcribe_run(
    video_path: Path = typer.Argument(..., help="Path to video file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output transcript file"),
    word_timestamps: bool = typer.Option(False, "--words", "-w", help="Extract word-level timestamps"),
) -> None:
    """Transcribe video audio."""
    console.print(f"\n[bold cyan]Transcribing:[/bold cyan] {video_path}\n")

    try:
        transcript_service = TranscriptService()
        
        if word_timestamps:
            words = transcript_service.transcribe_with_word_timestamps(video_path)
            console.print(f"[green]✓[/green] Extracted {len(words)} word timestamps\n")
            
            if output:
                import json
                output_data = [
                    {"word": w.word, "start": w.start, "end": w.end}
                    for w in words
                ]
                output.write_text(json.dumps(output_data, indent=2))
                console.print(f"[green]✓[/green] Saved to: {output}\n")
        else:
            transcript = transcript_service.transcribe_with_whisper(video_path)
            console.print(f"[green]✓[/green] Transcribed {len(transcript.segments)} segments\n")
            
            if output:
                output.write_text(transcript.full_text)
                console.print(f"[green]✓[/green] Saved to: {output}\n")

    except ClipperError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    config_items = [
        ("AI Model", settings.ninerouter_model),
        ("Whisper Model", settings.whisper_model_size),
        ("Whisper Device", settings.whisper_device),
        ("Output Quality", str(settings.output_quality)),
        ("Max Clip Duration", f"{settings.max_clip_duration}s"),
        ("Min Clip Duration", f"{settings.min_clip_duration}s"),
        ("Temp Directory", str(settings.temp_dir)),
        ("Export Directory", str(settings.export_dir)),
    ]

    for key, value in config_items:
        table.add_row(key, value)

    console.print(table)
    console.print()


@config_app.command("validate")
def config_validate() -> None:
    """Validate configuration and dependencies."""
    console.print("\n[bold cyan]Validating Configuration[/bold cyan]\n")

    checks = []

    if settings.ninerouter_api_key and settings.ninerouter_api_key != "your-api-key-here":
        checks.append(("AI API Key", True, "Configured"))
    else:
        checks.append(("AI API Key", False, "Not configured"))

    try:
        ffmpeg_service = FFmpegService()
        checks.append(("FFmpeg", True, "Available"))
    except Exception:
        checks.append(("FFmpeg", False, "Not found"))

    try:
        import faster_whisper
        checks.append(("Faster-Whisper", True, "Installed"))
    except ImportError:
        checks.append(("Faster-Whisper", False, "Not installed"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    for name, status, details in checks:
        status_icon = "[green]✓[/green]" if status else "[red]✗[/red]"
        table.add_row(name, status_icon, details)

    console.print(table)
    console.print()


def _display_results(result, verbose: bool = False) -> None:
    """Display processing results."""
    console.print(f"\n[bold green]✓ Processing Complete[/bold green]\n")
    console.print(f"Video: {result.video_metadata.title}")
    console.print(f"Clips Generated: {len(result.clips)}")
    console.print(f"Processing Time: {result.processing_time:.1f}s\n")

    if verbose:
        _display_clip_analysis(result.clips)

    if result.exports:
        console.print("\n[bold cyan]Exported Clips:[/bold cyan]\n")
        for export in result.exports:
            if verbose:
                console.print(f"  • {export.clip.title}")
                console.print(f"    Path: {export.video_path}")
                console.print(f"    Score: {export.clip.final_score:.2f}\n")
            else:
                console.print(f"  • {export.clip.title_en or export.clip.title}")
                console.print(f"    Path: {export.video_path}\n")


def _display_clip_analysis(clips) -> None:
    """Display clip analysis table."""
    if not clips:
        console.print("[yellow]No clips found[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Title", style="green", width=40)
    table.add_column("Duration", style="yellow", width=10)
    table.add_column("Score", style="blue", width=8)
    table.add_column("Hook", style="magenta", width=8)

    for clip in clips[:10]:
        table.add_row(
            str(clip.rank),
            clip.title[:37] + "..." if len(clip.title) > 40 else clip.title,
            f"{clip.duration:.1f}s",
            f"{clip.final_score:.2f}",
            f"{clip.scores.hook_strength:.1f}",
        )

    console.print(table)
    console.print()
