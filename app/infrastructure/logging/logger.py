import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from app.config.settings import settings

console = Console()


def setup_logging() -> logging.Logger:
    """Setup structured logging with rich handler."""
    
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=settings.debug,
                show_time=True,
                show_path=settings.debug,
            )
        ],
    )
    
    logger = logging.getLogger("yt-clipper")
    logger.setLevel(log_level)
    
    if settings.debug:
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("yt_dlp").setLevel(logging.DEBUG)
    else:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("yt_dlp").setLevel(logging.WARNING)
    
    return logger


logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"yt-clipper.{name}")
