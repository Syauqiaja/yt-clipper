"""Infrastructure service tests."""

from app.infrastructure.cache.manager import CacheManager


class TestCacheManager:
    def test_set_and_get(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path / "cache")
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key", ttl=3600)
        assert result == {"data": "value"}

    def test_cache_miss(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path / "cache2")
        result = cache.get("nonexistent", ttl=3600)
        assert result is None

    def test_cache_expiry(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path / "cache3")
        cache.set("expiring", "data")
        result = cache.get("expiring", ttl=0)  # TTL expired
        assert result is None

    def test_clear(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path / "cache4")
        for i in range(5):
            cache.set(f"key_{i}", f"value_{i}")
        cache.clear()
        for i in range(5):
            assert cache.get(f"key_{i}") is None
