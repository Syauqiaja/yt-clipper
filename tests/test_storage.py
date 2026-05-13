"""Storage manager tests."""

from pathlib import Path
import tempfile
import pytest

from app.infrastructure.storage.manager import StorageManager


class TestStorageManager:
    @pytest.fixture
    def storage(self, tmp_path):
        return StorageManager(base_dir=tmp_path)

    def test_create_temp_file_string(self, storage):
        path = storage.create_temp_file("test.txt", "hello world")
        assert path.exists()
        assert path.read_text() == "hello world"

    def test_create_temp_file_bytes(self, storage):
        path = storage.create_temp_file("test.bin", b"\x00\x01\x02")
        assert path.exists()
        assert path.read_bytes() == b"\x00\x01\x02"

    def test_read_write_json(self, storage):
        data = {"key": "value", "number": 42}
        storage.write_json("data.json", data)
        result = storage.read_json("data.json")
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_cleanup(self, storage):
        for i in range(5):
            storage.create_temp_file(f"file_{i}.txt", f"data {i}")
        storage.cleanup("file_*.txt")
        remaining = list(storage.base_dir.glob("file_*.txt"))
        assert len(remaining) == 0

    def test_ensure_dir(self, storage):
        path = storage.ensure_dir("subdir/nested")
        assert path.exists()
        assert path.is_dir()
