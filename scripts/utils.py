#!/usr/bin/env python3
"""
Day 6: Shared utilities for scripts - Eliminates code duplication

Common functions used across multiple scripts including:
- Banner printing and formatting
- Logging setup
- Configuration loading
- Error handling
- Script setup patterns
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from src.utils.config import Config
    from src.utils.structured_logger import get_structured_logger
except ImportError:
    # Fallback configuration for development
    Config = None


def print_banner(title: str, subtitle: str = "", width: int = 60):
    """Print a standardized banner for scripts."""
    separator = "=" * width
    print(f"🚀{separator}")
    print(f"  {title.upper()}")
    if subtitle:
        print(f"  {subtitle}")
    print(separator)


def print_step(step_num: int, title: str, description: str = ""):
    """Print a standardized step indicator."""
    print(f"\n🔸 Step {step_num}: {title}")
    if description:
        print(f"   {description}")


def print_success(message: str, details: str = ""):
    """Print a success message."""
    print(f"✅ {message}")
    if details:
        print(f"   {details}")


def print_error(message: str, details: str = ""):
    """Print an error message."""
    print(f"❌ {message}")
    if details:
        print(f"   {details}")


def print_warning(message: str, details: str = ""):
    """Print a warning message."""
    print(f"⚠️ {message}")
    if details:
        print(f"   {details}")


def print_info(message: str, details: str = ""):
    """Print an info message."""
    print(f"ℹ️ {message}")
    if details:
        print(f"   {details}")


def setup_script_logging(
    script_name: str, level: str = "INFO", use_structured_logging: bool = True
) -> logging.Logger:
    """Setup standardized logging for scripts."""
    if use_structured_logging and Config and Config.STRUCTURED_LOGGING_ENABLED:
        try:
            logger = get_structured_logger(script_name)
            return logger
        except ImportError:
            pass

    # Fallback to standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(script_name)


def get_script_config() -> Dict[str, Any]:
    """Get centralized configuration for scripts."""
    if Config:
        return {
            "api_base_url": Config.API_BASE_URL,
            "api_timeout": Config.API_TIMEOUT,
            "redis_url": Config.REDIS_URL,
            "enable_cache": Config.ENABLE_CACHE,
            "log_level": Config.LOG_LEVEL,
            "structured_logging": Config.STRUCTURED_LOGGING_ENABLED,
        }
    else:
        # Fallback configuration
        return {
            "api_base_url": "http://localhost:8000",
            "api_timeout": 30,
            "redis_url": "redis://localhost:6379/0",
            "enable_cache": True,
            "log_level": "INFO",
            "structured_logging": False,
        }


def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def format_size(bytes_size: int) -> str:
    """Format file size in a human-readable way."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def safe_json_load(file_path: Path) -> Optional[Dict]:
    """Safely load JSON file with error handling."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print_error(f"Failed to load JSON file: {file_path}", str(e))
        return None


def safe_json_save(data: Dict, file_path: Path) -> bool:
    """Safely save data to JSON file with error handling."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print_error(f"Failed to save JSON file: {file_path}", str(e))
        return False


def create_timestamp_filename(base_name: str, extension: str = "json") -> str:
    """Create a filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


def ensure_project_root() -> Path:
    """Ensure we're working from the project root directory."""
    current_path = Path.cwd()

    # Look for project markers
    project_markers = ["pyproject.toml", "requirements.txt", "src", "tests"]

    # Check if current directory has project markers
    if any((current_path / marker).exists() for marker in project_markers):
        return current_path

    # Check parent directories
    for parent in current_path.parents:
        if any((parent / marker).exists() for marker in project_markers):
            return parent

    # If not found, assume current directory
    return current_path


class ScriptError(Exception):
    """Custom exception for script errors."""

    pass


class ScriptContext:
    """Context manager for script execution with standardized setup and cleanup."""

    def __init__(
        self,
        script_name: str,
        title: str,
        subtitle: str = "",
        enable_logging: bool = True,
    ):
        self.script_name = script_name
        self.title = title
        self.subtitle = subtitle
        self.enable_logging = enable_logging
        self.logger = None
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()

        # Print banner
        print_banner(self.title, self.subtitle)

        # Setup logging
        if self.enable_logging:
            self.logger = setup_script_logging(self.script_name)
            self.logger.info(f"Script started: {self.script_name}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            duration_str = format_duration(duration)

            if exc_type is None:
                print_success(f"Script completed successfully in {duration_str}")
                if self.logger:
                    self.logger.info(f"Script completed successfully in {duration_str}")
            else:
                print_error(f"Script failed after {duration_str}", str(exc_val))
                if self.logger:
                    self.logger.error(f"Script failed after {duration_str}: {exc_val}")

        return False  # Don't suppress exceptions


def main():
    """Demo of script utilities."""
    with ScriptContext(
        "script_utils_demo", "Script Utilities Demo", "Testing shared utilities"
    ):
        print_step(1, "Configuration Loading")
        config = get_script_config()
        print_info("Configuration loaded", f"API URL: {config['api_base_url']}")

        print_step(2, "Timing Demo")
        import time

        time.sleep(0.5)
        print_success("Sleep completed")

        print_step(3, "Size Formatting Demo")
        sizes = [1024, 1048576, 1073741824]
        for size in sizes:
            print_info(f"Size: {size} bytes = {format_size(size)}")


if __name__ == "__main__":
    main()
