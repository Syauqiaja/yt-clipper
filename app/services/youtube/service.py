"""YouTube service: download videos, extract subtitles, get metadata via yt-dlp."""

import json
import re
from pathlib import Path
from typing import Any, Optional

import yt_dlp

from app.config.settings import settings
from app.core.exceptions import VideoDownloadError
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import DownloadResult, VideoMetadata

logger = get_logger("youtube")


class YouTubeService:
    def __init__(self, output_dir: str | Path | None = None):
        self.output_dir = Path(output_dir or settings.temp_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._cookies_file = settings.youtube_cookies_file
        self._cookies_from_browser = settings.youtube_cookies_from_browser

    def _get_ydl_opts(self, format_type: str = "best") -> dict[str, Any]:
        """Get base yt-dlp options."""
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "outtmpl": str(self.output_dir / "%(id)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "writeinfojson": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "skip_download": False,
            "no_color": True,
        }

        # Add cookies from browser if configured
        if self._cookies_from_browser:
            opts["cookiesfrombrowser"] = (self._cookies_from_browser,)
            logger.info(f"Using cookies from browser: {self._cookies_from_browser}")
        # Otherwise use cookies file if configured
        elif self._cookies_file and Path(self._cookies_file).exists():
            opts["cookiefile"] = self._cookies_file
            logger.info(f"Using cookies file: {self._cookies_file}")

        if settings.debug:
            opts["verbose"] = True
            opts["quiet"] = False

        return opts

    def extract_metadata(self, url: str) -> VideoMetadata:
        """Extract video metadata from a YouTube URL."""
        logger.info(f"Extracting metadata from: {url}")
        opts = self._get_ydl_opts()
        opts["skip_download"] = True

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return VideoMetadata(
                    video_id=info.get("id", ""),
                    title=info.get("title", "Unknown Title"),
                    description=info.get("description", ""),
                    duration=info.get("duration", 0),
                    uploader=info.get("uploader"),
                    upload_date=info.get("upload_date"),
                    view_count=info.get("view_count"),
                    like_count=info.get("like_count"),
                    channel=info.get("channel"),
                    thumbnail_url=info.get("thumbnail"),
                    categories=info.get("categories") or [],
                    tags=info.get("tags") or [],
                )

        except Exception as e:
            raise VideoDownloadError(f"Failed to extract metadata: {e}")

    def download(self, url: str, extract_audio: bool = False) -> DownloadResult:
        """Download a YouTube video and its subtitles."""
        logger.info(f"Downloading: {url}")

        video_opts = self._get_ydl_opts()
        video_opts["writesubtitles"] = True
        video_opts["writeautomaticsub"] = True
        video_opts["subtitlesformat"] = "vtt"

        try:
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info.get("id", "")
                ext = info.get("ext", "mp4")
                video_path = str(self.output_dir / f"{video_id}.{ext}")

                metadata = VideoMetadata(
                    video_id=video_id,
                    title=info.get("title", "Unknown Title"),
                    description=info.get("description", ""),
                    duration=float(info.get("duration", 0)),
                    uploader=info.get("uploader"),
                    upload_date=info.get("upload_date"),
                    view_count=info.get("view_count"),
                    like_count=info.get("like_count"),
                    channel=info.get("channel"),
                    thumbnail_url=info.get("thumbnail"),
                    categories=info.get("categories") or [],
                    tags=info.get("tags") or [],
                )

        except Exception as e:
            raise VideoDownloadError(f"Failed to download video: {e}")

        subtitle_path = self._find_subtitle(video_id)

        audio_path = None
        if extract_audio:
            audio_path = self._extract_audio(video_path)

        logger.info(f"Downloaded: {metadata.title}")
        return DownloadResult(
            video_path=video_path,
            audio_path=audio_path,
            metadata=metadata,
            subtitle_path=subtitle_path,
        )

    def _find_subtitle(self, video_id: str) -> str | None:
        """Find downloaded subtitle file."""
        patterns = [
            self.output_dir / f"{video_id}*.en.vtt",
            self.output_dir / f"{video_id}*.vtt",
            self.output_dir / f"{video_id}*.en.srt",
            self.output_dir / f"{video_id}*.srt",
        ]
        for pattern in patterns:
            matches = list(self.output_dir.glob(str(pattern)))
            if matches:
                return str(matches[0])
        return None

    def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file."""
        import subprocess

        video_path_obj = Path(video_path)
        audio_path = video_path_obj.with_suffix(".wav")

        cmd = [
            settings.ffmpeg_path,
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            str(audio_path),
        ]

        logger.debug(f"Extracting audio: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

        if result.returncode != 0:
            raise VideoDownloadError(f"Failed to extract audio: {result.stderr}")

        return str(audio_path)

    def download_subtitles_only(self, url: str) -> Optional[str]:
        """Download only subtitles from a video."""
        opts = self._get_ydl_opts()
        opts["skip_download"] = True
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        opts["subtitlesformat"] = "vtt"

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = info.get("id", "")
                return self._find_subtitle(video_id)
        except Exception as e:
            raise VideoDownloadError(f"Failed to download subtitles: {e}")

    def get_available_subtitles(self, url: str) -> dict[str, list[str]]:
        """Get available subtitle languages and formats."""
        opts = self._get_ydl_opts()
        opts["skip_download"] = True
        opts["listsubtitles"] = True

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                subtitles = info.get("subtitles", {})
                result = {}
                for lang, subs in subtitles.items():
                    result[lang] = [s.get("ext", "") for s in subs]
                return result
        except Exception as e:
            raise VideoDownloadError(f"Failed to get subtitles: {e}")

    def validate_url(self, url: str) -> bool:
        """Validate if a URL is a valid YouTube URL."""
        youtube_regex = (
            r"(https?://)?(www\.)?"
            r"(youtube\.com|youtu\.be)/"
            r"(watch\?v=|embed/|v/|shorts/)?"
            r"[\w-]{11}(&[\w-]+=[\w-]+)*"
        )
        return bool(re.match(youtube_regex, url))

    def clean_up(self, video_id: str) -> None:
        """Clean up downloaded files for a video."""
        for f in self.output_dir.glob(f"{video_id}*"):
            try:
                f.unlink()
                logger.debug(f"Cleaned up: {f}")
            except Exception as e:
                logger.warning(f"Failed to clean up {f}: {e}")
