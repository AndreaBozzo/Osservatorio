"""Simple DuckDB adapter for immediate use.

This is a lightweight adapter that provides essential DuckDB functionality
without the complex manager wrapper. It can be used immediately for ISTAT
data processing while the full manager implementation is being stabilized.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd


class SimpleDuckDBAdapter:
    """Lightweight DuckDB adapter for ISTAT data processing."""

    def __init__(self, database_path: str = ":memory:"):
        """Initialize adapter with database path.

        Args:
            database_path: Path to database file or ':memory:' for in-memory
        """
        self.database_path = database_path
        self.connection = None
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensure database connection is established."""
        if self.connection is None:
            self.connection = duckdb.connect(self.database_path)

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute query and return DataFrame.

        Args:
            query: SQL query to execute

        Returns:
            Query results as DataFrame
        """
        self._ensure_connection()
        return self.connection.execute(query).df()

    def execute_statement(self, statement: str):
        """Execute SQL statement (no return).

        Args:
            statement: SQL statement to execute
        """
        self._ensure_connection()
        self.connection.execute(statement)

    def create_istat_schema(self):
        """Create basic ISTAT schema for data storage."""
        # Create metadata table
        self.execute_statement(
            """
            CREATE TABLE IF NOT EXISTS dataset_metadata (
                dataset_id VARCHAR PRIMARY KEY,
                dataset_name VARCHAR,
                category VARCHAR,
                priority INTEGER DEFAULT 1,
                total_observations INTEGER DEFAULT 0,
                completeness_score DECIMAL(5,2),
                data_quality_score DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Create observations table with sequence
        self.execute_statement("CREATE SEQUENCE IF NOT EXISTS obs_id_seq;")
        self.execute_statement(
            """
            CREATE TABLE IF NOT EXISTS istat_observations (
                id INTEGER DEFAULT nextval('obs_id_seq'),
                dataset_id VARCHAR,
                year INTEGER,
                territory_code VARCHAR,
                territory_name VARCHAR,
                measure_code VARCHAR,
                measure_name VARCHAR,
                obs_value DECIMAL,
                obs_status VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES dataset_metadata(dataset_id)
            );
        """
        )

        # Create indexes for performance
        try:
            self.execute_statement(
                "CREATE INDEX IF NOT EXISTS idx_obs_dataset ON istat_observations(dataset_id);"
            )
            self.execute_statement(
                "CREATE INDEX IF NOT EXISTS idx_obs_year ON istat_observations(year);"
            )
            self.execute_statement(
                "CREATE INDEX IF NOT EXISTS idx_obs_territory ON istat_observations(territory_code);"
            )
            self.execute_statement(
                "CREATE INDEX IF NOT EXISTS idx_metadata_category ON dataset_metadata(category);"
            )
        except:
            # Indexes might already exist
            pass

    def insert_metadata(
        self,
        dataset_id: str,
        dataset_name: str,
        category: str = "altro",
        priority: int = 1,
    ):
        """Insert dataset metadata.

        Args:
            dataset_id: Unique dataset identifier
            dataset_name: Human-readable dataset name
            category: Dataset category
            priority: Dataset priority (higher = more important)
        """
        self.execute_statement(
            f"""
            INSERT OR REPLACE INTO dataset_metadata (dataset_id, dataset_name, category, priority)
            VALUES ('{dataset_id}', '{dataset_name}', '{category}', {priority});
        """
        )

    def insert_observations(self, df: pd.DataFrame):
        """Insert observations from DataFrame.

        Args:
            df: DataFrame with observation data
        """
        # Register DataFrame and insert
        self.connection.register("temp_observations", df)
        self.execute_statement(
            """
            INSERT INTO istat_observations (dataset_id, year, territory_code, territory_name,
                                          measure_code, measure_name, obs_value, obs_status)
            SELECT
                dataset_id,
                year,
                territory_code,
                territory_name,
                measure_code,
                measure_name,
                obs_value,
                obs_status
            FROM temp_observations;
        """
        )
        self.connection.unregister("temp_observations")

    def get_dataset_summary(self) -> pd.DataFrame:
        """Get summary of all datasets.

        Returns:
            DataFrame with dataset summary information
        """
        return self.execute_query(
            """
            SELECT
                m.dataset_id,
                m.dataset_name,
                m.category,
                m.priority,
                COUNT(o.id) as total_observations,
                MIN(o.year) as start_year,
                MAX(o.year) as end_year,
                COUNT(DISTINCT o.territory_code) as territories,
                AVG(o.obs_value) as avg_value
            FROM dataset_metadata m
            LEFT JOIN istat_observations o ON m.dataset_id = o.dataset_id
            GROUP BY m.dataset_id, m.dataset_name, m.category, m.priority
            ORDER BY m.priority DESC, m.category, m.dataset_name;
        """
        )

    def get_time_series(
        self, dataset_id: str, territory_code: str = None
    ) -> pd.DataFrame:
        """Get time series data for a dataset.

        Args:
            dataset_id: Dataset to retrieve
            territory_code: Optional territory filter

        Returns:
            Time series data
        """
        where_clause = f"WHERE dataset_id = '{dataset_id}'"
        if territory_code:
            where_clause += f" AND territory_code = '{territory_code}'"

        return self.execute_query(
            f"""
            SELECT
                year,
                territory_code,
                territory_name,
                measure_code,
                measure_name,
                obs_value,
                obs_status
            FROM istat_observations
            {where_clause}
            ORDER BY year, territory_code, measure_code;
        """
        )

    def get_territory_comparison(self, dataset_id: str, year: int) -> pd.DataFrame:
        """Get territory comparison for a specific year.

        Args:
            dataset_id: Dataset to analyze
            year: Year to compare

        Returns:
            Territory comparison data
        """
        return self.execute_query(
            f"""
            SELECT
                territory_code,
                territory_name,
                COUNT(*) as indicators,
                AVG(obs_value) as avg_value,
                MIN(obs_value) as min_value,
                MAX(obs_value) as max_value,
                RANK() OVER (ORDER BY AVG(obs_value) DESC) as rank
            FROM istat_observations
            WHERE dataset_id = '{dataset_id}' AND year = {year}
              AND obs_value IS NOT NULL
            GROUP BY territory_code, territory_name
            ORDER BY avg_value DESC;
        """
        )

    def get_category_trends(
        self, category: str, start_year: int = None, end_year: int = None
    ) -> pd.DataFrame:
        """Get trend analysis for a category.

        Args:
            category: Category to analyze
            start_year: Optional start year
            end_year: Optional end year

        Returns:
            Trend analysis data
        """
        year_filter = ""
        if start_year and end_year:
            year_filter = f"AND o.year BETWEEN {start_year} AND {end_year}"
        elif start_year:
            year_filter = f"AND o.year >= {start_year}"
        elif end_year:
            year_filter = f"AND o.year <= {end_year}"

        return self.execute_query(
            f"""
            SELECT
                o.year,
                COUNT(DISTINCT m.dataset_id) as datasets,
                COUNT(o.id) as total_observations,
                AVG(o.obs_value) as avg_value,
                MEDIAN(o.obs_value) as median_value
            FROM dataset_metadata m
            JOIN istat_observations o ON m.dataset_id = o.dataset_id
            WHERE m.category = '{category}' {year_filter}
              AND o.obs_value IS NOT NULL
            GROUP BY o.year
            ORDER BY o.year;
        """
        )

    def optimize_database(self):
        """Run database optimization."""
        try:
            self.execute_statement("ANALYZE;")
            self.execute_statement("CHECKPOINT;")
        except:
            # Optimization might fail in some versions
            pass

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_adapter(database_path: str = ":memory:") -> SimpleDuckDBAdapter:
    """Create and initialize a DuckDB adapter.

    Args:
        database_path: Database file path or ':memory:'

    Returns:
        Configured SimpleDuckDBAdapter
    """
    adapter = SimpleDuckDBAdapter(database_path)
    adapter.create_istat_schema()
    return adapter


def create_file_adapter(
    db_name: str = "osservatorio_simple.duckdb",
) -> SimpleDuckDBAdapter:
    """Create file-based adapter in data directory.

    Args:
        db_name: Database filename

    Returns:
        File-based SimpleDuckDBAdapter
    """
    # Create data/databases directory if it doesn't exist
    base_dir = Path(__file__).parent.parent.parent.parent
    db_dir = base_dir / "data" / "databases"
    db_dir.mkdir(parents=True, exist_ok=True)

    db_path = db_dir / db_name
    adapter = SimpleDuckDBAdapter(str(db_path))
    adapter.create_istat_schema()
    return adapter


def create_temp_adapter() -> SimpleDuckDBAdapter:
    """Create temporary file-based adapter for testing.

    Returns:
        Temporary SimpleDuckDBAdapter
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "temp.duckdb")
    adapter = SimpleDuckDBAdapter(temp_path)
    adapter.create_istat_schema()
    return adapter
