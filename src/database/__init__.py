"""
Database layer for Osservatorio ISTAT Data Platform.

This module provides the database abstraction layer for the hybrid
SQLite + DuckDB architecture as defined in ADR-002.

Architecture:
- SQLite: Metadata, user preferences, API credentials, audit logging
- DuckDB: ISTAT data analytics, time series, aggregations, performance data
- Unified Repository: Facade pattern combining both databases

Current implementations:
- DuckDB: High-performance analytics database for ISTAT data processing
- SQLite: Lightweight metadata layer for configuration and audit
- Unified Repository: Single interface for both databases
"""

from .duckdb import (
    DUCKDB_CONFIG,
    DuckDBManager,
    DuckDBQueryBuilder,
    SimpleDuckDBAdapter,
    create_adapter,
    create_file_adapter,
    get_duckdb_config,
    get_manager,
)
from .sqlite import (
    MetadataSchema,
    SQLiteMetadataManager,
    UnifiedDataRepository,
    create_metadata_schema,
    get_metadata_manager,
    get_unified_repository,
    reset_metadata_manager,
    reset_unified_repository,
)

__all__ = [
    # DuckDB components
    "DuckDBManager",
    "SimpleDuckDBAdapter",
    "get_manager",
    "reset_manager",
    "create_adapter",
    "create_file_adapter",
    "DuckDBQueryBuilder",
    "get_duckdb_config",
    "DUCKDB_CONFIG",
    # SQLite components
    "SQLiteMetadataManager",
    "get_metadata_manager",
    "reset_metadata_manager",
    "MetadataSchema",
    "create_metadata_schema",
    # Unified Repository
    "UnifiedDataRepository",
    "get_unified_repository",
    "reset_unified_repository",
]

__version__ = "1.0.0"
__author__ = "Osservatorio Development Team"
