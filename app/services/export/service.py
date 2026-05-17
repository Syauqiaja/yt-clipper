"""Export service: organize and save generated clips."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import ClipCandidate, ClipExport, Transcript

logger = get_logger("export")


class ExportService:
    def __init__(self, export_dir: str | Path | None = None):
        self.base_dir = Path(export_dir or settings.export_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _create_project_dir(self, project_name: str) -> dict[str, Path]:
        """Create project directory structure."""
        project_dir = self.base_dir / self._sanitize_name(project_name)

        dirs = {
            "root": project_dir,
            "clips": project_dir / "clips",
            "subtitles": project_dir / "subtitles",
            "thumbnails": project_dir / "thumbnails",
            "metadata": project_dir / "metadata",
        }

        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        return dirs

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for filesystem use."""
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
        return safe[:100].strip()

    def export_clip(
        self,
        clip: ClipCandidate,
        video_path: str | Path,
        subtitle_path: Optional[str | Path],
        thumbnail_path: Optional[str | Path],
        transcript: Optional[Transcript] = None,
        verbose: bool = False,
    ) -> ClipExport:
        """Export a single clip with all artifacts."""
        project_name = f"clip_{clip.rank:02d}_{self._sanitize_name(clip.title)[:40]}"
        dirs = self._create_project_dir(project_name)

        # Move clip video
        final_video = dirs["clips"] / f"{project_name}.mp4"
        Path(video_path).rename(final_video)

        # Move subtitle
        final_sub = None
        if subtitle_path:
            sub_ext = Path(subtitle_path).suffix
            final_sub = dirs["subtitles"] / f"{project_name}{sub_ext}"
            Path(subtitle_path).rename(final_sub)

        # Move thumbnail
        final_thumb = None
        if thumbnail_path:
            final_thumb = dirs["thumbnails"] / f"{project_name}.jpg"
            Path(thumbnail_path).rename(final_thumb)

        # Save metadata
        metadata_path = dirs["metadata"] / f"{project_name}.json"
        self._save_clip_metadata(metadata_path, clip, final_video, final_sub, final_thumb, verbose)

        return ClipExport(
            clip=clip,
            video_path=str(final_video),
            subtitle_path=str(final_sub) if final_sub else None,
            thumbnail_path=str(final_thumb) if final_thumb else None,
            metadata_path=str(metadata_path),
            export_dir=str(dirs["root"]),
        )

    def _save_clip_metadata(
        self,
        path: Path,
        clip: ClipCandidate,
        video_path: Path,
        subtitle_path: Optional[Path],
        thumbnail_path: Optional[Path],
        verbose: bool = False,
    ) -> None:
        """Save clip metadata as JSON."""
        metadata = {
            "title_id": clip.title_id or clip.title,
            "title_en": clip.title_en or clip.title,
            "description_id": clip.description_id or clip.summary,
            "description_en": clip.description_en or clip.summary,
            "files": {
                "video": str(video_path),
                "subtitles": str(subtitle_path) if subtitle_path else None,
                "thumbnail": str(thumbnail_path) if thumbnail_path else None,
            },
            "exported_at": datetime.now().isoformat(),
        }
        
        if verbose:
            metadata.update({
                "title": clip.title,
                "hook": clip.hook,
                "summary": clip.summary,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
                "rank": clip.rank,
                "final_score": clip.final_score,
                "scores": {
                    "hook_strength": clip.scores.hook_strength,
                    "information_density": clip.scores.information_density,
                    "emotional_engagement": clip.scores.emotional_engagement,
                    "storytelling": clip.scores.storytelling,
                    "retention_potential": clip.scores.retention_potential,
                    "viral_potential": clip.scores.viral_potential,
                },
            })

        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def export_all_clips(
        self,
        clips: list[ClipCandidate],
        clip_paths: dict[int, tuple[Path, Optional[Path], Optional[Path]]],
        project_name: str,
        verbose: bool = False,
    ) -> list[ClipExport]:
        """Export all clips for a project."""
        dirs = self._create_project_dir(project_name)
        exports = []

        for clip in clips:
            video_path, sub_path, thumb_path = clip_paths.get(
                clip.rank, (None, None, None)
            )
            if video_path is None:
                continue

            export = self.export_clip(
                clip=clip,
                video_path=video_path,
                subtitle_path=sub_path,
                thumbnail_path=thumb_path,
                verbose=verbose,
            )
            exports.append(export)

        self._save_project_summary(dirs["root"], project_name, exports)
        return exports

    def _save_project_summary(
        self,
        project_dir: Path,
        project_name: str,
        exports: list[ClipExport],
    ) -> None:
        """Save project summary JSON."""
        summary = {
            "project": project_name,
            "total_clips": len(exports),
            "total_duration": sum(e.clip.duration for e in exports),
            "exported_at": datetime.now().isoformat(),
            "clips": [
                {
                    "rank": e.clip.rank,
                    "title": e.clip.title,
                    "duration": e.clip.duration,
                    "score": e.clip.final_score,
                    "video": e.video_path,
                    "subtitles": e.subtitle_path,
                    "metadata": e.metadata_path,
                }
                for e in sorted(exports, key=lambda x: x.clip.rank)
            ],
        }

        summary_path = project_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Project summary saved: {summary_path}")

    def get_export_path(
        self, filename: str, subdir: str = "clips"
    ) -> Path:
        """Get an export file path."""
        safe_name = self._sanitize_name(filename)
        return self.base_dir / subdir / safe_name
