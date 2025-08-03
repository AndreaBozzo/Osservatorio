#!/usr/bin/env python3
"""
Scaling Stress Test - Issue #63

Test the pipeline's behavior under increasing load to identify scaling limits.
"""

import asyncio
import gc
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineConfig, PipelineService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScalingStressTest:
    """Comprehensive scaling and stress testing suite."""

    def __init__(self):
        self.results = []
        self.process = psutil.Process()

    async def run_scaling_tests(self):
        """Run comprehensive scaling tests."""
        print("🔥 SCALING STRESS TEST - Issue #63")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Test scenarios in increasing complexity
        test_scenarios = [
            ("Baseline", self._test_baseline_performance),
            ("Memory Scaling", self._test_memory_scaling),
            ("Concurrent Processing", self._test_concurrent_scaling),
            ("Large Dataset Simulation", self._test_large_dataset_handling),
            ("Batch Size Scaling", self._test_batch_size_scaling),
            ("Resource Exhaustion", self._test_resource_limits),
        ]

        for scenario_name, test_method in test_scenarios:
            print(f"\n🧪 SCENARIO: {scenario_name}")
            print("-" * 50)

            # Memory cleanup before each test
            gc.collect()

            try:
                result = await test_method()
                self.results.append((scenario_name, result))

                # Resource monitoring
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                cpu_percent = self.process.cpu_percent()

                print(f"   Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%")

            except Exception as e:
                print(f"   ❌ SCENARIO FAILED: {e}")
                self.results.append((scenario_name, {"error": str(e)}))
                logger.error(f"Scaling test '{scenario_name}' failed: {e}")

        # Generate scaling report
        await self._generate_scaling_report()

    async def _test_baseline_performance(self):
        """Test baseline single dataset performance."""
        print("   Testing single dataset processing baseline...")

        config = PipelineConfig(
            batch_size=100,
            max_concurrent=1,  # Single processing
            enable_quality_checks=True,
        )

        service = PipelineService(config=config)
        await service.start_background_processing()

        # Simple test data
        test_xml = self._generate_test_xml(records=100)

        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        result = await service.pipeline.ingest_dataset(
            dataset_id="baseline_test",
            sdmx_data=test_xml,
            target_formats=["powerbi"],
        )

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024

        duration = end_time - start_time
        memory_delta = end_memory - start_memory

        baseline_result = {
            "duration_seconds": duration,
            "memory_usage_mb": end_memory,
            "memory_delta_mb": memory_delta,
            "records_processed": result.records_processed,
            "throughput": result.records_processed / duration if duration > 0 else 0,
            "status": result.status.value,
        }

        print(
            f"   ✅ Baseline: {duration:.3f}s, {baseline_result['throughput']:.1f} rec/s"
        )
        return baseline_result

    async def _test_memory_scaling(self):
        """Test memory usage with increasing dataset sizes."""
        print("   Testing memory scaling with dataset sizes...")

        config = PipelineConfig(batch_size=1000, max_concurrent=1)
        service = PipelineService(config=config)
        await service.start_background_processing()

        memory_results = []
        record_counts = [100, 500, 1000, 2000, 5000]

        for record_count in record_counts:
            # Memory cleanup
            gc.collect()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            # Generate test data
            test_xml = self._generate_test_xml(records=record_count)

            try:
                start_time = time.time()

                result = await service.pipeline.ingest_dataset(
                    dataset_id=f"memory_test_{record_count}",
                    sdmx_data=test_xml,
                    target_formats=["powerbi"],
                )

                end_time = time.time()
                end_memory = self.process.memory_info().rss / 1024 / 1024

                memory_result = {
                    "record_count": record_count,
                    "duration": end_time - start_time,
                    "start_memory_mb": start_memory,
                    "end_memory_mb": end_memory,
                    "memory_delta_mb": end_memory - start_memory,
                    "memory_per_record": (end_memory - start_memory) / record_count
                    if record_count > 0
                    else 0,
                    "status": result.status.value,
                }

                memory_results.append(memory_result)

                print(
                    f"   Records: {record_count:,} -> Memory: +{memory_result['memory_delta_mb']:.1f}MB"
                )

                # Check for memory issues
                if end_memory > 1000:  # > 1GB
                    print(f"   ⚠️  HIGH MEMORY USAGE: {end_memory:.1f}MB")
                    break

            except Exception as e:
                print(f"   ❌ Failed at {record_count} records: {e}")
                break

        return {
            "memory_scaling_results": memory_results,
            "max_records_tested": max(r["record_count"] for r in memory_results)
            if memory_results
            else 0,
            "memory_efficiency": "good"
            if all(r["memory_per_record"] < 1.0 for r in memory_results)
            else "poor",
        }

    async def _test_concurrent_scaling(self):
        """Test concurrent processing capabilities."""
        print("   Testing concurrent processing scaling...")

        concurrency_results = []
        concurrency_levels = [1, 2, 4, 8]

        for concurrency in concurrency_levels:
            config = PipelineConfig(
                batch_size=100,
                max_concurrent=concurrency,
                enable_quality_checks=False,  # Faster processing
            )

            service = PipelineService(config=config)
            await service.start_background_processing()

            # Create multiple datasets for concurrent processing
            datasets = []
            for i in range(concurrency * 2):  # 2x datasets vs concurrency
                datasets.append(
                    {
                        "id": f"concurrent_test_{concurrency}_{i}",
                        "data": self._generate_test_xml(records=100),
                    }
                )

            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            try:
                results = await service.pipeline.batch_ingest(
                    datasets=datasets,
                    target_formats=["powerbi"],
                )

                end_time = time.time()
                end_memory = self.process.memory_info().rss / 1024 / 1024

                duration = end_time - start_time
                successful = len([r for r in results if r.status.value == "completed"])
                total_records = sum(r.records_processed for r in results)

                concurrency_result = {
                    "concurrency_level": concurrency,
                    "datasets_processed": len(datasets),
                    "successful_datasets": successful,
                    "total_records": total_records,
                    "duration_seconds": duration,
                    "throughput": total_records / duration if duration > 0 else 0,
                    "memory_usage_mb": end_memory,
                    "memory_delta_mb": end_memory - start_memory,
                    "success_rate": successful / len(datasets) * 100,
                }

                concurrency_results.append(concurrency_result)

                print(
                    f"   Concurrency {concurrency}: {successful}/{len(datasets)} success, {concurrency_result['throughput']:.1f} rec/s"
                )

            except Exception as e:
                print(f"   ❌ Concurrency {concurrency} failed: {e}")
                break

        return {
            "concurrency_results": concurrency_results,
            "optimal_concurrency": max(
                concurrency_results, key=lambda x: x["throughput"]
            )["concurrency_level"]
            if concurrency_results
            else 1,
            "max_throughput": max(r["throughput"] for r in concurrency_results)
            if concurrency_results
            else 0,
        }

    async def _test_large_dataset_handling(self):
        """Test handling of large datasets."""
        print("   Testing large dataset processing...")

        config = PipelineConfig(
            batch_size=10000,  # Large batch size
            max_concurrent=2,
            enable_quality_checks=True,
        )

        service = PipelineService(config=config)
        await service.start_background_processing()

        # Simulate progressively larger datasets
        large_dataset_results = []
        sizes = [1000, 5000, 10000]  # Record counts

        for size in sizes:
            print(f"   Testing {size:,} records...")

            # Memory check before
            start_memory = self.process.memory_info().rss / 1024 / 1024
            if start_memory > 800:  # >800MB already used
                print(
                    f"   ⚠️  Skipping {size} - memory already high: {start_memory:.1f}MB"
                )
                break

            large_xml = self._generate_test_xml(records=size)
            xml_size_mb = len(large_xml) / 1024 / 1024

            try:
                start_time = time.time()

                result = await service.pipeline.ingest_dataset(
                    dataset_id=f"large_test_{size}",
                    sdmx_data=large_xml,
                    target_formats=["powerbi"],
                )

                end_time = time.time()
                end_memory = self.process.memory_info().rss / 1024 / 1024

                large_result = {
                    "record_count": size,
                    "xml_size_mb": xml_size_mb,
                    "duration_seconds": end_time - start_time,
                    "memory_usage_mb": end_memory,
                    "memory_delta_mb": end_memory - start_memory,
                    "throughput": result.records_processed / (end_time - start_time)
                    if (end_time - start_time) > 0
                    else 0,
                    "status": result.status.value,
                    "records_processed": result.records_processed,
                }

                large_dataset_results.append(large_result)

                print(
                    f"   ✅ {size:,} records: {large_result['duration_seconds']:.2f}s, {large_result['throughput']:.0f} rec/s"
                )

                # Check for performance degradation
                if large_result["duration_seconds"] > 30:  # >30 seconds
                    print(
                        f"   ⚠️  SLOW PROCESSING: {large_result['duration_seconds']:.1f}s"
                    )

                if end_memory > 1000:  # >1GB
                    print(f"   ⚠️  HIGH MEMORY: {end_memory:.1f}MB")
                    break

            except Exception as e:
                print(f"   ❌ Failed at {size:,} records: {e}")
                break

        return {
            "large_dataset_results": large_dataset_results,
            "max_records_handled": max(r["record_count"] for r in large_dataset_results)
            if large_dataset_results
            else 0,
            "performance_degradation": self._analyze_performance_degradation(
                large_dataset_results
            ),
        }

    async def _test_batch_size_scaling(self):
        """Test different batch sizes."""
        print("   Testing batch size optimization...")

        batch_results = []
        batch_sizes = [50, 100, 500, 1000, 2000]

        for batch_size in batch_sizes:
            config = PipelineConfig(
                batch_size=batch_size,
                max_concurrent=2,
                enable_quality_checks=True,
            )

            service = PipelineService(config=config)
            await service.start_background_processing()

            # Create test datasets
            datasets = []
            for i in range(5):  # 5 datasets
                datasets.append(
                    {
                        "id": f"batch_test_{batch_size}_{i}",
                        "data": self._generate_test_xml(records=200),
                    }
                )

            try:
                start_time = time.time()

                results = await service.pipeline.batch_ingest(
                    datasets=datasets,
                    target_formats=["powerbi"],
                )

                end_time = time.time()

                successful = len([r for r in results if r.status.value == "completed"])
                total_records = sum(r.records_processed for r in results)

                batch_result = {
                    "batch_size": batch_size,
                    "datasets": len(datasets),
                    "successful": successful,
                    "total_records": total_records,
                    "duration": end_time - start_time,
                    "throughput": total_records / (end_time - start_time)
                    if (end_time - start_time) > 0
                    else 0,
                }

                batch_results.append(batch_result)

                print(
                    f"   Batch size {batch_size}: {batch_result['throughput']:.1f} rec/s"
                )

            except Exception as e:
                print(f"   ❌ Batch size {batch_size} failed: {e}")

        return {
            "batch_size_results": batch_results,
            "optimal_batch_size": max(batch_results, key=lambda x: x["throughput"])[
                "batch_size"
            ]
            if batch_results
            else 100,
        }

    async def _test_resource_limits(self):
        """Test system resource limits."""
        print("   Testing resource exhaustion limits...")

        config = PipelineConfig(
            batch_size=2000,
            max_concurrent=8,  # High concurrency
            enable_quality_checks=True,
        )

        service = PipelineService(config=config)
        await service.start_background_processing()

        resource_results = {
            "max_memory_reached": False,
            "max_cpu_reached": False,
            "processing_failures": 0,
            "successful_operations": 0,
        }

        # Create many datasets to stress the system
        datasets = []
        for i in range(20):  # 20 datasets
            datasets.append(
                {
                    "id": f"stress_test_{i}",
                    "data": self._generate_test_xml(records=500),
                }
            )

        try:
            start_memory = self.process.memory_info().rss / 1024 / 1024

            results = await service.pipeline.batch_ingest(
                datasets=datasets,
                target_formats=["powerbi"],
            )

            end_memory = self.process.memory_info().rss / 1024 / 1024

            successful = len([r for r in results if r.status.value == "completed"])
            failed = len(results) - successful

            resource_results.update(
                {
                    "datasets_processed": len(results),
                    "successful_operations": successful,
                    "processing_failures": failed,
                    "start_memory_mb": start_memory,
                    "end_memory_mb": end_memory,
                    "memory_delta_mb": end_memory - start_memory,
                    "max_memory_reached": end_memory > 1000,  # >1GB
                    "success_rate": successful / len(results) * 100 if results else 0,
                }
            )

            print(f"   ✅ Stress test: {successful}/{len(results)} successful")
            print(f"   Memory usage: {start_memory:.1f}MB → {end_memory:.1f}MB")

        except Exception as e:
            print(f"   ❌ Resource limit reached: {e}")
            resource_results["error"] = str(e)

        return resource_results

    def _generate_test_xml(self, records=100):
        """Generate test SDMX XML data."""
        xml_parts = ['<?xml version="1.0" encoding="utf-8"?>']
        xml_parts.append(
            '<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">'
        )
        xml_parts.append("<message:DataSet>")

        for i in range(records):
            xml_parts.append("<generic:Series>")
            xml_parts.append("<generic:Obs>")
            xml_parts.append(
                f'<generic:ObsDimension id="TIME_PERIOD" value="{2020 + (i % 5)}" />'
            )
            xml_parts.append(f'<generic:ObsValue value="{1000 + i}" />')
            xml_parts.append("</generic:Obs>")
            xml_parts.append("</generic:Series>")

        xml_parts.append("</message:DataSet>")
        xml_parts.append("</message:GenericData>")

        return "\n".join(xml_parts)

    def _analyze_performance_degradation(self, results):
        """Analyze performance degradation patterns."""
        if len(results) < 2:
            return "insufficient_data"

        # Check if throughput decreases with size
        throughputs = [r["throughput"] for r in results]
        sizes = [r["record_count"] for r in results]

        # Simple degradation check
        if throughputs[0] > throughputs[-1] * 1.5:  # 50% degradation
            return "significant_degradation"
        elif throughputs[0] > throughputs[-1] * 1.2:  # 20% degradation
            return "moderate_degradation"
        else:
            return "stable_performance"

    async def _generate_scaling_report(self):
        """Generate comprehensive scaling report."""
        end_time = datetime.now()

        print("\n" + "=" * 60)
        print("📊 SCALING STRESS TEST REPORT")
        print("=" * 60)

        successful_tests = len(
            [r for _, r in self.results if not isinstance(r, dict) or "error" not in r]
        )
        total_tests = len(self.results)

        print(f"Test Categories: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")

        # Analyze results for scaling insights
        scaling_insights = self._analyze_scaling_insights()

        print("\n🔍 SCALING INSIGHTS:")
        for insight in scaling_insights:
            print(f"   • {insight}")

        # Recommendations
        recommendations = self._generate_scaling_recommendations()

        print("\n🚀 SCALING RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   • {rec}")

        # Save detailed report
        report_data = {
            "timestamp": end_time.isoformat(),
            "test_results": dict(self.results),
            "scaling_insights": scaling_insights,
            "recommendations": recommendations,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "cpu_count": psutil.cpu_count(),
            },
        }

        report_path = (
            Path("data/performance_results")
            / f"scaling_stress_test_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        )

        import json

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved: {report_path}")

    def _analyze_scaling_insights(self):
        """Extract scaling insights from test results."""
        insights = []

        for test_name, result in self.results:
            if isinstance(result, dict) and "error" not in result:
                if test_name == "Memory Scaling":
                    max_records = result.get("max_records_tested", 0)
                    insights.append(f"Memory scales up to {max_records:,} records")

                elif test_name == "Concurrent Processing":
                    optimal_concurrency = result.get("optimal_concurrency", 1)
                    max_throughput = result.get("max_throughput", 0)
                    insights.append(
                        f"Optimal concurrency: {optimal_concurrency} (max throughput: {max_throughput:.0f} rec/s)"
                    )

                elif test_name == "Large Dataset Simulation":
                    max_records = result.get("max_records_handled", 0)
                    degradation = result.get("performance_degradation", "unknown")
                    insights.append(
                        f"Handles up to {max_records:,} records with {degradation} performance"
                    )

                elif test_name == "Batch Size Scaling":
                    optimal_batch = result.get("optimal_batch_size", 100)
                    insights.append(f"Optimal batch size: {optimal_batch}")

        return insights

    def _generate_scaling_recommendations(self):
        """Generate scaling recommendations based on test results."""
        recommendations = []

        # Analyze memory usage
        memory_results = next(
            (r for n, r in self.results if n == "Memory Scaling"), None
        )
        if memory_results and isinstance(memory_results, dict):
            efficiency = memory_results.get("memory_efficiency", "unknown")
            if efficiency == "poor":
                recommendations.append(
                    "Implement streaming processing for large datasets"
                )

            max_records = memory_results.get("max_records_tested", 0)
            if max_records < 5000:
                recommendations.append("Add memory optimization for larger datasets")

        # Analyze concurrency
        concurrency_results = next(
            (r for n, r in self.results if n == "Concurrent Processing"), None
        )
        if concurrency_results and isinstance(concurrency_results, dict):
            optimal = concurrency_results.get("optimal_concurrency", 1)
            if optimal <= 2:
                recommendations.append(
                    "Consider distributed processing for higher throughput"
                )

        # Analyze large datasets
        large_results = next(
            (r for n, r in self.results if n == "Large Dataset Simulation"), None
        )
        if large_results and isinstance(large_results, dict):
            degradation = large_results.get("performance_degradation", "stable")
            if degradation in ["moderate_degradation", "significant_degradation"]:
                recommendations.append(
                    "Implement chunk-based processing for very large datasets"
                )

        # Resource limits
        resource_results = next(
            (r for n, r in self.results if n == "Resource Exhaustion"), None
        )
        if resource_results and isinstance(resource_results, dict):
            if resource_results.get("max_memory_reached", False):
                recommendations.append("Add memory monitoring and garbage collection")

            success_rate = resource_results.get("success_rate", 100)
            if success_rate < 90:
                recommendations.append("Improve error handling and retry mechanisms")

        # Default recommendations
        if not recommendations:
            recommendations = [
                "Current architecture scales well for tested loads",
                "Monitor performance as dataset sizes increase",
                "Consider PostgreSQL migration for >1000 datasets",
            ]

        return recommendations


async def main():
    """Run scaling stress tests."""
    test_suite = ScalingStressTest()
    await test_suite.run_scaling_tests()


if __name__ == "__main__":
    asyncio.run(main())
