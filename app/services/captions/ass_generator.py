"""ASS subtitle generator for advanced caption rendering."""

from pathlib import Path

from app.infrastructure.logging.logger import get_logger
from app.services.captions.models import CaptionChunk, CaptionStyle

logger = get_logger("captions.ass")


class ASSGenerator:
    """
    ASS subtitle file generator.
    
    Generates Advanced SubStation Alpha subtitle files with:
        - Custom styling
        - Positioning
        - Animation effects
        - Karaoke highlighting
    """
    
    def __init__(self, style: CaptionStyle):
        """
        Initialize generator.
        
        Args:
            style: Caption style configuration
        """
        self.style = style
    
    def generate(
        self,
        chunks: list[CaptionChunk],
        output_path: str | Path,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Path:
        """
        Generate ASS subtitle file.
        
        Args:
            chunks: Caption chunks
            output_path: Output file path
            video_width: Video width for positioning
            video_height: Video height for positioning
            
        Returns:
            Path to generated ASS file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating ASS subtitles: {len(chunks)} chunks")
        
        content = self._build_ass_content(chunks, video_width, video_height)
        
        output_path.write_text(content, encoding="utf-8")
        
        logger.info(f"ASS file saved: {output_path}")
        
        return output_path
    
    def _build_ass_content(
        self,
        chunks: list[CaptionChunk],
        video_width: int,
        video_height: int,
    ) -> str:
        """
        Build complete ASS file content.
        
        Args:
            chunks: Caption chunks
            video_width: Video width
            video_height: Video height
            
        Returns:
            Complete ASS file content
        """
        header = self._build_header(video_width, video_height)
        styles = self._build_styles()
        events = self._build_events(chunks)
        
        return f"{header}\n\n{styles}\n\n{events}"
    
    def _build_header(self, video_width: int, video_height: int) -> str:
        """Build ASS header section."""
        return f"""[Script Info]
Title: Auto-Generated Captions
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes"""
    
    def _build_styles(self) -> str:
        """Build ASS styles section."""
        style_line = self.style.to_ass_style("Default")
        
        return f"""[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}"""
    
    def _build_events(self, chunks: list[CaptionChunk]) -> str:
        """Build ASS events section."""
        events_header = """[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""
        
        event_lines = []
        for chunk in chunks:
            event_line = self._build_event(chunk)
            event_lines.append(event_line)
        
        return events_header + "\n" + "\n".join(event_lines)
    
    def _build_event(self, chunk: CaptionChunk) -> str:
        """
        Build single ASS event line.
        
        Args:
            chunk: Caption chunk
            
        Returns:
            ASS event line
        """
        start_time = self._format_timestamp(chunk.start)
        end_time = self._format_timestamp(chunk.end)
        
        text = chunk.text.replace("\n", "\\N")
        
        if self.style.animation_preset:
            text = self._apply_animation(text, self.style.animation_preset)
        
        return (
            f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
        )
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format timestamp for ASS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            ASS timestamp (H:MM:SS.CC)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _apply_animation(self, text: str, preset: str) -> str:
        """
        Apply animation preset to text.
        
        Args:
            text: Caption text
            preset: Animation preset name
            
        Returns:
            Text with ASS animation tags
        """
        if preset == "fade_in":
            return f"{{\\fad(200,0)}}{text}"
        elif preset == "fade_in_out":
            return f"{{\\fad(200,200)}}{text}"
        elif preset == "scale_in":
            return f"{{\\t(0,200,\\fscx120\\fscy120)\\t(200,400,\\fscx100\\fscy100)}}{text}"
        elif preset == "bounce":
            return f"{{\\move(0,50,0,0,0,200)}}{text}"
        else:
            return text
    
    def generate_with_karaoke(
        self,
        chunks: list[CaptionChunk],
        output_path: str | Path,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Path:
        """
        Generate ASS with karaoke-style word highlighting.
        
        Args:
            chunks: Caption chunks with word timestamps
            output_path: Output file path
            video_width: Video width
            video_height: Video height
            
        Returns:
            Path to generated ASS file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating karaoke ASS: {len(chunks)} chunks")
        
        header = self._build_header(video_width, video_height)
        styles = self._build_karaoke_styles()
        events = self._build_karaoke_events(chunks)
        
        content = f"{header}\n\n{styles}\n\n{events}"
        
        output_path.write_text(content, encoding="utf-8")
        
        logger.info(f"Karaoke ASS file saved: {output_path}")
        
        return output_path
    
    def _build_karaoke_styles(self) -> str:
        """Build styles for karaoke highlighting."""
        default_style = self.style.to_ass_style("Default")
        
        highlight_style = self.style.model_copy()
        highlight_style.primary_color = "&H0000FFFF"
        highlight_line = highlight_style.to_ass_style("Highlight")
        
        return f"""[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{default_style}
{highlight_line}"""
    
    def _build_karaoke_events(self, chunks: list[CaptionChunk]) -> str:
        """Build karaoke events with word-level timing."""
        events_header = """[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""
        
        event_lines = []
        for chunk in chunks:
            if chunk.words:
                event_line = self._build_karaoke_event(chunk)
                event_lines.append(event_line)
            else:
                event_line = self._build_event(chunk)
                event_lines.append(event_line)
        
        return events_header + "\n" + "\n".join(event_lines)
    
    def _build_karaoke_event(self, chunk: CaptionChunk) -> str:
        """
        Build karaoke event with word highlighting.
        
        Args:
            chunk: Caption chunk with word timestamps
            
        Returns:
            ASS karaoke event line
        """
        start_time = self._format_timestamp(chunk.start)
        end_time = self._format_timestamp(chunk.end)
        
        karaoke_text = ""
        for word in chunk.words:
            duration_cs = int((word.end - word.start) * 100)
            karaoke_text += f"{{\\k{duration_cs}}}{word.word} "
        
        karaoke_text = karaoke_text.strip()
        
        return (
            f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}"
        )
