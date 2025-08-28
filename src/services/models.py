"""
Domain models for dataflow analysis service.

This module contains Pydantic models that represent the domain objects
used in dataflow analysis operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DataflowCategory(str, Enum):
    """Available dataflow categories with business meaning."""

    POPOLAZIONE = "popolazione"
    ECONOMIA = "economia"
    LAVORO = "lavoro"
    TERRITORIO = "territorio"
    ISTRUZIONE = "istruzione"
    SALUTE = "salute"
    ALTRI = "altri"


class RefreshFrequency(str, Enum):
    """Suggested refresh frequencies by category."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class IstatDataflow(BaseModel):
    """Represents an ISTAT dataflow with metadata and analysis results."""

    id: str = Field(..., description="ISTAT dataflow identifier")
    name_it: Optional[str] = Field(None, description="Italian name")
    name_en: Optional[str] = Field(None, description="English name")
    display_name: Optional[str] = Field(
        None, description="Display name (Italian preferred, English fallback)"
    )
    description: Optional[str] = Field("", description="Dataflow description")
    category: DataflowCategory = Field(
        DataflowCategory.ALTRI, description="Assigned category"
    )
    relevance_score: int = Field(0, description="Calculated relevance score")
    created_at: Optional[datetime] = Field(None, description="Analysis timestamp")

    @model_validator(mode="after")
    def set_display_name(self):
        """Set display name from available names."""
        if not self.display_name:
            self.display_name = self.name_it or self.name_en or self.id or "Unknown"
        return self


class DataflowTest(BaseModel):
    """Represents test results for a specific dataflow."""

    dataflow_id: str = Field(..., description="Tested dataflow ID")
    data_access_success: bool = Field(False, description="Whether data is accessible")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    size_bytes: int = Field(0, description="Data size in bytes")
    observations_count: int = Field(0, description="Number of observations found")
    sample_file: Optional[str] = Field(None, description="Path to saved sample file")
    parse_error: bool = Field(False, description="Whether XML parsing failed")
    error_message: Optional[str] = Field(None, description="Error details if any")
    tested_at: datetime = Field(
        default_factory=datetime.now, description="Test timestamp"
    )

    @property
    def size_mb(self) -> float:
        """Data size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def is_successful(self) -> bool:
        """Whether the test was successful overall."""
        return self.data_access_success and not self.parse_error


class DataflowTestResult(BaseModel):
    """Complete test result for a dataflow including metadata."""

    dataflow: IstatDataflow = Field(..., description="Dataflow information")
    test: DataflowTest = Field(..., description="Test results")
    suggested_refresh: RefreshFrequency = Field(RefreshFrequency.QUARTERLY)
    priority: float = Field(0.0, description="Calculated priority score")

    @model_validator(mode="after")
    def set_computed_fields(self):
        """Set computed fields based on dataflow and test results."""
        # Set suggested_refresh
        if hasattr(self, "dataflow") and self.dataflow:
            frequency_map = {
                DataflowCategory.POPOLAZIONE: RefreshFrequency.MONTHLY,
                DataflowCategory.ECONOMIA: RefreshFrequency.QUARTERLY,
                DataflowCategory.LAVORO: RefreshFrequency.MONTHLY,
                DataflowCategory.TERRITORIO: RefreshFrequency.YEARLY,
                DataflowCategory.ISTRUZIONE: RefreshFrequency.YEARLY,
                DataflowCategory.SALUTE: RefreshFrequency.QUARTERLY,
            }
            self.suggested_refresh = frequency_map.get(
                self.dataflow.category, RefreshFrequency.QUARTERLY
            )
        else:
            self.suggested_refresh = RefreshFrequency.QUARTERLY

        # Calculate priority
        if (
            hasattr(self, "dataflow")
            and hasattr(self, "test")
            and self.dataflow
            and self.test
        ):
            base_score = self.dataflow.relevance_score
            size_bonus = min(5, self.test.size_mb / 10)
            obs_bonus = min(5, self.test.observations_count / 1000)
            self.priority = base_score + size_bonus + obs_bonus
        else:
            self.priority = 0.0

        return self


class CategoryResult(BaseModel):
    """Results of categorization analysis."""

    category: DataflowCategory = Field(..., description="Assigned category")
    relevance_score: int = Field(..., description="Score for this category")
    matched_keywords: list[str] = Field(
        default_factory=list, description="Keywords that matched"
    )
    confidence: float = Field(0.0, description="Confidence in categorization (0-1)")

    @model_validator(mode="after")
    def calculate_confidence(self):
        """Calculate confidence based on score and keywords."""
        if self.relevance_score == 0:
            self.confidence = 0.0
        else:
            # Higher confidence with more keywords and higher score
            keyword_factor = min(
                1.0, len(self.matched_keywords) / 3
            )  # Max confidence with 3+ keywords
            score_factor = min(1.0, self.relevance_score / 50)  # Normalize score to 0-1
            self.confidence = (keyword_factor + score_factor) / 2
        return self


class AnalysisFilters(BaseModel):
    """Filters for dataflow analysis operations."""

    categories: Optional[list[DataflowCategory]] = Field(
        None, description="Filter by categories"
    )
    min_relevance_score: int = Field(0, description="Minimum relevance score")
    max_results: int = Field(100, description="Maximum number of results")
    include_tests: bool = Field(True, description="Whether to include test results")

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v):
        """Ensure reasonable limits on result count."""
        return min(max(1, v), 1000)  # Between 1 and 1000


class AnalysisResult(BaseModel):
    """Complete analysis result with categorized dataflows."""

    total_analyzed: int = Field(..., description="Total dataflows analyzed")
    categorized_dataflows: dict[DataflowCategory, list[IstatDataflow]] = Field(
        default_factory=dict, description="Dataflows grouped by category"
    )
    test_results: list[DataflowTestResult] = Field(
        default_factory=list, description="Test results for analyzed dataflows"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )
    performance_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics from analysis"
    )

    def get_top_by_category(
        self, category: DataflowCategory, limit: int = 5
    ) -> list[IstatDataflow]:
        """Get top dataflows for a specific category."""
        dataflows = self.categorized_dataflows.get(category, [])
        return sorted(dataflows, key=lambda x: x.relevance_score, reverse=True)[:limit]

    def get_summary_stats(self) -> dict[str, int]:
        """Get summary statistics for the analysis."""
        stats = {"total_dataflows": self.total_analyzed}

        for category in DataflowCategory:
            count = len(self.categorized_dataflows.get(category, []))
            stats[f"{category.value}_count"] = count

        return stats


class BulkAnalysisRequest(BaseModel):
    """Request model for bulk dataflow analysis."""

    dataflow_ids: list[str] = Field(..., description="List of dataflow IDs to analyze")
    include_tests: bool = Field(True, description="Whether to run data access tests")
    save_samples: bool = Field(False, description="Whether to save sample data files")
    max_concurrent: int = Field(5, description="Maximum concurrent requests")

    @field_validator("max_concurrent")
    @classmethod
    def validate_concurrent_limit(cls, v):
        """Ensure reasonable concurrency limits."""
        return min(max(1, v), 10)  # Between 1 and 10


class CategorizationRule(BaseModel):
    """Rule for categorizing dataflows - will be stored in database."""

    id: Optional[str] = Field(None, description="Rule ID")
    category: DataflowCategory = Field(..., description="Target category")
    keywords: list[str] = Field(..., description="Keywords to match")
    priority: int = Field(..., description="Category priority weight")
    is_active: bool = Field(True, description="Whether rule is active")
    created_at: Optional[datetime] = Field(None, description="Rule creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        """Ensure keywords are non-empty and lowercase."""
        return [keyword.lower().strip() for keyword in v if keyword.strip()]
