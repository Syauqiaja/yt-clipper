"""Caption style presets for different content types."""

from app.services.captions.models import CaptionStyle


class CaptionPresets:
    """
    Predefined caption style presets.
    
    Provides production-ready caption styles for different content types.
    """
    
    @staticmethod
    def tiktok() -> CaptionStyle:
        """
        TikTok-style captions.
        
        Bold, high-contrast, centered captions with strong outline.
        """
        return CaptionStyle(
            font_name="Arial Black",
            font_size=52,
            primary_color="&H00FFFFFF",
            outline_color="&H00000000",
            outline_width=4,
            shadow=3,
            alignment=2,
            bold=True,
            italic=False,
            margin_v=100,
            margin_l=40,
            margin_r=40,
            animation_preset="fade_in_out",
        )
    
    @staticmethod
    def hormozi() -> CaptionStyle:
        """
        Alex Hormozi-style captions.
        
        Large, bold, yellow text with heavy black outline.
        """
        return CaptionStyle(
            font_name="Impact",
            font_size=60,
            primary_color="&H0000FFFF",
            outline_color="&H00000000",
            outline_width=5,
            shadow=4,
            alignment=2,
            bold=True,
            italic=False,
            margin_v=120,
            margin_l=50,
            margin_r=50,
            animation_preset="scale_in",
        )
    
    @staticmethod
    def documentary() -> CaptionStyle:
        """
        Documentary-style captions.
        
        Clean, readable, subtle styling.
        """
        return CaptionStyle(
            font_name="Helvetica",
            font_size=44,
            primary_color="&H00FFFFFF",
            outline_color="&H00000000",
            outline_width=2,
            shadow=1,
            alignment=2,
            bold=False,
            italic=False,
            margin_v=80,
            margin_l=60,
            margin_r=60,
            animation_preset="fade_in",
        )
    
    @staticmethod
    def gaming() -> CaptionStyle:
        """
        Gaming-style captions.
        
        Bold, colorful, energetic styling.
        """
        return CaptionStyle(
            font_name="Arial Black",
            font_size=56,
            primary_color="&H0000FF00",
            outline_color="&H00000000",
            outline_width=4,
            shadow=3,
            alignment=2,
            bold=True,
            italic=False,
            margin_v=100,
            margin_l=40,
            margin_r=40,
            animation_preset="bounce",
        )
    
    @staticmethod
    def podcast() -> CaptionStyle:
        """
        Podcast-style captions.
        
        Professional, clean, easy to read.
        """
        return CaptionStyle(
            font_name="Open Sans",
            font_size=48,
            primary_color="&H00FFFFFF",
            outline_color="&H00000000",
            outline_width=3,
            shadow=2,
            alignment=2,
            bold=True,
            italic=False,
            margin_v=90,
            margin_l=50,
            margin_r=50,
            animation_preset="fade_in",
        )
    
    @staticmethod
    def minimal() -> CaptionStyle:
        """
        Minimal captions.
        
        Simple, unobtrusive styling.
        """
        return CaptionStyle(
            font_name="Arial",
            font_size=42,
            primary_color="&H00FFFFFF",
            outline_color="&H00000000",
            outline_width=2,
            shadow=1,
            alignment=2,
            bold=False,
            italic=False,
            margin_v=70,
            margin_l=50,
            margin_r=50,
            animation_preset=None,
        )
    
    @staticmethod
    def get_preset(name: str) -> CaptionStyle:
        """
        Get preset by name.
        
        Args:
            name: Preset identifier
            
        Returns:
            CaptionStyle instance
            
        Raises:
            ValueError: If preset not found
        """
        presets = {
            "tiktok": CaptionPresets.tiktok,
            "hormozi": CaptionPresets.hormozi,
            "documentary": CaptionPresets.documentary,
            "gaming": CaptionPresets.gaming,
            "podcast": CaptionPresets.podcast,
            "minimal": CaptionPresets.minimal,
        }
        
        if name not in presets:
            raise ValueError(
                f"Preset '{name}' not found. Available: {', '.join(presets.keys())}"
            )
        
        return presets[name]()
    
    @staticmethod
    def list_presets() -> list[str]:
        """
        List all available preset names.
        
        Returns:
            List of preset identifiers
        """
        return ["tiktok", "hormozi", "documentary", "gaming", "podcast", "minimal"]
