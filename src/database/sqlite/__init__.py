"""
SQLite Metadata Layer for Osservatorio ISTAT Data Platform

This module implements the SQLite portion of the hybrid SQLite + DuckDB architecture
as defined in ADR-002. It handles metadata, configuration, authentication, and audit
logging while DuckDB handles analytics and ISTAT data processing.

Architecture:
- SQLite: Metadata, user preferences, API keys, audit logging
- DuckDB: ISTAT analytics, time series, aggregations, performance data
- Unified Repository: Facade pattern combining both databases

Key Components:
- Specialized Managers: DatasetManager, ConfigurationManager, UserManager, AuditManager
- MetadataManager: Legacy monolithic manager (deprecated)
- Schema: Database schema definitions for metadata tables
- Repository: Unified facade for both SQLite and DuckDB operations
- Factory: Centralized manager instantiation and lifecycle management
"""

# New specialized managers (recommended)
from .audit_manager import AuditManager
from .base_manager import BaseSQLiteManager
from .config_manager import ConfigurationManager
from .dataset_manager import DatasetManager

# Legacy imports (for backward compatibility)
from .manager import SQLiteMetadataManager, get_metadata_manager, reset_metadata_manager

# Factory functions (recommended for getting instances)
from .manager_factory import (
    SQLiteManagerFactory,
    get_all_managers,
    get_audit_manager,
    get_configuration_manager,
    get_dataset_manager,
    get_user_manager,
)
from .repository import (
    UnifiedDataRepository,
    get_unified_repository,
    reset_unified_repository,
)
from .schema import MetadataSchema, create_metadata_schema
from .user_manager import UserManager

__all__ = [
    # New specialized managers
    "BaseSQLiteManager",
    "DatasetManager",
    "ConfigurationManager",
    "UserManager",
    "AuditManager",
    "SQLiteManagerFactory",
    "get_dataset_manager",
    "get_configuration_manager",
    "get_user_manager",
    "get_audit_manager",
    "get_all_managers",
    # Legacy components (deprecated but maintained for compatibility)
    "SQLiteMetadataManager",
    "get_metadata_manager",
    "reset_metadata_manager",
    "MetadataSchema",
    "create_metadata_schema",
    "UnifiedDataRepository",
    "get_unified_repository",
    "reset_unified_repository",
]

__version__ = "1.0.0"
__author__ = "Andrea Bozzo"
__description__ = "SQLite metadata layer for hybrid SQLite + DuckDB architecture"
