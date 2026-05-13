"""Transcript parsing tests."""

import tempfile
import pytest

from app.schemas.models import TranscriptSegment, Transcript
from app.services.transcript.service import TranscriptService
from pathlib import Path


class TestTranscriptParsing:
    @pytest.fixture
    def service(self):
        return TranscriptService()

    def test_parse_srt_basic(self, service):
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Hello world

2
00:00:03,500 --> 00:00:06,000
This is a test message
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False) as f:
            f.write(srt_content)
            f.flush()
            transcript = service.parse_subtitle_file(f.name)

        assert len(transcript.segments) >= 1
        assert transcript.source == "youtube"
        assert "Hello world" in transcript.full_text

    def test_parse_vtt_basic(self, service):
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
First segment

00:00:03.500 --> 00:00:06.000
Second segment
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vtt", delete=False) as f:
            f.write(vtt_content)
            f.flush()
            transcript = service.parse_subtitle_file(f.name)

        assert len(transcript.segments) >= 1
        assert transcript.source == "youtube"

    def test_timestamp_conversion(self, service):
        assert service._timestamp_to_seconds("00:01:30,500") == 90.5
        assert service._timestamp_to_seconds("00:00:05,000") == 5.0
        assert service._timestamp_to_seconds("01:00:00,000") == 3600.0

    def test_generate_semantic_chunks(self, service):
        segments = [
            TranscriptSegment(start=i * 10, end=(i + 1) * 10, text=f"Text {i}")
            for i in range(20)
        ]
        transcript = Transcript(segments=segments, source="test", full_text=" ".join(f"Text {i}" for i in range(20)))
        chunks = service.generate_semantic_chunks(transcript, chunk_duration=30.0)
        assert len(chunks) >= 1

    def test_merge_segments(self, service):
        segments = [
            TranscriptSegment(start=0, end=1, text="Hello"),
            TranscriptSegment(start=1, end=2, text="World"),
            TranscriptSegment(start=10, end=11, text="After gap"),
        ]
        transcript = Transcript(segments=segments, source="test")
        merged = service.merge_segments(transcript, max_gap=2.0)
        # First two should merge (gap < 2.0), third stays separate
        assert len(merged.segments) == 2
        assert "Hello World" in merged.segments[0].text

    def test_normalize_transcript(self, service):
        segments = [
            TranscriptSegment(start=0, end=1, text="I mean uh hello there"),
            TranscriptSegment(start=1, end=2, text="you know"),
            TranscriptSegment(start=2, end=3, text="This is great content"),
        ]
        transcript = Transcript(segments=segments, source="test")
        cleaned = service.normalize_transcript(transcript)
        assert "you know" not in cleaned.full_text.lower()

    def test_get_text_between(self, service):
        segments = [
            TranscriptSegment(start=0, end=5, text="Before clip"),
            TranscriptSegment(start=5, end=10, text="Inside clip"),
            TranscriptSegment(start=10, end=15, text="After clip"),
        ]
        transcript = Transcript(segments=segments, source="test")
        text = service.get_text_between(transcript, 5, 10)
        assert "Inside clip" in text
        assert "Before clip" not in text
        assert "After clip" not in text
