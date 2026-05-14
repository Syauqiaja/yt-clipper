"""Tests for FFmpeg graph builder."""

import pytest

from app.services.composition.models import BackgroundMode, CompositionPlan, FitMode, VideoLayer, BackgroundLayer
from app.services.renderer.graph_builder import FFmpegGraphBuilder


class TestFFmpegGraphBuilder:
    @pytest.fixture
    def builder(self):
        """Create graph builder."""
        return FFmpegGraphBuilder()
    
    @pytest.fixture
    def sample_plan(self):
        """Create sample composition plan."""
        return CompositionPlan(
            canvas_width=1080,
            canvas_height=1920,
            background=BackgroundLayer(
                mode=BackgroundMode.BLUR,
                blur_strength=15,
            ),
            video=VideoLayer(
                width=1080,
                height=607,
                x=0,
                y=656,
            ),
            fit_mode=FitMode.FIT_WIDTH,
        )
    
    def test_add_input(self, builder):
        """Test adding input."""
        label = builder.add_input("video.mp4")
        
        assert label == "0:v"
        assert len(builder.inputs) == 1
    
    def test_add_background_blur(self, builder, sample_plan):
        """Test adding background blur."""
        bg_label = builder.add_background_blur(sample_plan, "0:v")
        
        assert bg_label.startswith("bgblur")
        assert len(builder.filters) > 0
        
        filter_str = builder.build()
        assert "boxblur=15" in filter_str
        assert "scale=1080:1920" in filter_str
    
    def test_add_scaled_video(self, builder, sample_plan):
        """Test adding scaled video."""
        fg_label = builder.add_scaled_video(sample_plan, "0:v")
        
        assert fg_label.startswith("scaled")
        assert len(builder.filters) > 0
        
        filter_str = builder.build()
        assert "scale=" in filter_str
    
    def test_add_overlay(self, builder):
        """Test adding overlay."""
        final_label = builder.add_overlay(
            background_label="bg",
            foreground_label="fg",
            x=0,
            y=656,
        )
        
        assert final_label.startswith("overlay")
        assert len(builder.filters) > 0
        
        filter_str = builder.build()
        assert "overlay=0:656" in filter_str
    
    def test_add_ass_subtitles(self, builder):
        """Test adding ASS subtitles."""
        subs_label = builder.add_ass_subtitles(
            input_label="video",
            subtitle_path="captions.ass",
        )
        
        assert subs_label.startswith("subs")
        assert len(builder.filters) > 0
        
        filter_str = builder.build()
        assert "ass=" in filter_str
    
    def test_build_composition_graph(self, builder, sample_plan):
        """Test building complete composition graph."""
        filter_complex = builder.build_composition_graph(sample_plan)
        
        assert len(filter_complex) > 0
        assert "scale=" in filter_complex
        assert "boxblur=" in filter_complex
        assert "overlay=" in filter_complex
    
    def test_label_uniqueness(self, builder):
        """Test that labels are unique."""
        label1 = builder._next_label("test")
        label2 = builder._next_label("test")
        
        assert label1 != label2
    
    def test_empty_build(self, builder):
        """Test building with no filters."""
        filter_str = builder.build()
        
        assert filter_str == ""
    
    def test_multiple_filters(self, builder):
        """Test building with multiple filters."""
        builder.filters.append("[0:v]scale=1080:1920[a]")
        builder.filters.append("[a]blur=10[b]")
        builder.filters.append("[b]overlay=0:0[out]")
        
        filter_str = builder.build()
        
        assert filter_str.count(";") == 2
        assert "[0:v]scale=1080:1920[a]" in filter_str
        assert "[a]blur=10[b]" in filter_str
        assert "[b]overlay=0:0[out]" in filter_str
