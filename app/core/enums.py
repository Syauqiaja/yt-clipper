from enum import Enum


class VideoQuality(str, Enum):
    BEST = "best"
    Q1080P = "1080p"
    Q720P = "720p"
    Q480P = "480p"


class OutputFormat(str, Enum):
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"


class SubtitleFormat(str, Enum):
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    TXT = "txt"


class ClipFormat(str, Enum):
    VERTICAL = "vertical"  # 9:16 (1080x1920)
    SQUARE = "square"  # 1:1 (1080x1080)
    HORIZONTAL = "horizontal"  # 16:9 (1920x1080)


class TranscriptSource(str, Enum):
    YOUTUBE = "youtube"
    WHISPER = "whisper"
    MIXED = "mixed"


class ProcessingStage(str, Enum):
    INITIALIZING = "initializing"
    DOWNLOADING = "downloading"
    EXTRACTING_SUBTITLES = "extracting_subtitles"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    SCORING = "scoring"
    RENDERING = "rendering"
    EXPORTING = "exporting"
    COMPLETE = "complete"
    FAILED = "failed"


class ExportQuality(str, Enum):
    ULTRA = "ultra"  # CRF 18
    HIGH = "high"  # CRF 20
    MEDIUM = "medium"  # CRF 23
    LOW = "low"  # CRF 28


class WhisperModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large-v3"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
