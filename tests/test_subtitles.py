"""Subtitle service tests."""

from pathlib import Path
import tempfile
import pytest

from app.services.subtitles.service import SubtitleService
from app.schemas.models import TranscriptSegment, ClipCandidate, ClipScores


class TestSubtitleService:
    @pytest.fixture
    def service(self):
        return SubtitleService()

    def test_format_timestamp(self, service):
        ts = service.format_timestamp(3661.123)
        assert ts == "01:01:01,123"

    def test_format_vtt_timestamp(self, service):
        ts = service.format_vtt_timestamp(61.5)
        assert ts == "00:01:01.500"

    def test_generate_srt(self, service):
        segments = [
            TranscriptSegment(start=0, end=3, text="Line 1"),
            TranscriptSegment(start=4, end=7, text="Line 2"),
            TranscriptSegment(start=8, end=10, text="Line 3"),
        ]
        clip = ClipCandidate(
            start_time=2,
            end_time=9,
            duration=7,
            title="Test",
            hook="Test",
            summary="Test",
            scores=ClipScores(
                hook_strength=5,
                information_density=5,
                emotional_engagement=5,
                storytelling=5,
                retention_potential=5,
                viral_potential=5,
            ),
        )
        srt = service.generate_srt(segments, clip.start_time, clip.end_time)
        assert "Line 1" in srt
        assert "Line 2" in srt
        assert "Line 3" not in srt  # After end_time

    def test_generate_ass(self, service):
        segments = [
            TranscriptSegment(start=0, end=5, text="Ass line"),
        ]
        clip = ClipCandidate(
            start_time=0,
            end_time=10,
            duration=10,
            title="Test",
            hook="Test",
            summary="Test",
            scores=ClipScores(
                hook_strength=5,
                information_density=5,
                emotional_engagement=5,
                storytelling=5,
                retention_potential=5,
                viral_potential=5,
            ),
        )
        ass = service.generate_ass(segments, clip.start_time, clip.end_time)
        assert "Script Info" in ass
        assert "Ass line" in ass

    def test_generate_tiktok_captions(self, service):
        segments = [
            TranscriptSegment(start=0, end=2, text="Caption 1"),
            TranscriptSegment(start=2, end=4, text="Caption 2"),
        ]
        clip = ClipCandidate(
            start_time=0,
            end_time=10,
            duration=10,
            title="Test",
            hook="Test",
            summary="Test",
            scores=ClipScores(
                hook_strength=5,
                information_density=5,
                emotional_engagement=5,
                storytelling=5,
                retention_potential=5,
                viral_potential=5,
            ),
        )
        captions = service.generate_tiktok_captions(segments, clip)
        assert len(captions) == 2
        assert captions[0].start_time == 0
        assert captions[1].end_time == 4
