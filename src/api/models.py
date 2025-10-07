"""
Pydantic models for Osservatorio ISTAT FastAPI REST API

Defines request/response models for all API endpoints with validation,
documentation, and OpenAPI schema generation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


# Core enums for MVP API
class DataflowCategory(str, Enum):
    """Dataflow categories for ISTAT data organization"""

    POPOLAZIONE = "popolazione"
    ECONOMIA = "economia"
    LAVORO = "lavoro"
    TERRITORIO = "territorio"
    ISTRUZIONE = "istruzione"
    SALUTE = "salute"
    ALTRO = "altro"


class RefreshFrequency(str, Enum):
    """Data refresh frequency options"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class APIScope(str, Enum):
    """API access scopes"""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class DatasetStatus(str, Enum):
    """Dataset status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
    ERROR = "error"


# Base Response Models
class APIResponse(BaseModel):
    """Base API response model"""

    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class ErrorResponse(APIResponse):
    """Error response model following RFC 7807"""

    success: bool = False
    error_type: str = Field(..., description="Error type identifier")
    error_code: str = Field(..., description="Machine-readable error code")
    detail: Optional[str] = Field(None, description="Human-readable error description")
    instance: Optional[str] = Field(None, description="URI identifying error instance")


# Dataset Models
class DatasetBase(BaseModel):
    """Base dataset model"""

    dataset_id: str = Field(..., description="ISTAT dataset identifier")
    name: str = Field(..., description="Human-readable dataset name")
    category: str = Field(..., description="Dataset category")
    description: Optional[str] = Field(None, description="Dataset description")
    istat_agency: Optional[str] = Field(None, description="ISTAT agency responsible")
    priority: int = Field(5, ge=1, le=10, description="Dataset priority (1-10)")


class DatasetMetadata(BaseModel):
    """Dataset metadata"""

    frequency: Optional[str] = Field(
        None, description="Data frequency (annual, monthly, etc.)"
    )
    territory_level: Optional[str] = Field(
        None, description="Territory aggregation level"
    )
    measures: Optional[list[str]] = Field(None, description="Available measures")
    time_coverage: Optional[dict[str, int]] = Field(
        None, description="Time coverage (min/max years)"
    )
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")


class DatasetAnalytics(BaseModel):
    """Dataset analytics statistics"""

    record_count: int = Field(0, description="Total number of observations")
    min_year: Optional[int] = Field(None, description="Earliest year with data")
    max_year: Optional[int] = Field(None, description="Latest year with data")
    territory_count: int = Field(0, description="Number of territories covered")
    measure_count: int = Field(0, description="Number of measures available")


class Dataset(DatasetBase):
    """Complete dataset model"""

    id: Optional[int] = Field(None, description="Internal dataset ID")
    status: DatasetStatus = Field(DatasetStatus.ACTIVE, description="Dataset status")
    metadata: Optional[DatasetMetadata] = Field(None, description="Dataset metadata")
    analytics_stats: Optional[DatasetAnalytics] = Field(
        None, description="Analytics statistics"
    )
    has_analytics_data: bool = Field(
        False, description="Whether dataset has analytics data"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class DatasetListResponse(APIResponse):
    """Dataset list response"""

    datasets: list[Dataset] = Field(..., description="List of datasets")
    total_count: int = Field(..., description="Total number of datasets")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")
    has_next: bool = Field(False, description="Whether there are more pages")


class DatasetDetailResponse(APIResponse):
    """Dataset detail response"""

    dataset: Dataset = Field(..., description="Dataset details")
    data: Optional[list[dict[str, Any]]] = Field(
        None, description="Dataset observations (if requested)"
    )


# Time Series Models
class TimeSeriesPoint(BaseModel):
    """Time series data point"""

    year: Optional[int] = Field(None, description="Year")
    time_period: Optional[str] = Field(None, description="Time period (e.g., Q1, M01)")
    territory_code: Optional[str] = Field(None, description="Territory code")
    territory_name: Optional[str] = Field(None, description="Territory name")
    measure_code: Optional[str] = Field(None, description="Measure code")
    measure_name: Optional[str] = Field(None, description="Measure name")
    obs_value: Optional[float] = Field(None, description="Observation value")
    obs_status: Optional[str] = Field(None, description="Observation status")


class TimeSeriesResponse(APIResponse):
    """Time series response"""

    dataset_id: str = Field(..., description="Dataset identifier")
    data: list[TimeSeriesPoint] = Field(..., description="Time series data points")
    filters_applied: dict[str, Any] = Field(
        ..., description="Filters applied to the data"
    )
    total_points: int = Field(..., description="Total number of data points")


# Authentication Models
class APIKeyBase(BaseModel):
    """Base API key model"""

    name: str = Field(..., description="API key name")
    scopes: list[APIScope] = Field([APIScope.READ], description="API key scopes")
    rate_limit: int = Field(100, ge=1, le=10000, description="Rate limit per hour")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class APIKeyCreate(APIKeyBase):
    """API key creation request"""

    pass


class APIKeyInfo(APIKeyBase):
    """API key information (without sensitive data)"""

    id: int = Field(..., description="API key ID")
    is_active: bool = Field(True, description="Whether key is active")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(0, description="Number of times used")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class APIKeyResponse(APIResponse):
    """API key creation response"""

    api_key: str = Field(..., description="Generated API key (only shown once)")
    key_info: APIKeyInfo = Field(..., description="API key information")


class APIKeyListResponse(APIResponse):
    """API key list response"""

    api_keys: list[APIKeyInfo] = Field(..., description="List of API keys")
    total_count: int = Field(..., description="Total number of API keys")


# Usage Analytics Models
class UsageStatsPoint(BaseModel):
    """Usage statistics data point"""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    api_key_id: Optional[int] = Field(
        None, description="API key ID (if filtering by key)"
    )
    endpoint: str = Field(..., description="API endpoint")
    request_count: int = Field(..., description="Number of requests")
    avg_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    error_count: int = Field(0, description="Number of error responses")


class UsageAnalyticsResponse(APIResponse):
    """Usage analytics response"""

    stats: list[UsageStatsPoint] = Field(..., description="Usage statistics")
    summary: dict[str, Any] = Field(..., description="Summary statistics")
    time_range: dict[str, str] = Field(..., description="Time range of the data")


# OData Models
class ODataEntitySet(BaseModel):
    """OData entity set metadata"""

    name: str = Field(..., description="Entity set name")
    kind: str = Field("EntitySet", description="Entity kind")
    url: str = Field(..., description="Entity set URL")


class ODataMetadata(BaseModel):
    """OData service metadata"""

    odata_version: str = Field("4.0", description="OData version")
    entity_sets: list[ODataEntitySet] = Field(..., description="Available entity sets")


class ODataResponse(BaseModel):
    """OData query response"""

    odata_context: str = Field(..., alias="@odata.context", description="OData context")
    odata_count: Optional[int] = Field(
        None, alias="@odata.count", description="Total count (if requested)"
    )
    value: list[dict[str, Any]] = Field(..., description="Query results")


# Query Parameters Models
class DatasetListParams(BaseModel):
    """Dataset list query parameters"""

    category: Optional[str] = Field(None, description="Filter by category")
    with_analytics: Optional[bool] = Field(
        None, description="Filter by analytics data presence"
    )
    status: Optional[DatasetStatus] = Field(None, description="Filter by status")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Page size")
    include_metadata: bool = Field(False, description="Include metadata in response")


class DatasetDetailParams(BaseModel):
    """Dataset detail query parameters"""

    include_data: bool = Field(False, description="Include actual data observations")
    limit: Optional[int] = Field(
        None, ge=1, le=10000, description="Limit number of observations"
    )


class TimeSeriesParams(BaseModel):
    """Time series query parameters"""

    territory_code: Optional[str] = Field(None, description="Filter by territory code")
    measure_code: Optional[str] = Field(None, description="Filter by measure code")
    start_year: Optional[int] = Field(
        None, ge=1900, le=2100, description="Start year filter"
    )
    end_year: Optional[int] = Field(
        None, ge=1900, le=2100, description="End year filter"
    )
    format: str = Field("json", description="Response format (json, csv)")

    @validator("end_year")
    def end_year_after_start(cls, v, values):
        if (
            v is not None
            and "start_year" in values
            and values["start_year"] is not None
        ):
            if v < values["start_year"]:
                raise ValueError("end_year must be greater than or equal to start_year")
        return v


class UsageAnalyticsParams(BaseModel):
    """Usage analytics query parameters"""

    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    api_key_id: Optional[int] = Field(None, description="Filter by API key ID")
    endpoint: Optional[str] = Field(None, description="Filter by endpoint")
    group_by: str = Field("day", description="Group by period (day, week, month)")


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Check timestamp"
    )
    components: dict[str, dict[str, Any]] = Field(
        ..., description="Component health status"
    )

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


# User Authentication Models
class UserRegisterRequest(BaseModel):
    """User registration request"""

    email: str = Field(..., description="User email address")
    password: str = Field(
        ..., min_length=6, description="Password (minimum 6 characters)"
    )

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class UserLoginRequest(BaseModel):
    """User login request"""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class UserAuthResponse(APIResponse):
    """User authentication response"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Token expiration in seconds")
    user_info: dict = Field(..., description="Basic user information")
