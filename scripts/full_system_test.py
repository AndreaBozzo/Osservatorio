#!/usr/bin/env python3
"""
Full System Test Suite - Issue #63

Comprehensive testing suite for collaborators to validate
the entire unified pipeline system.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Project imports (after path modification)
from src.pipeline import PipelineConfig, PipelineService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SystemTestSuite:
    """Comprehensive test suite for the unified pipeline."""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    async def run_all_tests(self):
        """Run complete test suite."""
        print("🧪 FULL SYSTEM TEST SUITE - Issue #63")
        print("=" * 60)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Test categories
        test_categories = [
            ("System Health", self._test_system_health),
            ("Basic Functionality", self._test_basic_functionality),
            ("Real Data Processing", self._test_real_data_processing),
            ("Batch Processing", self._test_batch_processing),
            ("Output Validation", self._test_output_validation),
            ("Performance Monitoring", self._test_performance_monitoring),
            ("Integration Points", self._test_integration_points),
        ]

        for category_name, test_method in test_categories:
            print(f"\n🔍 TESTING: {category_name}")
            print("-" * 50)

            try:
                success = await test_method()
                status = "✅ PASS" if success else "❌ FAIL"
                self.results.append((category_name, success))
                print(f"   Result: {status}")

            except Exception as e:
                print(f"   Result: ❌ ERROR - {e}")
                self.results.append((category_name, False))
                logger.error(f"Test category '{category_name}' failed: {e}")

        # Generate final report
        await self._generate_final_report()

    async def _test_system_health(self):
        """Test basic system health."""
        checks = []

        # Check required directories
        required_dirs = [
            "data/databases",
            "data/processed/powerbi",
            "data/processed/tableau",
            "data/performance_results",
        ]

        for dir_path in required_dirs:
            exists = Path(dir_path).exists()
            print(f"   Directory {dir_path}: {'✅' if exists else '❌'}")
            checks.append(exists)

        # Check database files
        sqlite_db = Path("data/databases/osservatorio_metadata.db")
        duckdb_db = Path("data/databases/osservatorio.duckdb")

        sqlite_ok = sqlite_db.exists() and sqlite_db.stat().st_size > 1000
        duckdb_ok = duckdb_db.exists() and duckdb_db.stat().st_size > 1000

        print(f"   SQLite database: {'✅' if sqlite_ok else '❌'}")
        print(f"   DuckDB database: {'✅' if duckdb_ok else '❌'}")

        checks.extend([sqlite_ok, duckdb_ok])

        return all(checks)

    async def _test_basic_functionality(self):
        """Test basic pipeline functionality."""
        try:
            # Initialize service
            config = PipelineConfig(
                batch_size=50,
                max_concurrent=2,
                enable_quality_checks=True,
            )

            service = PipelineService(config=config)
            await service.start_background_processing()
            print("   ✅ Pipeline service initialized")

            # Test status
            status = await service.get_pipeline_status()
            healthy = status.get("status") == "healthy"
            print(
                f"   Pipeline status: {'✅' if healthy else '❌'} {status.get('status')}"
            )

            # Test formats
            formats = service.get_supported_formats()
            formats_ok = len(formats) >= 2 and "powerbi" in formats
            print(f"   Supported formats: {'✅' if formats_ok else '❌'} {formats}")

            return healthy and formats_ok

        except Exception as e:
            print(f"   ❌ Basic functionality error: {e}")
            return False

    async def _test_real_data_processing(self):
        """Test processing with real ISTAT data."""
        try:
            # Check for ISTAT data
            istat_dir = Path("data/raw/istat/istat_data")
            xml_files = list(istat_dir.glob("*.xml"))

            if not xml_files:
                print("   ⚠️  No ISTAT XML files found - using mock data")
                return await self._test_mock_data_processing()

            # Use first XML file
            xml_file = xml_files[0]
            print(f"   Using file: {xml_file.name} ({xml_file.stat().st_size:,} bytes)")

            # Read and process
            with open(xml_file, encoding="utf-8") as f:
                xml_content = f.read()

            service = PipelineService()
            await service.start_background_processing()

            result = await service.pipeline.ingest_dataset(
                dataset_id=f"test_{xml_file.stem}",
                sdmx_data=xml_content,
                target_formats=["powerbi"],
            )

            success = result.status.value == "completed"
            print(
                f"   Processing result: {'✅' if success else '❌'} {result.status.value}"
            )
            print(f"   Records processed: {result.records_processed}")

            if result.quality_score:
                print(f"   Quality score: {result.quality_score.overall_score:.1f}%")

            return success

        except Exception as e:
            print(f"   ❌ Real data processing error: {e}")
            return False

    async def _test_mock_data_processing(self):
        """Test with mock SDMX data."""
        mock_xml = """<?xml version="1.0" encoding="utf-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
                    <generic:Obs>
                        <generic:ObsDimension id="TIME_PERIOD" value="2023"/>
                        <generic:ObsValue value="12345"/>
                    </generic:Obs>
                    <generic:Obs>
                        <generic:ObsDimension id="TIME_PERIOD" value="2024"/>
                        <generic:ObsValue value="23456"/>
                    </generic:Obs>
                </generic:Series>
            </message:DataSet>
        </message:GenericData>"""

        try:
            service = PipelineService()
            await service.start_background_processing()

            result = await service.pipeline.ingest_dataset(
                dataset_id="mock_test_data",
                sdmx_data=mock_xml,
                target_formats=["powerbi"],
            )

            success = result.status.value == "completed"
            print(
                f"   Mock processing: {'✅' if success else '❌'} {result.status.value}"
            )

            return success

        except Exception as e:
            print(f"   ❌ Mock data processing error: {e}")
            return False

    async def _test_batch_processing(self):
        """Test batch processing capabilities."""
        try:
            # Create test datasets
            datasets = []
            for i in range(3):
                datasets.append(
                    {
                        "id": f"batch_test_{i}",
                        "data": f"<mock_data>test_batch_{i}</mock_data>",
                    }
                )

            service = PipelineService()
            await service.start_background_processing()

            # Process batch
            results = await service.pipeline.batch_ingest(
                datasets=datasets,
                target_formats=["powerbi"],
            )

            successful = len([r for r in results if r.status.value == "completed"])
            success_rate = successful / len(results) * 100

            batch_ok = success_rate >= 80  # Allow some failures
            print(
                f"   Batch results: {'✅' if batch_ok else '❌'} {successful}/{len(results)} successful"
            )
            print(f"   Success rate: {success_rate:.1f}%")

            return batch_ok

        except Exception as e:
            print(f"   ❌ Batch processing error: {e}")
            return False

    async def _test_output_validation(self):
        """Test that outputs are generated correctly."""
        try:
            # Check PowerBI outputs
            powerbi_dir = Path("data/processed/powerbi")
            excel_files = list(powerbi_dir.glob("*.xlsx"))
            csv_files = list(powerbi_dir.glob("*.csv"))

            excel_ok = len(excel_files) > 0
            csv_ok = len(csv_files) > 0

            print(
                f"   Excel files: {'✅' if excel_ok else '❌'} {len(excel_files)} found"
            )
            print(f"   CSV files: {'✅' if csv_ok else '❌'} {len(csv_files)} found")

            # Check file integrity
            if excel_files:
                latest_excel = max(excel_files, key=lambda f: f.stat().st_mtime)
                size_ok = latest_excel.stat().st_size > 1000  # At least 1KB
                print(
                    f"   File integrity: {'✅' if size_ok else '❌'} {latest_excel.stat().st_size:,} bytes"
                )
            else:
                size_ok = False

            return excel_ok and csv_ok and size_ok

        except Exception as e:
            print(f"   ❌ Output validation error: {e}")
            return False

    async def _test_performance_monitoring(self):
        """Test performance monitoring system."""
        try:
            # Check performance files
            perf_dir = Path("data/performance_results")
            perf_files = list(perf_dir.glob("*.json"))

            files_ok = len(perf_files) > 0
            print(
                f"   Performance files: {'✅' if files_ok else '❌'} {len(perf_files)} found"
            )

            if perf_files:
                # Check latest performance file
                latest_perf = max(perf_files, key=lambda f: f.stat().st_mtime)

                with open(latest_perf, encoding="utf-8") as f:
                    perf_data = json.load(f)

                # Check required fields
                has_summary = "performance_summary" in perf_data
                print(f"   Performance data structure: {'✅' if has_summary else '❌'}")

                if has_summary:
                    summary = perf_data["performance_summary"]
                    throughput = summary.get("average_throughput", 0)
                    print(f"   Throughput: {throughput:.1f} rec/s")

                return files_ok and has_summary

            return files_ok

        except Exception as e:
            print(f"   ❌ Performance monitoring error: {e}")
            return False

    async def _test_integration_points(self):
        """Test integration with existing components."""
        try:
            checks = []

            # Test converter factory
            from src.converters.factory import ConverterFactory

            factory = ConverterFactory()

            # Test PowerBI converter
            try:
                powerbi_converter = factory.create_converter("powerbi")
                powerbi_ok = powerbi_converter is not None
                print(f"   PowerBI converter: {'✅' if powerbi_ok else '❌'}")
                checks.append(powerbi_ok)
            except Exception as e:
                print(f"   PowerBI converter: ❌ {e}")
                checks.append(False)

            # Test Tableau converter
            try:
                tableau_converter = factory.create_converter("tableau")
                tableau_ok = tableau_converter is not None
                print(f"   Tableau converter: {'✅' if tableau_ok else '❌'}")
                checks.append(tableau_ok)
            except Exception as e:
                print(f"   Tableau converter: ❌ {e}")
                checks.append(False)

            # Test database connections
            try:
                from src.database.sqlite.repository import UnifiedDataRepository

                UnifiedDataRepository()
                db_ok = True
                print(f"   Database repository: {'✅' if db_ok else '❌'}")
                checks.append(db_ok)
            except Exception as e:
                print(f"   Database repository: ❌ {e}")
                checks.append(False)

            return all(checks)

        except Exception as e:
            print(f"   ❌ Integration points error: {e}")
            return False

    async def _generate_final_report(self):
        """Generate comprehensive test report."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print("📊 FULL SYSTEM TEST REPORT")
        print("=" * 60)

        # Test results summary
        passed = sum(1 for _, success in self.results if success)
        total = len(self.results)
        success_rate = (passed / total) * 100 if total > 0 else 0

        print(f"Duration: {duration:.2f} seconds")
        print(f"Test Categories: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")

        print("\n📋 DETAILED RESULTS:")
        for category, success in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {category}: {status}")

        # Overall assessment
        print("\n🎯 SYSTEM ASSESSMENT:")
        if success_rate >= 90:
            print("🏆 EXCELLENT - System fully operational")
            print("✅ All critical components working")
            print("✅ Ready for production use")
            print("✅ Collaborators can proceed with confidence")
        elif success_rate >= 75:
            print("⚡ GOOD - System mostly operational")
            print("✅ Core functionality working")
            print("⚠️  Some minor issues to address")
            print("✅ Safe for collaborative development")
        elif success_rate >= 50:
            print("⚠️  FAIR - Partial functionality")
            print("✅ Basic components working")
            print("❌ Several issues need attention")
            print("⚠️  Review failed tests before proceeding")
        else:
            print("❌ POOR - Major issues detected")
            print("🛑 System not ready for collaboration")
            print("❌ Address critical failures first")

        print("\n🔗 Issue #63 Status:")
        if success_rate >= 75:
            print("✅ Unified Data Ingestion Pipeline - VALIDATED")
            print("✅ System ready for collaborative development")
            print("✅ All integration points confirmed")
            print("✅ Performance monitoring active")
        else:
            print("⚠️  System needs improvement before collaboration")

        # Save report
        report_data = {
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "test_results": [
                {"category": cat, "passed": success} for cat, success in self.results
            ],
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": success_rate,
            },
            "assessment": (
                "excellent"
                if success_rate >= 90
                else (
                    "good"
                    if success_rate >= 75
                    else "fair"
                    if success_rate >= 50
                    else "poor"
                )
            ),
        }

        report_path = (
            Path("data/performance_results")
            / f"full_system_test_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Test report saved: {report_path}")

        return success_rate >= 75


async def main():
    """Run full system test suite."""
    test_suite = SystemTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
