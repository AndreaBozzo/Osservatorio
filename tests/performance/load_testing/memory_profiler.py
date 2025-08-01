"""
Memory Profiling and Optimization Tool.

This module provides comprehensive memory profiling for:
- Memory usage tracking during operations
- Memory leak detection
- Memory optimization recommendations
- Peak memory usage analysis
- Memory usage patterns over time
"""
import gc
import json
import logging
import threading
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import psutil
from memory_profiler import memory_usage, profile


@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""

    timestamp: datetime
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float  # Available system memory
    heap_size_mb: float  # Python heap size
    object_count: int  # Number of objects
    tracemalloc_size_mb: Optional[float] = None


@dataclass
class MemoryProfileResult:
    """Memory profiling result."""

    operation_name: str
    start_memory_mb: float
    peak_memory_mb: float
    end_memory_mb: float
    memory_delta_mb: float
    duration_seconds: float
    snapshots: List[MemorySnapshot]
    top_allocations: List[Dict[str, Any]]
    potential_leaks: List[Dict[str, Any]]
    recommendations: List[str]


class MemoryProfiler:
    """Advanced memory profiling tool."""

    def __init__(self, enable_tracemalloc: bool = True):
        """Initialize memory profiler."""
        self.enable_tracemalloc = enable_tracemalloc
        self.process = psutil.Process()
        self.snapshots: List[MemorySnapshot] = []
        self.baseline_memory: Optional[float] = None
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        if enable_tracemalloc:
            tracemalloc.start()

    def take_snapshot(self, operation_name: str = "") -> MemorySnapshot:
        """Take a memory usage snapshot."""
        memory_info = self.process.memory_info()
        system_memory = psutil.virtual_memory()

        # Get heap size approximation
        gc.collect()  # Force garbage collection for accurate measurement
        heap_size_mb = len(gc.get_objects()) * 8 / 1024 / 1024  # Rough estimate

        # Get tracemalloc info if available
        tracemalloc_size_mb = None
        if self.enable_tracemalloc and tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc_size_mb = current / 1024 / 1024

        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=self.process.memory_percent(),
            available_mb=system_memory.available / 1024 / 1024,
            heap_size_mb=heap_size_mb,
            object_count=len(gc.get_objects()),
            tracemalloc_size_mb=tracemalloc_size_mb,
        )

        self.snapshots.append(snapshot)
        return snapshot

    @contextmanager
    def profile_operation(
        self, operation_name: str
    ) -> Generator[MemoryProfileResult, None, None]:
        """Context manager for profiling a specific operation."""
        # Take initial snapshot
        start_snapshot = self.take_snapshot(f"{operation_name}_start")
        start_time = time.perf_counter()

        # Start continuous monitoring
        self.start_monitoring(interval_seconds=0.1)

        # Reset tracemalloc for this operation
        if self.enable_tracemalloc:
            tracemalloc.clear_traces()

        operation_snapshots = []

        try:
            # Create result object to yield
            result = MemoryProfileResult(
                operation_name=operation_name,
                start_memory_mb=start_snapshot.rss_mb,
                peak_memory_mb=start_snapshot.rss_mb,
                end_memory_mb=start_snapshot.rss_mb,
                memory_delta_mb=0,
                duration_seconds=0,
                snapshots=[],
                top_allocations=[],
                potential_leaks=[],
                recommendations=[],
            )

            yield result

        finally:
            # Stop monitoring and take final snapshot
            self.stop_monitoring()
            end_time = time.perf_counter()
            end_snapshot = self.take_snapshot(f"{operation_name}_end")

            # Calculate metrics
            operation_snapshots = [
                s
                for s in self.snapshots
                if start_snapshot.timestamp <= s.timestamp <= end_snapshot.timestamp
            ]

            peak_memory = (
                max(s.rss_mb for s in operation_snapshots)
                if operation_snapshots
                else start_snapshot.rss_mb
            )

            # Get tracemalloc statistics
            top_allocations = []
            if self.enable_tracemalloc:
                top_allocations = self._get_top_allocations()

            # Detect potential memory leaks
            potential_leaks = self._detect_memory_leaks(operation_snapshots)

            # Generate recommendations
            recommendations = self._generate_memory_recommendations(
                start_snapshot.rss_mb,
                peak_memory,
                end_snapshot.rss_mb,
                operation_snapshots,
            )

            # Update result
            result.peak_memory_mb = peak_memory
            result.end_memory_mb = end_snapshot.rss_mb
            result.memory_delta_mb = end_snapshot.rss_mb - start_snapshot.rss_mb
            result.duration_seconds = end_time - start_time
            result.snapshots = operation_snapshots
            result.top_allocations = top_allocations
            result.potential_leaks = potential_leaks
            result.recommendations = recommendations

    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous memory monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        def monitor():
            while self.monitoring_active:
                self.take_snapshot("monitor")
                time.sleep(interval_seconds)

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop continuous memory monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None

    def _get_top_allocations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory allocations using tracemalloc."""
        if not tracemalloc.is_tracing():
            return []

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        allocations = []
        for stat in top_stats[:limit]:
            allocations.append(
                {
                    "filename": stat.traceback.format()[0]
                    if stat.traceback
                    else "unknown",
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count,
                    "average_size_kb": stat.size / stat.count / 1024
                    if stat.count > 0
                    else 0,
                }
            )

        return allocations

    def _detect_memory_leaks(
        self, snapshots: List[MemorySnapshot]
    ) -> List[Dict[str, Any]]:
        """Detect potential memory leaks from snapshots."""
        if len(snapshots) < 10:  # Need enough data points
            return []

        leaks = []

        # Check for consistent memory growth
        memory_values = [s.rss_mb for s in snapshots]

        # Simple leak detection: consistent upward trend
        if len(memory_values) >= 5:
            # Check if memory is consistently increasing
            increases = 0
            for i in range(1, len(memory_values)):
                if memory_values[i] > memory_values[i - 1]:
                    increases += 1

            increase_ratio = increases / (len(memory_values) - 1)

            if increase_ratio > 0.8:  # 80% of measurements show increase
                total_increase = memory_values[-1] - memory_values[0]
                if total_increase > 10:  # More than 10MB increase
                    leaks.append(
                        {
                            "type": "consistent_growth",
                            "description": f"Memory increased consistently by {total_increase:.1f}MB",
                            "severity": "high" if total_increase > 100 else "medium",
                        }
                    )

        # Check for object count growth
        object_counts = [s.object_count for s in snapshots if s.object_count > 0]
        if len(object_counts) >= 5:
            object_increase = object_counts[-1] - object_counts[0]
            if object_increase > 1000:  # More than 1000 new objects
                leaks.append(
                    {
                        "type": "object_growth",
                        "description": f"Object count increased by {object_increase:,}",
                        "severity": "medium",
                    }
                )

        return leaks

    def _generate_memory_recommendations(
        self,
        start_memory: float,
        peak_memory: float,
        end_memory: float,
        snapshots: List[MemorySnapshot],
    ) -> List[str]:
        """Generate memory optimization recommendations."""
        recommendations = []

        memory_increase = end_memory - start_memory
        peak_increase = peak_memory - start_memory

        # High memory usage
        if peak_memory > 1000:  # More than 1GB
            recommendations.append(
                f"High peak memory usage: {peak_memory:.1f}MB. "
                "Consider processing data in smaller batches."
            )

        # Memory not released
        if memory_increase > 50:  # More than 50MB not released
            recommendations.append(
                f"Memory not fully released: {memory_increase:.1f}MB delta. "
                "Check for memory leaks or consider explicit garbage collection."
            )

        # High peak vs steady state
        if peak_increase > 200:  # More than 200MB peak increase
            recommendations.append(
                f"High temporary memory usage: {peak_increase:.1f}MB peak. "
                "Consider streaming or iterative processing."
            )

        # Memory fragmentation
        if len(snapshots) > 10:
            memory_variance = max(s.rss_mb for s in snapshots) - min(
                s.rss_mb for s in snapshots
            )
            if memory_variance > 100:  # High variance
                recommendations.append(
                    "High memory usage variance detected. "
                    "Consider memory pooling or more consistent allocation patterns."
                )

        # System memory pressure
        low_memory_snapshots = [
            s for s in snapshots if s.available_mb < 1000
        ]  # Less than 1GB available
        if len(low_memory_snapshots) > len(snapshots) * 0.3:  # 30% of time
            recommendations.append(
                "System memory pressure detected. "
                "Consider reducing memory usage or scaling horizontally."
            )

        if not recommendations:
            recommendations.append("Memory usage is within acceptable limits.")

        return recommendations

    def profile_function(
        self, func, *args, **kwargs
    ) -> tuple[Any, MemoryProfileResult]:
        """Profile a function call and return result + memory profile."""
        with self.profile_operation(func.__name__) as profile_result:
            result = func(*args, **kwargs)

        return result, profile_result

    def benchmark_memory_operations(self) -> Dict[str, MemoryProfileResult]:
        """Benchmark common memory-intensive operations."""
        results = {}

        # Test 1: Large list creation
        with self.profile_operation("large_list_creation") as result:
            large_list = list(range(1_000_000))
            del large_list
        results["large_list_creation"] = result

        # Test 2: Dictionary operations
        with self.profile_operation("dict_operations") as result:
            large_dict = {f"key_{i}": f"value_{i}" for i in range(100_000)}
            # Access operations
            for i in range(0, 100_000, 1000):
                _ = large_dict.get(f"key_{i}")
            del large_dict
        results["dict_operations"] = result

        # Test 3: String operations
        with self.profile_operation("string_operations") as result:
            large_string = "x" * 1_000_000
            concatenated = large_string + large_string
            parts = concatenated.split("x" * 1000)
            del large_string, concatenated, parts
        results["string_operations"] = result

        # Test 4: Garbage collection
        with self.profile_operation("garbage_collection") as result:
            # Create objects with circular references
            objects = []
            for i in range(10_000):
                obj = {"id": i, "data": [j for j in range(100)]}
                obj["self"] = obj  # Circular reference
                objects.append(obj)

            # Force garbage collection
            collected = gc.collect()
            del objects
        results["garbage_collection"] = result

        return results

    def generate_memory_report(
        self,
        results: Optional[Dict[str, MemoryProfileResult]] = None,
        output_path: Optional[Path] = None,
    ) -> Dict:
        """Generate comprehensive memory analysis report."""
        if results is None:
            results = self.benchmark_memory_operations()

        report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "available_memory_gb": psutil.virtual_memory().available
                / 1024
                / 1024
                / 1024,
                "memory_percent": psutil.virtual_memory().percent,
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                "process_memory_mb": self.process.memory_info().rss / 1024 / 1024,
            },
            "operations": {},
            "overall_insights": [],
        }

        # Analyze each operation
        total_memory_delta = 0
        max_peak_memory = 0
        operations_with_leaks = 0

        for operation_name, result in results.items():
            report["operations"][operation_name] = {
                "start_memory_mb": result.start_memory_mb,
                "peak_memory_mb": result.peak_memory_mb,
                "end_memory_mb": result.end_memory_mb,
                "memory_delta_mb": result.memory_delta_mb,
                "duration_seconds": result.duration_seconds,
                "peak_delta_mb": result.peak_memory_mb - result.start_memory_mb,
                "memory_efficiency": "good"
                if result.memory_delta_mb < 10
                else "needs_attention",
                "leak_detected": len(result.potential_leaks) > 0,
                "recommendations": result.recommendations,
                "top_allocations": result.top_allocations[:5],  # Top 5 only
            }

            total_memory_delta += result.memory_delta_mb
            max_peak_memory = max(max_peak_memory, result.peak_memory_mb)
            if result.potential_leaks:
                operations_with_leaks += 1

        # Generate overall insights
        insights = []

        if total_memory_delta > 50:
            insights.append(
                f"Total memory not released: {total_memory_delta:.1f}MB across all operations"
            )

        if max_peak_memory > 500:
            insights.append(f"High peak memory usage detected: {max_peak_memory:.1f}MB")

        if operations_with_leaks > 0:
            insights.append(
                f"Potential memory leaks detected in {operations_with_leaks} operations"
            )

        system_memory_percent = psutil.virtual_memory().percent
        if system_memory_percent > 80:
            insights.append(f"High system memory usage: {system_memory_percent:.1f}%")

        if not insights:
            insights.append("Memory usage patterns are healthy")

        report["overall_insights"] = insights

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def clear_snapshots(self):
        """Clear all memory snapshots."""
        self.snapshots.clear()

    def close(self):
        """Clean up profiler resources."""
        self.stop_monitoring()
        if self.enable_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()
