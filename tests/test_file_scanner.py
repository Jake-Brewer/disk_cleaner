"""Tests for File System Scanner module."""

import pytest
from pathlib import Path
from typing import List


class TestFileSystemScanner:
    """Test suite for File System Scanner functionality."""

    @pytest.mark.unit
    def test_directory_traversal_core(self):
        """Test basic recursive directory traversal functionality."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test directory structure
            (temp_path / "file1.txt").write_text("content1")
            (temp_path / "file2.txt").write_text("content2")
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "file3.txt").write_text("content3")

            # This should work if directory traversal is implemented
            files = list(scanner._scan_directory(temp_path, max_depth=5))
            assert len(files) == 3

            file_paths = [f.path for f in files]
            assert (temp_path / "file1.txt") in file_paths
            assert (temp_path / "file2.txt") in file_paths
            assert (subdir / "file3.txt") in file_paths

    @pytest.mark.unit
    def test_max_depth_limiting(self):
        """Test that max_depth parameter limits traversal depth."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create deep directory structure
            deep_dir = temp_path
            for i in range(5):
                deep_dir = deep_dir / f"level{i}"
                deep_dir.mkdir()
                (deep_dir / f"file{i}.txt").write_text(f"content{i}")

            # Test with max_depth=2
            files = list(scanner._scan_directory(temp_path, max_depth=2))
            file_paths = [str(f.path) for f in files]

            # Should find files in levels 0 and 1, but not deeper
            level0_files = [p for p in file_paths if "level0" in p and p.endswith(".txt")]
            level1_files = [p for p in file_paths if "level1" in p and p.endswith(".txt")]
            level2_files = [p for p in file_paths if "level2" in p and p.endswith(".txt")]

            assert len(level0_files) > 0
            assert len(level1_files) > 0
            assert len(level2_files) == 0  # Should be limited by max_depth

    @pytest.mark.unit
    def test_permission_error_handling(self):
        """Test graceful handling of permission denied errors."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path
        import os
        import stat

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a directory with no access permissions
            no_access_dir = temp_path / "no_access"
            no_access_dir.mkdir()

            # Remove all permissions (this might not work on all systems)
            try:
                os.chmod(no_access_dir, 0o000)
                files = list(scanner._scan_directory(temp_path, max_depth=5))
                # Should continue scanning despite permission error
                assert len(files) >= 0  # May find other files or none
            finally:
                # Restore permissions for cleanup
                os.chmod(no_access_dir, stat.S_IRWXU)

    @pytest.mark.unit
    def test_symlink_handling(self):
        """Test handling of symbolic links according to configuration."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create target directory and file
            target_dir = temp_path / "target"
            target_dir.mkdir()
            (target_dir / "target_file.txt").write_text("target content")

            # Create symlink (if supported on platform)
            link_path = temp_path / "link"
            try:
                link_path.symlink_to(target_dir, target_is_directory=True)

                # Test with follow_symlinks=False (default)
                files_no_follow = list(scanner._scan_directory(temp_path, max_depth=5, follow_symlinks=False))
                symlink_files = [f for f in files_no_follow if "link" in str(f.path)]
                assert len(symlink_files) == 0  # Symlink target should not be followed

                # Test with follow_symlinks=True
                files_follow = list(scanner._scan_directory(temp_path, max_depth=5, follow_symlinks=True))
                target_files = [f for f in files_follow if "target_file.txt" in str(f.path)]
                assert len(target_files) > 0  # Should find file through symlink

            except OSError:
                # Symlinks not supported on this platform
                pytest.skip("Symlinks not supported on this platform")

    @pytest.mark.unit
    def test_cancellation_support(self):
        """Test that directory traversal can be cancelled."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path
        import threading
        import time

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create many files to slow down traversal
            for i in range(100):
                (temp_path / f"file{i}.txt").write_text(f"content{i}")

            # Start scanning in a thread
            results = []
            def scan_worker():
                try:
                    results.extend(scanner._scan_directory(temp_path, max_depth=5))
                except Exception as e:
                    results.append(e)

            scan_thread = threading.Thread(target=scan_worker)
            scan_thread.start()

            # Cancel after a short time
            time.sleep(0.01)  # Give it a tiny bit of time to start
            scanner.cancel()

            scan_thread.join(timeout=1.0)

            # Should either complete or be cancelled gracefully
            assert scan_thread.is_alive() == False  # Thread should have finished
