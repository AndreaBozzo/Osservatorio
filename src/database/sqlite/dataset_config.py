"""
SQLite Dataset Configuration Manager

Manages dataset configurations stored in the SQLite metadata layer.
Replaces JSON-based configuration loading for converters.

This module provides a unified interface for:
- Loading dataset configurations from SQLite
- Caching configurations for performance
- Filtering and querying datasets
- Managing dataset metadata
"""

import json
from datetime import datetime
from typing import Any, Optional

from src.database.sqlite.schema import MetadataSchema
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatasetConfigManager:
    """Manages dataset configurations from SQLite metadata database."""

    def __init__(self, db_path: Optional[str] = None, repository=None):
        """Initialize the dataset configuration manager.

        Args:
            db_path: Path to SQLite database. If None, uses default.
            repository: UnifiedDataRepository instance for database operations.
        """
        self.schema = MetadataSchema(db_path)
        self._config_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL

        # Issue #84: Use UnifiedDataRepository instead of direct connections
        if repository:
            self.repository = repository
        else:
            from src.database.sqlite.repository import get_unified_repository

            self.repository = get_unified_repository()

        # Ensure schema exists
        if not self.schema.verify_schema():
            logger.warning("SQLite schema not found, creating...")
            self.schema.create_schema()

    def _is_cache_valid(self) -> bool:
        """Check if configuration cache is still valid.

        Returns:
            True if cache is valid, False otherwise.
        """
        if not self._cache_timestamp:
            return False

        cache_age = (datetime.now() - self._cache_timestamp).total_seconds()
        return cache_age < self._cache_ttl

    def _load_datasets_from_sqlite(self) -> list[dict[str, Any]]:
        """Load all active datasets from SQLite database.

        Returns:
            List of dataset dictionaries.
        """
        try:
            # Issue #84: Use UnifiedDataRepository with specialized managers
            # Use the list_datasets method which is available in the dataset manager
            datasets_raw = self.repository.dataset_manager.list_datasets(
                active_only=True
            )

            datasets = []
            for dataset_data in datasets_raw:
                # Convert from repository format to converter format
                metadata = {}
                if "metadata" in dataset_data and dataset_data["metadata"]:
                    try:
                        if isinstance(dataset_data["metadata"], str):
                            metadata = json.loads(dataset_data["metadata"])
                        else:
                            metadata = dataset_data["metadata"]
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(
                            f"Invalid metadata for dataset {dataset_data.get('dataset_id', 'unknown')}"
                        )

                dataset = {
                    "dataflow_id": dataset_data.get("dataset_id", ""),
                    "name": dataset_data.get("name", ""),
                    "category": dataset_data.get("category", ""),
                    "description": dataset_data.get("description", ""),
                    "agency": dataset_data.get("istat_agency", "ISTAT"),
                    "priority": dataset_data.get("priority", 5),
                    "quality": dataset_data.get("quality_score", 0.0),
                    "record_count": dataset_data.get("record_count", 0),
                    "created_at": dataset_data.get("created_at"),
                    "updated_at": dataset_data.get("updated_at"),
                    **metadata,  # Merge any additional metadata
                }
                datasets.append(dataset)

            logger.info(f"Loaded {len(datasets)} active datasets from SQLite")
            return datasets

        except Exception as e:
            logger.error(f"Failed to load datasets from SQLite: {e}")
            return []

    def get_datasets_config(self, force_refresh: bool = False) -> dict[str, Any]:
        """Get complete datasets configuration in the expected format.

        Args:
            force_refresh: If True, bypasses cache and reloads from database.

        Returns:
            Dictionary with datasets configuration in converter-compatible format.
        """
        # Use cache if valid and not forcing refresh
        if not force_refresh and self._is_cache_valid() and self._config_cache:
            logger.debug("Using cached dataset configuration")
            return self._config_cache

        # Load fresh data from SQLite
        datasets = self._load_datasets_from_sqlite()

        # Group datasets by category
        categories = {}
        for dataset in datasets:
            category = dataset["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(dataset["dataflow_id"])

        # Build configuration in expected format
        config = {
            "timestamp": datetime.now().isoformat(),
            "source": "sqlite_metadata",
            "total_datasets": len(datasets),
            "categories": categories,
            "datasets": datasets,
        }

        # Update cache
        self._config_cache = config
        self._cache_timestamp = datetime.now()

        logger.info(
            f"Generated dataset configuration: {len(datasets)} datasets, {len(categories)} categories"
        )
        return config

    def get_datasets_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get all datasets for a specific category.

        Args:
            category: Dataset category to filter by.

        Returns:
            List of dataset dictionaries for the category.
        """
        config = self.get_datasets_config()
        return [ds for ds in config["datasets"] if ds["category"] == category]

    def get_dataset_by_id(self, dataset_id: str) -> Optional[dict[str, Any]]:
        """Get a specific dataset by its ID.

        Args:
            dataset_id: Dataset ID to look up.

        Returns:
            Dataset dictionary if found, None otherwise.
        """
        config = self.get_datasets_config()
        for dataset in config["datasets"]:
            if dataset["dataflow_id"] == dataset_id:
                return dataset
        return None

    def get_high_priority_datasets(
        self, limit: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Get high priority datasets (priority >= 7).

        Args:
            limit: Maximum number of datasets to return.

        Returns:
            List of high priority dataset dictionaries.
        """
        config = self.get_datasets_config()
        high_priority = [ds for ds in config["datasets"] if ds.get("priority", 5) >= 7]

        if limit:
            high_priority = high_priority[:limit]

        return high_priority

    def refresh_cache(self) -> bool:
        """Force refresh of configuration cache.

        Returns:
            True if refresh successful, False otherwise.
        """
        try:
            self.get_datasets_config(force_refresh=True)
            logger.info("Dataset configuration cache refreshed")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh configuration cache: {e}")
            return False

    def get_categories_summary(self) -> dict[str, int]:
        """Get summary of datasets by category.

        Returns:
            Dictionary mapping category names to dataset counts.
        """
        config = self.get_datasets_config()
        return {cat: len(ds_list) for cat, ds_list in config["categories"].items()}

    def add_dataset(self, dataset_config: dict[str, Any]) -> bool:
        """Add a new dataset configuration to SQLite.

        Args:
            dataset_config: Dataset configuration dictionary.

        Returns:
            True if added successfully, False otherwise.
        """
        try:
            # Issue #84: Use UnifiedDataRepository register_dataset method
            success = self.repository.dataset_manager.register_dataset(
                dataset_id=dataset_config.get("dataflow_id"),
                name=dataset_config.get("name", ""),
                category=dataset_config.get("category", ""),
                description=dataset_config.get("description", ""),
                metadata=dataset_config,
            )

            if success:
                # Invalidate cache
                self._config_cache = {}
                self._cache_timestamp = None
                logger.info(f"Added dataset: {dataset_config.get('dataflow_id')}")
                return True
            else:
                logger.error(
                    f"Failed to register dataset: {dataset_config.get('dataflow_id')}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to add dataset: {e}")
            return False

    def update_dataset(self, dataset_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing dataset configuration.

        Args:
            dataset_id: ID of dataset to update.
            updates: Dictionary of fields to update.

        Returns:
            True if updated successfully, False otherwise.
        """
        try:
            # Issue #84: Use schema's BaseSQLiteManager connection for complex updates
            # This ensures consistent connection configuration and thread safety
            with self.schema.transaction() as conn:
                # Build dynamic update query
                update_fields = []
                update_values = []

                field_mapping = {
                    "name": "name",
                    "category": "category",
                    "description": "description",
                    "agency": "istat_agency",
                    "priority": "priority",
                    "quality": "quality_score",
                    "record_count": "record_count",
                }

                for key, value in updates.items():
                    if key in field_mapping:
                        update_fields.append(f"{field_mapping[key]} = ?")
                        update_values.append(value)

                if not update_fields:
                    logger.warning(
                        f"No valid fields to update for dataset {dataset_id}"
                    )
                    return False

                # Add updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")

                # Execute update
                update_sql = f"""
                    UPDATE dataset_registry
                    SET {", ".join(update_fields)}
                    WHERE dataset_id = ?
                """
                update_values.append(dataset_id)

                cursor = conn.execute(update_sql, update_values)
                conn.commit()

                if cursor.rowcount > 0:
                    # Invalidate cache
                    self._config_cache = {}
                    self._cache_timestamp = None

                    logger.info(f"Updated dataset: {dataset_id}")
                    return True
                else:
                    logger.warning(f"Dataset not found for update: {dataset_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to update dataset {dataset_id}: {e}")
            return False

    def deactivate_dataset(self, dataset_id: str) -> bool:
        """Deactivate a dataset (soft delete).

        Args:
            dataset_id: ID of dataset to deactivate.

        Returns:
            True if deactivated successfully, False otherwise.
        """
        try:
            # Issue #84: Use schema's BaseSQLiteManager connection for deactivation
            # This ensures consistent connection configuration and thread safety
            with self.schema.transaction() as conn:
                cursor = conn.execute(
                    "UPDATE dataset_registry SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE dataset_id = ?",
                    (dataset_id,),
                )
                conn.commit()

                if cursor.rowcount > 0:
                    # Invalidate cache
                    self._config_cache = {}
                    self._cache_timestamp = None

                    logger.info(f"Deactivated dataset: {dataset_id}")
                    return True
                else:
                    logger.warning(f"Dataset not found for deactivation: {dataset_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to deactivate dataset {dataset_id}: {e}")
            return False


# Factory function for easy instantiation
def get_dataset_config_manager(db_path: Optional[str] = None) -> DatasetConfigManager:
    """Get a dataset configuration manager instance.

    Args:
        db_path: Path to SQLite database. If None, uses default.

    Returns:
        DatasetConfigManager instance.
    """
    return DatasetConfigManager(db_path)


# Example usage and testing
if __name__ == "__main__":
    # Test the dataset configuration manager
    manager = get_dataset_config_manager()

    # Get configuration
    config = manager.get_datasets_config()
    print(f"✅ Loaded {config['total_datasets']} datasets")
    print(f"📊 Categories: {list(config['categories'].keys())}")

    # Test category filtering
    for category in config["categories"]:
        datasets = manager.get_datasets_by_category(category)
        print(f"📁 {category}: {len(datasets)} datasets")

    # Test high priority datasets
    high_priority = manager.get_high_priority_datasets(limit=5)
    print(f"⭐ High priority datasets: {len(high_priority)}")
