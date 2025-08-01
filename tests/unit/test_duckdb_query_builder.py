"""Comprehensive unit tests for DuckDB Query Builder.

Tests cover:
- Fluent interface functionality
- SQL generation and validation
- Query caching with TTL
- ISTAT-specific methods
- Error handling and validation
- Performance characteristics
"""
import os
import tempfile
import time
from unittest.mock import Mock

import pandas as pd
import pytest

from src.database.duckdb.manager import DuckDBManager
from src.database.duckdb.query_builder import (
    AggregateFunction,
    DuckDBQueryBuilder,
    FilterCondition,
    FilterOperator,
    QueryCache,
    QueryType,
    create_query_builder,
    get_global_cache,
)


class TestFilterCondition:
    """Test FilterCondition class functionality."""

    def test_simple_equality_condition(self):
        """Test simple equality condition SQL generation."""
        condition = FilterCondition("age", FilterOperator.EQ, 25)
        sql, params = condition.to_sql()

        assert sql == "age = ?"
        assert params == [25]

    def test_in_condition(self):
        """Test IN condition SQL generation."""
        condition = FilterCondition("category", FilterOperator.IN, ["A", "B", "C"])
        sql, params = condition.to_sql()

        assert sql == "category IN (?, ?, ?)"
        assert params == ["A", "B", "C"]

    def test_between_condition(self):
        """Test BETWEEN condition SQL generation."""
        condition = FilterCondition("year", FilterOperator.BETWEEN, [2020, 2022])
        sql, params = condition.to_sql()

        assert sql == "year BETWEEN ? AND ?"
        assert params == [2020, 2022]

    def test_null_conditions(self):
        """Test IS NULL and IS NOT NULL conditions."""
        null_condition = FilterCondition("value", FilterOperator.IS_NULL, None)
        sql, params = null_condition.to_sql()
        assert sql == "value IS NULL"
        assert params == []

        not_null_condition = FilterCondition("value", FilterOperator.IS_NOT_NULL, None)
        sql, params = not_null_condition.to_sql()
        assert sql == "value IS NOT NULL"
        assert params == []

    def test_between_validation(self):
        """Test BETWEEN condition validation."""
        with pytest.raises(
            ValueError, match="BETWEEN operator requires a list/tuple with 2 values"
        ):
            condition = FilterCondition("year", FilterOperator.BETWEEN, [2020])
            condition.to_sql()

    def test_in_validation(self):
        """Test IN condition validation."""
        with pytest.raises(ValueError, match="IN operator requires a list/tuple"):
            condition = FilterCondition("category", FilterOperator.IN, "single_value")
            condition.to_sql()


class TestQueryCache:
    """Test QueryCache functionality."""

    def test_basic_caching(self):
        """Test basic cache put/get operations."""
        cache = QueryCache(default_ttl=60)
        df = pd.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})

        # Cache miss
        result = cache.get("test_key")
        assert result is None

        # Put and get
        cache.put("test_key", df)
        result = cache.get("test_key")

        assert result is not None
        pd.testing.assert_frame_equal(result, df)

    def test_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = QueryCache(default_ttl=1)  # 1 second TTL
        df = pd.DataFrame({"id": [1, 2, 3]})

        cache.put("test_key", df)

        # Should be available immediately
        result = cache.get("test_key")
        assert result is not None

        # Wait for expiration
        time.sleep(1.1)
        result = cache.get("test_key")
        assert result is None

    def test_cache_eviction(self):
        """Test LRU cache eviction."""
        cache = QueryCache(default_ttl=60, max_size=2)
        df1 = pd.DataFrame({"id": [1]})
        df2 = pd.DataFrame({"id": [2]})
        df3 = pd.DataFrame({"id": [3]})

        cache.put("key1", df1)
        cache.put("key2", df2)

        # Both should be available
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None

        # Access key1 to make it more recently used
        cache.get("key1")

        # Add third item, should evict key2 (least recently used)
        cache.put("key3", df3)

        assert cache.get("key1") is not None  # Still available
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is not None  # New item

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        cache = QueryCache()
        df = pd.DataFrame({"id": [1]})

        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["cache_size"] == 0

        # Cache miss
        cache.get("missing_key")
        stats = cache.get_stats()
        assert stats["misses"] == 1

        # Cache put and hit
        cache.put("test_key", df)
        cache.get("test_key")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["cache_size"] == 1
        assert stats["hit_rate_percent"] == 50.0  # 1 hit out of 2 total requests


class TestDuckDBQueryBuilder:
    """Test DuckDBQueryBuilder functionality."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock DuckDB manager."""
        manager = Mock(spec=DuckDBManager)
        manager.execute_query.return_value = pd.DataFrame(
            {"id": [1, 2, 3], "value": [10, 20, 30]}
        )
        return manager

    @pytest.fixture
    def query_builder(self, mock_manager):
        """Create a query builder with mocked manager."""
        cache = QueryCache()
        return DuckDBQueryBuilder(manager=mock_manager, cache=cache)

    def test_basic_select_query(self, query_builder):
        """Test basic SELECT query building."""
        sql, params = query_builder.select("id", "name").from_table("users").build_sql()

        expected_sql = "SELECT id, name\nFROM users"
        assert sql == expected_sql
        assert params == []

    def test_select_with_where(self, query_builder):
        """Test SELECT with WHERE conditions."""
        sql, params = (
            query_builder.select("*")
            .from_table("users")
            .where("age", FilterOperator.GT, 18)
            .where("status", FilterOperator.EQ, "active")
            .build_sql()
        )

        expected_sql = "SELECT *\nFROM users\nWHERE age > ? AND status = ?"
        assert sql == expected_sql
        assert params == [18, "active"]

    def test_select_with_joins(self, query_builder):
        """Test SELECT with JOIN clauses."""
        sql, params = (
            query_builder.select("u.name", "p.title")
            .from_table("users u")
            .join("posts p", "u.id = p.user_id", "LEFT")
            .build_sql()
        )

        expected_sql = "SELECT u.name, p.title\nFROM users u\nLEFT JOIN posts p ON u.id = p.user_id"
        assert sql == expected_sql
        assert params == []

    def test_aggregate_query(self, query_builder):
        """Test aggregate query with GROUP BY and HAVING."""
        sql, params = (
            query_builder.select(
                "category", "COUNT(*) as count", "AVG(value) as avg_value"
            )
            .from_table("data")
            .where("year", FilterOperator.EQ, 2023)
            .group_by("category")
            .having("COUNT(*)", FilterOperator.GT, 10)
            .order_by("avg_value", "DESC")
            .build_sql()
        )

        expected_lines = [
            "SELECT category, COUNT(*) as count, AVG(value) as avg_value",
            "FROM data",
            "WHERE year = ?",
            "GROUP BY category",
            "HAVING COUNT(*) > ?",
            "ORDER BY avg_value DESC",
        ]
        expected_sql = "\n".join(expected_lines)

        assert sql == expected_sql
        assert params == [2023, 10]

    def test_complex_query_with_limit_offset(self, query_builder):
        """Test complex query with LIMIT and OFFSET."""
        sql, params = (
            query_builder.select("id", "name", "created_at")
            .from_table("items")
            .where_in("category", ["A", "B", "C"])
            .where_between("created_at", "2023-01-01", "2023-12-31")
            .order_by("created_at", "DESC")
            .limit(20)
            .offset(40)
            .build_sql()
        )

        expected_lines = [
            "SELECT id, name, created_at",
            "FROM items",
            "WHERE category IN (?, ?, ?) AND created_at BETWEEN ? AND ?",
            "ORDER BY created_at DESC",
            "LIMIT 20",
            "OFFSET 40",
        ]
        expected_sql = "\n".join(expected_lines)

        assert sql == expected_sql
        assert params == ["A", "B", "C", "2023-01-01", "2023-12-31"]

    def test_istat_time_series_method(self, query_builder):
        """Test ISTAT-specific time series method."""
        sql, params = (
            query_builder.select_time_series("DATASET_001")
            .year_range(2020, 2022)
            .build_sql()
        )

        # Check that it includes the expected tables and joins
        assert "main.istat_datasets d" in sql
        assert "main.istat_observations o" in sql
        assert "main.dataset_metadata m" in sql
        assert "d.id = o.dataset_row_id" in sql
        assert "d.dataset_id = m.dataset_id" in sql
        assert "d.dataset_id = ?" in sql
        assert "d.year BETWEEN ? AND ?" in sql
        assert "DATASET_001" in params
        assert 2020 in params
        assert 2022 in params

    def test_territory_comparison_method(self, query_builder):
        """Test territory comparison method."""
        sql, params = query_builder.select_territory_comparison(
            "POP_TOTAL", 2023
        ).build_sql()

        assert "AVG(o.obs_value) as avg_value" in sql
        assert "GROUP BY d.territory_code, d.territory_name" in sql
        assert "ORDER BY avg_value DESC" in sql
        assert "d.measure_code = ?" in sql
        assert "d.year = ?" in sql
        assert params == ["POP_TOTAL", 2023]

    def test_category_trends_method(self, query_builder):
        """Test category trends analysis method."""
        sql, params = query_builder.select_category_trends("popolazione").build_sql()

        assert "COUNT(DISTINCT d.dataset_id) as dataset_count" in sql
        assert "AVG(o.obs_value) as avg_value" in sql
        assert "GROUP BY d.year" in sql
        assert "m.category = ?" in sql
        assert params == ["popolazione"]

    def test_query_execution_with_caching(self, query_builder):
        """Test query execution with caching."""
        # First execution
        result1 = (
            query_builder.select("id", "value")
            .from_table("test_table")
            .cache_for(60)
            .execute()
        )

        # Manager should be called once
        query_builder.manager.execute_query.assert_called_once()

        # Reset mock and execute same query
        query_builder.manager.execute_query.reset_mock()

        result2 = (
            query_builder.select("id", "value")
            .from_table("test_table")
            .cache_for(60)
            .execute()
        )

        # Manager should not be called again (cache hit)
        query_builder.manager.execute_query.assert_not_called()

        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_count_method(self, query_builder):
        """Test count method."""
        query_builder.manager.execute_query.return_value = pd.DataFrame(
            {"row_count": [42]}
        )

        count = (
            query_builder.select("id", "name")
            .from_table("users")
            .where("active", FilterOperator.EQ, True)
            .count()
        )

        assert count == 42

        # Check that the query was modified to use COUNT(*)
        args = query_builder.manager.execute_query.call_args[0]
        sql = args[0]
        assert "COUNT(*) as row_count" in sql
        assert "ORDER BY" not in sql  # ORDER BY should be removed for count

    def test_first_method(self, query_builder):
        """Test first method."""
        query_builder.manager.execute_query.return_value = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]}
        )

        first_row = query_builder.select("id", "name").from_table("users").first()

        assert first_row is not None
        assert first_row["id"] == 1
        assert first_row["name"] == "Alice"

        # Check that LIMIT 1 was added
        args = query_builder.manager.execute_query.call_args[0]
        sql = args[0]
        assert "LIMIT 1" in sql

    def test_exists_method(self, query_builder):
        """Test exists method."""
        query_builder.manager.execute_query.return_value = pd.DataFrame(
            {"row_count": [5]}
        )

        exists = (
            query_builder.select("id")
            .from_table("users")
            .where("active", FilterOperator.EQ, True)
            .exists()
        )

        assert exists is True

        # Test with zero count
        query_builder.manager.execute_query.return_value = pd.DataFrame(
            {"row_count": [0]}
        )

        exists = (
            query_builder.select("id")
            .from_table("users")
            .where("active", FilterOperator.EQ, False)
            .exists()
        )

        assert exists is False

    def test_validation_errors(self, query_builder):
        """Test validation error handling."""
        # Empty select
        with pytest.raises(ValueError, match="At least one column must be specified"):
            query_builder.select().from_table("users").build_sql()

        # Missing FROM table
        with pytest.raises(ValueError, match="FROM table must be specified"):
            query_builder.select("id").build_sql()

        # Invalid limit
        with pytest.raises(
            ValueError, match="Limit count must be a non-negative integer"
        ):
            query_builder.limit(-1)

        # Invalid offset
        with pytest.raises(
            ValueError, match="Offset count must be a non-negative integer"
        ):
            query_builder.offset(-5)

        # Invalid join type
        with pytest.raises(ValueError, match="Invalid join type"):
            query_builder.join("table2", "t1.id = t2.id", "INVALID_JOIN")

        # Invalid ORDER BY direction
        with pytest.raises(ValueError, match="Direction must be ASC or DESC"):
            query_builder.order_by("name", "INVALID")

    def test_explain_query(self, query_builder):
        """Test EXPLAIN query generation."""
        sql, params = (
            query_builder.select("id", "name").from_table("users").explain().build_sql()
        )

        assert sql.startswith("EXPLAIN")
        assert "SELECT id, name" in sql
        assert "FROM users" in sql

    def test_string_operator_conversion(self, query_builder):
        """Test string to FilterOperator conversion."""
        sql, params = (
            query_builder.select("*")
            .from_table("users")
            .where("age", ">", 21)
            .where("name", "LIKE", "John%")
            .build_sql()
        )

        assert "age > ?" in sql
        assert "name LIKE ?" in sql
        assert params == [21, "John%"]

    def test_helper_methods(self, query_builder):
        """Test convenience helper methods."""
        sql, params = (
            query_builder.select("*")
            .from_table("data")
            .where_in("category", ["A", "B"])
            .where_between("year", 2020, 2023)
            .where_null("deleted_at")
            .where_not_null("value")
            .build_sql()
        )

        assert "category IN (?, ?)" in sql
        assert "year BETWEEN ? AND ?" in sql
        assert "deleted_at IS NULL" in sql
        assert "value IS NOT NULL" in sql
        assert params == ["A", "B", 2020, 2023]

    def test_cache_key_generation(self, query_builder):
        """Test cache key generation consistency."""
        # Same query should generate same cache key
        builder1 = query_builder
        key1 = builder1._generate_cache_key("SELECT * FROM users", [])

        builder2 = query_builder
        key2 = builder2._generate_cache_key("SELECT * FROM users", [])

        assert key1 == key2

        # Different queries should generate different keys
        key3 = builder1._generate_cache_key("SELECT * FROM posts", [])
        assert key1 != key3


class TestQueryBuilderIntegration:
    """Integration tests with real DuckDB (if available)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        # Use a temporary directory instead of file
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.duckdb")

        yield db_path

        # Cleanup - try multiple times if file is locked
        import time

        for i in range(5):
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                break
            except PermissionError:
                if i < 4:  # Not the last attempt
                    time.sleep(0.1)
                    continue
                # Give up on cleanup if still locked after 5 attempts

    @pytest.mark.integration
    def test_real_query_execution(self, temp_db):
        """Test query execution with real DuckDB (integration test)."""
        # This test requires actual DuckDB
        try:
            import duckdb

            # Create test data
            conn = duckdb.connect(temp_db)
            conn.execute(
                """
                CREATE TABLE test_users (
                    id INTEGER,
                    name VARCHAR,
                    age INTEGER,
                    city VARCHAR
                )
            """
            )

            conn.execute(
                """
                INSERT INTO test_users VALUES
                (1, 'Alice', 25, 'New York'),
                (2, 'Bob', 30, 'London'),
                (3, 'Charlie', 35, 'Paris')
            """
            )

            conn.close()

            # Create manager and query builder
            from src.database.duckdb.config import get_duckdb_config

            config = get_duckdb_config()
            config["database"] = temp_db

            manager = DuckDBManager(config)
            builder = DuckDBQueryBuilder(manager)

            # Test basic query
            result = (
                builder.select("name", "age")
                .from_table("test_users")
                .where("age", FilterOperator.GT, 25)
                .order_by("age")
                .execute()
            )

            assert len(result) == 2
            assert result.iloc[0]["name"] == "Bob"
            assert result.iloc[1]["name"] == "Charlie"

            # Test count
            count = (
                builder.select("*")
                .from_table("test_users")
                .where("age", FilterOperator.LTE, 30)
                .count()
            )

            assert count == 2

        except ImportError:
            pytest.skip("DuckDB not available for integration test")


class TestPerformance:
    """Performance tests for query builder."""

    def test_cache_performance_improvement(self):
        """Test that caching improves query performance."""
        # Mock a slow query execution
        manager = Mock()
        slow_df = pd.DataFrame({"id": range(1000), "value": range(1000)})

        def slow_execute_query(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow query
            return slow_df

        manager.execute_query.side_effect = slow_execute_query

        builder = DuckDBQueryBuilder(manager, QueryCache(default_ttl=60))

        # First execution (should be slow)
        start_time = time.time()
        result1 = builder.select("*").from_table("large_table").execute()
        first_time = time.time() - start_time

        # Second execution (should be fast due to cache)
        start_time = time.time()
        result2 = builder.select("*").from_table("large_table").execute()
        second_time = time.time() - start_time

        # Cache should provide significant speedup
        assert second_time < first_time / 2  # At least 50% faster
        assert manager.execute_query.call_count == 1  # Only called once
        pd.testing.assert_frame_equal(result1, result2)

    def test_query_builder_overhead(self):
        """Test that query builder doesn't add significant overhead."""
        manager = Mock()
        manager.execute_query.return_value = pd.DataFrame({"id": [1]})

        # Measure time to build complex query
        start_time = time.time()

        for _ in range(100):  # Build 100 queries
            builder = DuckDBQueryBuilder(manager, QueryCache())
            sql, params = (
                builder.select("a", "b", "c")
                .from_table("table1")
                .join("table2", "table1.id = table2.id")
                .where("a", FilterOperator.GT, 10)
                .where_in("b", ["x", "y", "z"])
                .group_by("a")
                .having("COUNT(*)", FilterOperator.GT, 5)
                .order_by("a")
                .limit(100)
                .build_sql()
            )

        build_time = time.time() - start_time

        # Should build queries quickly (less than 1ms per query on average)
        avg_time_per_query = build_time / 100
        assert avg_time_per_query < 0.001  # Less than 1ms per query


def test_factory_functions():
    """Test module-level factory functions."""
    # Test create_query_builder
    builder = create_query_builder()
    assert isinstance(builder, DuckDBQueryBuilder)
    assert builder.manager is not None
    assert builder.cache is not None

    # Test get_global_cache
    cache = get_global_cache()
    assert isinstance(cache, QueryCache)


def test_module_exports():
    """Test that all expected classes and functions are exported."""
    from src.database.duckdb.query_builder import (
        DuckDBQueryBuilder,
        FilterCondition,
        FilterOperator,
        QueryCache,
        create_query_builder,
    )

    # All imports should work without errors
    assert DuckDBQueryBuilder is not None
    assert QueryCache is not None
    assert FilterCondition is not None
    assert FilterOperator is not None
    assert QueryType is not None
    assert AggregateFunction is not None
    assert create_query_builder is not None
