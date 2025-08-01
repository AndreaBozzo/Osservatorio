"""
Unit tests for SQLite metadata layer.

Tests the SQLite metadata manager, schema creation, and CRUD operations
for the hybrid SQLite + DuckDB architecture.
"""
import json
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.database.sqlite.manager import SQLiteMetadataManager
from src.database.sqlite.schema import MetadataSchema, create_metadata_schema
from tests.utils.database_cleanup import safe_database_cleanup


class TestMetadataSchema:
    """Test cases for MetadataSchema."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Robust cleanup
        safe_database_cleanup(sqlite_path=temp_path)

    def test_schema_creation(self, temp_db_path):
        """Test schema creation and verification."""
        schema = MetadataSchema(temp_db_path)

        # Create schema
        assert schema.create_schema() is True

        # Verify schema
        assert schema.verify_schema() is True

        # Check that all required tables exist
        for table_name in schema.SCHEMA_SQL.keys():
            table_info = schema.get_table_info(table_name)
            assert len(table_info) > 0, f"Table {table_name} should have columns"

    def test_schema_default_config(self, temp_db_path):
        """Test that default configuration is inserted."""
        schema = create_metadata_schema(temp_db_path)

        # Test that we can get a default config value
        import sqlite3

        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute(
                "SELECT config_value FROM system_config WHERE config_key = ?",
                ("database.sqlite.path",),
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == str(temp_db_path)

    def test_schema_drop(self, temp_db_path):
        """Test schema dropping."""
        schema = create_metadata_schema(temp_db_path)
        assert Path(temp_db_path).exists()

        # Drop schema
        drop_result = schema.drop_schema()
        assert drop_result is True

        # On Windows, file might still exist due to locking but should be empty/invalid
        # Check if file doesn't exist OR if it exists, it should be invalid/empty
        if Path(temp_db_path).exists():
            # If file still exists, verify it's been invalidated
            import sqlite3

            try:
                with sqlite3.connect(temp_db_path) as conn:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    tables = cursor.fetchall()
                    # If we can connect and have no user tables, schema was effectively dropped
                    # (sqlite_sequence and other sqlite_* tables are system tables that may remain)
                    assert (
                        len(tables) == 0
                    ), f"Database still contains user tables: {tables}"
            except sqlite3.DatabaseError:
                # If we can't connect, database was properly invalidated
                pass
        # If file doesn't exist, that's the ideal case


class TestSQLiteMetadataManager:
    """Test cases for SQLiteMetadataManager."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Robust cleanup
        safe_database_cleanup(sqlite_path=temp_path)

    @pytest.fixture
    def manager(self, temp_db_path):
        """Create SQLite metadata manager."""
        manager = SQLiteMetadataManager(temp_db_path)
        yield manager
        manager.close_connections()

    # Dataset Registry Tests

    def test_dataset_registration(self, manager):
        """Test dataset registration."""
        # Register a dataset
        success = manager.register_dataset(
            "DCIS_POPRES1",
            "Popolazione residente",
            "popolazione",
            "Dati popolazione italiana",
            "ISTAT",
            10,
            {"frequency": "annual", "unit": "persons"},
        )

        assert success is True

        # Verify registration
        dataset = manager.get_dataset("DCIS_POPRES1")
        assert dataset is not None
        assert dataset["name"] == "Popolazione residente"
        assert dataset["category"] == "popolazione"
        assert dataset["priority"] == 10
        assert dataset["metadata"]["frequency"] == "annual"

    def test_dataset_not_found(self, manager):
        """Test getting non-existent dataset."""
        dataset = manager.get_dataset("NONEXISTENT")
        assert dataset is None

    def test_list_datasets(self, manager):
        """Test listing datasets with filtering."""
        # Register multiple datasets
        datasets_to_register = [
            ("POP_1", "Population 1", "popolazione", None, "ISTAT", 8),
            ("ECO_1", "Economy 1", "economia", None, "ISTAT", 7),
            ("POP_2", "Population 2", "popolazione", None, "ISTAT", 9),
        ]

        for dataset_id, name, category, desc, agency, priority in datasets_to_register:
            manager.register_dataset(dataset_id, name, category, desc, agency, priority)

        # Test listing all datasets
        all_datasets = manager.list_datasets()
        assert len(all_datasets) == 3

        # Test category filtering
        pop_datasets = manager.list_datasets(category="popolazione")
        assert len(pop_datasets) == 2
        assert all(d["category"] == "popolazione" for d in pop_datasets)

        # Test priority ordering (highest first)
        assert pop_datasets[0]["priority"] == 9  # POP_2
        assert pop_datasets[1]["priority"] == 8  # POP_1

    def test_update_dataset_stats(self, manager):
        """Test updating dataset statistics."""
        # Register dataset first
        manager.register_dataset("TEST_STATS", "Test Stats", "test")

        # Update stats
        success = manager.update_dataset_stats(
            "TEST_STATS", quality_score=0.95, record_count=1000
        )
        assert success is True

        # Verify update
        dataset = manager.get_dataset("TEST_STATS")
        assert dataset["quality_score"] == 0.95
        assert dataset["record_count"] == 1000

    # User Preferences Tests

    def test_user_preferences_string(self, manager):
        """Test string user preferences."""
        # Set preference
        success = manager.set_user_preference("user1", "theme", "dark")
        assert success is True

        # Get preference
        theme = manager.get_user_preference("user1", "theme")
        assert theme == "dark"

        # Test default value
        language = manager.get_user_preference("user1", "language", "en")
        assert language == "en"

    def test_user_preferences_json(self, manager):
        """Test JSON user preferences."""
        # Set JSON preference
        config = {"notifications": True, "refresh_rate": 300}
        success = manager.set_user_preference(
            "user1", "dashboard_config", config, "json"
        )
        assert success is True

        # Get JSON preference
        retrieved_config = manager.get_user_preference("user1", "dashboard_config")
        assert retrieved_config == config
        assert retrieved_config["notifications"] is True
        assert retrieved_config["refresh_rate"] == 300

    def test_user_preferences_boolean(self, manager):
        """Test boolean user preferences."""
        # Set boolean preference
        success = manager.set_user_preference(
            "user1", "notifications_enabled", True, "boolean"
        )
        assert success is True

        # Get boolean preference
        enabled = manager.get_user_preference("user1", "notifications_enabled")
        assert enabled is True

        # Set false
        manager.set_user_preference("user1", "notifications_enabled", False, "boolean")
        enabled = manager.get_user_preference("user1", "notifications_enabled")
        assert enabled is False

    def test_user_preferences_encrypted(self, manager):
        """Test encrypted user preferences."""
        # Set encrypted preference
        secret_value = "my_secret_api_key"
        success = manager.set_user_preference(
            "user1", "api_key", secret_value, encrypt=True
        )
        assert success is True

        # Get encrypted preference (should be decrypted automatically)
        retrieved_value = manager.get_user_preference("user1", "api_key")
        assert retrieved_value == secret_value

    def test_get_all_user_preferences(self, manager):
        """Test getting all user preferences."""
        # Set multiple preferences
        manager.set_user_preference("user1", "theme", "dark")
        manager.set_user_preference("user1", "language", "it")
        manager.set_user_preference("user1", "auto_refresh", True, "boolean")

        # Get all preferences
        preferences = manager.get_user_preferences("user1")
        assert len(preferences) == 3
        assert preferences["theme"] == "dark"
        assert preferences["language"] == "it"
        assert preferences["auto_refresh"] is True

    # API Credentials Tests

    def test_api_credentials_storage(self, manager):
        """Test API credentials storage and verification."""
        # Store credentials
        success = manager.store_api_credentials(
            "istat_api",
            "test_api_key_123",
            "test_secret_456",
            "https://api.istat.it",
            50,
            datetime.now() + timedelta(days=30),
        )
        assert success is True

        # Verify credentials
        is_valid = manager.verify_api_credentials("istat_api", "test_api_key_123")
        assert is_valid is True

        # Verify wrong credentials
        is_valid = manager.verify_api_credentials("istat_api", "wrong_key")
        assert is_valid is False

        # Verify non-existent service
        is_valid = manager.verify_api_credentials("nonexistent", "any_key")
        assert is_valid is False

    def test_api_credentials_expiration(self, manager):
        """Test API credentials expiration."""
        # Store expired credentials
        past_date = datetime.now() - timedelta(days=1)
        manager.store_api_credentials("expired_api", "key123", expires_at=past_date)

        # Should fail verification due to expiration
        is_valid = manager.verify_api_credentials("expired_api", "key123")
        assert is_valid is False

    # System Configuration Tests

    def test_system_configuration(self, manager):
        """Test system configuration operations."""
        # Set configuration
        success = manager.set_config(
            "test.setting",
            "test_value",
            "string",
            "Test configuration setting",
            False,
            "development",
        )
        assert success is True

        # Get configuration
        value = manager.get_config("test.setting", environment="development")
        assert value == "test_value"

        # Test default value
        default_value = manager.get_config("nonexistent.setting", "default_val")
        assert default_value == "default_val"

    # Audit Logging Tests

    def test_audit_logging(self, manager):
        """Test audit logging functionality."""
        # Log an audit event
        success = manager.log_audit(
            "user1",
            "dataset_view",
            "dataset",
            "DCIS_POPRES1",
            {"action_details": "viewed population data"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert success is True

        # Get audit logs
        logs = manager.get_audit_logs(user_id="user1", limit=10)
        assert len(logs) >= 1

        log_entry = logs[0]
        assert log_entry["user_id"] == "user1"
        assert log_entry["action"] == "dataset_view"
        assert log_entry["resource_type"] == "dataset"
        assert log_entry["resource_id"] == "DCIS_POPRES1"
        assert log_entry["ip_address"] == "192.168.1.1"
        assert log_entry["success"] is True

    def test_audit_logging_with_filters(self, manager):
        """Test audit logging with various filters."""
        # Log multiple events
        events = [
            ("user1", "login", "user", "user1"),
            ("user1", "dataset_view", "dataset", "DATASET_1"),
            ("user2", "login", "user", "user2"),
            ("user1", "dataset_export", "dataset", "DATASET_1"),
        ]

        for user_id, action, resource_type, resource_id in events:
            manager.log_audit(user_id, action, resource_type, resource_id)

        # Test user filter
        user1_logs = manager.get_audit_logs(user_id="user1")
        assert len(user1_logs) >= 3
        assert all(log["user_id"] == "user1" for log in user1_logs)

        # Test action filter
        login_logs = manager.get_audit_logs(action="login")
        assert len(login_logs) >= 2
        assert all(log["action"] == "login" for log in login_logs)

        # Test resource type filter
        dataset_logs = manager.get_audit_logs(resource_type="dataset")
        assert len(dataset_logs) >= 2
        assert all(log["resource_type"] == "dataset" for log in dataset_logs)

    # Database Statistics Tests

    def test_database_statistics(self, manager):
        """Test database statistics retrieval."""
        # Add some data
        manager.register_dataset("STATS_TEST", "Statistics Test", "test")
        manager.set_user_preference("stats_user", "theme", "light")
        manager.log_audit("stats_user", "test_action", "test_resource")

        # Get statistics
        stats = manager.get_database_stats()

        # Verify statistics structure
        assert "dataset_registry_count" in stats
        assert "user_preferences_count" in stats
        assert "audit_log_count" in stats
        assert "database_size_bytes" in stats
        assert "schema_version" in stats

        # Verify counts are reasonable
        assert stats["dataset_registry_count"] >= 1
        assert stats["user_preferences_count"] >= 1
        assert stats["audit_log_count"] >= 1
        assert stats["database_size_bytes"] > 0

    # Thread Safety Tests

    def test_thread_safety(self, manager):
        """Test thread safety of metadata manager."""
        results = []
        errors = []

        def worker_thread(thread_id):
            try:
                # Each thread performs multiple operations
                for i in range(10):
                    dataset_id = f"THREAD_{thread_id}_DATASET_{i}"
                    success = manager.register_dataset(
                        dataset_id, f"Thread {thread_id} Dataset {i}", "test"
                    )
                    results.append((thread_id, i, success))

                    # Also test preferences
                    manager.set_user_preference(
                        f"user_{thread_id}", f"pref_{i}", f"value_{i}"
                    )

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create and start multiple threads
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 50  # 5 threads * 10 operations each
        assert all(success for _, _, success in results), "Some operations failed"

        # Verify all datasets were created
        all_datasets = manager.list_datasets()
        thread_datasets = [
            d for d in all_datasets if d["dataset_id"].startswith("THREAD_")
        ]
        assert len(thread_datasets) == 50

    # Transaction Tests

    def test_transaction_success(self, manager):
        """Test successful transaction."""
        with manager.transaction() as conn:
            # Perform multiple operations
            conn.execute(
                "INSERT INTO dataset_registry (dataset_id, name, category) VALUES (?, ?, ?)",
                ("TRANS_TEST1", "Transaction Test 1", "test"),
            )
            conn.execute(
                "INSERT INTO dataset_registry (dataset_id, name, category) VALUES (?, ?, ?)",
                ("TRANS_TEST2", "Transaction Test 2", "test"),
            )

        # Verify both datasets exist
        dataset1 = manager.get_dataset("TRANS_TEST1")
        dataset2 = manager.get_dataset("TRANS_TEST2")
        assert dataset1 is not None
        assert dataset2 is not None

    def test_transaction_rollback(self, manager):
        """Test transaction rollback on error."""
        try:
            with manager.transaction() as conn:
                # First operation succeeds
                conn.execute(
                    "INSERT INTO dataset_registry (dataset_id, name, category) VALUES (?, ?, ?)",
                    ("ROLLBACK_TEST1", "Rollback Test 1", "test"),
                )

                # Second operation fails (duplicate key)
                conn.execute(
                    "INSERT INTO dataset_registry (dataset_id, name, category) VALUES (?, ?, ?)",
                    ("ROLLBACK_TEST1", "Rollback Test Duplicate", "test"),
                )
        except Exception:
            # Expected to fail
            pass

        # Verify first dataset was rolled back
        dataset = manager.get_dataset("ROLLBACK_TEST1")
        assert dataset is None


# Integration tests
class TestSQLiteIntegration:
    """Integration tests for SQLite metadata layer."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Robust cleanup
        safe_database_cleanup(sqlite_path=temp_path)

    def test_complete_workflow(self, temp_db_path):
        """Test complete metadata workflow."""
        # Initialize manager
        manager = SQLiteMetadataManager(temp_db_path)

        try:
            # 1. Register datasets
            datasets = [
                ("DCIS_POPRES1", "Population", "popolazione", 10),
                ("DCCN_PILN", "Economy", "economia", 9),
                ("DCCV_TAXOCCU", "Employment", "lavoro", 8),
            ]

            for dataset_id, name, category, priority in datasets:
                success = manager.register_dataset(
                    dataset_id, name, category, priority=priority
                )
                assert success is True

            # 2. Set user preferences
            manager.set_user_preference("analyst1", "favorite_category", "popolazione")
            manager.set_user_preference("analyst1", "dashboard_refresh", 300, "integer")
            manager.set_user_preference("analyst1", "notifications", True, "boolean")

            # 3. Store API credentials
            manager.store_api_credentials("istat", "api_key_123", "secret_456")

            # 4. Set system configuration
            manager.set_config("api.rate_limit", "100", "integer")
            manager.set_config("cache.ttl", "1800", "integer")

            # 5. Log some audit events
            manager.log_audit("analyst1", "login", "user", "analyst1")
            manager.log_audit("analyst1", "dataset_view", "dataset", "DCIS_POPRES1")
            manager.log_audit("analyst1", "export_data", "dataset", "DCIS_POPRES1")

            # 6. Verify everything works
            # Check datasets
            all_datasets = manager.list_datasets()
            assert len(all_datasets) == 3

            pop_datasets = manager.list_datasets(category="popolazione")
            assert len(pop_datasets) == 1
            assert pop_datasets[0]["name"] == "Population"

            # Check preferences
            preferences = manager.get_user_preferences("analyst1")
            assert preferences["favorite_category"] == "popolazione"
            assert preferences["dashboard_refresh"] == 300
            assert preferences["notifications"] is True

            # Check credentials
            is_valid = manager.verify_api_credentials("istat", "api_key_123")
            assert is_valid is True

            # Check configuration
            rate_limit = manager.get_config("api.rate_limit")
            assert rate_limit == "100"

            # Check audit logs
            logs = manager.get_audit_logs(user_id="analyst1")
            assert len(logs) >= 3

            # Check statistics
            stats = manager.get_database_stats()
            assert stats["dataset_registry_count"] == 3
            assert stats["user_preferences_count"] == 3
            assert stats["audit_log_count"] >= 3

        finally:
            manager.close_connections()


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
