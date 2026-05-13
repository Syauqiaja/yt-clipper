"""AI analysis service: orchestrate semantic clip analysis."""

from typing import Any

from app.config.settings import settings
from app.core.exceptions import AIAnalysisError
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import ClipCandidate, Transcript, VideoMetadata

from .client import AIClient, AIError
from .prompts import CLIP_ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt

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
