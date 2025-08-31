"""
Performance Monitor - Issue #63

Advanced performance monitoring and benchmarking for the unified ingestion pipeline.
Tracks metrics, detects regressions, and provides optimization insights.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .models import PipelineResult

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for pipeline operations."""

    timestamp: datetime
    operation_type: str  # ingest_dataset, batch_ingest, convert_data
    dataset_id: Optional[str] = None
    batch_id: Optional[str] = None

    # Timing metrics
    duration_seconds: float = 0.0
    queue_wait_time: float = 0.0
    processing_time: float = 0.0

    # Throughput metrics
    records_processed: int = 0
    records_per_second: float = 0.0

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Quality metrics
    quality_score: Optional[float] = None
    error_count: int = 0

    # Additional context
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark for comparison."""

    operation_type: str
    target_duration_seconds: float
    target_throughput: float
    target_quality_score: float
    max_memory_mb: float
    max_cpu_percent: float


class PerformanceMonitor:
    """
    Monitors and analyzes pipeline performance.

    Features:
    - Real-time metrics collection
    - Performance benchmarking
    - Regression detection
    - Optimization recommendations
    - Historical analysis
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize performance monitor.

        Args:
            data_dir: Directory for storing performance data
        """
        self.data_dir = data_dir or Path("data/performance_results")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory metrics storage
        self.metrics_history: list[PerformanceMetrics] = []
        self.active_timers: dict[str, float] = {}

        # Performance benchmarks
        self.benchmarks = self._initialize_benchmarks()

        # Configuration
        self.max_history_size = 1000
        self.auto_save_interval = 300  # 5 minutes

        logger.info(f"Performance Monitor initialized (data_dir: {self.data_dir})")

    def start_operation(self, operation_id: str, operation_type: str) -> str:
        """
        Start timing an operation.

        Args:
            operation_id: Unique operation identifier
            operation_type: Type of operation (ingest_dataset, batch_ingest, etc.)

        Returns:
            Timer ID for stopping the operation
        """
        timer_id = f"{operation_type}_{operation_id}_{time.time()}"
        self.active_timers[timer_id] = time.time()

        logger.debug(f"Started timing operation: {timer_id}")
        return timer_id

    def stop_operation(
        self,
        timer_id: str,
        operation_type: str,
        dataset_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        records_processed: int = 0,
        quality_score: Optional[float] = None,
        error_count: int = 0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> PerformanceMetrics:
        """
        Stop timing an operation and record metrics.

        Args:
            timer_id: Timer ID from start_operation
            operation_type: Type of operation
            dataset_id: Optional dataset identifier
            batch_id: Optional batch identifier
            records_processed: Number of records processed
            quality_score: Data quality score
            error_count: Number of errors encountered
            metadata: Additional context information

        Returns:
            Performance metrics for this operation
        """
        if timer_id not in self.active_timers:
            logger.warning(f"Timer not found: {timer_id}")
            return self._create_error_metrics(operation_type)

        # Calculate duration
        start_time = self.active_timers.pop(timer_id)
        duration = time.time() - start_time

        # Calculate throughput
        throughput = records_processed / duration if duration > 0 else 0.0

        # Get system resource usage (placeholder - would use psutil in production)
        memory_usage = self._get_memory_usage()
        cpu_usage = self._get_cpu_usage()

        # Create metrics record
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            operation_type=operation_type,
            dataset_id=dataset_id,
            batch_id=batch_id,
            duration_seconds=duration,
            processing_time=duration,  # Simplified - would separate queue time
            records_processed=records_processed,
            records_per_second=throughput,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            quality_score=quality_score,
            error_count=error_count,
            metadata=metadata or {},
        )

        # Store metrics
        self.metrics_history.append(metrics)

        # Trim history if needed
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

        # Log performance summary
        logger.info(
            f"Operation completed: {operation_type} "
            f"({duration:.2f}s, {throughput:.1f} rec/s, quality: {quality_score:.1f}%)"
        )

        # Check against benchmarks
        self._check_performance_against_benchmarks(metrics)

        return metrics

    def record_pipeline_result(self, result: PipelineResult) -> None:
        """Record metrics from a pipeline result."""
        try:
            quality_score = (
                result.quality_score.overall_score if result.quality_score else None
            )

            metrics = PerformanceMetrics(
                timestamp=result.end_time or datetime.now(),
                operation_type="pipeline_result",
                dataset_id=result.dataset_id,
                batch_id=result.job_id,
                duration_seconds=result.duration_seconds or 0.0,
                processing_time=result.duration_seconds or 0.0,
                records_processed=result.records_processed,
                records_per_second=(
                    result.records_processed / result.duration_seconds
                    if result.duration_seconds and result.duration_seconds > 0
                    else 0.0
                ),
                quality_score=quality_score,
                error_count=1 if result.error_message else 0,
                metadata=result.metadata,
            )

            self.metrics_history.append(metrics)
            logger.debug(f"Recorded pipeline result metrics: {result.job_id}")

        except Exception as e:
            logger.error(f"Failed to record pipeline result metrics: {e}")

    def get_performance_summary(self, hours: int = 24) -> dict[str, Any]:
        """
        Get performance summary for recent operations.

        Args:
            hours: Number of hours to include in summary

        Returns:
            Performance summary with key metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"status": "no_recent_data", "hours": hours}

        # Calculate aggregate metrics
        total_operations = len(recent_metrics)
        total_records = sum(m.records_processed for m in recent_metrics)
        total_duration = sum(m.duration_seconds for m in recent_metrics)

        avg_duration = total_duration / total_operations if total_operations > 0 else 0
        avg_throughput = (
            sum(m.records_per_second for m in recent_metrics) / total_operations
        )

        # Quality metrics
        quality_scores = [
            m.quality_score for m in recent_metrics if m.quality_score is not None
        ]
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else None
        )

        # Error metrics
        total_errors = sum(m.error_count for m in recent_metrics)
        error_rate = (
            (total_errors / total_operations * 100) if total_operations > 0 else 0
        )

        # Resource usage
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / total_operations
        avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / total_operations

        return {
            "status": "healthy",
            "time_period_hours": hours,
            "total_operations": total_operations,
            "total_records_processed": total_records,
            "average_duration_seconds": round(avg_duration, 2),
            "average_throughput": round(avg_throughput, 1),
            "average_quality_score": round(avg_quality, 1) if avg_quality else None,
            "error_rate_percent": round(error_rate, 2),
            "average_memory_usage_mb": round(avg_memory, 1),
            "average_cpu_usage_percent": round(avg_cpu, 1),
            "operation_types": list({m.operation_type for m in recent_metrics}),
        }

    def detect_performance_regressions(
        self, lookback_hours: int = 168
    ) -> list[dict[str, Any]]:
        """
        Detect performance regressions by comparing recent vs historical performance.

        Args:
            lookback_hours: Hours to look back for comparison (default: 1 week)

        Returns:
            List of detected regressions
        """
        regressions = []

        try:
            # Split metrics into recent and historical
            cutoff_time = datetime.now() - timedelta(hours=24)  # Last 24 hours = recent
            historical_cutoff = datetime.now() - timedelta(hours=lookback_hours)

            recent_metrics = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]

            historical_metrics = [
                m
                for m in self.metrics_history
                if historical_cutoff <= m.timestamp < cutoff_time
            ]

            if not recent_metrics or not historical_metrics:
                return regressions

            # Group by operation type
            operation_types = {m.operation_type for m in recent_metrics}

            for op_type in operation_types:
                recent_ops = [m for m in recent_metrics if m.operation_type == op_type]
                historical_ops = [
                    m for m in historical_metrics if m.operation_type == op_type
                ]

                if not historical_ops:
                    continue

                # Calculate averages
                recent_avg_duration = sum(m.duration_seconds for m in recent_ops) / len(
                    recent_ops
                )
                historical_avg_duration = sum(
                    m.duration_seconds for m in historical_ops
                ) / len(historical_ops)

                recent_avg_throughput = sum(
                    m.records_per_second for m in recent_ops
                ) / len(recent_ops)
                historical_avg_throughput = sum(
                    m.records_per_second for m in historical_ops
                ) / len(historical_ops)

                # Check for regressions (20% threshold)
                duration_increase = (
                    (recent_avg_duration - historical_avg_duration)
                    / historical_avg_duration
                    * 100
                )
                throughput_decrease = (
                    (historical_avg_throughput - recent_avg_throughput)
                    / historical_avg_throughput
                    * 100
                )

                if duration_increase > 20:
                    regressions.append(
                        {
                            "type": "duration_regression",
                            "operation_type": op_type,
                            "recent_avg_duration": round(recent_avg_duration, 2),
                            "historical_avg_duration": round(
                                historical_avg_duration, 2
                            ),
                            "increase_percent": round(duration_increase, 1),
                            "severity": "high" if duration_increase > 50 else "medium",
                        }
                    )

                if throughput_decrease > 20:
                    regressions.append(
                        {
                            "type": "throughput_regression",
                            "operation_type": op_type,
                            "recent_avg_throughput": round(recent_avg_throughput, 1),
                            "historical_avg_throughput": round(
                                historical_avg_throughput, 1
                            ),
                            "decrease_percent": round(throughput_decrease, 1),
                            "severity": (
                                "high" if throughput_decrease > 50 else "medium"
                            ),
                        }
                    )

            if regressions:
                logger.warning(f"Detected {len(regressions)} performance regressions")

        except Exception as e:
            logger.error(f"Error detecting performance regressions: {e}")

        return regressions

    def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []

        try:
            recent_summary = self.get_performance_summary(hours=24)

            if recent_summary.get("status") == "no_recent_data":
                return recommendations

            # Check against benchmarks
            avg_duration = recent_summary.get("average_duration_seconds", 0)
            avg_throughput = recent_summary.get("average_throughput", 0)
            avg_memory = recent_summary.get("average_memory_usage_mb", 0)
            error_rate = recent_summary.get("error_rate_percent", 0)

            # Duration recommendations
            if avg_duration > 30:  # Slow operations
                recommendations.append(
                    {
                        "type": "performance",
                        "priority": "high",
                        "title": "High processing duration detected",
                        "description": f"Average operation duration is {avg_duration:.1f}s",
                        "suggestions": [
                            "Consider increasing batch_size for better throughput",
                            "Review data parsing efficiency",
                            "Enable parallel processing for batch operations",
                        ],
                    }
                )

            # Throughput recommendations
            if avg_throughput < 10:  # Low throughput
                recommendations.append(
                    {
                        "type": "throughput",
                        "priority": "medium",
                        "title": "Low throughput detected",
                        "description": f"Average throughput is {avg_throughput:.1f} records/second",
                        "suggestions": [
                            "Optimize SDMX parsing algorithms",
                            "Consider caching frequently accessed data",
                            "Review database write performance",
                        ],
                    }
                )

            # Memory recommendations
            if avg_memory > 500:  # High memory usage
                recommendations.append(
                    {
                        "type": "memory",
                        "priority": "medium",
                        "title": "High memory usage detected",
                        "description": f"Average memory usage is {avg_memory:.1f}MB",
                        "suggestions": [
                            "Implement streaming processing for large datasets",
                            "Review data structure efficiency",
                            "Consider reducing batch_size",
                        ],
                    }
                )

            # Error rate recommendations
            if error_rate > 5:  # High error rate
                recommendations.append(
                    {
                        "type": "reliability",
                        "priority": "high",
                        "title": "High error rate detected",
                        "description": f"Error rate is {error_rate:.1f}%",
                        "suggestions": [
                            "Review error handling and retry logic",
                            "Validate input data quality",
                            "Monitor ISTAT API connectivity",
                        ],
                    }
                )

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")

        return recommendations

    async def save_metrics_to_file(self) -> None:
        """Save current metrics to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
            filepath = self.data_dir / filename

            # Convert metrics to serializable format
            metrics_data = []
            for metric in self.metrics_history:
                data = {
                    "timestamp": metric.timestamp.isoformat(),
                    "operation_type": metric.operation_type,
                    "dataset_id": metric.dataset_id,
                    "batch_id": metric.batch_id,
                    "duration_seconds": metric.duration_seconds,
                    "records_processed": metric.records_processed,
                    "records_per_second": metric.records_per_second,
                    "memory_usage_mb": metric.memory_usage_mb,
                    "cpu_usage_percent": metric.cpu_usage_percent,
                    "quality_score": metric.quality_score,
                    "error_count": metric.error_count,
                    "metadata": metric.metadata,
                }
                metrics_data.append(data)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2)

            logger.info(f"Saved {len(metrics_data)} metrics to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save metrics to file: {e}")

    def _initialize_benchmarks(self) -> dict[str, PerformanceBenchmark]:
        """Initialize performance benchmarks."""
        return {
            "ingest_dataset": PerformanceBenchmark(
                operation_type="ingest_dataset",
                target_duration_seconds=10.0,
                target_throughput=100.0,
                target_quality_score=85.0,
                max_memory_mb=200.0,
                max_cpu_percent=70.0,
            ),
            "batch_ingest": PerformanceBenchmark(
                operation_type="batch_ingest",
                target_duration_seconds=60.0,
                target_throughput=50.0,
                target_quality_score=80.0,
                max_memory_mb=500.0,
                max_cpu_percent=80.0,
            ),
        }

    def _check_performance_against_benchmarks(
        self, metrics: PerformanceMetrics
    ) -> None:
        """Check metrics against performance benchmarks."""
        benchmark = self.benchmarks.get(metrics.operation_type)
        if not benchmark:
            return

        issues = []

        if metrics.duration_seconds > benchmark.target_duration_seconds:
            issues.append(
                f"Duration {metrics.duration_seconds:.1f}s exceeds target {benchmark.target_duration_seconds:.1f}s"
            )

        if metrics.records_per_second < benchmark.target_throughput:
            issues.append(
                f"Throughput {metrics.records_per_second:.1f} below target {benchmark.target_throughput:.1f}"
            )

        if (
            metrics.quality_score
            and metrics.quality_score < benchmark.target_quality_score
        ):
            issues.append(
                f"Quality {metrics.quality_score:.1f}% below target {benchmark.target_quality_score:.1f}%"
            )

        if issues:
            logger.warning(
                f"Performance benchmark issues for {metrics.operation_type}: {'; '.join(issues)}"
            )

    def _create_error_metrics(self, operation_type: str) -> PerformanceMetrics:
        """Create error metrics for failed operations."""
        return PerformanceMetrics(
            timestamp=datetime.now(),
            operation_type=operation_type,
            error_count=1,
            metadata={"error": "timer_not_found"},
        )

    def _get_memory_usage(self) -> float:
        """Get current memory usage (placeholder)."""
        # In production, would use psutil.Process().memory_info().rss / 1024 / 1024
        return 150.0  # Mock value

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage (placeholder)."""
        # In production, would use psutil.cpu_percent()
        return 45.0  # Mock value
