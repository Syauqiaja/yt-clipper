"""Tests for template system."""

import pytest

from app.services.composition.models import FitMode
from app.services.formats.models import OutputFormat
from app.services.templates.registry import TemplateRegistry
from app.services.templates.shorts_fit import ShortsFitTemplate
from app.services.templates.shorts_blur import ShortsBlurTemplate
from app.services.templates.square import SquareTemplate


class TestShortsFitTemplate:
    @pytest.fixture
    def template(self):
        """Create shorts fit template."""
        return ShortsFitTemplate(blur_strength=15)
    
    @pytest.fixture
    def shorts_format(self):
        """Create shorts format."""
        return OutputFormat(
            name="shorts",
            width=1080,
            height=1920,
            aspect_ratio="9:16",
        )
    
    def test_template_name(self, template):
        """Test template name."""
        assert template.name == "shorts_fit"
    
    def test_template_description(self, template):
        """Test template description."""
        assert len(template.description) > 0
    
    def test_generate_composition(self, template, shorts_format):
        """Test composition generation."""
        plan = template.generate_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
        )
        
        assert plan.canvas_width == 1080
        assert plan.canvas_height == 1920
        assert plan.fit_mode == FitMode.FIT_WIDTH
    
    def test_supports_format(self, template):
        """Test format support."""
        assert template.supports_format("shorts") is True
        assert template.supports_format("tiktok") is True
        assert template.supports_format("landscape") is False


class TestShortsBlurTemplate:
    @pytest.fixture
    def template(self):
        """Create shorts blur template."""
        return ShortsBlurTemplate(blur_strength=10)
    
    def test_template_name(self, template):
        """Test template name."""
        assert template.name == "shorts_blur"
    
    def test_center_crop_mode(self, template):
        """Test uses center crop."""
        shorts_format = OutputFormat(
            name="shorts",
            width=1080,
            height=1920,
            aspect_ratio="9:16",
        )
        
        plan = template.generate_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
        )
        
        assert plan.fit_mode == FitMode.CENTER_CROP


class TestSquareTemplate:
    @pytest.fixture
    def template(self):
        """Create square template."""
        return SquareTemplate()
    
    @pytest.fixture
    def square_format(self):
        """Create square format."""
        return OutputFormat(
            name="square",
            width=1080,
            height=1080,
            aspect_ratio="1:1",
        )
    
    def test_template_name(self, template):
        """Test template name."""
        assert template.name == "square"
    
    def test_generate_composition(self, template, square_format):
        """Test composition generation."""
        plan = template.generate_composition(
            video_width=1920,
            video_height=1080,
            output_format=square_format,
        )
        
        assert plan.canvas_width == 1080
        assert plan.canvas_height == 1080
    
    def test_supports_format(self, template):
        """Test format support."""
        assert template.supports_format("square") is True
        assert template.supports_format("shorts") is False


class TestTemplateRegistry:
    def test_get_template(self):
        """Test getting template."""
        template = TemplateRegistry.get("shorts_fit")
        
        assert isinstance(template, ShortsFitTemplate)
    
    def test_get_invalid_template(self):
        """Test getting invalid template."""
        from app.core.exceptions import ValidationError
        
        with pytest.raises(ValidationError, match="Template 'invalid' not found"):
            TemplateRegistry.get("invalid")
    
    def test_list_templates(self):
        """Test listing templates."""
        templates = TemplateRegistry.list_templates()
        
        assert "shorts_fit" in templates
        assert "shorts_blur" in templates
        assert "square" in templates
    
    def test_get_for_format(self):
        """Test getting templates for format."""
        templates = TemplateRegistry.get_for_format("shorts")
        
        assert len(templates) >= 2
        assert any(t.name == "shorts_fit" for t in templates)
    
    def test_register_custom_template(self):
        """Test registering custom template."""
        from app.services.templates.base import RenderTemplate
        
        class CustomTemplate(RenderTemplate):
            @property
            def name(self):
                return "custom_test"
            
            @property
            def description(self):
                return "Test template"
            
            def generate_composition(self, video_width, video_height, output_format):
                pass
            
            def supports_format(self, format_name):
                return True
        
        custom = CustomTemplate()
        TemplateRegistry.register(custom)
        
        retrieved = TemplateRegistry.get("custom_test")
        assert retrieved.name == "custom_test"
