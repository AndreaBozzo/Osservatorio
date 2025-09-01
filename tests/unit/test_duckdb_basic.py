"""Basic DuckDB functionality tests.

Tests core DuckDB functionality without the complex manager wrapper.
Focuses on ensuring DuckDB works correctly for ISTAT data processing.
"""

import os
import tempfile

import duckdb
import pandas as pd


class TestDuckDBBasic:
    """Test basic DuckDB functionality."""

    def test_in_memory_database(self):
        """Test in-memory DuckDB operations."""
        with duckdb.connect(":memory:") as conn:
            # Test simple query
            result = conn.execute("SELECT 1 as test_value;").df()
            assert len(result) == 1
            assert result.iloc[0]["test_value"] == 1

    def test_file_database(self):
        """Test file-based DuckDB operations."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.duckdb")

        try:
            with duckdb.connect(db_path) as conn:
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

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
            os.rmdir(temp_dir)

    def test_dataframe_operations(self):
        """Test DataFrame integration with DuckDB."""
        with duckdb.connect(":memory:") as conn:
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

    def test_istat_like_schema(self):
        """Test schema similar to ISTAT data structure."""
        with duckdb.connect(":memory:") as conn:
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

    def test_partitioning_simulation(self):
        """Test partitioning-like queries for performance."""
        with duckdb.connect(":memory:") as conn:
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
                    year,
                    territory_code,
                    COUNT(*) as records,
                    AVG(obs_value) as avg_value
                FROM partitioned_data
                WHERE year >= 2021
                GROUP BY year, territory_code
                ORDER BY year, territory_code;
            """
            ).df()

            assert len(result) == 6  # 2 years * 3 territories
            assert result.iloc[0]["year"] == 2021

    def test_analytical_functions(self):
        """Test analytical functions for ISTAT-like data."""
        with duckdb.connect(":memory:") as conn:
            # Create time series data
            conn.execute(
                """
                CREATE TABLE time_series (
                    dataset_id VARCHAR,
                    year INTEGER,
                    quarter INTEGER,
                    obs_value DECIMAL
                );
            """
            )

            # Insert quarterly data for 2 years
            quarterly_data = []
            for year in [2022, 2023]:
                for quarter in [1, 2, 3, 4]:
                    value = 100 + (year - 2022) * 10 + quarter * 2.5
                    quarterly_data.append(("GDP_QUARTERLY", year, quarter, value))

            for data in quarterly_data:
                conn.execute(
                    f"""
                    INSERT INTO time_series VALUES
                    ('{data[0]}', {data[1]}, {data[2]}, {data[3]});
                """
                )

            # Test window functions
            result = conn.execute(
                """
                SELECT
                    year,
                    quarter,
                    obs_value,
                    LAG(obs_value) OVER (ORDER BY year, quarter) as prev_value,
                    obs_value - LAG(obs_value) OVER (ORDER BY year, quarter) as growth
                FROM time_series
                ORDER BY year, quarter;
            """
            ).df()

            assert len(result) == 8
            assert result.iloc[1]["growth"] == 2.5  # Expected growth between quarters

    def test_performance_config(self):
        """Test DuckDB with performance configurations."""
        with duckdb.connect(":memory:", config={"memory_limit": "512MB"}) as conn:
            # Test with memory limit
            result = conn.execute("SELECT 1 as test;").df()
            assert result.iloc[0]["test"] == 1

    def test_threading_config(self):
        """Test DuckDB with threading configurations."""
        with duckdb.connect(":memory:", config={"threads": 2}) as conn:
            # Test with thread limit
            result = conn.execute("SELECT 1 as test;").df()
            assert result.iloc[0]["test"] == 1
