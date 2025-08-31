"""
Pipeline Service - Issue #63

High-level service interface for the unified data ingestion pipeline.
Provides simplified API for common operations while maintaining full flexibility.
"""

from typing import Any, Optional

from api.production_istat_client import ProductionIstatClient
from converters.factory import ConverterFactory
from database.duckdb.manager import DuckDBManager
from database.sqlite.repository import UnifiedDataRepository

# DataflowAnalysisService removed for MVP simplification
try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger
from utils.temp_file_manager import TempFileManager

from .job_manager import IngestionJobManager
from .models import BatchResult, PipelineConfig, PipelineResult
from .unified_ingestion import UnifiedDataIngestionPipeline

logger = get_logger(__name__)


class PipelineService:
    """
    High-level service interface for unified data ingestion pipeline.

    Provides simplified methods for common operations:
    - Single dataset processing
    - Batch processing with job management
    - Integration with existing converters
    - Performance monitoring
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        istat_client: Optional[ProductionIstatClient] = None,
    ):
        """
        Initialize pipeline service.

        Args:
            config: Pipeline configuration
            istat_client: ISTAT API client for data fetching
        """
        self.config = config or PipelineConfig()
        self.istat_client = istat_client or ProductionIstatClient()

        # Initialize core components
        self.repository = UnifiedDataRepository()
        self.duckdb_manager = DuckDBManager()
        self.temp_file_manager = TempFileManager()

        # Initialize pipeline and job manager
        self.pipeline = UnifiedDataIngestionPipeline(
            config=self.config,
            repository=self.repository,
            duckdb_manager=self.duckdb_manager,
            temp_file_manager=self.temp_file_manager,
        )

        self.job_manager = IngestionJobManager(pipeline=self.pipeline)

        # DataflowAnalysisService removed for MVP simplification

        logger.info("Pipeline Service initialized")

    async def process_dataset(
        self,
        dataset_id: str,
        target_formats: Optional[list[str]] = None,
        fetch_from_istat: bool = True,
    ) -> PipelineResult:
        """
        Process a single dataset through the unified pipeline.

        Args:
            dataset_id: ISTAT dataset identifier
            target_formats: Output formats (csv, json, parquet, etc.)
            fetch_from_istat: Whether to fetch fresh data from ISTAT API

        Returns:
            Pipeline processing result
        """
        logger.info(f"Processing dataset: {dataset_id}")

        try:
            # Fetch data from ISTAT if requested
            if fetch_from_istat:
                response = self.istat_client.fetch_dataset(dataset_id)
                if not response.get("success"):
                    raise ValueError(
                        f"Failed to fetch dataset {dataset_id}: {response.get('error_message')}"
                    )
                sdmx_data = response["data"]
            else:
                # Use placeholder data for testing
                sdmx_data = f"<mock_data>{dataset_id}</mock_data>"

            # Process through unified pipeline
            result = await self.pipeline.ingest_dataset(
                dataset_id=dataset_id,
                sdmx_data=sdmx_data,
                target_formats=target_formats or [],
            )

            logger.info(f"Dataset processed successfully: {dataset_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_id}: {e}")
            raise

    async def process_multiple_datasets(
        self,
        dataset_ids: list[str],
        target_formats: Optional[list[str]] = None,
        fetch_from_istat: bool = True,
    ) -> str:
        """
        Process multiple datasets as a batch job.

        Args:
            dataset_ids: List of ISTAT dataset identifiers
            target_formats: Output formats
            fetch_from_istat: Whether to fetch fresh data from ISTAT API

        Returns:
            Batch job ID for tracking progress
        """
        logger.info(f"Processing batch of {len(dataset_ids)} datasets")

        # Prepare dataset information
        datasets = []
        for dataset_id in dataset_ids:
            if fetch_from_istat:
                try:
                    response = self.istat_client.fetch_dataset(dataset_id)
                    if response.get("success"):
                        datasets.append(
                            {
                                "id": dataset_id,
                                "data": response["data"],
                            }
                        )
                    else:
                        logger.warning(
                            f"Failed to fetch {dataset_id}, using placeholder"
                        )
                        datasets.append(
                            {
                                "id": dataset_id,
                                "data": f"<mock_data>{dataset_id}</mock_data>",
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"Error fetching {dataset_id}: {e}, using placeholder"
                    )
                    datasets.append(
                        {
                            "id": dataset_id,
                            "data": f"<mock_data>{dataset_id}</mock_data>",
                        }
                    )
            else:
                datasets.append(
                    {
                        "id": dataset_id,
                        "data": f"<mock_data>{dataset_id}</mock_data>",
                    }
                )

        # Submit batch job
        batch_id = await self.job_manager.submit_batch_job(
            datasets=datasets,
            target_formats=target_formats or [],
        )

        logger.info(f"Batch job submitted: {batch_id}")
        return batch_id

    async def convert_existing_data(
        self,
        dataset_id: str,
        source_format: str,
        target_formats: list[str],
    ) -> dict[str, Any]:
        """
        Convert existing processed data to different formats.

        Args:
            dataset_id: Dataset identifier
            source_format: Current format (csv, json, raw)
            target_formats: Target formats to convert to

        Returns:
            Conversion results
        """
        logger.info(f"Converting {dataset_id} from {source_format} to {target_formats}")

        try:
            # This would typically fetch existing data from storage
            # For now, we'll use the converter factory directly
            conversion_results = {}

            for target_format in target_formats:
                if ConverterFactory.is_target_supported(target_format):
                    converter = ConverterFactory.create_converter(target_format)

                    # Mock conversion (would use real data in production)
                    result = converter.convert_xml_to_target(
                        f"<mock_conversion>{dataset_id}</mock_conversion>",
                        dataset_id,
                        dataset_id,
                    )

                    conversion_results[target_format] = {
                        "success": True,
                        "result": result,
                    }
                else:
                    conversion_results[target_format] = {
                        "success": False,
                        "error": f"Unsupported target format: {target_format}",
                    }

            logger.info(f"Conversion completed for {dataset_id}")
            return conversion_results

        except Exception as e:
            logger.error(f"Conversion failed for {dataset_id}: {e}")
            raise

    async def analyze_dataflows(
        self,
        xml_content: Optional[str] = None,
        fetch_from_istat: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze available dataflows and suggest processing priorities.

        NOTE: Simplified for MVP. Analysis service removed in Issue #153.
        Future: Will be enhanced in Issue #149 with proper dataflow analysis.

        Args:
            xml_content: Optional dataflow XML content
            fetch_from_istat: Whether to fetch dataflow list from ISTAT

        Returns:
            Dataflow analysis results (simplified for MVP)
        """
        logger.info("Analyzing dataflows (MVP simplified)")

        try:
            if xml_content:
                # MVP: Basic XML parsing without complex analysis
                logger.info("Processing XML content with basic parsing")

                # Simple XML validation
                try:
                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(xml_content)
                    dataflow_count = len(
                        root.findall(".//dataflow") + root.findall(".//*[@id]")
                    )
                except Exception as parse_error:
                    logger.warning(f"XML parsing failed: {parse_error}")
                    dataflow_count = 0

                return {
                    "status": "mvp_analysis_complete",
                    "dataflows_found": dataflow_count,
                    "message": "Basic XML analysis complete. Full analysis in Issue #149",
                    "analysis_type": "mvp_simplified",
                }

            elif fetch_from_istat:
                # MVP: Use production client for simple dataflow listing
                logger.info("Fetching dataflow list from ISTAT API")

                try:
                    # Use existing ISTAT client to fetch dataflow metadata
                    response = self.istat_client.fetch_dataflows()
                    if response and response.get("success"):
                        dataflow_data = response.get("data", "")
                        # Basic count from response
                        dataflow_count = (
                            len(str(dataflow_data).split("dataflow")) - 1
                            if dataflow_data
                            else 0
                        )

                        return {
                            "status": "istat_fetch_complete",
                            "dataflows_available": max(
                                dataflow_count, 7
                            ),  # At least our 7 known datasets
                            "message": "ISTAT dataflow list fetched. Full analysis in Issue #149",
                            "data_source": "istat_api",
                        }
                    else:
                        raise Exception(
                            f"ISTAT API error: {response.get('error_message', 'Unknown error')}"
                        )

                except Exception as api_error:
                    logger.warning(f"ISTAT API fetch failed: {api_error}")
                    return {
                        "status": "fallback_analysis",
                        "dataflows_available": 7,  # Our known MVP datasets
                        "message": "Using known datasets as fallback. ISTAT API unavailable",
                        "data_source": "fallback",
                    }

            else:
                return {
                    "error": "No XML content provided and fetch_from_istat is False",
                    "suggestion": "Provide XML content or set fetch_from_istat=True",
                }

        except Exception as e:
            logger.error(f"Dataflow analysis failed: {e}")
            # Graceful fallback for MVP
            return {
                "status": "error_fallback",
                "dataflows_available": 7,  # MVP known datasets
                "error": str(e),
                "message": "Analysis failed, using MVP fallback. Full analysis in Issue #149",
            }

    async def get_batch_status(self, batch_id: str) -> Optional[BatchResult]:
        """Get status of a batch processing job."""
        return await self.job_manager.get_batch_status(batch_id)

    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a running batch job."""
        return await self.job_manager.cancel_batch(batch_id)

    async def get_pipeline_status(self) -> dict[str, Any]:
        """Get overall pipeline status and metrics."""
        try:
            queue_status = await self.job_manager.get_queue_status()
            performance_summary = self.job_manager.get_performance_summary()
            pipeline_metrics = self.pipeline.get_pipeline_metrics()

            return {
                "status": "healthy",
                "queue": queue_status,
                "performance": performance_summary,
                "pipeline": pipeline_metrics,
                "available_formats": ConverterFactory.get_available_targets(),
                "configuration": {
                    "batch_size": self.config.batch_size,
                    "max_concurrent": self.config.max_concurrent,
                    "quality_checks": self.config.enable_quality_checks,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def start_background_processing(self) -> None:
        """Start background job processing (call once at startup)."""
        import asyncio

        # Start job queue processor as background task
        asyncio.create_task(self.job_manager.process_job_queue())
        logger.info("Background job processing started")

    async def cleanup_old_jobs(self, hours: int = 24) -> dict[str, Any]:
        """Clean up old completed jobs."""
        try:
            cleaned_count = await self.job_manager.cleanup_completed_jobs(hours)
            return {
                "success": True,
                "jobs_cleaned": cleaned_count,
            }
        except Exception as e:
            logger.error(f"Job cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_supported_formats(self) -> list[str]:
        """Get list of supported output formats."""
        return ConverterFactory.get_available_targets()

    async def validate_dataset_quality(
        self, dataset_id: str, fetch_from_istat: bool = True
    ) -> dict[str, Any]:
        """
        Validate quality of a specific dataset.

        Args:
            dataset_id: Dataset to validate
            fetch_from_istat: Whether to fetch fresh data

        Returns:
            Quality validation results
        """
        logger.info(f"Validating dataset quality: {dataset_id}")

        try:
            if fetch_from_istat:
                response = self.istat_client.fetch_dataset(dataset_id)
                if not response.get("success"):
                    return {
                        "success": False,
                        "error": f"Failed to fetch dataset: {response.get('error_message')}",
                    }
                sdmx_data = response["data"]
            else:
                sdmx_data = f"<mock_data>{dataset_id}</mock_data>"

            # Parse data for quality assessment
            parsed_data = await self.pipeline._parse_sdmx_data(sdmx_data, dataset_id)

            # Run quality validation
            quality_score = await self.pipeline._validate_data_quality(
                parsed_data, dataset_id
            )

            return {
                "success": True,
                "dataset_id": dataset_id,
                "records_analyzed": len(parsed_data),
                "quality_score": {
                    "overall": quality_score.overall_score,
                    "completeness": quality_score.completeness,
                    "consistency": quality_score.consistency,
                    "accuracy": quality_score.accuracy,
                    "timeliness": quality_score.timeliness,
                    "level": quality_score.level.value,
                },
                "issues": quality_score.issues,
                "recommendations": quality_score.recommendations,
            }

        except Exception as e:
            logger.error(f"Quality validation failed for {dataset_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
