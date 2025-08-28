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

    @pytest.mark.unit
    def test_comprehensive_file_metadata(self):
        """Test collection of comprehensive file metadata."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path
        import time

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files with different characteristics
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")

            # Create a hidden file (Windows-specific)
            hidden_file = temp_path / "hidden.txt"
            hidden_file.write_text("hidden content")
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(hidden_file), 2)  # FILE_ATTRIBUTE_HIDDEN
            except (AttributeError, OSError):
                pass  # Skip on non-Windows platforms

            # Create a large file
            large_file = temp_path / "large.txt"
            large_content = "x" * 10000
            large_file.write_text(large_content)

            # Wait a moment to ensure different timestamps
            time.sleep(0.1)

            # Scan and collect metadata
            files = list(scanner._scan_directory(temp_path, max_depth=5))

            # Find our test files
            test_file_info = next((f for f in files if f.path.name == "test.txt"), None)
            hidden_file_info = next((f for f in files if f.path.name == "hidden.txt"), None)
            large_file_info = next((f for f in files if f.path.name == "large.txt"), None)

            # Verify comprehensive metadata collection
            assert test_file_info is not None
            assert test_file_info.size_bytes == len("test content")
            assert test_file_info.is_directory == False
            assert isinstance(test_file_info.modified_time, datetime)
            assert isinstance(test_file_info.created_time, datetime)

            assert large_file_info is not None
            assert large_file_info.size_bytes == len(large_content)
            assert large_file_info.size_bytes > 1000  # Should be large

            # Verify large file handling
            assert large_file_info.is_large_file()  # Should have this method

    @pytest.mark.unit
    def test_file_hash_seed_generation(self):
        """Test generation of hash seeds for duplicate detection."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            file1 = temp_path / "file1.txt"
            file1.write_text("content1")

            file2 = temp_path / "file2.txt"
            file2.write_text("content2")

            # Scan and check hash seed generation
            files = list(scanner._scan_directory(temp_path, max_depth=5))

            file1_info = next((f for f in files if f.path.name == "file1.txt"), None)
            file2_info = next((f for f in files if f.path.name == "file2.txt"), None)

            # Verify hash seed generation
            assert file1_info is not None
            assert file2_info is not None
            assert hasattr(file1_info, 'hash_seed')
            assert hasattr(file2_info, 'hash_seed')
            assert file1_info.hash_seed != file2_info.hash_seed  # Different files should have different seeds

    @pytest.mark.unit
    def test_windows_file_attributes(self):
        """Test collection of Windows file attributes."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            normal_file = temp_path / "normal.txt"
            normal_file.write_text("normal")

            # Create system file (if possible)
            system_file = temp_path / "system.txt"
            system_file.write_text("system")
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(system_file), 4)  # FILE_ATTRIBUTE_SYSTEM
            except (AttributeError, OSError):
                pass  # Skip on non-Windows platforms

            # Scan and check attributes
            files = list(scanner._scan_directory(temp_path, max_depth=5))

            normal_info = next((f for f in files if f.path.name == "normal.txt"), None)
            system_info = next((f for f in files if f.path.name == "system.txt"), None)

            # Verify attribute collection
            assert normal_info is not None
            assert system_info is not None
            assert hasattr(normal_info, 'attributes')
            assert hasattr(system_info, 'attributes')

    @pytest.mark.unit
    def test_metadata_collection_performance(self):
        """Test that metadata collection is performed efficiently."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path
        import time

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create many files for performance testing
            for i in range(100):
                (temp_path / f"file{i}.txt").write_text(f"content{i}")

            # Time the metadata collection
            start_time = time.time()
            files = list(scanner._scan_directory(temp_path, max_depth=5))
            end_time = time.time()

            # Verify performance is reasonable
            assert len(files) == 100
            assert (end_time - start_time) < 1.0  # Should complete in less than 1 second

    @pytest.mark.unit
    def test_special_file_handling(self):
        """Test handling of special file types (junctions, hardlinks)."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a regular file
            regular_file = temp_path / "regular.txt"
            regular_file.write_text("regular")

            # Try to create a hardlink (if supported)
            try:
                hardlink_file = temp_path / "hardlink.txt"
                hardlink_file.hardlink_to(regular_file)

                # Scan and verify both files are found
                files = list(scanner._scan_directory(temp_path, max_depth=5))
                file_names = [f.path.name for f in files if f.path.name.endswith('.txt')]

                assert "regular.txt" in file_names
                assert "hardlink.txt" in file_names

            except OSError:
                files = list(scanner._scan_directory(temp_path, max_depth=5))
                file_names = [f.path.name for f in files if f.path.name.endswith('.txt')]
                assert "regular.txt" in file_names

    @pytest.mark.unit
    def test_glob_pattern_exclusion(self):
        """Test exclusion of files and directories using glob patterns."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner, ScanConfig
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test directory structure
            (temp_path / "keep.txt").write_text("keep")
            (temp_path / "exclude.txt").write_text("exclude")
            (temp_path / "important.doc").write_text("important")

            # Create subdirectory with files
            subdir = temp_path / "cache"
            subdir.mkdir()
            (subdir / "temp.dat").write_text("temp")
            (subdir / "cache.tmp").write_text("cache")

            # Test glob pattern exclusion
            config = ScanConfig(
                max_depth=5,
                exclude_patterns=["*.tmp", "*.dat", "cache/**"]
            )

            files = list(scanner._scan_directory_with_config(temp_path, config))

            # Verify excluded files are not present
            file_names = [f.path.name for f in files]
            assert "exclude.txt" not in file_names  # Should be excluded by pattern
            assert "temp.dat" not in file_names     # Should be excluded
            assert "cache.tmp" not in file_names    # Should be excluded
            assert "keep.txt" in file_names         # Should be kept
            assert "important.doc" in file_names    # Should be kept

    @pytest.mark.unit
    def test_size_based_filtering(self):
        """Test filtering files based on size thresholds."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner, ScanConfig
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files of different sizes
            small_file = temp_path / "small.txt"
            small_file.write_text("small")  # ~5 bytes

            large_file = temp_path / "large.txt"
            large_content = "x" * 2000  # ~2000 bytes
            large_file.write_text(large_content)

            # Test size-based filtering (exclude files smaller than 100 bytes)
            config = ScanConfig(
                max_depth=5,
                min_file_size_bytes=100
            )

            files = list(scanner._scan_directory_with_config(temp_path, config))

            # Verify only large file is included
            file_names = [f.path.name for f in files]
            assert "large.txt" in file_names
            assert "small.txt" not in file_names  # Should be filtered out

    @pytest.mark.unit
    def test_file_extension_filtering(self):
        """Test filtering files based on extensions."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner, ScanConfig
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different extensions
            (temp_path / "document.txt").write_text("text")
            (temp_path / "spreadsheet.xlsx").write_text("excel")
            (temp_path / "presentation.pptx").write_text("powerpoint")
            (temp_path / "executable.exe").write_text("binary")
            (temp_path / "archive.zip").write_text("archive")

            # Test extension-based filtering
            config = ScanConfig(
                max_depth=5,
                exclude_extensions=[".exe", ".zip"]
            )

            files = list(scanner._scan_directory_with_config(temp_path, config))

            # Verify excluded extensions are not present
            file_names = [f.path.name for f in files]
            assert "document.txt" in file_names
            assert "spreadsheet.xlsx" in file_names
            assert "presentation.pptx" in file_names
            assert "executable.exe" not in file_names  # Should be excluded
            assert "archive.zip" not in file_names     # Should be excluded

    @pytest.mark.unit
    def test_path_based_exclusion(self):
        """Test exclusion based on specific paths and directories."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner, ScanConfig
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            (temp_path / "keep.txt").write_text("keep")

            temp_dir = temp_path / "temp"
            temp_dir.mkdir()
            (temp_dir / "tempfile.txt").write_text("temp")

            cache_dir = temp_path / "cache"
            cache_dir.mkdir()
            (cache_dir / "cached.dat").write_text("cache")

            # Test path-based exclusion
            config = ScanConfig(
                max_depth=5,
                exclude_patterns=["temp/**", "cache/**"]
            )

            files = list(scanner._scan_directory_with_config(temp_path, config))

            # Verify excluded paths are not present
            file_paths = [str(f.path) for f in files]
            assert any("keep.txt" in path for path in file_paths)
            assert not any("tempfile.txt" in path for path in file_paths)
            assert not any("cached.dat" in path for path in file_paths)

    @pytest.mark.unit
    def test_combined_exclusion_rules(self):
        """Test that multiple exclusion rules work together."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner, ScanConfig
        import tempfile
        from pathlib import Path

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mixed file structure
            (temp_path / "keep.txt").write_text("keep")
            (temp_path / "temp.log").write_text("x" * 50)  # Small file
            (temp_path / "large.tmp").write_text("x" * 2000)  # Large temp file

            temp_dir = temp_path / "temp"
            temp_dir.mkdir()
            (temp_dir / "nested.exe").write_text("exe")  # In temp dir

            # Test combined exclusion rules
            config = ScanConfig(
                max_depth=5,
                exclude_patterns=["temp/**", "*.tmp"],
                min_file_size_bytes=100,
                exclude_extensions=[".exe"]
            )

            files = list(scanner._scan_directory_with_config(temp_path, config))

            # Verify all exclusion rules work together
            file_names = [f.path.name for f in files]
            assert "keep.txt" in file_names         # Should be kept
            assert "temp.log" not in file_names     # Excluded by size
            assert "large.tmp" not in file_names    # Excluded by extension
            assert "nested.exe" not in file_names   # Excluded by path and extension

    @pytest.mark.unit
    def test_exclusion_performance(self):
        """Test that exclusion rules don't significantly impact performance."""
        from disk_cleaner.src.disk_cleaner.file_scanner import FileSystemScanner, ScanConfig
        import tempfile
        from pathlib import Path
        import time

        scanner = FileSystemScanner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create many files with various patterns
            for i in range(200):
                if i % 3 == 0:
                    (temp_path / f"keep{i}.txt").write_text("keep")
                elif i % 3 == 1:
                    (temp_path / f"temp{i}.tmp").write_text("temp")
                else:
                    (temp_path / f"exclude{i}.exe").write_text("exe")

            # Test performance with exclusion rules
            config = ScanConfig(
                max_depth=5,
                exclude_patterns=["*.tmp", "*.exe"],
                min_file_size_bytes=0
            )

            start_time = time.time()
            files = list(scanner._scan_directory_with_config(temp_path, config))
            end_time = time.time()

            # Verify exclusions worked
            file_names = [f.path.name for f in files]
            assert any("keep" in name for name in file_names)
            assert not any(".tmp" in name for name in file_names)
            assert not any(".exe" in name for name in file_names)

            # Verify performance is reasonable
            assert (end_time - start_time) < 2.0  # Should complete in less than 2 seconds
