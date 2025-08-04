"""
User Manager - Specialized SQLite manager for user preferences and settings

Handles user preferences, settings, and user-related operations
as part of the refactored SQLite metadata architecture.
"""

import json
from typing import Any, Optional

from src.utils.logger import get_logger

from .base_manager import BaseSQLiteManager

logger = get_logger(__name__)


class UserManager(BaseSQLiteManager):
    """Specialized manager for user preferences and settings operations."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize user manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        super().__init__(db_path)
        logger.info(f"User manager initialized: {self.db_path}")

    def set_user_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: Any,
        preference_type: str = "string",
        is_encrypted: bool = False,
    ) -> bool:
        """Set a user preference.

        Args:
            user_id: User identifier
            preference_key: Preference key
            preference_value: Preference value
            preference_type: Value type (string, number, boolean, json)
            is_encrypted: Whether value should be encrypted

        Returns:
            True if set successfully, False otherwise
        """
        try:
            if not user_id or not preference_key:
                logger.error("User ID and preference key are required")
                return False

            # Convert value based on type
            if preference_type == "json":
                stored_value = json.dumps(preference_value)
            elif preference_type == "boolean":
                stored_value = str(bool(preference_value)).lower()
            elif preference_type == "number":
                stored_value = str(preference_value)
            else:
                stored_value = str(preference_value)

            # Insert or update preference
            query = """
                INSERT OR REPLACE INTO user_preferences (
                    user_id, preference_key, preference_value,
                    preference_type, is_encrypted, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

            affected_rows = self.execute_update(
                query,
                (user_id, preference_key, stored_value, preference_type, is_encrypted),
            )

            if affected_rows > 0:
                logger.debug(f"User preference set: {user_id}.{preference_key}")
                return True
            else:
                logger.warning(
                    f"User preference set had no effect: {user_id}.{preference_key}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to set user preference {user_id}.{preference_key}: {e}"
            )
            return False

    def get_user_preference(
        self, user_id: str, preference_key: str, default: Any = None
    ) -> Any:
        """Get a user preference value.

        Args:
            user_id: User identifier
            preference_key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        try:
            query = """
                SELECT preference_value, preference_type
                FROM user_preferences
                WHERE user_id = ? AND preference_key = ?
            """

            results = self.execute_query(query, (user_id, preference_key))

            if results:
                row = results[0]
                value = row["preference_value"]
                preference_type = row["preference_type"]

                # Convert value based on type
                if preference_type == "json":
                    try:
                        parsed_value = json.loads(value)
                        logger.debug(
                            f"User preference retrieved (json): {user_id}.{preference_key}"
                        )
                        return parsed_value
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid JSON in preference {user_id}.{preference_key}, returning raw value"
                        )
                        return value
                elif preference_type == "boolean":
                    parsed_value = value.lower() in ("true", "1", "yes", "on")
                    logger.debug(
                        f"User preference retrieved (boolean): {user_id}.{preference_key} = {parsed_value}"
                    )
                    return parsed_value
                elif preference_type in ("number", "integer"):
                    try:
                        # Try integer first, then float
                        if "." in value:
                            parsed_value = float(value)
                        else:
                            parsed_value = int(value)
                        logger.debug(
                            f"User preference retrieved (number): {user_id}.{preference_key} = {parsed_value}"
                        )
                        return parsed_value
                    except ValueError:
                        logger.warning(
                            f"Invalid number in preference {user_id}.{preference_key}, returning raw value"
                        )
                        return value
                else:
                    logger.debug(
                        f"User preference retrieved (string): {user_id}.{preference_key}"
                    )
                    return value
            else:
                logger.debug(
                    f"User preference not found, using default: {user_id}.{preference_key} = {default}"
                )
                return default

        except Exception as e:
            logger.error(
                f"Failed to get user preference {user_id}.{preference_key}: {e}"
            )
            return default

    def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """Get all preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of preference key-value pairs
        """
        try:
            query = """
                SELECT preference_key, preference_value, preference_type
                FROM user_preferences
                WHERE user_id = ?
                ORDER BY preference_key
            """

            results = self.execute_query(query, (user_id,))

            preferences = {}
            for row in results:
                key = row["preference_key"]
                value = row["preference_value"]
                preference_type = row["preference_type"]

                # Convert value based on type (same logic as get_user_preference)
                if preference_type == "json":
                    try:
                        preferences[key] = json.loads(value)
                    except json.JSONDecodeError:
                        preferences[key] = value
                elif preference_type == "boolean":
                    preferences[key] = value.lower() in ("true", "1", "yes", "on")
                elif preference_type in ("number", "integer"):
                    try:
                        preferences[key] = float(value) if "." in value else int(value)
                    except ValueError:
                        preferences[key] = value
                else:
                    preferences[key] = value

            logger.debug(f"Retrieved {len(preferences)} preferences for user {user_id}")
            return preferences

        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return {}

    def delete_user_preference(self, user_id: str, preference_key: str) -> bool:
        """Delete a user preference.

        Args:
            user_id: User identifier
            preference_key: Preference key to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            query = """
                DELETE FROM user_preferences
                WHERE user_id = ? AND preference_key = ?
            """
            affected_rows = self.execute_update(query, (user_id, preference_key))

            if affected_rows > 0:
                logger.info(f"User preference deleted: {user_id}.{preference_key}")
                return True
            else:
                logger.warning(
                    f"User preference not found for deletion: {user_id}.{preference_key}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to delete user preference {user_id}.{preference_key}: {e}"
            )
            return False

    def delete_all_user_preferences(self, user_id: str) -> bool:
        """Delete all preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            query = "DELETE FROM user_preferences WHERE user_id = ?"
            affected_rows = self.execute_update(query, (user_id,))

            logger.info(f"Deleted {affected_rows} preferences for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete all preferences for user {user_id}: {e}")
            return False

    def get_users_with_preferences(self) -> list[str]:
        """Get list of all users that have preferences set.

        Returns:
            List of user IDs
        """
        try:
            query = """
                SELECT DISTINCT user_id
                FROM user_preferences
                ORDER BY user_id
            """

            results = self.execute_query(query)
            users = [row["user_id"] for row in results]

            logger.debug(f"Retrieved {len(users)} users with preferences")
            return users

        except Exception as e:
            logger.error(f"Failed to get users with preferences: {e}")
            return []

    def get_preference_usage_stats(self) -> dict[str, Any]:
        """Get statistics about preference usage.

        Returns:
            Dictionary with preference usage statistics
        """
        try:
            query = """
                SELECT
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(*) as total_preferences,
                    COUNT(DISTINCT preference_key) as unique_keys,
                    AVG(CASE WHEN preference_type = 'json' THEN 1 ELSE 0 END) as json_ratio,
                    COUNT(CASE WHEN is_encrypted = 1 THEN 1 END) as encrypted_count
                FROM user_preferences
            """

            results = self.execute_query(query)

            if results:
                stats = dict(results[0])
                logger.debug("Preference usage statistics retrieved")
                return stats
            else:
                return {}

        except Exception as e:
            logger.error(f"Failed to get preference usage stats: {e}")
            return {}

    def bulk_set_preferences(
        self, user_id: str, preferences: dict[str, dict[str, Any]]
    ) -> bool:
        """Set multiple preferences for a user in a single transaction.

        Args:
            user_id: User identifier
            preferences: Dict of {key: {"value": val, "type": type, "encrypted": bool}}

        Returns:
            True if all preferences set successfully, False otherwise
        """
        try:
            if not user_id or not preferences:
                logger.error("User ID and preferences are required")
                return False

            with self.transaction() as conn:
                for key, pref_data in preferences.items():
                    value = pref_data.get("value")
                    pref_type = pref_data.get("type", "string")
                    is_encrypted = pref_data.get("encrypted", False)

                    # Convert value based on type
                    if pref_type == "json":
                        stored_value = json.dumps(value)
                    elif pref_type == "boolean":
                        stored_value = str(bool(value)).lower()
                    elif pref_type == "number":
                        stored_value = str(value)
                    else:
                        stored_value = str(value)

                    query = """
                        INSERT OR REPLACE INTO user_preferences (
                            user_id, preference_key, preference_value,
                            preference_type, is_encrypted, updated_at
                        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """

                    conn.execute(
                        query, (user_id, key, stored_value, pref_type, is_encrypted)
                    )

            logger.info(f"Bulk set {len(preferences)} preferences for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to bulk set preferences for user {user_id}: {e}")
            return False


# Factory function for easy instantiation
def get_user_manager(db_path: Optional[str] = None) -> UserManager:
    """Get a user manager instance.

    Args:
        db_path: Path to SQLite database. If None, uses default.

    Returns:
        UserManager instance
    """
    return UserManager(db_path)
