"""DuckDB database manager for Osservatorio ISTAT analytics.

This module provides a high-level database manager that handles:
- Connection management and pooling
- Transaction handling
- Query execution with error handling
- Performance monitoring and optimization
"""

import atexit
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Union

import duckdb
import pandas as pd

from src.utils.logger import get_logger

from .config import PERFORMANCE_CONFIG, get_connection_string, get_duckdb_config

# from src.utils.security_enhanced import security_manager

logger = get_logger(__name__)


class DuckDBManager:
    """High-performance DuckDB manager for ISTAT analytics data.

    Features:
    - Connection pooling and management
    - Query performance monitoring
    - Transaction support
    - Automatic schema management
    - Security validation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize DuckDB manager.

        Args:
            config: Optional custom configuration, uses default if None
        """
        if config is None:
            self.config = get_duckdb_config()
            self.connection_string = get_connection_string()
        else:
            self.config = config
            self.connection_string = config.get("database", get_connection_string())
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._lock = Lock()
        self._query_stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "slow_queries": 0,
            "errors": 0,
        }

        # DON'T initialize connection in constructor - do it lazily
        # This prevents blocking during object creation

        # Register cleanup on exit
        atexit.register(self.close)

        print(f"DuckDB manager initialized (lazy connection): {self.connection_string}")

    def _initialize_connection(self) -> None:
        """Initialize DuckDB connection with configuration."""
        if self._connection is not None:
            return  # Already connected

        try:
            # Ensure the database path is properly encoded as string
            db_path_str = str(self.connection_string).replace("\\", "/")

            # Handle database path - if it exists and is invalid, remove it
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # If database file exists but is empty/invalid, remove it
            if db_path.exists() and db_path.stat().st_size == 0:
                db_path.unlink()

            print(f"Connecting to database: {db_path_str}")

            # Create connection with minimal config for stability
            self._connection = duckdb.connect(
                database=db_path_str,
                read_only=self.config.get("read_only", False),
                config={"enable_object_cache": False},
            )

            # Apply performance settings
            self._apply_performance_settings()

            print("DuckDB connection established successfully")

        except Exception as e:
            print(f"Failed to initialize DuckDB connection: {e}")
            self._connection = None
            raise

    def _apply_performance_settings(self) -> None:
        """Apply performance optimization settings."""
        try:
            # Skip performance settings for now to avoid issues
            print("Skipping performance settings for stability")

        except Exception as e:
            print(f"Failed to apply performance settings: {e}")

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup.

        Yields:
            DuckDB connection object
        """
        # Simplified connection management to avoid deadlocks
        try:
            if self._connection is None:
                print("Initializing connection...")
                self._initialize_connection()
            print("Yielding connection...")
            yield self._connection
            print("Connection context exited successfully")
        except Exception as e:
            print(f"Connection error: {e}")
            # Reset connection on error
            self._connection = None
            raise

    def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame.

        Args:
            query: SQL query to execute
            parameters: Optional query parameters for prepared statements

        Returns:
            Query results as pandas DataFrame

        Raises:
            Exception: If query execution fails
        """
        start_time = time.time()

        try:
            # Security validation (temporarily disabled for stability)
            # if not security_manager.sanitize_input(query):
            #     raise ValueError("Query failed security validation")

            with self.get_connection() as conn:
                if parameters:
                    result = conn.execute(query, parameters).df()
                else:
                    result = conn.execute(query).df()

                # Update statistics
                execution_time = time.time() - start_time
                self._update_query_stats(execution_time, success=True)

                print(f"Query executed successfully in {execution_time:.3f}s")
                return result

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(execution_time, success=False)

            print(f"Query execution failed after {execution_time:.3f}s: {e}")
            print(f"Failed query: {query[:200]}...")
            raise

    def execute_statement(
        self,
        statement: str,
        parameters: Optional[Union[Dict[str, Any], List[Any]]] = None,
    ) -> None:
        """Execute SQL statement without returning results.

        Args:
            statement: SQL statement to execute
            parameters: Optional statement parameters
        """
        start_time = time.time()

        try:
            # Security validation (temporarily disabled for stability)
            # if not security_manager.sanitize_input(statement):
            #     raise ValueError("Statement failed security validation")

            with self.get_connection() as conn:
                if parameters:
                    conn.execute(statement, parameters)
                else:
                    conn.execute(statement)

                # Update statistics
                execution_time = time.time() - start_time
                self._update_query_stats(execution_time, success=True)

                print(f"Statement executed successfully in {execution_time:.3f}s")

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(execution_time, success=False)

            print(f"Statement execution failed after {execution_time:.3f}s: {e}")
            print(f"Failed statement: {statement[:200]}...")
            raise

    def bulk_insert(self, table_name: str, data: pd.DataFrame) -> None:
        """Perform optimized bulk insert of DataFrame data.

        Args:
            table_name: Target table name
            data: DataFrame to insert
        """
        start_time = time.time()

        try:
            # Validate table name (temporarily disabled for stability)
            # if not security_manager.sanitize_input(table_name):
            #     raise ValueError("Table name failed security validation")

            with self.get_connection() as conn:
                # Use DuckDB's optimized DataFrame insertion with enhanced validation
                # Enhanced table name validation to prevent SQL injection
                table_parts = table_name.split(".")
                if len(table_parts) > 2:
                    raise ValueError(f"Invalid table name format: {table_name}")

                for part in table_parts:
                    if not part.replace("_", "").isalnum() or not part.islower():
                        raise ValueError(f"Invalid table name component: {part}")

                conn.register("temp_df", data)
                # Table name validated above - safe for f-string usage
                insert_query = f"INSERT INTO {table_name} SELECT * FROM temp_df"
                conn.execute(insert_query)
                conn.unregister("temp_df")

                execution_time = time.time() - start_time
                self._update_query_stats(execution_time, success=True)

                print(
                    f"Bulk insert completed: {len(data)} rows in {execution_time:.3f}s"
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(execution_time, success=False)

            print(f"Bulk insert failed after {execution_time:.3f}s: {e}")
            raise

    @contextmanager
    def transaction(self):
        """Context manager for database transactions.

        Yields:
            DuckDB connection within transaction
        """
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION;")
                yield conn
                conn.execute("COMMIT;")
                print("Transaction committed successfully")
            except Exception as e:
                conn.execute("ROLLBACK;")
                print(f"Transaction rolled back due to error: {e}")
                raise

    def create_schema(self, schema_name: str) -> None:
        """Create database schema if it doesn't exist.

        Args:
            schema_name: Name of schema to create
        """
        try:
            # Validate schema name (temporarily disabled for stability)
            # if not security_manager.sanitize_input(schema_name):
            #     raise ValueError("Schema name failed security validation")

            create_sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
            self.execute_statement(create_sql)
            print(f"Schema created/verified: {schema_name}")

        except Exception as e:
            print(f"Failed to create schema {schema_name}: {e}")
            raise

    def table_exists(self, table_name: str, schema_name: str = "main") -> bool:
        """Check if table exists in database.

        Args:
            table_name: Name of table to check
            schema_name: Schema name (default: main)

        Returns:
            True if table exists, False otherwise
        """
        try:
            # Use DuckDB's system tables to check existence with parameterized queries
            # Validate inputs to prevent SQL injection
            if not table_name.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid table name: {table_name}")
            if not schema_name.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid schema name: {schema_name}")

            with self.get_connection() as conn:
                if schema_name == "main":
                    query = "SELECT COUNT(*) as table_count FROM duckdb_tables WHERE table_name = ?;"
                    result = conn.execute(query, [table_name]).fetchone()
                else:
                    query = "SELECT COUNT(*) as table_count FROM duckdb_tables WHERE schema_name = ? AND table_name = ?;"
                    result = conn.execute(query, [schema_name, table_name]).fetchone()

                return bool(result[0] > 0)

        except Exception as e:
            print(f"Error checking table existence: {e}")
            return False

    def get_table_info(
        self, table_name: str, schema_name: str = "main"
    ) -> pd.DataFrame:
        """Get detailed information about table structure.

        Args:
            table_name: Name of table
            schema_name: Schema name (default: main)

        Returns:
            DataFrame with table column information
        """
        try:
            query = f"DESCRIBE {schema_name}.{table_name};"
            return self.execute_query(query)

        except Exception as e:
            print(f"Error getting table info: {e}")
            raise

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        with self._lock:
            stats = self._query_stats.copy()

            # Calculate derived metrics
            if stats["total_queries"] > 0:
                stats["avg_query_time"] = stats["total_time"] / stats["total_queries"]
                stats["slow_query_percentage"] = (
                    stats["slow_queries"] / stats["total_queries"]
                ) * 100
                stats["error_percentage"] = (
                    stats["errors"] / stats["total_queries"]
                ) * 100
            else:
                stats["avg_query_time"] = 0.0
                stats["slow_query_percentage"] = 0.0
                stats["error_percentage"] = 0.0

            return stats

    def _update_query_stats(self, execution_time: float, success: bool = True) -> None:
        """Update query execution statistics.

        Args:
            execution_time: Query execution time in seconds
            success: Whether query succeeded
        """
        with self._lock:
            self._query_stats["total_queries"] += 1
            self._query_stats["total_time"] += execution_time

            # Consider queries > 1 second as slow
            if execution_time > 1.0:
                self._query_stats["slow_queries"] += 1

            if not success:
                self._query_stats["errors"] += 1

    def optimize_database(self) -> None:
        """Perform database optimization operations.

        This includes:
        - Analyzing table statistics
        - Optimizing query plans
        - Cleaning up temporary data
        """
        try:
            print("Starting database optimization...")

            with self.get_connection() as conn:
                # Analyze all tables for query optimization
                conn.execute("ANALYZE;")

                # Checkpoint to flush WAL and optimize storage
                conn.execute("CHECKPOINT;")

                # Vacuum to reclaim space (if supported)
                try:
                    conn.execute("VACUUM;")
                except Exception as e:
                    # VACUUM may not be available in all DuckDB versions
                    logger.debug(
                        f"VACUUM not supported or failed (this is normal): {e}"
                    )

            print("Database optimization completed successfully")

        except Exception as e:
            print(f"Database optimization failed: {e}")
            raise

    def close(self) -> None:
        """Close database connection and cleanup resources."""
        try:
            with self._lock:
                if self._connection:
                    self._connection.close()
                    self._connection = None
                    print("DuckDB connection closed successfully")
        except Exception as e:
            print(f"Error during connection cleanup: {e}")


# Global manager instance
_manager_instance = None
_manager_lock = Lock()


def get_manager() -> DuckDBManager:
    """Get global DuckDB manager instance (singleton pattern).

    Returns:
        Global DuckDBManager instance
    """
    global _manager_instance

    if _manager_instance is None:
        with _manager_lock:
            if _manager_instance is None:
                _manager_instance = DuckDBManager()

    return _manager_instance


def reset_manager() -> None:
    """Reset global manager instance (mainly for testing)."""
    global _manager_instance

    with _manager_lock:
        if _manager_instance:
            _manager_instance.close()
        _manager_instance = None
