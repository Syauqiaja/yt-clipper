"""Output format models for multi-format rendering."""

from pydantic import BaseModel, Field


class OutputFormat(BaseModel):
    """
    Defines output format specifications for video rendering.
    
    Attributes:
        name: Unique format identifier
        width: Canvas width in pixels
        height: Canvas height in pixels
        aspect_ratio: Human-readable aspect ratio
        safe_margin: Margin in pixels for safe area
        caption_zone_height: Height reserved for captions in pixels
    """
    
    name: str = Field(description="Format identifier")
    width: int = Field(gt=0, description="Canvas width in pixels")
    height: int = Field(gt=0, description="Canvas height in pixels")
    aspect_ratio: str = Field(description="Aspect ratio (e.g., '9:16')")
    safe_margin: int = Field(ge=0, default=40, description="Safe area margin in pixels")
    caption_zone_height: int = Field(ge=0, default=200, description="Caption zone height in pixels")
    
    @property
    def ratio(self) -> float:
        """Calculate numeric aspect ratio."""
        return self.width / self.height
    
    @property
    def is_vertical(self) -> bool:
        """Check if format is vertical (portrait)."""
        return self.height > self.width
    
    @property
    def is_square(self) -> bool:
        """Check if format is square."""
        return self.width == self.height
    
    @property
    def is_horizontal(self) -> bool:
        """Check if format is horizontal (landscape)."""
        return self.width > self.height
