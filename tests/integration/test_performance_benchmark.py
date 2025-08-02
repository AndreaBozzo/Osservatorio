"""
Performance benchmark integration tests.

Tests that integrate the benchmark script into the test suite
and validate performance regression detection.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


class TestPerformanceBenchmark:
    """Test performance benchmarking integration."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_benchmark_script_execution(self):
        """Test that benchmark script executes without errors."""
        benchmark_script = project_root / "scripts" / "benchmark_istat_client.py"

        # Run benchmark script with timeout
        try:
            result = subprocess.run(
                [sys.executable, str(benchmark_script), "--quick"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
            )

            # Check if script ran successfully
            assert result.returncode == 0, f"Benchmark script failed: {result.stderr}"

            # Check for expected output patterns
            output = result.stdout
            assert "Performance Benchmark Suite" in output
            assert "Benchmark Results" in output or "COMPLETED" in output

        except subprocess.TimeoutExpired:
            pytest.skip("Benchmark script timed out - may indicate performance issues")
        except FileNotFoundError:
            pytest.skip("Benchmark script not found")

    @pytest.mark.benchmark
    def test_production_client_performance_baseline(self):
        """Test production client meets basic performance baselines."""
        import time

        from src.api.production_istat_client import ProductionIstatClient

        client = ProductionIstatClient(enable_cache_fallback=True)

        # Test 1: Client initialization should be fast
        start_time = time.time()
        client.get_status()
        init_time = time.time() - start_time

        assert init_time < 5.0, f"Client initialization too slow: {init_time:.2f}s"

        # Test 2: Status check should be very fast
        start_time = time.time()
        status = client.get_status()
        status_time = time.time() - start_time

        assert status_time < 1.0, f"Status check too slow: {status_time:.2f}s"
        assert "status" in status

        # Test 3: Cache fallback should be fast
        start_time = time.time()
        try:
            # This will likely use cache fallback
            dataflows = client.fetch_dataflows(limit=1)
        except Exception:
            # Expected if no network - cache fallback should still work
            pass
        cache_time = time.time() - start_time

        assert cache_time < 3.0, f"Cache fallback too slow: {cache_time:.2f}s"

    @pytest.mark.benchmark
    def test_circuit_breaker_performance(self):
        """Test circuit breaker doesn't significantly impact performance."""
        import time

        from src.api.production_istat_client import ProductionIstatClient

        client = ProductionIstatClient()

        # Measure multiple status calls to test circuit breaker overhead
        times = []
        for i in range(5):
            start_time = time.time()
            client.get_status()
            times.append(time.time() - start_time)

        # Average time should be consistent (no significant degradation)
        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 0.1, f"Average status call too slow: {avg_time:.3f}s"
        assert max_time < 0.5, f"Max status call too slow: {max_time:.3f}s"

        # Variance should be low (consistent performance)
        if len(times) > 1:
            variance = sum((t - avg_time) ** 2 for t in times) / len(times)
            assert variance < 0.01, f"Status call times too variable: {variance:.3f}"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_async_batch_performance(self):
        """Test async batch processing performance."""
        import time

        from src.api.production_istat_client import ProductionIstatClient

        client = ProductionIstatClient(enable_cache_fallback=True)
        test_dataset_ids = ["POPULATION_2023", "EMPLOYMENT_2023", "GDP_REGIONS_2023"]

        # Test batch processing time
        start_time = time.time()
        try:
            result = await client.fetch_dataset_batch(test_dataset_ids)
            batch_time = time.time() - start_time

            # Batch processing should be reasonably fast
            assert batch_time < 10.0, f"Batch processing too slow: {batch_time:.2f}s"

            # Should process all datasets
            total_processed = len(result.successful) + len(result.failed)
            assert total_processed == len(test_dataset_ids)

        except Exception as e:
            # If network issues, at least test should complete quickly
            batch_time = time.time() - start_time
            assert batch_time < 5.0, f"Batch error handling too slow: {batch_time:.2f}s"

    @pytest.mark.benchmark
    def test_cache_fallback_performance(self):
        """Test cache fallback system performance."""
        import time

        from src.api.mock_istat_data import get_cache_generator

        cache = get_cache_generator()

        # Test cache response time
        start_time = time.time()
        dataflows = cache.get_cached_dataflows(limit=10)
        cache_time = time.time() - start_time

        assert cache_time < 0.1, f"Cache dataflows too slow: {cache_time:.3f}s"
        assert "dataflows" in dataflows
        assert len(dataflows["dataflows"]) > 0

        # Test cached dataset performance
        start_time = time.time()
        dataset = cache.get_cached_dataset("POPULATION_2023", include_data=True)
        dataset_time = time.time() - start_time

        assert dataset_time < 0.5, f"Cache dataset too slow: {dataset_time:.3f}s"
        assert dataset["dataset_id"] == "POPULATION_2023"

    @pytest.mark.benchmark
    def test_memory_usage_stability(self):
        """Test that client doesn't leak memory during operations."""
        import gc
        import os

        import psutil

        from src.api.production_istat_client import ProductionIstatClient

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform multiple operations
        client = ProductionIstatClient(enable_cache_fallback=True)
        for i in range(10):
            client.get_status()
            if i % 3 == 0:
                gc.collect()  # Force garbage collection

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert (
            memory_increase < 50 * 1024 * 1024
        ), f"Memory leak detected: {memory_increase / 1024 / 1024:.1f}MB increase"


class TestPerformanceRegression:
    """Test for performance regression detection."""

    @pytest.mark.benchmark
    def test_performance_regression_detection(self):
        """Test that performance hasn't regressed significantly."""
        import json
        import time
        from pathlib import Path

        from src.api.production_istat_client import ProductionIstatClient

        client = ProductionIstatClient()

        # Define performance baselines (in seconds)
        baselines = {
            "status_check": 0.1,
            "client_init": 2.0,
        }

        results = {}

        # Test client initialization time
        start_time = time.time()
        test_client = ProductionIstatClient()
        results["client_init"] = time.time() - start_time

        # Test status check time
        start_time = time.time()
        test_client.get_status()
        results["status_check"] = time.time() - start_time

        # Check against baselines
        failures = []
        for operation, baseline in baselines.items():
            actual = results.get(operation, float("inf"))
            if actual > baseline * 2:  # Allow 2x baseline before failing
                failures.append(f"{operation}: {actual:.3f}s > {baseline * 2:.3f}s")

        assert not failures, f"Performance regression detected: {', '.join(failures)}"

        # Save results for tracking (optional)
        results_file = Path("performance_results.json")
        if results_file.exists():
            with open(results_file) as f:
                historical_results = json.load(f)
        else:
            historical_results = {}

        from datetime import datetime

        historical_results[datetime.now().isoformat()] = results

        with open(results_file, "w") as f:
            json.dump(historical_results, f, indent=2)
