"""Domain schemas: Pydantic models for all domain entities."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ClipScores(BaseModel):
    hook_strength: float = Field(ge=0, le=10, description="Hook strength score")
    information_density: float = Field(ge=0, le=10, description="Information density score")
    emotional_engagement: float = Field(ge=0, le=10, description="Emotional engagement score")
    storytelling: float = Field(ge=0, le=10, description="Storytelling score")
    retention_potential: float = Field(ge=0, le=10, description="Retention potential score")
    viral_potential: float = Field(ge=0, le=10, description="Viral potential score")


class ClipCandidate(BaseModel):
    start_time: float = Field(ge=0, description="Start time in seconds")
    end_time: float = Field(gt=0, description="End time in seconds")
    duration: float = Field(gt=0, description="Duration in seconds")
    title: str = Field(min_length=1, max_length=200, description="Clip title")
    hook: str = Field(min_length=1, max_length=500, description="Hook description")
    summary: str = Field(min_length=1, max_length=1000, description="Clip summary")
    scores: ClipScores
    final_score: float = Field(default=0.0, ge=0, le=10, description="Weighted final score")
    rank: int = Field(default=0, ge=0, description="Rank among all clips")
    title_id: str | None = Field(default=None, description="Indonesian title")
    title_en: str | None = Field(default=None, description="English title")
    description_id: str | None = Field(default=None, description="Indonesian description")
    description_en: str | None = Field(default=None, description="English description")

    def calculate_final_score(self) -> float:
        from app.config.settings import settings

        s = self.scores
        w = settings.scoring_weights
        total = sum(w.values())
        normalized = {k: v / total for k, v in w.items()} if total else w

        return round(
            s.hook_strength * normalized["hook_strength"]
            + s.retention_potential * normalized["retention_potential"]
            + s.information_density * normalized["information_density"]
            + s.storytelling * normalized["storytelling"]
            + s.emotional_engagement * normalized["emotional_engagement"],
            4,
        )


class VideoMetadata(BaseModel):
    video_id: str
    title: str
    description: str | None = None
    duration: float
    uploader: str | None = None
    upload_date: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    channel: str | None = None
    thumbnail_url: str | None = None
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TranscriptSegment(BaseModel):
    start: float = Field(ge=0, description="Start time in seconds")
    end: float = Field(gt=0, description="End time in seconds")
    text: str = Field(min_length=1, description="Transcript text")
    confidence: float | None = Field(default=None, ge=0, le=1)


class Transcript(BaseModel):
    segments: list[TranscriptSegment]
    source: str = Field(description="youtube, whisper, or mixed")
    language: str | None = None
    full_text: str = Field(default="")

    def model_post_init(self, __context: Any) -> None:
        if not self.full_text and self.segments:
            self.full_text = " ".join(seg.text for seg in self.segments)


class SubtitleLine(BaseModel):
    index: int
    start_time: float
    end_time: float
    text: str


class DownloadResult(BaseModel):
    video_path: str
    audio_path: str | None = None
    metadata: VideoMetadata
    subtitle_path: str | None = None


class ClipExport(BaseModel):
    clip: ClipCandidate
    video_path: str
    subtitle_path: str | None = None
    thumbnail_path: str | None = None
    metadata_path: str
    export_dir: str
    created_at: datetime = Field(default_factory=datetime.now)


class ProcessingResult(BaseModel):
    video_url: str
    video_metadata: VideoMetadata
    transcript: Transcript
    clips: list[ClipCandidate]
    exports: list[ClipExport]
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)


class AIAnalysisRequest(BaseModel):
    video_metadata: VideoMetadata
    transcript: Transcript
    max_clips: int = Field(default=5, ge=1, le=20)
    min_duration: int = Field(default=15, ge=5)
    max_duration: int = Field(default=60, ge=10)


class AIAnalysisResponse(BaseModel):
    clips: list[ClipCandidate]
    analysis_metadata: dict[str, Any] = Field(default_factory=dict)
