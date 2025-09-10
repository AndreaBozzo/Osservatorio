"""DuckDB implementation for high-performance ISTAT data analytics.

This module provides DuckDB-based storage and querying capabilities
optimized for statistical data analysis and reporting.
"""

from .config import (
    DUCKDB_CONFIG,
    PERFORMANCE_CONFIG,
    SCHEMA_CONFIG,
    get_connection_string,
    get_duckdb_config,
    get_schema_config,
    get_table_config,
    validate_config,
)
from .manager import DuckDBManager, get_manager
from .query_builder import (
    AggregateFunction,
    DuckDBQueryBuilder,
    FilterCondition,
    FilterOperator,
    QueryCache,
    QueryType,
    create_query_builder,
    get_global_cache,
)
from .schema import ISTATSchemaManager, initialize_schema

# Import working simple adapter
from .simple_adapter import (
    SimpleDuckDBAdapter,
    create_adapter,
    create_file_adapter,
    create_temp_adapter,
)

__all__ = [
    # Configuration
    "get_duckdb_config",
    "get_connection_string",
    "get_schema_config",
    "get_table_config",
    # "validate_config",  # Temporarily disabled
    "DUCKDB_CONFIG",
    "SCHEMA_CONFIG",
    "PERFORMANCE_CONFIG",
    # Working simple adapter
    "SimpleDuckDBAdapter",
    "create_adapter",
    "create_file_adapter",
    "create_temp_adapter",
    # Core components
    "DuckDBManager",
    "get_manager",
    "ISTATSchemaManager",
    "initialize_schema",
    # Query Builder
    "DuckDBQueryBuilder",
    "QueryCache",
    "FilterCondition",
    "FilterOperator",
    "QueryType",
    "AggregateFunction",
    "create_query_builder",
    "get_global_cache",
]
