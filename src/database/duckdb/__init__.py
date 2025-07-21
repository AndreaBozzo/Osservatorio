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

# Import working simple adapter
from .simple_adapter import (
    SimpleDuckDBAdapter,
    create_adapter,
    create_file_adapter,
    create_temp_adapter,
)

# from .manager import DuckDBManager, get_manager, reset_manager
# from .schema import ISTATSchemaManager, initialize_schema
# from .query_optimizer import QueryOptimizer, QueryType, create_optimizer
# from .partitioning import (
#     PartitionManager, YearPartitionStrategy, TerritoryPartitionStrategy,
#     HybridPartitionStrategy, create_partition_manager
# )


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
]
