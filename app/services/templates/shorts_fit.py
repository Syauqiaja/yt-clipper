"""Shorts fit-width template with blur background."""

from app.services.composition.models import BackgroundMode, CompositionPlan, FitMode
from app.services.composition.planner import CompositionPlanner
from app.services.formats.models import OutputFormat
from app.services.templates.base import RenderTemplate


class ShortsFitTemplate(RenderTemplate):
    """
    Shorts template using fit-width layout with blurred background.
    
    This is the new default template for vertical content.
    Preserves full source frame without aggressive cropping.
    """
    
    def __init__(self, blur_strength: int = 15):
        self.planner = CompositionPlanner()
        self.blur_strength = blur_strength
    
    @property
    def name(self) -> str:
        return "shorts_fit"
    
    @property
    def description(self) -> str:
        return "Fit video by width with blurred background for shorts"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate fit-width composition with blur background."""
        return self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=FitMode.FIT_WIDTH,
            background_mode=BackgroundMode.BLUR,
            blur_strength=self.blur_strength,
        )
    
    def supports_format(self, format_name: str) -> bool:
        """Supports vertical formats."""
        return format_name in ["shorts", "tiktok", "instagram_reel", "youtube_short", "portrait_45"]
