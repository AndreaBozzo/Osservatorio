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
from .audit_manager import AuditManager, get_audit_manager
from .base_manager import BaseSQLiteManager
from .config_manager import ConfigurationManager, get_configuration_manager
from .dataset_manager import DatasetManager, get_dataset_manager

# Legacy imports (for backward compatibility)
from .manager import SQLiteMetadataManager, get_metadata_manager, reset_metadata_manager
from .manager_factory import (
    SQLiteManagerFactory,
    get_all_managers,
)
from .manager_factory import get_audit_manager as factory_get_audit_manager
from .manager_factory import (
    get_configuration_manager as factory_get_configuration_manager,
)
from .manager_factory import get_dataset_manager as factory_get_dataset_manager
from .manager_factory import get_user_manager as factory_get_user_manager
from .repository import (
    UnifiedDataRepository,
    get_unified_repository,
    reset_unified_repository,
)
from .schema import MetadataSchema, create_metadata_schema
from .user_manager import UserManager, get_user_manager

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
