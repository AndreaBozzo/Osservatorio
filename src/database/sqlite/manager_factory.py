"""
SQLite Manager Factory - Centralized manager instantiation

Provides a factory pattern for creating and managing SQLite manager instances
with proper configuration and singleton behavior.
"""

from typing import Optional

from src.utils.logger import get_logger

from .audit_manager import AuditManager
from .base_manager import BaseSQLiteManager
from .config_manager import ConfigurationManager
from .dataset_manager import DatasetManager
from .user_manager import UserManager

logger = get_logger(__name__)


class SQLiteManagerFactory:
    """Factory for creating and managing SQLite manager instances."""

    _instances = {}
    _default_db_path = None

    @classmethod
    def set_default_db_path(cls, db_path: str) -> None:
        """Set the default database path for all managers.

        Args:
            db_path: Default database path
        """
        cls._default_db_path = db_path
        logger.info(f"Default database path set to: {db_path}")

    @classmethod
    def get_dataset_manager(cls, db_path: Optional[str] = None) -> DatasetManager:
        """Get a dataset manager instance.

        Args:
            db_path: Database path (uses default if None)

        Returns:
            DatasetManager instance
        """
        effective_path = (
            db_path or cls._default_db_path or "data/databases/osservatorio_metadata.db"
        )
        cache_key = f"dataset_{effective_path}"

        if cache_key not in cls._instances:
            cls._instances[cache_key] = DatasetManager(effective_path)
            logger.debug(f"Created new DatasetManager instance: {effective_path}")

        return cls._instances[cache_key]

    @classmethod
    def get_configuration_manager(
        cls, db_path: Optional[str] = None
    ) -> ConfigurationManager:
        """Get a configuration manager instance.

        Args:
            db_path: Database path (uses default if None)

        Returns:
            ConfigurationManager instance
        """
        effective_path = (
            db_path or cls._default_db_path or "data/databases/osservatorio_metadata.db"
        )
        cache_key = f"config_{effective_path}"

        if cache_key not in cls._instances:
            cls._instances[cache_key] = ConfigurationManager(effective_path)
            logger.debug(f"Created new ConfigurationManager instance: {effective_path}")

        return cls._instances[cache_key]

    @classmethod
    def get_user_manager(cls, db_path: Optional[str] = None) -> UserManager:
        """Get a user manager instance.

        Args:
            db_path: Database path (uses default if None)

        Returns:
            UserManager instance
        """
        effective_path = (
            db_path or cls._default_db_path or "data/databases/osservatorio_metadata.db"
        )
        cache_key = f"user_{effective_path}"

        if cache_key not in cls._instances:
            cls._instances[cache_key] = UserManager(effective_path)
            logger.debug(f"Created new UserManager instance: {effective_path}")

        return cls._instances[cache_key]

    @classmethod
    def get_audit_manager(cls, db_path: Optional[str] = None) -> AuditManager:
        """Get an audit manager instance.

        Args:
            db_path: Database path (uses default if None)

        Returns:
            AuditManager instance
        """
        effective_path = (
            db_path or cls._default_db_path or "data/databases/osservatorio_metadata.db"
        )
        cache_key = f"audit_{effective_path}"

        if cache_key not in cls._instances:
            cls._instances[cache_key] = AuditManager(effective_path)
            logger.debug(f"Created new AuditManager instance: {effective_path}")

        return cls._instances[cache_key]

    @classmethod
    def get_all_managers(
        cls, db_path: Optional[str] = None
    ) -> dict[str, BaseSQLiteManager]:
        """Get all manager instances.

        Args:
            db_path: Database path (uses default if None)

        Returns:
            Dictionary of manager instances
        """
        return {
            "dataset": cls.get_dataset_manager(db_path),
            "config": cls.get_configuration_manager(db_path),
            "user": cls.get_user_manager(db_path),
            "audit": cls.get_audit_manager(db_path),
        }

    @classmethod
    def close_all_connections(cls) -> None:
        """Close all database connections for cleanup."""
        for manager in cls._instances.values():
            try:
                manager.close_connections()
            except Exception as e:
                logger.warning(f"Error closing manager connections: {e}")

        logger.info(f"Closed connections for {len(cls._instances)} manager instances")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the manager instance cache."""
        cls.close_all_connections()
        cls._instances.clear()
        logger.info("Manager factory cache cleared")

    @classmethod
    def get_cache_info(cls) -> dict[str, any]:
        """Get information about cached manager instances.

        Returns:
            Dictionary with cache information
        """
        return {
            "cached_instances": len(cls._instances),
            "instance_types": [key.split("_")[0] for key in cls._instances.keys()],
            "default_db_path": cls._default_db_path,
        }


# Convenience functions for direct access
def get_dataset_manager(db_path: Optional[str] = None) -> DatasetManager:
    """Get a dataset manager instance."""
    return SQLiteManagerFactory.get_dataset_manager(db_path)


def get_configuration_manager(db_path: Optional[str] = None) -> ConfigurationManager:
    """Get a configuration manager instance."""
    return SQLiteManagerFactory.get_configuration_manager(db_path)


def get_user_manager(db_path: Optional[str] = None) -> UserManager:
    """Get a user manager instance."""
    return SQLiteManagerFactory.get_user_manager(db_path)


def get_audit_manager(db_path: Optional[str] = None) -> AuditManager:
    """Get an audit manager instance."""
    return SQLiteManagerFactory.get_audit_manager(db_path)


def get_all_managers(db_path: Optional[str] = None) -> dict[str, BaseSQLiteManager]:
    """Get all manager instances."""
    return SQLiteManagerFactory.get_all_managers(db_path)
