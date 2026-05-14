"""Shorts blur template (legacy center crop with blur fallback)."""

from app.services.composition.models import BackgroundMode, CompositionPlan, FitMode
from app.services.composition.planner import CompositionPlanner
from app.services.formats.models import OutputFormat
from app.services.templates.base import RenderTemplate


class ShortsBlurTemplate(RenderTemplate):
    """
    Legacy shorts template using center crop.
    
    Maintained for backward compatibility.
    """
    
    def __init__(self, blur_strength: int = 10):
        self.planner = CompositionPlanner()
        self.blur_strength = blur_strength
    
    @property
    def name(self) -> str:
        return "shorts_blur"
    
    @property
    def description(self) -> str:
        return "Center crop with blur background (legacy)"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate center crop composition."""
        return self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=FitMode.CENTER_CROP,
            background_mode=BackgroundMode.BLUR,
            blur_strength=self.blur_strength,
        )
    
    def supports_format(self, format_name: str) -> bool:
        """Supports vertical formats."""
        return format_name in ["shorts", "tiktok", "instagram_reel", "youtube_short"]
