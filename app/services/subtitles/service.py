"""Subtitles service: generate SRT and ASS subtitle files."""

from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import ClipCandidate, SubtitleLine, TranscriptSegment

logger = get_logger("subtitles")


class SubtitleService:
    def __init__(self):
        self.font = settings.subtitle_font
        self.font_size = settings.subtitle_font_size
        self.primary_color = settings.subtitle_primary_color
        self.outline_color = settings.subtitle_outline_color

    def format_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs - int(secs)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{millisecs:03d}"

    def format_vtt_timestamp(self, seconds: float) -> str:
        """Format seconds to VTT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs - int(secs)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d}.{millisecs:03d}"

    def generate_srt(
        self,
        segments: list[TranscriptSegment],
        clip_start: float,
        clip_end: float,
    ) -> str:
        """Generate SRT subtitles for a clip."""
        lines = []
        counter = 1

        for seg in segments:
            if seg.end < clip_start or seg.start > clip_end:
                continue

            srt_start = max(seg.start - clip_start, 0)
            srt_end = min(seg.end, clip_end) - clip_start

            if srt_end - srt_start < 0.5:
                continue

            lines.append(str(counter))
            lines.append(
                f"{self.format_timestamp(srt_start)} --> {self.format_timestamp(srt_end)}"
            )
            lines.append(seg.text)
            lines.append("")
            counter += 1

        return "\n".join(lines)

    def generate_vtt(
        self,
        segments: list[TranscriptSegment],
        clip_start: float,
        clip_end: float,
    ) -> str:
        """Generate WebVTT subtitles for a clip."""
        lines = ["WEBVTT", ""]

        for seg in segments:
            if seg.end < clip_start or seg.start > clip_end:
                continue

            vtt_start = max(seg.start - clip_start, 0)
            vtt_end = min(seg.end, clip_end) - clip_start

            if vtt_end - vtt_start < 0.5:
                continue

            lines.append(
                f"{self.format_vtt_timestamp(vtt_start)} --> {self.format_vtt_timestamp(vtt_end)}"
            )
            lines.append(seg.text)
            lines.append("")

        return "\n".join(lines)

    def generate_ass(
        self,
        segments: list[TranscriptSegment],
        clip_start: float,
        clip_end: float,
        style: str = "tiktok",
    ) -> str:
        """Generate ASS subtitles with TikTok-style formatting."""
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.font},{self.font_size * 2.5},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for seg in segments:
            if seg.end < clip_start or seg.start > clip_end:
                continue

            ass_start = max(seg.start - clip_start, 0)
            ass_end = min(seg.end, clip_end) - clip_start

            if ass_end - ass_start < 0.5:
                continue

            start_str = self._format_ass_time(ass_start)
            end_str = self._format_ass_time(ass_end)

            text = seg.text
            events.append(
                f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}"
            )

        return ass_header + "\n".join(events)

    def _format_ass_time(self, seconds: float) -> str:
        """Format seconds to ASS timestamp (H:MM:SS.cc)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds - int(seconds)) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def generate_subtitle_file(
        self,
        segments: list[TranscriptSegment],
        clip: ClipCandidate,
        output_path: str | Path,
        subtitle_format: str = "srt",
    ) -> Path:
        """Generate and save subtitle file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if subtitle_format == "srt":
            content = self.generate_srt(segments, clip.start_time, clip.end_time)
        elif subtitle_format == "vtt":
            content = self.generate_vtt(segments, clip.start_time, clip.end_time)
        elif subtitle_format == "ass":
            content = self.generate_ass(segments, clip.start_time, clip.end_time)
        else:
            content = self.generate_srt(segments, clip.start_time, clip.end_time)

        output_path.write_text(content, encoding="utf-8")
        logger.debug(f"Subtitle file saved: {output_path}")
        return output_path

    def generate_tiktok_captions(
        self,
        segments: list[TranscriptSegment],
        clip: ClipCandidate,
    ) -> list[SubtitleLine]:
        """Generate TikTok-style animated caption segments."""
        subtitle_lines = []

        for i, seg in enumerate(segments):
            if seg.end < clip.start_time or seg.start > clip.end_time:
                continue

            rel_start = max(seg.start - clip.start_time, 0)
            rel_end = min(seg.end, clip.end_time) - clip.start_time

            if rel_end - rel_start < 0.5:
                continue

            subtitle_lines.append(
                SubtitleLine(
                    index=i + 1,
                    start_time=rel_start,
                    end_time=rel_end,
                    text=seg.text,
                )
            )

        return subtitle_lines
