"""
Unit tests for DatasetManager specialized SQLite manager.

Tests dataset operations including registration, retrieval, statistics,
and categorization for the refactored SQLite metadata architecture.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.database.sqlite.dataset_manager import DatasetManager, get_dataset_manager


class TestDatasetManager:
    """Test cases for DatasetManager functionality."""

    @pytest.fixture
    def manager(self, temp_db):
        """Create DatasetManager instance with temporary database."""
        return DatasetManager(temp_db)

    @pytest.fixture
    def sample_dataset_data(self):
        """Sample dataset data for testing."""
        return {
            "dataset_id": "TEST_DATASET_001",
            "name": "Test Dataset",
            "category": "economia",
            "description": "Test dataset for unit testing",
            "metadata": {"frequency": "monthly", "unit": "euro"},
            "istat_agency": "ISTAT",
            "priority": 8,
        }

    def test_manager_initialization(self, temp_db):
        """Test DatasetManager initialization."""
        manager = DatasetManager(temp_db)

        assert manager.db_path == temp_db
        assert hasattr(manager, "execute_query")
        assert hasattr(manager, "execute_update")

    def test_manager_initialization_default_path(self):
        """Test DatasetManager initialization with default path."""
        manager = DatasetManager()

        assert manager.db_path is not None
        assert manager.db_path.endswith(".db")

    def test_register_dataset_success(self, manager, sample_dataset_data):
        """Test successful dataset registration."""
        result = manager.register_dataset(**sample_dataset_data)

        assert result is True

        # Verify dataset was registered
        dataset = manager.get_dataset(sample_dataset_data["dataset_id"])
        assert dataset is not None
        assert dataset["dataset_id"] == sample_dataset_data["dataset_id"]
        assert dataset["name"] == sample_dataset_data["name"]
        assert dataset["category"] == sample_dataset_data["category"]
        assert dataset["metadata"] == sample_dataset_data["metadata"]

    def test_register_dataset_minimal(self, manager):
        """Test dataset registration with minimal required fields."""
        result = manager.register_dataset(
            dataset_id="MINIMAL_001", name="Minimal Dataset", category="test"
        )

        assert result is True

        # Verify dataset was registered with defaults
        dataset = manager.get_dataset("MINIMAL_001")
        assert dataset is not None
        assert dataset["description"] == ""
        assert dataset["metadata"] == {}
        assert dataset["istat_agency"] == "ISTAT"
        assert dataset["priority"] == 5

    def test_register_dataset_invalid_inputs(self, manager):
        """Test dataset registration with invalid inputs."""
        # Test empty dataset_id
        result = manager.register_dataset(
            dataset_id="", name="Test Dataset", category="test"
        )
        assert result is False

        # Test None dataset_id
        result = manager.register_dataset(
            dataset_id=None, name="Test Dataset", category="test"
        )
        assert result is False

        # Test empty name
        result = manager.register_dataset(
            dataset_id="TEST_001", name="", category="test"
        )
        assert result is False

    def test_register_dataset_replace_existing(self, manager, sample_dataset_data):
        """Test replacing existing dataset (INSERT OR REPLACE)."""
        # Register initial dataset
        result1 = manager.register_dataset(**sample_dataset_data)
        assert result1 is True

        # Register same dataset with different data
        modified_data = sample_dataset_data.copy()
        modified_data["name"] = "Updated Test Dataset"
        modified_data["priority"] = 9

        result2 = manager.register_dataset(**modified_data)
        assert result2 is True

        # Verify dataset was updated
        dataset = manager.get_dataset(sample_dataset_data["dataset_id"])
        assert dataset["name"] == "Updated Test Dataset"
        assert dataset["priority"] == 9

    def test_register_dataset_database_error(self, manager, sample_dataset_data):
        """Test dataset registration with database error."""
        with patch.object(manager, "execute_update", side_effect=Exception("DB Error")):
            result = manager.register_dataset(**sample_dataset_data)
            assert result is False

    def test_get_dataset_found(self, manager, sample_dataset_data):
        """Test retrieving existing dataset."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Retrieve dataset
        dataset = manager.get_dataset(sample_dataset_data["dataset_id"])

        assert dataset is not None
        assert dataset["dataset_id"] == sample_dataset_data["dataset_id"]
        assert dataset["name"] == sample_dataset_data["name"]
        assert dataset["category"] == sample_dataset_data["category"]
        assert dataset["description"] == sample_dataset_data["description"]
        assert dataset["metadata"] == sample_dataset_data["metadata"]
        assert dataset["istat_agency"] == sample_dataset_data["istat_agency"]
        assert dataset["priority"] == sample_dataset_data["priority"]
        assert dataset["is_active"] == 1

    def test_get_dataset_not_found(self, manager):
        """Test retrieving non-existent dataset."""
        dataset = manager.get_dataset("NON_EXISTENT")
        assert dataset is None

    def test_get_dataset_invalid_metadata_json(self, manager):
        """Test retrieving dataset with invalid metadata JSON."""
        # Mock execute_query to return invalid JSON
        mock_row = {
            "dataset_id": "TEST_001",
            "name": "Test Dataset",
            "category": "test",
            "description": "",
            "metadata_json": "invalid_json{",
            "istat_agency": "ISTAT",
            "priority": 5,
            "is_active": 1,
        }

        with patch.object(manager, "execute_query", return_value=[mock_row]):
            dataset = manager.get_dataset("TEST_001")

            assert dataset is not None
            assert dataset["metadata"] == {}  # Should default to empty dict

    def test_get_dataset_no_metadata(self, manager):
        """Test retrieving dataset with no metadata."""
        # Mock execute_query to return None metadata
        mock_row = {
            "dataset_id": "TEST_001",
            "name": "Test Dataset",
            "category": "test",
            "description": "",
            "metadata_json": None,
            "istat_agency": "ISTAT",
            "priority": 5,
            "is_active": 1,
        }

        with patch.object(manager, "execute_query", return_value=[mock_row]):
            dataset = manager.get_dataset("TEST_001")

            assert dataset is not None
            assert dataset["metadata"] == {}

    def test_get_dataset_database_error(self, manager):
        """Test retrieving dataset with database error."""
        with patch.object(manager, "execute_query", side_effect=Exception("DB Error")):
            dataset = manager.get_dataset("TEST_001")
            assert dataset is None

    def test_list_datasets_all(self, manager, sample_dataset_data):
        """Test listing all datasets."""
        # Register multiple datasets
        for i in range(3):
            data = sample_dataset_data.copy()
            data["dataset_id"] = f"TEST_DATASET_{i:03d}"
            data["name"] = f"Test Dataset {i}"
            data["priority"] = 10 - i  # Different priorities for ordering test
            manager.register_dataset(**data)

        # List all datasets
        datasets = manager.list_datasets()

        assert len(datasets) == 3
        # Should be ordered by priority DESC, name ASC
        assert datasets[0]["dataset_id"] == "TEST_DATASET_000"  # Priority 10
        assert datasets[1]["dataset_id"] == "TEST_DATASET_001"  # Priority 9
        assert datasets[2]["dataset_id"] == "TEST_DATASET_002"  # Priority 8

    def test_list_datasets_by_category(self, manager, sample_dataset_data):
        """Test listing datasets filtered by category."""
        # Register datasets with different categories
        categories = ["economia", "popolazione", "lavoro"]
        for i, category in enumerate(categories):
            data = sample_dataset_data.copy()
            data["dataset_id"] = f"TEST_DATASET_{i:03d}"
            data["category"] = category
            manager.register_dataset(**data)

        # List datasets by category
        economia_datasets = manager.list_datasets(category="economia")
        popolazione_datasets = manager.list_datasets(category="popolazione")

        assert len(economia_datasets) == 1
        assert economia_datasets[0]["category"] == "economia"

        assert len(popolazione_datasets) == 1
        assert popolazione_datasets[0]["category"] == "popolazione"

    def test_list_datasets_with_pagination(self, manager, sample_dataset_data):
        """Test listing datasets with limit and offset."""
        # Register multiple datasets
        for i in range(5):
            data = sample_dataset_data.copy()
            data["dataset_id"] = f"TEST_DATASET_{i:03d}"
            data["name"] = f"Test Dataset {i}"
            manager.register_dataset(**data)

        # Test limit
        datasets = manager.list_datasets(limit=3)
        assert len(datasets) == 3

        # Test limit with offset
        datasets = manager.list_datasets(limit=2, offset=2)
        assert len(datasets) == 2

    def test_list_datasets_include_inactive(self, manager, sample_dataset_data):
        """Test listing datasets including inactive ones."""
        # Register dataset and then deactivate it
        manager.register_dataset(**sample_dataset_data)
        manager.deactivate_dataset(sample_dataset_data["dataset_id"])

        # List active only (default)
        active_datasets = manager.list_datasets(active_only=True)
        assert len(active_datasets) == 0

        # List including inactive
        all_datasets = manager.list_datasets(active_only=False)
        assert len(all_datasets) == 1
        assert all_datasets[0]["is_active"] == 0

    def test_list_datasets_database_error(self, manager):
        """Test listing datasets with database error."""
        with patch.object(manager, "execute_query", side_effect=Exception("DB Error")):
            datasets = manager.list_datasets()
            assert datasets == []

    def test_update_dataset_stats_record_count(self, manager, sample_dataset_data):
        """Test updating dataset record count."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Update record count
        result = manager.update_dataset_stats(
            dataset_id=sample_dataset_data["dataset_id"], record_count=1000
        )

        assert result is True

        # Verify update (would need to check database directly in real scenario)

    def test_update_dataset_stats_quality_score(self, manager, sample_dataset_data):
        """Test updating dataset quality score."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Update quality score
        result = manager.update_dataset_stats(
            dataset_id=sample_dataset_data["dataset_id"], quality_score=0.95
        )

        assert result is True

    def test_update_dataset_stats_last_processed(self, manager, sample_dataset_data):
        """Test updating dataset last processed time."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Update last processed time
        processed_time = datetime.now()
        result = manager.update_dataset_stats(
            dataset_id=sample_dataset_data["dataset_id"], last_processed=processed_time
        )

        assert result is True

    def test_update_dataset_stats_file_size_skipped(self, manager, sample_dataset_data):
        """Test updating dataset file size (should be skipped due to schema)."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Update file size (should be skipped)
        result = manager.update_dataset_stats(
            dataset_id=sample_dataset_data["dataset_id"], file_size=1024
        )

        assert result is False  # No other fields to update

    def test_update_dataset_stats_no_updates(self, manager, sample_dataset_data):
        """Test updating dataset stats with no actual updates."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Call update with no parameters
        result = manager.update_dataset_stats(
            dataset_id=sample_dataset_data["dataset_id"]
        )

        assert result is False

    def test_update_dataset_stats_not_found(self, manager):
        """Test updating stats for non-existent dataset."""
        result = manager.update_dataset_stats(
            dataset_id="NON_EXISTENT", record_count=1000
        )

        assert result is False

    def test_update_dataset_stats_database_error(self, manager, sample_dataset_data):
        """Test updating dataset stats with database error."""
        with patch.object(manager, "execute_update", side_effect=Exception("DB Error")):
            result = manager.update_dataset_stats(
                dataset_id=sample_dataset_data["dataset_id"], record_count=1000
            )
            assert result is False

    def test_deactivate_dataset_success(self, manager, sample_dataset_data):
        """Test successful dataset deactivation."""
        # Register dataset first
        manager.register_dataset(**sample_dataset_data)

        # Deactivate dataset
        result = manager.deactivate_dataset(sample_dataset_data["dataset_id"])

        assert result is True

        # Verify dataset is no longer in active list
        datasets = manager.list_datasets(active_only=True)
        assert len(datasets) == 0

    def test_deactivate_dataset_not_found(self, manager):
        """Test deactivating non-existent dataset."""
        result = manager.deactivate_dataset("NON_EXISTENT")
        assert result is False

    def test_deactivate_dataset_database_error(self, manager):
        """Test deactivating dataset with database error."""
        with patch.object(manager, "execute_update", side_effect=Exception("DB Error")):
            result = manager.deactivate_dataset("TEST_001")
            assert result is False

    def test_get_dataset_categories(self, manager, sample_dataset_data):
        """Test retrieving dataset categories."""
        # Register datasets with different categories
        categories = ["economia", "popolazione", "lavoro", "ambiente"]
        for i, category in enumerate(categories):
            data = sample_dataset_data.copy()
            data["dataset_id"] = f"TEST_DATASET_{i:03d}"
            data["category"] = category
            manager.register_dataset(**data)

        # Get categories
        retrieved_categories = manager.get_dataset_categories()

        assert len(retrieved_categories) == 4
        assert set(retrieved_categories) == set(categories)
        # Should be ordered alphabetically
        assert retrieved_categories == sorted(categories)

    def test_get_dataset_categories_empty(self, manager):
        """Test retrieving categories when no datasets exist."""
        categories = manager.get_dataset_categories()
        assert categories == []

    def test_get_dataset_categories_database_error(self, manager):
        """Test retrieving categories with database error."""
        with patch.object(manager, "execute_query", side_effect=Exception("DB Error")):
            categories = manager.get_dataset_categories()
            assert categories == []

    def test_get_dataset_stats_summary(self, manager, sample_dataset_data):
        """Test retrieving dataset statistics summary."""
        # Register multiple datasets
        for i in range(3):
            data = sample_dataset_data.copy()
            data["dataset_id"] = f"TEST_DATASET_{i:03d}"
            data["category"] = ["economia", "popolazione", "lavoro"][i]
            manager.register_dataset(**data)

        # Update some stats
        manager.update_dataset_stats(
            "TEST_DATASET_000", record_count=1000, quality_score=0.9
        )
        manager.update_dataset_stats(
            "TEST_DATASET_001", record_count=2000, quality_score=0.8
        )

        # Deactivate one dataset
        manager.deactivate_dataset("TEST_DATASET_002")

        # Get summary stats
        stats = manager.get_dataset_stats_summary()

        assert stats is not None
        assert "total_datasets" in stats
        assert "active_datasets" in stats
        assert "categories" in stats

    def test_get_dataset_stats_summary_empty(self, manager):
        """Test retrieving stats summary with no datasets."""
        stats = manager.get_dataset_stats_summary()

        # Should return empty dict or stats with zero values
        assert isinstance(stats, dict)

    def test_get_dataset_stats_summary_database_error(self, manager):
        """Test retrieving stats summary with database error."""
        with patch.object(manager, "execute_query", side_effect=Exception("DB Error")):
            stats = manager.get_dataset_stats_summary()
            assert stats == {}


class TestDatasetManagerFactory:
    """Test factory function for DatasetManager."""

    def test_get_dataset_manager_with_path(self, temp_db):
        """Test factory function with specific database path."""
        manager = get_dataset_manager(temp_db)

        assert isinstance(manager, DatasetManager)
        assert manager.db_path == temp_db

    def test_get_dataset_manager_default_path(self):
        """Test factory function with default database path."""
        manager = get_dataset_manager()

        assert isinstance(manager, DatasetManager)
        assert manager.db_path is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
