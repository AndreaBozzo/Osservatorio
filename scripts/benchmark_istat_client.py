#!/usr/bin/env python3
"""
Performance Benchmark Suite for ISTAT Client

Benchmarks the performance of the ISTAT client and related components.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.production_istat_client import ProductionIstatClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceBenchmarkSuite:
    """Performance benchmark suite for ISTAT client."""

    def __init__(self, quick_mode=False):
        self.quick_mode = quick_mode
        self.results = {}

    def benchmark_client_initialization(self):
        """Benchmark client initialization time."""
        print("📊 Benchmarking client initialization...")

        times = []
        iterations = 3 if self.quick_mode else 10

        for i in range(iterations):
            start_time = time.time()
            _ = ProductionIstatClient(enable_cache_fallback=True)
            init_time = time.time() - start_time
            times.append(init_time)

        avg_time = sum(times) / len(times)
        self.results["client_init"] = {
            "average": avg_time,
            "min": min(times),
            "max": max(times),
            "iterations": iterations,
        }

        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min(times):.3f}s")
        print(f"   Max: {max(times):.3f}s")

    def benchmark_status_checks(self):
        """Benchmark status check performance."""
        print("📊 Benchmarking status checks...")

        client = ProductionIstatClient(enable_cache_fallback=True)
        times = []
        iterations = 5 if self.quick_mode else 20

        for i in range(iterations):
            start_time = time.time()
            _ = client.get_status()
            check_time = time.time() - start_time
            times.append(check_time)

        avg_time = sum(times) / len(times)
        self.results["status_check"] = {
            "average": avg_time,
            "min": min(times),
            "max": max(times),
            "iterations": iterations,
        }

        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min(times):.3f}s")
        print(f"   Max: {max(times):.3f}s")

    def benchmark_cache_fallback(self):
        """Benchmark cache fallback performance."""
        print("📊 Benchmarking cache fallback...")

        from src.api.mock_istat_data import get_cache_generator

        cache = get_cache_generator()
        times = []
        iterations = 3 if self.quick_mode else 10

        for i in range(iterations):
            start_time = time.time()
            _ = cache.get_cached_dataflows(limit=10)
            cache_time = time.time() - start_time
            times.append(cache_time)

        avg_time = sum(times) / len(times)
        self.results["cache_fallback"] = {
            "average": avg_time,
            "min": min(times),
            "max": max(times),
            "iterations": iterations,
        }

        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min(times):.3f}s")
        print(f"   Max: {max(times):.3f}s")

    async def benchmark_async_operations(self):
        """Benchmark async batch operations."""
        print("📊 Benchmarking async operations...")

        client = ProductionIstatClient(enable_cache_fallback=True)
        test_datasets = ["POPULATION_2023", "EMPLOYMENT_2023"]

        if self.quick_mode:
            test_datasets = test_datasets[:1]

        start_time = time.time()
        try:
            result = await client.fetch_dataset_batch(test_datasets)
            batch_time = time.time() - start_time

            self.results["async_batch"] = {
                "duration": batch_time,
                "datasets": len(test_datasets),
                "successful": len(result.successful)
                if hasattr(result, "successful")
                else 0,
                "failed": len(result.failed) if hasattr(result, "failed") else 0,
            }

            print(f"   Duration: {batch_time:.3f}s")
            print(f"   Datasets: {len(test_datasets)}")

        except Exception as e:
            batch_time = time.time() - start_time
            self.results["async_batch"] = {"duration": batch_time, "error": str(e)}
            print(f"   Error handled in: {batch_time:.3f}s")

    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("Performance Benchmark Suite")
        print("=" * 50)

        if self.quick_mode:
            print("🚀 Quick mode enabled - reduced iterations")

        print()

        # Run synchronous benchmarks
        self.benchmark_client_initialization()
        print()

        self.benchmark_status_checks()
        print()

        self.benchmark_cache_fallback()
        print()

        # Run async benchmarks
        print("Running async benchmarks...")
        asyncio.run(self.benchmark_async_operations())
        print()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print benchmark summary."""
        print("Benchmark Results")
        print("=" * 30)

        for test_name, results in self.results.items():
            print(f"{test_name}:")
            if "average" in results:
                print(f"  Average: {results['average']:.3f}s")
                print(f"  Range: {results['min']:.3f}s - {results['max']:.3f}s")
            elif "duration" in results:
                print(f"  Duration: {results['duration']:.3f}s")
                if "error" in results:
                    print(f"  Error: {results['error']}")
            print()

        print("COMPLETED")


def main():
    """Main benchmark execution."""
    parser = argparse.ArgumentParser(description="ISTAT Client Performance Benchmark")
    parser.add_argument(
        "--quick", action="store_true", help="Run in quick mode with reduced iterations"
    )

    args = parser.parse_args()

    try:
        benchmark_suite = PerformanceBenchmarkSuite(quick_mode=args.quick)
        benchmark_suite.run_all_benchmarks()

    except Exception as e:
        print(f"Benchmark failed: {e}")
        logger.error(f"Benchmark execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
