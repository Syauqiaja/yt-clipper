"""FFmpeg filter graph builder for modular video rendering."""

from pathlib import Path
from typing import Any

from app.infrastructure.logging.logger import get_logger
from app.services.composition.models import BackgroundMode, CompositionPlan, FitMode

logger = get_logger("ffmpeg.graph")


class FFmpegGraphBuilder:
    """
    Modular FFmpeg filter graph builder.
    
    Generates complex filter graphs from composition plans without
    hardcoding giant filter strings.
    
    Usage:
        builder = FFmpegGraphBuilder()
        builder.add_input("video.mp4")
        builder.add_background_blur(plan)
        builder.add_scaled_video(plan)
        builder.add_overlay(plan)
        filter_complex = builder.build()
    """
    
    def __init__(self):
        self.inputs: list[str] = []
        self.filters: list[str] = []
        self.output_label: str = "out"
        self._label_counter: int = 0
    
    def _next_label(self, prefix: str = "v") -> str:
        """Generate unique filter label."""
        label = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return label
    
    def add_input(self, input_path: str | Path) -> str:
        """
        Add input file.
        
        Args:
            input_path: Path to input video
            
        Returns:
            Input label (e.g., "0:v")
        """
        idx = len(self.inputs)
        self.inputs.append(str(input_path))
        return f"{idx}:v"
    
    def add_background_blur(
        self,
        plan: CompositionPlan,
        input_label: str = "0:v",
    ) -> str:
        """
        Add blurred background layer.
        
        Args:
            plan: Composition plan
            input_label: Input video label
            
        Returns:
            Output label for blurred background
        """
        if plan.background.mode != BackgroundMode.BLUR:
            return input_label
        
        bg_label = self._next_label("bg")
        blur_label = self._next_label("bgblur")
        
        blur_strength = plan.background.blur_strength
        
        self.filters.append(
            f"[{input_label}]scale={plan.canvas_width}:{plan.canvas_height}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={plan.canvas_width}:{plan.canvas_height},"
            f"boxblur={blur_strength}[{blur_label}]"
        )
        
        return blur_label
    
    def add_scaled_video(
        self,
        plan: CompositionPlan,
        input_label: str = "0:v",
    ) -> str:
        """
        Add scaled video layer based on fit mode.
        
        Args:
            plan: Composition plan
            input_label: Input video label
            
        Returns:
            Output label for scaled video
        """
        video = plan.video
        scaled_label = self._next_label("scaled")
        
        if plan.fit_mode == FitMode.FIT_WIDTH:
            self.filters.append(
                f"[{input_label}]scale={video.width}:{video.height}:"
                f"force_original_aspect_ratio=decrease[{scaled_label}]"
            )
        elif plan.fit_mode == FitMode.FIT_HEIGHT:
            self.filters.append(
                f"[{input_label}]scale={video.width}:{video.height}:"
                f"force_original_aspect_ratio=decrease[{scaled_label}]"
            )
        elif plan.fit_mode == FitMode.CENTER_CROP:
            self.filters.append(
                f"[{input_label}]scale={plan.canvas_width}:{plan.canvas_height}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={plan.canvas_width}:{plan.canvas_height}[{scaled_label}]"
            )
        elif plan.fit_mode == FitMode.STRETCH:
            self.filters.append(
                f"[{input_label}]scale={video.width}:{video.height}[{scaled_label}]"
            )
        else:
            self.filters.append(
                f"[{input_label}]scale={video.width}:{video.height}:"
                f"force_original_aspect_ratio=decrease[{scaled_label}]"
            )
        
        return scaled_label
    
    def add_overlay(
        self,
        background_label: str,
        foreground_label: str,
        x: int,
        y: int,
        output_label: str | None = None,
    ) -> str:
        """
        Add overlay filter.
        
        Args:
            background_label: Background layer label
            foreground_label: Foreground layer label
            x: X position
            y: Y position
            output_label: Optional output label
            
        Returns:
            Output label
        """
        out_label = output_label or self._next_label("overlay")
        
        self.filters.append(
            f"[{background_label}][{foreground_label}]overlay={x}:{y}[{out_label}]"
        )
        
        return out_label
    
    def add_ass_subtitles(
        self,
        input_label: str,
        subtitle_path: str | Path,
        output_label: str | None = None,
    ) -> str:
        """
        Add ASS subtitle overlay.
        
        Args:
            input_label: Input video label
            subtitle_path: Path to ASS subtitle file
            output_label: Optional output label
            
        Returns:
            Output label
        """
        out_label = output_label or self._next_label("subs")
        
        subtitle_path_str = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
        
        self.filters.append(
            f"[{input_label}]ass={subtitle_path_str}[{out_label}]"
        )
        
        return out_label
    
    def add_pad(
        self,
        input_label: str,
        width: int,
        height: int,
        x: int,
        y: int,
        color: str = "black",
        output_label: str | None = None,
    ) -> str:
        """
        Add padding filter.
        
        Args:
            input_label: Input label
            width: Pad width
            height: Pad height
            x: X position
            y: Y position
            color: Pad color
            output_label: Optional output label
            
        Returns:
            Output label
        """
        out_label = output_label or self._next_label("pad")
        
        self.filters.append(
            f"[{input_label}]pad={width}:{height}:{x}:{y}:color={color}[{out_label}]"
        )
        
        return out_label
    
    def build(self) -> str:
        """
        Build complete filter_complex string.
        
        Returns:
            FFmpeg filter_complex argument
        """
        if not self.filters:
            return ""
        
        filter_str = ";".join(self.filters)
        
        logger.debug(f"Built filter graph with {len(self.filters)} filters")
        
        return filter_str
    
    def build_composition_graph(self, plan: CompositionPlan) -> str:
        """
        Build complete filter graph from composition plan.
        
        This is a convenience method that generates the full graph
        for a standard composition with background and video layers.
        
        Args:
            plan: Composition plan
            
        Returns:
            Complete filter_complex string
        """
        input_label = "0:v"
        
        if plan.background.mode == BackgroundMode.BLUR:
            bg_label = self.add_background_blur(plan, input_label)
            fg_label = self.add_scaled_video(plan, input_label)
            
            final_label = self.add_overlay(
                background_label=bg_label,
                foreground_label=fg_label,
                x=plan.video.x,
                y=plan.video.y,
                output_label="out",
            )
        elif plan.background.mode == BackgroundMode.NONE:
            canvas_label = self._next_label("canvas")
            self.filters.append(
                f"color=c=black:s={plan.canvas_width}x{plan.canvas_height}[{canvas_label}]"
            )
            
            fg_label = self.add_scaled_video(plan, input_label)
            
            final_label = self.add_overlay(
                background_label=canvas_label,
                foreground_label=fg_label,
                x=plan.video.x,
                y=plan.video.y,
                output_label="out",
            )
        else:
            fg_label = self.add_scaled_video(plan, input_label)
            final_label = fg_label
        
        return self.build()
