"""
Data access layer for export functionality.
Integrates with the existing UnifiedDataRepository to fetch data for export.
"""

from typing import Optional

import pandas as pd

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from database.sqlite.repository import get_unified_repository

logger = get_logger(__name__)


class ExportDataAccess:
    """Data access layer for export operations."""

    def __init__(self):
        """Initialize with unified repository."""
        self.repository = get_unified_repository()

    def get_dataset_data(
        self,
        dataset_id: str,
        columns: Optional[list[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch dataset data with optional filtering.

        Args:
            dataset_id: Dataset identifier
            columns: List of columns to include
            start_date: Filter start date (YYYY-MM-DD format)
            end_date: Filter end date (YYYY-MM-DD format)
            limit: Maximum number of rows

        Returns:
            DataFrame with requested data
        """
        try:
            # Direct DuckDB query to get actual data from main schema
            from database.duckdb.manager import DuckDBManager

            duckdb = DuckDBManager()

            # Build query for the actual schema
            query = "SELECT * FROM main.istat_observations WHERE dataset_id = ?"
            params = [dataset_id]

            # Add time period filtering if needed
            if start_date:
                query += " AND time_period >= ?"
                params.append(start_date)
            if end_date:
                query += " AND time_period <= ?"
                params.append(end_date)

            # Add limit
            if limit:
                query += f" LIMIT {limit}"

            logger.info(f"Executing DuckDB query for dataset {dataset_id}: {query}")
            result = duckdb.execute_query(query, params)

            if result is not None and not result.empty:
                # Filter columns if specified
                if columns:
                    available_columns = [
                        col for col in columns if col in result.columns
                    ]
                    if available_columns:
                        result = result[available_columns]

                logger.info(
                    f"Successfully fetched {len(result)} rows for dataset {dataset_id}"
                )
                return result
            else:
                logger.warning(f"No data found for dataset {dataset_id}")
                return pd.DataFrame()

            # Fallback to repository method (which currently doesn't work)
            dataset_info = self.repository.get_dataset_complete(dataset_id)
            if not dataset_info:
                logger.error(f"Dataset {dataset_id} not found")
                return pd.DataFrame()

            logger.info(f"Fetching data for dataset: {dataset_id}")

            # Build DuckDB query based on filters
            query = self._build_export_query(
                dataset_id, columns, start_date, end_date, limit
            )

            # Execute query through DuckDB manager
            df = self.repository.execute_analytics_query(query)

            if df is not None and not df.empty:
                logger.info(f"Retrieved {len(df)} rows for dataset {dataset_id}")
                return df
            else:
                logger.warning(f"No data found for dataset {dataset_id}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching dataset data for {dataset_id}: {e}")
            return pd.DataFrame()

    def _build_export_query(
        self,
        dataset_id: str,
        columns: Optional[list[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Build SQL query for data export with filtering."""

        # TODO: Enhance DuckDB integration
        # This is a placeholder implementation. Future enhancements:
        # 1. Use DuckDB query builder for more sophisticated queries
        # 2. Integrate with partitioning strategy for large datasets
        # 3. Add query optimization for different export scenarios
        # 4. Support advanced filtering (regex, ranges, etc.)

        # Base query - assume table name matches dataset_id
        table_name = f"dataset_{dataset_id}"

        # Build SELECT clause
        if columns:
            # Validate column names to prevent SQL injection
            safe_columns = [col for col in columns if col.replace("_", "").isalnum()]
            select_clause = ", ".join(safe_columns) if safe_columns else "*"
        else:
            select_clause = "*"

        query = f"SELECT {select_clause} FROM {table_name}"

        # Build WHERE clause
        where_conditions = []

        if start_date or end_date:
            # TODO: Dynamic date column detection
            # Future enhancement: Query table schema to find date columns automatically
            # For now, use a generic approach - this could be enhanced with metadata
            date_column = "Time"  # Most common in ISTAT data

            if start_date:
                where_conditions.append(f"{date_column} >= '{start_date}'")
            if end_date:
                where_conditions.append(f"{date_column} <= '{end_date}'")

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        # Add ORDER BY for consistent results
        query += " ORDER BY 1"  # Order by first column

        # Add LIMIT
        if limit and limit > 0:
            query += f" LIMIT {limit}"

        logger.debug(f"Built export query: {query}")
        return query

    def get_dataset_metadata(self, dataset_id: str) -> dict:
        """Get dataset metadata for export."""
        try:
            dataset_info = self.repository.get_dataset_complete(dataset_id)
            if dataset_info:
                return {
                    "dataset_id": dataset_id,
                    "name": dataset_info.get("name", ""),
                    "description": dataset_info.get("description", ""),
                    "last_updated": dataset_info.get("last_updated", ""),
                    "total_records": dataset_info.get("total_records", 0),
                    "columns": dataset_info.get("columns", []),
                }
            else:
                return {"dataset_id": dataset_id}

        except Exception as e:
            logger.error(f"Error getting metadata for dataset {dataset_id}: {e}")
            return {"dataset_id": dataset_id}

    def validate_dataset_exists(self, dataset_id: str) -> bool:
        """Check if dataset exists and is accessible."""
        try:
            dataset_info = self.repository.get_dataset_complete(dataset_id)
            return dataset_info is not None
        except Exception as e:
            logger.error(f"Error validating dataset {dataset_id}: {e}")
            return False

    def get_dataset_columns(self, dataset_id: str) -> list[str]:
        """Get list of available columns for a dataset."""
        try:
            # Try to get schema information from DuckDB
            table_name = f"dataset_{dataset_id}"
            schema_query = f"DESCRIBE {table_name}"

            result = self.repository.execute_analytics_query(schema_query)

            if (
                result is not None
                and not result.empty
                and "column_name" in result.columns
            ):
                return result["column_name"].tolist()
            else:
                # Fallback to metadata
                metadata = self.get_dataset_metadata(dataset_id)
                return metadata.get("columns", [])

        except Exception as e:
            logger.error(f"Error getting columns for dataset {dataset_id}: {e}")
            return []

    def estimate_export_size(self, dataset_id: str) -> dict:
        """Estimate export size and performance metrics."""
        try:
            # Get row count
            table_name = f"dataset_{dataset_id}"
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"

            result = self.repository.execute_analytics_query(count_query)
            row_count = 0
            if result is not None and not result.empty:
                row_count = int(result.iloc[0]["row_count"])

            # Estimate sizes based on row count
            # These are rough estimates based on typical ISTAT data
            estimated_csv_size_mb = (row_count * 100) / (
                1024 * 1024
            )  # ~100 bytes per row
            estimated_json_size_mb = (row_count * 150) / (
                1024 * 1024
            )  # ~150 bytes per row
            estimated_parquet_size_mb = (row_count * 50) / (
                1024 * 1024
            )  # ~50 bytes per row (compressed)

            return {
                "row_count": row_count,
                "estimated_sizes": {
                    "csv_mb": round(estimated_csv_size_mb, 2),
                    "json_mb": round(estimated_json_size_mb, 2),
                    "parquet_mb": round(estimated_parquet_size_mb, 2),
                },
                "recommended_streaming": row_count > 50000,  # Stream for large datasets
            }

        except Exception as e:
            logger.error(f"Error estimating export size for dataset {dataset_id}: {e}")
            return {
                "row_count": 0,
                "estimated_sizes": {"csv_mb": 0, "json_mb": 0, "parquet_mb": 0},
                "recommended_streaming": False,
            }
