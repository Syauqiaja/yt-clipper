import shutil
import subprocess as sp
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.core.exceptions import FFmpegError
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.subprocess.runner import SubprocessRunner

logger = get_logger("ffmpeg.service")


class FFmpegService:
    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
        self.ffprobe_path = settings.ffprobe_path
        self.runner = SubprocessRunner()

        if not self._check_ffmpeg():
            if shutil.which("ffmpeg"):
                self.ffmpeg_path = "ffmpeg"
                self.ffprobe_path = "ffprobe"
            else:
                raise FFmpegError("FFmpeg not found. Install ffmpeg first.")
    
    def _check_ffmpeg(self) -> bool:
        return self.runner.check_command_exists(self.ffmpeg_path)

    def _build_cmd(self, *args: str) -> list[str]:
        return [self.ffmpeg_path, *args]

    def _build_probe_cmd(self, *args: str) -> list[str]:
        return [self.ffprobe_path, *args]

    def get_video_info(self, input_path: str | Path) -> dict[str, Any]:
        """Get video file metadata using ffprobe."""
        cmd = self._build_probe_cmd(
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(input_path),
        )

        import json
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to probe video: {result.stderr}")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            raise FFmpegError(f"ffprobe returned invalid JSON")

    def get_duration(self, input_path: str | Path) -> float:
        """Get video duration in seconds."""
        info = self.get_video_info(input_path)
        return float(info.get("format", {}).get("duration", 0))

    def cut_clip(
        self,
        input_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
        quality: int | None = None,
    ) -> Path:
        """Cut a clip between start and end time with smart seeking."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        quality = quality or settings.output_quality

        cmd = self._build_cmd(
            "-ss", str(start_time),
            "-i", str(input_path),
            "-ss", "0",
            "-to", str(end_time - start_time),
            "-c:v", "libx264",
            "-crf", str(quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-avoid_negative_ts", "1",
            "-y",
            str(output_path),
        )

        logger.info(f"Cutting clip: {start_time:.1f}s - {end_time:.1f}s")
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to cut clip: {result.stderr[:500]}")

        logger.debug(f"Clip saved: {output_path}")
        return output_path

    def convert_to_vertical(
        self,
        input_path: str | Path,
        output_path: str | Path,
        resolution: str = "1080x1920",
    ) -> Path:
        """Convert a clip to vertical 9:16 format with smart crop."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        width, height = resolution.split("x")
        width, height = int(width), int(height)

        filter_str = (
            f"crop=trunc(ih*9/16/2)*2:ih,"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        )

        cmd = self._build_cmd(
            "-i", str(input_path),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-crf", str(settings.output_quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        )

        logger.info(f"Converting to vertical: {resolution}")
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to convert to vertical: {result.stderr[:500]}")

        return output_path

    def add_subtitles(
        self,
        input_path: str | Path,
        subtitle_path: str | Path,
        output_path: str | Path,
    ) -> Path:
        """Burn subtitles into video."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = self._build_cmd(
            "-i", str(input_path),
            "-vf", f"subtitles={subtitle_path}",
            "-c:v", "libx264",
            "-crf", str(settings.output_quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        )

        logger.info("Burning subtitles into video")
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to add subtitles: {result.stderr[:500]}")

        return output_path

    def trim_silence(
        self,
        input_path: str | Path,
        output_path: str | Path,
        silence_threshold: float = -30.0,
        min_silence_duration: float = 0.5,
    ) -> Path:
        """Trim silence from beginning and end of audio."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = self._build_cmd(
            "-i", str(input_path),
            "-af", (
                f"silenceremove=start_periods=1:start_duration={min_silence_duration}:"
                f"start_threshold={silence_threshold}dB,"
                f"silenceremove=stop_periods=1:stop_duration={min_silence_duration}:"
                f"stop_threshold={silence_threshold}dB"
            ),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        )

        logger.info("Trimming silence")
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to trim silence: {result.stderr[:500]}")

        return output_path

    def normalize_audio(
        self,
        input_path: str | Path,
        output_path: str | Path,
        loudness_target: float = -14.0,
    ) -> Path:
        """Normalize audio to target loudness."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = self._build_cmd(
            "-i", str(input_path),
            "-af", f"loudnorm=I={loudness_target}:LRA=7:TP=-1.5",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path),
        )

        logger.info(f"Normalizing audio to {loudness_target} LUFS")
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to normalize audio: {result.stderr[:500]}")

        return output_path

    def add_fade_effects(
        self,
        input_path: str | Path,
        output_path: str | Path,
        fade_in: float = 0.3,
        fade_out: float = 0.3,
    ) -> Path:
        """Add fade in/out video effects."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = self._build_cmd(
            "-i", str(input_path),
            "-vf", f"fade=t=in:st=0:d={fade_in},fade=t=out:st={self.get_duration(input_path) - fade_out}:d={fade_out}",
            "-c:v", "libx264",
            "-crf", str(settings.output_quality),
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-af", f"afade=t=in:st=0:d={fade_in},afade=t=out:st={self.get_duration(input_path) - fade_out}:d={fade_out}",
            "-y",
            str(output_path),
        )

        logger.info("Adding fade effects")
        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to add fade effects: {result.stderr[:500]}")

        return output_path

    def generate_thumbnail(
        self,
        input_path: str | Path,
        output_path: str | Path,
        at_time: float = 0,
        resolution: str = "1080x1920",
    ) -> Path:
        """Generate a thumbnail at a specific time."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        width, height = resolution.split("x")
        width, height = int(width), int(height)

        cmd = self._build_cmd(
            "-ss", str(at_time),
            "-i", str(input_path),
            "-vf", f"crop=trunc(ih*{width}/{height}/2)*2:ih,scale={width}:{height}",
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            str(output_path),
        )

        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to generate thumbnail: {result.stderr[:500]}")

        return output_path

    def create_concatenated_video(
        self,
        input_paths: list[Path],
        output_path: str | Path,
    ) -> Path:
        """Concatenate multiple video clips."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        concat_file = Path(settings.temp_dir) / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for p in input_paths:
                f.write(f"file '{p.absolute()}'\n")

        cmd = self._build_cmd(
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            "-y",
            str(output_path),
        )

        result = self.runner.run(cmd)
        if result.returncode != 0:
            raise FFmpegError(f"Failed to concatenate videos: {result.stderr[:500]}")

        return output_path
