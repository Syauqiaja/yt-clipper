import pytest
from app.schemas.models import ClipScores, ClipCandidate, TranscriptSegment, Transcript
from app.services.scoring.service import ScoringService


class TestClipScores:
    def test_valid_scores(self):
        scores = ClipScores(
            hook_strength=8.0,
            information_density=7.5,
            emotional_engagement=6.0,
            storytelling=7.0,
            retention_potential=8.5,
            viral_potential=7.0,
        )
        assert scores.hook_strength == 8.0
        assert scores.information_density == 7.5
        assert scores.retention_potential == 8.5

    def test_score_bounds(self):
        with pytest.raises(Exception):
            ClipScores(
                hook_strength=11.0,  # Above max 10
                information_density=7.0,
                emotional_engagement=5.0,
                storytelling=6.0,
                retention_potential=8.0,
                viral_potential=7.0,
            )


class TestClipCandidate:
    def test_calculate_final_score(self):
        clip = ClipCandidate(
            start_time=10.0,
            end_time=60.0,
            duration=50.0,
            title="Test Clip",
            hook="Test Hook",
            summary="Test Summary",
            scores=ClipScores(
                hook_strength=9.0,
                information_density=8.0,
                emotional_engagement=7.0,
                storytelling=8.0,
                retention_potential=9.0,
                viral_potential=8.5,
            ),
        )
        score = clip.calculate_final_score()
        assert 0 <= score <= 10
        assert score > 7.0

    def test_duration_validation(self):
        with pytest.raises(Exception):
            ClipCandidate(
                start_time=10.0,
                end_time=-5.0,
                duration=15.0,
                title="Bad Clip",
                hook="Hook",
                summary="Summary",
                scores=ClipScores(
                    hook_strength=5.0,
                    information_density=5.0,
                    emotional_engagement=5.0,
                    storytelling=5.0,
                    retention_potential=5.0,
                    viral_potential=5.0,
                ),
            )


class TestTranscript:
    def test_segment_creation(self):
        seg = TranscriptSegment(start=0.0, end=5.0, text="Hello world", confidence=0.95)
        assert seg.start == 0.0
        assert seg.text == "Hello world"

    def test_full_text_generation(self):
        segments = [
            TranscriptSegment(start=0.0, end=1.0, text="This is a test."),
            TranscriptSegment(start=1.0, end=2.0, text="Second sentence."),
        ]
        transcript = Transcript(segments=segments, source="youtube")
        assert "This is a test. Second sentence." in transcript.full_text


class TestScoringService:
    def test_rank_clips(self):
        service = ScoringService()
        clips = [
            ClipCandidate(
                start_time=0,
                end_time=30,
                duration=30,
                title="Great Clip",
                hook="Amazing hook",
                summary="Great content",
                scores=ClipScores(
                    hook_strength=9.0,
                    information_density=8.0,
                    emotional_engagement=7.0,
                    storytelling=8.0,
                    retention_potential=9.0,
                    viral_potential=8.5,
                ),
            ),
            ClipCandidate(
                start_time=30,
                end_time=60,
                duration=30,
                title="OK Clip",
                hook="OK hook",
                summary="OK content",
                scores=ClipScores(
                    hook_strength=5.0,
                    information_density=5.0,
                    emotional_engagement=5.0,
                    storytelling=5.0,
                    retention_potential=5.0,
                    viral_potential=5.0,
                ),
            ),
        ]
        ranked = service.rank_clips(clips)
        assert ranked[0].rank == 1
        assert ranked[0].final_score > ranked[1].final_score

    def test_filter_by_min_score(self):
        service = ScoringService()
        clips = [
            ClipCandidate(
                start_time=0,
                end_time=30,
                duration=30,
                title="Good",
                hook="Good",
                summary="Good",
                scores=ClipScores(
                    hook_strength=8.0,
                    information_density=8.0,
                    emotional_engagement=8.0,
                    storytelling=8.0,
                    retention_potential=8.0,
                    viral_potential=8.0,
                ),
            ),
            ClipCandidate(
                start_time=30,
                end_time=60,
                duration=30,
                title="Bad",
                hook="Bad",
                summary="Bad",
                scores=ClipScores(
                    hook_strength=2.0,
                    information_density=2.0,
                    emotional_engagement=2.0,
                    storytelling=2.0,
                    retention_potential=2.0,
                    viral_potential=2.0,
                ),
            ),
        ]
        ranked = service.rank_clips(clips)
        filtered = service.filter_by_min_score(ranked, 5.0)
        assert len(filtered) == 1
        assert filtered[0].title == "Good"
