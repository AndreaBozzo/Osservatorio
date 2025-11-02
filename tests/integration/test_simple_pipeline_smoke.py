"""
Smoke tests for SimpleIngestionPipeline - minimal, fast validation.

Simple smoke tests to verify the pipeline actually works with real components.
No complex scenarios, just "does it run without crashing?"
"""

from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestSimplePipelineSmoke:
    """Smoke tests - verify basic functionality without breaking."""

    @pytest.mark.skip(reason="Issue #159 - async tests require pytest-asyncio configuration")
    @pytest.mark.asyncio
    async def test_single_dataset_ingestion_smoke(self):
        """Smoke test: single dataset ingestion doesn't crash."""
        # Mock ISTAT client to avoid real API calls
        with patch(
            "src.ingestion.simple_pipeline.ProductionIstatClient"
        ) as mock_client:
            mock_client.return_value.fetch_dataset.return_value = {
                "success": True,
                "data": {
                    "status": "success",
                    "content": "<GenericData><DataSet><Obs><ObsValue value='1000'/></Obs></DataSet></GenericData>",
                    "size": 100,
                },
            }

            with patch("src.ingestion.simple_pipeline.get_manager") as mock_manager:
                with patch("src.ingestion.simple_pipeline.UnifiedDataRepository"):
                    from src.ingestion.simple_pipeline import SimpleIngestionPipeline

                    pipeline = SimpleIngestionPipeline()

                    # Mock database operations to avoid real DB
                    mock_conn = mock_manager.return_value.get_connection.return_value.__enter__.return_value
                    mock_conn.execute.return_value.fetchone.return_value = [
                        0
                    ]  # No existing records

                    # This should not crash
                    result = await pipeline.ingest_single_dataset("101_1015")

                    # Basic validation - it returned something
                    assert result is not None
                    assert "success" in result
                    assert "dataset_id" in result

    def test_pipeline_creation_smoke(self):
        """Smoke test: pipeline can be created."""
        with patch("src.ingestion.simple_pipeline.ProductionIstatClient"):
            with patch("src.ingestion.simple_pipeline.get_manager"):
                with patch("src.ingestion.simple_pipeline.UnifiedDataRepository"):
                    from src.ingestion.simple_pipeline import (
                        SimpleIngestionPipeline,
                        create_simple_pipeline,
                    )

                    # Direct creation
                    pipeline1 = SimpleIngestionPipeline()
                    assert pipeline1 is not None

                    # Factory creation
                    pipeline2 = create_simple_pipeline()
                    assert pipeline2 is not None

    @pytest.mark.skip(reason="Issue #159 - async tests require pytest-asyncio configuration")
    @pytest.mark.asyncio
    async def test_health_check_smoke(self):
        """Smoke test: health check works."""
        with patch("src.ingestion.simple_pipeline.ProductionIstatClient"):
            with patch("src.ingestion.simple_pipeline.get_manager"):
                with patch("src.ingestion.simple_pipeline.UnifiedDataRepository"):
                    from src.ingestion.simple_pipeline import SimpleIngestionPipeline

                    pipeline = SimpleIngestionPipeline()
                    result = await pipeline.health_check()

                    # Should return something reasonable
                    assert result is not None
                    assert isinstance(result, dict)
                    assert "healthy" in result
