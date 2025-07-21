"""Basic DuckDB functionality tests.

Tests core DuckDB functionality without the complex manager wrapper.
Focuses on ensuring DuckDB works correctly for ISTAT data processing.
"""

import os
import tempfile
from pathlib import Path

import duckdb
import pandas as pd
import pytest


class TestDuckDBBasic:
    """Test basic DuckDB functionality."""

    def test_in_memory_database(self):
        """Test in-memory DuckDB operations."""
        conn = duckdb.connect(":memory:")

        # Test simple query
        result = conn.execute("SELECT 1 as test_value;").df()
        assert len(result) == 1
        assert result.iloc[0]["test_value"] == 1

        conn.close()

    def test_file_database(self):
        """Test file-based DuckDB operations."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.duckdb")

        try:
            conn = duckdb.connect(db_path)

            # Create table
            conn.execute(
                """
                CREATE TABLE test_table (
                    id INTEGER,
                    name VARCHAR,
                    value DECIMAL
                );
            """
            )

            # Insert data
            conn.execute(
                """
                INSERT INTO test_table VALUES
                (1, 'test1', 10.5),
                (2, 'test2', 20.0);
            """
            )

            # Query data
            result = conn.execute("SELECT * FROM test_table ORDER BY id;").df()
            assert len(result) == 2
            assert result.iloc[0]["name"] == "test1"
            assert result.iloc[1]["value"] == 20.0

            conn.close()

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
            os.rmdir(temp_dir)

    def test_dataframe_operations(self):
        """Test DataFrame integration with DuckDB."""
        conn = duckdb.connect(":memory:")

        # Create test DataFrame
        test_df = pd.DataFrame(
            {
                "dataset_id": ["TEST_001", "TEST_002", "TEST_003"],
                "year": [2020, 2021, 2022],
                "territory_code": ["IT", "IT", "FR"],
                "obs_value": [100.5, 110.2, 95.8],
            }
        )

        # Register DataFrame with DuckDB
        conn.register("test_data", test_df)

        # Query the DataFrame
        result = conn.execute(
            """
            SELECT
                territory_code,
                COUNT(*) as count,
                AVG(obs_value) as avg_value
            FROM test_data
            GROUP BY territory_code
            ORDER BY territory_code;
        """
        ).df()

        assert len(result) == 2
        assert result.iloc[0]["territory_code"] == "FR"
        assert result.iloc[1]["count"] == 2  # IT has 2 records

        conn.close()

    def test_istat_like_schema(self):
        """Test schema similar to ISTAT data structure."""
        conn = duckdb.connect(":memory:")

        # Create tables similar to ISTAT schema
        conn.execute(
            """
            CREATE TABLE dataset_metadata (
                dataset_id VARCHAR PRIMARY KEY,
                dataset_name VARCHAR,
                category VARCHAR,
                priority INTEGER
            );
        """
        )

        conn.execute(
            """
            CREATE TABLE istat_observations (
                id INTEGER,
                dataset_id VARCHAR,
                year INTEGER,
                territory_code VARCHAR,
                obs_value DECIMAL,
                FOREIGN KEY (dataset_id) REFERENCES dataset_metadata(dataset_id)
            );
        """
        )

        # Insert test metadata
        conn.execute(
            """
            INSERT INTO dataset_metadata VALUES
            ('DCIS_POPRES1', 'Popolazione residente', 'popolazione', 10),
            ('DCCN_PILN', 'PIL nazionale', 'economia', 9);
        """
        )

        # Insert test observations
        conn.execute(
            """
            INSERT INTO istat_observations VALUES
            (1, 'DCIS_POPRES1', 2020, 'IT', 59641488),
            (2, 'DCIS_POPRES1', 2021, 'IT', 59030133),
            (3, 'DCCN_PILN', 2020, 'IT', 1659516.7),
            (4, 'DCCN_PILN', 2021, 'IT', 1785373.9);
        """
        )

        # Test analytical query
        result = conn.execute(
            """
            SELECT
                m.category,
                m.dataset_name,
                m.priority,
                COUNT(o.id) as observations,
                MIN(o.year) as start_year,
                MAX(o.year) as end_year
            FROM dataset_metadata m
            JOIN istat_observations o ON m.dataset_id = o.dataset_id
            GROUP BY m.category, m.dataset_name, m.priority
            ORDER BY m.priority DESC;
        """
        ).df()

        assert len(result) == 2
        assert result.iloc[0]["category"] == "popolazione"  # Higher priority
        assert result.iloc[0]["observations"] == 2

        conn.close()

    def test_partitioning_simulation(self):
        """Test partitioning-like queries for performance."""
        conn = duckdb.connect(":memory:")

        # Create partitioned-like table
        conn.execute(
            """
            CREATE TABLE partitioned_data (
                partition_key VARCHAR,
                dataset_id VARCHAR,
                year INTEGER,
                territory_code VARCHAR,
                obs_value DECIMAL
            );
        """
        )

        # Insert test data with partition keys
        test_data = []
        for year in [2020, 2021, 2022]:
            for territory in ["IT", "FR", "DE"]:
                partition_key = f"year_{year}_{territory[:2]}"
                test_data.append(
                    (
                        partition_key,
                        "TEST_DATASET",
                        year,
                        territory,
                        year * 100 + ord(territory[0]),
                    )
                )

        for data in test_data:
            conn.execute(
                f"""
                INSERT INTO partitioned_data VALUES
                ('{data[0]}', '{data[1]}', {data[2]}, '{data[3]}', {data[4]});
            """
            )

        # Test partition-aware query
        result = conn.execute(
            """
            SELECT
                partition_key,
                COUNT(*) as records,
                AVG(obs_value) as avg_value
            FROM partitioned_data
            WHERE year >= 2021  -- Partition pruning simulation
            GROUP BY partition_key
            ORDER BY partition_key;
        """
        ).df()

        assert len(result) == 6  # 2 years * 3 territories
        assert all("year_202" in pk for pk in result["partition_key"])

        conn.close()

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset simulation."""
        conn = duckdb.connect(":memory:")

        # Create table
        conn.execute(
            """
            CREATE TABLE performance_test (
                id INTEGER,
                category VARCHAR,
                year INTEGER,
                value DECIMAL
            );
        """
        )

        # Generate larger dataset
        large_df = pd.DataFrame(
            {
                "id": range(1000),
                "category": [f"cat_{i % 10}" for i in range(1000)],
                "year": [2020 + (i % 5) for i in range(1000)],
                "value": [i * 1.5 for i in range(1000)],
            }
        )

        # Bulk insert via DataFrame
        conn.register("large_data", large_df)
        conn.execute("INSERT INTO performance_test SELECT * FROM large_data;")

        # Test aggregation performance
        result = conn.execute(
            """
            SELECT
                category,
                year,
                COUNT(*) as count,
                AVG(value) as avg_value,
                MAX(value) as max_value
            FROM performance_test
            GROUP BY category, year
            ORDER BY category, year;
        """
        ).df()

        # Each category appears in each year, but not all combinations exist
        # We have 1000 records with 10 categories and 5 years
        # So each category-year combination has 20 records (1000/50)
        expected_combinations = 10 * 5  # 10 categories * 5 years = 50
        # But our data generation creates only one record per category per year cycle
        # So we should have 10 combinations (one per category)
        assert len(result) == 10  # 10 categories
        assert result["count"].sum() == 1000

        conn.close()

    def test_advanced_analytics(self):
        """Test advanced analytical functions."""
        conn = duckdb.connect(":memory:")

        # Create time series data
        conn.execute(
            """
            CREATE TABLE time_series (
                date DATE,
                category VARCHAR,
                value DECIMAL
            );
        """
        )

        # Insert monthly data
        conn.execute(
            """
            INSERT INTO time_series VALUES
            ('2023-01-01', 'A', 100),
            ('2023-02-01', 'A', 105),
            ('2023-03-01', 'A', 110),
            ('2023-01-01', 'B', 200),
            ('2023-02-01', 'B', 195),
            ('2023-03-01', 'B', 205);
        """
        )

        # Test window functions
        result = conn.execute(
            """
            SELECT
                category,
                date,
                value,
                LAG(value) OVER (PARTITION BY category ORDER BY date) as prev_value,
                value - LAG(value) OVER (PARTITION BY category ORDER BY date) as change
            FROM time_series
            ORDER BY category, date;
        """
        ).df()

        assert len(result) == 6
        # Check that change calculation works
        category_a_changes = result[result["category"] == "A"]["change"].dropna()
        assert list(category_a_changes) == [5.0, 5.0]  # Both changes are +5

        conn.close()


class TestDuckDBConfiguration:
    """Test DuckDB configuration options."""

    def test_memory_limit_configuration(self):
        """Test memory limit configuration."""
        # Test with conservative memory limit
        conn = duckdb.connect(":memory:", config={"memory_limit": "512MB"})

        # Simple test to ensure connection works
        result = conn.execute("SELECT 1;").fetchone()
        assert result[0] == 1

        conn.close()

    def test_thread_configuration(self):
        """Test thread configuration."""
        # Test with limited threads
        conn = duckdb.connect(":memory:", config={"threads": 2})

        # Test parallel operation
        result = conn.execute(
            """
            SELECT COUNT(*)
            FROM generate_series(1, 100) t(i);
        """
        ).fetchone()

        assert result[0] == 100

        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
