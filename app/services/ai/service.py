"""AI analysis service: orchestrate semantic clip analysis."""

from typing import Any

from app.config.settings import settings
from app.core.exceptions import AIAnalysisError
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import ClipCandidate, Transcript, VideoMetadata

from .client import AIClient, AIError
from .prompts import CLIP_ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt
from .metadata_prompts import METADATA_GENERATION_SYSTEM_PROMPT, build_metadata_prompt

logger = get_logger("ai.service")


class AIAnalysisService:
    def __init__(self):
        self.client = AIClient()

    def analyze(self, metadata: VideoMetadata, transcript: Transcript) -> list[ClipCandidate]:
        """Analyze video and identify best clips for short-form content."""
        logger.info(f"Analyzing video: {metadata.title}")

        prompt = build_analysis_prompt(
            video_title=metadata.title,
            video_duration=metadata.duration,
            uploader=metadata.uploader or "Unknown",
            full_transcript=transcript.full_text,
            max_clips=settings.target_clip_count,
            min_duration=settings.min_clip_duration,
            max_duration=settings.max_clip_duration,
        )

        response = ""
        try:
            raw_response = self.client.chat_completion(
                system_prompt=CLIP_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=8192,
            )

            parsed = self.client.parse_json_response(raw_response)

            if isinstance(parsed, dict) and "clips" in parsed:
                raw_clips = parsed["clips"]
            elif isinstance(parsed, list):
                raw_clips = parsed
            else:
                raise AIAnalysisError(f"Unexpected AI response format: {type(parsed)}")

            clips = []
            for raw_clip in raw_clips:
                try:
                    scores_data = raw_clip.get("scores", {})
                    duration = raw_clip.get("duration", 0)

                    if not (settings.min_clip_duration <= duration <= settings.max_clip_duration):
                        logger.debug(
                            f"Skipping clip outside duration range: {duration:.1f}s"
                        )
                        continue

                    clip = ClipCandidate(
                        start_time=raw_clip.get("start_time", 0),
                        end_time=raw_clip.get("end_time", 0),
                        duration=raw_clip.get("duration", round(duration, 1)),
                        title=raw_clip.get("title", ""),
                        hook=raw_clip.get("hook", ""),
                        summary=raw_clip.get("summary", ""),
                        scores={
                            "hook_strength": scores_data.get("hook_strength", 0),
                            "information_density": scores_data.get("information_density", 0),
                            "emotional_engagement": scores_data.get("emotional_engagement", 0),
                            "storytelling": scores_data.get("storytelling", 0),
                            "retention_potential": scores_data.get("retention_potential", 0),
                            "viral_potential": scores_data.get("viral_potential", 0),
                        },
                    )

                    clip.final_score = clip.calculate_final_score()
                    clips.append(clip)

                except Exception as e:
                    logger.warning(f"Failed to parse clip data: {e}")
                    continue

            clips.sort(key=lambda c: c.final_score, reverse=True)
            for rank, clip in enumerate(clips, 1):
                clip.rank = rank

            logger.info(f"Found {len(clips)} valid clip candidates")
            return clips

        except AIError as e:
            raise AIAnalysisError(f"AI API error: {e}")
        except AIAnalysisError:
            raise
        except Exception as e:
            raise AIAnalysisError(f"Analysis failed: {e}")

    def generate_clip_metadata(
        self,
        clips: list[ClipCandidate],
        video_path: str,
    ) -> list[ClipCandidate]:
        """Generate titles and descriptions for clips by transcribing each clip individually."""
        from app.services.transcript.service import TranscriptService
        from pathlib import Path
        
        logger.info(f"Generating metadata for {len(clips)} clips")
        transcript_service = TranscriptService()
        
        for clip in clips:
            try:
                logger.info(f"Processing clip {clip.rank}: {clip.start_time}s - {clip.end_time}s")
                
                # Extract clip audio and transcribe it
                clip_audio = Path(video_path).parent / f"clip_{clip.rank}_audio.wav"
                
                # Use ffmpeg to extract clip audio
                import subprocess
                from app.config.settings import settings
                
                cmd = [
                    settings.ffmpeg_path,
                    "-i", video_path,
                    "-ss", str(clip.start_time),
                    "-t", str(clip.duration),
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",
                    str(clip_audio),
                ]
                
                logger.debug(f"Extracting clip audio: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.warning(f"Failed to extract audio for clip {clip.rank}: {result.stderr}")
                    clip.title_id = clip.title
                    clip.title_en = clip.title
                    clip.description_id = clip.summary
                    clip.description_en = clip.summary
                    continue
                
                # Transcribe the clip audio
                try:
                    clip_transcript_obj = transcript_service.transcribe_with_whisper(clip_audio)
                    clip_transcript = clip_transcript_obj.full_text
                    
                    # Clean up audio file
                    clip_audio.unlink(missing_ok=True)
                    
                except Exception as e:
                    logger.warning(f"Failed to transcribe clip {clip.rank}: {e}")
                    clip_audio.unlink(missing_ok=True)
                    clip.title_id = clip.title
                    clip.title_en = clip.title
                    clip.description_id = clip.summary
                    clip.description_en = clip.summary
                    continue
                
                if not clip_transcript:
                    logger.warning(f"No transcript for clip {clip.rank}, using fallback")
                    clip.title_id = clip.title
                    clip.title_en = clip.title
                    clip.description_id = clip.summary
                    clip.description_en = clip.summary
                    continue
                
                logger.info(f"Clip {clip.rank} transcript length: {len(clip_transcript)} chars")
                logger.debug(f"Clip {clip.rank} transcript: {clip_transcript[:200]}...")
                
                prompt = build_metadata_prompt(
                    original_title=clip.title,
                    hook=clip.hook,
                    summary=clip.summary,
                    duration=clip.duration,
                    transcript=clip_transcript,
                )
                
                raw_response = self.client.chat_completion(
                    system_prompt=METADATA_GENERATION_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    temperature=0.7,
                    max_tokens=1024,
                )
                
                parsed = self.client.parse_json_response(raw_response)
                
                clip.title_id = parsed.get("title_id", clip.title)
                clip.title_en = parsed.get("title_en", clip.title)
                clip.description_id = parsed.get("description_id", clip.summary)
                clip.description_en = parsed.get("description_en", clip.summary)
                
                logger.info(f"Generated metadata for clip {clip.rank}: {clip.title_en}")
                
            except Exception as e:
                logger.warning(f"Failed to generate metadata for clip {clip.rank}: {e}")
                clip.title_id = clip.title
                clip.title_en = clip.title
                clip.description_id = clip.summary
                clip.description_en = clip.summary
                continue
        
        return clips
