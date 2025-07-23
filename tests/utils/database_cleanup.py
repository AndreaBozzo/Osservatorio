"""
Database cleanup utilities for tests.

Provides robust file cleanup for SQLite and DuckDB files on Windows,
handling common permission errors and file locking issues.
"""

import gc
import logging
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """Robust database file cleanup for test environments."""

    @staticmethod
    def force_close_connections():
        """Force garbage collection to close any lingering database connections."""
        try:
            # Force garbage collection multiple times
            for _ in range(3):
                gc.collect()
            time.sleep(0.1)  # Give time for cleanup
        except Exception as e:
            logger.debug(f"Error during connection cleanup: {e}")

    @staticmethod
    def cleanup_sqlite_file(db_path: str, max_attempts: int = 5) -> bool:
        """
        Safely cleanup SQLite database file.

        Args:
            db_path: Path to SQLite database file
            max_attempts: Maximum cleanup attempts

        Returns:
            bool: True if cleanup successful, False otherwise
        """
        if not db_path or not Path(db_path).exists():
            return True

        try:
            db_path = Path(db_path)

            # Step 1: Try to close any open connections
            DatabaseCleaner.force_close_connections()

            # Step 2: Try to checkpoint and close WAL files
            try:
                with sqlite3.connect(db_path, timeout=1.0) as conn:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    conn.close()
            except Exception:
                pass  # Ignore connection errors

            # Step 3: Force another garbage collection
            DatabaseCleaner.force_close_connections()

            # Step 4: Try to delete file with retries
            for attempt in range(max_attempts):
                try:
                    # Try to delete main database file
                    if db_path.exists():
                        db_path.unlink()

                    # Try to delete related files (WAL, SHM)
                    for suffix in ["-wal", "-shm", ".wal", ".shm"]:
                        related_file = Path(str(db_path) + suffix)
                        if related_file.exists():
                            try:
                                related_file.unlink()
                            except PermissionError:
                                pass  # Ignore related file cleanup errors

                    logger.debug(f"Successfully cleaned up SQLite file: {db_path}")
                    return True

                except PermissionError as e:
                    if attempt < max_attempts - 1:
                        # Wait and retry
                        time.sleep(0.2 * (2**attempt))  # Exponential backoff
                        DatabaseCleaner.force_close_connections()
                        continue
                    else:
                        # Final attempt failed - this is expected on Windows sometimes
                        logger.warning(f"Could not cleanup SQLite file {db_path}: {e}")
                        return False

            return False

        except Exception as e:
            logger.error(f"Error during SQLite cleanup for {db_path}: {e}")
            return False

    @staticmethod
    def cleanup_duckdb_file(db_path: str, max_attempts: int = 3) -> bool:
        """
        Safely cleanup DuckDB database file.

        Args:
            db_path: Path to DuckDB database file
            max_attempts: Maximum cleanup attempts

        Returns:
            bool: True if cleanup successful, False otherwise
        """
        if not db_path or not Path(db_path).exists():
            return True

        try:
            db_path = Path(db_path)

            # Step 1: Force garbage collection
            DatabaseCleaner.force_close_connections()

            # Step 2: Try to delete with retries
            for attempt in range(max_attempts):
                try:
                    if db_path.exists():
                        db_path.unlink()

                    logger.debug(f"Successfully cleaned up DuckDB file: {db_path}")
                    return True

                except PermissionError as e:
                    if attempt < max_attempts - 1:
                        time.sleep(0.1 * (2**attempt))
                        DatabaseCleaner.force_close_connections()
                        continue
                    else:
                        logger.warning(f"Could not cleanup DuckDB file {db_path}: {e}")
                        return False

            return False

        except Exception as e:
            logger.error(f"Error during DuckDB cleanup for {db_path}: {e}")
            return False

    @staticmethod
    def cleanup_database_files(
        sqlite_paths: List[str] = None, duckdb_paths: List[str] = None
    ) -> dict:
        """
        Cleanup multiple database files.

        Args:
            sqlite_paths: List of SQLite database paths
            duckdb_paths: List of DuckDB database paths

        Returns:
            dict: Cleanup results summary
        """
        results = {
            "sqlite_success": 0,
            "sqlite_failed": 0,
            "duckdb_success": 0,
            "duckdb_failed": 0,
            "total_files": 0,
        }

        # Cleanup SQLite files
        if sqlite_paths:
            for path in sqlite_paths:
                results["total_files"] += 1
                if DatabaseCleaner.cleanup_sqlite_file(path):
                    results["sqlite_success"] += 1
                else:
                    results["sqlite_failed"] += 1

        # Cleanup DuckDB files
        if duckdb_paths:
            for path in duckdb_paths:
                results["total_files"] += 1
                if DatabaseCleaner.cleanup_duckdb_file(path):
                    results["duckdb_success"] += 1
                else:
                    results["duckdb_failed"] += 1

        logger.info(f"Database cleanup results: {results}")
        return results


def safe_database_cleanup(
    sqlite_path: Optional[str] = None, duckdb_path: Optional[str] = None
) -> bool:
    """
    Convenience function for safe database cleanup.

    Args:
        sqlite_path: Optional SQLite database path
        duckdb_path: Optional DuckDB database path

    Returns:
        bool: True if all cleanups successful
    """
    sqlite_paths = [sqlite_path] if sqlite_path else []
    duckdb_paths = [duckdb_path] if duckdb_path else []

    results = DatabaseCleaner.cleanup_database_files(sqlite_paths, duckdb_paths)
    return results["sqlite_failed"] == 0 and results["duckdb_failed"] == 0
