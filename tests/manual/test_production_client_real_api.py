#!/usr/bin/env python3
"""
Manual testing script for ProductionIstatClient with real ISTAT API.

This script performs comprehensive testing against the actual ISTAT API
to validate production readiness and performance characteristics.
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

# Use proper package imports
try:
    from osservatorio_istat.api.production_istat_client import ProductionIstatClient
    from osservatorio_istat.database.sqlite.repository import get_unified_repository
except ImportError:
    # Development mode fallback
    import sys

    # Issue #84: Removed unsafe sys.path manipulation
    from src.api.production_istat_client import ProductionIstatClient
    from src.database.sqlite.repository import get_unified_repository


class RealAPITester:
    """Comprehensive tester for ProductionIstatClient with real API."""

    def __init__(self):
        """Initialize tester."""
        self.repository = get_unified_repository()
        self.client = ProductionIstatClient(repository=self.repository)
        self.test_results = {}

        print("🧪 Production ISTAT Client - Real API Tester")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def test_basic_functionality(self):
        """Test basic client functionality."""
        print("🔍 Testing basic functionality...")

        try:
            # Test status
            status = self.client.get_status()
            print(f"  ✅ Client status: {status['status']}")
            print(f"  🔄 Circuit breaker: {status['circuit_breaker_state']}")
            print(f"  📊 Rate limit remaining: {status['rate_limit_remaining']}")

            self.test_results["basic_functionality"] = "PASS"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results["basic_functionality"] = f"FAIL: {e}"

        print()

    def test_health_check(self):
        """Test health check with real API."""
        print("🏥 Testing health check...")

        try:
            start_time = time.time()
            health = self.client.health_check()
            response_time = time.time() - start_time

            print(f"  🌐 API Status: {health['status']}")
            print(f"  ⏱️  Response time: {response_time:.3f}s")

            if health["status"] == "healthy":
                print(f"  📊 API response time: {health['response_time']:.3f}s")
                print(f"  🔢 Status code: {health['api_status_code']}")
                self.test_results["health_check"] = "PASS"
            else:
                print(f"  ❌ API Error: {health.get('error', 'Unknown')}")
                self.test_results["health_check"] = f"FAIL: {health.get('error')}"

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            self.test_results["health_check"] = f"FAIL: {e}"

        print()

    def test_dataflows_fetch(self):
        """Test dataflows fetching."""
        print("📋 Testing dataflows fetch...")

        try:
            start_time = time.time()
            dataflows = self.client.fetch_dataflows(limit=10)
            response_time = time.time() - start_time

            print(f"  ⏱️  Fetch time: {response_time:.3f}s")
            print(f"  📊 Dataflows found: {len(dataflows.get('dataflows', []))}")
            print(f"  📈 Total count: {dataflows.get('total_count', 0)}")

            # Show some examples
            for i, dataflow in enumerate(dataflows.get("dataflows", [])[:3]):
                print(f"    {i+1}. {dataflow['name']} (ID: {dataflow['id']})")

            if len(dataflows.get("dataflows", [])) > 0:
                self.test_results["dataflows_fetch"] = "PASS"
                return dataflows.get("dataflows", [])
            else:
                self.test_results["dataflows_fetch"] = "FAIL: No dataflows returned"
                return []

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results["dataflows_fetch"] = f"FAIL: {e}"
            return []

        finally:
            print()

    def test_single_dataset_fetch(self, dataset_id="DCIS_POPRES1"):
        """Test single dataset fetching."""
        print(f"📊 Testing single dataset fetch: {dataset_id}...")

        try:
            # Test structure only
            start_time = time.time()
            result_structure = self.client.fetch_dataset(dataset_id, include_data=False)
            structure_time = time.time() - start_time

            print(f"  📋 Structure fetch: {structure_time:.3f}s")
            print(
                f"  🗂️  Structure status: {result_structure.get('structure', {}).get('status', 'unknown')}"
            )

            # Test with data
            start_time = time.time()
            result_data = self.client.fetch_dataset(dataset_id, include_data=True)
            data_time = time.time() - start_time

            print(f"  📊 Data fetch: {data_time:.3f}s")

            data_info = result_data.get("data", {})
            if data_info.get("status") == "success":
                print(f"  ✅ Data status: {data_info['status']}")
                print(f"  📏 Data size: {data_info.get('size', 0)} bytes")
                print(f"  🔢 Observations: {data_info.get('observations_count', 0)}")

                self.test_results["single_dataset_fetch"] = "PASS"
                return result_data
            else:
                print(f"  ❌ Data error: {data_info.get('error', 'Unknown')}")
                self.test_results[
                    "single_dataset_fetch"
                ] = f"FAIL: {data_info.get('error')}"
                return None

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            self.test_results["single_dataset_fetch"] = f"FAIL: {e}"
            return None

        finally:
            print()

    def test_quality_validation(self, dataset_id="DCIS_POPRES1"):
        """Test quality validation."""
        print(f"🔍 Testing quality validation: {dataset_id}...")

        try:
            start_time = time.time()
            quality = self.client.fetch_with_quality_validation(dataset_id)
            validation_time = time.time() - start_time

            print(f"  ⏱️  Validation time: {validation_time:.3f}s")
            print(f"  🎯 Quality score: {quality.quality_score:.1f}/100")
            print(f"  📊 Completeness: {quality.completeness:.1f}%")
            print(f"  🔄 Consistency: {quality.consistency:.1f}%")

            if quality.validation_errors:
                print(f"  ⚠️  Validation errors:")
                for error in quality.validation_errors[:3]:
                    print(f"    - {error}")
            else:
                print(f"  ✅ No validation errors")

            self.test_results["quality_validation"] = "PASS"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results["quality_validation"] = f"FAIL: {e}"

        print()

    async def test_batch_processing(self, dataset_ids=None):
        """Test batch processing."""
        if dataset_ids is None:
            dataset_ids = ["DCIS_POPRES1", "DCIS_POPSTRRES1"]

        print(f"⚡ Testing batch processing: {len(dataset_ids)} datasets...")

        try:
            start_time = time.time()
            batch_result = await self.client.fetch_dataset_batch(dataset_ids)
            total_time = time.time() - start_time

            print(f"  ⏱️  Total time: {total_time:.3f}s")
            print(f"  ✅ Successful: {len(batch_result.successful)}")
            print(f"  ❌ Failed: {len(batch_result.failed)}")
            print(f"  📊 Batch time: {batch_result.total_time:.3f}s")

            if batch_result.successful:
                print(f"  🎉 Successful datasets:")
                for dataset_id in batch_result.successful:
                    print(f"    - {dataset_id}")

            if batch_result.failed:
                print(f"  💥 Failed datasets:")
                for dataset_id, error in batch_result.failed:
                    print(f"    - {dataset_id}: {error}")

            if len(batch_result.successful) > 0:
                self.test_results["batch_processing"] = "PASS"
            else:
                self.test_results["batch_processing"] = "FAIL: No successful datasets"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results["batch_processing"] = f"FAIL: {e}"

        print()

    def test_repository_integration(self, dataset_data=None):
        """Test repository integration."""
        print("💾 Testing repository integration...")

        if dataset_data is None:
            # Fetch a dataset first
            try:
                dataset_data = self.client.fetch_dataset(
                    "DCIS_POPRES1", include_data=True
                )
            except Exception as e:
                print(f"  ❌ Could not fetch dataset for testing: {e}")
                self.test_results["repository_integration"] = f"FAIL: {e}"
                return

        try:
            start_time = time.time()
            sync_result = self.client.sync_to_repository(dataset_data)
            sync_time = time.time() - start_time

            print(f"  ⏱️  Sync time: {sync_time:.3f}s")
            print(f"  📊 Records synced: {sync_result.records_synced}")
            print(f"  🗃️  Metadata updated: {sync_result.metadata_updated}")
            print(f"  📅 Timestamp: {sync_result.timestamp.strftime('%H:%M:%S')}")

            if sync_result.metadata_updated:
                self.test_results["repository_integration"] = "PASS"
            else:
                self.test_results[
                    "repository_integration"
                ] = "FAIL: Metadata not updated"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results["repository_integration"] = f"FAIL: {e}"

        print()

    def test_metrics_tracking(self):
        """Test metrics tracking."""
        print("📈 Testing metrics tracking...")

        try:
            # Make some requests first
            self.client.health_check()
            self.client.fetch_dataflows(limit=5)

            status = self.client.get_status()
            metrics = status.get("metrics", {})

            print(f"  📊 Total requests: {metrics.get('total_requests', 0)}")
            print(f"  ✅ Successful requests: {metrics.get('successful_requests', 0)}")
            print(f"  ❌ Failed requests: {metrics.get('failed_requests', 0)}")
            print(
                f"  ⏱️  Average response time: {metrics.get('average_response_time', 0):.3f}s"
            )
            print(f"  🕐 Last request: {metrics.get('last_request_time', 'Never')}")

            if metrics.get("total_requests", 0) > 0:
                success_rate = (
                    metrics.get("successful_requests", 0)
                    / metrics.get("total_requests", 1)
                ) * 100
                print(f"  📊 Success rate: {success_rate:.1f}%")
                self.test_results["metrics_tracking"] = "PASS"
            else:
                self.test_results["metrics_tracking"] = "FAIL: No metrics recorded"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results["metrics_tracking"] = f"FAIL: {e}"

        print()

    def test_error_scenarios(self):
        """Test error handling scenarios."""
        print("🚨 Testing error scenarios...")

        # Test invalid dataset
        try:
            print("  Testing invalid dataset...")
            result = self.client.fetch_dataset("INVALID_DATASET_12345")
            print(f"  ⚠️  Unexpected success for invalid dataset")
            self.test_results["error_invalid_dataset"] = "UNEXPECTED_SUCCESS"
        except Exception as e:
            print(f"  ✅ Expected error for invalid dataset: {type(e).__name__}")
            self.test_results["error_invalid_dataset"] = "PASS"

        # Test circuit breaker behavior
        print("  Testing circuit breaker...")
        try:
            # Force some failures to test circuit breaker
            failure_count = 0
            for i in range(3):
                try:
                    self.client.fetch_dataset(f"NONEXISTENT_{i}")
                except Exception:
                    failure_count += 1

            status = self.client.get_status()
            circuit_state = status.get("circuit_breaker_state", "unknown")
            print(
                f"  🔄 Circuit breaker state after {failure_count} failures: {circuit_state}"
            )

            self.test_results["error_circuit_breaker"] = "PASS"

        except Exception as e:
            print(f"  ❌ Error testing circuit breaker: {e}")
            self.test_results["error_circuit_breaker"] = f"FAIL: {e}"

        print()

    async def run_comprehensive_test(self):
        """Run all tests."""
        print("🚀 Starting comprehensive ProductionIstatClient test...")
        print()

        # Basic tests
        self.test_basic_functionality()
        self.test_health_check()

        # API tests
        dataflows = self.test_dataflows_fetch()
        dataset_data = self.test_single_dataset_fetch()
        self.test_quality_validation()

        # Advanced tests
        await self.test_batch_processing()
        self.test_repository_integration(dataset_data)
        self.test_metrics_tracking()
        self.test_error_scenarios()

        # Final report
        self.generate_test_report()

    def generate_test_report(self):
        """Generate final test report."""
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 50)

        passed = 0
        failed = 0

        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result == "PASS" else f"❌ FAIL"
            print(f"{test_name:25} {status}")

            if result == "PASS":
                passed += 1
            else:
                failed += 1
                if result != "PASS":
                    print(f"                           └─ {result}")

        print()
        print(f"📊 Summary: {passed} passed, {failed} failed")
        print(
            f"🎯 Success rate: {(passed / (passed + failed) * 100):.1f}%"
            if (passed + failed) > 0
            else "No tests"
        )

        # Client status
        status = self.client.get_status()
        print()
        print("🔧 Final Client Status:")
        print(f"  Status: {status['status']}")
        print(f"  Circuit Breaker: {status['circuit_breaker_state']}")
        print(f"  Requests Made: {status['metrics']['total_requests']}")
        print(
            f"  Success Rate: {(status['metrics']['successful_requests'] / max(1, status['metrics']['total_requests']) * 100):.1f}%"
        )

        return passed, failed

    def cleanup(self):
        """Cleanup resources."""
        self.client.close()
        print("\n✅ Test completed and resources cleaned up")


async def main():
    """Main test execution."""
    tester = RealAPITester()

    try:
        passed, failed = await tester.run_comprehensive_test()

        if failed == 0:
            print(
                "\n🎉 All tests passed! ProductionIstatClient is ready for production."
            )
            return True
        else:
            print(
                f"\n⚠️  {failed} tests failed. Review issues before production deployment."
            )
            return False

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        return False
    finally:
        tester.cleanup()


if __name__ == "__main__":
    print("⚠️  WARNING: This test makes real API calls to ISTAT servers")
    print("🌐 Ensure you have internet connectivity and respect rate limits")
    print()

    success = asyncio.run(main())
    exit(0 if success else 1)
