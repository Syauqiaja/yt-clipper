from pydantic import BaseModel


class WebhookPayload(BaseModel):
    event: str
    video_url: str
    video_title: str
    video_metadata: dict
    clips: list[dict]
    drive_uploads: list[dict] | None = None
    processing_time: float
    timestamp: str
    error: str | None = None
