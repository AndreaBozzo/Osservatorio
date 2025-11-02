"""
Extended unit tests for UnifiedDataRepository - focusing on uncovered methods.

These tests target specific methods and error conditions to increase coverage
beyond the integration tests.

NOTE: These tests are currently skipped because they reference get_metadata_manager
which was removed during Phase 1 refactoring. These tests need to be rewritten
to use the new specialized managers architecture.

TODO: Rewrite these tests to use DatasetManager, UserManager, ConfigurationManager,
      AuditManager instead of the deprecated monolithic metadata manager.
"""

import threading
import time
from unittest.mock import Mock, patch

import pytest

from src.database.sqlite.repository import (
    UnifiedDataRepository,
    get_unified_repository,
    reset_unified_repository,
)


@pytest.mark.skip(reason="Tests reference removed get_metadata_manager - need refactoring to use specialized managers")
class TestUnifiedDataRepositoryExtended:
    """Extended test cases for UnifiedDataRepository uncovered methods."""

    @pytest.fixture
    def mock_repository(self, temp_db):
        """Create repository with mocked managers for isolated testing."""
        with (
            patch("src.database.sqlite.repository.get_dataset_manager") as mock_dataset,
            patch(
                "src.database.sqlite.repository.get_configuration_manager"
            ) as mock_config,
            patch("src.database.sqlite.repository.get_user_manager") as mock_user,
            patch("src.database.sqlite.repository.get_audit_manager") as mock_audit,
            patch(
                "src.database.sqlite.repository.get_metadata_manager"
            ) as mock_metadata,
            patch("src.database.sqlite.repository.get_manager") as mock_get_manager,
        ):
            # Setup mock managers
            mock_dataset.return_value = Mock()
            mock_config.return_value = Mock()
            mock_user.return_value = Mock()
            mock_audit.return_value = Mock()
            mock_metadata.return_value = Mock()
            mock_get_manager.return_value = Mock()

            repo = UnifiedDataRepository(temp_db, ":memory:")
            yield repo
            repo.close()

    def test_get_dataset_analytics_stats_success(self, mock_repository):
        """Test _get_dataset_analytics_stats with successful query."""
        # Setup mock analytics manager
        mock_result = [
            (
                1000,
                2020,
                2024,
                5,
                3,
            )  # record_count, min_year, max_year, territory_count, measure_count
        ]
        mock_repository.analytics_manager.execute_query.return_value = mock_result

        # Call the private method through public interface
        stats = mock_repository._get_dataset_analytics_stats("TEST_DATASET")

        expected_stats = {
            "record_count": 1000,
            "min_year": 2020,
            "max_year": 2024,
            "territory_count": 5,
            "measure_count": 3,
        }

        assert stats == expected_stats
        mock_repository.analytics_manager.execute_query.assert_called_once()

    def test_get_dataset_analytics_stats_empty_result(self, mock_repository):
        """Test _get_dataset_analytics_stats with empty result."""
        # Setup mock analytics manager with empty result
        mock_repository.analytics_manager.execute_query.return_value = []

        stats = mock_repository._get_dataset_analytics_stats("TEST_DATASET")

        assert stats == {"record_count": 0}

    def test_get_dataset_analytics_stats_none_values(self, mock_repository):
        """Test _get_dataset_analytics_stats with None values."""
        # Setup mock analytics manager with None values
        mock_result = [(None, None, None, 0, 0)]
        mock_repository.analytics_manager.execute_query.return_value = mock_result

        stats = mock_repository._get_dataset_analytics_stats("TEST_DATASET")

        expected_stats = {
            "record_count": 0,
            "min_year": 2020,  # Default value
            "max_year": 2024,  # Default value
            "territory_count": 0,
            "measure_count": 0,
        }

        assert stats == expected_stats

    def test_get_dataset_analytics_stats_error(self, mock_repository):
        """Test _get_dataset_analytics_stats with database error."""
        # Setup mock analytics manager to raise exception
        mock_repository.analytics_manager.execute_query.side_effect = Exception(
            "Database error"
        )

        stats = mock_repository._get_dataset_analytics_stats("TEST_DATASET")

        assert stats == {"record_count": 0}

    def test_register_dataset_complete_metadata_failure(self, mock_repository):
        """Test register_dataset_complete with metadata registration failure."""
        # Setup mocks
        mock_repository.dataset_manager.register_dataset.return_value = False

        result = mock_repository.register_dataset_complete(
            "TEST_DATASET", "Test Dataset", "test"
        )

        assert result is False
        mock_repository.dataset_manager.register_dataset.assert_called_once()
        # Analytics manager should not be called if metadata fails
        mock_repository.analytics_manager.ensure_schema_exists.assert_not_called()

    def test_register_dataset_complete_analytics_failure(self, mock_repository):
        """Test register_dataset_complete with analytics schema failure."""
        # Setup mocks
        mock_repository.dataset_manager.register_dataset.return_value = True
        mock_repository.analytics_manager.ensure_schema_exists.return_value = False

        result = mock_repository.register_dataset_complete(
            "TEST_DATASET", "Test Dataset", "test"
        )

        assert result is False
        mock_repository.dataset_manager.register_dataset.assert_called_once()
        mock_repository.analytics_manager.ensure_schema_exists.assert_called_once()

    def test_register_dataset_complete_exception(self, mock_repository):
        """Test register_dataset_complete with exception during registration."""
        # Setup mock to raise exception
        mock_repository.dataset_manager.register_dataset.side_effect = Exception(
            "Database error"
        )

        result = mock_repository.register_dataset_complete(
            "TEST_DATASET", "Test Dataset", "test"
        )

        assert result is False

    def test_get_dataset_complete_not_found(self, mock_repository):
        """Test get_dataset_complete with non-existent dataset."""
        # Setup mock to return None
        mock_repository.dataset_manager.get_dataset.return_value = None

        result = mock_repository.get_dataset_complete("NONEXISTENT")

        assert result is None
        mock_repository.dataset_manager.get_dataset.assert_called_once_with(
            "NONEXISTENT"
        )

    def test_get_dataset_complete_exception(self, mock_repository):
        """Test get_dataset_complete with exception."""
        # Setup mock to raise exception
        mock_repository.dataset_manager.get_dataset.side_effect = Exception(
            "Database error"
        )

        result = mock_repository.get_dataset_complete("TEST_DATASET")

        assert result is None

    def test_list_datasets_complete_with_analytics_filter_true(self, mock_repository):
        """Test list_datasets_complete with analytics filter true."""
        # Setup mock datasets
        mock_datasets = [
            {"dataset_id": "DATASET_1", "name": "Dataset 1"},
            {"dataset_id": "DATASET_2", "name": "Dataset 2"},
        ]
        mock_repository.dataset_manager.list_datasets.return_value = mock_datasets

        # Setup analytics stats - one with data, one without
        def mock_analytics_stats(dataset_id):
            if dataset_id == "DATASET_1":
                return {"record_count": 1000}
            else:
                return {"record_count": 0}

        mock_repository._get_dataset_analytics_stats = Mock(
            side_effect=mock_analytics_stats
        )

        # Filter for datasets with analytics data
        result = mock_repository.list_datasets_complete(with_analytics=True)

        assert len(result) == 1
        assert result[0]["dataset_id"] == "DATASET_1"
        assert result[0]["has_analytics_data"] is True

    def test_list_datasets_complete_with_analytics_filter_false(self, mock_repository):
        """Test list_datasets_complete with analytics filter false."""
        # Setup mock datasets
        mock_datasets = [
            {"dataset_id": "DATASET_1", "name": "Dataset 1"},
            {"dataset_id": "DATASET_2", "name": "Dataset 2"},
        ]
        mock_repository.dataset_manager.list_datasets.return_value = mock_datasets

        # Setup analytics stats - one with data, one without
        def mock_analytics_stats(dataset_id):
            if dataset_id == "DATASET_1":
                return {"record_count": 1000}
            else:
                return {"record_count": 0}

        mock_repository._get_dataset_analytics_stats = Mock(
            side_effect=mock_analytics_stats
        )

        # Filter for datasets without analytics data
        result = mock_repository.list_datasets_complete(with_analytics=False)

        assert len(result) == 1
        assert result[0]["dataset_id"] == "DATASET_2"
        assert result[0]["has_analytics_data"] is False

    def test_list_datasets_complete_exception(self, mock_repository):
        """Test list_datasets_complete with exception."""
        # Setup mock to raise exception
        mock_repository.dataset_manager.list_datasets.side_effect = Exception(
            "Database error"
        )

        result = mock_repository.list_datasets_complete()

        assert result == []

    def test_set_user_preference_with_caching(self, mock_repository):
        """Test set_user_preference with successful caching."""
        # Setup mock
        mock_repository.user_manager.set_user_preference.return_value = True

        result = mock_repository.set_user_preference(
            "user123", "theme", "dark", cache_minutes=60
        )

        assert result is True
        mock_repository.user_manager.set_user_preference.assert_called_once_with(
            "user123", "theme", "dark"
        )

    def test_set_user_preference_failure(self, mock_repository):
        """Test set_user_preference with database failure."""
        # Setup mock to return False
        mock_repository.user_manager.set_user_preference.return_value = False

        result = mock_repository.set_user_preference("user123", "theme", "dark")

        assert result is False

    def test_set_user_preference_exception(self, mock_repository):
        """Test set_user_preference with exception."""
        # Setup mock to raise exception
        mock_repository.user_manager.set_user_preference.side_effect = Exception(
            "Database error"
        )

        result = mock_repository.set_user_preference("user123", "theme", "dark")

        assert result is False

    def test_get_user_preference_with_cache_hit(self, mock_repository):
        """Test get_user_preference with cache hit."""
        # Setup cache
        mock_repository._set_cache("pref_user123_theme", "dark", 60)

        result = mock_repository.get_user_preference("user123", "theme", use_cache=True)

        assert result == "dark"
        # Database should not be called
        mock_repository.user_manager.get_user_preference.assert_not_called()

    def test_get_user_preference_cache_miss(self, mock_repository):
        """Test get_user_preference with cache miss."""
        # Setup mock to return value from database
        mock_repository.user_manager.get_user_preference.return_value = "light"

        result = mock_repository.get_user_preference(
            "user123", "theme", default="dark", use_cache=True
        )

        assert result == "light"
        mock_repository.user_manager.get_user_preference.assert_called_once_with(
            "user123", "theme", "dark"
        )

    def test_get_user_preference_no_cache(self, mock_repository):
        """Test get_user_preference without using cache."""
        # Setup mock to return value from database
        mock_repository.user_manager.get_user_preference.return_value = "light"

        result = mock_repository.get_user_preference(
            "user123", "theme", use_cache=False
        )

        assert result == "light"
        mock_repository.user_manager.get_user_preference.assert_called_once()

    def test_get_user_preference_exception(self, mock_repository):
        """Test get_user_preference with exception."""
        # Setup mock to raise exception
        mock_repository.user_manager.get_user_preference.side_effect = Exception(
            "Database error"
        )

        result = mock_repository.get_user_preference("user123", "theme", default="dark")

        assert result == "dark"

    def test_execute_analytics_query_with_dataframe(self, mock_repository):
        """Test execute_analytics_query with pandas DataFrame result."""
        # Setup mock DataFrame
        mock_df = Mock()
        mock_df.values.tolist.return_value = [[1, "test"], [2, "data"]]
        mock_repository.analytics_manager.execute_query.return_value = mock_df

        result = mock_repository.execute_analytics_query(
            "SELECT * FROM test", ["param1"], user_id="user123"
        )

        expected = [(1, "test"), (2, "data")]
        assert result == expected

        # Verify audit logging
        mock_repository.audit_manager.log_action.assert_called_once()
        call_args = mock_repository.audit_manager.log_action.call_args
        assert call_args[1]["action"] == "analytics_query"
        assert call_args[1]["success"] is True

    def test_execute_analytics_query_with_tuples(self, mock_repository):
        """Test execute_analytics_query with tuple result."""
        # Setup mock to return tuples directly
        mock_result = [(1, "test"), (2, "data")]
        mock_repository.analytics_manager.execute_query.return_value = mock_result

        result = mock_repository.execute_analytics_query("SELECT * FROM test")

        assert result == mock_result

    def test_execute_analytics_query_exception(self, mock_repository):
        """Test execute_analytics_query with exception."""
        # Setup mock to raise exception
        mock_repository.analytics_manager.execute_query.side_effect = Exception(
            "Query error"
        )

        with pytest.raises(Exception):
            mock_repository.execute_analytics_query(
                "SELECT * FROM test", user_id="user123"
            )

        # Verify error audit logging
        mock_repository.audit_manager.log_action.assert_called_once()
        call_args = mock_repository.audit_manager.log_action.call_args
        assert call_args[1]["success"] is False
        assert "error" in call_args[1]["details"]

    def test_get_dataset_time_series_dataset_not_found(self, mock_repository):
        """Test get_dataset_time_series with non-existent dataset."""
        # Setup mock to return None
        mock_repository.dataset_manager.get_dataset.return_value = None

        result = mock_repository.get_dataset_time_series("NONEXISTENT")

        assert result == []

    def test_cache_operations(self, mock_repository):
        """Test internal cache operations."""
        # Test setting and getting cache
        mock_repository._set_cache("test_key", "test_value", 60)

        # Test getting cached value
        result = mock_repository._get_cache("test_key")
        assert result == "test_value"

        # Test getting non-existent key
        result = mock_repository._get_cache("non_existent")
        assert result is None

    def test_cache_expiration(self, mock_repository):
        """Test cache expiration."""
        # Set cache with very short TTL
        mock_repository._set_cache("test_key", "test_value", 0.1)  # 0.1 seconds

        # Should get value immediately
        result = mock_repository._get_cache("test_key")
        assert result == "test_value"

        # Wait for expiration
        time.sleep(0.2)

        # Should return None after expiration
        result = mock_repository._get_cache("test_key")
        assert result is None

    def test_threading_lock(self, mock_repository):
        """Test thread safety with RLock."""
        results = []

        def thread_operation():
            with mock_repository._lock:
                # Simulate some work
                time.sleep(0.1)
                results.append(threading.current_thread().name)

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=thread_operation, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All threads should have completed
        assert len(results) == 3

    def test_close_method(self, mock_repository):
        """Test repository close method."""
        # Setup mocks with close methods
        mock_repository.dataset_manager.close_connections = Mock()
        mock_repository.config_manager.close_connections = Mock()
        mock_repository.user_manager.close_connections = Mock()
        mock_repository.audit_manager.close_connections = Mock()
        mock_repository.metadata_manager.close_connections = Mock()

        # Call close
        mock_repository.close()

        # Verify all managers are closed (analytics_manager.close is not called in actual implementation)
        mock_repository.dataset_manager.close_connections.assert_called_once()
        mock_repository.config_manager.close_connections.assert_called_once()
        mock_repository.user_manager.close_connections.assert_called_once()
        mock_repository.audit_manager.close_connections.assert_called_once()
        mock_repository.metadata_manager.close_connections.assert_called_once()

    def test_close_method_with_exceptions(self, mock_repository):
        """Test repository close method with exceptions."""
        # Setup mocks to raise exceptions
        mock_repository.dataset_manager.close_connections = Mock(
            side_effect=Exception("Close error")
        )
        mock_repository.config_manager.close_connections = Mock()
        mock_repository.user_manager.close_connections = Mock()
        mock_repository.audit_manager.close_connections = Mock()
        mock_repository.metadata_manager.close_connections = Mock()

        # Close should not raise exception even if individual closes fail
        mock_repository.close()

        # First manager was called and raised exception
        mock_repository.dataset_manager.close_connections.assert_called_once()

        # Due to the exception handling in the actual implementation,
        # subsequent calls may not be made if the exception occurs early
        # This test verifies that the method handles exceptions gracefully


class TestRepositoryFactoryFunctions:
    """Test factory functions and singleton behavior."""

    def test_get_unified_repository_default(self):
        """Test get_unified_repository with default parameters."""
        # Reset any existing singletons
        reset_unified_repository()

        repo = get_unified_repository()

        assert isinstance(repo, UnifiedDataRepository)
        assert repo.dataset_manager is not None
        assert repo.analytics_manager is not None

    def test_get_unified_repository_with_params(self, temp_db):
        """Test get_unified_repository with specific parameters."""
        # Reset any existing singletons
        reset_unified_repository()

        repo = get_unified_repository(temp_db, ":memory:")

        assert isinstance(repo, UnifiedDataRepository)
        assert repo.dataset_manager.db_path == temp_db

    def test_get_unified_repository_singleton(self, temp_db):
        """Test singleton behavior of get_unified_repository."""
        # Reset any existing singletons
        reset_unified_repository()

        repo1 = get_unified_repository(temp_db, ":memory:")
        repo2 = get_unified_repository(temp_db, ":memory:")

        # Should return the same instance
        assert repo1 is repo2

    def test_reset_unified_repository(self, temp_db):
        """Test reset_unified_repository function."""
        # Create initial repository
        repo1 = get_unified_repository(temp_db, ":memory:")

        # Reset and create new repository
        reset_unified_repository()
        repo2 = get_unified_repository(temp_db, ":memory:")

        # Should be different instances
        assert repo1 is not repo2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
