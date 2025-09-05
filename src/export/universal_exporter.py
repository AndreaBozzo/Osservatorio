"""
Universal data exporter for CSV, JSON, and Parquet formats.
Simple, focused implementation for Issue #150 export requirements.
"""

import io
import json
from datetime import datetime
from typing import Optional, Union

import pandas as pd

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

logger = get_logger(__name__)


class UniversalExporter:
    """Universal exporter supporting CSV, JSON, and Parquet formats."""

    SUPPORTED_FORMATS = ["csv", "json", "parquet"]

    def __init__(self):
        """Initialize the universal exporter."""
        pass

    def export_dataframe(
        self,
        df: pd.DataFrame,
        format: str,
        dataset_id: str,
        columns: Optional[list[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Union[str, bytes]:
        """
        Export DataFrame to specified format with optional filtering.

        Args:
            df: Source DataFrame
            format: Export format (csv, json, parquet)
            dataset_id: Dataset identifier for metadata
            columns: List of columns to include (None = all)
            start_date: Filter start date (YYYY-MM-DD format)
            end_date: Filter end date (YYYY-MM-DD format)
            limit: Maximum number of rows

        Returns:
            Exported data as string (CSV/JSON) or bytes (Parquet)
        """
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS}"
            )

        if df.empty:
            logger.warning(f"Empty DataFrame provided for export to {format}")
            return self._export_empty(format)

        # Apply filtering
        filtered_df = self._apply_filters(df, columns, start_date, end_date, limit)

        logger.info(
            f"Exporting {len(filtered_df)} rows to {format} format for dataset {dataset_id}"
        )

        # Export based on format
        if format == "csv":
            return self._export_csv(filtered_df)
        elif format == "json":
            return self._export_json(filtered_df, dataset_id)
        elif format == "parquet":
            return self._export_parquet(filtered_df)

    def _apply_filters(
        self,
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Apply filtering options to DataFrame."""
        result_df = df.copy()

        # Column filtering
        if columns:
            available_columns = [col for col in columns if col in result_df.columns]
            if available_columns:
                result_df = result_df[available_columns]
                logger.debug(f"Filtered to columns: {available_columns}")
            else:
                logger.warning(
                    f"None of requested columns {columns} found in DataFrame"
                )

        # Date filtering (look for common date column names)
        date_columns = []
        for col in result_df.columns:
            col_lower = col.lower()
            if any(
                date_word in col_lower for date_word in ["time", "date", "anno", "year"]
            ):
                date_columns.append(col)

        if date_columns and (start_date or end_date):
            # Use the first date column found
            date_col = date_columns[0]
            logger.debug(f"Using date column '{date_col}' for filtering")

            try:
                # Convert date column to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(result_df[date_col]):
                    result_df[date_col] = pd.to_datetime(
                        result_df[date_col], errors="coerce"
                    )

                if start_date:
                    start_dt = pd.to_datetime(start_date)
                    result_df = result_df[result_df[date_col] >= start_dt]
                    logger.debug(f"Filtered from {start_date}")

                if end_date:
                    end_dt = pd.to_datetime(end_date)
                    result_df = result_df[result_df[date_col] <= end_dt]
                    logger.debug(f"Filtered to {end_date}")

            except Exception as e:
                logger.warning(f"Date filtering failed: {e}")

        # Limit filtering
        if limit and limit > 0:
            result_df = result_df.head(limit)
            logger.debug(f"Limited to {limit} rows")

        return result_df

    def _export_csv(self, df: pd.DataFrame) -> str:
        """Export DataFrame to CSV format."""
        return df.to_csv(index=False)

    def _export_json(self, df: pd.DataFrame, dataset_id: str) -> str:
        """Export DataFrame to JSON format with metadata."""
        # Convert DataFrame to records
        records = df.to_dict("records")

        # Create JSON with metadata
        export_data = {
            "metadata": {
                "dataset_id": dataset_id,
                "exported_at": datetime.now().isoformat(),
                "total_records": len(records),
                "columns": list(df.columns),
            },
            "data": records,
        }

        return json.dumps(export_data, default=str, ensure_ascii=False, indent=2)

    def _export_parquet(self, df: pd.DataFrame) -> bytes:
        """Export DataFrame to Parquet format."""
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, compression="snappy")
        return buffer.getvalue()

    def _export_empty(self, format: str) -> Union[str, bytes]:
        """Handle empty DataFrame export for each format."""
        if format == "csv":
            return ""
        elif format == "json":
            return json.dumps(
                {
                    "metadata": {
                        "exported_at": datetime.now().isoformat(),
                        "total_records": 0,
                        "columns": [],
                    },
                    "data": [],
                }
            )
        elif format == "parquet":
            # Create empty parquet file
            empty_df = pd.DataFrame()
            buffer = io.BytesIO()
            empty_df.to_parquet(buffer, index=False)
            return buffer.getvalue()

    def get_content_type(self, format: str) -> str:
        """Get appropriate Content-Type header for format."""
        content_types = {
            "csv": "text/csv",
            "json": "application/json",
            "parquet": "application/octet-stream",
        }
        return content_types.get(format, "application/octet-stream")

    def get_file_extension(self, format: str) -> str:
        """Get file extension for format."""
        extensions = {"csv": ".csv", "json": ".json", "parquet": ".parquet"}
        return extensions.get(format, ".dat")
