"""
Streaming export functionality for large datasets.
Handles memory-efficient export of large data using generators and chunked processing.
"""

import io
import json
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi.responses import StreamingResponse

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .universal_exporter import UniversalExporter

logger = get_logger(__name__)


class StreamingExporter:
    """Memory-efficient streaming exporter for large datasets."""

    def __init__(self, chunk_size: int = 10000):
        """
        Initialize streaming exporter.

        Args:
            chunk_size: Number of rows to process at once
        """
        self.chunk_size = chunk_size
        self.universal_exporter = UniversalExporter()

    def stream_csv_response(
        self, df: pd.DataFrame, dataset_id: str, filename: Optional[str] = None
    ) -> StreamingResponse:
        """Create streaming CSV response for large datasets."""
        if filename is None:
            filename = (
                f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        def csv_generator() -> Generator[str, None, None]:
            if df.empty:
                return

            # Yield CSV header first
            if not df.empty:
                yield df.iloc[:0].to_csv(index=False)  # Header only

            # Stream data in chunks
            for start_idx in range(0, len(df), self.chunk_size):
                end_idx = min(start_idx + self.chunk_size, len(df))
                chunk = df.iloc[start_idx:end_idx]

                # For first chunk, skip header (already sent)
                # For subsequent chunks, don't include header
                chunk_csv = chunk.to_csv(index=False, header=False)
                yield chunk_csv

                logger.debug(
                    f"Streamed CSV chunk {start_idx}-{end_idx} of {len(df)} rows"
                )

        return StreamingResponse(
            csv_generator(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    def stream_json_response(
        self, df: pd.DataFrame, dataset_id: str, filename: Optional[str] = None
    ) -> StreamingResponse:
        """Create streaming JSON response for large datasets."""
        if filename is None:
            filename = (
                f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        def json_generator() -> Generator[str, None, None]:
            # Start JSON structure with metadata
            yield "{\n"
            yield '  "metadata": {\n'
            yield f'    "dataset_id": "{dataset_id}",\n'
            yield f'    "exported_at": "{datetime.now().isoformat()}",\n'
            yield f'    "total_records": {len(df)},\n'
            yield f'    "columns": {json.dumps(list(df.columns))}\n'
            yield "  },\n"
            yield '  "data": [\n'

            if df.empty:
                yield "  ]\n}\n"
                return

            # Stream data records in chunks
            first_record = True
            for start_idx in range(0, len(df), self.chunk_size):
                end_idx = min(start_idx + self.chunk_size, len(df))
                chunk = df.iloc[start_idx:end_idx]

                for _, row in chunk.iterrows():
                    if not first_record:
                        yield ",\n"
                    else:
                        first_record = False

                    record_json = json.dumps(
                        row.to_dict(), default=str, ensure_ascii=False
                    )
                    yield f"    {record_json}"

                logger.debug(
                    f"Streamed JSON chunk {start_idx}-{end_idx} of {len(df)} rows"
                )

            # Close JSON structure
            yield "\n  ]\n}\n"

        return StreamingResponse(
            json_generator(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    def stream_parquet_response(
        self, df: pd.DataFrame, dataset_id: str, filename: Optional[str] = None
    ) -> StreamingResponse:
        """Create streaming Parquet response."""
        if filename is None:
            filename = f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"

        def parquet_generator() -> Generator[bytes, None, None]:
            # For Parquet, we need to write the entire file at once
            # But we can still process in chunks to manage memory
            if df.empty:
                empty_df = pd.DataFrame()
                buffer = io.BytesIO()
                empty_df.to_parquet(buffer, index=False)
                yield buffer.getvalue()
                return

            # For large datasets, we could implement Parquet streaming
            # For now, use standard approach but in manageable chunks
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, compression="snappy")

            # Stream the parquet data in chunks
            parquet_data = buffer.getvalue()
            chunk_size = 64 * 1024  # 64KB chunks for binary data

            for i in range(0, len(parquet_data), chunk_size):
                yield parquet_data[i : i + chunk_size]

            logger.debug(
                f"Streamed Parquet data ({len(parquet_data)} bytes) for {len(df)} rows"
            )

        return StreamingResponse(
            parquet_generator(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    def create_streaming_response(
        self,
        df: pd.DataFrame,
        format: str,
        dataset_id: str,
        filename: Optional[str] = None,
    ) -> StreamingResponse:
        """Create appropriate streaming response based on format."""
        if format == "csv":
            return self.stream_csv_response(df, dataset_id, filename)
        elif format == "json":
            return self.stream_json_response(df, dataset_id, filename)
        elif format == "parquet":
            return self.stream_parquet_response(df, dataset_id, filename)
        else:
            raise ValueError(f"Unsupported streaming format: {format}")

    async def async_stream_from_query_results(
        self,
        query_results: AsyncGenerator[pd.DataFrame, None],
        format: str,
        dataset_id: str,
    ) -> StreamingResponse:
        """Stream export from async query results (for future DuckDB integration)."""
        # Placeholder for async streaming when we integrate with DuckDB
        # This would allow streaming directly from database query results
        # without loading entire dataset into memory

        async def async_generator():
            chunk_count = 0
            async for chunk_df in query_results:
                chunk_count += 1
                logger.debug(
                    f"Processing chunk {chunk_count} with {len(chunk_df)} rows"
                )

                if format == "csv":
                    if chunk_count == 1 and not chunk_df.empty:
                        # Include header for first chunk only
                        yield chunk_df.to_csv(index=False)
                    else:
                        yield chunk_df.to_csv(index=False, header=False)
                # Add other formats as needed

        content_type = self.universal_exporter.get_content_type(format)
        file_ext = self.universal_exporter.get_file_extension(format)
        filename = (
            f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        )

        return StreamingResponse(
            async_generator(),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
