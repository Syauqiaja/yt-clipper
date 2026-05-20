import httpx
from datetime import datetime

from app.config.settings import settings
from app.infrastructure.logging.logger import get_logger
from app.services.webhooks.models import WebhookPayload

logger = get_logger("webhook")


class WebhookService:
    def __init__(self):
        self.webhook_url = settings.webhook_url
        self.webhook_enabled = settings.webhook_enabled
    
    async def send_completion_webhook(
        self,
        video_url: str,
        video_metadata: dict,
        clips: list,
        drive_uploads: list | None = None,
        processing_time: float = 0.0,
    ) -> None:
        """Send webhook notification when processing completes"""
        if not self.webhook_enabled or not self.webhook_url:
            logger.debug("Webhook disabled or URL not configured")
            return
        
        payload = WebhookPayload(
            event="clip.completed",
            video_url=video_url,
            video_title=video_metadata.get("title", "Unknown"),
            video_metadata=video_metadata,
            clips=clips,
            drive_uploads=drive_uploads,
            processing_time=processing_time,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                logger.info(f"Webhook sent successfully: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    async def send_error_webhook(
        self,
        video_url: str,
        error: str,
    ) -> None:
        """Send webhook notification when processing fails"""
        if not self.webhook_enabled or not self.webhook_url:
            return
        
        payload = WebhookPayload(
            event="clip.failed",
            video_url=video_url,
            video_title="",
            video_metadata={},
            clips=[],
            processing_time=0.0,
            timestamp=datetime.utcnow().isoformat() + "Z",
            error=error,
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    self.webhook_url,
                    json=payload.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                logger.info("Error webhook sent successfully")
        except Exception as e:
            logger.error(f"Failed to send error webhook: {e}")
