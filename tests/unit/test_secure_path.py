"""
Unit tests for secure path validation utilities.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.utils.secure_path import SecurePathValidator, create_secure_validator


class TestSecurePathValidator:
    """Test SecurePathValidator class."""

    def test_init_creates_validator(self):
        """Test validator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            assert validator.base_directory == Path(temp_dir).resolve()
            assert len(validator.DANGEROUS_PATTERNS) > 0
            assert len(validator.ALLOWED_EXTENSIONS) > 0

    def test_validate_filename_valid_names(self):
        """Test filename validation with valid names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test valid filenames
            assert validator.validate_filename("test.json") is True
            assert validator.validate_filename("data_file.csv") is True
            assert validator.validate_filename("report.xlsx") is True
            assert validator.validate_filename("script.ps1") is True
            assert validator.validate_filename("config.xml") is True

    def test_validate_filename_invalid_names(self):
        """Test filename validation with invalid names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test invalid filenames
            assert validator.validate_filename("../test.json") is False
            assert validator.validate_filename("test.exe") is False
            assert validator.validate_filename("script.bat") is False
            assert validator.validate_filename("") is False
            assert validator.validate_filename(None) is False

    def test_validate_filename_dangerous_patterns(self):
        """Test filename validation with dangerous patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test dangerous patterns
            assert validator.validate_filename("../../../etc/passwd") is False
            assert validator.validate_filename("..\\..\\windows\\system32") is False
            assert validator.validate_filename("~/sensitive_file") is False
            assert validator.validate_filename("<script>alert('xss')</script>") is False
            assert validator.validate_filename("javascript:alert('xss')") is False

    def test_validate_extension_allowed_extensions(self):
        """Test extension validation with allowed extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test allowed extensions
            assert validator.validate_extension("test.json") is True
            assert validator.validate_extension("data.csv") is True
            assert validator.validate_extension("report.xlsx") is True
            assert validator.validate_extension("script.ps1") is True
            assert validator.validate_extension("config.xml") is True

    def test_validate_extension_disallowed_extensions(self):
        """Test extension validation with disallowed extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test disallowed extensions
            assert validator.validate_extension("malware.exe") is False
            assert validator.validate_extension("script.bat") is False
            assert validator.validate_extension("virus.scr") is False
            assert validator.validate_extension("test.unknown") is False

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test basic sanitization
            assert validator.sanitize_filename("test file.json") == "test_file.json"
            assert (
                validator.sanitize_filename("file:with:colons.csv")
                == "file_with_colons.csv"
            )
            assert (
                validator.sanitize_filename("file<>with<>brackets.txt")
                == "file_with_brackets.txt"
            )

    def test_sanitize_filename_reserved_names(self):
        """Test filename sanitization with reserved names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test reserved names
            assert validator.sanitize_filename("CON.txt") == "CON_file.txt"
            assert validator.sanitize_filename("PRN.json") == "PRN_file.json"
            assert validator.sanitize_filename("AUX.csv") == "AUX_file.csv"

    def test_sanitize_filename_long_names(self):
        """Test filename sanitization with long names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test long filename
            long_name = "a" * 300 + ".txt"
            sanitized = validator.sanitize_filename(long_name)

            assert len(sanitized) <= 255
            assert sanitized.endswith(".txt")

    def test_validate_path_within_base_directory(self):
        """Test path validation within base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test paths within base directory
            valid_path = Path(temp_dir) / "test_file.json"
            assert validator.validate_path(valid_path) is True

            sub_dir = Path(temp_dir) / "subdir" / "test.txt"
            assert validator.validate_path(sub_dir) is True

    def test_validate_path_outside_base_directory(self):
        """Test path validation outside base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test paths outside base directory
            parent_path = Path(temp_dir).parent / "outside.txt"
            assert validator.validate_path(parent_path) is False

            root_path = Path("/etc/passwd")
            assert validator.validate_path(root_path) is False

    def test_get_safe_path_relative(self):
        """Test getting safe path for relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test relative path
            safe_path = validator.get_safe_path("test_file.json")
            assert safe_path is not None
            assert safe_path.parent == Path(temp_dir).resolve()
            assert safe_path.name == "test_file.json"

    def test_get_safe_path_absolute_within_base(self):
        """Test getting safe path for absolute paths within base."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test absolute path within base
            abs_path = Path(temp_dir) / "test_file.json"
            safe_path = validator.get_safe_path(abs_path)
            assert safe_path is not None
            assert safe_path == abs_path.resolve()

    def test_get_safe_path_absolute_outside_base(self):
        """Test getting safe path for absolute paths outside base."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test absolute path outside base
            outside_path = Path(temp_dir).parent / "outside.txt"
            safe_path = validator.get_safe_path(outside_path)
            assert safe_path is None

    def test_get_safe_path_with_directory_creation(self):
        """Test getting safe path with directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test path with non-existent directory
            nested_path = "subdir/nested/test_file.json"
            safe_path = validator.get_safe_path(nested_path, create_dirs=True)

            assert safe_path is not None
            assert safe_path.parent.exists()
            assert safe_path.parent.is_dir()

    def test_safe_open_valid_file(self):
        """Test safe file opening with valid file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test opening valid file
            with patch("builtins.open", mock_open()) as mock_file:
                file_handle = validator.safe_open("test.json", "w")
                assert file_handle is not None
                mock_file.assert_called_once()

    def test_safe_open_invalid_file(self):
        """Test safe file opening with invalid file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test opening invalid file
            file_handle = validator.safe_open("../../../etc/passwd", "w")
            assert file_handle is None

    def test_safe_open_disallowed_extension(self):
        """Test safe file opening with disallowed extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurePathValidator(temp_dir)

            # Test opening file with disallowed extension
            file_handle = validator.safe_open("malware.exe", "w")
            assert file_handle is None


class TestCreateSecureValidator:
    """Test create_secure_validator function."""

    def test_create_secure_validator_with_string(self):
        """Test creating validator with string path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = create_secure_validator(temp_dir)

            assert isinstance(validator, SecurePathValidator)
            assert validator.base_directory == Path(temp_dir).resolve()

    def test_create_secure_validator_with_path(self):
        """Test creating validator with Path object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path_obj = Path(temp_dir)
            validator = create_secure_validator(path_obj)

            assert isinstance(validator, SecurePathValidator)
            assert validator.base_directory == path_obj.resolve()

    def test_create_secure_validator_with_nonexistent_path(self):
        """Test creating validator with non-existent path."""
        # Should not raise exception - validator will create directory if needed
        validator = create_secure_validator("/tmp/nonexistent_test_dir")
        assert isinstance(validator, SecurePathValidator)
