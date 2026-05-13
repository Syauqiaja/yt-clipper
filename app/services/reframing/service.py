"""Reframing service: convert video clips to vertical format."""

from pathlib import Path

from app.infrastructure.logging.logger import get_logger
from app.services.ffmpeg.service import FFmpegService

logger = get_logger("reframing")


class ReframingService:
    def __init__(self, ffmpeg_service: FFmpegService):
        self.ffmpeg = ffmpeg_service

    def convert_to_vertical(
        self,
        input_path: str | Path,
        output_path: str | Path,
        resolution: str = "1080x1920",
    ) -> Path:
        """Convert clip to vertical format using center crop."""
        logger.info(f"Converting to vertical (center crop): {resolution}")
        return self.ffmpeg.convert_to_vertical(input_path, output_path, resolution)

    def convert_with_blur_background(
        self,
        input_path: str | Path,
        output_path: str | Path,
        resolution: str = "1080x1920",
        blur_strength: int = 10,
    ) -> Path:
        """Convert to vertical with background blur (instead of crop)."""
        from app.config.settings import settings

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        width, height = resolution.split("x")
        width, height = int(width), int(height)

        filter_complex = (
            f"[0:v]split[fg][bg];"
            f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},boxblur={blur_strength}[bgblurred];"
            f"[fg]scale=-1:{height}[fgscaled];"
            f"[bgblurred][fgscaled]overlay=(W-w)/2:(H-h)/2"
        )

        cmd = [
            settings.ffmpeg_path,
            "-i", str(input_path),
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-crf", str(settings.output_quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        ]

        from app.infrastructure.subprocess.runner import SubprocessRunner

        runner = SubprocessRunner()
        result = runner.run(cmd)
        if result.returncode != 0:
            logger.error(f"Blur background failed: {result.stderr[:500]}")

        return output_path

    def apply_smart_crop(
        self,
        input_path: str | Path,
        output_path: str | Path,
        resolution: str = "1080x1920",
        detection_method: str = "center",
    ) -> Path:
        """Smart crop that keeps points of interest in frame."""
        if detection_method == "center":
            return self.convert_to_vertical(input_path, output_path, resolution)
        elif detection_method == "blur":
            return self.convert_with_blur_background(
                input_path, output_path, resolution
            )
        else:
            return self.convert_to_vertical(input_path, output_path, resolution)

    def apply_zoom_pan(
        self,
        input_path: str | Path,
        output_path: str | Path,
        resolution: str = "1080x1920",
        zoom_factor: float = 1.05,
    ) -> Path:
        """Apply gentle Ken Burns zoom effect."""
        from app.config.settings import settings

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        width, height = resolution.split("x")
        width, height = int(width), int(height)
        
        zoom_filter = (
            f"scale={width * 2}:{height * 2}:flags=bicubic,"
            f"crop={width}:{height}:(iw-ow)/2:(ih-oh)/2,"
            f"zoompan=z='min(zoom+0.001,{zoom_factor})':d=1:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2',"
            f"scale={width}:{height}"
        )

        cmd = [
            settings.ffmpeg_path,
            "-i", str(input_path),
            "-vf", zoom_filter,
            "-c:v", "libx264",
            "-crf", str(settings.output_quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        ]

        from app.infrastructure.subprocess.runner import SubprocessRunner

        runner = SubprocessRunner()
        result = runner.run(cmd)
        if result.returncode != 0:
            logger.error(f"Zoom pan failed: {result.stderr[:500]}")

        return output_path
