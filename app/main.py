"""Main entry point for yt-clipper CLI."""

import sys
from typing import Optional

import typer
from rich.console import Console

from app.cli.commands import add_commands
from app.config.settings import settings
from app.infrastructure.logging.logger import logger

console = Console()

app = typer.Typer(
    name="yt-clipper",
    help="AI-powered YouTube video clipper - Generate viral short-form clips automatically",
    add_completion=False,
    no_args_is_help=True,
)

add_commands(app)


@app.callback()
def callback(
    version: bool = typer.Option(False, "--version", help="Show version"),
) -> None:
    """Global callback."""
    if version:
        console.print("[bold cyan]YT-Clipper[/bold cyan] v0.1.0")
        raise typer.Exit()


def main() -> None:
    """Main entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
