"""
Dataset Manager - Specialized SQLite manager for dataset operations

Handles dataset registration, retrieval, statistics, and categorization
as part of the refactored SQLite metadata architecture.
"""

import json
from datetime import datetime
from typing import Any, Optional

from src.utils.logger import get_logger

from .base_manager import BaseSQLiteManager

logger = get_logger(__name__)


class DatasetManager(BaseSQLiteManager):
    """Specialized manager for dataset-related database operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize dataset manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        super().__init__(db_path)
        logger.info(f"Dataset manager initialized: {self.db_path}")

    def register_dataset(
        self,
        dataset_id: str,
        name: str,
        category: str,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
        istat_agency: str = "ISTAT",
        priority: int = 5,
    ) -> bool:
        """Register a new dataset in the metadata registry.

        Args:
            dataset_id: Unique dataset identifier
            name: Human-readable dataset name
            category: Dataset category (e.g., 'economia', 'popolazione')
            description: Dataset description
            metadata: Additional metadata as JSON
            istat_agency: Source agency (default: ISTAT)
            priority: Dataset priority (1-10, higher = more important)

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate inputs
            if not dataset_id or not name:
                logger.error("Dataset ID and name are required")
                return False

            # Prepare metadata
            metadata_json = json.dumps(metadata) if metadata else None

            # Insert dataset
            query = """
                INSERT OR REPLACE INTO dataset_registry (
                    dataset_id, name, category, description, metadata_json,
                    istat_agency, priority, last_updated, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
            """

            affected_rows = self.execute_update(
                query,
                (
                    dataset_id,
                    name,
                    category,
                    description,
                    metadata_json,
                    istat_agency,
                    priority,
                ),
            )

            if affected_rows > 0:
                logger.info(f"Dataset registered successfully: {dataset_id}")
                return True
            else:
                logger.warning(f"Dataset registration had no effect: {dataset_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to register dataset {dataset_id}: {e}")
            return False

    def get_dataset(self, dataset_id: str) -> Optional[dict[str, Any]]:
        """Retrieve dataset information by ID.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dataset dictionary if found, None otherwise
        """
        try:
            query = """
                SELECT * FROM dataset_registry
                WHERE dataset_id = ? AND is_active = 1
            """

            results = self.execute_query(query, (dataset_id,))

            if results:
                row = results[0]
                dataset = dict(row)

                # Parse metadata JSON
                if dataset.get("metadata_json"):
                    try:
                        dataset["metadata"] = json.loads(dataset["metadata_json"])
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid metadata JSON for dataset {dataset_id}"
                        )
                        dataset["metadata"] = {}
                    # Remove the raw JSON field
                    del dataset["metadata_json"]
                else:
                    dataset["metadata"] = {}

                logger.debug(f"Dataset retrieved: {dataset_id}")
                return dataset
            else:
                logger.debug(f"Dataset not found: {dataset_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve dataset {dataset_id}: {e}")
            return None

    def list_datasets(
        self,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List datasets with optional filtering.

        Args:
            category: Filter by category (optional)
            active_only: Only return active datasets
            limit: Maximum number of results
            offset: Results offset for pagination

        Returns:
            List of dataset dictionaries
        """
        try:
            # Build query
            query_parts = ["SELECT * FROM dataset_registry WHERE 1=1"]
            params = []

            if category:
                query_parts.append("AND category = ?")
                params.append(category)

            if active_only:
                query_parts.append("AND is_active = 1")

            query_parts.append("ORDER BY priority DESC, name ASC")

            if limit:
                query_parts.append(f"LIMIT {limit}")
                if offset > 0:
                    query_parts.append(f"OFFSET {offset}")

            query = " ".join(query_parts)
            results = self.execute_query(query, tuple(params))

            # Process results
            datasets = []
            for row in results:
                dataset = dict(row)

                # Parse metadata JSON
                if dataset.get("metadata_json"):
                    try:
                        dataset["metadata"] = json.loads(dataset["metadata_json"])
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid metadata JSON for dataset {dataset['dataset_id']}"
                        )
                        dataset["metadata"] = {}
                    # Remove the raw JSON field
                    del dataset["metadata_json"]
                else:
                    dataset["metadata"] = {}

                datasets.append(dataset)

            logger.debug(
                f"Listed {len(datasets)} datasets (category={category}, active_only={active_only})"
            )
            return datasets

        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []

    def update_dataset_stats(
        self,
        dataset_id: str,
        record_count: Optional[int] = None,
        file_size: Optional[int] = None,
        quality_score: Optional[float] = None,
        last_processed: Optional[datetime] = None,
    ) -> bool:
        """Update dataset processing statistics.

        Args:
            dataset_id: Dataset identifier
            record_count: Number of records processed
            file_size: File size in bytes
            quality_score: Data quality score (0.0-1.0)
            last_processed: Last processing timestamp

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Build dynamic update query
            update_fields = []
            params = []

            if record_count is not None:
                update_fields.append("record_count = ?")
                params.append(record_count)

            if file_size is not None:
                update_fields.append("file_size = ?")
                params.append(file_size)

            if quality_score is not None:
                update_fields.append("quality_score = ?")
                params.append(quality_score)

            if last_processed is not None:
                update_fields.append("last_processed = ?")
                params.append(last_processed)

            if not update_fields:
                logger.warning(f"No stats to update for dataset {dataset_id}")
                return False

            # Always update the updated_at timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(dataset_id)

            query = f"""
                UPDATE dataset_registry
                SET {", ".join(update_fields)}
                WHERE dataset_id = ?
            """

            affected_rows = self.execute_update(query, tuple(params))

            if affected_rows > 0:
                logger.info(f"Dataset stats updated: {dataset_id}")
                return True
            else:
                logger.warning(f"Dataset not found for stats update: {dataset_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to update dataset stats {dataset_id}: {e}")
            return False

    def deactivate_dataset(self, dataset_id: str) -> bool:
        """Deactivate a dataset (soft delete).

        Args:
            dataset_id: Dataset identifier

        Returns:
            True if deactivation successful, False otherwise
        """
        try:
            query = """
                UPDATE dataset_registry
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE dataset_id = ?
            """

            affected_rows = self.execute_update(query, (dataset_id,))

            if affected_rows > 0:
                logger.info(f"Dataset deactivated: {dataset_id}")
                return True
            else:
                logger.warning(f"Dataset not found for deactivation: {dataset_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to deactivate dataset {dataset_id}: {e}")
            return False

    def get_dataset_categories(self) -> list[str]:
        """Get list of all dataset categories.

        Returns:
            List of unique category names
        """
        try:
            query = """
                SELECT DISTINCT category
                FROM dataset_registry
                WHERE is_active = 1 AND category IS NOT NULL
                ORDER BY category
            """

            results = self.execute_query(query)
            categories = [row["category"] for row in results if row["category"]]

            logger.debug(f"Retrieved {len(categories)} dataset categories")
            return categories

        except Exception as e:
            logger.error(f"Failed to get dataset categories: {e}")
            return []

    def get_dataset_stats_summary(self) -> dict[str, Any]:
        """Get summary statistics for all datasets.

        Returns:
            Dictionary with dataset statistics
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_datasets,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_datasets,
                    COUNT(DISTINCT category) as categories,
                    SUM(record_count) as total_records,
                    AVG(quality_score) as avg_quality_score,
                    MAX(last_processed) as last_processing
                FROM dataset_registry
            """

            results = self.execute_query(query)

            if results:
                stats = dict(results[0])
                logger.debug("Dataset summary statistics retrieved")
                return stats
            else:
                return {}

        except Exception as e:
            logger.error(f"Failed to get dataset summary stats: {e}")
            return {}


# Factory function for easy instantiation
def get_dataset_manager(db_path: Optional[str] = None) -> DatasetManager:
    """Get a dataset manager instance.

    Args:
        db_path: Path to SQLite database. If None, uses default.

    Returns:
        DatasetManager instance
    """
    return DatasetManager(db_path)
