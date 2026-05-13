import json
import shutil
from pathlib import Path
from typing import Any

from app.core.exceptions import StorageError
from app.infrastructure.logging.logger import get_logger

logger = get_logger("storage")


class StorageManager:
    def __init__(self, base_dir: str | Path = "temp"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Storage manager initialized at {self.base_dir}")

    def get_temp_path(self, filename: str) -> Path:
        """Get a temporary file path."""
        return self.base_dir / filename

    def create_temp_file(self, filename: str, content: bytes | str) -> Path:
        """Create a temporary file with content."""
        path = self.get_temp_path(filename)
        try:
            if isinstance(content, str):
                path.write_text(content, encoding="utf-8")
            else:
                path.write_bytes(content)
            logger.debug(f"Created temp file: {path}")
            return path
        except Exception as e:
            raise StorageError(f"Failed to create temp file {filename}: {e}")

    def read_temp_file(self, filename: str) -> str:
        """Read a temporary file."""
        path = self.get_temp_path(filename)
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise StorageError(f"Failed to read temp file {filename}: {e}")

    def read_json(self, filename: str) -> Any:
        """Read JSON from a temporary file."""
        content = self.read_temp_file(filename)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON in {filename}: {e}")

    def write_json(self, filename: str, data: Any) -> Path:
        """Write JSON to a temporary file."""
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return self.create_temp_file(filename, content)

    def copy_file(self, src: Path, dst_filename: str) -> Path:
        """Copy a file to temp storage."""
        dst = self.get_temp_path(dst_filename)
        try:
            shutil.copy2(src, dst)
            logger.debug(f"Copied {src} to {dst}")
            return dst
        except Exception as e:
            raise StorageError(f"Failed to copy {src} to {dst_filename}: {e}")

    def move_file(self, src: Path, dst_filename: str) -> Path:
        """Move a file to temp storage."""
        dst = self.get_temp_path(dst_filename)
        try:
            shutil.move(str(src), dst)
            logger.debug(f"Moved {src} to {dst}")
            return dst
        except Exception as e:
            raise StorageError(f"Failed to move {src} to {dst_filename}: {e}")

    def cleanup(self, pattern: str = "*") -> None:
        """Clean up temporary files."""
        try:
            for path in self.base_dir.glob(pattern):
                if path.is_file():
                    path.unlink()
                    logger.debug(f"Cleaned up: {path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

    def ensure_dir(self, dirname: str) -> Path:
        """Ensure a directory exists in temp storage."""
        path = self.base_dir / dirname
        path.mkdir(parents=True, exist_ok=True)
        return path
