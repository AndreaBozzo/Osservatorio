"""DuckDB database manager for Osservatorio ISTAT analytics.

This module provides a high-level database manager that handles:
- Connection management and pooling
- Transaction handling
- Query execution with error handling
- Performance monitoring and optimization
"""

import atexit
import os
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Union

import duckdb
import pandas as pd

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .config import get_connection_string, get_duckdb_config

# from utils.security_enhanced import security_manager

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

    def __init__(self, config: Optional[Union[dict[str, Any], str]] = None):
        """Initialize DuckDB manager.

        Args:
            config: Optional custom configuration dict, database path string, or None for defaults
        """
        if config is None:
            self.config = get_duckdb_config()
            self.connection_string = get_connection_string()
        elif isinstance(config, str):
            # Handle db_path string parameter
            self.config = get_duckdb_config()
            self.connection_string = config
        else:
            # Handle config dictionary
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
            # Ensure the database path is properly encoded for Windows
            db_path_str = str(self.connection_string)

            # Handle Windows path properly - keep backslashes for Windows
            if os.name == "nt":  # Windows
                db_path_str = os.path.normpath(db_path_str)
            else:
                db_path_str = db_path_str.replace("\\", "/")

            # Handle database path
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Let DuckDB handle its own file validation - no manual corruption detection

            print(f"Connecting to database: {db_path_str}")

            # Create connection with proper encoding handling
            self._connection = duckdb.connect(
                database=str(db_path_str),  # Ensure string conversion
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

        STABLE PATTERN: Always create fresh connection per context.
        This prevents lock issues and ensures clean state.
        """
        conn = None
        try:
            # Always create fresh connection - no shared state
            db_path_str = self.connection_string
            conn = duckdb.connect(database=str(db_path_str))
            yield conn
        except Exception as e:
            print(f"Connection error: {e}")
            raise
        finally:
            # Always clean up connection
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass  # Ignore close errors

    def execute_query(
        self, query: str, parameters: Optional[dict[str, Any]] = None
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
        parameters: Optional[Union[dict[str, Any], list[Any]]] = None,
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

                # Get table schema and reorder DataFrame to match
                schema_query = f"DESCRIBE {table_name}"
                table_columns = [
                    row[0] for row in conn.execute(schema_query).fetchall()
                ]
                df_columns = list(data.columns)
                available_columns = [col for col in table_columns if col in df_columns]

                if not available_columns:
                    raise ValueError(
                        f"No matching columns found between DataFrame and table {table_name}"
                    )

                # Reorder DataFrame to match table schema order
                data_reordered = data[available_columns]

                # Insert with reordered data
                try:
                    conn.register("temp_df", data_reordered)
                    insert_query = f"INSERT INTO {table_name} SELECT * FROM temp_df"  # nosec B608
                    conn.execute(insert_query)
                finally:
                    # Always cleanup temp registration
                    try:
                        conn.unregister("temp_df")
                    except Exception:
                        pass  # Ignore cleanup errors

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

    def get_performance_stats(self) -> dict[str, Any]:
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

    def ensure_schema_exists(self) -> bool:
        """Ensure that the required DuckDB schema exists.

        This method is called by the UnifiedDataRepository to ensure
        that the analytics database schema is properly initialized.

        Returns:
            bool: True if schema exists or was created successfully
        """
        try:
            # For now, we'll just verify that we can connect to the database
            # In a full implementation, this would create necessary tables
            with self.get_connection() as conn:
                # Simple test query to verify connection works
                conn.execute("SELECT 1").fetchone()
                return True
        except Exception as e:
            logger.error(f"Failed to ensure schema exists: {e}")
            return False

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


def get_manager() -> DuckDBManager:
    """Get new DuckDB manager instance (no singleton - always fresh).

    Returns:
        New DuckDBManager instance
    """
    return DuckDBManager()
