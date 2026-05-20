from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 9Router AI API
    ninerouter_api_key: str = Field(default="", description="9Router API key")
    ninerouter_base_url: str = Field(
        default="https://api.9router.com/v1",
        description="9Router API base URL",
    )
    ninerouter_model: str = Field(
        default="gpt-4o", description="AI model to use"
    )
    ninerouter_timeout: int = Field(
        default=120, description="AI API timeout in seconds"
    )
    ninerouter_max_retries: int = Field(
        default=3, description="Max retries for AI API"
    )

    # FFmpeg
    ffmpeg_path: str = Field(default="", description="Path to ffmpeg binary")
    ffprobe_path: str = Field(default="", description="Path to ffprobe binary")

    # Video Output
    output_quality: int = Field(
        default=23, ge=1, le=51, description="CRF quality (lower=better)"
    )
    output_resolution: str = Field(
        default="1080x1920", description="Output resolution for vertical clips"
    )

    # Clip Settings
    max_clip_duration: int = Field(
        default=60, ge=10, le=180, description="Maximum clip duration in seconds"
    )
    min_clip_duration: int = Field(
        default=15, ge=5, le=60, description="Minimum clip duration in seconds"
    )
    target_clip_count: int = Field(
        default=5, ge=1, le=20, description="Number of clips to generate"
    )

    # Subtitle Style
    subtitle_font: str = Field(default="Arial", description="Subtitle font")
    subtitle_font_size: int = Field(
        default=24, ge=12, le=72, description="Subtitle font size"
    )
    subtitle_primary_color: str = Field(
        default="#FFFFFF", description="Subtitle primary color"
    )
    subtitle_outline_color: str = Field(
        default="#000000", description="Subtitle outline color"
    )

    # Whisper
    whisper_model_size: str = Field(
        default="base", description="Whisper model size"
    )
    whisper_device: str = Field(
        default="cpu", description="Whisper device (cpu/cuda)"
    )
    whisper_compute_type: str = Field(
        default="int8", description="Whisper compute type"
    )

    # Paths
    export_dir: str = Field(
        default="exports", description="Export directory base path"
    )
    temp_dir: str = Field(
        default="temp", description="Temporary files directory"
    )

    # YouTube
    youtube_cookies_file: str = Field(
        default="",
        description="Path to YouTube cookies file for authentication"
    )

    # Google Drive
    google_oauth_credentials_path: str = Field(
        default="google_oauth_credentials.json",
        description="Path to Google OAuth credentials JSON"
    )
    google_drive_folder_id: str = Field(
        default="",
        description="Google Drive folder ID for uploads"
    )
    google_drive_token_path: str = Field(
        default="google_drive_token.json",
        description="Path to store Google Drive token"
    )

    # Webhooks
    webhook_enabled: bool = Field(
        default=False,
        description="Enable webhook notifications"
    )
    webhook_url: str = Field(
        default="",
        description="Webhook URL to send notifications"
    )

    # Observability
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Scoring Weights
    scoring_hook_weight: float = Field(
        default=0.30, ge=0, le=1, description="Hook strength weight"
    )
    scoring_retention_weight: float = Field(
        default=0.25, ge=0, le=1, description="Retention potential weight"
    )
    scoring_info_weight: float = Field(
        default=0.20, ge=0, le=1, description="Information density weight"
    )
    scoring_story_weight: float = Field(
        default=0.15, ge=0, le=1, description="Storytelling weight"
    )
    scoring_emotion_weight: float = Field(
        default=0.10, ge=0, le=1, description="Emotional engagement weight"
    )

    @property
    def scoring_weights(self) -> dict[str, float]:
        return {
            "hook_strength": self.scoring_hook_weight,
            "retention_potential": self.scoring_retention_weight,
            "information_density": self.scoring_info_weight,
            "storytelling": self.scoring_story_weight,
            "emotional_engagement": self.scoring_emotion_weight,
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ffmpeg_path:
            self.ffmpeg_path = "ffmpeg"
        if not self.ffprobe_path:
            self.ffprobe_path = "ffprobe"


settings = Settings()
