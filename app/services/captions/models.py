"""Caption models for word-level timestamps and chunking."""

from pydantic import BaseModel, Field


class WordTimestamp(BaseModel):
    """
    Word-level timestamp from transcription.
    
    Attributes:
        word: The word text
        start: Start time in seconds
        end: End time in seconds
        confidence: Optional confidence score
    """
    
    word: str = Field(min_length=1)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    
    @property
    def duration(self) -> float:
        """Calculate word duration."""
        return self.end - self.start


class CaptionChunk(BaseModel):
    """
    Caption chunk with timing and word-level data.
    
    Attributes:
        text: Complete chunk text
        start: Chunk start time in seconds
        end: Chunk end time in seconds
        words: Word-level timestamps
        index: Chunk index in sequence
    """
    
    text: str = Field(min_length=1)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    words: list[WordTimestamp] = Field(default_factory=list)
    index: int = Field(ge=0, default=0)
    
    @property
    def duration(self) -> float:
        """Calculate chunk duration."""
        return self.end - self.start
    
    @property
    def word_count(self) -> int:
        """Get word count."""
        return len(self.words)


class CaptionStyle(BaseModel):
    """
    ASS subtitle styling configuration.
    
    Attributes:
        font_name: Font family name
        font_size: Font size in points
        primary_color: Primary text color (ASS format)
        outline_color: Outline/stroke color (ASS format)
        outline_width: Outline width in pixels
        shadow: Shadow depth
        alignment: Text alignment (ASS format)
        bold: Bold text
        italic: Italic text
        margin_v: Vertical margin
        margin_l: Left margin
        margin_r: Right margin
        animation_preset: Animation style preset
    """
    
    font_name: str = Field(default="Arial")
    font_size: int = Field(default=48, gt=0)
    primary_color: str = Field(default="&H00FFFFFF")
    outline_color: str = Field(default="&H00000000")
    outline_width: int = Field(default=3, ge=0)
    shadow: int = Field(default=2, ge=0)
    alignment: int = Field(default=2, ge=1, le=9)
    bold: bool = Field(default=True)
    italic: bool = Field(default=False)
    margin_v: int = Field(default=150, ge=0)
    margin_l: int = Field(default=60, ge=0)
    margin_r: int = Field(default=60, ge=0)
    animation_preset: str | None = Field(default=None)
    
    def to_ass_style(self, name: str = "Default") -> str:
        """
        Convert to ASS style definition.
        
        Args:
            name: Style name
            
        Returns:
            ASS style line
        """
        bold_flag = "-1" if self.bold else "0"
        italic_flag = "-1" if self.italic else "0"
        
        return (
            f"Style: {name},{{font_name}},{{font_size}},{self.primary_color},"
            f"&H000000FF,{self.outline_color},&H00000000,"
            f"{bold_flag},{italic_flag},0,0,100,100,0,0,"
            f"1,{self.outline_width},{self.shadow},{self.alignment},"
            f"{self.margin_l},{self.margin_r},{self.margin_v},1"
        ).format(font_name=self.font_name, font_size=self.font_size)
