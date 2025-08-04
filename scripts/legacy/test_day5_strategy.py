#!/usr/bin/env python3
"""
Day 5 Testing Strategy - Quick Command
Implements the optimized testing workflow for development.
"""

import subprocess
import sys
import time


def run_fast_tests():
    """Run fast unit tests for development."""
    print("🚀 Running FAST unit tests (development workflow)...")
    start = time.time()

    cmd = [
        "pytest",
        "-c",
        "pytest-fast.ini",
        "tests/unit/test_sqlite_metadata.py",
        "tests/unit/test_config.py",
        "--tb=short",
        "-q",
    ]

    result = subprocess.run(cmd)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"✅ Fast tests completed in {elapsed:.1f}s")
    else:
        print(f"❌ Fast tests failed after {elapsed:.1f}s")

    return result.returncode == 0


def run_critical_tests():
    """Run critical path tests."""
    print("⚡ Running CRITICAL PATH tests...")
    start = time.time()

    cmd = [
        "pytest",
        "-c",
        "pytest-fast.ini",
        "tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration",
        "tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_system_status",
        "tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration",
        "--tb=short",
        "-v",
    ]

    result = subprocess.run(cmd)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"✅ Critical tests completed in {elapsed:.1f}s")
    else:
        print(f"❌ Critical tests failed after {elapsed:.1f}s")

    return result.returncode == 0


def run_integration_sample():
    """Run sample integration tests."""
    print("🔗 Running INTEGRATION sample tests...")
    start = time.time()

    cmd = [
        "pytest",
        "tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_user_preferences_with_cache",
        "tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_cache_operations",
        "--tb=short",
        "-v",
    ]

    result = subprocess.run(cmd)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"✅ Integration sample completed in {elapsed:.1f}s")
    else:
        print(f"❌ Integration sample failed after {elapsed:.1f}s")

    return result.returncode == 0


def main():
    """Main execution."""
    print("🎯 Day 5 Optimized Testing Strategy")
    print("=" * 40)

    if len(sys.argv) > 1:
        strategy = sys.argv[1]
    else:
        strategy = "all"

    success_count = 0
    total_start = time.time()

    if strategy in ["all", "fast"]:
        if run_fast_tests():
            success_count += 1
        print()

    if strategy in ["all", "critical"]:
        if run_critical_tests():
            success_count += 1
        print()

    if strategy in ["all", "integration"]:
        if run_integration_sample():
            success_count += 1
        print()

    total_elapsed = time.time() - total_start

    print(f"🏁 Testing completed in {total_elapsed:.1f}s")

    if strategy == "all":
        if success_count == 3:
            print("🎉 All testing strategies PASSED!")
            print("   Day 5 testing optimization is working correctly.")
        else:
            print(f"⚠️  {success_count}/3 strategies passed.")

    print("\n📋 Usage:")
    print("   python scripts/test_day5_strategy.py fast        # Fast unit tests only")
    print("   python scripts/test_day5_strategy.py critical    # Critical path tests")
    print("   python scripts/test_day5_strategy.py integration # Integration sample")
    print("   python scripts/test_day5_strategy.py all         # All strategies")


if __name__ == "__main__":
    main()
