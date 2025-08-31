"""
Base SQLite Manager - Foundation for all database managers

Provides common database connection handling, transaction management,
and shared utilities for all SQLite-based managers.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseSQLiteManager:
    """Base class for all SQLite managers with common functionality."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize base SQLite manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        self.db_path = db_path or "data/databases/osservatorio_metadata.db"
        self._lock = threading.RLock()
        self._thread_local = threading.local()

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Base SQLite manager initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection with consistent configuration."""
        if not hasattr(self._thread_local, "connection"):
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = memory")

            self._thread_local.connection = conn
            logger.debug("New database connection created")

        return self._thread_local.connection

    @contextmanager
    def transaction(self):
        """Context manager for database transactions with proper error handling."""
        conn = self._get_connection()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    def close_connections(self):
        """Close all database connections for cleanup."""
        with self._lock:
            if hasattr(self._thread_local, "connection"):
                try:
                    self._thread_local.connection.close()
                    delattr(self._thread_local, "connection")
                    logger.debug("Database connection closed")
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

    def execute_query(self, query: str, params: tuple = None) -> list[sqlite3.Row]:
        """Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            List of Row objects with query results
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(query, params or ())
            results = cursor.fetchall()
            logger.debug(f"Query executed successfully, {len(results)} rows returned")
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows.

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            Number of affected rows
        """
        try:
            with self.transaction() as conn:
                cursor = conn.execute(query, params or ())
                affected_rows = cursor.rowcount
                logger.debug(
                    f"Update executed successfully, {affected_rows} rows affected"
                )
                return affected_rows
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            raise

    def __del__(self):
        """Cleanup connections on object destruction."""
        try:
            self.close_connections()
        except Exception:
            pass  # Ignore errors during cleanup
