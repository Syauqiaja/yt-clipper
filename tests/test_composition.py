"""Tests for composition planner."""

import pytest

from app.services.composition.models import BackgroundMode, FitMode
from app.services.composition.planner import CompositionPlanner
from app.services.formats.models import OutputFormat


class TestCompositionPlanner:
    @pytest.fixture
    def planner(self):
        """Create composition planner."""
        return CompositionPlanner()
    
    @pytest.fixture
    def shorts_format(self):
        """Create shorts format."""
        return OutputFormat(
            name="shorts",
            width=1080,
            height=1920,
            aspect_ratio="9:16",
            safe_margin=40,
            caption_zone_height=200,
        )
    
    def test_fit_width_composition(self, planner, shorts_format):
        """Test fit-width composition planning."""
        plan = planner.plan_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
            fit_mode=FitMode.FIT_WIDTH,
            background_mode=BackgroundMode.BLUR,
        )
        
        assert plan.canvas_width == 1080
        assert plan.canvas_height == 1920
        assert plan.fit_mode == FitMode.FIT_WIDTH
        assert plan.background.mode == BackgroundMode.BLUR
        
        # Video should be scaled to canvas width
        assert plan.video.width == 1080
        # Height should maintain aspect ratio
        assert plan.video.height == pytest.approx(607, abs=2)
        # Should be centered vertically
        assert plan.video.x == 0
        assert plan.video.y > 0
    
    def test_fit_height_composition(self, planner, shorts_format):
        """Test fit-height composition planning."""
        plan = planner.plan_composition(
            video_width=1080,
            video_height=1920,
            output_format=shorts_format,
            fit_mode=FitMode.FIT_HEIGHT,
        )
        
        # Video should be scaled to canvas height
        assert plan.video.height == 1920
        # Width should maintain aspect ratio
        assert plan.video.width == pytest.approx(1080, abs=2)
        # Should be centered horizontally
        assert plan.video.y == 0
    
    def test_center_crop_composition(self, planner, shorts_format):
        """Test center crop composition."""
        plan = planner.plan_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
            fit_mode=FitMode.CENTER_CROP,
        )
        
        # Video should fill canvas
        assert plan.video.width == 1080
        assert plan.video.height == 1920
        assert plan.video.x == 0
        assert plan.video.y == 0
    
    def test_safe_area_calculation(self, planner, shorts_format):
        """Test safe area calculation."""
        plan = planner.plan_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
        )
        
        safe_x, safe_y, safe_width, safe_height = plan.get_safe_area()
        
        assert safe_x == 40
        assert safe_y == 40
        assert safe_width == 1000
        assert safe_height == 1840
    
    def test_aspect_ratio_property(self, planner, shorts_format):
        """Test aspect ratio property."""
        plan = planner.plan_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
        )
        
        assert plan.aspect_ratio == pytest.approx(0.5625, rel=1e-3)
    
    def test_blur_background_mode(self, planner, shorts_format):
        """Test blur background configuration."""
        plan = planner.plan_composition(
            video_width=1920,
            video_height=1080,
            output_format=shorts_format,
            background_mode=BackgroundMode.BLUR,
            blur_strength=20,
        )
        
        assert plan.background.mode == BackgroundMode.BLUR
        assert plan.background.blur_strength == 20
