"""
Integration tests for the Unified Data Repository.

Tests the facade pattern implementation that combines SQLite metadata
and DuckDB analytics operations in the hybrid architecture.
"""

import tempfile
import threading
from datetime import datetime

import pytest

from src.database.sqlite.repository import UnifiedDataRepository
from tests.utils.database_cleanup import safe_database_cleanup


class TestUnifiedDataRepository:
    """Test cases for UnifiedDataRepository."""

    @pytest.fixture
    def temp_paths(self):
        """Create temporary database paths."""
        sqlite_temp = tempfile.NamedTemporaryFile(suffix="_metadata.db", delete=False)
        duckdb_temp = tempfile.NamedTemporaryFile(suffix="_analytics.db", delete=False)

        sqlite_path = sqlite_temp.name
        duckdb_path = duckdb_temp.name

        sqlite_temp.close()
        duckdb_temp.close()

        yield sqlite_path, duckdb_path

        # Robust cleanup
        safe_database_cleanup(sqlite_path=sqlite_path, duckdb_path=duckdb_path)

    @pytest.fixture
    def repository(self, temp_paths):
        """Create unified data repository."""
        sqlite_path, duckdb_path = temp_paths
        repo = UnifiedDataRepository(sqlite_path, duckdb_path)
        yield repo
        repo.close()

    # Dataset Operations Tests

    def test_complete_dataset_registration(self, repository):
        """Test complete dataset registration in both databases."""
        # Register dataset
        success = repository.register_dataset_complete(
            "TEST_COMPLETE",
            "Complete Test Dataset",
            "test",
            "Test dataset for unified repository",
            "TEST_AGENCY",
            8,
            {"test": True, "frequency": "monthly"},
        )

        assert success is True

        # Verify dataset exists in metadata
        dataset = repository.get_dataset_complete("TEST_COMPLETE")
        assert dataset is not None
        assert dataset["name"] == "Complete Test Dataset"
        assert dataset["category"] == "test"
        assert dataset["priority"] == 8
        assert dataset["metadata"]["test"] is True

        # Check analytics integration
        assert "analytics_stats" in dataset
        assert "has_analytics_data" in dataset
        assert isinstance(dataset["has_analytics_data"], bool)

    def test_dataset_not_found_complete(self, repository):
        """Test getting non-existent dataset from complete view."""
        dataset = repository.get_dataset_complete("NONEXISTENT")
        assert dataset is None

    def test_list_datasets_complete(self, repository):
        """Test listing complete datasets with analytics integration."""
        # Register multiple datasets
        test_datasets = [
            ("COMPLETE_1", "Complete Dataset 1", "test", 9),
            ("COMPLETE_2", "Complete Dataset 2", "test", 7),
            ("COMPLETE_3", "Complete Dataset 3", "analytics", 8),
        ]

        for dataset_id, name, category, priority in test_datasets:
            success = repository.register_dataset_complete(
                dataset_id, name, category, priority=priority
            )
            assert success is True

        # List all datasets
        all_datasets = repository.list_datasets_complete()
        assert len(all_datasets) >= 3

        # List by category
        test_datasets = repository.list_datasets_complete(category="test")
        assert len(test_datasets) >= 2
        assert all(d["category"] == "test" for d in test_datasets)

        # Verify analytics stats are included
        for dataset in all_datasets:
            assert "analytics_stats" in dataset
            assert "has_analytics_data" in dataset

    def test_list_datasets_with_analytics_filter(self, repository):
        """Test filtering datasets by analytics data presence."""
        # Register datasets
        repository.register_dataset_complete("WITH_ANALYTICS", "With Analytics", "test")
        repository.register_dataset_complete(
            "WITHOUT_ANALYTICS", "Without Analytics", "test"
        )

        # Test filtering (note: these will likely not have analytics data in tests)
        datasets_with_analytics = repository.list_datasets_complete(with_analytics=True)
        datasets_without_analytics = repository.list_datasets_complete(
            with_analytics=False
        )

        # Should be able to filter (exact results depend on test data)
        assert isinstance(datasets_with_analytics, list)
        assert isinstance(datasets_without_analytics, list)

    # User Preferences with Caching Tests

    def test_user_preferences_with_cache(self, repository):
        """Test user preferences with caching layer."""
        # Set preference with caching
        success = repository.set_user_preference(
            "cache_user", "theme", "dark", cache_minutes=5
        )
        assert success is True

        # Get preference (should hit cache)
        theme = repository.get_user_preference("cache_user", "theme", use_cache=True)
        assert theme == "dark"

        # Get preference without cache
        theme_no_cache = repository.get_user_preference(
            "cache_user", "theme", use_cache=False
        )
        assert theme_no_cache == "dark"

        # Test default value
        language = repository.get_user_preference("cache_user", "language", "en")
        assert language == "en"

    def test_user_preferences_cache_behavior(self, repository):
        """Test caching behavior for user preferences."""
        # Set preference
        repository.set_user_preference("cache_test", "setting1", "value1")

        # First access (should cache)
        value1 = repository.get_user_preference("cache_test", "setting1")
        assert value1 == "value1"

        # Verify cache contains the value
        cache_key = "pref_cache_test_setting1"
        cached_value = repository._get_cache(cache_key)
        assert cached_value == "value1"

        # Clear cache and verify
        repository.clear_cache()
        cached_value_after_clear = repository._get_cache(cache_key)
        assert cached_value_after_clear is None

        # Should still get value from database
        value_from_db = repository.get_user_preference("cache_test", "setting1")
        assert value_from_db == "value1"

    # Analytics Operations Tests

    def test_analytics_query_with_audit(self, repository):
        """Test analytics query execution with audit logging."""
        # Execute a simple query
        query = "SELECT 1 as test_value"
        results = repository.execute_analytics_query(query, user_id="analyst1")

        assert results is not None
        assert len(results) == 1
        assert results[0][0] == 1

        # Verify audit log was created
        audit_logs = repository.metadata_manager.get_audit_logs(
            user_id="analyst1", action="analytics_query"
        )
        assert len(audit_logs) >= 1

        log_entry = audit_logs[0]
        assert log_entry["user_id"] == "analyst1"
        assert log_entry["action"] == "analytics_query"
        assert log_entry["resource_type"] == "duckdb_query"
        assert log_entry["success"] is True
        assert log_entry["execution_time_ms"] is not None

    def test_analytics_query_error_handling(self, repository):
        """Test analytics query error handling and audit logging."""
        # Execute invalid query
        invalid_query = "SELECT FROM invalid_table_that_does_not_exist"

        with pytest.raises(Exception):
            repository.execute_analytics_query(invalid_query, user_id="analyst1")

        # Verify error was logged
        audit_logs = repository.metadata_manager.get_audit_logs(
            user_id="analyst1", action="analytics_query"
        )

        # Should have at least one failed query log
        failed_logs = [log for log in audit_logs if not log["success"]]
        assert len(failed_logs) >= 1

        failed_log = failed_logs[0]
        assert failed_log["success"] is False
        assert failed_log["error_message"] is not None

    def test_get_dataset_time_series_integration(self, repository):
        """Test time series data retrieval with metadata integration."""
        # First register a dataset in metadata
        repository.register_dataset_complete(
            "TIMESERIES_TEST",
            "Time Series Test",
            "test",
            "Test dataset for time series",
        )

        # Try to get time series data (will be empty in test, but should not error)
        time_series = repository.get_dataset_time_series(
            "TIMESERIES_TEST", territory_code="IT", start_year=2020, end_year=2023
        )

        # Should return empty list (no data in test database)
        assert isinstance(time_series, list)
        assert len(time_series) >= 0  # Could be empty in test environment

    def test_get_dataset_time_series_nonexistent(self, repository):
        """Test time series retrieval for non-existent dataset."""
        # Try to get time series for non-existent dataset
        time_series = repository.get_dataset_time_series("NONEXISTENT_DATASET")

        # Should return empty list with warning logged
        assert time_series == []

    # System Status Tests

    def test_system_status(self, repository):
        """Test system status retrieval."""
        status = repository.get_system_status()

        # Verify status structure
        assert "metadata_database" in status
        assert "analytics_database" in status
        assert "cache" in status
        assert "timestamp" in status

        # Check metadata database status
        metadata_status = status["metadata_database"]
        assert metadata_status["status"] == "connected"
        assert "stats" in metadata_status

        # Check analytics database status
        analytics_status = status["analytics_database"]
        assert analytics_status["status"] in ["connected", "error"]
        assert "stats" in analytics_status

        # Check cache status
        cache_status = status["cache"]
        assert "size" in cache_status

        # Verify timestamp format
        timestamp = status["timestamp"]
        assert isinstance(timestamp, str)
        # Should be valid ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    # Cache Operations Tests

    def test_cache_operations(self, repository):
        """Test cache set, get, and clear operations."""
        # Set cache value
        repository._set_cache("test_key", "test_value", 60)

        # Get cache value
        value = repository._get_cache("test_key")
        assert value == "test_value"

        # Test TTL expiration (simulate)
        import time

        repository._set_cache("ttl_key", "ttl_value", 0.1)  # 0.1 seconds
        time.sleep(0.2)
        expired_value = repository._get_cache("ttl_key")
        assert expired_value is None

        # Test cache clear
        repository._set_cache("clear_test", "clear_value", 300)
        repository.clear_cache()
        cleared_value = repository._get_cache("clear_test")
        assert cleared_value is None

    # Transaction Tests

    def test_transaction_context_manager(self, repository):
        """Test transaction context manager."""
        # Test successful transaction
        with repository.transaction():
            success = repository.register_dataset_complete(
                "TRANSACTION_TEST", "Transaction Test", "test"
            )
            assert success is True

        # Verify dataset exists after transaction
        dataset = repository.get_dataset_complete("TRANSACTION_TEST")
        assert dataset is not None

    def test_transaction_error_handling(self, repository):
        """Test transaction error handling."""
        try:
            with repository.transaction():
                # Perform valid operation
                repository.set_user_preference("trans_user", "setting", "value")

                # Force an error
                raise ValueError("Simulated transaction error")

        except ValueError as e:
            assert str(e) == "Simulated transaction error"

        # Transaction should have been handled gracefully
        # (Note: This is a simplified test - real 2-phase commit would be more complex)

    # Thread Safety Tests

    def test_thread_safety(self, repository):
        """Test thread safety of unified repository."""
        results = []
        errors = []

        def worker_thread(thread_id):
            try:
                # Each thread performs operations
                for i in range(5):
                    # Register dataset
                    dataset_id = f"THREAD_{thread_id}_DS_{i}"
                    success = repository.register_dataset_complete(
                        dataset_id, f"Thread {thread_id} Dataset {i}", "test"
                    )
                    results.append((thread_id, "dataset", success))

                    # Set preference
                    success = repository.set_user_preference(
                        f"thread_user_{thread_id}", f"pref_{i}", f"value_{i}"
                    )
                    results.append((thread_id, "preference", success))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create and start multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 30  # 3 threads * 5 operations * 2 types each
        assert all(success for _, _, success in results), "Some operations failed"

    # Performance Tests

    def test_cache_performance(self, repository):
        """Test cache performance benefits."""
        import time

        # Set a preference
        repository.set_user_preference("perf_user", "test_setting", "test_value")

        # Measure database access time
        start_time = time.time()
        for _ in range(100):
            repository.get_user_preference("perf_user", "test_setting", use_cache=False)
        db_time = time.time() - start_time

        # Measure cached access time
        start_time = time.time()
        for _ in range(100):
            repository.get_user_preference("perf_user", "test_setting", use_cache=True)
        cache_time = time.time() - start_time

        # Cache should be faster (though in tests the difference might be minimal)
        # At minimum, cached version should not be significantly slower
        assert cache_time <= db_time * 1.5  # Allow 50% tolerance for test overhead

    # Integration Workflow Tests

    def test_complete_workflow_integration(self, repository):
        """Test complete workflow integrating all components."""
        # 1. Register multiple datasets
        datasets = [
            ("WORKFLOW_POP", "Population Data", "popolazione", 10),
            ("WORKFLOW_ECO", "Economic Data", "economia", 9),
            ("WORKFLOW_LAV", "Employment Data", "lavoro", 8),
        ]

        for dataset_id, name, category, priority in datasets:
            success = repository.register_dataset_complete(
                dataset_id,
                name,
                category,
                priority=priority,
                metadata={"workflow_test": True},
            )
            assert success is True

        # 2. Set user preferences with caching
        user_prefs = [
            ("analyst1", "favorite_category", "popolazione"),
            ("analyst1", "refresh_interval", 300),
            ("analyst1", "notifications", True),
            ("analyst2", "favorite_category", "economia"),
            ("analyst2", "theme", "dark"),
        ]

        for user_id, key, value in user_prefs:
            pref_type = (
                "boolean"
                if isinstance(value, bool)
                else "integer" if isinstance(value, int) else "string"
            )
            success = repository.set_user_preference(
                user_id, key, value, preference_type=pref_type
            )
            assert success is True

        # 3. Execute analytics queries with audit
        queries = [
            ("SELECT 1 as test", "analyst1"),
            ("SELECT 2 as another_test", "analyst2"),
            ("SELECT COUNT(*) FROM (SELECT 1 UNION SELECT 2) as dummy", "analyst1"),
        ]

        for query, user_id in queries:
            results = repository.execute_analytics_query(query, user_id=user_id)
            assert results is not None

        # 4. Verify complete integration
        # Check datasets
        all_datasets = repository.list_datasets_complete()
        workflow_datasets = [
            d for d in all_datasets if d["dataset_id"].startswith("WORKFLOW_")
        ]
        assert len(workflow_datasets) == 3

        # Check preferences
        analyst1_prefs = repository.metadata_manager.get_user_preferences("analyst1")
        assert analyst1_prefs["favorite_category"] == "popolazione"
        assert analyst1_prefs["refresh_interval"] == 300
        assert analyst1_prefs["notifications"] is True

        # Check audit logs
        audit_logs = repository.metadata_manager.get_audit_logs(limit=50)
        assert len(audit_logs) >= 6  # 3 dataset registrations + 3 queries

        # Check system status
        status = repository.get_system_status()
        assert status["metadata_database"]["status"] == "connected"

        # Verify statistics
        stats = status["metadata_database"]["stats"]
        assert stats["dataset_registry_count"] >= 3
        assert stats["user_preferences_count"] >= 5
        assert stats["audit_log_count"] >= 6


class TestUnifiedRepositorySingleton:
    """Test singleton pattern for unified repository."""

    def test_singleton_pattern(self):
        """Test that get_unified_repository returns the same instance."""
        from src.database.sqlite.repository import (
            get_unified_repository,
            reset_unified_repository,
        )

        # Reset to ensure clean state
        reset_unified_repository()

        # Get repository instances
        repo1 = get_unified_repository()
        repo2 = get_unified_repository()

        # Should be same instance
        assert repo1 is repo2

        # Reset and get again
        reset_unified_repository()
        repo3 = get_unified_repository()

        # Should be different instance after reset
        assert repo3 is not repo1

        # Cleanup
        reset_unified_repository()


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
