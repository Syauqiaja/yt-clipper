"""Format registry for managing output formats."""

from typing import Dict

from app.core.exceptions import ValidationError
from app.services.formats.models import OutputFormat


class FormatRegistry:
    """
    Registry for managing output format definitions.
    
    Provides built-in formats and supports custom format registration.
    """
    
    _formats: Dict[str, OutputFormat] = {}
    _initialized: bool = False
    
    @classmethod
    def _initialize_builtin_formats(cls) -> None:
        """Initialize built-in format definitions."""
        if cls._initialized:
            return
        
        builtin_formats = [
            OutputFormat(
                name="shorts",
                width=1080,
                height=1920,
                aspect_ratio="9:16",
                safe_margin=40,
                caption_zone_height=200,
            ),
            OutputFormat(
                name="square",
                width=1080,
                height=1080,
                aspect_ratio="1:1",
                safe_margin=30,
                caption_zone_height=150,
            ),
            OutputFormat(
                name="landscape",
                width=1920,
                height=1080,
                aspect_ratio="16:9",
                safe_margin=40,
                caption_zone_height=120,
            ),
            OutputFormat(
                name="portrait_45",
                width=1080,
                height=1350,
                aspect_ratio="4:5",
                safe_margin=35,
                caption_zone_height=180,
            ),
            OutputFormat(
                name="tiktok",
                width=1080,
                height=1920,
                aspect_ratio="9:16",
                safe_margin=50,
                caption_zone_height=220,
            ),
            OutputFormat(
                name="instagram_reel",
                width=1080,
                height=1920,
                aspect_ratio="9:16",
                safe_margin=45,
                caption_zone_height=200,
            ),
            OutputFormat(
                name="youtube_short",
                width=1080,
                height=1920,
                aspect_ratio="9:16",
                safe_margin=40,
                caption_zone_height=200,
            ),
        ]
        
        for fmt in builtin_formats:
            cls._formats[fmt.name] = fmt
        
        cls._initialized = True
    
    @classmethod
    def get(cls, name: str) -> OutputFormat:
        """
        Get format by name.
        
        Args:
            name: Format identifier
            
        Returns:
            OutputFormat instance
            
        Raises:
            ValidationError: If format not found
        """
        cls._initialize_builtin_formats()
        
        if name not in cls._formats:
            raise ValidationError(
                f"Format '{name}' not found. Available: {', '.join(cls.list_formats())}"
            )
        
        return cls._formats[name]
    
    @classmethod
    def register(cls, format_def: OutputFormat) -> None:
        """
        Register a custom format.
        
        Args:
            format_def: OutputFormat instance to register
        """
        cls._initialize_builtin_formats()
        cls._formats[format_def.name] = format_def
    
    @classmethod
    def list_formats(cls) -> list[str]:
        """
        List all available format names.
        
        Returns:
            List of format identifiers
        """
        cls._initialize_builtin_formats()
        return list(cls._formats.keys())
    
    @classmethod
    def get_all(cls) -> Dict[str, OutputFormat]:
        """
        Get all registered formats.
        
        Returns:
            Dictionary of format name to OutputFormat
        """
        cls._initialize_builtin_formats()
        return cls._formats.copy()
