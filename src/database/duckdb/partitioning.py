"""Data partitioning strategies for DuckDB ISTAT analytics.

This module implements partitioning strategies to optimize query performance:
- Year-based partitioning for time series analysis
- Territory-based partitioning for geographic analysis
- Hybrid partitioning strategies
- Partition maintenance and optimization
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.utils.logger import get_logger

from .config import get_schema_config
from .manager import DuckDBManager

logger = get_logger(__name__)


class PartitionStrategy:
    """Base class for partitioning strategies."""

    def __init__(self, name: str, columns: List[str]):
        """Initialize partition strategy.

        Args:
            name: Strategy name
            columns: Columns to partition by
        """
        self.name = name
        self.columns = columns

    def get_partition_key(self, row: Dict[str, Any]) -> str:
        """Generate partition key for a data row.

        Args:
            row: Data row as dictionary

        Returns:
            Partition key string
        """
        raise NotImplementedError

    def get_partition_filter(self, **kwargs) -> str:
        """Generate SQL filter for partition pruning.

        Returns:
            SQL WHERE clause for partition pruning
        """
        raise NotImplementedError


class YearPartitionStrategy(PartitionStrategy):
    """Year-based partitioning strategy."""

    def __init__(self):
        super().__init__("year_partition", ["year"])

    def get_partition_key(self, row: Dict[str, Any]) -> str:
        """Generate year-based partition key."""
        year = row.get("year", datetime.now().year)
        return f"year_{year}"

    def get_partition_filter(self, start_year: int = None, end_year: int = None) -> str:
        """Generate year filter for partition pruning."""
        if start_year and end_year:
            return f"year BETWEEN {start_year} AND {end_year}"
        elif start_year:
            return f"year >= {start_year}"
        elif end_year:
            return f"year <= {end_year}"
        return ""


class TerritoryPartitionStrategy(PartitionStrategy):
    """Territory-based partitioning strategy."""

    def __init__(self):
        super().__init__("territory_partition", ["territory_code"])

    def get_partition_key(self, row: Dict[str, Any]) -> str:
        """Generate territory-based partition key."""
        territory = row.get("territory_code", "UNKNOWN")
        # Group territories to avoid too many small partitions
        if territory.startswith("IT"):
            return f"territory_italy_{territory[:4]}"  # Group by first 4 chars
        return f"territory_{territory[:2]}"  # Group by first 2 chars

    def get_partition_filter(self, territories: List[str] = None) -> str:
        """Generate territory filter for partition pruning."""
        if territories:
            territory_list = "', '".join(territories)
            return f"territory_code IN ('{territory_list}')"
        return ""


class HybridPartitionStrategy(PartitionStrategy):
    """Hybrid year + territory partitioning strategy."""

    def __init__(self):
        super().__init__("hybrid_partition", ["year", "territory_code"])

    def get_partition_key(self, row: Dict[str, Any]) -> str:
        """Generate hybrid partition key."""
        year = row.get("year", datetime.now().year)
        territory = row.get("territory_code", "UNKNOWN")

        # Create decade-based partitions to limit partition count
        decade = (year // 10) * 10
        territory_group = territory[:2] if territory else "UNK"

        return f"hybrid_{decade}s_{territory_group}"

    def get_partition_filter(
        self,
        start_year: int = None,
        end_year: int = None,
        territories: List[str] = None,
    ) -> str:
        """Generate hybrid filter for partition pruning."""
        filters = []

        if start_year and end_year:
            filters.append(f"year BETWEEN {start_year} AND {end_year}")
        elif start_year:
            filters.append(f"year >= {start_year}")
        elif end_year:
            filters.append(f"year <= {end_year}")

        if territories:
            territory_list = "', '".join(territories)
            filters.append(f"territory_code IN ('{territory_list}')")

        return " AND ".join(filters)


class PartitionManager:
    """Manages data partitioning for DuckDB ISTAT analytics."""

    def __init__(self, manager: Optional[DuckDBManager] = None):
        """Initialize partition manager.

        Args:
            manager: Optional DuckDB manager instance
        """
        self.manager = manager or DuckDBManager()
        self.schema_config = get_schema_config()

        # Available partitioning strategies
        self.strategies = {
            "year": YearPartitionStrategy(),
            "territory": TerritoryPartitionStrategy(),
            "hybrid": HybridPartitionStrategy(),
        }

        # Default strategy
        self.default_strategy = "hybrid"

    def create_partitioned_tables(self, strategy_name: str = None) -> None:
        """Create partitioned versions of main tables.

        Args:
            strategy_name: Partitioning strategy to use
        """
        strategy = self.strategies.get(strategy_name or self.default_strategy)
        if not strategy:
            raise ValueError(f"Unknown partitioning strategy: {strategy_name}")

        schema = self.schema_config["main_schema"]

        # Create partitioned datasets table
        self._create_partitioned_datasets_table(schema, strategy)

        # Create partitioned observations table
        self._create_partitioned_observations_table(schema, strategy)

        logger.info(f"Partitioned tables created using {strategy.name} strategy")

    def _create_partitioned_datasets_table(
        self, schema: str, strategy: PartitionStrategy
    ) -> None:
        """Create partitioned datasets table."""
        table_name = f"{schema}.istat_datasets_partitioned"

        # DuckDB doesn't have native table partitioning like PostgreSQL,
        # so we implement logical partitioning using views and storage optimization

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Primary key
            id BIGINT PRIMARY KEY DEFAULT nextval('dataset_part_id_seq'),

            -- Partitioning columns (indexed for performance)
            partition_key VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL,
            territory_code VARCHAR(10),

            -- Foreign key to metadata
            dataset_id VARCHAR(50) NOT NULL,

            -- Original columns
            territory_name VARCHAR(100),
            time_period VARCHAR(20) NOT NULL,
            time_period_type VARCHAR(10),
            measure_code VARCHAR(50),
            measure_name VARCHAR(200),
            gender VARCHAR(10),
            age_group VARCHAR(20),
            sector VARCHAR(50),
            dim1_code VARCHAR(50),
            dim1_value VARCHAR(200),
            dim2_code VARCHAR(50),
            dim2_value VARCHAR(200),
            dim3_code VARCHAR(50),
            dim3_value VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source VARCHAR(100) DEFAULT 'ISTAT',

            -- Constraints
            FOREIGN KEY (dataset_id) REFERENCES {schema}.dataset_metadata(dataset_id)
        );
        """

        # Create sequence
        self.manager.execute_statement(
            "CREATE SEQUENCE IF NOT EXISTS dataset_part_id_seq;"
        )

        self.manager.execute_statement(create_sql)

        # Create partition-aware indexes
        partition_indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_datasets_part_key ON {table_name}(partition_key);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_part_year ON {table_name}(year);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_part_territory ON {table_name}(territory_code);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_part_dataset ON {table_name}(dataset_id);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_part_composite ON {table_name}(partition_key, dataset_id, year);",
        ]

        for index_sql in partition_indexes:
            self.manager.execute_statement(index_sql)

        logger.debug(f"Partitioned datasets table created: {table_name}")

    def _create_partitioned_observations_table(
        self, schema: str, strategy: PartitionStrategy
    ) -> None:
        """Create partitioned observations table."""
        table_name = f"{schema}.istat_observations_partitioned"

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Primary key
            id BIGINT PRIMARY KEY DEFAULT nextval('observation_part_id_seq'),

            -- Partitioning columns
            partition_key VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL,
            territory_code VARCHAR(10),

            -- Foreign keys
            dataset_row_id BIGINT NOT NULL,
            dataset_id VARCHAR(50) NOT NULL,

            -- Observation data
            obs_value DECIMAL(20,6),
            obs_status VARCHAR(10),
            obs_conf VARCHAR(10),

            -- Value metadata
            value_type VARCHAR(20) DEFAULT 'NUMERIC',
            string_value VARCHAR(500),
            unit_multiplier INTEGER DEFAULT 1,
            decimals INTEGER DEFAULT 2,

            -- Quality flags
            is_estimated BOOLEAN DEFAULT FALSE,
            is_provisional BOOLEAN DEFAULT FALSE,
            confidence_interval_lower DECIMAL(20,6),
            confidence_interval_upper DECIMAL(20,6),

            -- Processing metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_row INTEGER,

            -- Constraints
            FOREIGN KEY (dataset_id) REFERENCES {schema}.dataset_metadata(dataset_id)
        );
        """

        # Create sequence
        self.manager.execute_statement(
            "CREATE SEQUENCE IF NOT EXISTS observation_part_id_seq;"
        )

        self.manager.execute_statement(create_sql)

        # Create partition-aware indexes
        partition_indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_obs_part_key ON {table_name}(partition_key);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_part_year ON {table_name}(year);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_part_territory ON {table_name}(territory_code);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_part_dataset ON {table_name}(dataset_id);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_part_value ON {table_name}(obs_value);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_part_composite ON {table_name}(partition_key, dataset_id, obs_value);",
        ]

        for index_sql in partition_indexes:
            self.manager.execute_statement(index_sql)

        logger.debug(f"Partitioned observations table created: {table_name}")

    def create_partition_views(self, strategy_name: str = None) -> None:
        """Create views for each partition to optimize queries.

        Args:
            strategy_name: Partitioning strategy to use
        """
        strategy = self.strategies.get(strategy_name or self.default_strategy)
        if not strategy:
            raise ValueError(f"Unknown partitioning strategy: {strategy_name}")

        schema = self.schema_config["main_schema"]

        # Get existing partition keys
        partition_keys = self._get_existing_partition_keys()

        for partition_key in partition_keys:
            self._create_partition_view(schema, partition_key)

        logger.info(f"Created {len(partition_keys)} partition views")

    def _get_existing_partition_keys(self) -> List[str]:
        """Get list of existing partition keys."""
        schema = self.schema_config["main_schema"]

        query = f"""
        SELECT DISTINCT partition_key
        FROM {schema}.istat_datasets_partitioned
        ORDER BY partition_key;
        """

        try:
            result = self.manager.execute_query(query)
            return result["partition_key"].tolist()
        except Exception as e:
            logger.warning(f"Could not get partition keys: {e}")
            return []

    def _create_partition_view(self, schema: str, partition_key: str) -> None:
        """Create view for specific partition."""
        safe_partition_key = partition_key.replace("-", "_").replace(".", "_")
        view_name = f"{schema}.partition_{safe_partition_key}"

        view_sql = f"""
        CREATE OR REPLACE VIEW {view_name} AS
        SELECT
            d.*,
            o.obs_value,
            o.obs_status,
            o.value_type,
            o.is_estimated,
            o.is_provisional
        FROM {schema}.istat_datasets_partitioned d
        LEFT JOIN {schema}.istat_observations_partitioned o ON d.id = o.dataset_row_id
        WHERE d.partition_key = '{partition_key}';
        """

        try:
            self.manager.execute_statement(view_sql)
            logger.debug(f"Created partition view: {view_name}")
        except Exception as e:
            logger.warning(f"Failed to create partition view {view_name}: {e}")

    def partition_data(
        self, df: pd.DataFrame, dataset_id: str, strategy_name: str = None
    ) -> Dict[str, pd.DataFrame]:
        """Partition DataFrame data according to strategy.

        Args:
            df: DataFrame to partition
            dataset_id: Dataset ID for the data
            strategy_name: Partitioning strategy to use

        Returns:
            Dictionary mapping partition keys to DataFrames
        """
        strategy = self.strategies.get(strategy_name or self.default_strategy)
        if not strategy:
            raise ValueError(f"Unknown partitioning strategy: {strategy_name}")

        partitions = {}

        for _, row in df.iterrows():
            row_dict = row.to_dict()
            partition_key = strategy.get_partition_key(row_dict)

            if partition_key not in partitions:
                partitions[partition_key] = []

            partitions[partition_key].append(row_dict)

        # Convert to DataFrames
        partition_dfs = {}
        for partition_key, rows in partitions.items():
            partition_df = pd.DataFrame(rows)
            partition_df["partition_key"] = partition_key
            partition_df["dataset_id"] = dataset_id
            partition_dfs[partition_key] = partition_df

        logger.info(
            f"Data partitioned into {len(partition_dfs)} partitions using {strategy.name}"
        )
        return partition_dfs

    def insert_partitioned_data(
        self, partitioned_data: Dict[str, pd.DataFrame]
    ) -> None:
        """Insert partitioned data into appropriate tables.

        Args:
            partitioned_data: Dictionary mapping partition keys to DataFrames
        """
        schema = self.schema_config["main_schema"]
        datasets_table = f"{schema}.istat_datasets_partitioned"
        observations_table = f"{schema}.istat_observations_partitioned"

        total_inserted = 0

        with self.manager.transaction() as conn:
            for partition_key, df in partitioned_data.items():
                try:
                    # Separate datasets and observations data
                    dataset_columns = [
                        "partition_key",
                        "dataset_id",
                        "year",
                        "territory_code",
                        "territory_name",
                        "time_period",
                        "time_period_type",
                        "measure_code",
                        "measure_name",
                        "gender",
                        "age_group",
                        "sector",
                        "data_source",
                    ]

                    observation_columns = [
                        "partition_key",
                        "dataset_id",
                        "year",
                        "territory_code",
                        "obs_value",
                        "obs_status",
                        "value_type",
                        "is_estimated",
                        "is_provisional",
                    ]

                    # Insert dataset records
                    dataset_df = df[df.columns.intersection(dataset_columns)].copy()
                    if not dataset_df.empty:
                        self.manager.bulk_insert(datasets_table, dataset_df)

                    # Insert observation records
                    obs_df = df[df.columns.intersection(observation_columns)].copy()
                    if not obs_df.empty:
                        self.manager.bulk_insert(observations_table, obs_df)

                    total_inserted += len(df)
                    logger.debug(f"Inserted partition {partition_key}: {len(df)} rows")

                except Exception as e:
                    logger.error(f"Failed to insert partition {partition_key}: {e}")
                    raise

        logger.info(
            f"Successfully inserted {total_inserted} total rows across all partitions"
        )

    def optimize_partitions(self) -> None:
        """Optimize partition performance through statistics and maintenance."""
        schema = self.schema_config["main_schema"]

        tables = [
            f"{schema}.istat_datasets_partitioned",
            f"{schema}.istat_observations_partitioned",
        ]

        for table in tables:
            try:
                # Update table statistics
                self.manager.execute_statement(f"ANALYZE {table};")

                # Get partition statistics
                stats = self._get_partition_statistics(table)
                logger.info(f"Partition stats for {table}: {stats}")

            except Exception as e:
                logger.warning(f"Failed to optimize partition table {table}: {e}")

    def _get_partition_statistics(self, table: str) -> Dict[str, Any]:
        """Get statistics for partitioned table.

        Args:
            table: Table name to analyze

        Returns:
            Dictionary with partition statistics
        """
        try:
            stats_query = f"""
            SELECT
                partition_key,
                COUNT(*) as row_count,
                MIN(year) as min_year,
                MAX(year) as max_year,
                COUNT(DISTINCT territory_code) as territory_count
            FROM {table}
            GROUP BY partition_key
            ORDER BY row_count DESC;
            """

            result = self.manager.execute_query(stats_query)

            return {
                "total_partitions": len(result),
                "largest_partition": result.iloc[0]["row_count"]
                if not result.empty
                else 0,
                "smallest_partition": result.iloc[-1]["row_count"]
                if not result.empty
                else 0,
                "partition_details": result.to_dict("records"),
            }

        except Exception as e:
            logger.warning(f"Could not get partition statistics: {e}")
            return {}

    def get_partition_pruning_query(self, base_query: str, **filter_kwargs) -> str:
        """Add partition pruning to existing query.

        Args:
            base_query: Original SQL query
            **filter_kwargs: Filter parameters for partition pruning

        Returns:
            Modified query with partition pruning
        """
        strategy = self.strategies[self.default_strategy]
        partition_filter = strategy.get_partition_filter(**filter_kwargs)

        if partition_filter:
            # Simple injection of WHERE clause - in production, use proper SQL parsing
            if "WHERE" in base_query.upper():
                return base_query.replace("WHERE", f"WHERE {partition_filter} AND")
            else:
                # Add WHERE clause before ORDER BY, GROUP BY, etc.
                keywords = ["ORDER BY", "GROUP BY", "HAVING", "LIMIT"]
                insert_pos = len(base_query)

                for keyword in keywords:
                    pos = base_query.upper().find(keyword)
                    if pos != -1 and pos < insert_pos:
                        insert_pos = pos

                return (
                    base_query[:insert_pos]
                    + f" WHERE {partition_filter} "
                    + base_query[insert_pos:]
                )

        return base_query


def create_partition_manager(
    manager: Optional[DuckDBManager] = None,
) -> PartitionManager:
    """Create and configure partition manager.

    Args:
        manager: Optional DuckDB manager instance

    Returns:
        Configured PartitionManager instance
    """
    partition_manager = PartitionManager(manager)
    return partition_manager
