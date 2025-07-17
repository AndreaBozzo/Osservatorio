"""
Secure path validation utilities for file operations.
Prevents directory traversal attacks and ensures safe file operations.
"""

import os
import re
from pathlib import Path
from typing import Optional, Union

from .logger import get_logger

logger = get_logger(__name__)


class SecurePathValidator:
    """Validator for secure file path operations."""

    # Dangerous path patterns to reject
    DANGEROUS_PATTERNS = [
        r"\.\./",  # Directory traversal
        r"\.\.\\",  # Directory traversal (Windows)
        r"~/",  # Home directory expansion
        r"^\/",  # Absolute path from root
        r"^[A-Za-z]:[\\/]",  # Windows absolute paths with drive letters
        r"<script",  # Script injection
        r"javascript:",  # JavaScript execution
        r"data:",  # Data URI
        r"file:",  # File URI
        r"\.exe$",  # Executable files
        r"\.bat$",  # Batch files
        r"\.cmd$",  # Command files
        r"\.com$",  # COM files
        r"\.scr$",  # Screen saver files
        r"\.vbs$",  # VBScript files
        r"\.sh$",  # Shell scripts
        r"\.py$",  # Python scripts (except in allowed directories)
        r"\.jar$",  # Java archives
    ]

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        ".txt",
        ".md",
        ".json",
        ".xml",
        ".csv",
        ".xlsx",
        ".xls",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".html",
        ".htm",
        ".css",
        ".js",
        ".ts",
        ".parquet",
        ".log",
        ".tmp",
        ".ps1",
    }

    def __init__(self, base_directory: Union[str, Path]):
        """
        Initialize validator with base directory.

        Args:
            base_directory: Base directory for safe operations
        """
        self.base_directory = Path(base_directory).resolve()
        logger.debug(
            f"SecurePathValidator initialized with base: {self.base_directory}"
        )

    def validate_filename(self, filename: str) -> bool:
        """
        Validate filename for security issues.

        Args:
            filename: Filename to validate

        Returns:
            True if filename is safe, False otherwise
        """
        if not filename or not isinstance(filename, str):
            logger.warning("Invalid filename: empty or not string")
            return False

        # Skip validation for Windows drive letters
        if re.match(r"^[A-Za-z]:[\\/]?$", filename):
            return True

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                logger.warning(f"Dangerous pattern found in filename: {filename}")
                return False

        # Check for null bytes
        if "\x00" in filename:
            logger.warning(f"Null byte found in filename: {filename}")
            return False

        # Check for control characters
        if any(ord(char) < 32 for char in filename):
            logger.warning(f"Control character found in filename: {filename}")
            return False

        # Check filename length
        if len(filename) > 255:
            logger.warning(f"Filename too long: {filename}")
            return False

        # Check for reserved Windows names
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        name_part = filename.split(".")[0].upper()
        if name_part in reserved_names:
            logger.warning(f"Reserved Windows name: {filename}")
            return False

        return True

    def validate_path(self, path: Union[str, Path]) -> bool:
        """
        Validate path for security issues.

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        if not path:
            logger.warning("Empty path provided")
            return False

        try:
            path_obj = Path(path)

            # Check if path is within base directory
            resolved_path = path_obj.resolve()

            # Ensure path is within base directory
            try:
                resolved_path.relative_to(self.base_directory)
            except ValueError:
                logger.warning(f"Path outside base directory: {path}")
                return False

            # Validate each path component (skip drive letters on Windows)
            for part in path_obj.parts:
                # Skip Windows drive letters (e.g., 'C:', 'C:\')
                if re.match(r"^[A-Za-z]:[\\/]?$", part):
                    continue
                if not self.validate_filename(part):
                    return False

            return True

        except Exception as e:
            logger.warning(f"Error validating path {path}: {e}")
            return False

    def validate_extension(self, filename: str) -> bool:
        """
        Validate file extension.

        Args:
            filename: Filename to check

        Returns:
            True if extension is allowed, False otherwise
        """
        if not filename:
            return False

        path_obj = Path(filename)
        extension = path_obj.suffix.lower()

        # Allow files without extension in some cases
        if not extension:
            return True

        is_allowed = extension in self.ALLOWED_EXTENSIONS
        if not is_allowed:
            logger.warning(f"Disallowed file extension: {extension}")

        return is_allowed

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing dangerous characters.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"

        # Remove dangerous characters and replace spaces with underscores
        sanitized = re.sub(r'[<>:"/\\|?*\s]', "_", filename)

        # Collapse multiple consecutive underscores to single underscore
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove control characters
        sanitized = "".join(char for char in sanitized if ord(char) >= 32)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[: 255 - len(ext)] + ext

        # Handle reserved Windows names
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        name_part = sanitized.split(".")[0].upper()
        if name_part in reserved_names:
            # Replace reserved name with name_file
            parts = sanitized.split(".", 1)
            if len(parts) > 1:
                sanitized = f"{parts[0]}_file.{parts[1]}"
            else:
                sanitized = f"{sanitized}_file"

        # Ensure not empty
        if not sanitized or sanitized == ".":
            sanitized = "unnamed_file"

        return sanitized

    def get_safe_path(
        self, path: Union[str, Path], create_dirs: bool = False
    ) -> Optional[Path]:
        """
        Get safe path within base directory.

        Args:
            path: Path to make safe
            create_dirs: Whether to create parent directories

        Returns:
            Safe path or None if invalid
        """
        if not path:
            return None

        try:
            path_obj = Path(path)

            # If absolute path, make it relative to base
            if path_obj.is_absolute():
                # Only allow if already within base directory
                if not self.validate_path(path):
                    return None
                safe_path = path_obj.resolve()
            else:
                # Make relative path safe
                safe_path = (self.base_directory / path).resolve()

            # Final validation
            if not self.validate_path(safe_path):
                return None

            # Create parent directories if requested
            if create_dirs:
                safe_path.parent.mkdir(parents=True, exist_ok=True)

            return safe_path

        except Exception as e:
            logger.error(f"Error creating safe path for {path}: {e}")
            return None

    def safe_open(self, path: Union[str, Path], mode: str = "r", **kwargs):
        """
        Safely open file with path validation.

        Args:
            path: Path to file
            mode: File open mode
            **kwargs: Additional arguments for open()

        Returns:
            File handle or None if invalid
        """
        safe_path = self.get_safe_path(path)
        if not safe_path:
            logger.error(f"Cannot safely open file: {path}")
            return None

        # Validate filename
        if not self.validate_filename(safe_path.name):
            logger.error(f"Invalid filename: {safe_path.name}")
            return None

        # Validate extension for write operations
        if "w" in mode or "a" in mode:
            if not self.validate_extension(safe_path.name):
                logger.error(f"Disallowed file extension: {safe_path.name}")
                return None

        try:
            # Create parent directories for write operations
            if "w" in mode or "a" in mode:
                safe_path.parent.mkdir(parents=True, exist_ok=True)

            return open(safe_path, mode, **kwargs)

        except Exception as e:
            logger.error(f"Error opening file {safe_path}: {e}")
            return None


def create_secure_validator(base_directory: Union[str, Path]) -> SecurePathValidator:
    """
    Create secure path validator instance.

    Args:
        base_directory: Base directory for operations

    Returns:
        SecurePathValidator instance
    """
    return SecurePathValidator(base_directory)
