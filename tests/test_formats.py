"""Tests for format registry and output formats."""

import pytest

from app.core.exceptions import ValidationError
from app.services.formats.models import OutputFormat
from app.services.formats.registry import FormatRegistry


class TestOutputFormat:
    def test_format_creation(self):
        """Test creating an output format."""
        format = OutputFormat(
            name="test",
            width=1080,
            height=1920,
            aspect_ratio="9:16",
            safe_margin=40,
            caption_zone_height=200,
        )
        
        assert format.name == "test"
        assert format.width == 1080
        assert format.height == 1920
        assert format.aspect_ratio == "9:16"
    
    def test_format_ratio(self):
        """Test aspect ratio calculation."""
        format = OutputFormat(
            name="test",
            width=1080,
            height=1920,
            aspect_ratio="9:16",
        )
        
        assert format.ratio == pytest.approx(0.5625, rel=1e-3)
    
    def test_format_is_vertical(self):
        """Test vertical format detection."""
        vertical = OutputFormat(
            name="vertical",
            width=1080,
            height=1920,
            aspect_ratio="9:16",
        )
        
        assert vertical.is_vertical is True
        assert vertical.is_horizontal is False
        assert vertical.is_square is False
    
    def test_format_is_horizontal(self):
        """Test horizontal format detection."""
        horizontal = OutputFormat(
            name="horizontal",
            width=1920,
            height=1080,
            aspect_ratio="16:9",
        )
        
        assert horizontal.is_horizontal is True
        assert horizontal.is_vertical is False
        assert horizontal.is_square is False
    
    def test_format_is_square(self):
        """Test square format detection."""
        square = OutputFormat(
            name="square",
            width=1080,
            height=1080,
            aspect_ratio="1:1",
        )
        
        assert square.is_square is True
        assert square.is_vertical is False
        assert square.is_horizontal is False


class TestFormatRegistry:
    def test_get_builtin_format(self):
        """Test getting built-in format."""
        format = FormatRegistry.get("shorts")
        
        assert format.name == "shorts"
        assert format.width == 1080
        assert format.height == 1920
    
    def test_get_invalid_format(self):
        """Test getting non-existent format."""
        with pytest.raises(ValidationError, match="Format 'invalid' not found"):
            FormatRegistry.get("invalid")
    
    def test_list_formats(self):
        """Test listing all formats."""
        formats = FormatRegistry.list_formats()
        
        assert "shorts" in formats
        assert "square" in formats
        assert "landscape" in formats
        assert len(formats) >= 3
    
    def test_register_custom_format(self):
        """Test registering custom format."""
        custom = OutputFormat(
            name="custom_test",
            width=1080,
            height=2400,
            aspect_ratio="9:20",
        )
        
        FormatRegistry.register(custom)
        
        retrieved = FormatRegistry.get("custom_test")
        assert retrieved.name == "custom_test"
        assert retrieved.width == 1080
        assert retrieved.height == 2400
    
    def test_get_all_formats(self):
        """Test getting all format objects."""
        all_formats = FormatRegistry.get_all()
        
        assert isinstance(all_formats, dict)
        assert "shorts" in all_formats
        assert isinstance(all_formats["shorts"], OutputFormat)
