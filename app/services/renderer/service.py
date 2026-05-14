"""Render service for orchestrating video rendering."""

from pathlib import Path

from app.config.settings import settings
from app.core.exceptions import FFmpegError
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.subprocess.runner import SubprocessRunner
from app.services.composition.models import CompositionPlan
from app.services.renderer.graph_builder import FFmpegGraphBuilder

logger = get_logger("renderer")


class RenderService:
    """
    Orchestrates final video rendering.
    
    Responsibilities:
        - Apply composition plans
        - Generate FFmpeg filter graphs
        - Execute rendering
        - Manage temporary artifacts
        - Coordinate subtitle overlays
    
    This service does NOT handle composition planning.
    It consumes CompositionPlan objects from the composition service.
    """
    
    def __init__(self):
        self.runner = SubprocessRunner()
        self.ffmpeg_path = settings.ffmpeg_path
    
    def render_composition(
        self,
        input_path: str | Path,
        output_path: str | Path,
        plan: CompositionPlan,
        subtitle_path: str | Path | None = None,
        quality: int | None = None,
    ) -> Path:
        """
        Render video using composition plan.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            plan: Composition plan
            subtitle_path: Optional ASS subtitle file
            quality: CRF quality (lower = better)
            
        Returns:
            Path to rendered video
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        quality = quality or settings.output_quality
        
        logger.info(
            f"Rendering composition: {plan.canvas_width}x{plan.canvas_height} "
            f"({plan.fit_mode.value})"
        )
        
        builder = FFmpegGraphBuilder()
        filter_complex = builder.build_composition_graph(plan)
        
        if not filter_complex:
            raise FFmpegError("Failed to build filter graph - empty result")
        
        # Render composition first, then add subtitles in a second pass if needed
        map_label = "[out]"
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(input_path),
            "-filter_complex", filter_complex,
            "-map", map_label,
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", str(quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        ]
        
        logger.debug(f"FFmpeg filter_complex: {filter_complex}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        result = self.runner.run(cmd)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg stderr: {result.stderr}")
            logger.error(f"FFmpeg stdout: {result.stdout}")
            logger.error(f"Filter complex was: {filter_complex}")
            raise FFmpegError(f"FFmpeg rendering failed. Check logs for details.")
        
        # If subtitles requested, burn them in a second pass
        if subtitle_path:
            logger.info("Adding subtitles in second pass")
            temp_output = Path(str(output_path).replace(".mp4", "_temp.mp4"))
            
            # Move the first output to temp
            import shutil
            shutil.move(output_path, temp_output)
            
            # Escape subtitle path for FFmpeg (Windows-style backslashes and colons)
            sub_path_str = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
            
            # Burn subtitles using subtitles filter
            sub_cmd = [
                self.ffmpeg_path,
                "-i", str(temp_output),
                "-vf", f"subtitles='{sub_path_str}'",
                "-c:a", "copy",
                "-y",
                str(output_path),
            ]
            
            logger.debug(f"Subtitle command: {' '.join(sub_cmd)}")
            
            sub_result = self.runner.run(sub_cmd)
            
            if sub_result.returncode != 0:
                logger.error(f"Subtitle rendering failed: {sub_result.stderr}")
                # Keep the non-subtitle version
                shutil.move(temp_output, output_path)
                logger.warning("Subtitles failed to render, keeping video without subtitles")
            else:
                # Clean up temp file
                temp_output.unlink()
                logger.info("Subtitles added successfully")
        
        logger.info(f"Render complete: {output_path}")
        
        return output_path
    
    def render_with_template(
        self,
        input_path: str | Path,
        output_path: str | Path,
        template_name: str,
        format_name: str,
        video_width: int,
        video_height: int,
        subtitle_path: str | Path | None = None,
        quality: int | None = None,
    ) -> Path:
        """
        Render video using template and format.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            template_name: Template identifier
            format_name: Format identifier
            video_width: Source video width
            video_height: Source video height
            subtitle_path: Optional subtitle file
            quality: CRF quality
            
        Returns:
            Path to rendered video
        """
        from app.services.formats.registry import FormatRegistry
        from app.services.templates.registry import TemplateRegistry
        
        output_format = FormatRegistry.get(format_name)
        template = TemplateRegistry.get(template_name)
        
        if not template.supports_format(format_name):
            raise FFmpegError(
                f"Template '{template_name}' does not support format '{format_name}'"
            )
        
        plan = template.generate_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
        )
        
        return self.render_composition(
            input_path=input_path,
            output_path=output_path,
            plan=plan,
            subtitle_path=subtitle_path,
            quality=quality,
        )
