"""File System Scanner module for Disk Cleaner."""

from abc import ABC, abstractmethod
from typing import Iterator, List, Optional
from pathlib import Path
import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """Information about a file or directory."""
    path: Path
    size_bytes: int
    modified_time: datetime
    created_time: datetime
    is_directory: bool
    attributes: Optional[object] = None  # For Windows file attributes
    hash_seed: Optional[str] = None  # For duplicate detection optimization

    def is_large_file(self, threshold_mb: int = 100) -> bool:
        """Check if file is considered large based on size threshold.

        Args:
            threshold_mb: Size threshold in MB

        Returns:
            True if file size exceeds threshold
        """
        threshold_bytes = threshold_mb * 1024 * 1024
        return self.size_bytes > threshold_bytes

    def get_age_days(self) -> int:
        """Get the age of the file in days since modification.

        Returns:
            Number of days since last modification
        """
        return (datetime.now() - self.modified_time).days


@dataclass
class ScanConfig:
    """Configuration for file system scanning."""
    max_depth: int = 10
    follow_symlinks: bool = False


class FileSystemScanner:
    """Scans file systems and collects file metadata."""

    def __init__(self):
        """Initialize the file system scanner."""
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel ongoing scan operations."""
        self._cancelled = True

    def _scan_directory(self, path: Path, max_depth: int, follow_symlinks: bool = False) -> Iterator[FileInfo]:
        """Recursively scan a directory and yield FileInfo objects.

        Args:
            path: Root path to scan
            max_depth: Maximum directory depth to scan
            follow_symlinks: Whether to follow symbolic links

        Yields:
            FileInfo objects for each file and directory found
        """
        if self._cancelled:
            return

        if max_depth < 0:
            return

        try:
            # Check if it's a symlink and whether we should follow it
            if path.is_symlink() and not follow_symlinks:
                return

            # Resolve symlinks if we're following them
            resolved_path = path.resolve() if follow_symlinks and path.is_symlink() else path

            # Get file metadata
            try:
                stat = resolved_path.stat()
                hash_seed = f"{resolved_path.name}:{stat.st_size}:{stat.st_mtime}"

                # Collect Windows file attributes if available
                attributes = None
                try:
                    import ctypes
                    # Get file attributes using Windows API
                    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(resolved_path))
                    if attrs != -1:  # -1 indicates error
                        attributes = attrs
                except (AttributeError, OSError):
                    # Not on Windows or API failed, attributes remain None
                    pass

                file_info = FileInfo(
                    path=path,  # Keep original path, not resolved
                    size_bytes=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime),
                    created_time=datetime.fromtimestamp(stat.st_ctime),
                    is_directory=resolved_path.is_dir(),
                    attributes=attributes,  # Windows file attributes
                    hash_seed=hash_seed  # For duplicate detection optimization
                )
                yield file_info
            except (OSError, PermissionError):
                # Skip files we can't access
                return

            # If it's a directory, recurse into it
            if resolved_path.is_dir():
                try:
                    for child in resolved_path.iterdir():
                        if self._cancelled:
                            return
                        yield from self._scan_directory(child, max_depth - 1, follow_symlinks)
                except (OSError, PermissionError):
                    # Skip directories we can't access
                    pass

        except (OSError, PermissionError):
            # Skip paths we can't access
            pass
