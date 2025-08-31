"""
Configuration Manager - Specialized SQLite manager for system configuration

Handles system configuration storage, retrieval, and management
as part of the refactored SQLite metadata architecture.
"""

import json
from typing import Any, Optional

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .base_manager import BaseSQLiteManager

logger = get_logger(__name__)


class ConfigurationManager(BaseSQLiteManager):
    """Specialized manager for system configuration operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        super().__init__(db_path)
        logger.info(f"Configuration manager initialized: {self.db_path}")

    def set_config(self, key: str, value: Any, config_type: str = "string") -> bool:
        """Set a configuration value in the database.

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Value type (string, number, boolean, json)

        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Validate inputs
            if not key:
                logger.error("Configuration key cannot be empty")
                return False

            # Convert value based on type
            if config_type == "json":
                stored_value = json.dumps(value)
            elif config_type == "boolean":
                stored_value = str(bool(value)).lower()
            elif config_type == "number":
                stored_value = str(value)
            else:
                stored_value = str(value)

            # Insert or update configuration
            query = """
                INSERT OR REPLACE INTO system_config (
                    config_key, config_value, config_type, updated_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """

            affected_rows = self.execute_update(query, (key, stored_value, config_type))

            if affected_rows > 0:
                logger.debug(f"Configuration set: {key} = {value}")
                return True
            else:
                logger.warning(f"Configuration set had no effect: {key}")
                return False

        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from the database.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        try:
            query = """
                SELECT config_value, config_type
                FROM system_config
                WHERE config_key = ?
            """

            results = self.execute_query(query, (key,))

            if results:
                row = results[0]
                value = row["config_value"]
                config_type = row["config_type"]

                # Convert value based on type
                if config_type == "json":
                    try:
                        parsed_value = json.loads(value)
                        logger.debug(f"Configuration retrieved (json): {key}")
                        return parsed_value
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid JSON in config {key}, returning raw value"
                        )
                        return value
                elif config_type == "boolean":
                    parsed_value = value.lower() in ("true", "1", "yes", "on")
                    logger.debug(
                        f"Configuration retrieved (boolean): {key} = {parsed_value}"
                    )
                    return parsed_value
                elif config_type == "number":
                    try:
                        # Try integer first, then float
                        if "." in value:
                            parsed_value = float(value)
                        else:
                            parsed_value = int(value)
                        logger.debug(
                            f"Configuration retrieved (number): {key} = {parsed_value}"
                        )
                        return parsed_value
                    except ValueError:
                        logger.warning(
                            f"Invalid number in config {key}, returning raw value"
                        )
                        return value
                else:
                    logger.debug(f"Configuration retrieved (string): {key}")
                    return value
            else:
                logger.debug(
                    f"Configuration not found, using default: {key} = {default}"
                )
                return default

        except Exception as e:
            logger.error(f"Failed to get configuration {key}: {e}")
            return default

    def delete_config(self, key: str) -> bool:
        """Delete a configuration value from the database.

        Args:
            key: Configuration key to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            query = "DELETE FROM system_config WHERE config_key = ?"
            affected_rows = self.execute_update(query, (key,))

            if affected_rows > 0:
                logger.info(f"Configuration deleted: {key}")
                return True
            else:
                logger.warning(f"Configuration not found for deletion: {key}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete configuration {key}: {e}")
            return False

    def list_configs(self, key_pattern: Optional[str] = None) -> dict[str, Any]:
        """List all configuration values, optionally filtered by key pattern.

        Args:
            key_pattern: SQL LIKE pattern to filter keys (optional)

        Returns:
            Dictionary of configuration key-value pairs
        """
        try:
            if key_pattern:
                query = """
                    SELECT config_key, config_value, config_type
                    FROM system_config
                    WHERE config_key LIKE ?
                    ORDER BY config_key
                """
                results = self.execute_query(query, (key_pattern,))
            else:
                query = """
                    SELECT config_key, config_value, config_type
                    FROM system_config
                    ORDER BY config_key
                """
                results = self.execute_query(query)

            configs = {}
            for row in results:
                key = row["config_key"]
                value = row["config_value"]
                config_type = row["config_type"]

                # Convert value based on type (same logic as get_config)
                if config_type == "json":
                    try:
                        configs[key] = json.loads(value)
                    except json.JSONDecodeError:
                        configs[key] = value
                elif config_type == "boolean":
                    configs[key] = value.lower() in ("true", "1", "yes", "on")
                elif config_type == "number":
                    try:
                        configs[key] = float(value) if "." in value else int(value)
                    except ValueError:
                        configs[key] = value
                else:
                    configs[key] = value

            logger.debug(f"Listed {len(configs)} configurations")
            return configs

        except Exception as e:
            logger.error(f"Failed to list configurations: {e}")
            return {}

    def get_config_info(self, key: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a configuration entry.

        Args:
            key: Configuration key

        Returns:
            Dictionary with configuration details or None if not found
        """
        try:
            query = """
                SELECT key, value, config_type, description, is_sensitive, updated_at
                FROM system_config
                WHERE key = ?
            """

            results = self.execute_query(query, (key,))

            if results:
                row = results[0]
                info = dict(row)
                logger.debug(f"Configuration info retrieved: {key}")
                return info
            else:
                logger.debug(f"Configuration info not found: {key}")
                return None

        except Exception as e:
            logger.error(f"Failed to get configuration info {key}: {e}")
            return None

    def set_config_with_metadata(
        self,
        key: str,
        value: Any,
        config_type: str = "string",
        description: str = "",
        is_sensitive: bool = False,
    ) -> bool:
        """Set configuration with additional metadata.

        Args:
            key: Configuration key
            value: Configuration value
            config_type: Value type (string, number, boolean, json)
            description: Configuration description
            is_sensitive: Whether value contains sensitive data

        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Convert value based on type (same logic as set_config)
            if config_type == "json":
                stored_value = json.dumps(value)
            elif config_type == "boolean":
                stored_value = str(bool(value)).lower()
            elif config_type == "number":
                stored_value = str(value)
            else:
                stored_value = str(value)

            # Insert or update with metadata
            query = """
                INSERT OR REPLACE INTO system_config (
                    key, value, config_type, description, is_sensitive, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

            affected_rows = self.execute_update(
                query, (key, stored_value, config_type, description, is_sensitive)
            )

            if affected_rows > 0:
                logger.info(f"Configuration with metadata set: {key}")
                return True
            else:
                logger.warning(f"Configuration set had no effect: {key}")
                return False

        except Exception as e:
            logger.error(f"Failed to set configuration with metadata {key}: {e}")
            return False

    def get_sensitive_configs(self) -> list[str]:
        """Get list of all sensitive configuration keys.

        Returns:
            List of sensitive configuration keys
        """
        try:
            query = """
                SELECT key
                FROM system_config
                WHERE is_sensitive = 1
                ORDER BY key
            """

            results = self.execute_query(query)
            keys = [row["key"] for row in results]

            logger.debug(f"Retrieved {len(keys)} sensitive configuration keys")
            return keys

        except Exception as e:
            logger.error(f"Failed to get sensitive configurations: {e}")
            return []


# Factory function for easy instantiation
def get_configuration_manager(db_path: Optional[str] = None) -> ConfigurationManager:
    """Get a configuration manager instance.

    Args:
        db_path: Path to SQLite database. If None, uses default.

    Returns:
        ConfigurationManager instance
    """
    return ConfigurationManager(db_path)
