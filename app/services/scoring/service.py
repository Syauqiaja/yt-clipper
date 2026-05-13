"""Scoring engine: weighted clip ranking and filtering."""

from app.config.settings import settings
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import ClipCandidate

logger = get_logger("scoring")


class ScoringService:
    @property
    def weights(self) -> dict[str, float]:
        """Get current scoring weights."""
        w = settings.scoring_weights
        # Ensure total = 1.0 by normalizing
        total = sum(w.values())
        if total == 0:
            default_w = len(w)
            return {k: 1.0 / default_w for k in w}
        return {k: v / total for k, v in w.items()}

    def calculate_score(self, clip: ClipCandidate) -> float:
        """Calculate weighted final score for a single clip."""
        s = clip.scores
        w = self.weights

        score = (
            s.hook_strength * w["hook_strength"]
            + s.retention_potential * w["retention_potential"]
            + s.information_density * w["information_density"]
            + s.storytelling * w["storytelling"]
            + s.emotional_engagement * w["emotional_engagement"]
        )

        return round(score, 4)

    def rank_clips(self, clips: list[ClipCandidate]) -> list[ClipCandidate]:
        """Rank clips by final weighted score."""
        scored = []
        for clip in clips:
            clip.final_score = self.calculate_score(clip)
            scored.append(clip)

        scored.sort(key=lambda c: c.final_score, reverse=True)

        for rank, clip in enumerate(scored, 1):
            clip.rank = rank

        logger.info(f"Ranked {len(scored)} clips by score")
        return scored

    def filter_by_min_score(
        self, clips: list[ClipCandidate], threshold: float
    ) -> list[ClipCandidate]:
        """Filter clips below minimum final score."""
        filtered = [c for c in clips if c.final_score >= threshold]
        logger.info(f"Filtered to {len(filtered)} clips above score {threshold}")
        return filtered

    def select_top_clips(
        self, clips: list[ClipCandidate], count: int
    ) -> list[ClipCandidate]:
        """Select top N clips by score."""
        ranked = self.rank_clips(clips)
        selected = ranked[:count]
        logger.info(f"Selected top {count} clips from {len(ranked)} candidates")
        return selected

    def compare_clips(self, clips: list[ClipCandidate]) -> dict[str, float]:
        """Get average scores across all clips per dimension."""
        if not clips:
            return {}

        dims = ["hook_strength", "information_density", "emotional_engagement",
                "storytelling", "retention_potential", "viral_potential"]
        averages = {}

        for dim in dims:
            values = [getattr(c.scores, dim) for c in clips]
            averages[dim] = round(sum(values) / len(values), 2)

        return averages

    def validate_scores(
        self, clip: ClipCandidate, min_total: float = 5.0
    ) -> bool:
        """Validate that a clip meets minimum quality standards."""
        avg = self.calculate_score(clip)
        min_single = min(
            clip.scores.hook_strength,
            clip.scores.retention_potential,
            clip.scores.information_density,
        )

        if avg < min_total:
            logger.debug(
                f"Clip '{clip.title}' avg score {avg:.2f} below minimum {min_total}"
            )
            return False
        if min_single < 3.0:
            logger.debug(
                f"Clip '{clip.title}' weakest dimension {min_single:.2f} too low"
            )
            return False

        return True
