"""Core module: exceptions, enums, and base classes."""


class ClipperError(Exception):
    """Base exception for all clipper errors."""
    pass


class VideoDownloadError(ClipperError):
    """Failed to download video."""
    pass


class TranscriptError(ClipperError):
    """Failed to extract or process transcript."""
    pass


class AIAnalysisError(ClipperError):
    """Failed AI analysis."""
    pass


class FFmpegError(ClipperError):
    """FFmpeg execution failed."""
    pass


class SubtitleError(ClipperError):
    """Subtitle generation failed."""
    pass


class ExportError(ClipperError):
    """Export failed."""
    pass


class ValidationError(ClipperError):
    """Validation failed."""
    pass


class ConfigurationError(ClipperError):
    """Configuration error."""
    pass


class TimeoutError(ClipperError):
    """Operation timed out."""
    pass


class CacheError(ClipperError):
    """Cache operation failed."""
    pass


class StorageError(ClipperError):
    """Storage operation failed."""
    pass
