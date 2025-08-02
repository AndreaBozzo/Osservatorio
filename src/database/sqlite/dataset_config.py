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
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database.sqlite.schema import MetadataSchema
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatasetConfigManager:
    """Manages dataset configurations from SQLite metadata database."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the dataset configuration manager.

        Args:
            db_path: Path to SQLite database. If None, uses default.
        """
        self.schema = MetadataSchema(db_path)
        self._config_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL

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

    def _load_datasets_from_sqlite(self) -> List[Dict[str, Any]]:
        """Load all active datasets from SQLite database.

        Returns:
            List of dataset dictionaries.
        """
        try:
            conn = sqlite3.connect(self.schema.db_path)
            try:
                cursor = conn.execute(
                    """
                    SELECT dataset_id, name, category, description, istat_agency,
                           priority, metadata_json, quality_score, record_count,
                           created_at, updated_at
                    FROM dataset_registry
                    WHERE is_active = 1
                    ORDER BY priority DESC, name ASC
                """
                )

                datasets = []
                for row in cursor.fetchall():
                    # Parse metadata JSON if available
                    metadata = {}
                    if row[6]:  # metadata_json column
                        try:
                            metadata = json.loads(row[6])
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Invalid metadata JSON for dataset {row[0]}"
                            )

                    dataset = {
                        "dataflow_id": row[0],
                        "name": row[1],
                        "category": row[2],
                        "description": row[3],
                        "agency": row[4],
                        "priority": row[5],
                        "quality": row[7],
                        "record_count": row[8],
                        "created_at": row[9],
                        "updated_at": row[10],
                        **metadata,  # Merge any additional metadata
                    }
                    datasets.append(dataset)

                logger.info(f"Loaded {len(datasets)} active datasets from SQLite")
                return datasets

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to load datasets from SQLite: {e}")
            return []

    def get_datasets_config(self, force_refresh: bool = False) -> Dict[str, Any]:
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

    def get_datasets_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all datasets for a specific category.

        Args:
            category: Dataset category to filter by.

        Returns:
            List of dataset dictionaries for the category.
        """
        config = self.get_datasets_config()
        return [ds for ds in config["datasets"] if ds["category"] == category]

    def get_dataset_by_id(self, dataset_id: str) -> Optional[Dict[str, Any]]:
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
    ) -> List[Dict[str, Any]]:
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

    def get_categories_summary(self) -> Dict[str, int]:
        """Get summary of datasets by category.

        Returns:
            Dictionary mapping category names to dataset counts.
        """
        config = self.get_datasets_config()
        return {cat: len(ds_list) for cat, ds_list in config["categories"].items()}

    def add_dataset(self, dataset_config: Dict[str, Any]) -> bool:
        """Add a new dataset configuration to SQLite.

        Args:
            dataset_config: Dataset configuration dictionary.

        Returns:
            True if added successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.schema.db_path)
            try:
                # Prepare dataset data
                insert_sql = """
                    INSERT INTO dataset_registry
                    (dataset_id, name, category, description, istat_agency,
                     priority, is_active, metadata_json, quality_score, record_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                conn.execute(
                    insert_sql,
                    (
                        dataset_config.get("dataflow_id"),
                        dataset_config.get("name", ""),
                        dataset_config.get("category", ""),
                        dataset_config.get("description", ""),
                        dataset_config.get("agency", "ISTAT"),
                        dataset_config.get("priority", 5),
                        True,  # is_active
                        json.dumps(dataset_config, ensure_ascii=False),
                        dataset_config.get("quality", 0.0),
                        dataset_config.get("record_count", 0),
                    ),
                )

                conn.commit()

                # Invalidate cache
                self._config_cache = {}
                self._cache_timestamp = None

                logger.info(f"Added dataset: {dataset_config.get('dataflow_id')}")
                return True

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Failed to add dataset: {e}")
            return False

    def update_dataset(self, dataset_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing dataset configuration.

        Args:
            dataset_id: ID of dataset to update.
            updates: Dictionary of fields to update.

        Returns:
            True if updated successfully, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.schema.db_path)
            try:
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
                    SET {', '.join(update_fields)}
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

            finally:
                conn.close()

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
            conn = sqlite3.connect(self.schema.db_path)
            try:
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

            finally:
                conn.close()

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
