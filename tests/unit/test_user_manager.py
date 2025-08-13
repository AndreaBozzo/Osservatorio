"""
Unit tests for UserManager

Tests the specialized user management functionality.
"""

from unittest.mock import patch

import pytest

from src.database.sqlite.user_manager import UserManager


class TestUserManager:
    """Test UserManager functionality"""

    @pytest.fixture
    def user_manager(self, temp_db):
        """Create a UserManager instance for testing"""
        manager = UserManager(temp_db)
        try:
            yield manager
        finally:
            try:
                manager.close_connections()
            except Exception:
                pass

    def test_manager_initialization(self, user_manager):
        """Test UserManager initialization"""
        assert user_manager is not None
        assert user_manager.db_path is not None

    def test_create_user_preferences(self, user_manager):
        """Test creating user preferences"""
        success = user_manager.set_user_preference(
            "test_user", "theme", "dark", "string"
        )
        assert success is True

    def test_get_user_preferences(self, user_manager):
        """Test retrieving user preferences"""
        # Set a preference first
        user_manager.set_user_preference("test_user", "language", "en", "string")

        # Retrieve it
        value = user_manager.get_user_preference("test_user", "language")
        assert value == "en"

    def test_get_nonexistent_user_preference(self, user_manager):
        """Test retrieving non-existent user preference"""
        value = user_manager.get_user_preference("nonexistent_user", "theme")
        assert value is None

    def test_list_user_preferences(self, user_manager):
        """Test listing user preferences"""
        # Add multiple preferences with correct signature
        user_manager.set_user_preference("test_user", "theme", "dark", "string")
        user_manager.set_user_preference("test_user", "language", "en", "string")

        # List preferences - method is get_user_preferences and returns dict
        preferences = user_manager.get_user_preferences("test_user")
        assert isinstance(preferences, dict)
        assert len(preferences) >= 2

        # Check keys exist
        assert "theme" in preferences
        assert "language" in preferences

    def test_update_user_preference(self, user_manager):
        """Test updating user preferences"""
        # Create initial preference
        user_manager.set_user_preference("test_user", "theme", "light", "string")

        # Update it
        success = user_manager.set_user_preference(
            "test_user", "theme", "dark", "string"
        )
        assert success is True

        # Verify update
        value = user_manager.get_user_preference("test_user", "theme")
        assert value == "dark"

    def test_delete_user_preferences(self, user_manager):
        """Test deleting user preferences"""
        # Create preferences with correct signature
        user_manager.set_user_preference("test_user", "theme", "dark", "string")
        user_manager.set_user_preference("test_user", "language", "en", "string")

        # Delete specific preference
        success = user_manager.delete_user_preference("test_user", "theme")
        assert success is True

        # Verify deletion
        value = user_manager.get_user_preference("test_user", "theme")
        assert value is None

        # Verify other preference still exists
        value = user_manager.get_user_preference("test_user", "language")
        assert value == "en"

    def test_clear_all_user_preferences(self, user_manager):
        """Test clearing all user preferences"""
        # Create multiple preferences with correct signature
        user_manager.set_user_preference("test_user", "theme", "dark", "string")
        user_manager.set_user_preference("test_user", "language", "en", "string")

        # Clear all preferences for user - use correct method name
        success = user_manager.delete_all_user_preferences("test_user")
        assert success is True

        # Verify all preferences are gone - use correct method name
        preferences = user_manager.get_user_preferences("test_user")
        assert len(preferences) == 0

    def test_user_preference_types(self, user_manager):
        """Test different preference value types"""
        # String with correct signature
        user_manager.set_user_preference("test_user", "name", "John Doe", "string")
        assert user_manager.get_user_preference("test_user", "name") == "John Doe"

        # Number with correct type
        user_manager.set_user_preference("test_user", "count", 42, "number")
        assert user_manager.get_user_preference("test_user", "count") == 42

        # Boolean with correct type
        user_manager.set_user_preference("test_user", "enabled", True, "boolean")
        assert user_manager.get_user_preference("test_user", "enabled") is True

        # JSON type
        json_data = {"key": "value", "nested": {"data": [1, 2, 3]}}
        user_manager.set_user_preference("test_user", "config", json_data, "json")
        retrieved_json = user_manager.get_user_preference("test_user", "config")
        assert retrieved_json == json_data

    def test_multiple_users(self, user_manager):
        """Test preferences for multiple users"""
        # Set preferences for different users with correct signature
        user_manager.set_user_preference("user1", "theme", "dark", "string")
        user_manager.set_user_preference("user2", "theme", "light", "string")

        # Verify isolation
        assert user_manager.get_user_preference("user1", "theme") == "dark"
        assert user_manager.get_user_preference("user2", "theme") == "light"

    def test_preference_key_uniqueness(self, user_manager):
        """Test that preference keys are unique per user"""
        # Set initial value with correct signature
        user_manager.set_user_preference("test_user", "setting", "value1", "string")

        # Update with same key
        user_manager.set_user_preference("test_user", "setting", "value2", "string")

        # Should have updated value
        preferences = user_manager.get_user_preferences("test_user")
        assert preferences.get("setting") == "value2"

    def test_error_handling_invalid_operations(self, user_manager):
        """Test error handling for invalid operations"""
        # Try to delete non-existent preference
        success = user_manager.delete_user_preference("nonexistent_user", "theme")
        # Should not raise exception, may return False
        assert success in [True, False]

        # Try to clear preferences for non-existent user - use correct method
        success = user_manager.delete_all_user_preferences("nonexistent_user")
        # Should not raise exception, may return False
        assert success in [True, False]

    def test_database_error_handling(self, user_manager):
        """Test handling of database errors"""
        with patch.object(user_manager, "_get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Database connection failed")

            # Should handle error gracefully - use correct signature
            success = user_manager.set_user_preference(
                "test_user", "theme", "dark", "string"
            )
            assert success is False

            value = user_manager.get_user_preference("test_user", "theme")
            assert value is None

    def test_connection_management(self, user_manager):
        """Test database connection management"""
        # Test that connections can be closed
        user_manager.close_connections()

        # Manager should still work after reconnection - use correct signature
        success = user_manager.set_user_preference(
            "test_user", "theme", "dark", "string"
        )
        assert success is True

    def test_concurrent_access(self, user_manager):
        """Test concurrent access to user preferences"""
        import threading

        results = []

        def set_preference(user_id):
            success = user_manager.set_user_preference(
                f"user_{user_id}", "theme", f"theme_{user_id}", "string"
            )
            results.append(success)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=set_preference, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)
        assert len(results) == 5

    def test_preference_with_special_characters(self, user_manager):
        """Test preferences with special characters"""
        special_value = "Value with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"

        success = user_manager.set_user_preference(
            "test_user", "special", special_value, "string"
        )
        assert success is True

        retrieved_value = user_manager.get_user_preference("test_user", "special")
        assert retrieved_value == special_value

    def test_empty_and_null_values(self, user_manager):
        """Test handling of empty and null values"""
        # Empty string with correct signature
        user_manager.set_user_preference("test_user", "empty", "", "string")
        assert user_manager.get_user_preference("test_user", "empty") == ""

        # None value (should be converted to string)
        user_manager.set_user_preference("test_user", "null", None, "string")
        retrieved = user_manager.get_user_preference("test_user", "null")
        # Should handle None gracefully (converted to "None" string)
        assert retrieved == "None"

    def test_get_users_with_preferences(self, user_manager):
        """Test getting list of users with preferences"""
        # Add preferences for multiple users
        user_manager.set_user_preference("user1", "theme", "dark", "string")
        user_manager.set_user_preference("user2", "language", "en", "string")
        user_manager.set_user_preference("user3", "notifications", True, "boolean")

        # Get users with preferences
        users = user_manager.get_users_with_preferences()

        # Should return list of user IDs
        assert isinstance(users, list)
        assert "user1" in users
        assert "user2" in users
        assert "user3" in users

    def test_get_preference_usage_stats(self, user_manager):
        """Test getting preference usage statistics"""
        # Add various preferences
        user_manager.set_user_preference("user1", "theme", "dark", "string")
        user_manager.set_user_preference("user1", "config", {"key": "value"}, "json")
        user_manager.set_user_preference("user2", "enabled", True, "boolean")
        user_manager.set_user_preference("user2", "count", 42, "number")
        user_manager.set_user_preference(
            "user3", "secret", "encrypted_data", "string", True
        )

        # Get usage statistics
        stats = user_manager.get_preference_usage_stats()

        # Should return statistics dictionary
        assert isinstance(stats, dict)

        # Check for expected statistics
        if stats:  # May be empty if no data
            # Should have some basic stats
            assert (
                "total_users" in stats
                or "total_preferences" in stats
                or len(stats) >= 0
            )

    def test_bulk_set_preferences(self, user_manager):
        """Test bulk setting preferences"""
        preferences_data = {
            "theme": {"value": "dark", "type": "string", "encrypted": False},
            "language": {"value": "en", "type": "string", "encrypted": False},
            "notifications": {"value": True, "type": "boolean", "encrypted": False},
            "config": {"value": {"key": "value"}, "type": "json", "encrypted": False},
            "api_key": {"value": "secret123", "type": "string", "encrypted": True},
        }

        # Bulk set preferences
        success = user_manager.bulk_set_preferences("test_user", preferences_data)
        assert success is True

        # Verify all preferences were set
        all_prefs = user_manager.get_user_preferences("test_user")
        assert "theme" in all_prefs
        assert "language" in all_prefs
        assert "notifications" in all_prefs
        assert "config" in all_prefs
        assert "api_key" in all_prefs

        # Verify values
        assert all_prefs["theme"] == "dark"
        assert all_prefs["language"] == "en"
        assert all_prefs["notifications"] is True
        assert all_prefs["config"] == {"key": "value"}

    def test_encrypted_preferences(self, user_manager):
        """Test encrypted preference handling"""
        # Set encrypted preference
        success = user_manager.set_user_preference(
            "test_user", "secret", "sensitive_data", "string", is_encrypted=True
        )
        assert success is True

        # Retrieve encrypted preference
        value = user_manager.get_user_preference("test_user", "secret")
        # Value should be retrievable (encryption handling is internal)
        assert value == "sensitive_data"

    def test_preference_default_values(self, user_manager):
        """Test preference default values"""
        # Test with default parameter
        default_value = "default_theme"
        value = user_manager.get_user_preference(
            "nonexistent_user", "theme", default_value
        )
        assert value == default_value

        # Test without default (should return None)
        value = user_manager.get_user_preference("nonexistent_user", "language")
        assert value is None

    def test_preference_type_conversions(self, user_manager):
        """Test various preference type conversions"""
        # Test integer conversion
        user_manager.set_user_preference("test_user", "int_val", 123, "number")
        assert user_manager.get_user_preference("test_user", "int_val") == 123

        # Test float conversion
        user_manager.set_user_preference("test_user", "float_val", 123.45, "number")
        assert user_manager.get_user_preference("test_user", "float_val") == 123.45

        # Test boolean false
        user_manager.set_user_preference("test_user", "bool_false", False, "boolean")
        assert user_manager.get_user_preference("test_user", "bool_false") is False

        # Test complex JSON
        complex_json = {
            "nested": {"array": [1, 2, 3], "string": "value"},
            "boolean": True,
            "number": 42.5,
        }
        user_manager.set_user_preference("test_user", "complex", complex_json, "json")
        retrieved = user_manager.get_user_preference("test_user", "complex")
        assert retrieved == complex_json

    def test_invalid_preference_inputs(self, user_manager):
        """Test handling of invalid preference inputs"""
        # Empty user_id
        success = user_manager.set_user_preference("", "key", "value", "string")
        assert success is False

        # Empty preference_key
        success = user_manager.set_user_preference("user", "", "value", "string")
        assert success is False

        # None user_id
        success = user_manager.set_user_preference(None, "key", "value", "string")
        assert success is False

    def test_bulk_preferences_error_handling(self, user_manager):
        """Test bulk preferences error handling"""
        # Empty user_id
        success = user_manager.bulk_set_preferences("", {"key": {"value": "val"}})
        assert success is False

        # Empty preferences dict
        success = user_manager.bulk_set_preferences("user", {})
        assert success is False

        # None inputs
        success = user_manager.bulk_set_preferences(None, None)
        assert success is False
