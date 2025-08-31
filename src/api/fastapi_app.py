"""
FastAPI REST API for Osservatorio ISTAT Data Platform

Production-ready REST API providing:
- Dataset management and querying
- JWT-based authentication with API keys
- Rate limiting and security middleware
- Export capabilities (CSV, JSON, Parquet)
- Comprehensive audit logging
- OpenAPI documentation with examples

Performance targets:
- Dataset List: <100ms for 1000 datasets
- Dataset Detail: <200ms with data included
- OData Query: <500ms for 10k records
- Authentication: <50ms per request
"""

import time
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from auth.security_middleware import SecurityHeadersMiddleware
from database.sqlite.repository import get_unified_repository
from ingestion.simple_pipeline import create_simple_pipeline
from utils.config import get_config
from utils.logger import get_logger

from .dependencies import (
    check_rate_limit,
    get_auth_manager,
    get_current_user,
    get_istat_client,
    get_jwt_manager,
    get_repository,
    handle_api_errors,
    log_api_request,
    require_admin,
    require_write,
    validate_dataset_id,
)
from .models import (
    APIKeyCreate,
    APIKeyListResponse,
    APIKeyResponse,
    Dataset,
    DatasetDetailResponse,
    DatasetListResponse,
    ErrorResponse,
    HealthCheckResponse,
    TimeSeriesResponse,
    UsageAnalyticsResponse,
)
from .odata import create_odata_router

logger = get_logger(__name__)
config = get_config()

# FastAPI application
app = FastAPI(
    title="Osservatorio ISTAT Data Platform API",
    description="""
    Production-ready REST API for accessing ISTAT statistical data with advanced analytics capabilities.

    ## Features
    - **Dataset Management**: Browse and access Italian statistical datasets
    - **Time Series Data**: Query time series with flexible filtering
    - **Export Capabilities**: Universal export formats (CSV, JSON, Parquet)
    - **JWT Authentication**: Secure API key-based authentication
    - **Rate Limiting**: Configurable rate limits per API key
    - **Audit Logging**: Comprehensive request and usage tracking

    ## Authentication
    1. Obtain an API key from your administrator
    2. Use the `/auth/token` endpoint to get a JWT token
    3. Include the token in the `Authorization: Bearer <token>` header

    ## Rate Limits
    - Default: 100 requests per hour per API key
    - Configurable per API key
    - Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

    ## Data Sources
    - **Metadata**: SQLite database for dataset registry and user management
    - **Analytics**: DuckDB for high-performance time series analytics
    - **Source**: Italian National Institute of Statistics (ISTAT)
    """,
    version="1.0.0",
    contact={
        "name": "Osservatorio ISTAT Team",
        "email": "admin@osservatorio-istat.it",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware - Order matters: security headers first, then CORS, then compression
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format"""
    error_response = ErrorResponse(
        error_type="http_error",
        error_code=f"HTTP_{exc.status_code}",
        detail=exc.detail,
        instance=str(request.url),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    error_response = ErrorResponse(
        error_type="internal_error",
        error_code="INTERNAL_SERVER_ERROR",
        detail="An unexpected error occurred",
        instance=str(request.url),
    )
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(error_response),
    )


# Middleware for response headers and timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time and rate limit headers"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Add timing header
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

    # Add rate limit headers if available
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value

    return response


# Health Check Endpoint
@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check(repository=Depends(get_repository)):
    """
    Health check endpoint for monitoring system status.

    Returns system health including database connectivity,
    component status, and basic statistics.
    """
    try:
        system_status = repository.get_system_status()

        return HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            components={
                "sqlite_metadata": {
                    "status": system_status.get("metadata_database", {}).get(
                        "status", "unknown"
                    ),
                    "stats": system_status.get("metadata_database", {}).get(
                        "stats", {}
                    ),
                },
                "duckdb_analytics": {
                    "status": system_status.get("analytics_database", {}).get(
                        "status", "unknown"
                    ),
                    "stats": system_status.get("analytics_database", {}).get(
                        "stats", {}
                    ),
                },
                "cache": system_status.get("cache", {}),
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_health = HealthCheckResponse(
            status="unhealthy", version="1.0.0", components={"error": str(e)}
        )
        return JSONResponse(
            status_code=503,
            content=jsonable_encoder(error_health),
        )


# Additional Health Check Endpoints (Issue #134)
@app.get("/health/live", tags=["System"])
async def liveness_probe():
    """
    Kubernetes liveness probe - basic service availability.
    Returns 200 if service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "osservatorio-api",
    }


@app.get("/health/ready", tags=["System"])
async def readiness_probe(repository=Depends(get_repository)):
    """
    Kubernetes readiness probe - service ready to serve traffic.
    Checks database connectivity and core dependencies.
    """
    try:
        # Basic database connectivity check
        system_status = repository.get_system_status()

        # Check if databases are accessible
        metadata_ok = (
            system_status.get("metadata_database", {}).get("status") == "connected"
        )
        analytics_ok = (
            system_status.get("analytics_database", {}).get("status") == "connected"
        )

        if metadata_ok and analytics_ok:
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "database": "healthy",
                    "metadata_db": "connected",
                    "analytics_db": "connected",
                },
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat(),
                    "checks": {
                        "metadata_db": "connected" if metadata_ok else "disconnected",
                        "analytics_db": "connected" if analytics_ok else "disconnected",
                    },
                },
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            },
        )


@app.get("/health/db", tags=["System"])
async def database_health(repository=Depends(get_repository)):
    """
    Database connectivity health check.
    """
    try:
        system_status = repository.get_system_status()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "databases": {
                "metadata": system_status.get("metadata_database", {}),
                "analytics": system_status.get("analytics_database", {}),
            },
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            },
        )


@app.get("/health/external", tags=["System"])
async def external_dependencies_health(istat_client=Depends(get_istat_client)):
    """
    External dependencies health check (ISTAT APIs, etc.).
    """
    try:
        # Check ISTAT API connectivity
        istat_health = istat_client.health_check()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "external_services": {"istat_api": istat_health},
        }
    except Exception as e:
        logger.error(f"External dependencies health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "external_services": {"istat_api": {"status": "unreachable"}},
            },
        )


@app.get("/health/metrics", tags=["System"])
async def metrics_health(repository=Depends(get_repository)):
    """
    Basic system metrics for monitoring.
    """
    try:
        import psutil

        # Get basic system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)

        # Get database stats
        system_status = repository.get_system_status()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": cpu_percent,
                "memory_available_mb": memory.available / 1024 / 1024,
            },
            "database_stats": {
                "metadata": system_status.get("metadata_database", {}).get("stats", {}),
                "analytics": system_status.get("analytics_database", {}).get(
                    "stats", {}
                ),
            },
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            },
        )


@app.get("/health/cache", tags=["System"])
async def cache_health():
    """
    Redis cache connectivity health check.
    """
    try:
        # For now, return healthy - Redis connectivity can be implemented later
        # This maintains compatibility with docker-compose health monitoring
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cache": {
                "redis": "not_configured",
                "message": "Redis health check not yet implemented",
            },
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            },
        )


# Dataset Endpoints
@app.get("/datasets", response_model=DatasetListResponse, tags=["Datasets"])
@handle_api_errors
async def list_datasets(
    category: Optional[str] = Query(None, description="Filter by dataset category"),
    with_analytics: Optional[bool] = Query(
        None, description="Filter by analytics data presence"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    include_metadata: bool = Query(False, description="Include dataset metadata"),
    repository=Depends(get_repository),
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    List datasets with filtering and pagination.

    Supports filtering by category and analytics data presence.
    Results are paginated with configurable page size.

    **Performance**: Target <100ms for 1000 datasets
    """
    try:
        # Get datasets from repository
        datasets = repository.list_datasets_complete(
            category=category, with_analytics=with_analytics
        )

        # Apply pagination
        total_count = len(datasets)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_datasets = datasets[start_idx:end_idx]

        # Convert to response format
        dataset_models = []
        for dataset in paginated_datasets:
            dataset_model = Dataset(
                dataset_id=dataset["dataset_id"],
                name=dataset["name"],
                category=dataset["category"],
                description=dataset.get("description"),
                istat_agency=dataset.get("istat_agency"),
                priority=dataset.get("priority", 5),
                id=dataset.get("id"),
                status=dataset.get("status", "active"),
                analytics_stats=dataset.get("analytics_stats"),
                has_analytics_data=dataset.get("has_analytics_data", False),
                created_at=dataset.get("created_at"),
                updated_at=dataset.get("updated_at"),
            )
            dataset_models.append(dataset_model)

        return DatasetListResponse(
            datasets=dataset_models,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count,
        )

    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve datasets",
        )


@app.get(
    "/datasets/{dataset_id}", response_model=DatasetDetailResponse, tags=["Datasets"]
)
@handle_api_errors
async def get_dataset_detail(
    dataset_id: str = Path(..., description="ISTAT dataset identifier"),
    include_data: bool = Query(False, description="Include actual data observations"),
    limit: Optional[int] = Query(
        None, ge=1, le=10000, description="Limit number of observations"
    ),
    repository=Depends(get_repository),
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Get detailed information about a specific dataset.

    Optionally includes actual data observations with configurable limit.

    **Performance**: Target <200ms with data included
    """
    try:
        # Validate dataset ID
        dataset_id = validate_dataset_id(dataset_id)

        # Get dataset details
        dataset = repository.get_dataset_complete(dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found",
            )

        # Convert to response format
        dataset_model = Dataset(
            dataset_id=dataset["dataset_id"],
            name=dataset["name"],
            category=dataset["category"],
            description=dataset.get("description"),
            istat_agency=dataset.get("istat_agency"),
            priority=dataset.get("priority", 5),
            id=dataset.get("id"),
            analytics_stats=dataset.get("analytics_stats"),
            has_analytics_data=dataset.get("has_analytics_data", False),
            created_at=dataset.get("created_at"),
            updated_at=dataset.get("updated_at"),
        )

        # Get data if requested
        data = None
        if include_data and dataset.get("has_analytics_data"):
            time_series = repository.get_dataset_time_series(dataset_id=dataset_id)
            if limit:
                time_series = time_series[:limit]
            data = time_series

        return DatasetDetailResponse(dataset=dataset_model, data=data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dataset details",
        )


@app.get(
    "/datasets/{dataset_id}/timeseries",
    response_model=TimeSeriesResponse,
    tags=["Datasets"],
)
@handle_api_errors
async def get_dataset_timeseries(
    dataset_id: str = Path(..., description="ISTAT dataset identifier"),
    territory_code: Optional[str] = Query(None, description="Filter by territory code"),
    measure_code: Optional[str] = Query(None, description="Filter by measure code"),
    start_year: Optional[int] = Query(
        None, ge=1900, le=2100, description="Start year filter"
    ),
    end_year: Optional[int] = Query(
        None, ge=1900, le=2100, description="End year filter"
    ),
    repository=Depends(get_repository),
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Get time series data for a dataset with flexible filtering.

    Supports filtering by territory, measure, and time period.
    Results include all available metadata for each data point.
    """
    try:
        # Validate parameters
        dataset_id = validate_dataset_id(dataset_id)

        if end_year and start_year and end_year < start_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_year must be greater than or equal to start_year",
            )

        # Get time series data
        time_series = repository.get_dataset_time_series(
            dataset_id=dataset_id,
            territory_code=territory_code,
            measure_code=measure_code,
            start_year=start_year,
            end_year=end_year,
        )

        # Prepare filters applied info
        filters_applied = {
            "dataset_id": dataset_id,
            "territory_code": territory_code,
            "measure_code": measure_code,
            "start_year": start_year,
            "end_year": end_year,
        }

        return TimeSeriesResponse(
            dataset_id=dataset_id,
            data=time_series,
            filters_applied=filters_applied,
            total_points=len(time_series),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get time series for {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve time series data",
        )


# Authentication Endpoints
@app.post("/auth/token", response_model=APIKeyResponse, tags=["Authentication"])
@handle_api_errors
async def create_auth_token(
    api_key_request: APIKeyCreate,
    repository=Depends(get_repository),
    current_user=Depends(require_admin()),
    auth_manager=Depends(get_auth_manager),
    jwt_manager=Depends(get_jwt_manager),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Create a new API key and return JWT token.

    **Admin only**: Requires admin scope to create new API keys.
    Returns the API key (shown only once) and JWT token for immediate use.
    """
    try:
        # Create API key
        expires_days = None
        if api_key_request.expires_at:
            # Calculate days from now to expiration
            expires_days = (api_key_request.expires_at - datetime.now()).days

        api_key_data = auth_manager.generate_api_key(
            name=api_key_request.name,
            scopes=[scope.value for scope in api_key_request.scopes],
            expires_days=expires_days,
        )

        if not api_key_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key",
            )

        # Create JWT token
        jwt_manager.create_access_token(api_key_data)

        return APIKeyResponse(
            api_key=api_key_data.key,
            key_info={
                "id": api_key_data.id,
                "name": api_key_data.name,
                "scopes": api_key_data.scopes,
                "rate_limit": api_key_request.rate_limit,  # Use requested rate limit
                "is_active": api_key_data.is_active,
                "expires_at": api_key_data.expires_at,
                "created_at": api_key_data.created_at,
                "last_used": api_key_data.last_used,
                "usage_count": api_key_data.usage_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@app.get("/auth/keys", response_model=APIKeyListResponse, tags=["Authentication"])
@handle_api_errors
async def list_api_keys(
    repository=Depends(get_repository),
    current_user=Depends(require_admin()),
    auth_manager=Depends(get_auth_manager),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    List all API keys with usage statistics.

    **Admin only**: Requires admin scope to view API keys.
    Returns key information without sensitive data.
    """
    try:
        # Get all API keys
        api_keys = auth_manager.list_api_keys()

        return APIKeyListResponse(
            api_keys=[
                {
                    "id": key.id,
                    "name": key.name,
                    "scopes": key.scopes,
                    "rate_limit": key.rate_limit,
                    "is_active": key.is_active,
                    "expires_at": key.expires_at,
                    "last_used": key.last_used,
                    "usage_count": key.usage_count,
                    "created_at": key.created_at,
                }
                for key in api_keys
            ],
            total_count=len(api_keys),
        )

    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys",
        )


# Usage Analytics Endpoint
@app.get("/analytics/usage", response_model=UsageAnalyticsResponse, tags=["Analytics"])
@handle_api_errors
async def get_usage_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    api_key_id: Optional[int] = Query(None, description="Filter by API key ID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    group_by: str = Query("day", description="Group by period (day, week, month)"),
    repository=Depends(get_repository),
    current_user=Depends(require_admin()),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Get usage analytics and statistics.

    **Admin only**: Requires admin scope to view usage analytics.
    Provides insights into API usage patterns, performance, and errors.
    """
    try:
        # This is a placeholder implementation
        # In a real system, you would query audit logs and aggregate usage data

        # Mock response for demonstration
        stats = [
            {
                "date": "2024-01-20",
                "endpoint": "/datasets",
                "request_count": 150,
                "avg_response_time_ms": 85.5,
                "error_count": 2,
            },
            {
                "date": "2024-01-20",
                "endpoint": "/datasets/{id}",
                "request_count": 89,
                "avg_response_time_ms": 125.2,
                "error_count": 0,
            },
        ]

        summary = {
            "total_requests": 239,
            "avg_response_time_ms": 98.7,
            "error_rate": 0.008,
            "most_used_endpoint": "/datasets",
        }

        time_range = {
            "start_date": start_date or "2024-01-20",
            "end_date": end_date or "2024-01-20",
        }

        return UsageAnalyticsResponse(
            stats=stats, summary=summary, time_range=time_range
        )

    except Exception as e:
        logger.error(f"Failed to get usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics",
        )


# Include OData router for export capabilities
odata_router = create_odata_router()
app.include_router(odata_router, prefix="/odata", tags=["OData"])

# Issue #153: Dataflow Analysis router removed for MVP


# OpenAPI customization
def custom_openapi():
    """Custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/token endpoint",
        }
    }

    # Add security requirement to all protected endpoints
    for path_data in openapi_schema["paths"].values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "tags" in operation:
                if operation["tags"][0] != "System":  # Exclude health check
                    operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ISTAT API Integration Endpoints
@app.get("/api/istat/status", tags=["ISTAT API"], summary="Get ISTAT API client status")
@handle_api_errors
async def get_istat_status(
    current_user=Depends(get_current_user),
    istat_client=Depends(get_istat_client),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Get current status of the production ISTAT API client.

    Returns client health, metrics, and operational status including:
    - Connection status and circuit breaker state
    - Rate limiting information
    - Performance metrics
    - Recent request statistics
    """
    try:
        status = istat_client.get_status()
        health = istat_client.health_check()

        return {
            "client_status": status,
            "api_health": health,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get ISTAT client status: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ISTAT API client error: {str(e)}",
        )


# Issue #153: /api/istat/dataflows endpoint removed for MVP - disconnected from real ingestion pipeline


@app.get(
    "/api/istat/dataset/{dataset_id}",
    tags=["ISTAT API"],
    summary="Fetch specific ISTAT dataset",
)
@handle_api_errors
async def fetch_istat_dataset(
    dataset_id: str = Path(..., description="ISTAT dataset identifier"),
    include_data: bool = Query(True, description="Include dataset data in response"),
    with_quality: bool = Query(False, description="Include data quality validation"),
    current_user=Depends(get_current_user),
    istat_client=Depends(get_istat_client),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Fetch specific dataset from ISTAT API.

    Retrieves dataset structure and optionally data from ISTAT SDMX API.
    Includes basic data quality validation for MVP.
    """
    try:
        if with_quality:
            # Fetch with quality validation
            quality_result = istat_client.fetch_with_quality_validation(dataset_id)
            dataset_result = istat_client.fetch_dataset(
                dataset_id, include_data=include_data
            )

            return {
                "dataset": dataset_result,
                "quality": {
                    "quality_score": quality_result.quality_score,
                    "completeness": quality_result.completeness,
                    "consistency": quality_result.consistency,
                    "validation_errors": quality_result.validation_errors,
                    "timestamp": quality_result.timestamp.isoformat(),
                },
            }
        else:
            # Standard fetch
            result = istat_client.fetch_dataset(dataset_id, include_data=include_data)
            return result

    except Exception as e:
        logger.error(f"Failed to fetch ISTAT dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ISTAT API error: {str(e)}",
        )


@app.post(
    "/api/istat/sync/{dataset_id}",
    tags=["ISTAT API"],
    summary="Sync dataset to repository",
)
@handle_api_errors
async def sync_istat_dataset(
    dataset_id: str = Path(..., description="ISTAT dataset identifier"),
    current_user=Depends(require_write),  # Requires write permissions
    istat_client=Depends(get_istat_client),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
):
    """
    Synchronize ISTAT dataset to local repository.

    Fetches dataset from ISTAT API and synchronizes it with the local
    SQLite metadata and DuckDB analytics storage.

    Requires write permissions.
    """
    try:
        # Fetch dataset with data
        dataset_result = istat_client.fetch_dataset(dataset_id, include_data=True)

        if dataset_result.get("data", {}).get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to fetch dataset data from ISTAT API",
            )

        # Sync to repository
        sync_result = istat_client.sync_to_repository(dataset_result)

        return {
            "sync_result": {
                "dataset_id": sync_result.dataset_id,
                "records_synced": sync_result.records_synced,
                "sync_time": sync_result.sync_time,
                "metadata_updated": sync_result.metadata_updated,
                "timestamp": sync_result.timestamp.isoformat(),
            },
            "dataset_info": {
                "observations_count": dataset_result.get("data", {}).get(
                    "observations_count", 0
                ),
                "data_size": dataset_result.get("data", {}).get("size", 0),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync ISTAT dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Sync error: {str(e)}",
        )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Osservatorio ISTAT FastAPI application")

    try:
        # Initialize simple ingestion pipeline FIRST (creates schema)
        ingestion_pipeline = create_simple_pipeline()
        app.state.ingestion_pipeline = ingestion_pipeline
        logger.info("Simple ingestion pipeline initialized")

        # Initialize ISTAT client
        istat_client = get_istat_client()
        istat_health = istat_client.health_check()
        logger.info(f"ISTAT API client status: {istat_health.get('status', 'unknown')}")

        # Initialize repository AFTER schema is created
        repository = get_unified_repository()
        status = repository.get_system_status()
        logger.info(f"System status: {status}")

        logger.info("FastAPI application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


# Issue #149 - Simple Ingestion Pipeline Endpoints
@app.post(
    "/ingestion/run-all",
    tags=["Ingestion"],
    summary="Run ingestion for all 7 priority datasets",
)
async def run_ingestion_all(request: Request):
    """
    Trigger ingestion for all 7 priority ISTAT datasets.

    Returns comprehensive results including success/failure status for each dataset.
    """
    pipeline = app.state.ingestion_pipeline

    try:
        results = await pipeline.ingest_all_priority_datasets()

        # Simple logging without auth dependency
        logger.info(
            f"API request: POST /ingestion/run-all - 200 - {len(str(results))} bytes"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": results["success"],
                "message": f"Ingestion completed: {results['successful']}/{results['total_datasets']} datasets successful",
                "details": results,
            },
        )

    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Batch ingestion failed",
            },
        )


@app.post(
    "/ingestion/run/{dataset_id}",
    tags=["Ingestion"],
    summary="Run ingestion for single dataset",
)
async def run_ingestion_single(
    dataset_id: str = Path(..., description="ISTAT dataset ID"), request: Request = None
):
    """
    Trigger ingestion for a single dataset.

    Supports both priority datasets and custom dataset IDs.
    """
    pipeline = app.state.ingestion_pipeline

    try:
        result = await pipeline.ingest_single_dataset(dataset_id)

        # Simple logging without auth dependency
        if request:
            status_code = 200 if result["success"] else 500
            logger.info(
                f"API request: POST /ingestion/run/{dataset_id} - {status_code} - {len(str(result))} bytes"
            )

        status_code = 200 if result["success"] else 500
        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        logger.error(f"Single dataset ingestion failed for {dataset_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "dataset_id": dataset_id,
                "error": str(e),
                "message": f"Ingestion failed for {dataset_id}",
            },
        )


@app.get(
    "/ingestion/status", tags=["Ingestion"], summary="Get ingestion pipeline status"
)
async def get_ingestion_status(request: Request):
    """
    Get current status of the ingestion pipeline.

    Returns information about last runs, dataset status, and system health.
    """
    pipeline = app.state.ingestion_pipeline

    try:
        status = pipeline.get_ingestion_status()

        # Simple logging without auth dependency
        logger.info(
            f"API request: GET /ingestion/status - 200 - {len(str(status))} bytes"
        )

        return JSONResponse(status_code=200, content=status)

    except Exception as e:
        logger.error(f"Failed to get ingestion status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "Failed to retrieve ingestion status"},
        )


@app.get(
    "/ingestion/health",
    tags=["Ingestion"],
    summary="Health check for ingestion pipeline",
)
async def get_ingestion_health(request: Request):
    """
    Simple health check for the ingestion pipeline components.
    """
    pipeline = app.state.ingestion_pipeline

    try:
        health = await pipeline.health_check()

        # Simple logging without auth dependency
        status_code = 200 if health["healthy"] else 503
        logger.info(
            f"API request: GET /ingestion/health - {status_code} - {len(str(health))} bytes"
        )

        status_code = 200 if health["healthy"] else 503
        return JSONResponse(status_code=status_code, content=health)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "healthy": False,
                "error": str(e),
                "message": "Health check failed",
            },
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Osservatorio ISTAT FastAPI application")

    try:
        # Close repository connections
        repository = get_unified_repository()
        repository.close()

        # Close ISTAT client
        from .dependencies import _istat_client

        if _istat_client:
            _istat_client.close()

        logger.info("FastAPI application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Development server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
