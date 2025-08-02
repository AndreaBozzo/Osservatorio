"""
Pipeline Data Models for Issue #63

Defines the core data structures for the unified data ingestion pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityLevel(str, Enum):
    """Data quality assessment levels"""
    EXCELLENT = "excellent"  # >= 90%
    GOOD = "good"           # >= 75%
    FAIR = "fair"           # >= 60%
    POOR = "poor"           # < 60%


@dataclass
class QualityScore:
    """Data quality assessment result"""
    overall_score: float = 0.0
    completeness: float = 0.0
    consistency: float = 0.0
    accuracy: float = 0.0
    timeliness: float = 0.0
    level: QualityLevel = QualityLevel.POOR
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate overall score and level"""
        self.overall_score = (
            self.completeness + self.consistency + 
            self.accuracy + self.timeliness
        ) / 4.0
        
        if self.overall_score >= 90:
            self.level = QualityLevel.EXCELLENT
        elif self.overall_score >= 75:
            self.level = QualityLevel.GOOD
        elif self.overall_score >= 60:
            self.level = QualityLevel.FAIR
        else:
            self.level = QualityLevel.POOR


class PipelineConfig(BaseModel):
    """Pipeline configuration parameters"""
    
    # Processing settings
    batch_size: int = Field(default=1000, description="Batch size for processing")
    max_concurrent: int = Field(default=4, description="Maximum concurrent operations")
    timeout_seconds: int = Field(default=300, description="Operation timeout")
    
    # Quality thresholds
    min_quality_score: float = Field(default=60.0, description="Minimum acceptable quality score")
    enable_quality_checks: bool = Field(default=True, description="Enable quality validation")
    fail_on_quality: bool = Field(default=False, description="Fail pipeline on low quality")
    
    # Output settings
    store_raw_data: bool = Field(default=True, description="Store original SDMX data")
    store_analytics: bool = Field(default=True, description="Store processed analytics data")
    generate_reports: bool = Field(default=True, description="Generate quality reports")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=2.0, description="Delay between retries (seconds)")
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"
        validate_assignment = True


@dataclass
class PipelineResult:
    """Pipeline execution result"""
    job_id: str
    dataset_id: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Processing results
    records_processed: int = 0
    records_stored: int = 0
    quality_score: Optional[QualityScore] = None
    
    # Error information
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate duration if end_time is set"""
        if self.end_time and self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()


class BatchResult(BaseModel):
    """Batch processing result"""
    batch_id: str = Field(description="Unique batch identifier")
    total_datasets: int = Field(description="Total number of datasets in batch")
    completed_datasets: int = Field(default=0, description="Successfully completed datasets")
    failed_datasets: int = Field(default=0, description="Failed datasets")
    
    results: List[PipelineResult] = Field(default_factory=list, description="Individual results")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    overall_quality: Optional[QualityScore] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate batch success rate"""
        if self.total_datasets == 0:
            return 0.0
        return (self.completed_datasets / self.total_datasets) * 100.0
    
    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete"""
        return (self.completed_datasets + self.failed_datasets) >= self.total_datasets


@dataclass 
class DataflowStructure:
    """SDMX Dataflow structure information"""
    id: str
    name: str
    description: str
    dimensions: List[Dict[str, Any]] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    measures: List[Dict[str, Any]] = field(default_factory=list)
    codelists: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class Observation:
    """Individual data observation"""
    dataset_id: str
    time_period: str
    value: Optional[float]
    dimensions: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    quality_flags: List[str] = field(default_factory=list)


class QualityReport(BaseModel):
    """Comprehensive quality assessment report"""
    dataset_id: str = Field(description="Dataset identifier")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    score: QualityScore = Field(description="Overall quality assessment")
    
    # Detailed assessments
    completeness_details: Dict[str, Any] = Field(default_factory=dict)
    consistency_details: Dict[str, Any] = Field(default_factory=dict) 
    accuracy_details: Dict[str, Any] = Field(default_factory=dict)
    timeliness_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Recommendations
    improvement_suggestions: List[str] = Field(default_factory=list)
    data_issues: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"