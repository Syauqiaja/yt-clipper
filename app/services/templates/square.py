"""Square format template."""

from app.services.composition.models import BackgroundMode, CompositionPlan, FitMode
from app.services.composition.planner import CompositionPlanner
from app.services.formats.models import OutputFormat
from app.services.templates.base import RenderTemplate


class SquareTemplate(RenderTemplate):
    """
    Square format template for Instagram posts and other 1:1 content.
    """
    
    def __init__(self, fit_mode: FitMode = FitMode.FIT_WIDTH):
        self.planner = CompositionPlanner()
        self.fit_mode = fit_mode
    
    @property
    def name(self) -> str:
        return "square"
    
    @property
    def description(self) -> str:
        return "Square 1:1 format for Instagram posts"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate square composition."""
        video_aspect = video_width / video_height
        
        if video_aspect > 1.0:
            fit_mode = FitMode.FIT_HEIGHT
        else:
            fit_mode = FitMode.FIT_WIDTH
        
        return self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=fit_mode,
            background_mode=BackgroundMode.BLUR,
            blur_strength=12,
        )
    
    def supports_format(self, format_name: str) -> bool:
        """Supports square format."""
        return format_name == "square"
