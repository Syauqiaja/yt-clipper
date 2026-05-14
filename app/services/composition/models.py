"""Composition models for video layout planning."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FitMode(str, Enum):
    """Video fit modes for composition."""
    
    FIT_WIDTH = "fit_width"
    FIT_HEIGHT = "fit_height"
    SMART_CROP = "smart_crop"
    CENTER_CROP = "center_crop"
    STRETCH = "stretch"


class BackgroundMode(str, Enum):
    """Background rendering modes."""
    
    BLUR = "blur"
    COLOR = "color"
    GRADIENT = "gradient"
    IMAGE = "image"
    NONE = "none"


class OverlayPosition(str, Enum):
    """Overlay positioning presets."""
    
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class VideoLayer(BaseModel):
    """
    Video layer configuration in composition.
    
    Attributes:
        width: Layer width in pixels
        height: Layer height in pixels
        x: X position in canvas
        y: Y position in canvas
        scale: Scale factor
        opacity: Opacity (0.0 to 1.0)
    """
    
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    scale: float = Field(default=1.0, gt=0)
    opacity: float = Field(default=1.0, ge=0, le=1)


class BackgroundLayer(BaseModel):
    """
    Background layer configuration.
    
    Attributes:
        mode: Background rendering mode
        blur_strength: Blur intensity (for blur mode)
        color: Hex color code (for color mode)
        gradient_start: Start color for gradient
        gradient_end: End color for gradient
        image_path: Path to background image
    """
    
    mode: BackgroundMode
    blur_strength: int = Field(default=10, ge=0, le=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    gradient_start: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    gradient_end: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    image_path: str | None = None


class OverlayLayer(BaseModel):
    """
    Overlay layer configuration.
    
    Attributes:
        type: Overlay type (text, image, logo)
        position: Position preset
        x: Custom X position (overrides position)
        y: Custom Y position (overrides position)
        width: Overlay width
        height: Overlay height
        content: Overlay content (text or path)
        opacity: Opacity (0.0 to 1.0)
    """
    
    type: str = Field(description="Overlay type: text, image, logo")
    position: OverlayPosition = Field(default=OverlayPosition.CENTER)
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None
    content: str | None = None
    opacity: float = Field(default=1.0, ge=0, le=1)


class CompositionPlan(BaseModel):
    """
    Complete composition plan for video rendering.
    
    This is the output of composition planning and input to rendering.
    
    Attributes:
        canvas_width: Output canvas width
        canvas_height: Output canvas height
        background: Background layer configuration
        video: Main video layer configuration
        fit_mode: How video fits in canvas
        overlays: List of overlay layers
        safe_area_margin: Safe area margin in pixels
        metadata: Additional composition metadata
    """
    
    canvas_width: int = Field(gt=0)
    canvas_height: int = Field(gt=0)
    background: BackgroundLayer
    video: VideoLayer
    fit_mode: FitMode
    overlays: list[OverlayLayer] = Field(default_factory=list)
    safe_area_margin: int = Field(ge=0, default=40)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate canvas aspect ratio."""
        return self.canvas_width / self.canvas_height
    
    def get_safe_area(self) -> tuple[int, int, int, int]:
        """
        Get safe area bounds (x, y, width, height).
        
        Returns:
            Tuple of (x, y, width, height) for safe area
        """
        margin = self.safe_area_margin
        return (
            margin,
            margin,
            self.canvas_width - (2 * margin),
            self.canvas_height - (2 * margin),
        )
