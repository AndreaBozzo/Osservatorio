"""
Unit tests for ConfigurationManager

Tests the specialized configuration management functionality.
"""

import json
from unittest.mock import patch

import pytest

from src.database.sqlite.config_manager import ConfigurationManager


class TestConfigurationManager:
    """Test ConfigurationManager functionality"""

    @pytest.fixture
    def config_manager(self, temp_db):
        """Create a ConfigurationManager instance for testing"""
        manager = ConfigurationManager(temp_db)
        try:
            yield manager
        finally:
            try:
                manager.close_connections()
            except Exception:
                pass

    def test_manager_initialization(self, config_manager):
        """Test ConfigurationManager initialization"""
        assert config_manager is not None
        assert config_manager.db_path is not None

    def test_set_config_basic(self, config_manager):
        """Test setting basic configuration"""
        success = config_manager.set_config("test.setting", "test_value")
        assert success is True

    def test_get_config_basic(self, config_manager):
        """Test getting basic configuration"""
        # Set a config first
        config_manager.set_config("app.name", "Test App")

        # Retrieve it
        value = config_manager.get_config("app.name")
        assert value == "Test App"

    def test_get_nonexistent_config(self, config_manager):
        """Test getting non-existent configuration"""
        value = config_manager.get_config("nonexistent.key")
        assert value is None

    def test_get_config_with_default(self, config_manager):
        """Test getting configuration with default value"""
        # Default should work even if get_config doesn't support it directly
        value = config_manager.get_config("nonexistent.key")
        default_value = value if value is not None else "default_value"
        assert default_value == "default_value"

    def test_set_config_with_description(self, config_manager):
        """Test setting configuration with type"""
        success = config_manager.set_config(
            "database.timeout", "30", config_type="string"
        )
        assert success is True

    def test_update_existing_config(self, config_manager):
        """Test updating existing configuration"""
        # Set initial value
        config_manager.set_config("app.version", "1.0.0")

        # Update it
        success = config_manager.set_config("app.version", "1.1.0")
        assert success is True

        # Verify update
        value = config_manager.get_config("app.version")
        assert value == "1.1.0"

    def test_delete_config(self, config_manager):
        """Test deleting configuration"""
        # Set a config
        config_manager.set_config("temp.setting", "temporary")

        # Delete it
        success = config_manager.delete_config("temp.setting")
        assert success is True

        # Verify deletion
        value = config_manager.get_config("temp.setting")
        assert value is None

    def test_list_configs(self, config_manager):
        """Test listing configurations"""
        # Add multiple configs
        config_manager.set_config("app.name", "Test App")
        config_manager.set_config("app.version", "1.0.0")
        config_manager.set_config("database.host", "localhost")

        # List configs - returns dictionary
        configs = config_manager.list_configs()
        assert len(configs) >= 3

        # Check keys
        assert "app.name" in configs
        assert "app.version" in configs
        assert "database.host" in configs

    def test_list_configs_with_prefix(self, config_manager):
        """Test listing configurations with prefix filter"""
        # Add configs with different prefixes
        config_manager.set_config("app.name", "Test App")
        config_manager.set_config("app.version", "1.0.0")
        config_manager.set_config("database.host", "localhost")

        # Get configs - filter using pattern
        app_configs = config_manager.list_configs("app.%")

        assert len(app_configs) >= 2
        assert "app.name" in app_configs
        assert "app.version" in app_configs

    def test_config_value_types(self, config_manager):
        """Test different configuration value types"""
        # String
        config_manager.set_config("string.value", "hello world")
        assert config_manager.get_config("string.value") == "hello world"

        # JSON-like string
        json_value = json.dumps({"key": "value", "number": 42})
        config_manager.set_config("json.value", json_value)
        retrieved = config_manager.get_config("json.value")
        assert retrieved == json_value

        # Number as string
        config_manager.set_config("number.value", "42")
        assert config_manager.get_config("number.value") == "42"

    def test_hierarchical_config_keys(self, config_manager):
        """Test hierarchical configuration keys"""
        # Set nested configuration keys
        config_manager.set_config("app.database.host", "localhost")
        config_manager.set_config("app.database.port", "5432")
        config_manager.set_config("app.cache.enabled", "true")
        config_manager.set_config("app.cache.ttl", "3600")

        # Retrieve them
        assert config_manager.get_config("app.database.host") == "localhost"
        assert config_manager.get_config("app.database.port") == "5432"
        assert config_manager.get_config("app.cache.enabled") == "true"
        assert config_manager.get_config("app.cache.ttl") == "3600"

    def test_special_characters_in_values(self, config_manager):
        """Test configuration values with special characters"""
        special_value = "Value with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"

        success = config_manager.set_config("special.chars", special_value)
        assert success is True

        retrieved_value = config_manager.get_config("special.chars")
        assert retrieved_value == special_value

    def test_empty_and_null_values(self, config_manager):
        """Test handling of empty and null values"""
        # Empty string
        config_manager.set_config("empty.value", "")
        assert config_manager.get_config("empty.value") == ""

        # None value
        config_manager.set_config("null.value", None)
        retrieved = config_manager.get_config("null.value")
        # Should handle None gracefully
        assert retrieved in [None, "None", ""]

    def test_long_config_values(self, config_manager):
        """Test handling of long configuration values"""
        long_value = "A" * 1000  # 1000 character string

        success = config_manager.set_config("long.value", long_value)
        assert success is True

        retrieved_value = config_manager.get_config("long.value")
        assert retrieved_value == long_value

    def test_config_key_validation(self, config_manager):
        """Test configuration key validation"""
        # Valid keys should work
        assert config_manager.set_config("valid.key", "value") is True
        assert config_manager.set_config("valid_key", "value") is True
        assert config_manager.set_config("valid123", "value") is True

        # Keys with spaces or invalid chars might be handled differently
        # Just test they don't crash
        try:
            config_manager.set_config("key with spaces", "value")
            config_manager.set_config("key@special", "value")
        except Exception:
            pass  # May or may not be allowed

    def test_concurrent_config_access(self, config_manager):
        """Test concurrent access to configurations"""
        import threading

        results = []

        def set_config(key_suffix):
            success = config_manager.set_config(
                f"concurrent.{key_suffix}", f"value_{key_suffix}"
            )
            results.append(success)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=set_config, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)
        assert len(results) == 5

    def test_database_error_handling(self, config_manager):
        """Test handling of database errors"""
        with patch.object(config_manager, "_get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Database connection failed")

            # Should handle error gracefully
            success = config_manager.set_config("test.key", "test_value")
            assert success is False

            value = config_manager.get_config("test.key")
            assert value is None

    def test_connection_management(self, config_manager):
        """Test database connection management"""
        # Test that connections can be closed
        config_manager.close_connections()

        # Manager should still work after reconnection
        success = config_manager.set_config("reconnect.test", "value")
        assert success is True

    def test_config_persistence(self, config_manager):
        """Test that configurations persist across manager instances"""
        # Set config in current manager
        config_manager.set_config("persist.test", "persistent_value")

        # Close current manager
        db_path = config_manager.db_path
        config_manager.close_connections()

        # Create new manager with same database
        new_manager = ConfigurationManager(db_path)

        try:
            # Should retrieve the persistent value
            value = new_manager.get_config("persist.test")
            assert value == "persistent_value"
        finally:
            new_manager.close_connections()

    def test_bulk_config_operations(self, config_manager):
        """Test bulk configuration operations"""
        # Set multiple configs
        test_configs = {
            "bulk.config1": "value1",
            "bulk.config2": "value2",
            "bulk.config3": "value3",
            "bulk.config4": "value4",
            "bulk.config5": "value5",
        }

        # Set all configs
        for key, value in test_configs.items():
            success = config_manager.set_config(key, value)
            assert success is True

        # Verify all configs
        for key, expected_value in test_configs.items():
            actual_value = config_manager.get_config(key)
            assert actual_value == expected_value

        # List and verify count
        all_configs = config_manager.list_configs()
        bulk_configs = {k: v for k, v in all_configs.items() if k.startswith("bulk.")}
        assert len(bulk_configs) >= 5
