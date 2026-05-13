"""Main workflow: orchestrates the entire clip generation pipeline."""

import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn

from app.config.settings import settings
from app.core.enums import ProcessingStage
from app.core.exceptions import ClipperError
from app.infrastructure.logging.logger import get_logger, logger
from app.schemas.models import ClipCandidate, ClipExport, ProcessingResult, Transcript
from app.services.ai.service import AIAnalysisService
from app.services.export.service import ExportService
from app.services.ffmpeg.service import FFmpegService
from app.services.reframing.service import ReframingService
from app.services.scoring.service import ScoringService
from app.services.subtitles.service import SubtitleService
from app.services.transcript.service import TranscriptService
from app.services.youtube.service import YouTubeService

console = Console()


class ClipWorkflow:
    def __init__(self):
        self.youtube = YouTubeService()
        self.transcript = TranscriptService()
        self.ai = AIAnalysisService()
        self.scoring = ScoringService()
        self.ffmpeg = FFmpegService()
        self.subtitles = SubtitleService()
        self.reframing = ReframingService(self.ffmpeg)
        self.export = ExportService()

    def run(
        self,
        url: str,
        project_name: Optional[str] = None,
        download_only: bool = False,
        transcribe_only: bool = False,
        analyze_only: bool = False,
        max_clips: int | None = None,
    ) -> ProcessingResult:
        """Run the complete clip generation workflow."""
        start_time = time.time()
        stage = ProcessingStage.INITIALIZING

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:

                # Stage 1: Download
                stage = ProcessingStage.DOWNLOADING
                dl_task = progress.add_task("[cyan]Downloading video...", total=100)

                dl_result = self.youtube.download(url)
                progress.update(dl_task, completed=100)

                if download_only:
                    return ProcessingResult(
                        video_url=url,
                        video_metadata=dl_result.metadata,
                        transcript=Transcript(segments=[], source="none"),
                        clips=[],
                        exports=[],
                        processing_time=time.time() - start_time,
                    )

                # Stage 2: Transcript
                stage = ProcessingStage.EXTRACTING_SUBTITLES
                tr_task = progress.add_task("[cyan]Extracting transcript...", total=100)

                transcript = self._get_transcript(dl_result)
                progress.update(tr_task, completed=100)

                if transcribe_only:
                    return ProcessingResult(
                        video_url=url,
                        video_metadata=dl_result.metadata,
                        transcript=transcript,
                        clips=[],
                        exports=[],
                        processing_time=time.time() - start_time,
                    )

                # Stage 3: AI Analysis
                stage = ProcessingStage.ANALYZING
                ai_task = progress.add_task("[cyan]Analyzing content...", total=100)

                clips = self.ai.analyze(dl_result.metadata, transcript)
                if max_clips:
                    clips = self.scoring.select_top_clips(clips, max_clips)
                progress.update(ai_task, completed=100)

                if analyze_only:
                    return ProcessingResult(
                        video_url=url,
                        video_metadata=dl_result.metadata,
                        transcript=transcript,
                        clips=clips,
                        exports=[],
                        processing_time=time.time() - start_time,
                    )

                # Stage 4: Render clips
                stage = ProcessingStage.RENDERING
                render_task = progress.add_task(
                    f"[cyan]Rendering {len(clips)} clips...", total=len(clips)
                )

                clip_paths = self._render_clips(clips, str(dl_result.video_path), transcript)
                progress.update(render_task, completed=len(clips))

                # Stage 5: Export
                stage = ProcessingStage.EXPORTING
                exp_task = progress.add_task("[cyan]Exporting clips...", total=100)

                proj_name = project_name or self._sanitize_project_name(dl_result.metadata.title)
                exports = self.export.export_all_clips(clips, clip_paths, proj_name)
                progress.update(exp_task, completed=100)

                stage = ProcessingStage.COMPLETE

                return ProcessingResult(
                    video_url=url,
                    video_metadata=dl_result.metadata,
                    transcript=transcript,
                    clips=clips,
                    exports=exports,
                    processing_time=time.time() - start_time,
                )

        except ClipperError as e:
            logger.error(f"Workflow failed at {stage}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error at {stage}: {e}")
            raise ClipperError(f"Workflow failed: {e}")

    def _get_transcript(self, dl_result) -> Transcript:
        """Get transcript from video."""
        if dl_result.subtitle_path:
            try:
                return self.transcript.parse_subtitle_file(dl_result.subtitle_path)
            except Exception as e:
                logger.warning(f"Failed to parse subtitles: {e}")

        if dl_result.audio_path:
            try:
                return self.transcript.transcribe_with_whisper(dl_result.audio_path)
            except Exception as e:
                logger.warning(f"Failed to transcribe: {e}")

        return Transcript(segments=[], source="none", full_text="")

    def _render_clips(
        self,
        clips: list[ClipCandidate],
        video_path: str,
        transcript: Transcript,
    ) -> dict[int, tuple[Path, Optional[Path], Optional[Path]]]:
        """Render all clips with subtitles and thumbnails."""
        clip_paths: dict[int, tuple[Path, Optional[Path], Optional[Path]]] = {}
        temp_dir = Path(settings.temp_dir)

        for clip in clips:
            try:
                logger.info(f"Rendering clip {clip.rank}: {clip.title}")

                # Cut raw clip
                raw_clip = temp_dir / f"raw_{clip.rank}.mp4"
                self.ffmpeg.cut_clip(
                    video_path,
                    raw_clip,
                    clip.start_time,
                    clip.end_time,
                )

                # Convert to vertical
                vertical_clip = temp_dir / f"vertical_{clip.rank}.mp4"
                self.reframing.convert_to_vertical(
                    raw_clip, vertical_clip, settings.output_resolution
                )

                # Generate subtitles
                sub_path = None
                if transcript.segments:
                    sub_path = self.subtitles.generate_subtitle_file(
                        transcript.segments,
                        clip,
                        temp_dir / f"sub_{clip.rank}.srt",
                        "srt",
                    )

                # Generate thumbnail
                thumb_path = self.ffmpeg.generate_thumbnail(
                    vertical_clip,
                    temp_dir / f"thumb_{clip.rank}.jpg",
                    at_time=1.0,
                )

                clip_paths[clip.rank] = (vertical_clip, sub_path, thumb_path)
                logger.debug(f"Clip {clip.rank} rendered successfully")

            except Exception as e:
                logger.error(f"Failed to render clip {clip.rank}: {e}")
                continue

        return clip_paths

    def _sanitize_project_name(self, title: str) -> str:
        """Sanitize video title for use as project name."""
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        return safe[:60].strip()
