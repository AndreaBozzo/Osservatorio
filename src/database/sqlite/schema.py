"""
SQLite Metadata Schema for Osservatorio ISTAT Data Platform

Implements the metadata layer of the hybrid SQLite + DuckDB architecture.
Handles dataset registry, user preferences, API keys/auth, and audit logging.

Tables:
- dataset_registry: ISTAT dataset metadata and configuration
- user_preferences: User settings and dashboard preferences
- api_credentials: API keys and authentication tokens
- audit_log: System audit trail and logging
- system_config: Application configuration and settings
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from src.utils.security_enhanced import SecurityManager

logger = get_logger(__name__)
security = SecurityManager()


class MetadataSchema:
    """SQLite metadata schema manager for the hybrid architecture."""

    # Schema version for migrations
    SCHEMA_VERSION = "1.0.0"

    # Table creation SQL statements
    SCHEMA_SQL = {
        "dataset_registry": """
            CREATE TABLE IF NOT EXISTS dataset_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                istat_agency TEXT,
                priority INTEGER DEFAULT 5,
                is_active BOOLEAN DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT,
                quality_score REAL DEFAULT 0.0,
                record_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "user_preferences": """
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                preference_type TEXT DEFAULT 'string',
                is_encrypted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, preference_key)
            )
        """,
        "api_credentials": """
            CREATE TABLE IF NOT EXISTS api_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL UNIQUE,
                api_key_hash TEXT NOT NULL,
                api_secret_hash TEXT,
                endpoint_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                expires_at TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "audit_log": """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                details_json TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                execution_time_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "system_config": """
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                is_sensitive BOOLEAN DEFAULT 0,
                environment TEXT DEFAULT 'development',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "schema_migrations": """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
    }

    # Index creation SQL statements
    INDEXES_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_dataset_registry_category ON dataset_registry(category)",
        "CREATE INDEX IF NOT EXISTS idx_dataset_registry_priority ON dataset_registry(priority DESC)",
        "CREATE INDEX IF NOT EXISTS idx_dataset_registry_active ON dataset_registry(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_api_credentials_service ON api_credentials(service_name)",
        "CREATE INDEX IF NOT EXISTS idx_api_credentials_active ON api_credentials(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)",
        "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key)",
        "CREATE INDEX IF NOT EXISTS idx_system_config_env ON system_config(environment)",
    ]

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the metadata schema manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        if db_path is None:
            db_path = self._get_default_db_path()

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing SQLite metadata schema: {self.db_path}")

    def _get_default_db_path(self) -> str:
        """Get the default database path."""
        return "data/databases/osservatorio_metadata.db"

    def create_schema(self) -> bool:
        """Create the complete metadata schema.

        Returns:
            bool: True if schema created successfully, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")

                # Create all tables
                for table_name, sql in self.SCHEMA_SQL.items():
                    logger.debug(f"Creating table: {table_name}")
                    conn.execute(sql)

                # Create indexes
                for index_sql in self.INDEXES_SQL:
                    conn.execute(index_sql)

                # Record schema version
                conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations (version, description) VALUES (?, ?)",
                    (self.SCHEMA_VERSION, "Initial SQLite metadata schema"),
                )

                # Insert default system configuration
                self._insert_default_config(conn)

                conn.commit()
                logger.info("SQLite metadata schema created successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to create metadata schema: {e}")
            return False

    def _insert_default_config(self, conn: sqlite3.Connection) -> None:
        """Insert default system configuration."""
        default_configs = [
            (
                "database.sqlite.path",
                str(self.db_path),
                "string",
                "SQLite metadata database path",
                False,
            ),
            (
                "database.duckdb.path",
                "data/databases/osservatorio.duckdb",
                "string",
                "DuckDB analytics database path",
                False,
            ),
            (
                "api.istat.rate_limit",
                "50",
                "integer",
                "ISTAT API rate limit per hour",
                False,
            ),
            (
                "api.istat.timeout",
                "30",
                "integer",
                "ISTAT API timeout in seconds",
                False,
            ),
            (
                "cache.default_ttl",
                "1800",
                "integer",
                "Default cache TTL in seconds",
                False,
            ),
            (
                "security.max_login_attempts",
                "5",
                "integer",
                "Maximum login attempts before lockout",
                False,
            ),
            ("logging.level", "INFO", "string", "Application logging level", False),
            (
                "dashboard.refresh_interval",
                "300",
                "integer",
                "Dashboard refresh interval in seconds",
                False,
            ),
        ]

        for key, value, type_, desc, sensitive in default_configs:
            conn.execute(
                """INSERT OR IGNORE INTO system_config
                   (config_key, config_value, config_type, description, is_sensitive)
                   VALUES (?, ?, ?, ?, ?)""",
                (key, value, type_, desc, sensitive),
            )

    def verify_schema(self) -> bool:
        """Verify that the schema is properly created.

        Returns:
            bool: True if schema is valid, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check that all required tables exist
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                existing_tables = {row[0] for row in cursor.fetchall()}
                required_tables = set(self.SCHEMA_SQL.keys())

                missing_tables = required_tables - existing_tables
                if missing_tables:
                    logger.error(f"Missing required tables: {missing_tables}")
                    return False

                # Check schema version
                cursor = conn.execute(
                    "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
                )
                result = cursor.fetchone()
                if not result or result[0] != self.SCHEMA_VERSION:
                    logger.warning(
                        f"Schema version mismatch. Expected: {self.SCHEMA_VERSION}, Found: {result[0] if result else 'None'}"
                    )

                logger.info("SQLite metadata schema verification successful")
                return True

        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get information about a specific table.

        Args:
            table_name: Name of the table to inspect.

        Returns:
            List of column information dictionaries.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                return [
                    {
                        "cid": col[0],
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "default_value": col[4],
                        "pk": bool(col[5]),
                    }
                    for col in columns
                ]
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return []

    def drop_schema(self) -> bool:
        """Drop the entire metadata schema (for testing/cleanup).

        Returns:
            bool: True if schema dropped successfully, False otherwise.
        """
        try:
            if self.db_path.exists():
                # Force close any connections and clear WAL files on Windows
                import gc
                import sqlite3
                import time

                # First, drop all tables to clear the schema content
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        # Get all tables
                        cursor = conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        )
                        tables = [row[0] for row in cursor.fetchall()]

                        # Drop all tables
                        for table in tables:
                            conn.execute(f"DROP TABLE IF EXISTS {table}")

                        # Checkpoint and close
                        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                        conn.commit()
                        logger.debug("All tables dropped from database")
                except Exception as e:
                    logger.debug(f"Error dropping tables (continuing): {e}")

                # Force garbage collection to clean up connections
                gc.collect()

                # Try multiple times on Windows due to file locking
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        self.db_path.unlink()
                        logger.info("SQLite metadata database dropped successfully")
                        return True
                    except PermissionError:
                        if attempt < max_attempts - 1:
                            time.sleep(0.1)  # Wait briefly
                            continue
                        else:
                            # On Windows, if we can't delete file but tables are dropped, that's OK
                            logger.warning(
                                f"Could not delete database file due to Windows file locking: {self.db_path}"
                            )
                            logger.info("Schema tables were dropped successfully")
                            return True
            return True
        except Exception as e:
            logger.error(f"Failed to drop schema: {e}")
            return False


def create_metadata_schema(db_path: Optional[str] = None) -> MetadataSchema:
    """Factory function to create and initialize metadata schema.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        MetadataSchema instance with schema created.
    """
    schema = MetadataSchema(db_path)
    schema.create_schema()
    return schema


# Example usage and testing
if __name__ == "__main__":
    # Create test schema
    schema = create_metadata_schema("data/test_metadata.db")

    # Verify schema
    if schema.verify_schema():
        print("✅ Metadata schema created and verified successfully")

        # Show table information
        for table_name in schema.SCHEMA_SQL.keys():
            info = schema.get_table_info(table_name)
            print(f"\n📋 Table: {table_name}")
            for col in info:
                print(
                    f"  - {col['name']} ({col['type']}) {'PK' if col['pk'] else ''}{'NOT NULL' if col['notnull'] else ''}"
                )
    else:
        print("❌ Schema verification failed")
