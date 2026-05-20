"""Main workflow: orchestrates the entire clip generation pipeline."""

import asyncio
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
from app.services.webhooks import WebhookService
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
        self.webhook = WebhookService()

    def run(
        self,
        url: str,
        project_name: Optional[str] = None,
        download_only: bool = False,
        transcribe_only: bool = False,
        analyze_only: bool = False,
        max_clips: int | None = None,
        output_format: str = "shorts",
        template: str = "shorts_fit",
        captions: bool = False,
        caption_style: str = "tiktok",
        karaoke: bool = False,
        verbose: bool = False,
        upload_to_drive: bool = False,
        send_webhook: bool = True,
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
                
                # Generate metadata for clips
                if not analyze_only:
                    meta_task = progress.add_task("[cyan]Generating titles & descriptions...", total=100)
                    clips = self.ai.generate_clip_metadata(clips, str(dl_result.video_path))
                    progress.update(meta_task, completed=100)

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

                clip_paths = self._render_clips(
                    clips, 
                    str(dl_result.video_path), 
                    transcript,
                    output_format,
                    template,
                    captions,
                    caption_style,
                    karaoke,
                )
                progress.update(render_task, completed=len(clips))

                # Stage 5: Export
                stage = ProcessingStage.EXPORTING
                exp_task = progress.add_task("[cyan]Exporting clips...", total=100)

                proj_name = project_name or self._sanitize_project_name(dl_result.metadata.title)
                exports = self.export.export_all_clips(clips, clip_paths, proj_name, verbose)
                progress.update(exp_task, completed=100)

                # Stage 6: Upload to Google Drive (optional)
                drive_uploads = []
                if upload_to_drive:
                    from app.services.storage import GoogleDriveService
                    
                    drive_task = progress.add_task("[cyan]Uploading to Google Drive...", total=len(exports))
                    drive_service = GoogleDriveService()
                    
                    for export in exports:
                        upload_result = drive_service.upload_file(export.video_path)
                        drive_uploads.append({
                            "clip_rank": export.clip.rank,
                            "clip_title": export.clip.title,
                            "file_id": upload_result.file_id,
                            "file_name": upload_result.file_name,
                            "view_link": upload_result.view_link,
                            "download_link": upload_result.download_link,
                            "thumbnail_link": upload_result.thumbnail_link,
                        })
                        progress.update(drive_task, advance=1)

                stage = ProcessingStage.COMPLETE
                
                result = ProcessingResult(
                    video_url=url,
                    video_metadata=dl_result.metadata,
                    transcript=transcript,
                    clips=clips,
                    exports=exports,
                    processing_time=time.time() - start_time,
                    drive_uploads=drive_uploads if drive_uploads else None,
                )

                # Send webhook notification
                if send_webhook:
                    # Merge drive upload info into clips
                    clips_with_uploads = []
                    for clip in clips:
                        clip_data = clip.model_dump()
                        # Find matching drive upload by rank
                        if drive_uploads:
                            matching_upload = next(
                                (u for u in drive_uploads if u["clip_rank"] == clip.rank),
                                None
                            )
                            if matching_upload:
                                clip_data["drive_file_id"] = matching_upload["file_id"]
                                clip_data["drive_file_name"] = matching_upload["file_name"]
                                clip_data["drive_view_link"] = matching_upload["view_link"]
                                clip_data["drive_download_link"] = matching_upload["download_link"]
                                clip_data["drive_thumbnail_link"] = matching_upload["thumbnail_link"]
                        clips_with_uploads.append(clip_data)
                    
                    asyncio.run(self.webhook.send_completion_webhook(
                        video_url=url,
                        video_metadata=dl_result.metadata.model_dump(),
                        clips=clips_with_uploads,
                        drive_uploads=None,
                        processing_time=result.processing_time,
                    ))

                return result

        except ClipperError as e:
            logger.error(f"Workflow failed at {stage}: {e}")
            if send_webhook:
                asyncio.run(self.webhook.send_error_webhook(
                    video_url=url,
                    error=str(e),
                ))
            raise
        except Exception as e:
            logger.error(f"Unexpected error at {stage}: {e}")
            if send_webhook:
                asyncio.run(self.webhook.send_error_webhook(
                    video_url=url,
                    error=str(e),
                ))
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
        output_format: str = "shorts",
        template: str = "shorts_fit",
        captions: bool = False,
        caption_style: str = "tiktok",
        karaoke: bool = False,
    ) -> dict[int, tuple[Path, Optional[Path], Optional[Path]]]:
        """Render all clips with Phase 2 rendering and optional captions."""
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

                # Phase 2: Use new rendering system if available
                try:
                    from app.services.formats import FormatRegistry
                    from app.services.renderer import RenderService
                    
                    # Get video info
                    video_info = self.ffmpeg.get_video_info(raw_clip)
                    video_width = video_info["streams"][0]["width"]
                    video_height = video_info["streams"][0]["height"]
                    
                    # Generate captions if requested
                    sub_path = None
                    if captions:
                        sub_path = self._generate_captions(
                            raw_clip,
                            clip,
                            transcript,
                            output_format,
                            caption_style,
                            karaoke,
                            temp_dir,
                        )
                    
                    # Render with Phase 2 system
                    vertical_clip = temp_dir / f"vertical_{clip.rank}.mp4"
                    renderer = RenderService()
                    renderer.render_with_template(
                        input_path=raw_clip,
                        output_path=vertical_clip,
                        template_name=template,
                        format_name=output_format,
                        video_width=video_width,
                        video_height=video_height,
                        subtitle_path=sub_path,
                    )
                    
                except ImportError:
                    # Fallback to Phase 1 rendering
                    logger.warning("Phase 2 rendering not available, using legacy rendering")
                    vertical_clip = temp_dir / f"vertical_{clip.rank}.mp4"
                    self.reframing.convert_to_vertical(
                        raw_clip, vertical_clip, settings.output_resolution
                    )
                    
                    # Generate subtitles (Phase 1)
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
    
    def _generate_captions(
        self,
        audio_path: Path,
        clip: ClipCandidate,
        transcript: Transcript,
        output_format: str,
        caption_style: str,
        karaoke: bool,
        temp_dir: Path,
    ) -> Optional[Path]:
        """Generate captions for clip using Phase 2 caption system."""
        try:
            from app.services.captions import CaptionService, CaptionPresets
            from app.services.formats import FormatRegistry
            
            # Get word timestamps for clip timeframe
            words = self.transcript.transcribe_with_word_timestamps(audio_path)
            
            if not words:
                logger.warning("No word timestamps available for captions")
                return None
            
            # Get format for caption positioning
            fmt = FormatRegistry.get(output_format)
            
            # Get caption style
            style = CaptionPresets.get_preset(caption_style)
            
            # Generate captions
            caption_service = CaptionService(style=style)
            ass_path = temp_dir / f"captions_{clip.rank}.ass"
            
            caption_service.generate_captions(
                words=words,
                output_path=ass_path,
                video_width=fmt.width,
                video_height=fmt.height,
                karaoke=karaoke,
            )
            
            logger.info(f"Generated captions for clip {clip.rank}")
            return ass_path
            
        except Exception as e:
            logger.error(f"Failed to generate captions: {e}")
            return None

    def _sanitize_project_name(self, title: str) -> str:
        """Sanitize video title for use as project name."""
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        return safe[:60].strip()
