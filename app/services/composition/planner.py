"""Composition planning service."""

from pathlib import Path

from app.infrastructure.logging.logger import get_logger
from app.services.composition.models import (
    BackgroundLayer,
    BackgroundMode,
    CompositionPlan,
    FitMode,
    VideoLayer,
)
from app.services.formats.models import OutputFormat

logger = get_logger("composition")


class CompositionPlanner:
    """
    Generates composition plans for multi-format video rendering.
    
    Responsibilities:
        - Calculate video positioning and scaling
        - Plan background layer rendering
        - Coordinate overlay placement
        - Ensure safe area compliance
    
    This service does NOT perform rendering directly.
    It generates plans consumed by the renderer.
    """
    
    def __init__(self):
        pass
    
    def plan_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
        fit_mode: FitMode = FitMode.FIT_WIDTH,
        background_mode: BackgroundMode = BackgroundMode.BLUR,
        blur_strength: int = 10,
    ) -> CompositionPlan:
        """
        Create composition plan for given video and output format.
        
        Args:
            video_width: Source video width
            video_height: Source video height
            output_format: Target output format
            fit_mode: How to fit video in canvas
            background_mode: Background rendering mode
            blur_strength: Blur intensity for blur mode
            
        Returns:
            CompositionPlan with complete layout specification
        """
        logger.info(
            f"Planning composition: {video_width}x{video_height} -> "
            f"{output_format.width}x{output_format.height} ({fit_mode.value})"
        )
        
        video_layer = self._calculate_video_layer(
            video_width,
            video_height,
            output_format.width,
            output_format.height,
            fit_mode,
        )
        
        background_layer = BackgroundLayer(
            mode=background_mode,
            blur_strength=blur_strength,
        )
        
        plan = CompositionPlan(
            canvas_width=output_format.width,
            canvas_height=output_format.height,
            background=background_layer,
            video=video_layer,
            fit_mode=fit_mode,
            safe_area_margin=output_format.safe_margin,
            metadata={
                "source_resolution": f"{video_width}x{video_height}",
                "output_format": output_format.name,
            },
        )
        
        logger.debug(
            f"Video layer: {video_layer.width}x{video_layer.height} "
            f"at ({video_layer.x}, {video_layer.y})"
        )
        
        return plan
    
    def _calculate_video_layer(
        self,
        video_width: int,
        video_height: int,
        canvas_width: int,
        canvas_height: int,
        fit_mode: FitMode,
    ) -> VideoLayer:
        """
        Calculate video layer dimensions and position.
        
        Args:
            video_width: Source video width
            video_height: Source video height
            canvas_width: Canvas width
            canvas_height: Canvas height
            fit_mode: Fit mode
            
        Returns:
            VideoLayer with calculated dimensions and position
        """
        if fit_mode == FitMode.FIT_WIDTH:
            return self._fit_width(video_width, video_height, canvas_width, canvas_height)
        elif fit_mode == FitMode.FIT_HEIGHT:
            return self._fit_height(video_width, video_height, canvas_width, canvas_height)
        elif fit_mode == FitMode.CENTER_CROP:
            return self._center_crop(video_width, video_height, canvas_width, canvas_height)
        elif fit_mode == FitMode.STRETCH:
            return self._stretch(canvas_width, canvas_height)
        else:
            return self._fit_width(video_width, video_height, canvas_width, canvas_height)
    
    def _fit_width(
        self,
        video_width: int,
        video_height: int,
        canvas_width: int,
        canvas_height: int,
    ) -> VideoLayer:
        """
        Fit video by width, preserve aspect ratio, center vertically.
        
        This is the new default behavior for Phase 2.
        """
        video_aspect = video_width / video_height
        canvas_aspect = canvas_width / canvas_height
        
        scaled_width = canvas_width
        scaled_height = int(canvas_width / video_aspect)
        
        x = 0
        y = (canvas_height - scaled_height) // 2
        
        return VideoLayer(
            width=scaled_width,
            height=scaled_height,
            x=x,
            y=y,
        )
    
    def _fit_height(
        self,
        video_width: int,
        video_height: int,
        canvas_width: int,
        canvas_height: int,
    ) -> VideoLayer:
        """Fit video by height, preserve aspect ratio, center horizontally."""
        video_aspect = video_width / video_height
        
        scaled_height = canvas_height
        scaled_width = int(canvas_height * video_aspect)
        
        x = (canvas_width - scaled_width) // 2
        y = 0
        
        return VideoLayer(
            width=scaled_width,
            height=scaled_height,
            x=x,
            y=y,
        )
    
    def _center_crop(
        self,
        video_width: int,
        video_height: int,
        canvas_width: int,
        canvas_height: int,
    ) -> VideoLayer:
        """Center crop video to fill canvas (legacy behavior)."""
        return VideoLayer(
            width=canvas_width,
            height=canvas_height,
            x=0,
            y=0,
        )
    
    def _stretch(
        self,
        canvas_width: int,
        canvas_height: int,
    ) -> VideoLayer:
        """Stretch video to fill canvas (may distort)."""
        return VideoLayer(
            width=canvas_width,
            height=canvas_height,
            x=0,
            y=0,
        )
