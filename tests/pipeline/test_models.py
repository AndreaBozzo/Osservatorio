"""
Tests for pipeline data models (Issue #63)
"""

import pytest
from datetime import datetime, timedelta
from src.pipeline.models import (
    PipelineConfig,
    PipelineResult,
    PipelineStatus,
    QualityScore,
    QualityLevel,
    BatchResult,
    QualityReport
)


class TestQualityScore:
    """Test QualityScore calculation and classification"""
    
    def test_quality_score_calculation(self):
        """Test overall score calculation"""
        score = QualityScore(
            completeness=90.0,
            consistency=85.0,
            accuracy=88.0,
            timeliness=92.0
        )
        
        expected_overall = (90.0 + 85.0 + 88.0 + 92.0) / 4.0
        assert score.overall_score == expected_overall
        assert score.level == QualityLevel.EXCELLENT
    
    def test_quality_levels(self):
        """Test quality level classification"""
        # Excellent (>= 90%)
        excellent = QualityScore(completeness=95, consistency=90, accuracy=92, timeliness=93)
        assert excellent.level == QualityLevel.EXCELLENT
        
        # Good (>= 75%)
        good = QualityScore(completeness=80, consistency=75, accuracy=78, timeliness=82)
        assert good.level == QualityLevel.GOOD
        
        # Fair (>= 60%)
        fair = QualityScore(completeness=65, consistency=60, accuracy=68, timeliness=62)
        assert fair.level == QualityLevel.FAIR
        
        # Poor (< 60%)
        poor = QualityScore(completeness=50, consistency=45, accuracy=55, timeliness=40)
        assert poor.level == QualityLevel.POOR


class TestPipelineConfig:
    """Test pipeline configuration validation"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = PipelineConfig()
        
        assert config.batch_size == 1000
        assert config.max_concurrent == 4
        assert config.timeout_seconds == 300
        assert config.min_quality_score == 60.0
        assert config.enable_quality_checks is True
        assert config.fail_on_quality is False
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = PipelineConfig(
            batch_size=500,
            max_concurrent=2,
            min_quality_score=80.0,
            fail_on_quality=True
        )
        
        assert config.batch_size == 500
        assert config.max_concurrent == 2
        assert config.min_quality_score == 80.0
        assert config.fail_on_quality is True
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config should not raise
        PipelineConfig(batch_size=1, max_concurrent=1, timeout_seconds=1)
        
        # Test Pydantic validation
        with pytest.raises(ValueError):
            PipelineConfig(batch_size="invalid")


class TestPipelineResult:
    """Test pipeline result data structure"""
    
    def test_result_creation(self):
        """Test pipeline result creation"""
        start_time = datetime.now()
        result = PipelineResult(
            job_id="test-job-123",
            dataset_id="DCIS_POPRES1", 
            status=PipelineStatus.COMPLETED,
            start_time=start_time
        )
        
        assert result.job_id == "test-job-123"
        assert result.dataset_id == "DCIS_POPRES1"
        assert result.status == PipelineStatus.COMPLETED
        assert result.start_time == start_time
        assert result.duration_seconds is None
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=120)
        
        result = PipelineResult(
            job_id="test-job-123",
            dataset_id="DCIS_POPRES1",
            status=PipelineStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time
        )
        
        assert result.duration_seconds == 120.0


class TestBatchResult:
    """Test batch processing result"""
    
    def test_batch_result_creation(self):
        """Test batch result creation"""
        batch = BatchResult(
            batch_id="batch-456",
            total_datasets=5
        )
        
        assert batch.batch_id == "batch-456"
        assert batch.total_datasets == 5
        assert batch.completed_datasets == 0
        assert batch.failed_datasets == 0
        assert batch.success_rate == 0.0
        assert not batch.is_complete
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        batch = BatchResult(
            batch_id="batch-456",
            total_datasets=10,
            completed_datasets=8,
            failed_datasets=2
        )
        
        assert batch.success_rate == 80.0
        assert batch.is_complete
    
    def test_completion_status(self):
        """Test batch completion detection"""
        batch = BatchResult(
            batch_id="batch-456", 
            total_datasets=5,
            completed_datasets=3,
            failed_datasets=1
        )
        
        assert not batch.is_complete  # 3 + 1 < 5
        
        batch.completed_datasets = 4
        assert batch.is_complete  # 4 + 1 = 5


class TestQualityReport:
    """Test quality report structure"""
    
    def test_quality_report_creation(self):
        """Test quality report creation"""
        quality_score = QualityScore(
            completeness=85.0,
            consistency=80.0,
            accuracy=88.0,
            timeliness=90.0
        )
        
        report = QualityReport(
            dataset_id="DCIS_POPRES1",
            score=quality_score,
            improvement_suggestions=["Improve data completeness"],
            data_issues=["Missing values in 2023 data"]
        )
        
        assert report.dataset_id == "DCIS_POPRES1"
        assert report.score.level == QualityLevel.EXCELLENT
        assert len(report.improvement_suggestions) == 1
        assert len(report.data_issues) == 1
        assert isinstance(report.generated_at, datetime)