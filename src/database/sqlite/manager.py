"""
SQLite Metadata Manager for Osservatorio ISTAT Data Platform

Core SQLite operations manager implementing the metadata layer of the hybrid
SQLite + DuckDB architecture. Handles dataset registry, user preferences,
API credentials, audit logging, and system configuration.

Features:
- Thread-safe connection management
- CRUD operations for all metadata tables
- Security-enhanced credential storage
- Comprehensive audit logging
- Configuration management
- Transaction support
"""

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.logger import get_logger
from src.utils.security_enhanced import SecurityManager

from .schema import MetadataSchema, create_metadata_schema


# Configure SQLite datetime handling to avoid deprecation warnings
def adapt_datetime(dt):
    """Convert datetime to ISO format string for SQLite storage."""
    return dt.isoformat() if dt else None


def convert_datetime(val):
    """Convert ISO format string back to datetime from SQLite."""
    if val:
        try:
            # Handle both bytes and string formats
            if isinstance(val, bytes):
                val = val.decode("utf-8")
            # Ensure we have a string
            if isinstance(val, str):
                return datetime.fromisoformat(val)
        except (ValueError, AttributeError, TypeError) as e:
            logger.debug(f"Failed to convert datetime: {val}, error: {e}")
            return None
    return None


# Register the adapters and converters
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

logger = get_logger(__name__)
security = SecurityManager()


class SQLiteMetadataManager:
    """Thread-safe SQLite metadata manager for the hybrid architecture."""

    def __init__(self, db_path: Optional[str] = None, auto_create_schema: bool = True):
        """Initialize the SQLite metadata manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
            auto_create_schema: Whether to automatically create schema if it doesn't exist.
        """
        self.db_path = db_path or "data/databases/osservatorio_metadata.db"
        self._lock = threading.RLock()
        self._connection_pool = {}
        self._thread_local = threading.local()

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema if needed
        if auto_create_schema:
            self.schema = create_metadata_schema(self.db_path)
        else:
            self.schema = MetadataSchema(self.db_path)

        logger.info(f"SQLite metadata manager initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
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
            self._thread_local.connection = conn

        return self._thread_local.connection

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()

        # Check if we're already in a transaction
        in_transaction = conn.in_transaction

        try:
            if not in_transaction:
                conn.execute("BEGIN")

            yield conn

            if not in_transaction:
                conn.commit()
        except Exception as e:
            if not in_transaction:
                conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
            else:
                logger.warning(f"Error in nested transaction: {e}")
            raise

    def close_connections(self):
        """Close all database connections."""
        with self._lock:
            # Close thread-local connection
            if hasattr(self._thread_local, "connection"):
                self._thread_local.connection.close()
                delattr(self._thread_local, "connection")

            # Close any connections in pool
            for conn in self._connection_pool.values():
                if conn:
                    conn.close()
            self._connection_pool.clear()

            # Close schema connections if it has any
            if hasattr(self.schema, "close_connections"):
                self.schema.close_connections()

    # Dataset Registry Operations

    def register_dataset(
        self,
        dataset_id: str,
        name: str,
        category: str,
        description: str = None,
        istat_agency: str = None,
        priority: int = 5,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Register a new ISTAT dataset in the metadata registry.

        Args:
            dataset_id: Unique ISTAT dataset identifier
            name: Human-readable dataset name
            category: Dataset category (e.g., 'popolazione', 'economia')
            description: Optional dataset description
            istat_agency: ISTAT agency responsible for the dataset
            priority: Dataset priority (1-10, higher = more important)
            metadata: Additional metadata as dictionary

        Returns:
            bool: True if dataset registered successfully
        """
        try:
            with self.transaction() as conn:
                metadata_json = json.dumps(metadata) if metadata else None

                conn.execute(
                    """
                    INSERT OR REPLACE INTO dataset_registry
                    (dataset_id, name, category, description, istat_agency, priority, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        dataset_id,
                        name,
                        category,
                        description,
                        istat_agency,
                        priority,
                        metadata_json,
                    ),
                )

                # Log the registration
                self._log_audit(
                    "system",
                    "dataset_register",
                    "dataset",
                    dataset_id,
                    {"name": name, "category": category},
                    conn=conn,
                )

                logger.info(f"Dataset registered: {dataset_id} ({category})")
                return True

        except Exception as e:
            logger.error(f"Failed to register dataset {dataset_id}: {e}")
            return False

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset information by ID.

        Args:
            dataset_id: ISTAT dataset identifier

        Returns:
            Dictionary with dataset information or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM dataset_registry WHERE dataset_id = ?", (dataset_id,)
            )
            row = cursor.fetchone()

            if row:
                dataset = dict(row)
                if dataset["metadata_json"]:
                    dataset["metadata"] = json.loads(dataset["metadata_json"])
                return dataset
            return None

        except Exception as e:
            logger.error(f"Failed to get dataset {dataset_id}: {e}")
            return None

    def list_datasets(
        self, category: str = None, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List datasets with optional filtering.

        Args:
            category: Optional category filter
            active_only: Whether to return only active datasets

        Returns:
            List of dataset dictionaries
        """
        try:
            conn = self._get_connection()

            query = "SELECT * FROM dataset_registry WHERE 1=1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if active_only:
                query += " AND is_active = 1"

            query += " ORDER BY priority DESC, name ASC"

            cursor = conn.execute(query, params)
            datasets = []

            for row in cursor.fetchall():
                dataset = dict(row)
                if dataset["metadata_json"]:
                    dataset["metadata"] = json.loads(dataset["metadata_json"])
                datasets.append(dataset)

            return datasets

        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            return []

    def update_dataset_stats(
        self, dataset_id: str, quality_score: float = None, record_count: int = None
    ) -> bool:
        """Update dataset statistics.

        Args:
            dataset_id: ISTAT dataset identifier
            quality_score: Data quality score (0.0-1.0)
            record_count: Number of records in dataset

        Returns:
            bool: True if updated successfully
        """
        try:
            with self.transaction() as conn:
                updates = []
                params = []

                if quality_score is not None:
                    updates.append("quality_score = ?")
                    params.append(quality_score)

                if record_count is not None:
                    updates.append("record_count = ?")
                    params.append(record_count)

                if updates:
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(dataset_id)

                    # Safe SQL construction - updates contains only predefined field assignments
                    query = (
                        "UPDATE dataset_registry SET "
                        + ", ".join(updates)
                        + " WHERE dataset_id = ?"
                    )
                    conn.execute(query, params)

                    logger.debug(f"Updated stats for dataset {dataset_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to update dataset stats {dataset_id}: {e}")
            return False

    # User Preferences Operations

    def set_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any,
        preference_type: str = "string",
        encrypt: bool = False,
    ) -> bool:
        """Set a user preference.

        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
            preference_type: Value type ('string', 'json', 'boolean', 'integer')
            encrypt: Whether to encrypt the value

        Returns:
            bool: True if preference set successfully
        """
        try:
            with self.transaction() as conn:
                # Convert value to string based on type
                if preference_type == "json":
                    str_value = json.dumps(value)
                elif preference_type == "boolean":
                    str_value = "1" if value else "0"
                else:
                    str_value = str(value)

                # Encrypt if requested
                if encrypt:
                    str_value = security.encrypt_data(str_value)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_preferences
                    (user_id, preference_key, preference_value, preference_type, is_encrypted)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (user_id, key, str_value, preference_type, encrypt),
                )

                logger.debug(f"Set preference for user {user_id}: {key}")
                return True

        except Exception as e:
            logger.error(f"Failed to set user preference {user_id}.{key}: {e}")
            return False

    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get a user preference.

        Args:
            user_id: User identifier
            key: Preference key
            default: Default value if preference not found

        Returns:
            Preference value or default
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT preference_value, preference_type, is_encrypted FROM user_preferences WHERE user_id = ? AND preference_key = ?",
                (user_id, key),
            )
            row = cursor.fetchone()

            if not row:
                return default

            value, pref_type, is_encrypted = row

            # Decrypt if encrypted
            if is_encrypted:
                value = security.decrypt_data(value)

            # Convert based on type
            if pref_type == "json":
                return json.loads(value)
            elif pref_type == "boolean":
                return value == "1"
            elif pref_type == "integer":
                return int(value)
            else:
                return value

        except Exception as e:
            logger.error(f"Failed to get user preference {user_id}.{key}: {e}")
            return default

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of preferences
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT preference_key, preference_value, preference_type, is_encrypted FROM user_preferences WHERE user_id = ?",
                (user_id,),
            )

            preferences = {}
            for row in cursor.fetchall():
                key, value, pref_type, is_encrypted = row

                # Decrypt if encrypted
                if is_encrypted:
                    value = security.decrypt_data(value)

                # Convert based on type
                try:
                    if pref_type == "json":
                        preferences[key] = json.loads(value)
                    elif pref_type == "boolean":
                        preferences[key] = value == "1"
                    elif pref_type == "integer":
                        preferences[key] = int(value)
                    else:
                        preferences[key] = value
                except ValueError as e:
                    # Handle conversion errors gracefully
                    logger.error(
                        f"Error converting preference {key} (type: {pref_type}, value: {value}): {e}"
                    )
                    # Return the raw value if conversion fails
                    preferences[key] = value

            return preferences

        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return {}

    # API Credentials Operations

    def store_api_credentials(
        self,
        service_name: str,
        api_key: str,
        api_secret: str = None,
        endpoint_url: str = None,
        rate_limit: int = 100,
        expires_at: datetime = None,
    ) -> bool:
        """Store API credentials securely.

        Args:
            service_name: Name of the API service
            api_key: API key (will be hashed)
            api_secret: Optional API secret (will be hashed)
            endpoint_url: API endpoint URL
            rate_limit: Rate limit per hour
            expires_at: Expiration timestamp

        Returns:
            bool: True if credentials stored successfully
        """
        try:
            with self.transaction() as conn:
                # Hash the credentials
                api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                api_secret_hash = (
                    hashlib.sha256(api_secret.encode()).hexdigest()
                    if api_secret
                    else None
                )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO api_credentials
                    (service_name, api_key_hash, api_secret_hash, endpoint_url, rate_limit, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        service_name,
                        api_key_hash,
                        api_secret_hash,
                        endpoint_url,
                        rate_limit,
                        expires_at,
                    ),
                )

                # Log the credential storage (without sensitive data)
                self._log_audit(
                    "system",
                    "credentials_store",
                    "api_credential",
                    service_name,
                    {"endpoint_url": endpoint_url},
                    conn=conn,
                )

                logger.info(f"API credentials stored for service: {service_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to store API credentials for {service_name}: {e}")
            return False

    def verify_api_credentials(self, service_name: str, api_key: str) -> bool:
        """Verify API credentials.

        Args:
            service_name: Name of the API service
            api_key: API key to verify

        Returns:
            bool: True if credentials are valid
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT api_key_hash, is_active, expires_at FROM api_credentials WHERE service_name = ?",
                (service_name,),
            )
            row = cursor.fetchone()

            if not row:
                return False

            stored_hash, is_active, expires_at = row

            # Check if credentials are active
            if not is_active:
                return False

            # Check expiration
            if expires_at:
                # expires_at is already converted to datetime by our converter
                expiry = (
                    expires_at
                    if isinstance(expires_at, datetime)
                    else datetime.fromisoformat(expires_at)
                )
                if datetime.now() > expiry:
                    return False

            # Verify hash
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            is_valid = api_key_hash == stored_hash

            if is_valid:
                # Update last used timestamp and usage count
                with self.transaction() as conn:
                    conn.execute(
                        "UPDATE api_credentials SET last_used = CURRENT_TIMESTAMP, usage_count = usage_count + 1 WHERE service_name = ?",
                        (service_name,),
                    )

            return is_valid

        except Exception as e:
            logger.error(f"Failed to verify API credentials for {service_name}: {e}")
            return False

    # System Configuration Operations

    def set_config(
        self,
        key: str,
        value: str,
        config_type: str = "string",
        description: str = None,
        is_sensitive: bool = False,
        environment: str = "development",
    ) -> bool:
        """Set system configuration value.

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Value type
            description: Optional description
            is_sensitive: Whether value is sensitive
            environment: Environment (development, production, etc.)

        Returns:
            bool: True if configuration set successfully
        """
        try:
            with self.transaction() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO system_config
                    (config_key, config_value, config_type, description, is_sensitive, environment)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (key, value, config_type, description, is_sensitive, environment),
                )

                logger.debug(
                    f"Set configuration: {key} = {value if not is_sensitive else '***'}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False

    def get_config(
        self, key: str, default: str = None, environment: str = "development"
    ) -> str:
        """Get system configuration value.

        Args:
            key: Configuration key
            default: Default value if not found
            environment: Environment filter

        Returns:
            Configuration value or default
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT config_value FROM system_config WHERE config_key = ? AND environment = ?",
                (key, environment),
            )
            row = cursor.fetchone()

            return row[0] if row else default

        except Exception as e:
            logger.error(f"Failed to get configuration {key}: {e}")
            return default

    # Audit Logging Operations

    def _log_audit(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True,
        error_message: str = None,
        execution_time_ms: int = None,
        conn: sqlite3.Connection = None,
    ) -> bool:
        """Internal audit logging method.

        Args:
            user_id: User performing the action
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action succeeded
            error_message: Error message if failed
            execution_time_ms: Execution time in milliseconds
            conn: Optional database connection

        Returns:
            bool: True if logged successfully
        """
        try:
            details_json = json.dumps(details) if details else None

            sql = """
                INSERT INTO audit_log
                (user_id, action, resource_type, resource_id, details_json,
                 ip_address, user_agent, success, error_message, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user_id,
                action,
                resource_type,
                resource_id,
                details_json,
                ip_address,
                user_agent,
                success,
                error_message,
                execution_time_ms,
            )

            if conn:
                conn.execute(sql, params)
            else:
                with self.transaction() as conn:
                    conn.execute(sql, params)

            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False

    def log_audit(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        **kwargs,
    ) -> bool:
        """Public audit logging method.

        Args:
            user_id: User performing the action
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            **kwargs: Additional audit parameters

        Returns:
            bool: True if logged successfully
        """
        return self._log_audit(
            user_id, action, resource_type, resource_id, details, **kwargs
        )

    def get_audit_logs(
        self,
        user_id: str = None,
        action: str = None,
        resource_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filtering.

        Args:
            user_id: Filter by user ID
            action: Filter by action
            resource_type: Filter by resource type
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of logs to return

        Returns:
            List of audit log dictionaries
        """
        try:
            conn = self._get_connection()

            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if action:
                query += " AND action = ?"
                params.append(action)

            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            logs = []

            for row in cursor.fetchall():
                log_entry = dict(row)
                if log_entry["details_json"]:
                    log_entry["details"] = json.loads(log_entry["details_json"])
                # Convert SQLite integer to boolean
                log_entry["success"] = bool(log_entry["success"])
                logs.append(log_entry)

            return logs

        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

    # Utility Methods

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        try:
            conn = self._get_connection()
            stats = {}

            # Table row counts - using hardcoded table names for security
            table_queries = {
                "dataset_registry": "SELECT COUNT(*) FROM dataset_registry",
                "user_preferences": "SELECT COUNT(*) FROM user_preferences",
                "api_credentials": "SELECT COUNT(*) FROM api_credentials",
                "audit_log": "SELECT COUNT(*) FROM audit_log",
                "system_config": "SELECT COUNT(*) FROM system_config",
            }
            for table_name, query in table_queries.items():
                cursor = conn.execute(query)
                stats[f"{table_name}_count"] = cursor.fetchone()[0]

            # Database size
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats["database_size_bytes"] = page_count * page_size

            # Schema version
            cursor = conn.execute(
                "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            stats["schema_version"] = result[0] if result else "unknown"

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# Global manager instance
_metadata_manager: Optional[SQLiteMetadataManager] = None
_manager_lock = threading.Lock()


def get_metadata_manager(db_path: Optional[str] = None) -> SQLiteMetadataManager:
    """Get global metadata manager instance (singleton pattern).

    Args:
        db_path: Optional database path (only used on first call)

    Returns:
        SQLiteMetadataManager instance
    """
    global _metadata_manager

    if _metadata_manager is None:
        with _manager_lock:
            if _metadata_manager is None:
                _metadata_manager = SQLiteMetadataManager(db_path)

    return _metadata_manager


def reset_metadata_manager():
    """Reset global metadata manager (for testing)."""
    global _metadata_manager

    with _manager_lock:
        if _metadata_manager:
            _metadata_manager.close_connections()
            _metadata_manager = None


# Example usage and testing
if __name__ == "__main__":
    # Test the metadata manager
    manager = SQLiteMetadataManager("data/test_metadata.db")

    # Test dataset registration
    success = manager.register_dataset(
        "DCIS_POPRES1",
        "Popolazione residente",
        "popolazione",
        "Dati sulla popolazione residente italiana",
        "ISTAT",
        10,
        {"frequency": "annual", "unit": "persons"},
    )

    if success:
        print("✅ Dataset registered successfully")

        # Test retrieval
        dataset = manager.get_dataset("DCIS_POPRES1")
        if dataset:
            print(f"📊 Retrieved dataset: {dataset['name']} ({dataset['category']})")

        # Test preferences
        manager.set_user_preference("user1", "theme", "dark")
        theme = manager.get_user_preference("user1", "theme")
        print(f"🎨 User preference: theme = {theme}")

        # Test configuration
        manager.set_config(
            "test.setting", "test_value", description="Test configuration"
        )
        value = manager.get_config("test.setting")
        print(f"⚙️ Configuration: test.setting = {value}")

        # Show stats
        stats = manager.get_database_stats()
        print(f"📈 Database stats: {stats}")

    else:
        print("❌ Failed to register dataset")

    # Cleanup
    manager.close_connections()
