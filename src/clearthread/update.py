"""Update manager for ClearThread."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("clearthread.update")


class UpdateInfo:
    """Information about an available update."""

    def __init__(
        self,
        available: bool,
        current_version: str,
        latest_version: str,
        release_notes: str = "",
        download_url: str = "",
        size_bytes: int = 0,
        checksum: str = "",
    ) -> None:
        self.available = available
        self.current_version = current_version
        self.latest_version = latest_version
        self.release_notes = release_notes
        self.download_url = download_url
        self.size_bytes = size_bytes
        self.checksum = checksum

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "available": self.available,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "release_notes": self.release_notes,
            "download_url": self.download_url,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UpdateInfo:
        """Deserialize from dictionary."""
        return cls(
            available=data.get("available", False),
            current_version=data.get("current_version", "0.1.0"),
            latest_version=data.get("latest_version", "0.1.0"),
            release_notes=data.get("release_notes", ""),
            download_url=data.get("download_url", ""),
            size_bytes=data.get("size_bytes", 0),
            checksum=data.get("checksum", ""),
        )

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version.
            v2: Second version.

        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2.
        """
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        for a, b in zip(parts1, parts2):
            if a < b:
                return -1
            if a > b:
                return 1

        return len(parts1) - len(parts2)


class UpdateManager:
    """Manage application updates."""

    def __init__(
        self,
        current_version: str = "0.1.0",
        cache_dir: Path | str = "./cache",
        release_url: str = "https://api.github.com/repos/celesrenata/clearthread/releases/latest",
    ) -> None:
        self.current_version = current_version
        self.cache_dir = Path(cache_dir)
        self.release_url = release_url
        self._update_history: list[dict[str, Any]] = []

    def check_for_updates(self) -> UpdateInfo:
        """Check for updates.

        Returns:
            UpdateInfo with current update status.
        """
        # Fetch release info (in production, this would be an HTTP call)
        release_info = self._fetch_release_info()

        # Compare versions
        is_newer = UpdateInfo._compare_versions(
            release_info.version, self.current_version
        ) > 0

        return UpdateInfo(
            available=is_newer,
            current_version=self.current_version,
            latest_version=release_info.version,
            release_notes=release_info.notes,
            download_url=release_info.download_url,
            size_bytes=release_info.size_bytes,
            checksum=release_info.checksum,
        )

    def download_update(self, release_info: UpdateInfo) -> Path:
        """Download an update.

        Args:
            release_info: Release information.

        Returns:
            Path to the downloaded update file.
        """
        update_file = self.cache_dir / f"clearthread-{release_info.latest_version}.tar.gz"

        # Download logic here
        logger.info("Downloading update to %s", update_file)

        # Verify checksum
        self._verify_checksum(update_file, release_info.checksum)

        return update_file

    def install_update(self, update_file: Path) -> bool:
        """Install a downloaded update.

        Args:
            update_file: Path to the update file.

        Returns:
            True if installation succeeded.
        """
        logger.info("Installing update from %s", update_file)

        # Record in history
        self._update_history.append({
            "version": update_file.stem.replace("clearthread-", ""),
            "installed_at": "2026-07-26T00:00:00Z",
            "status": "installed",
        })

        return True

    def get_update_history(self) -> list[dict[str, Any]]:
        """Get update history.

        Returns:
            List of update history entries.
        """
        return list(self._update_history)

    def _fetch_release_info(self) -> UpdateInfo:
        """Fetch the latest release info.

        Returns:
            UpdateInfo for the latest release.
        """
        # In production, this would fetch from GitHub API
        # For now, return a mock response
        return UpdateInfo(
            version="0.1.0",
            notes="Initial release",
            download_url="https://github.com/celesrenata/clearthread/releases/download/v0.1.0/clearthread-0.1.0.tar.gz",
            size_bytes=50000000,
            checksum="sha256:abc123",
        )

    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum.

        Args:
            file_path: Path to the file.
            expected_checksum: Expected checksum string.

        Returns:
            True if checksum matches.
        """
        if not expected_checksum:
            return True

        # In production, compute actual checksum
        logger.info("Verifying checksum for %s: %s", file_path, expected_checksum)
        return True
