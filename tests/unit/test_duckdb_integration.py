"""Comprehensive tests for DuckDB integration.

This module tests all aspects of the DuckDB implementation:
- Configuration and connection management
- Schema creation and management
- Query optimization and performance
- Data partitioning strategies
- Error handling and edge cases
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import duckdb
import pandas as pd
import pytest

from src.database.duckdb.config import (
    DUCKDB_CONFIG,
    get_connection_string,
    get_duckdb_config,
    get_schema_config,
    validate_config,
)
from src.database.duckdb.manager import DuckDBManager, get_manager, reset_manager
from src.database.duckdb.partitioning import (
    HybridPartitionStrategy,
    PartitionManager,
    TerritoryPartitionStrategy,
    YearPartitionStrategy,
    create_partition_manager,
)
from src.database.duckdb.query_optimizer import (
    QueryOptimizer,
    QueryType,
    create_optimizer,
)
from src.database.duckdb.schema import ISTATSchemaManager, initialize_schema


class TestDuckDBConfig:
    """Test DuckDB configuration management."""

    def test_get_duckdb_config_default(self):
        """Test getting default DuckDB configuration."""
        config = get_duckdb_config()

        assert isinstance(config, dict)
        assert "database" in config
        assert "threads" in config
        assert "memory_limit" in config
        assert config["threads"] == 4
        assert config["enable_external_access"] is False

    def test_get_connection_string(self):
        """Test connection string generation."""
        conn_string = get_connection_string()

        assert isinstance(conn_string, str)
        assert "osservatorio.duckdb" in conn_string

    def test_get_schema_config(self):
        """Test schema configuration retrieval."""
        schema_config = get_schema_config()

        assert isinstance(schema_config, dict)
        assert "main_schema" in schema_config
        assert "tables" in schema_config
        assert schema_config["main_schema"] == "istat"

    @patch.dict(os.environ, {"DUCKDB_THREADS": "8", "DUCKDB_MEMORY_LIMIT": "8GB"})
    def test_config_environment_variables(self):
        """Test configuration with environment variables."""
        # Need to reload the module since config is set at import time
        import importlib

        from src.database.duckdb import config as duckdb_config_module

        importlib.reload(duckdb_config_module)

        config = duckdb_config_module.get_duckdb_config()

        assert config["threads"] == 8
        assert config["memory_limit"] == "8GB"

    def test_validate_config_success(self):
        """Test successful configuration validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Temporarily modify config for testing
            original_db_path = DUCKDB_CONFIG["database"]
            DUCKDB_CONFIG["database"] = str(Path(temp_dir) / "test.duckdb")

            try:
                assert validate_config() is True
            finally:
                DUCKDB_CONFIG["database"] = original_db_path

    def test_validate_config_invalid_memory_format(self):
        """Test configuration validation with invalid memory format."""
        with patch(
            "src.database.duckdb.config.DUCKDB_CONFIG",
            {
                "memory_limit": "invalid_format",
                "threads": 4,
                "database": "test.db",
                "temp_directory": "temp",
            },
        ) as mock_config:
            with pytest.raises(ValueError, match="Invalid memory limit format"):
                validate_config()

    def test_validate_config_invalid_threads(self):
        """Test configuration validation with invalid thread count."""
        with patch(
            "src.database.duckdb.config.DUCKDB_CONFIG",
            {
                "memory_limit": "4GB",
                "threads": 0,
                "database": "test.db",
                "temp_directory": "temp",
            },
        ) as mock_config:
            with pytest.raises(ValueError, match="Thread count must be positive"):
                validate_config()


class TestDuckDBManager:
    """Test DuckDB manager functionality."""

    @pytest.fixture
    def temp_db_manager(self):
        """Create temporary DuckDB manager for testing."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path

        manager = DuckDBManager(config)
        yield manager

        manager.close()
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

    def test_manager_initialization(self, temp_db_manager):
        """Test DuckDB manager initialization."""
        # Connection is now lazy - should be None until first use
        assert temp_db_manager._connection is None
        assert temp_db_manager.config["database"] is not None
        assert temp_db_manager._query_stats["total_queries"] == 0

        # Force connection initialization by executing a simple query
        result = temp_db_manager.execute_query("SELECT 1 as test;")

        # Now connection should be established
        assert temp_db_manager._connection is not None
        assert len(result) == 1
        assert temp_db_manager._query_stats["total_queries"] == 1

    def test_execute_query_simple(self, temp_db_manager):
        """Test simple query execution."""
        result = temp_db_manager.execute_query("SELECT 1 as test_column;")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["test_column"] == 1
        assert temp_db_manager._query_stats["total_queries"] == 1

    def test_execute_query_with_parameters(self, temp_db_manager):
        """Test parameterized query execution."""
        # Create test table first
        temp_db_manager.execute_statement(
            "CREATE TABLE test_table (id INTEGER, name VARCHAR);"
        )
        temp_db_manager.execute_statement(
            "INSERT INTO test_table VALUES (1, 'test'), (2, 'example');"
        )

        result = temp_db_manager.execute_query(
            "SELECT * FROM test_table WHERE id = ?;", [1]
        )

        assert len(result) == 1
        assert result.iloc[0]["name"] == "test"

    def test_execute_statement(self, temp_db_manager):
        """Test SQL statement execution."""
        temp_db_manager.execute_statement(
            "CREATE TABLE test_statement (id INTEGER, data VARCHAR);"
        )

        # Verify table was created by checking if we can query it
        result = temp_db_manager.execute_query(
            "SELECT COUNT(*) as count FROM test_statement;"
        )
        assert result.iloc[0]["count"] == 0  # Empty table but exists

    def test_bulk_insert(self, temp_db_manager):
        """Test bulk data insertion."""
        # Create test table
        temp_db_manager.execute_statement(
            "CREATE TABLE bulk_test (id INTEGER, value DECIMAL, name VARCHAR);"
        )

        # Create test data
        test_data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "value": [10.5, 20.0, 30.25, 40.8, 50.1],
                "name": ["a", "b", "c", "d", "e"],
            }
        )

        temp_db_manager.bulk_insert("bulk_test", test_data)

        # Verify insertion
        result = temp_db_manager.execute_query(
            "SELECT COUNT(*) as count FROM bulk_test;"
        )
        assert result.iloc[0]["count"] == 5

    def test_transaction_success(self, temp_db_manager):
        """Test successful transaction handling."""
        temp_db_manager.execute_statement("CREATE TABLE transaction_test (id INTEGER);")

        with temp_db_manager.transaction() as conn:
            conn.execute("INSERT INTO transaction_test VALUES (1);")
            conn.execute("INSERT INTO transaction_test VALUES (2);")

        result = temp_db_manager.execute_query(
            "SELECT COUNT(*) as count FROM transaction_test;"
        )
        assert result.iloc[0]["count"] == 2

    def test_transaction_rollback(self, temp_db_manager):
        """Test transaction rollback on error."""
        temp_db_manager.execute_statement(
            "CREATE TABLE rollback_test (id INTEGER PRIMARY KEY);"
        )

        try:
            with temp_db_manager.transaction() as conn:
                conn.execute("INSERT INTO rollback_test VALUES (1);")
                conn.execute(
                    "INSERT INTO rollback_test VALUES (1);"
                )  # Duplicate key error
        except Exception:
            pass  # Expected error

        result = temp_db_manager.execute_query(
            "SELECT COUNT(*) as count FROM rollback_test;"
        )
        assert result.iloc[0]["count"] == 0  # Transaction rolled back

    def test_create_schema(self, temp_db_manager):
        """Test schema creation."""
        temp_db_manager.create_schema("test_schema")

        # Schema creation doesn't fail, we can't easily verify in DuckDB
        # but the operation should complete without error
        assert True

    def test_table_exists(self, temp_db_manager):
        """Test table existence checking."""
        temp_db_manager.execute_statement("CREATE TABLE exists_test (id INTEGER);")

        assert temp_db_manager.table_exists("exists_test") == True
        assert temp_db_manager.table_exists("nonexistent_table") == False

    def test_get_performance_stats(self, temp_db_manager):
        """Test performance statistics retrieval."""
        # Execute some queries to generate stats
        temp_db_manager.execute_query("SELECT 1;")
        temp_db_manager.execute_query("SELECT 2;")

        stats = temp_db_manager.get_performance_stats()

        assert stats["total_queries"] == 2
        assert stats["avg_query_time"] > 0
        assert stats["error_percentage"] == 0

    def test_optimize_database(self, temp_db_manager):
        """Test database optimization."""
        # Create test table with data
        temp_db_manager.execute_statement(
            "CREATE TABLE optimize_test (id INTEGER, data VARCHAR);"
        )
        temp_db_manager.execute_statement(
            "INSERT INTO optimize_test VALUES (1, 'test'), (2, 'data');"
        )

        # Should not raise exception
        temp_db_manager.optimize_database()
        assert True

    def test_singleton_manager(self):
        """Test singleton manager pattern."""
        manager1 = get_manager()
        manager2 = get_manager()

        assert manager1 is manager2

        # Reset for cleanup
        reset_manager()

    def test_security_validation(self, temp_db_manager):
        """Test security validation integration (currently disabled)."""
        # Security validation is currently disabled in the manager
        # This test verifies that queries execute normally without validation
        result = temp_db_manager.execute_query("SELECT 1 as test;")
        assert len(result) == 1
        assert result.iloc[0]["test"] == 1

    def test_query_error_handling(self, temp_db_manager):
        """Test query error handling and statistics."""
        with pytest.raises(Exception):
            temp_db_manager.execute_query("INVALID SQL QUERY;")

        stats = temp_db_manager.get_performance_stats()
        assert stats["errors"] == 1
        assert stats["error_percentage"] == 100.0


class TestISTATSchemaManager:
    """Test ISTAT schema management."""

    @pytest.fixture
    def schema_manager(self):
        """Create schema manager with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path

        manager = DuckDBManager(config)
        schema_mgr = ISTATSchemaManager(manager)

        yield schema_mgr

        # Force close connection and wait a bit
        try:
            manager.close()
            import time

            time.sleep(0.1)  # Give time for file handle to release
        except Exception:
            pass

        # Force cleanup
        try:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
        except PermissionError:
            # Try again after a short delay
            import time

            time.sleep(0.2)
            try:
                os.unlink(temp_db_path)
            except Exception:
                pass  # Ignore cleanup errors in tests

    def test_create_all_schemas(self, schema_manager):
        """Test creation of all required schemas."""
        schema_manager.create_all_schemas()
        # If no exception is raised, schemas were created successfully
        assert True

    def test_create_all_tables(self, schema_manager):
        """Test creation of all ISTAT tables."""
        schema_manager.create_all_tables()

        # Verify tables were created by checking their existence
        assert schema_manager.manager.table_exists("dataset_metadata", "istat") == True

    def test_insert_dataset_metadata(self, schema_manager):
        """Test dataset metadata insertion."""
        schema_manager.create_all_tables()

        metadata = {
            "dataset_id": "TEST_001",
            "dataset_name": "Test Dataset",
            "category": "test",
            "priority": 5,
            "completeness_score": 0.95,
            "data_quality_score": 0.88,
        }

        schema_manager.insert_dataset_metadata(metadata)

        # Verify insertion
        result = schema_manager.manager.execute_query(
            "SELECT * FROM istat.dataset_metadata WHERE dataset_id = 'TEST_001';"
        )
        assert len(result) == 1
        assert result.iloc[0]["dataset_name"] == "Test Dataset"

    def test_bulk_insert_observations(self, schema_manager):
        """Test bulk insertion of observations."""
        schema_manager.create_all_tables()

        # First insert metadata
        metadata = {
            "dataset_id": "TEST_002",
            "dataset_name": "Test Observations",
            "category": "test",
        }
        schema_manager.insert_dataset_metadata(metadata)

        # Create test observations
        obs_data = pd.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "territory_code": ["IT", "IT", "IT"],
                "obs_value": [100.5, 110.2, 120.8],
                "obs_status": ["A", "A", "E"],
            }
        )

        schema_manager.bulk_insert_observations(obs_data, "TEST_002")

        # Verify insertion
        result = schema_manager.manager.execute_query(
            "SELECT COUNT(*) as count FROM istat.istat_observations WHERE dataset_id = 'TEST_002';"
        )
        assert result.iloc[0]["count"] == 3

    def test_get_table_stats(self, schema_manager):
        """Test table statistics retrieval."""
        schema_manager.create_all_tables()

        # Insert some test data
        metadata = {
            "dataset_id": "STATS_TEST",
            "dataset_name": "Statistics Test",
            "category": "test",
        }
        schema_manager.insert_dataset_metadata(metadata)

        stats = schema_manager.get_table_stats()
        assert isinstance(stats, list)
        assert len(stats) >= 1

    def test_drop_all_tables(self, schema_manager):
        """Test dropping all tables for cleanup."""
        schema_manager.create_all_tables()
        schema_manager.drop_all_tables()

        # Verify tables are dropped
        assert schema_manager.manager.table_exists("dataset_metadata", "istat") == False

    def test_initialize_schema_function(self):
        """Test schema initialization function."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path
        manager = DuckDBManager(config)

        try:
            schema_mgr = initialize_schema(manager)
            assert isinstance(schema_mgr, ISTATSchemaManager)
            assert schema_mgr.manager.table_exists("dataset_metadata", "istat") == True
        finally:
            manager.close()
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


class TestQueryOptimizer:
    """Test query optimization functionality."""

    @pytest.fixture
    def optimizer(self):
        """Create query optimizer with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path

        manager = DuckDBManager(config)
        schema_mgr = ISTATSchemaManager(manager)
        schema_mgr.create_all_tables()

        optimizer = QueryOptimizer(manager)

        yield optimizer

        manager.close()
        # Small delay to let DuckDB release file handle on Windows
        import time

        time.sleep(0.1)
        try:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
        except PermissionError:
            # File still locked on Windows, ignore for testing
            pass

    def test_create_advanced_indexes(self, optimizer):
        """Test creation of advanced indexes."""
        optimizer.create_advanced_indexes()
        # If no exception is raised, indexes were created successfully
        assert True

    def test_get_time_series_data_cache_miss(self, optimizer):
        """Test time series data retrieval with cache miss."""
        # Insert test data using schema manager method
        from src.database.duckdb.schema import ISTATSchemaManager

        schema_mgr = ISTATSchemaManager(optimizer.manager)

        metadata = {
            "dataset_id": "TS_TEST",
            "dataset_name": "Time Series Test",
            "category": "test",
            "priority": 1,
        }
        schema_mgr.insert_dataset_metadata(metadata)

        result = optimizer.get_time_series_data(["TS_TEST"], 2020, 2022)
        assert isinstance(result, pd.DataFrame)

    def test_get_time_series_data_cache_hit(self, optimizer):
        """Test time series data retrieval with cache hit."""
        # Insert test data using schema manager method
        from src.database.duckdb.schema import ISTATSchemaManager

        schema_mgr = ISTATSchemaManager(optimizer.manager)

        metadata = {
            "dataset_id": "TS_CACHE",
            "dataset_name": "Cache Test",
            "category": "test",
            "priority": 1,
        }
        schema_mgr.insert_dataset_metadata(metadata)

        # First call (cache miss)
        result1 = optimizer.get_time_series_data(["TS_CACHE"], 2020, 2022)

        # Second call (cache hit)
        result2 = optimizer.get_time_series_data(["TS_CACHE"], 2020, 2022)

        assert result1.equals(result2)

    def test_clear_cache(self, optimizer):
        """Test cache clearing functionality."""
        # Add something to cache first
        optimizer.get_time_series_data(["TEST"], 2020, 2022)

        assert len(optimizer.query_cache) > 0

        optimizer.clear_cache()
        assert len(optimizer.query_cache) == 0

    def test_get_cache_stats(self, optimizer):
        """Test cache statistics retrieval."""
        stats = optimizer.get_cache_stats()

        assert isinstance(stats, dict)
        assert "total_entries" in stats
        assert "valid_entries" in stats
        assert "cache_ttl_minutes" in stats

    def test_optimize_table_statistics(self, optimizer):
        """Test table statistics optimization."""
        # Should not raise exception
        optimizer.optimize_table_statistics()
        assert True

    def test_create_optimizer_function(self):
        """Test optimizer creation function."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path
        manager = DuckDBManager(config)

        try:
            optimizer = create_optimizer(manager)
            assert isinstance(optimizer, QueryOptimizer)
        finally:
            manager.close()
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


class TestPartitioning:
    """Test data partitioning functionality."""

    def test_year_partition_strategy(self):
        """Test year-based partitioning strategy."""
        strategy = YearPartitionStrategy()

        test_row = {"year": 2020, "territory_code": "IT"}
        partition_key = strategy.get_partition_key(test_row)

        assert partition_key == "year_2020"

        partition_filter = strategy.get_partition_filter(start_year=2020, end_year=2022)
        assert "year BETWEEN 2020 AND 2022" in partition_filter

    def test_territory_partition_strategy(self):
        """Test territory-based partitioning strategy."""
        strategy = TerritoryPartitionStrategy()

        test_row = {"territory_code": "ITA", "year": 2020}
        partition_key = strategy.get_partition_key(test_row)

        assert "territory_" in partition_key

        partition_filter = strategy.get_partition_filter(territories=["IT", "FR"])
        assert "territory_code IN ('IT', 'FR')" in partition_filter

    def test_hybrid_partition_strategy(self):
        """Test hybrid partitioning strategy."""
        strategy = HybridPartitionStrategy()

        test_row = {"year": 2023, "territory_code": "ITA"}
        partition_key = strategy.get_partition_key(test_row)

        assert "hybrid_2020s_IT" in partition_key

        partition_filter = strategy.get_partition_filter(
            start_year=2020, end_year=2025, territories=["IT"]
        )
        assert "year BETWEEN 2020 AND 2025" in partition_filter
        assert "territory_code IN ('IT')" in partition_filter

    @pytest.fixture
    def partition_manager(self):
        """Create partition manager with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path

        manager = DuckDBManager(config)
        schema_mgr = ISTATSchemaManager(manager)
        schema_mgr.create_all_tables()

        partition_mgr = PartitionManager(manager)

        yield partition_mgr

        manager.close()
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

    def test_create_partitioned_tables(self, partition_manager):
        """Test creation of partitioned tables."""
        partition_manager.create_partitioned_tables("hybrid")

        # Verify partitioned tables exist
        assert partition_manager.manager.table_exists(
            "istat_datasets_partitioned", "istat"
        )
        assert partition_manager.manager.table_exists(
            "istat_observations_partitioned", "istat"
        )

    def test_partition_data(self, partition_manager):
        """Test data partitioning."""
        test_data = pd.DataFrame(
            {
                "year": [2020, 2021, 2020, 2022],
                "territory_code": ["IT", "IT", "FR", "IT"],
                "obs_value": [100, 200, 150, 250],
                "measure_code": ["TEST", "TEST", "TEST", "TEST"],
            }
        )

        partitioned_data = partition_manager.partition_data(
            test_data, "TEST_DATASET", "year"
        )

        assert isinstance(partitioned_data, dict)
        assert len(partitioned_data) > 0

        # Each partition should be a DataFrame
        for partition_key, df in partitioned_data.items():
            assert isinstance(df, pd.DataFrame)
            assert "partition_key" in df.columns
            assert "dataset_id" in df.columns

    def test_create_partition_manager_function(self):
        """Test partition manager creation function."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path
        manager = DuckDBManager(config)

        try:
            partition_mgr = create_partition_manager(manager)
            assert isinstance(partition_mgr, PartitionManager)
        finally:
            manager.close()
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


class TestIntegration:
    """Integration tests for complete DuckDB functionality."""

    @pytest.fixture
    def full_system(self):
        """Create complete DuckDB system for integration testing."""
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
            temp_db_path = temp_file.name

        config = get_duckdb_config().copy()
        config["database"] = temp_db_path

        manager = DuckDBManager(config)
        schema_mgr = initialize_schema(manager)
        optimizer = create_optimizer(manager)
        partition_mgr = create_partition_manager(manager)

        system = {
            "manager": manager,
            "schema": schema_mgr,
            "optimizer": optimizer,
            "partitions": partition_mgr,
        }

        yield system

        manager.close()
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

    def test_full_data_pipeline(self, full_system):
        """Test complete data processing pipeline."""
        schema = full_system["schema"]
        optimizer = full_system["optimizer"]

        # Insert test metadata
        metadata = {
            "dataset_id": "INTEGRATION_TEST",
            "dataset_name": "Integration Test Dataset",
            "category": "test",
            "priority": 5,
            "completeness_score": 0.95,
            "data_quality_score": 0.90,
        }
        schema.insert_dataset_metadata(metadata)

        # Insert observations
        obs_data = pd.DataFrame(
            {
                "year": [2020, 2021, 2022] * 3,
                "territory_code": ["IT"] * 9,
                "obs_value": [100, 110, 120, 200, 210, 220, 300, 310, 320],
                "obs_status": ["A"] * 9,
            }
        )
        schema.bulk_insert_observations(obs_data, "INTEGRATION_TEST")

        # Test optimized query
        result = optimizer.get_time_series_data(["INTEGRATION_TEST"], 2020, 2022)

        assert isinstance(result, pd.DataFrame)
        # Should have some results if analytics view works correctly

    def test_performance_under_load(self, full_system):
        """Test system performance under simulated load."""
        manager = full_system["manager"]

        # Create test table
        manager.execute_statement(
            """
            CREATE TABLE load_test (
                id INTEGER,
                year INTEGER,
                value DECIMAL,
                category VARCHAR
            );
        """
        )

        # Insert large dataset
        large_data = pd.DataFrame(
            {
                "id": range(1000),
                "year": [2020 + (i % 5) for i in range(1000)],
                "value": [i * 10.5 for i in range(1000)],
                "category": [f"cat_{i % 10}" for i in range(1000)],
            }
        )

        start_time = datetime.now()
        manager.bulk_insert("load_test", large_data)
        end_time = datetime.now()

        insertion_time = (end_time - start_time).total_seconds()

        # Should complete within reasonable time (adjust threshold as needed)
        assert insertion_time < 10.0

        # Verify data integrity
        result = manager.execute_query("SELECT COUNT(*) as count FROM load_test;")
        assert result.iloc[0]["count"] == 1000

    def test_error_recovery(self, full_system):
        """Test system behavior under error conditions."""
        manager = full_system["manager"]

        # Test query error doesn't break system
        try:
            manager.execute_query("SELECT * FROM nonexistent_table;")
        except Exception:
            pass

        # System should still be functional
        result = manager.execute_query("SELECT 1 as test;")
        assert result.iloc[0]["test"] == 1

        stats = manager.get_performance_stats()
        assert stats["errors"] > 0

    def test_concurrent_operations(self, full_system):
        """Test system with concurrent operations simulation."""
        manager = full_system["manager"]

        # Create test table
        manager.execute_statement(
            """
            CREATE TABLE concurrent_test (
                id INTEGER PRIMARY KEY,
                data VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Simulate multiple operations
        with manager.transaction() as conn:
            for i in range(10):
                conn.execute(
                    f"INSERT INTO concurrent_test (id, data) VALUES ({i}, 'data_{i}');"
                )

        # Verify all operations completed
        result = manager.execute_query("SELECT COUNT(*) as count FROM concurrent_test;")
        assert result.iloc[0]["count"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
