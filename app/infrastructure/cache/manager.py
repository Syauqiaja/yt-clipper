import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from app.core.exceptions import CacheError
from app.infrastructure.logging.logger import get_logger

logger = get_logger("cache")


class CacheManager:
    def __init__(self, cache_dir: str | Path = "temp/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cache manager initialized at {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, ttl: int = 3600) -> Optional[Any]:
        """Get cached value if not expired."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at > timedelta(seconds=ttl):
                logger.debug(f"Cache expired for {key}")
                cache_path.unlink()
                return None
            
            logger.debug(f"Cache hit for {key}")
            return data["value"]
        
        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Set cached value."""
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                "cached_at": datetime.now().isoformat(),
                "value": value,
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Cache set for {key}")
        
        except Exception as e:
            raise CacheError(f"Failed to set cache for {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete cached value."""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Cache deleted for {key}")

    def clear(self) -> None:
        """Clear all cache."""
        try:
            for path in self.cache_dir.glob("*.json"):
                path.unlink()
            logger.debug("Cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

    def get_or_compute(
        self, key: str, compute_func: callable, ttl: int = 3600, *args, **kwargs
    ) -> Any:
        """Get cached value or compute and cache it."""
        cached = self.get(key, ttl)
        if cached is not None:
            return cached
        
        value = compute_func(*args, **kwargs)
        self.set(key, value)
        return value


class VideoCache:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def get_video_metadata(self, video_id: str) -> Optional[dict]:
        """Get cached video metadata."""
        return self.cache.get(f"video_metadata_{video_id}", ttl=86400)

    def set_video_metadata(self, video_id: str, metadata: dict) -> None:
        """Cache video metadata."""
        self.cache.set(f"video_metadata_{video_id}", metadata)

    def get_transcript(self, video_id: str) -> Optional[list]:
        """Get cached transcript."""
        return self.cache.get(f"transcript_{video_id}", ttl=86400)

    def set_transcript(self, video_id: str, transcript: list) -> None:
        """Cache transcript."""
        self.cache.set(f"transcript_{video_id}", transcript)

    def get_analysis(self, video_id: str) -> Optional[dict]:
        """Get cached AI analysis."""
        return self.cache.get(f"analysis_{video_id}", ttl=3600)

    def set_analysis(self, video_id: str, analysis: dict) -> None:
        """Cache AI analysis."""
        self.cache.set(f"analysis_{video_id}", analysis)
