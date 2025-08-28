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

            # Get file metadata
            try:
                stat = path.stat()
                file_info = FileInfo(
                    path=path,
                    size_bytes=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime),
                    created_time=datetime.fromtimestamp(stat.st_ctime),
                    is_directory=path.is_dir(),
                    attributes=None  # Will be filled in by Windows-specific code later
                )
                yield file_info
            except (OSError, PermissionError):
                # Skip files we can't access
                return

            # If it's a directory, recurse into it
            if path.is_dir():
                try:
                    for child in path.iterdir():
                        if self._cancelled:
                            return
                        yield from self._scan_directory(child, max_depth - 1, follow_symlinks)
                except (OSError, PermissionError):
                    # Skip directories we can't access
                    pass

        except (OSError, PermissionError):
            # Skip paths we can't access
            pass
