"""
Ingestion Job Manager - Issue #63

Manages batch processing, job scheduling, and pipeline orchestration
for the unified data ingestion framework.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from ..utils.logger import get_logger
from .models import BatchResult, PipelineStatus
from .unified_ingestion import UnifiedDataIngestionPipeline

logger = get_logger(__name__)


class IngestionJobManager:
    """
    Manages ingestion jobs, batching, and pipeline orchestration.

    Features:
    - Batch job management
    - Job scheduling and queuing
    - Progress tracking
    - Resource management
    - Performance monitoring
    """

    def __init__(self, pipeline: Optional[UnifiedDataIngestionPipeline] = None):
        """
        Initialize job manager.

        Args:
            pipeline: Unified ingestion pipeline (creates default if None)
        """
        self.pipeline = pipeline or UnifiedDataIngestionPipeline()

        # Job tracking
        self.batch_jobs: dict[str, BatchResult] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.active_batches: set[str] = set()

        # Performance tracking
        self.performance_history: list[dict[str, Any]] = []

        logger.info("Ingestion Job Manager initialized")

    async def submit_batch_job(
        self,
        datasets: list[dict[str, Any]],
        target_formats: Optional[list[str]] = None,
        batch_id: Optional[str] = None,
        priority: int = 5,
    ) -> str:
        """
        Submit a batch ingestion job.

        Args:
            datasets: List of datasets to process
            target_formats: Output formats (csv, json, parquet, etc.)
            batch_id: Optional batch identifier
            priority: Job priority (1=highest, 10=lowest)

        Returns:
            Batch job ID
        """
        batch_id = batch_id or f"batch_{uuid.uuid4().hex[:8]}"

        # Create batch result tracking
        batch_result = BatchResult(
            batch_id=batch_id,
            total_datasets=len(datasets),
            start_time=datetime.now(),
        )

        self.batch_jobs[batch_id] = batch_result
        self.active_batches.add(batch_id)

        # Queue job for processing
        job_info = {
            "batch_id": batch_id,
            "datasets": datasets,
            "target_formats": target_formats or [],
            "priority": priority,
            "submitted_at": datetime.now(),
        }

        await self.job_queue.put(job_info)

        logger.info(f"Batch job submitted: {batch_id} ({len(datasets)} datasets)")

        return batch_id

    async def process_job_queue(self) -> None:
        """
        Process jobs from queue (runs continuously).
        Should be started as background task.
        """
        logger.info("Job queue processor started")

        while True:
            try:
                # Get next job from queue (blocks until available)
                job_info = await self.job_queue.get()

                # Process the batch job
                await self._process_batch_job(job_info)

                # Mark job as done in queue
                self.job_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing job queue: {e}")
                await asyncio.sleep(1)  # Brief pause on error

    async def _process_batch_job(self, job_info: dict[str, Any]) -> None:
        """Process a single batch job."""
        batch_id = job_info["batch_id"]

        try:
            logger.info(f"Processing batch job: {batch_id}")

            # Get batch tracking
            batch_result = self.batch_jobs[batch_id]

            # Process through unified pipeline
            results = await self.pipeline.batch_ingest(
                datasets=job_info["datasets"],
                target_formats=job_info["target_formats"],
                batch_id=batch_id,
            )

            # Update batch results
            batch_result.results = results
            batch_result.end_time = datetime.now()

            # Count successes and failures
            for result in results:
                if result.status == PipelineStatus.COMPLETED:
                    batch_result.completed_datasets += 1
                else:
                    batch_result.failed_datasets += 1

            # Calculate overall quality
            quality_scores = [
                r.quality_score.overall_score
                for r in results
                if r.quality_score is not None
            ]

            if quality_scores:
                from .models import QualityScore

                avg_quality = sum(quality_scores) / len(quality_scores)
                batch_result.overall_quality = QualityScore(
                    overall_score=avg_quality,
                    completeness=avg_quality,  # Simplified
                    consistency=avg_quality,
                    accuracy=avg_quality,
                    timeliness=avg_quality,
                )

            # Record performance metrics
            await self._record_performance_metrics(batch_result)

            logger.info(
                f"Batch job completed: {batch_id} "
                f"({batch_result.success_rate:.1f}% success rate)"
            )

        except Exception as e:
            logger.error(f"Batch job failed: {batch_id} - {e}")

            # Update batch with error
            if batch_id in self.batch_jobs:
                batch_result = self.batch_jobs[batch_id]
                batch_result.end_time = datetime.now()
                batch_result.failed_datasets = batch_result.total_datasets

        finally:
            # Clean up active batch tracking
            self.active_batches.discard(batch_id)

    async def get_batch_status(self, batch_id: str) -> Optional[BatchResult]:
        """Get status of a batch job."""
        return self.batch_jobs.get(batch_id)

    async def list_active_batches(self) -> list[str]:
        """Get list of currently active batch IDs."""
        return list(self.active_batches)

    async def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel a batch job.

        Args:
            batch_id: Batch to cancel

        Returns:
            True if cancelled, False if not found or already completed
        """
        if batch_id not in self.active_batches:
            return False

        # Try to cancel individual jobs in the pipeline
        batch_result = self.batch_jobs.get(batch_id)
        if batch_result:
            for result in batch_result.results:
                await self.pipeline.cancel_job(result.job_id)

        # Remove from active tracking
        self.active_batches.discard(batch_id)

        # Update batch status
        if batch_id in self.batch_jobs:
            self.batch_jobs[batch_id].end_time = datetime.now()

        logger.info(f"Batch cancelled: {batch_id}")
        return True

    async def get_queue_status(self) -> dict[str, Any]:
        """Get current job queue status."""
        return {
            "queued_jobs": self.job_queue.qsize(),
            "active_batches": len(self.active_batches),
            "total_batches": len(self.batch_jobs),
            "queue_healthy": True,
        }

    async def cleanup_completed_jobs(self, older_than_hours: int = 24) -> int:
        """
        Clean up completed job records older than specified hours.

        Args:
            older_than_hours: Remove jobs older than this many hours

        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleaned_count = 0

        # Find batches to clean up
        to_remove = []
        for batch_id, batch_result in self.batch_jobs.items():
            if (
                batch_result.end_time
                and batch_result.end_time < cutoff_time
                and batch_id not in self.active_batches
            ):
                to_remove.append(batch_id)

        # Remove old batches
        for batch_id in to_remove:
            del self.batch_jobs[batch_id]
            cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} completed job records")
        return cleaned_count

    async def _record_performance_metrics(self, batch_result: BatchResult) -> None:
        """Record performance metrics for monitoring."""
        if not batch_result.end_time or not batch_result.start_time:
            return

        duration = (batch_result.end_time - batch_result.start_time).total_seconds()
        throughput = batch_result.total_datasets / duration if duration > 0 else 0

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "batch_id": batch_result.batch_id,
            "total_datasets": batch_result.total_datasets,
            "duration_seconds": duration,
            "throughput_datasets_per_second": throughput,
            "success_rate": batch_result.success_rate,
            "overall_quality_score": (
                batch_result.overall_quality.overall_score
                if batch_result.overall_quality
                else None
            ),
        }

        self.performance_history.append(metrics)

        # Keep only recent history (last 100 batches)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        logger.debug(f"Recorded performance metrics for batch {batch_result.batch_id}")

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary from recent batches."""
        if not self.performance_history:
            return {"status": "no_data"}

        recent_metrics = self.performance_history[-10:]  # Last 10 batches

        avg_throughput = sum(
            m["throughput_datasets_per_second"] for m in recent_metrics
        ) / len(recent_metrics)
        avg_success_rate = sum(m["success_rate"] for m in recent_metrics) / len(
            recent_metrics
        )

        quality_scores = [
            m["overall_quality_score"]
            for m in recent_metrics
            if m["overall_quality_score"] is not None
        ]
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else None
        )

        return {
            "recent_batches": len(recent_metrics),
            "average_throughput": round(avg_throughput, 2),
            "average_success_rate": round(avg_success_rate, 1),
            "average_quality_score": round(avg_quality, 1) if avg_quality else None,
            "total_datasets_processed": sum(
                m["total_datasets"] for m in recent_metrics
            ),
            "status": "healthy",
        }

    async def schedule_periodic_job(
        self,
        datasets: list[dict[str, Any]],
        interval_hours: int,
        target_formats: Optional[list[str]] = None,
        job_name: Optional[str] = None,
    ) -> str:
        """
        Schedule a recurring batch job.

        Args:
            datasets: Datasets to process
            interval_hours: Repeat interval in hours
            target_formats: Output formats
            job_name: Optional job name for tracking

        Returns:
            Scheduled job ID
        """
        job_name = job_name or f"scheduled_{uuid.uuid4().hex[:8]}"

        async def recurring_job():
            while True:
                try:
                    batch_id = await self.submit_batch_job(
                        datasets=datasets,
                        target_formats=target_formats,
                        batch_id=f"{job_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    )
                    logger.info(f"Scheduled job executed: {job_name} -> {batch_id}")

                    # Wait for next execution
                    await asyncio.sleep(interval_hours * 3600)

                except Exception as e:
                    logger.error(f"Scheduled job error: {job_name} - {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes on error

        # Start recurring job as background task
        asyncio.create_task(recurring_job())

        logger.info(f"Scheduled recurring job: {job_name} (every {interval_hours}h)")
        return job_name
