"""
Unified Data Repository for Osservatorio ISTAT Data Platform

Implements the Facade pattern to provide a unified interface for both
SQLite metadata operations and DuckDB analytics operations as defined
in the hybrid architecture (ADR-002).

Architecture:
- SQLite: Dataset registry, user preferences, API credentials, audit logging
- DuckDB: ISTAT data analytics, time series, aggregations, performance data
- Repository: Unified facade combining both databases

Features:
- Single interface for both databases
- Intelligent routing of operations
- Transaction coordination across databases
- Caching layer for performance
- Error handling and resilience
"""

import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

from src.database.duckdb import DuckDBManager
from src.utils.logger import get_logger

from .manager_factory import (
    get_audit_manager,
    get_configuration_manager,
    get_dataset_manager,
    get_user_manager,
)

logger = get_logger(__name__)


class UnifiedDataRepository:
    """
    Unified repository providing a single interface for SQLite metadata
    and DuckDB analytics operations.
    """

    def __init__(
        self, sqlite_db_path: Optional[str] = None, duckdb_db_path: Optional[str] = None
    ):
        """Initialize the unified repository.

        Args:
            sqlite_db_path: Path to SQLite metadata database
            duckdb_db_path: Path to DuckDB analytics database
        """
        self._lock = threading.RLock()

        # Initialize database managers
        self.dataset_manager = get_dataset_manager(sqlite_db_path)
        self.config_manager = get_configuration_manager(sqlite_db_path)
        self.user_manager = get_user_manager(sqlite_db_path)
        self.audit_manager = get_audit_manager(sqlite_db_path)
        self.analytics_manager = DuckDBManager(duckdb_db_path)

        # Cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = {}

        logger.info("Unified data repository initialized")

    # Dataset Operations (Combined SQLite + DuckDB)

    def register_dataset_complete(
        self,
        dataset_id: str,
        name: str,
        category: str,
        description: str = None,
        istat_agency: str = None,
        priority: int = 5,
        metadata: dict[str, Any] = None,
    ) -> bool:
        """Register a dataset in both metadata registry and analytics engine.

        Args:
            dataset_id: Unique ISTAT dataset identifier
            name: Human-readable dataset name
            category: Dataset category
            description: Optional dataset description
            istat_agency: ISTAT agency responsible
            priority: Dataset priority (1-10)
            metadata: Additional metadata

        Returns:
            bool: True if dataset registered in both databases
        """
        try:
            with self._lock:
                # Register in SQLite metadata
                metadata_success = self.dataset_manager.register_dataset(
                    dataset_id,
                    name,
                    category,
                    description,
                    metadata,
                    istat_agency,
                    priority,
                )

                if not metadata_success:
                    logger.error(f"Failed to register dataset {dataset_id} in metadata")
                    return False

                # Ensure analytics schema exists
                analytics_success = self.analytics_manager.ensure_schema_exists()

                if not analytics_success:
                    logger.error(
                        f"Failed to ensure analytics schema for dataset {dataset_id}"
                    )
                    return False

                # Log the complete registration
                self.audit_manager.log_action(
                    action="CREATE",
                    resource_type="dataset",
                    user_id="system",
                    resource_id=dataset_id,
                    details={
                        "name": name,
                        "category": category,
                        "registered_in": "both",
                    },
                    success=True,
                )

                logger.info(
                    f"Dataset {dataset_id} registered completely in both databases"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to register dataset {dataset_id} completely: {e}")
            return False

    def get_dataset_complete(self, dataset_id: str) -> Optional[dict[str, Any]]:
        """Get complete dataset information from both databases.

        Args:
            dataset_id: ISTAT dataset identifier

        Returns:
            Dictionary with complete dataset information
        """
        try:
            # Get metadata from SQLite
            metadata = self.dataset_manager.get_dataset(dataset_id)
            if not metadata:
                return None

            # Get analytics stats from DuckDB
            analytics_stats = self._get_dataset_analytics_stats(dataset_id)

            # Combine information
            complete_dataset = metadata.copy()
            complete_dataset.update(
                {
                    "analytics_stats": analytics_stats,
                    "has_analytics_data": analytics_stats.get("record_count", 0) > 0,
                }
            )

            return complete_dataset

        except Exception as e:
            logger.error(f"Failed to get complete dataset info for {dataset_id}: {e}")
            return None

    def _get_dataset_analytics_stats(self, dataset_id: str) -> dict[str, Any]:
        """Get analytics statistics for a dataset from DuckDB.

        Args:
            dataset_id: ISTAT dataset identifier

        Returns:
            Dictionary with analytics statistics
        """
        try:
            # Query DuckDB for dataset statistics
            stats_query = """
                SELECT
                    COUNT(*) as record_count,
                    MIN(o.year) as min_year,
                    MAX(o.year) as max_year,
                    COUNT(DISTINCT o.territory_code) as territory_count,
                    COUNT(DISTINCT o.value_type) as measure_count
                FROM istat.istat_observations o
                JOIN istat.istat_datasets d ON o.dataset_row_id = d.id
                WHERE d.dataset_id = ?
            """

            result = self.analytics_manager.execute_query(stats_query, [dataset_id])

            if (
                result is not None
                and not (hasattr(result, "empty") and result.empty)
                and len(result) > 0
            ):
                row = result[0]
                return {
                    "record_count": row[0] or 0,
                    "min_year": row[1] if row[1] is not None else 2020,
                    "max_year": row[2] if row[2] is not None else 2024,
                    "territory_count": row[3] or 0,
                    "measure_count": row[4] or 0,
                }

            return {"record_count": 0}

        except Exception as e:
            logger.error(f"Failed to get analytics stats for {dataset_id}: {e}")
            return {"record_count": 0}

    def list_datasets_complete(
        self, category: str = None, with_analytics: bool = None
    ) -> list[dict[str, Any]]:
        """List datasets with complete information from both databases.

        Args:
            category: Optional category filter
            with_analytics: Filter by presence of analytics data

        Returns:
            List of complete dataset dictionaries
        """
        try:
            # Get datasets from metadata
            datasets = self.dataset_manager.list_datasets(category)

            # Enhance with analytics information
            complete_datasets = []
            for dataset in datasets:
                dataset_id = dataset["dataset_id"]
                analytics_stats = self._get_dataset_analytics_stats(dataset_id)

                complete_dataset = dataset.copy()
                complete_dataset.update(
                    {
                        "analytics_stats": analytics_stats,
                        "has_analytics_data": analytics_stats.get("record_count", 0)
                        > 0,
                    }
                )

                # Apply analytics filter if specified
                if with_analytics is not None:
                    if with_analytics and not complete_dataset["has_analytics_data"]:
                        continue
                    if not with_analytics and complete_dataset["has_analytics_data"]:
                        continue

                complete_datasets.append(complete_dataset)

            return complete_datasets

        except Exception as e:
            logger.error(f"Failed to list complete datasets: {e}")
            return []

    # User Operations (SQLite + Caching)

    def set_user_preference(
        self, user_id: str, key: str, value: Any, cache_minutes: int = 30, **kwargs
    ) -> bool:
        """Set user preference with caching.

        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
            cache_minutes: Cache TTL in minutes
            **kwargs: Additional preference parameters

        Returns:
            bool: True if preference set successfully
        """
        try:
            success = self.user_manager.set_user_preference(
                user_id, key, value, **kwargs
            )

            if success:
                # Update cache
                cache_key = f"pref_{user_id}_{key}"
                self._set_cache(cache_key, value, cache_minutes * 60)

                logger.debug(f"User preference cached: {user_id}.{key}")

            return success

        except Exception as e:
            logger.error(f"Failed to set user preference {user_id}.{key}: {e}")
            return False

    def get_user_preference(
        self, user_id: str, key: str, default: Any = None, use_cache: bool = True
    ) -> Any:
        """Get user preference with caching.

        Args:
            user_id: User identifier
            key: Preference key
            default: Default value
            use_cache: Whether to use cache

        Returns:
            Preference value or default
        """
        try:
            cache_key = f"pref_{user_id}_{key}"

            # Try cache first
            if use_cache:
                cached_value = self._get_cache(cache_key)
                if cached_value is not None:
                    return cached_value

            # Get from database
            value = self.user_manager.get_user_preference(user_id, key, default)

            # Cache the result
            if use_cache and value is not None:
                self._set_cache(cache_key, value, 1800)  # 30 minutes

            return value

        except Exception as e:
            logger.error(f"Failed to get user preference {user_id}.{key}: {e}")
            return default

    # Analytics Operations (DuckDB with Metadata Integration)

    def execute_analytics_query(
        self,
        query: str,
        params: list[Any] = None,
        user_id: str = None,
        cache_minutes: int = 10,
    ) -> list[tuple]:
        """Execute analytics query with audit logging.

        Args:
            query: SQL query for DuckDB
            params: Query parameters
            user_id: User executing the query (for audit)
            cache_minutes: Cache TTL in minutes

        Returns:
            Query results
        """
        try:
            start_time = datetime.now()

            # Execute query through DuckDB manager
            df_results = self.analytics_manager.execute_query(query, params)

            # Convert DataFrame to list of tuples for compatibility
            if hasattr(df_results, "values"):
                # It's a pandas DataFrame
                results = [tuple(row) for row in df_results.values.tolist()]
            else:
                # It's already in tuple format
                results = df_results

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log the query execution
            if user_id:
                self.audit_manager.log_action(
                    action="analytics_query",
                    resource_type="duckdb_query",
                    user_id=user_id,
                    details={
                        "query_hash": hash(query),
                        "param_count": len(params) if params else 0,
                    },
                    execution_time_ms=int(execution_time),
                    success=True,
                )

            return results

        except Exception as e:
            # Log the error
            if user_id:
                self.audit_manager.log_action(
                    action="analytics_query",
                    resource_type="duckdb_query",
                    user_id=user_id,
                    details={"error": str(e)},
                    success=False,
                    error_message=str(e),
                )

            logger.error(f"Analytics query failed: {e}")
            raise

    def get_dataset_time_series(
        self,
        dataset_id: str,
        territory_code: str = None,
        measure_code: str = None,
        start_year: int = None,
        end_year: int = None,
    ) -> list[dict[str, Any]]:
        """Get time series data for a dataset with metadata integration.

        Args:
            dataset_id: ISTAT dataset identifier
            territory_code: Optional territory filter
            measure_code: Optional measure filter
            start_year: Optional start year filter
            end_year: Optional end year filter

        Returns:
            List of time series data points
        """
        try:
            # Verify dataset exists in metadata
            dataset_metadata = self.dataset_manager.get_dataset(dataset_id)
            if not dataset_metadata:
                logger.warning(f"Dataset {dataset_id} not found in metadata registry")
                return []

            # Build query conditions
            query_params = [dataset_id]
            conditions = []

            if territory_code:
                conditions.append("o.territory_code = ?")
                query_params.append(territory_code)

            if measure_code:
                conditions.append("o.measure_code = ?")
                query_params.append(measure_code)

            if start_year:
                conditions.append("d.year >= ?")
                query_params.append(start_year)

            if end_year:
                conditions.append("d.year <= ?")
                query_params.append(end_year)

            where_clause = " AND " + " AND ".join(conditions) if conditions else ""

            # Execute time series query - safe construction with predefined conditions
            base_query = """
                SELECT
                    d.year,
                    d.time_period,
                    o.territory_code,
                    o.territory_name,
                    o.measure_code,
                    o.measure_name,
                    o.obs_value,
                    o.obs_status
                FROM istat.istat_datasets d
                JOIN istat_observations o ON d.id = o.dataset_id
                WHERE d.dataset_id = ?"""

            query = (
                base_query
                + where_clause
                + " ORDER BY d.year ASC, o.territory_code ASC, o.measure_code ASC"
            )

            results = self.analytics_manager.execute_query(query, query_params)

            # Convert to dictionary format
            time_series = []
            for row in results:
                time_series.append(
                    {
                        "year": row[0],
                        "time_period": row[1],
                        "territory_code": row[2],
                        "territory_name": row[3],
                        "measure_code": row[4],
                        "measure_name": row[5],
                        "obs_value": row[6],
                        "obs_status": row[7],
                    }
                )

            # Update dataset statistics
            if time_series:
                self.dataset_manager.update_dataset_stats(
                    dataset_id, record_count=len(time_series)
                )

            return time_series

        except Exception as e:
            logger.error(f"Failed to get time series for {dataset_id}: {e}")
            return []

    # Categorization Rules Operations

    def get_categorization_rules(
        self, category: str = None, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get categorization rules for dataflow analysis.

        Args:
            category: Optional category filter
            active_only: Whether to return only active rules

        Returns:
            List of categorization rules
        """
        try:
            # TODO: Implement categorization rules in specialized manager
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to get categorization rules: {e}")
            return []

    def create_categorization_rule(
        self,
        rule_id: str,
        category: str,
        keywords: list[str],
        priority: int = 5,
        description: str = None,
    ) -> bool:
        """Create a new categorization rule.

        Args:
            rule_id: Unique rule identifier
            category: Target category
            keywords: List of keywords for matching
            priority: Rule priority (higher = more important)
            description: Optional description

        Returns:
            bool: True if rule created successfully
        """
        try:
            # TODO: Implement categorization rules in specialized manager
            return False  # self.config_manager.create_categorization_rule(rule_id, category, keywords, priority, description)
        except Exception as e:
            logger.error(f"Failed to create categorization rule: {e}")
            return False

    def update_categorization_rule(
        self,
        rule_id: str,
        keywords: list[str] = None,
        priority: int = None,
        is_active: bool = None,
        description: str = None,
    ) -> bool:
        """Update an existing categorization rule.

        Args:
            rule_id: Rule identifier to update
            keywords: Optional new keywords list
            priority: Optional new priority
            is_active: Optional active status
            description: Optional new description

        Returns:
            bool: True if rule updated successfully
        """
        try:
            # TODO: Implement categorization rules in specialized manager
            return False  # self.config_manager.update_categorization_rule(rule_id, keywords, priority, is_active, description)
        except Exception as e:
            logger.error(f"Failed to update categorization rule: {e}")
            return False

    def delete_categorization_rule(self, rule_id: str) -> bool:
        """Delete a categorization rule.

        Args:
            rule_id: Rule identifier to delete

        Returns:
            bool: True if rule deleted successfully
        """
        try:
            # TODO: Implement categorization rules in specialized manager
            return False  # self.config_manager.delete_categorization_rule(rule_id)
        except Exception as e:
            logger.error(f"Failed to delete categorization rule: {e}")
            return False

    # System Operations

    def get_system_status(self) -> dict[str, Any]:
        """Get complete system status from both databases.

        Returns:
            Dictionary with system status information
        """
        try:
            # Get SQLite metadata stats from all specialized managers
            metadata_stats = {}

            # Dataset stats
            dataset_stats = self.dataset_manager.get_dataset_stats_summary()
            metadata_stats.update(dataset_stats)

            # Add table counts using BaseSQLiteManager connection
            conn = self.dataset_manager._get_connection()
            table_counts = {
                "dataset_registry": "SELECT COUNT(*) FROM dataset_registry",
                "user_preferences": "SELECT COUNT(*) FROM user_preferences",
                "audit_log": "SELECT COUNT(*) FROM audit_log",
                "system_config": "SELECT COUNT(*) FROM system_config",
            }

            for table_name, query in table_counts.items():
                try:
                    cursor = conn.execute(query)
                    metadata_stats[f"{table_name}_count"] = cursor.fetchone()[0]
                except Exception as e:
                    logger.debug(f"Could not get count for {table_name}: {e}")
                    metadata_stats[f"{table_name}_count"] = 0

            # Get DuckDB analytics stats (if available)
            analytics_stats = {}
            try:
                # Try to get analytics statistics
                result = self.analytics_manager.execute_query(
                    "SELECT COUNT(*) FROM istat.istat_observations"
                )
                analytics_stats["total_observations"] = result[0][0] if result else 0

                result = self.analytics_manager.execute_query(
                    "SELECT COUNT(DISTINCT dataset_id) FROM istat.istat_datasets"
                )
                analytics_stats["datasets_with_data"] = result[0][0] if result else 0

            except Exception as e:
                logger.debug(f"Could not get analytics stats: {e}")
                analytics_stats["error"] = str(e)

            # Combine status information
            return {
                "metadata_database": {"status": "connected", "stats": metadata_stats},
                "analytics_database": {
                    "status": (
                        "connected" if "error" not in analytics_stats else "error"
                    ),
                    "stats": analytics_stats,
                },
                "cache": {
                    "size": len(self._cache),
                    "hit_rate": "pending_issue_63",  # Cache metrics to be implemented in Issue #63
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    # Cache Operations

    def _set_cache(self, key: str, value: Any, ttl_seconds: int):
        """Set cache value with TTL."""
        with self._lock:
            self._cache[key] = value
            self._cache_ttl[key] = datetime.now().timestamp() + ttl_seconds

    def _get_cache(self, key: str) -> Any:
        """Get cache value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            # Check TTL
            if datetime.now().timestamp() > self._cache_ttl.get(key, 0):
                # Expired, remove from cache
                del self._cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]
                return None

            return self._cache[key]

    def clear_cache(self):
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._cache_ttl.clear()
            logger.info("Cache cleared")

    # Context Managers

    @contextmanager
    def transaction(self):
        """Context manager for coordinated transactions across both databases."""
        # Note: This is a simplified implementation
        # In a production system, you might want to implement 2-phase commit
        try:
            yield self
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise

    # Convenience Methods (Aliases for backward compatibility)

    def list_datasets(self, category: str = None) -> list[dict[str, Any]]:
        """List datasets (alias for list_datasets_complete for backward compatibility).

        Args:
            category: Optional category filter

        Returns:
            List of dataset dictionaries
        """
        return self.list_datasets_complete(category=category)

    # Cleanup

    def close(self):
        """Close all database connections and cleanup resources."""
        try:
            # Close all specialized manager connections
            self.dataset_manager.close_connections()
            self.config_manager.close_connections()
            self.user_manager.close_connections()
            self.audit_manager.close_connections()
            # DuckDB manager has its own cleanup
            self.clear_cache()
            logger.info("Unified data repository closed")
        except Exception as e:
            logger.error(f"Error closing repository: {e}")


# Global repository instance
_unified_repository: Optional[UnifiedDataRepository] = None
_repository_lock = threading.Lock()


def get_unified_repository(
    sqlite_db_path: Optional[str] = None, duckdb_db_path: Optional[str] = None
) -> UnifiedDataRepository:
    """Get global unified repository instance (singleton pattern).

    Args:
        sqlite_db_path: Optional SQLite database path
        duckdb_db_path: Optional DuckDB database path

    Returns:
        UnifiedDataRepository instance
    """
    global _unified_repository

    if _unified_repository is None:
        with _repository_lock:
            if _unified_repository is None:
                _unified_repository = UnifiedDataRepository(
                    sqlite_db_path, duckdb_db_path
                )

    return _unified_repository


def reset_unified_repository():
    """Reset global unified repository (for testing)."""
    global _unified_repository

    with _repository_lock:
        if _unified_repository:
            _unified_repository.close()
            _unified_repository = None


# Example usage and testing
if __name__ == "__main__":
    # Test the unified repository
    repo = UnifiedDataRepository(
        sqlite_db_path="data/test_metadata.db", duckdb_db_path="data/test_analytics.db"
    )

    try:
        # Test complete dataset registration
        success = repo.register_dataset_complete(
            "TEST_DATASET",
            "Test Dataset",
            "test",
            "A test dataset for the unified repository",
            "TEST_AGENCY",
            5,
            {"test": True, "frequency": "annual"},
        )

        if success:
            print("✅ Dataset registered in both databases")

            # Test complete dataset retrieval
            dataset = repo.get_dataset_complete("TEST_DATASET")
            if dataset:
                print(f"📊 Complete dataset info: {dataset['name']}")
                print(f"   Analytics data: {dataset['has_analytics_data']}")

            # Test user preferences
            repo.set_user_preference("test_user", "theme", "dark")
            theme = repo.get_user_preference("test_user", "theme")
            print(f"🎨 User preference: {theme}")

            # Test system status
            status = repo.get_system_status()
            print(f"🔧 System status: {status['metadata_database']['status']}")

        else:
            print("❌ Failed to register dataset")

    finally:
        # Cleanup
        repo.close()
        print("🧹 Repository closed")
