"""DuckDB configuration for Osservatorio ISTAT analytics database.

This module provides configuration settings and utilities for DuckDB,
which is used for high-performance analytics on ISTAT statistical data.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

# from src.utils.logger import get_logger

# logger = get_logger(__name__)

# Base configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "databases"

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)

# DuckDB Configuration
DUCKDB_CONFIG = {
    "database": str(DB_DIR / "osservatorio.duckdb"),
    "read_only": False,
    "threads": int(os.getenv("DUCKDB_THREADS", "4")),
    "memory_limit": os.getenv("DUCKDB_MEMORY_LIMIT", "4GB"),
    "temp_directory": str(DATA_DIR / "temp"),
    "enable_object_cache": True,
    "enable_external_access": False,  # Security: disable external access
    "max_memory": os.getenv("DUCKDB_MAX_MEMORY", "80%"),
    "worker_threads": int(os.getenv("DUCKDB_WORKER_THREADS", "4")),
}

# Connection settings
CONNECTION_CONFIG = {
    "timeout": int(os.getenv("DUCKDB_TIMEOUT", "30")),
    "pool_size": int(os.getenv("DUCKDB_POOL_SIZE", "5")),
    "max_overflow": int(os.getenv("DUCKDB_MAX_OVERFLOW", "10")),
    "pool_timeout": int(os.getenv("DUCKDB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DUCKDB_POOL_RECYCLE", "3600")),
}

# Performance tuning
PERFORMANCE_CONFIG = {
    # Optimizer settings
    "enable_optimizer": True,
    "enable_profiling": os.getenv("DUCKDB_PROFILING", "false").lower() == "true",
    "profile_output": str(DATA_DIR / "logs" / "duckdb_profile.json"),
    # Memory settings
    "buffer_manager_size": os.getenv("DUCKDB_BUFFER_SIZE", "1GB"),
    "checkpoint_threshold": os.getenv("DUCKDB_CHECKPOINT_THRESHOLD", "16MB"),
    # Parallelism
    "enable_parallelism": True,
    "max_threads_per_query": int(os.getenv("DUCKDB_MAX_QUERY_THREADS", "4")),
    # I/O optimization
    "enable_external_sort": True,
    "external_sort_size": os.getenv("DUCKDB_EXTERNAL_SORT_SIZE", "1GB"),
}

# Schema configuration for ISTAT data
SCHEMA_CONFIG = {
    "main_schema": "istat",
    "temp_schema": "temp_istat",
    "analytics_schema": "analytics",
    # Table configurations
    "tables": {
        "datasets": {
            "name": "istat_datasets",
            "partition_by": ["year", "territory_code"],
            "indexes": ["dataset_id", "category", "year", "territory_code"],
        },
        "observations": {
            "name": "istat_observations",
            "partition_by": ["year", "territory_code"],
            "indexes": ["dataset_id", "time_period", "obs_value"],
        },
        "metadata": {
            "name": "dataset_metadata",
            "indexes": ["dataset_id", "category", "priority"],
        },
    },
}

# Data quality settings
QUALITY_CONFIG = {
    "completeness_threshold": float(os.getenv("DUCKDB_COMPLETENESS_THRESHOLD", "0.8")),
    "accuracy_threshold": float(os.getenv("DUCKDB_ACCURACY_THRESHOLD", "0.9")),
    "enable_validation": os.getenv("DUCKDB_ENABLE_VALIDATION", "true").lower()
    == "true",
    "max_null_percentage": float(os.getenv("DUCKDB_MAX_NULL_PERCENTAGE", "0.3")),
}

# Security settings
SECURITY_CONFIG = {
    "enable_unsigned_extensions": False,
    "allow_external_access": False,
    "secure_mode": os.getenv("DUCKDB_SECURE_MODE", "true").lower() == "true",
    "max_expression_depth": int(os.getenv("DUCKDB_MAX_EXPRESSION_DEPTH", "1000")),
}


def get_duckdb_config() -> Dict[str, Any]:
    """Get complete DuckDB configuration dictionary.

    Returns:
        Complete configuration dictionary for DuckDB
    """
    config = {
        **DUCKDB_CONFIG,
        **CONNECTION_CONFIG,
        **PERFORMANCE_CONFIG,
        **SECURITY_CONFIG,
    }

    print(f"DuckDB configuration loaded: database={config['database']}")
    return config


def get_connection_string() -> str:
    """Get DuckDB connection string.

    Returns:
        Connection string for DuckDB database
    """
    db_path = DUCKDB_CONFIG["database"]
    if isinstance(db_path, str):
        return db_path
    return str(db_path)


def get_schema_config() -> Dict[str, Any]:
    """Get schema configuration for ISTAT data structures.

    Returns:
        Schema configuration dictionary
    """
    return SCHEMA_CONFIG


def get_table_config(table_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for specific table.

    Args:
        table_name: Name of the table

    Returns:
        Table configuration or None if not found
    """
    tables = SCHEMA_CONFIG.get("tables", {})
    if not isinstance(tables, dict):
        return None
    for table_key, table_config in tables.items():
        if not isinstance(table_config, dict):
            continue
        if table_config.get("name") == table_name:
            return table_config
    return None


def validate_config() -> bool:
    """Validate DuckDB configuration settings.

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    # Check database path
    db_path_str = DUCKDB_CONFIG["database"]
    if not isinstance(db_path_str, str):
        raise ValueError(f"Database path must be string, got: {type(db_path_str)}")
    db_path = Path(db_path_str)
    if not db_path.parent.exists():
        raise ValueError(f"Database directory does not exist: {db_path.parent}")

    # Check memory limits
    memory_limit = DUCKDB_CONFIG["memory_limit"]
    if not isinstance(memory_limit, str):
        raise ValueError(f"Memory limit must be string, got: {type(memory_limit)}")
    if not memory_limit.endswith(("GB", "MB", "%")):
        raise ValueError(f"Invalid memory limit format: {memory_limit}")

    # Check thread counts
    threads = DUCKDB_CONFIG["threads"]
    if not isinstance(threads, int) or threads <= 0:
        raise ValueError("Thread count must be positive")

    # Check temp directory
    temp_dir_str = DUCKDB_CONFIG["temp_directory"]
    if not isinstance(temp_dir_str, str):
        raise ValueError(f"Temp directory must be string, got: {type(temp_dir_str)}")
    temp_dir = Path(temp_dir_str)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("DuckDB configuration validation successful")
    return True


# Initialize configuration on import
try:
    # validate_config()  # Temporarily disabled for debugging
    print("DuckDB configuration module loaded successfully")
except Exception as e:
    print(f"DuckDB configuration validation failed: {e}")
    # raise  # Don't raise for now
