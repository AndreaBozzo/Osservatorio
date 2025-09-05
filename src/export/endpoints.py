"""
FastAPI export endpoints for Issue #150 - Universal data export.
Provides REST API endpoints for exporting datasets in CSV, JSON, and Parquet formats.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from src.api.dependencies import (
    check_rate_limit,
    get_current_user,
    handle_api_errors,
    log_api_request,
)

from .data_access import ExportDataAccess
from .streaming_exporter import StreamingExporter
from .universal_exporter import UniversalExporter

logger = get_logger(__name__)

# Create router for export endpoints
export_router = APIRouter(prefix="/api/datasets", tags=["Export"])


@export_router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: str = Path(..., description="Dataset ID to export"),
    format: str = Query(..., description="Export format", regex="^(csv|json|parquet)$"),
    columns: Optional[str] = Query(
        None,
        description="Comma-separated list of columns to include (default: all columns)",
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date filter (YYYY-MM-DD format)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date filter (YYYY-MM-DD format)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    limit: Optional[int] = Query(
        None,
        description="Maximum number of rows to export (default: no limit)",
        gt=0,
        le=1000000,
    ),
    stream: Optional[bool] = Query(
        None, description="Force streaming response (auto-detected for large datasets)"
    ),
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _log_request=Depends(log_api_request),
    _error_handler=Depends(handle_api_errors),
):
    """
    Export dataset in specified format with optional filtering.

    **Supported Formats:**
    - `csv`: Comma-separated values (Excel-friendly)
    - `json`: JSON format with metadata
    - `parquet`: Parquet format (data science-friendly)

    **Filtering Options:**
    - `columns`: Select specific columns
    - `start_date`/`end_date`: Date range filtering
    - `limit`: Limit number of rows

    **Performance:**
    - Large datasets (>50k rows) automatically use streaming responses
    - Memory-efficient processing for all export sizes
    - Compressed Parquet format for optimal file size
    """

    logger.info(
        f"Export request - Dataset: {dataset_id}, Format: {format}, User: {getattr(current_user, 'user_id', 'unknown') if current_user else 'unknown'}"
    )

    try:
        # Initialize data access and exporters
        data_access = ExportDataAccess()
        universal_exporter = UniversalExporter()
        streaming_exporter = StreamingExporter()

        # Validate dataset exists
        if not data_access.validate_dataset_exists(dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id}' not found",
            )

        # Parse columns filter
        column_list = None
        if columns:
            column_list = [col.strip() for col in columns.split(",") if col.strip()]
            logger.debug(f"Column filter applied: {column_list}")

        # Get export size estimation
        size_info = data_access.estimate_export_size(dataset_id)
        use_streaming = (
            stream if stream is not None else size_info["recommended_streaming"]
        )

        logger.info(
            f"Export size estimation: {size_info['row_count']} rows, streaming: {use_streaming}"
        )

        # Fetch data
        df = data_access.get_dataset_data(
            dataset_id=dataset_id,
            columns=column_list,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        if df.empty:
            logger.warning(
                f"No data returned for dataset {dataset_id} with applied filters"
            )
            # Return empty response with appropriate content type
            if use_streaming:
                return streaming_exporter.create_streaming_response(
                    df, format, dataset_id
                )
            else:
                empty_export = universal_exporter.export_dataframe(
                    df, format, dataset_id
                )
                content_type = universal_exporter.get_content_type(format)
                file_ext = universal_exporter.get_file_extension(format)
                filename = f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"

                return StreamingResponse(
                    iter(
                        [empty_export]
                        if isinstance(empty_export, str)
                        else [empty_export]
                    ),
                    media_type=content_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )

        # Choose export method based on dataset size
        if use_streaming:
            logger.info(f"Using streaming export for {len(df)} rows")
            return streaming_exporter.create_streaming_response(df, format, dataset_id)
        else:
            logger.info(f"Using standard export for {len(df)} rows")

            # Use universal exporter for smaller datasets
            exported_data = universal_exporter.export_dataframe(
                df=df,
                format=format,
                dataset_id=dataset_id,
                columns=column_list,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            content_type = universal_exporter.get_content_type(format)
            file_ext = universal_exporter.get_file_extension(format)
            filename = f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"

            return StreamingResponse(
                iter(
                    [exported_data]
                    if isinstance(exported_data, str)
                    else [exported_data]
                ),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Export error for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )


@export_router.get("/{dataset_id}/export/info")
async def get_export_info(
    dataset_id: str = Path(..., description="Dataset ID"),
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _log_request=Depends(log_api_request),
    _error_handler=Depends(handle_api_errors),
):
    """
    Get export information for a dataset including size estimates and available columns.

    **Returns:**
    - Dataset metadata
    - Available columns
    - Export size estimates
    - Recommended export settings
    """

    logger.info(
        f"Export info request - Dataset: {dataset_id}, User: {getattr(current_user, 'user_id', 'unknown') if current_user else 'unknown'}"
    )

    try:
        data_access = ExportDataAccess()

        # Validate dataset exists
        if not data_access.validate_dataset_exists(dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id}' not found",
            )

        # Get dataset information
        metadata = data_access.get_dataset_metadata(dataset_id)
        columns = data_access.get_dataset_columns(dataset_id)
        size_info = data_access.estimate_export_size(dataset_id)

        export_info = {
            "dataset_id": dataset_id,
            "metadata": metadata,
            "available_columns": columns,
            "size_estimates": size_info,
            "supported_formats": UniversalExporter.SUPPORTED_FORMATS,
            "max_rows_limit": 1000000,
            "recommendations": {
                "use_streaming": size_info["recommended_streaming"],
                "optimal_format": "parquet"
                if size_info["row_count"] > 10000
                else "csv",
                "estimated_export_time_seconds": min(
                    size_info["row_count"] / 10000, 300
                ),  # Rough estimate
            },
        }

        logger.info(f"Export info generated for dataset {dataset_id}")
        return export_info

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error getting export info for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export information: {str(e)}",
        )


@export_router.get("/export/formats")
async def get_supported_formats(
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
):
    """Get list of supported export formats with descriptions."""

    formats_info = {
        "supported_formats": [
            {
                "format": "csv",
                "description": "Comma-separated values - Excel and business tool friendly",
                "content_type": "text/csv",
                "file_extension": ".csv",
                "pros": ["Widely supported", "Human readable", "Excel compatible"],
                "cons": ["Large file size", "No data types preserved"],
                "best_for": "Business users, Excel analysis, small to medium datasets",
            },
            {
                "format": "json",
                "description": "JSON format with metadata - Developer and API friendly",
                "content_type": "application/json",
                "file_extension": ".json",
                "pros": ["Includes metadata", "Web friendly", "Structured data"],
                "cons": ["Verbose", "Larger than CSV"],
                "best_for": "API consumption, web applications, data with metadata",
            },
            {
                "format": "parquet",
                "description": "Parquet columnar format - Data science and analytics friendly",
                "content_type": "application/octet-stream",
                "file_extension": ".parquet",
                "pros": [
                    "Compact size",
                    "Fast queries",
                    "Type preservation",
                    "Compressed",
                ],
                "cons": ["Binary format", "Requires special tools"],
                "best_for": "Data science, large datasets, analytics workflows",
            },
        ],
        "filtering_options": {
            "columns": "Select specific columns (comma-separated)",
            "start_date": "Filter from date (YYYY-MM-DD)",
            "end_date": "Filter to date (YYYY-MM-DD)",
            "limit": "Maximum rows (1 to 1,000,000)",
            "stream": "Force streaming for any size dataset",
        },
    }

    logger.debug("Returned supported export formats information")
    return formats_info


# TEMPORARY: Test endpoint without authentication for Issue #150 testing
@export_router.get("/test/{dataset_id}/export")
async def test_export_dataset(
    dataset_id: str = Path(..., description="Dataset ID to export"),
    format: str = Query(..., description="Export format", regex="^(csv|json|parquet)$"),
    columns: Optional[str] = Query(
        None,
        description="Comma-separated list of columns to include (default: all columns)",
    ),
    limit: Optional[int] = Query(
        None,
        description="Maximum number of rows to export (default: no limit)",
        gt=0,
        le=1000000,
    ),
):
    """
    TEMPORARY: Test export endpoint without authentication for Issue #150 testing.
    This will be removed once authentication is properly configured.
    """

    logger.info(f"TEST Export request - Dataset: {dataset_id}, Format: {format}")

    try:
        # Initialize data access and exporters
        data_access = ExportDataAccess()
        universal_exporter = UniversalExporter()

        # Validate dataset exists
        if not data_access.validate_dataset_exists(dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset '{dataset_id}' not found",
            )

        # Parse columns filter
        column_list = None
        if columns:
            column_list = [col.strip() for col in columns.split(",") if col.strip()]
            logger.debug(f"Column filter applied: {column_list}")

        # Fetch data
        df = data_access.get_dataset_data(
            dataset_id=dataset_id,
            columns=column_list,
            limit=limit,
        )

        if df.empty:
            logger.warning(f"No data returned for dataset {dataset_id}")
            # Return empty response
            empty_export = universal_exporter.export_dataframe(df, format, dataset_id)
            content_type = universal_exporter.get_content_type(format)
            file_ext = universal_exporter.get_file_extension(format)
            filename = f"{dataset_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"

            return StreamingResponse(
                iter(
                    [empty_export] if isinstance(empty_export, str) else [empty_export]
                ),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        logger.info(f"Exporting {len(df)} rows in {format} format")

        # Use universal exporter
        exported_data = universal_exporter.export_dataframe(
            df=df,
            format=format,
            dataset_id=dataset_id,
            columns=column_list,
            limit=limit,
        )

        content_type = universal_exporter.get_content_type(format)
        file_ext = universal_exporter.get_file_extension(format)
        filename = f"{dataset_id}_test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"

        return StreamingResponse(
            iter(
                [exported_data] if isinstance(exported_data, str) else [exported_data]
            ),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"TEST Export error for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )
