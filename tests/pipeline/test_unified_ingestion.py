"""
Tests for Unified Data Ingestion Pipeline - Issue #63

Comprehensive test suite for the unified ingestion framework.
"""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import (
    PipelineConfig,
    PipelineService,
    PipelineStatus,
    UnifiedDataIngestionPipeline,
)
from src.pipeline.models import QualityScore


class TestUnifiedDataIngestionPipeline:
    """Test suite for UnifiedDataIngestionPipeline."""

    @pytest.fixture
    def pipeline_config(self):
        """Create test pipeline configuration."""
        return PipelineConfig(
            batch_size=100,
            max_concurrent=2,
            enable_quality_checks=True,
            min_quality_score=70.0,
        )

    @pytest.fixture
    def mock_repository(self):
        """Create mock UnifiedDataRepository."""
        return MagicMock()

    @pytest.fixture
    def mock_duckdb_manager(self):
        """Create mock DuckDBManager."""
        return MagicMock()

    @pytest.fixture
    def pipeline(self, pipeline_config, mock_repository, mock_duckdb_manager):
        """Create test pipeline instance."""
        return UnifiedDataIngestionPipeline(
            config=pipeline_config,
            repository=mock_repository,
            duckdb_manager=mock_duckdb_manager,
        )

    @pytest.mark.asyncio
    async def test_ingest_dataset_success(self, pipeline):
        """Test successful dataset ingestion."""
        # Mock XML data
        xml_data = """<?xml version="1.0"?>
        <DataSet>
            <Obs>
                <ObsValue value="100"/>
                <ObsDimension value="2023"/>
            </Obs>
        </DataSet>"""

        # Test ingestion
        result = await pipeline.ingest_dataset(
            dataset_id="TEST_DATASET",
            sdmx_data=xml_data,
            target_formats=["powerbi"],
        )

        # Verify result
        assert result is not None
        assert result.dataset_id == "TEST_DATASET"
        assert result.status == PipelineStatus.COMPLETED
        assert result.records_processed >= 0
        assert result.quality_score is not None
        assert result.duration_seconds is not None

    @pytest.mark.asyncio
    async def test_ingest_dataset_invalid_xml(self, pipeline):
        """Test dataset ingestion with invalid XML."""
        invalid_xml = "not valid xml"

        with pytest.raises(Exception):
            await pipeline.ingest_dataset(
                dataset_id="INVALID_DATASET",
                sdmx_data=invalid_xml,
            )

    @pytest.mark.asyncio
    async def test_batch_ingest_success(self, pipeline):
        """Test successful batch ingestion."""
        datasets = [
            {
                "id": "DATASET_1",
                "data": "<DataSet><Obs><ObsValue value='1'/></Obs></DataSet>",
            },
            {
                "id": "DATASET_2",
                "data": "<DataSet><Obs><ObsValue value='2'/></Obs></DataSet>",
            },
        ]

        results = await pipeline.batch_ingest(datasets, target_formats=["powerbi"])

        # Verify results
        assert len(results) == 2
        for result in results:
            assert result.dataset_id in ["DATASET_1", "DATASET_2"]
            assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]

    @pytest.mark.asyncio
    async def test_batch_ingest_with_concurrency_limit(self, pipeline):
        """Test batch ingestion respects concurrency limits."""
        # Create many datasets to test concurrency
        datasets = [
            {
                "id": f"DATASET_{i}",
                "data": f"<DataSet><Obs><ObsValue value='{i}'/></Obs></DataSet>",
            }
            for i in range(5)
        ]

        start_time = datetime.now()
        results = await pipeline.batch_ingest(datasets)
        duration = (datetime.now() - start_time).total_seconds()

        # Should have processed all datasets
        assert len(results) == 5

        # With concurrency limit of 2, should take some time but not too long
        assert duration > 0.1  # Some processing time
        assert duration < 30  # But not too long

    def test_quality_validation_placeholder(self, pipeline):
        """Test quality validation placeholder functionality."""
        # Test data
        test_data = [
            {"field1": "value1", "field2": 100},
            {"field1": "value2", "field2": None},
            {"field1": None, "field2": 200},
        ]

        # Run quality validation (synchronous wrapper for testing)
        async def run_validation():
            return await pipeline._validate_data_quality(test_data, "TEST_DATASET")

        quality_score = asyncio.run(run_validation())

        # Verify quality score structure
        assert isinstance(quality_score, QualityScore)
        assert 0 <= quality_score.overall_score <= 100
        assert 0 <= quality_score.completeness <= 100
        assert quality_score.level is not None

    def test_converter_integration(self, pipeline):
        """Test integration with converter factory."""
        # Test converter factory access
        available_targets = pipeline.converter_factory.get_available_targets()
        assert isinstance(available_targets, list)
        assert len(available_targets) >= 1  # Should have at least one converter

    def test_pipeline_metrics(self, pipeline):
        """Test pipeline metrics collection."""
        metrics = pipeline.get_pipeline_metrics()

        assert isinstance(metrics, dict)
        assert "active_jobs" in metrics
        assert "configuration" in metrics
        assert "status" in metrics

        # Verify configuration metrics
        config_metrics = metrics["configuration"]
        assert config_metrics["batch_size"] == pipeline.config.batch_size
        assert config_metrics["max_concurrent"] == pipeline.config.max_concurrent

    @pytest.mark.asyncio
    async def test_job_tracking(self, pipeline):
        """Test job tracking functionality."""
        # Start a job that we can track
        xml_data = "<DataSet><Obs><ObsValue value='test'/></Obs></DataSet>"

        # Create a task that we can monitor
        task = asyncio.create_task(
            pipeline.ingest_dataset(
                dataset_id="TRACKED_DATASET",
                sdmx_data=xml_data,
                job_id="test_job_123",
            )
        )

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Check if job is tracked (might be too fast to catch)
        job_status = await pipeline.get_job_status("test_job_123")

        # Wait for completion
        result = await task

        # Should have completed successfully
        assert result.job_id == "test_job_123"
        assert result.status == PipelineStatus.COMPLETED


class TestPipelineService:
    """Test suite for PipelineService."""

    @pytest.fixture
    def mock_istat_client(self):
        """Create mock ISTAT client."""
        client = MagicMock()
        client.fetch_dataset.return_value = {
            "success": True,
            "data": "<DataSet><Obs><ObsValue value='test'/></Obs></DataSet>",
        }
        return client

    @pytest.fixture
    def pipeline_service(self, mock_istat_client):
        """Create test pipeline service."""
        config = PipelineConfig(batch_size=50, max_concurrent=1)
        return PipelineService(config=config, istat_client=mock_istat_client)

    @pytest.mark.asyncio
    async def test_process_dataset_with_fetch(self, pipeline_service):
        """Test processing dataset with ISTAT API fetch."""
        result = await pipeline_service.process_dataset(
            dataset_id="TEST_FETCH",
            target_formats=["powerbi"],
            fetch_from_istat=True,
        )

        assert result is not None
        assert result.dataset_id == "TEST_FETCH"
        assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_dataset_without_fetch(self, pipeline_service):
        """Test processing dataset without ISTAT API fetch."""
        result = await pipeline_service.process_dataset(
            dataset_id="TEST_NO_FETCH",
            target_formats=["powerbi"],
            fetch_from_istat=False,
        )

        assert result is not None
        assert result.dataset_id == "TEST_NO_FETCH"
        assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_multiple_datasets(self, pipeline_service):
        """Test processing multiple datasets."""
        dataset_ids = ["MULTI_1", "MULTI_2", "MULTI_3"]

        batch_id = await pipeline_service.process_multiple_datasets(
            dataset_ids=dataset_ids,
            target_formats=["powerbi"],
            fetch_from_istat=False,  # Use mock data
        )

        assert batch_id is not None
        assert isinstance(batch_id, str)
        assert batch_id.startswith("batch_")

    @pytest.mark.asyncio
    async def test_pipeline_status(self, pipeline_service):
        """Test pipeline status retrieval."""
        status = await pipeline_service.get_pipeline_status()

        assert isinstance(status, dict)
        assert "status" in status
        assert "configuration" in status
        assert "available_formats" in status

    @pytest.mark.asyncio
    async def test_quality_validation(self, pipeline_service):
        """Test dataset quality validation."""
        result = await pipeline_service.validate_dataset_quality(
            dataset_id="QUALITY_TEST",
            fetch_from_istat=False,
        )

        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert "quality_score" in result
            assert "dataset_id" in result

    def test_supported_formats(self, pipeline_service):
        """Test supported formats retrieval."""
        formats = pipeline_service.get_supported_formats()

        assert isinstance(formats, list)
        assert len(formats) >= 1

    @pytest.mark.asyncio
    async def test_error_handling(self, pipeline_service):
        """Test error handling in pipeline service."""
        # Mock ISTAT client to return error
        pipeline_service.istat_client.fetch_dataset.return_value = {
            "success": False,
            "error_message": "API Error",
        }

        with pytest.raises(ValueError):
            await pipeline_service.process_dataset(
                dataset_id="ERROR_DATASET",
                fetch_from_istat=True,
            )


class TestPipelineIntegration:
    """Integration tests for pipeline components."""

    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test end-to-end dataset processing."""
        # Create service with real components (but mocked external calls)
        config = PipelineConfig(
            batch_size=10,
            max_concurrent=1,
            enable_quality_checks=True,
        )

        with patch(
            "src.api.production_istat_client.ProductionIstatClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.fetch_dataset.return_value = {
                "success": True,
                "data": """<?xml version="1.0"?>
                <DataSet xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
                    <generic:Series>
                        <generic:Obs>
                            <generic:ObsValue value="100"/>
                            <generic:ObsDimension value="2023"/>
                        </generic:Obs>
                    </generic:Series>
                </DataSet>""",
            }
            mock_client_class.return_value = mock_client

            service = PipelineService(config=config, istat_client=mock_client)

            # Process dataset
            result = await service.process_dataset(
                dataset_id="E2E_TEST",
                target_formats=["powerbi", "tableau"],
                fetch_from_istat=True,
            )

            # Verify end-to-end processing
            assert result.dataset_id == "E2E_TEST"
            assert result.status == PipelineStatus.COMPLETED
            assert result.records_processed >= 0
            assert result.quality_score is not None

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test integration with performance monitoring."""
        from src.pipeline.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor()

        # Start timing an operation
        timer_id = monitor.start_operation("test_op", "ingest_dataset")

        # Simulate some work
        await asyncio.sleep(0.1)

        # Stop timing and record metrics
        metrics = monitor.stop_operation(
            timer_id=timer_id,
            operation_type="ingest_dataset",
            dataset_id="PERF_TEST",
            records_processed=100,
            quality_score=85.0,
        )

        # Verify metrics
        assert metrics.operation_type == "ingest_dataset"
        assert metrics.dataset_id == "PERF_TEST"
        assert metrics.duration_seconds > 0
        assert metrics.records_processed == 100
        assert metrics.quality_score == 85.0

    def test_configuration_validation(self):
        """Test pipeline configuration validation."""
        # Valid configuration
        valid_config = PipelineConfig(
            batch_size=100,
            max_concurrent=4,
            timeout_seconds=300,
        )
        assert valid_config.batch_size == 100
        assert valid_config.max_concurrent == 4

        # Test default values
        default_config = PipelineConfig()
        assert default_config.batch_size == 1000
        assert default_config.enable_quality_checks is True
