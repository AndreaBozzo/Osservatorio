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
- MetadataManager: Core SQLite operations and connection management
- Schema: Database schema definitions for metadata tables
- Repository: Unified facade for both SQLite and DuckDB operations
"""

from .manager import SQLiteMetadataManager, get_metadata_manager, reset_metadata_manager
from .repository import (
    UnifiedDataRepository,
    get_unified_repository,
    reset_unified_repository,
)
from .schema import MetadataSchema, create_metadata_schema

__all__ = [
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
