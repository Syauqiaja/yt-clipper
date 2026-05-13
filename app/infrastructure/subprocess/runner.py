import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any

from app.core.exceptions import FFmpegError, TimeoutError
from app.infrastructure.logging.logger import get_logger

logger = get_logger("subprocess")


class SubprocessRunner:
    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    def run(
        self,
        cmd: list[str],
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a subprocess command."""
        logger.debug(f"Running command: {' '.join(cmd)}")
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=capture_output,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )
            elapsed = time.time() - start_time
            logger.debug(f"Command completed in {elapsed:.2f}s")

            if result.returncode != 0:
                logger.error(f"Command failed with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Stderr: {result.stderr[:500]}")

            return result

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"Command timed out after {self.timeout}s: {e}")
        except Exception as e:
            raise FFmpegError(f"Failed to run command: {e}")

    async def run_async(
        self,
        cmd: list[str],
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a subprocess command asynchronously."""
        logger.debug(f"Running async command: {' '.join(cmd)}")
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )

            elapsed = time.time() - start_time
            logger.debug(f"Async command completed in {elapsed:.2f}s")

            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode("utf-8", errors="replace") if stdout else "",
                stderr=stderr.decode("utf-8", errors="replace") if stderr else "",
            )

            if result.returncode != 0:
                logger.error(f"Async command failed with code {result.returncode}")
                if result.stderr:
                    logger.error(f"Stderr: {result.stderr[:500]}")

            return result

        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Async command timed out after {self.timeout}s: {e}")
        except Exception as e:
            raise FFmpegError(f"Failed to run async command: {e}")

    def check_command_exists(self, cmd: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                ["which", cmd],
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def get_ffmpeg_version(self) -> str:
        """Get FFmpeg version."""
        try:
            result = self.run(["ffmpeg", "-version"])
            lines = result.stdout.split("\n")
            if lines:
                return lines[0].strip()
            return "Unknown"
        except Exception as e:
            logger.warning(f"Failed to get FFmpeg version: {e}")
            return "Not found"
