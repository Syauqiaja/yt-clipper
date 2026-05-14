"""Caption service for word-level timestamps and ASS generation."""

from pathlib import Path

from app.infrastructure.logging.logger import get_logger
from app.services.captions.ass_generator import ASSGenerator
from app.services.captions.chunker import CaptionChunker
from app.services.captions.models import CaptionChunk, CaptionStyle, WordTimestamp
from app.services.captions.presets import CaptionPresets

logger = get_logger("captions")


class CaptionService:
    """
    High-level caption service.
    
    Orchestrates caption generation pipeline:
        - Word timestamp extraction
        - Intelligent chunking
        - ASS subtitle generation
        - Style application
    """
    
    def __init__(
        self,
        style: CaptionStyle | None = None,
        max_words_per_chunk: int = 5,
        max_duration: float = 3.0,
    ):
        """
        Initialize caption service.
        
        Args:
            style: Caption style (defaults to TikTok preset)
            max_words_per_chunk: Maximum words per caption
            max_duration: Maximum chunk duration
        """
        self.style = style or CaptionPresets.tiktok()
        self.chunker = CaptionChunker(
            max_words_per_chunk=max_words_per_chunk,
            max_duration=max_duration,
        )
        self.generator = ASSGenerator(self.style)
    
    def generate_captions(
        self,
        words: list[WordTimestamp],
        output_path: str | Path,
        video_width: int = 1080,
        video_height: int = 1920,
        karaoke: bool = False,
    ) -> Path:
        """
        Generate caption file from word timestamps.
        
        Args:
            words: Word-level timestamps
            output_path: Output ASS file path
            video_width: Video width for positioning
            video_height: Video height for positioning
            karaoke: Enable karaoke-style highlighting
            
        Returns:
            Path to generated ASS file
        """
        logger.info(f"Generating captions from {len(words)} words")
        
        chunks = self.chunker.chunk_words(words)
        
        if karaoke:
            return self.generator.generate_with_karaoke(
                chunks=chunks,
                output_path=output_path,
                video_width=video_width,
                video_height=video_height,
            )
        else:
            return self.generator.generate(
                chunks=chunks,
                output_path=output_path,
                video_width=video_width,
                video_height=video_height,
            )
    
    def generate_from_chunks(
        self,
        chunks: list[CaptionChunk],
        output_path: str | Path,
        video_width: int = 1080,
        video_height: int = 1920,
        karaoke: bool = False,
    ) -> Path:
        """
        Generate caption file from pre-chunked captions.
        
        Args:
            chunks: Caption chunks
            output_path: Output ASS file path
            video_width: Video width
            video_height: Video height
            karaoke: Enable karaoke highlighting
            
        Returns:
            Path to generated ASS file
        """
        if karaoke:
            return self.generator.generate_with_karaoke(
                chunks=chunks,
                output_path=output_path,
                video_width=video_width,
                video_height=video_height,
            )
        else:
            return self.generator.generate(
                chunks=chunks,
                output_path=output_path,
                video_width=video_width,
                video_height=video_height,
            )
