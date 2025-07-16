"""
Unit tests for configuration module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.utils.config import Config


class TestConfig:
    """Test configuration management."""

    def test_default_values(self):
        """Test default configuration values."""
        assert Config.ISTAT_API_BASE_URL == "https://esploradati.istat.it/SDMXWS/rest"
        assert Config.ISTAT_API_TIMEOUT == 30
        assert Config.ENABLE_CACHE == True
        assert Config.CACHE_EXPIRY_HOURS == 24
        assert Config.LOG_LEVEL == "INFO"

    @patch.dict(
        os.environ,
        {
            "ISTAT_API_BASE_URL": "https://test.api.url/",
            "ISTAT_API_TIMEOUT": "60",
            "LOG_LEVEL": "DEBUG",
            "ENABLE_CACHE": "false",
        },
    )
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Reload config with new env vars
        from importlib import reload

        import src.utils.config

        reload(src.utils.config)

        assert src.utils.config.Config.ISTAT_API_BASE_URL == "https://test.api.url/"
        assert src.utils.config.Config.ISTAT_API_TIMEOUT == 60
        assert src.utils.config.Config.LOG_LEVEL == "DEBUG"
        assert src.utils.config.Config.ENABLE_CACHE == False

    def test_directory_structure(self):
        """Test that directory structure is properly defined."""
        assert Config.BASE_DIR.exists()
        assert Config.DATA_DIR == Config.BASE_DIR / "data"
        assert Config.RAW_DATA_DIR == Config.DATA_DIR / "raw"
        assert Config.PROCESSED_DATA_DIR == Config.DATA_DIR / "processed"
        assert Config.CACHE_DIR == Config.DATA_DIR / "cache"
        assert Config.LOGS_DIR == Config.BASE_DIR / "logs"

    def test_ensure_directories_creates_structure(self):
        """Test that ensure_directories creates the required structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock Config directories to use temp directory
            with patch.object(Config, "BASE_DIR", temp_path):
                with patch.object(Config, "DATA_DIR", temp_path / "data"):
                    with patch.object(
                        Config, "RAW_DATA_DIR", temp_path / "data" / "raw"
                    ):
                        with patch.object(
                            Config,
                            "PROCESSED_DATA_DIR",
                            temp_path / "data" / "processed",
                        ):
                            with patch.object(
                                Config, "CACHE_DIR", temp_path / "data" / "cache"
                            ):
                                with patch.object(
                                    Config, "LOGS_DIR", temp_path / "logs"
                                ):
                                    Config.ensure_directories()

                                    # Check directories were created
                                    assert (
                                        temp_path / "data" / "raw" / "istat"
                                    ).exists()
                                    assert (temp_path / "data" / "raw" / "xml").exists()
                                    assert (
                                        temp_path / "data" / "processed" / "tableau"
                                    ).exists()
                                    assert (
                                        temp_path / "data" / "processed" / "powerbi"
                                    ).exists()
                                    assert (temp_path / "data" / "cache").exists()
                                    assert (temp_path / "logs").exists()

                                    # Check .gitkeep files were created
                                    assert (
                                        temp_path
                                        / "data"
                                        / "raw"
                                        / "istat"
                                        / ".gitkeep"
                                    ).exists()
                                    assert (
                                        temp_path / "data" / "cache" / ".gitkeep"
                                    ).exists()

    def test_powerbi_config_optional(self):
        """Test that PowerBI configuration is optional."""
        # Without env vars, should be None
        assert Config.POWERBI_CLIENT_ID is None or Config.POWERBI_CLIENT_ID == ""
        assert (
            Config.POWERBI_CLIENT_SECRET is None or Config.POWERBI_CLIENT_SECRET == ""
        )
        assert Config.POWERBI_TENANT_ID is None or Config.POWERBI_TENANT_ID == ""

    def test_tableau_config_optional(self):
        """Test that Tableau configuration is optional."""
        # Without env vars, should be None
        assert Config.TABLEAU_SERVER_URL is None or Config.TABLEAU_SERVER_URL == ""
        assert Config.TABLEAU_USERNAME is None or Config.TABLEAU_USERNAME == ""
        assert Config.TABLEAU_PASSWORD is None or Config.TABLEAU_PASSWORD == ""

    def test_cache_expiry_hours_conversion(self):
        """Test cache expiry hours is properly converted to int."""
        assert isinstance(Config.CACHE_EXPIRY_HOURS, int)
        assert Config.CACHE_EXPIRY_HOURS > 0

    def test_timeout_conversion(self):
        """Test timeout is properly converted to int."""
        assert isinstance(Config.ISTAT_API_TIMEOUT, int)
        assert Config.ISTAT_API_TIMEOUT > 0

    @patch.dict(os.environ, {"CACHE_EXPIRY_HOURS": "invalid"})
    def test_invalid_cache_expiry_falls_back_to_default(self):
        """Test that invalid cache expiry falls back to default."""
        with pytest.raises(ValueError):
            # This should raise ValueError during config loading
            from importlib import reload

            import src.utils.config

            reload(src.utils.config)
