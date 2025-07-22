"""DuckDB schema definitions for ISTAT statistical data.

This module defines the database schema optimized for ISTAT data analysis:
- Normalized structure for observations and metadata
- Optimized for analytical queries
- Partitioned by year and territory for performance
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import pandas as pd

from src.utils.logger import get_logger

from .config import SCHEMA_CONFIG, get_schema_config
from .manager import DuckDBManager

logger = get_logger(__name__)


class ISTATSchemaManager:
    """Manager for ISTAT database schema creation and maintenance."""

    def __init__(self, manager: Optional[DuckDBManager] = None):
        """Initialize schema manager.

        Args:
            manager: Optional DuckDB manager instance
        """
        self.manager = manager or DuckDBManager()
        self.schema_config = get_schema_config()

    def create_all_schemas(self) -> None:
        """Create all required schemas for ISTAT data."""
        schemas = [
            self.schema_config["main_schema"],
            self.schema_config["temp_schema"],
            self.schema_config["analytics_schema"],
        ]

        for schema_name in schemas:
            try:
                self.manager.create_schema(schema_name)
                logger.info(f"Schema created/verified: {schema_name}")
            except Exception as e:
                logger.error(f"Failed to create schema {schema_name}: {e}")
                raise

    def create_all_tables(self) -> None:
        """Create all tables with optimized structure for ISTAT data."""
        self.create_all_schemas()

        # Create tables in dependency order
        self.create_dataset_metadata_table()
        self.create_datasets_table()
        self.create_observations_table()
        self.create_analytics_tables()

        logger.info("All ISTAT tables created successfully")

    def create_dataset_metadata_table(self) -> None:
        """Create table for dataset metadata and configuration."""
        schema = self.schema_config["main_schema"]
        table_name = f"{schema}.dataset_metadata"

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Primary identification
            dataset_id VARCHAR(50) NOT NULL PRIMARY KEY,
            dataset_name VARCHAR(200) NOT NULL,

            -- Classification
            category VARCHAR(50) NOT NULL,
            priority INTEGER NOT NULL DEFAULT 1,
            subcategory VARCHAR(100),

            -- Metadata
            description TEXT,
            source VARCHAR(100) DEFAULT 'ISTAT',
            frequency VARCHAR(20),
            unit_of_measure VARCHAR(50),

            -- Geographic coverage
            geographic_level VARCHAR(30),
            territory_codes TEXT[], -- Array of territory codes covered

            -- Time coverage
            start_period VARCHAR(10),
            end_period VARCHAR(10),
            latest_update TIMESTAMP,

            -- Data quality metrics
            total_observations INTEGER DEFAULT 0,
            completeness_score DECIMAL(5,2),
            data_quality_score DECIMAL(5,2),

            -- Processing metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_status VARCHAR(20) DEFAULT 'pending',
            processing_notes TEXT,

            -- File information
            source_file_path VARCHAR(500),
            source_file_size INTEGER,
            source_file_hash VARCHAR(64)
        );
        """

        self.manager.execute_statement(create_sql)

        # Create indexes for metadata table
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_metadata_category ON {table_name}(category);",
            f"CREATE INDEX IF NOT EXISTS idx_metadata_priority ON {table_name}(priority);",
            f"CREATE INDEX IF NOT EXISTS idx_metadata_status ON {table_name}(processing_status);",
            f"CREATE INDEX IF NOT EXISTS idx_metadata_updated ON {table_name}(updated_at);",
        ]

        for index_sql in indexes:
            self.manager.execute_statement(index_sql)

        logger.info(f"Dataset metadata table created: {table_name}")

    def create_datasets_table(self) -> None:
        """Create main datasets table with partitioning support."""
        schema = self.schema_config["main_schema"]
        table_name = f"{schema}.istat_datasets"

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Primary key
            id BIGINT PRIMARY KEY DEFAULT nextval('dataset_id_seq'),

            -- Foreign key to metadata
            dataset_id VARCHAR(50) NOT NULL,

            -- Dimensions (for partitioning and filtering)
            year INTEGER NOT NULL,
            territory_code VARCHAR(10),
            territory_name VARCHAR(100),

            -- Time dimension
            time_period VARCHAR(20) NOT NULL,
            time_period_type VARCHAR(10), -- YEAR, QUARTER, MONTH, etc.

            -- Measure dimensions
            measure_code VARCHAR(50),
            measure_name VARCHAR(200),

            -- Attribute dimensions
            gender VARCHAR(10),
            age_group VARCHAR(20),
            sector VARCHAR(50),

            -- Additional categorical dimensions
            dim1_code VARCHAR(50),
            dim1_value VARCHAR(200),
            dim2_code VARCHAR(50),
            dim2_value VARCHAR(200),
            dim3_code VARCHAR(50),
            dim3_value VARCHAR(200),

            -- Processing metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source VARCHAR(100) DEFAULT 'ISTAT',

            -- Constraints
            FOREIGN KEY (dataset_id) REFERENCES {schema}.dataset_metadata(dataset_id)
        );
        """

        # Create sequence for auto-incrementing ID
        self.manager.execute_statement("CREATE SEQUENCE IF NOT EXISTS dataset_id_seq;")

        self.manager.execute_statement(create_sql)

        # Create indexes optimized for common queries
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_datasets_dataset_id ON {table_name}(dataset_id);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_year ON {table_name}(year);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_territory ON {table_name}(territory_code);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_time_period ON {table_name}(time_period);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_measure ON {table_name}(measure_code);",
            f"CREATE INDEX IF NOT EXISTS idx_datasets_composite ON {table_name}(dataset_id, year, territory_code);",
        ]

        for index_sql in indexes:
            self.manager.execute_statement(index_sql)

        logger.info(f"Datasets table created: {table_name}")

    def create_observations_table(self) -> None:
        """Create observations table optimized for statistical values."""
        schema = self.schema_config["main_schema"]
        table_name = f"{schema}.istat_observations"

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Primary key
            id BIGINT PRIMARY KEY DEFAULT nextval('observation_id_seq'),

            -- Foreign key to datasets
            dataset_row_id BIGINT NOT NULL,
            dataset_id VARCHAR(50) NOT NULL,

            -- Partitioning columns
            year INTEGER NOT NULL,
            territory_code VARCHAR(10),

            -- Observation data
            obs_value DECIMAL(20,6),
            obs_status VARCHAR(10), -- Normal, Estimated, Provisional, etc.
            obs_conf VARCHAR(10),   -- Confidentiality status

            -- Value metadata
            value_type VARCHAR(20) DEFAULT 'NUMERIC', -- NUMERIC, STRING, CODE
            string_value VARCHAR(500), -- For non-numeric values

            -- Statistical metadata
            unit_multiplier INTEGER DEFAULT 1,
            decimals INTEGER DEFAULT 2,

            -- Quality flags
            is_estimated BOOLEAN DEFAULT FALSE,
            is_provisional BOOLEAN DEFAULT FALSE,
            confidence_interval_lower DECIMAL(20,6),
            confidence_interval_upper DECIMAL(20,6),

            -- Processing metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_row INTEGER, -- Row in source XML/file

            -- Constraints
            FOREIGN KEY (dataset_id) REFERENCES {schema}.dataset_metadata(dataset_id)
        );
        """

        # Create sequence for auto-incrementing ID
        self.manager.execute_statement(
            "CREATE SEQUENCE IF NOT EXISTS observation_id_seq;"
        )

        self.manager.execute_statement(create_sql)

        # Create indexes for observations table
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_obs_dataset ON {table_name}(dataset_id);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_year ON {table_name}(year);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_territory ON {table_name}(territory_code);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_value ON {table_name}(obs_value);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_composite ON {table_name}(dataset_id, year, territory_code);",
            f"CREATE INDEX IF NOT EXISTS idx_obs_status ON {table_name}(obs_status);",
        ]

        for index_sql in indexes:
            self.manager.execute_statement(index_sql)

        logger.info(f"Observations table created: {table_name}")

    def create_analytics_tables(self) -> None:
        """Create analytics views and materialized tables for performance."""
        analytics_schema = self.schema_config["analytics_schema"]
        main_schema = self.schema_config["main_schema"]

        self.manager.create_schema(analytics_schema)

        # Create analytics view for common aggregations
        view_sql = f"""
        CREATE OR REPLACE VIEW {analytics_schema}.dataset_summary AS
        SELECT
            m.dataset_id,
            m.dataset_name,
            m.category,
            m.priority,
            COUNT(o.id) as total_observations,
            MIN(d.year) as min_year,
            MAX(d.year) as max_year,
            COUNT(DISTINCT d.territory_code) as territory_count,
            AVG(o.obs_value) as avg_value,
            MIN(o.obs_value) as min_value,
            MAX(o.obs_value) as max_value,
            m.completeness_score,
            m.data_quality_score,
            m.updated_at
        FROM {main_schema}.dataset_metadata m
        LEFT JOIN {main_schema}.istat_datasets d ON m.dataset_id = d.dataset_id
        LEFT JOIN {main_schema}.istat_observations o ON d.id = o.dataset_row_id
        GROUP BY m.dataset_id, m.dataset_name, m.category, m.priority,
                 m.completeness_score, m.data_quality_score, m.updated_at;
        """

        self.manager.execute_statement(view_sql)

        # Create time series view
        time_series_view = f"""
        CREATE OR REPLACE VIEW {analytics_schema}.time_series AS
        SELECT
            d.dataset_id,
            d.year,
            d.time_period,
            d.territory_code,
            d.territory_name,
            d.measure_code,
            d.measure_name,
            o.obs_value,
            o.obs_status,
            m.category,
            m.unit_of_measure
        FROM {main_schema}.istat_datasets d
        JOIN {main_schema}.istat_observations o ON d.id = o.dataset_row_id
        JOIN {main_schema}.dataset_metadata m ON d.dataset_id = m.dataset_id
        WHERE o.obs_value IS NOT NULL
        ORDER BY d.dataset_id, d.year, d.time_period;
        """

        self.manager.execute_statement(time_series_view)

        # Create territory aggregation view
        territory_view = f"""
        CREATE OR REPLACE VIEW {analytics_schema}.territory_aggregates AS
        SELECT
            d.territory_code,
            d.territory_name,
            d.year,
            m.category,
            COUNT(*) as indicator_count,
            AVG(o.obs_value) as avg_value,
            SUM(CASE WHEN o.obs_value IS NOT NULL THEN 1 ELSE 0 END) as non_null_count,
            COUNT(*) as total_count,
            (SUM(CASE WHEN o.obs_value IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as completeness_pct
        FROM {main_schema}.istat_datasets d
        JOIN {main_schema}.istat_observations o ON d.id = o.dataset_row_id
        JOIN {main_schema}.dataset_metadata m ON d.dataset_id = m.dataset_id
        GROUP BY d.territory_code, d.territory_name, d.year, m.category;
        """

        self.manager.execute_statement(territory_view)

        logger.info(f"Analytics tables/views created in schema: {analytics_schema}")

    def insert_dataset_metadata(self, metadata: Dict) -> None:
        """Insert or update dataset metadata.

        Args:
            metadata: Dictionary with dataset metadata
        """
        schema = self.schema_config["main_schema"]
        table_name = f"{schema}.dataset_metadata"

        # Convert metadata to proper format
        insert_data = {
            "dataset_id": metadata.get("dataset_id"),
            "dataset_name": metadata.get("dataset_name", ""),
            "category": metadata.get("category", "altro"),
            "priority": metadata.get("priority", 1),
            "subcategory": metadata.get("subcategory"),
            "description": metadata.get("description"),
            "frequency": metadata.get("frequency"),
            "unit_of_measure": metadata.get("unit_of_measure"),
            "geographic_level": metadata.get("geographic_level"),
            "completeness_score": metadata.get("completeness_score"),
            "data_quality_score": metadata.get("data_quality_score"),
            "processing_status": metadata.get("processing_status", "processed"),
            "source_file_path": metadata.get("source_file_path"),
            "updated_at": datetime.now(),
        }

        # Use UPSERT pattern for DuckDB
        upsert_sql = f"""
        INSERT INTO {table_name} (
            dataset_id, dataset_name, category, priority, subcategory,
            description, frequency, unit_of_measure, geographic_level,
            completeness_score, data_quality_score, processing_status,
            source_file_path, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) ON CONFLICT (dataset_id) DO UPDATE SET
            dataset_name = EXCLUDED.dataset_name,
            category = EXCLUDED.category,
            priority = EXCLUDED.priority,
            description = EXCLUDED.description,
            completeness_score = EXCLUDED.completeness_score,
            data_quality_score = EXCLUDED.data_quality_score,
            processing_status = EXCLUDED.processing_status,
            updated_at = EXCLUDED.updated_at;
        """

        try:
            self.manager.execute_statement(upsert_sql, list(insert_data.values()))
            logger.debug(
                f"Metadata inserted/updated for dataset: {metadata.get('dataset_id')}"
            )
        except Exception as e:
            logger.error(f"Failed to insert metadata: {e}")
            raise

    def bulk_insert_observations(self, df: pd.DataFrame, dataset_id: str) -> None:
        """Bulk insert observations from DataFrame.

        Args:
            df: DataFrame with observation data
            dataset_id: Associated dataset ID
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for dataset {dataset_id}")
            return

        # Add dataset_id and processing columns
        df = df.copy()
        df["dataset_id"] = dataset_id
        df["created_at"] = datetime.now()

        # Map common columns to schema
        column_mapping = {
            "OBS_VALUE": "obs_value",
            "obs_value": "obs_value",
            "TIME_PERIOD": "year",
            "year": "year",
            "TERRITORY": "territory_code",
            "territory_code": "territory_code",
            "OBS_STATUS": "obs_status",
            "obs_status": "obs_status",
        }

        # Rename columns to match schema
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})

        # Add all required columns with defaults to match table schema
        required_columns = {
            "dataset_row_id": 1,  # Default value, will be updated
            "obs_conf": None,
            "value_type": "NUMERIC",
            "string_value": None,
            "unit_multiplier": 1,
            "decimals": 2,
            "is_estimated": False,
            "is_provisional": False,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "source_row": None,
        }

        # Add missing columns with defaults
        for col_name, default_value in required_columns.items():
            if col_name not in df.columns:
                df[col_name] = default_value

        # Reorder columns to match table structure (optional, but helps with clarity)
        expected_columns = [
            "dataset_row_id",
            "dataset_id",
            "year",
            "territory_code",
            "obs_value",
            "obs_status",
            "obs_conf",
            "value_type",
            "string_value",
            "unit_multiplier",
            "decimals",
            "is_estimated",
            "is_provisional",
            "confidence_interval_lower",
            "confidence_interval_upper",
            "created_at",
            "source_row",
        ]

        # Select only columns that exist in the DataFrame
        available_columns = [col for col in expected_columns if col in df.columns]
        df = df[available_columns]

        # Insert into observations table using direct SQL to avoid issues with auto-increment ID
        schema = self.schema_config["main_schema"]
        table_name = f"{schema}.istat_observations"

        try:
            # Use explicit column list to avoid ID column issues
            columns_str = ", ".join(available_columns)
            placeholders = ", ".join(["?" for _ in available_columns])

            insert_sql = (
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            )

            # Insert row by row to handle the auto-increment ID properly
            with self.manager.transaction() as conn:
                for _, row in df.iterrows():
                    values = [row[col] for col in available_columns]
                    conn.execute(insert_sql, values)

            logger.info(
                f"Bulk inserted {len(df)} observations for dataset {dataset_id}"
            )
        except Exception as e:
            logger.error(f"Bulk insert failed for dataset {dataset_id}: {e}")
            raise

    def get_table_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all ISTAT tables.

        Returns:
            Dictionary with table statistics
        """
        schema = self.schema_config["main_schema"]

        stats_query = f"""
        SELECT
            'dataset_metadata' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT category) as categories,
            AVG(completeness_score) as avg_completeness
        FROM {schema}.dataset_metadata

        UNION ALL

        SELECT
            'istat_datasets' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT dataset_id) as categories,
            COUNT(DISTINCT year) as avg_completeness
        FROM {schema}.istat_datasets

        UNION ALL

        SELECT
            'istat_observations' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT dataset_id) as categories,
            AVG(obs_value) as avg_completeness
        FROM {schema}.istat_observations;
        """

        try:
            result = self.manager.execute_query(stats_query)
            records = result.to_dict("records")
            # Cast to proper type for MyPy compliance
            return cast(List[Dict[str, Any]], records)
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return []

    def drop_all_tables(self) -> None:
        """Drop all ISTAT tables (for testing/cleanup)."""
        schema = self.schema_config["main_schema"]

        tables = [
            f"{schema}.istat_observations",
            f"{schema}.istat_datasets",
            f"{schema}.dataset_metadata",
        ]

        for table in tables:
            try:
                self.manager.execute_statement(f"DROP TABLE IF EXISTS {table} CASCADE;")
                logger.info(f"Dropped table: {table}")
            except Exception as e:
                logger.warning(f"Failed to drop table {table}: {e}")

        # Drop sequences
        sequences = ["dataset_id_seq", "observation_id_seq"]
        for seq in sequences:
            try:
                self.manager.execute_statement(f"DROP SEQUENCE IF EXISTS {seq};")
            except Exception as e:
                logger.warning(f"Failed to drop sequence {seq}: {e}")


def initialize_schema(manager: Optional[DuckDBManager] = None) -> ISTATSchemaManager:
    """Initialize ISTAT database schema.

    Args:
        manager: Optional DuckDB manager instance

    Returns:
        Configured schema manager
    """
    schema_manager = ISTATSchemaManager(manager)
    schema_manager.create_all_tables()
    return schema_manager
