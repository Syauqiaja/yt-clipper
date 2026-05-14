#!/usr/bin/env python3
"""
Test script for Phase 2 rendering system.

This script tests the rendering pipeline without requiring full video download,
transcription, and AI analysis. It uses dummy video and caption files.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.formats import FormatRegistry
from app.services.templates import TemplateRegistry
from app.services.composition import CompositionPlanner, FitMode, BackgroundMode
from app.services.renderer import RenderService, FFmpegGraphBuilder
from app.services.captions import CaptionService, CaptionPresets, CaptionChunk, WordTimestamp
from app.services.ffmpeg.service import FFmpegService
from app.infrastructure.logging.logger import get_logger

logger = get_logger("test_rendering")


def create_dummy_video(output_path: Path, duration: int = 10, width: int = 1920, height: int = 1080):
    """Create a dummy test video using FFmpeg."""
    import subprocess
    
    logger.info(f"Creating dummy video: {width}x{height}, {duration}s")
    
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size={width}x{height}:rate=25",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration={duration}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-y",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed to create dummy video: {result.stderr}")
        raise Exception("Failed to create dummy video")
    
    logger.info(f"✓ Created dummy video: {output_path}")
    return output_path


def create_dummy_captions(output_path: Path, duration: int = 10):
    """Create dummy ASS caption file."""
    logger.info("Creating dummy captions")
    
    # Create dummy word timestamps
    words = []
    word_list = ["This", "is", "a", "test", "caption", "for", "Phase", "2", "rendering", "system"]
    
    time_per_word = duration / len(word_list)
    for i, word in enumerate(word_list):
        words.append(WordTimestamp(
            word=word,
            start=i * time_per_word,
            end=(i + 1) * time_per_word,
        ))
    
    # Generate captions
    style = CaptionPresets.tiktok()
    caption_service = CaptionService(style=style)
    
    ass_path = caption_service.generate_captions(
        words=words,
        output_path=output_path,
        video_width=1080,
        video_height=1920,
        karaoke=True,
    )
    
    logger.info(f"✓ Created dummy captions: {ass_path}")
    return ass_path


def test_composition_planning():
    """Test composition planning."""
    logger.info("\n=== Testing Composition Planning ===")
    
    planner = CompositionPlanner()
    output_format = FormatRegistry.get("shorts")
    
    plan = planner.plan_composition(
        video_width=1920,
        video_height=1080,
        output_format=output_format,
        fit_mode=FitMode.FIT_WIDTH,
        background_mode=BackgroundMode.BLUR,
        blur_strength=15,
    )
    
    logger.info(f"✓ Canvas: {plan.canvas_width}x{plan.canvas_height}")
    logger.info(f"✓ Video layer: {plan.video.width}x{plan.video.height} at ({plan.video.x}, {plan.video.y})")
    logger.info(f"✓ Fit mode: {plan.fit_mode.value}")
    logger.info(f"✓ Background: {plan.background.mode.value}")
    
    return plan


def test_ffmpeg_graph_builder(plan):
    """Test FFmpeg graph builder."""
    logger.info("\n=== Testing FFmpeg Graph Builder ===")
    
    builder = FFmpegGraphBuilder()
    filter_complex = builder.build_composition_graph(plan)
    
    logger.info(f"✓ Generated filter graph with {len(builder.filters)} filters")
    logger.info(f"Filter complex:\n{filter_complex}")
    
    return filter_complex


def test_rendering_without_captions(input_video: Path, output_video: Path):
    """Test rendering without captions."""
    logger.info("\n=== Testing Rendering WITHOUT Captions ===")
    
    # Get video info
    ffmpeg = FFmpegService()
    info = ffmpeg.get_video_info(input_video)
    video_width = info["streams"][0]["width"]
    video_height = info["streams"][0]["height"]
    
    logger.info(f"Input video: {video_width}x{video_height}")
    
    # Render
    renderer = RenderService()
    result = renderer.render_with_template(
        input_path=input_video,
        output_path=output_video,
        template_name="shorts_fit",
        format_name="tiktok",
        video_width=video_width,
        video_height=video_height,
        subtitle_path=None,
    )
    
    logger.info(f"✓ Rendered successfully: {result}")
    return result


def test_rendering_with_captions(input_video: Path, caption_file: Path, output_video: Path):
    """Test rendering with captions."""
    logger.info("\n=== Testing Rendering WITH Captions ===")
    
    # Get video info
    ffmpeg = FFmpegService()
    info = ffmpeg.get_video_info(input_video)
    video_width = info["streams"][0]["width"]
    video_height = info["streams"][0]["height"]
    
    logger.info(f"Input video: {video_width}x{video_height}")
    logger.info(f"Caption file: {caption_file}")
    
    # Render
    renderer = RenderService()
    result = renderer.render_with_template(
        input_path=input_video,
        output_path=output_video,
        template_name="shorts_fit",
        format_name="tiktok",
        video_width=video_width,
        video_height=video_height,
        subtitle_path=caption_file,
    )
    
    logger.info(f"✓ Rendered successfully: {result}")
    return result


def test_manual_ffmpeg_command(input_video: Path, caption_file: Path, output_video: Path):
    """Test manual FFmpeg command to isolate the issue."""
    logger.info("\n=== Testing Manual FFmpeg Command ===")
    
    import subprocess
    
    # Test 1: Basic composition without captions
    logger.info("Test 1: Composition only (no captions)")
    cmd1 = [
        "ffmpeg",
        "-i", str(input_video),
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bg];"
        "[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=0:656[out]",
        "-map", "[out]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-y",
        str(output_video).replace(".mp4", "_no_subs.mp4"),
    ]
    
    result = subprocess.run(cmd1, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("✓ Test 1 PASSED: Composition works")
    else:
        logger.error(f"✗ Test 1 FAILED: {result.stderr[-500:]}")
    
    # Test 2: Subtitles filter syntax
    logger.info("\nTest 2: Subtitles filter (different syntaxes)")
    
    # Try different subtitle filter syntaxes
    subtitle_syntaxes = [
        f"subtitles={caption_file}",
        f"subtitles='{caption_file}'",
        f"subtitles=filename={caption_file}",
        f"subtitles=filename='{caption_file}'",
        f"ass={caption_file}",
        f"ass='{caption_file}'",
    ]
    
    for i, sub_filter in enumerate(subtitle_syntaxes, 1):
        logger.info(f"\n  Syntax {i}: {sub_filter}")
        
        cmd2 = [
            "ffmpeg",
            "-i", str(input_video),
            "-filter_complex",
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bg];"
            f"[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=0:656[out];"
            f"[out]{sub_filter}[final]",
            "-map", "[final]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(output_video).replace(".mp4", f"_syntax{i}.mp4"),
        ]
        
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info(f"  ✓ Syntax {i} WORKS!")
            return sub_filter
        else:
            error_msg = result.stderr.split('\n')[-5:]
            logger.error(f"  ✗ Syntax {i} failed: {' '.join(error_msg)}")
    
    logger.error("✗ All subtitle syntaxes failed")
    return None


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Phase 2 Rendering Test Suite")
    logger.info("=" * 80)
    
    # Setup test directory
    test_dir = Path("temp/test_rendering")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    dummy_video = test_dir / "dummy_input.mp4"
    dummy_captions = test_dir / "dummy_captions.ass"
    output_no_subs = test_dir / "output_no_subs.mp4"
    output_with_subs = test_dir / "output_with_subs.mp4"
    
    try:
        # Step 1: Create test files
        logger.info("\n" + "=" * 80)
        logger.info("Step 1: Creating Test Files")
        logger.info("=" * 80)
        
        if not dummy_video.exists():
            create_dummy_video(dummy_video, duration=10, width=1920, height=1080)
        else:
            logger.info(f"Using existing dummy video: {dummy_video}")
        
        if not dummy_captions.exists():
            create_dummy_captions(dummy_captions, duration=10)
        else:
            logger.info(f"Using existing dummy captions: {dummy_captions}")
        
        # Step 2: Test composition planning
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Testing Composition Planning")
        logger.info("=" * 80)
        plan = test_composition_planning()
        
        # Step 3: Test FFmpeg graph builder
        logger.info("\n" + "=" * 80)
        logger.info("Step 3: Testing FFmpeg Graph Builder")
        logger.info("=" * 80)
        filter_complex = test_ffmpeg_graph_builder(plan)
        
        # Step 4: Test rendering without captions
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Testing Rendering Without Captions")
        logger.info("=" * 80)
        try:
            test_rendering_without_captions(dummy_video, output_no_subs)
        except Exception as e:
            logger.error(f"✗ Rendering without captions failed: {e}")
        
        # Step 5: Test manual FFmpeg commands
        logger.info("\n" + "=" * 80)
        logger.info("Step 5: Testing Manual FFmpeg Commands")
        logger.info("=" * 80)
        working_syntax = test_manual_ffmpeg_command(dummy_video, dummy_captions, output_with_subs)
        
        if working_syntax:
            logger.info(f"\n✓ WORKING SUBTITLE SYNTAX: {working_syntax}")
        
        # Step 6: Test rendering with captions (if we found working syntax)
        if working_syntax:
            logger.info("\n" + "=" * 80)
            logger.info("Step 6: Testing Rendering With Captions")
            logger.info("=" * 80)
            try:
                test_rendering_with_captions(dummy_video, dummy_captions, output_with_subs)
            except Exception as e:
                logger.error(f"✗ Rendering with captions failed: {e}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("Test Summary")
        logger.info("=" * 80)
        logger.info(f"Test files created in: {test_dir}")
        logger.info(f"Dummy video: {dummy_video}")
        logger.info(f"Dummy captions: {dummy_captions}")
        if output_no_subs.exists():
            logger.info(f"✓ Output (no subs): {output_no_subs}")
        if output_with_subs.exists():
            logger.info(f"✓ Output (with subs): {output_with_subs}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Tests Complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
