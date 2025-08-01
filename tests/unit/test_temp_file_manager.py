"""
Unit tests for temp_file_manager module.
Testing TempFileManager class with comprehensive coverage.
"""
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.utils.temp_file_manager import TempFileManager


class TestTempFileManager:
    """Test TempFileManager class."""

    def test_singleton_pattern(self):
        """Test that TempFileManager implements singleton pattern."""
        manager1 = TempFileManager()
        manager2 = TempFileManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_singleton_thread_safety(self):
        """Test singleton pattern in multi-threaded environment."""
        instances = []

        def create_instance():
            instances.append(TempFileManager())

        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All instances should be the same object
        first_instance = instances[0]
        assert all(instance is first_instance for instance in instances)

    @pytest.fixture
    def manager(self):
        """Create a fresh manager instance for testing."""
        # Reset singleton for clean testing
        TempFileManager._instance = None
        return TempFileManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert hasattr(manager, "_temp_dirs")
        assert hasattr(manager, "_temp_files")
        assert hasattr(manager, "base_temp_dir")
        assert manager.base_temp_dir.exists()
        assert manager.base_temp_dir.name == "osservatorio_istat"

    def test_create_temp_dir_basic(self, manager):
        """Test basic temporary directory creation."""
        temp_dir = manager.create_temp_dir(prefix="test_")

        assert temp_dir.exists()
        assert temp_dir.is_dir()
        assert temp_dir.name.startswith("test_")
        assert temp_dir.parent == manager.base_temp_dir
        assert temp_dir in manager._temp_dirs

    def test_create_temp_dir_no_cleanup(self, manager):
        """Test directory creation without auto-cleanup."""
        temp_dir = manager.create_temp_dir(prefix="no_cleanup_", cleanup_on_exit=False)

        assert temp_dir.exists()
        assert temp_dir not in manager._temp_dirs

    def test_create_temp_file_basic(self, manager):
        """Test basic temporary file creation."""
        temp_file = manager.create_temp_file(suffix=".txt", prefix="test_")

        assert temp_file.exists()
        assert temp_file.is_file()
        assert temp_file.name.startswith("test_")
        assert temp_file.name.endswith(".txt")
        assert temp_file.parent == manager.base_temp_dir
        assert temp_file in manager._temp_files

    def test_create_temp_file_no_cleanup(self, manager):
        """Test file creation without auto-cleanup."""
        temp_file = manager.create_temp_file(suffix=".log", cleanup_on_exit=False)

        assert temp_file.exists()
        assert temp_file not in manager._temp_files

    def test_get_temp_file_path_simple(self, manager):
        """Test getting temp file path with simple filename."""
        temp_path = manager.get_temp_file_path("test.json")

        assert temp_path.name == "test.json"
        assert temp_path.parent == manager.base_temp_dir
        assert temp_path in manager._temp_files

    def test_get_temp_file_path_with_subdir(self, manager):
        """Test getting temp file path with subdirectory."""
        temp_path = manager.get_temp_file_path("data.csv", subdir="api_responses")

        assert temp_path.name == "data.csv"
        assert temp_path.parent.name == "api_responses"
        assert temp_path.parent.parent == manager.base_temp_dir
        assert temp_path.parent.exists()

    def test_get_temp_file_path_no_cleanup(self, manager):
        """Test temp file path without cleanup registration."""
        temp_path = manager.get_temp_file_path("no_cleanup.xml", cleanup_on_exit=False)

        assert temp_path not in manager._temp_files

    def test_cleanup_file(self, manager):
        """Test temporary file cleanup."""
        # Create file
        temp_file = manager.create_temp_file(suffix=".test")
        temp_file.write_text("test content")

        assert temp_file.exists()
        assert temp_file in manager._temp_files

        # Cleanup file
        success = manager.cleanup_file(temp_file)

        assert success
        assert not temp_file.exists()
        assert temp_file not in manager._temp_files

    def test_cleanup_file_nonexistent(self, manager):
        """Test cleaning up non-existent file."""
        fake_path = manager.base_temp_dir / "nonexistent.txt"

        success = manager.cleanup_file(fake_path)
        assert success  # Should return True even if file doesn't exist

    def test_cleanup_directory(self, manager):
        """Test temporary directory cleanup."""
        # Create directory with content
        temp_dir = manager.create_temp_dir(prefix="test_dir_")
        (temp_dir / "file.txt").write_text("content")

        assert temp_dir.exists()
        assert temp_dir in manager._temp_dirs

        # Cleanup directory
        success = manager.cleanup_directory(temp_dir)

        assert success
        assert not temp_dir.exists()
        assert temp_dir not in manager._temp_dirs

    def test_tracked_files_access(self, manager):
        """Test accessing tracked files."""
        # Create some files
        file1 = manager.create_temp_file(suffix=".txt")
        file2 = manager.create_temp_file(suffix=".json")

        temp_files = manager._temp_files

        assert file1 in temp_files
        assert file2 in temp_files
        assert len(temp_files) >= 2

    def test_tracked_dirs_access(self, manager):
        """Test accessing tracked directories."""
        # Create some directories
        dir1 = manager.create_temp_dir(prefix="dir1_")
        dir2 = manager.create_temp_dir(prefix="dir2_")

        temp_dirs = manager._temp_dirs

        assert dir1 in temp_dirs
        assert dir2 in temp_dirs
        assert len(temp_dirs) >= 2

    def test_get_temp_stats(self, manager):
        """Test getting temporary file statistics."""
        # Create files and directories
        manager.create_temp_file(suffix=".txt")
        manager.create_temp_file(suffix=".json")
        manager.create_temp_dir(prefix="stats_test_")

        stats = manager.get_temp_stats()

        assert "tracked_files" in stats
        assert "tracked_dirs" in stats
        assert "total_files" in stats
        assert "total_dirs" in stats
        assert "total_size_mb" in stats
        assert stats["tracked_files"] >= 2
        assert stats["tracked_dirs"] >= 1
        assert isinstance(stats["total_size_mb"], float)

    @patch("src.utils.temp_file_manager.logger")
    def test_cleanup_old_files(self, mock_logger, manager):
        """Test cleanup of old files."""
        # Create an old file by mocking its modification time
        old_file = manager.create_temp_file(suffix=".old")

        # Mock old modification time (2 days ago)
        old_time = time.time() - (2 * 24 * 60 * 60)
        with patch("os.path.getmtime", return_value=old_time):
            removed_count = manager.cleanup_old_files(max_age_hours=24)

        assert isinstance(removed_count, int)
        assert removed_count >= 0

    @patch("src.utils.temp_file_manager.logger")
    def test_cleanup_all(self, mock_logger, manager):
        """Test cleanup of all managed files."""
        # Create some files and directories
        temp_file = manager.create_temp_file(suffix=".cleanup")
        temp_dir = manager.create_temp_dir(prefix="cleanup_")

        # Cleanup
        result = manager.cleanup_all()

        assert "files_removed" in result
        assert "dirs_removed" in result
        assert "errors" in result
        mock_logger.debug.assert_called()

    def test_context_manager_temp_file(self, manager):
        """Test context manager for temporary files."""
        with manager.temp_file(suffix=".ctx") as temp_path:
            assert temp_path.exists()
            temp_path.write_text("context manager test")
            assert temp_path.read_text() == "context manager test"

        # File should be cleaned up after context
        assert not temp_path.exists()

    def test_context_manager_temp_dir(self, manager):
        """Test context manager for temporary directories."""
        with manager.temp_directory(prefix="ctx_") as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            test_file = temp_dir / "test.txt"
            test_file.write_text("test")
            assert test_file.exists()

        # Directory should be cleaned up after context
        assert not temp_dir.exists()

    @patch("shutil.rmtree", side_effect=Exception("Mock error"))
    @patch("src.utils.temp_file_manager.logger")
    def test_cleanup_error_handling(self, mock_logger, mock_rmtree, manager):
        """Test error handling during cleanup."""
        temp_dir = manager.create_temp_dir(prefix="error_test_")

        result = manager.cleanup_all()

        # Should handle errors gracefully
        assert "errors" in result
        # Check if warning was called (cleanup_directory logs warnings)
        assert mock_logger.warning.called or mock_logger.error.called

    @patch("tempfile.mkdtemp", side_effect=Exception("Mock tempdir error"))
    def test_create_temp_dir_error(self, mock_mkdtemp, manager):
        """Test error handling in directory creation."""
        with pytest.raises(Exception, match="Mock tempdir error"):
            manager.create_temp_dir()

    @patch("tempfile.mkstemp", side_effect=Exception("Mock tempfile error"))
    def test_create_temp_file_error(self, mock_mkstemp, manager):
        """Test error handling in file creation."""
        with pytest.raises(Exception, match="Mock tempfile error"):
            manager.create_temp_file()

    def test_temp_file_actual_creation_and_cleanup(self, manager):
        """Integration test for actual file operations."""
        # Test actual file creation and cleanup
        temp_file = manager.create_temp_file(suffix=".integration")

        # Write content
        test_content = "Integration test content"
        temp_file.write_text(test_content)

        # Verify content
        assert temp_file.read_text() == test_content

        # Manual cleanup
        manager.cleanup_file(temp_file)
        assert not temp_file.exists()

    def test_base_temp_dir_creation(self, manager):
        """Test that base temp directory is created correctly."""
        assert manager.base_temp_dir.exists()
        assert manager.base_temp_dir.is_dir()
        assert str(manager.base_temp_dir).endswith("osservatorio_istat")

    def test_multiple_subdir_creation(self, manager):
        """Test creating files in multiple subdirectories."""
        # Create files in different subdirs
        path1 = manager.get_temp_file_path("file1.txt", subdir="dir1")
        path2 = manager.get_temp_file_path("file2.txt", subdir="dir2/subdir")

        assert path1.parent.name == "dir1"
        assert path2.parent.name == "subdir"
        assert path1.parent.exists()
        assert path2.parent.exists()
