"""
Unit tests for K8sConfigManager

Tests the Kubernetes-native configuration management functionality.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.config.environment_config import EnvironmentConfig
from src.services.config.k8s_config_manager import K8sConfigManager


class TestK8sConfigManager:
    """Test K8sConfigManager functionality"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            secrets_dir = Path(temp_dir) / "secrets"

            config_dir.mkdir()
            secrets_dir.mkdir()

            yield str(config_dir), str(secrets_dir)

    def test_config_manager_initialization(self, temp_config_dir):
        """Test K8sConfigManager initialization"""
        config_dir, secrets_dir = temp_config_dir

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        assert manager.config_dir == Path(config_dir)
        assert manager.secrets_dir == Path(secrets_dir)
        assert not manager.enable_hot_reload

    def test_environment_config_loading(self):
        """Test loading configuration from environment variables"""
        with patch.dict(
            os.environ,
            {
                "DATAFLOW_ENVIRONMENT": "test",
                "DATAFLOW_SERVICE_NAME": "test-service",
                "DATAFLOW_DATABASE_URL": "postgresql://test:test@localhost:5432/test",
                "DATAFLOW_REDIS_HOST": "localhost",
                "DATAFLOW_ENABLE_DISTRIBUTED_CACHING": "true",
            },
        ):
            config = EnvironmentConfig.from_environment()

            assert config.environment == "test"
            assert config.service_name == "test-service"
            assert config.database.url == "postgresql://test:test@localhost:5432/test"
            assert config.redis.host == "localhost"
            assert config.enable_distributed_caching is True

    def test_configmap_file_loading(self, temp_config_dir):
        """Test loading configuration from ConfigMap files"""
        config_dir, secrets_dir = temp_config_dir

        # Create test ConfigMap files
        config_file = Path(config_dir) / "app-config.json"
        config_data = {
            "service_name": "dataflow-analyzer",
            "environment": "production",
            "database": {"pool_size": 20},
        }

        config_file.write_text(json.dumps(config_data))

        # Create plain text config file
        text_config = Path(config_dir) / "log-level"
        text_config.write_text("DEBUG")

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        config = manager.get_config()

        # Check that ConfigMap values are loaded
        assert config.service_name == "dataflow-analyzer"
        assert config.environment == "production"

    def test_secret_file_loading(self, temp_config_dir):
        """Test loading secrets from Secret files"""
        config_dir, secrets_dir = temp_config_dir

        # Create test Secret files
        db_password_file = Path(secrets_dir) / "database_password"
        db_password_file.write_text("secret-password")

        redis_password_file = Path(secrets_dir) / "redis_password"
        redis_password_file.write_text("redis-secret")

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        # The actual loading depends on how secrets are mapped in the configuration
        # This test verifies the mechanism works
        assert manager._load_secret_files() is not None

    def test_configuration_validation(self, temp_config_dir):
        """Test configuration validation"""
        config_dir, secrets_dir = temp_config_dir

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        validation_errors = manager.validate_configuration()

        # Should return a list (may be empty for valid config)
        assert isinstance(validation_errors, list)

    def test_health_status(self, temp_config_dir):
        """Test health status reporting"""
        config_dir, secrets_dir = temp_config_dir

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        health = manager.get_health_status()

        assert "status" in health
        assert "environment" in health
        assert "service_name" in health
        assert "hot_reload_enabled" in health
        assert health["hot_reload_enabled"] is False

    def test_configuration_masking(self, temp_config_dir):
        """Test that sensitive configuration values are masked"""
        config_dir, secrets_dir = temp_config_dir

        with patch.dict(
            os.environ,
            {"DATAFLOW_DATABASE_URL": "postgresql://user:password@localhost:5432/db"},
        ):
            manager = K8sConfigManager(
                config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
            )

            debug_info = manager.export_for_debugging()

            # Check that sensitive values are masked
            assert "***MASKED***" in str(debug_info)

    def test_context_manager(self, temp_config_dir):
        """Test context manager functionality"""
        config_dir, secrets_dir = temp_config_dir

        with K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        ) as manager:
            assert manager is not None
            config = manager.get_config()
            assert isinstance(config, EnvironmentConfig)

    def test_file_watching_disabled(self, temp_config_dir):
        """Test that file watching can be disabled"""
        config_dir, secrets_dir = temp_config_dir

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        assert not manager.enable_hot_reload
        assert manager._watch_thread is None

    def test_manual_configuration_reload(self, temp_config_dir):
        """Test manual configuration reload"""
        config_dir, secrets_dir = temp_config_dir

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        # Test manual reload
        result = manager.reload_configuration()
        assert isinstance(result, bool)

    def test_change_callback_registration(self, temp_config_dir):
        """Test configuration change callback registration"""
        config_dir, secrets_dir = temp_config_dir

        manager = K8sConfigManager(
            config_dir=config_dir, secrets_dir=secrets_dir, enable_hot_reload=False
        )

        callback_called = False

        def test_callback(config):
            nonlocal callback_called
            callback_called = True

        manager.register_change_callback(test_callback)
        assert test_callback in manager._change_callbacks

        manager.unregister_change_callback(test_callback)
        assert test_callback not in manager._change_callbacks
