#!/usr/bin/env python3
"""
Performance Testing Automation Script.

This script provides command-line interface for running performance tests:
- Full performance test suite
- Individual test categories
- CI/CD integration
- Regression detection
- Report generation
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.performance.load_testing.comprehensive_performance_suite import (
    PerformanceTestSuite,
)
from tests.performance.load_testing.performance_regression_detector import (
    PerformanceRegressionDetector,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run performance tests for Osservatorio ISTAT platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full performance suite
  python scripts/run_performance_tests.py --full-suite

  # Run only API tests
  python scripts/run_performance_tests.py --api-only

  # Run with custom base URL
  python scripts/run_performance_tests.py --base-url http://staging.example.com --api-only

  # Run for CI/CD with failure threshold
  python scripts/run_performance_tests.py --ci-mode --max-failures 5

  # Establish performance baselines
  python scripts/run_performance_tests.py --establish-baselines
        """,
    )

    # Test selection options
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--full-suite",
        action="store_true",
        help="Run complete performance test suite (default)",
    )
    test_group.add_argument(
        "--api-only", action="store_true", help="Run only API performance tests"
    )
    test_group.add_argument(
        "--database-only",
        action="store_true",
        help="Run only database performance tests",
    )
    test_group.add_argument(
        "--memory-only", action="store_true", help="Run only memory performance tests"
    )
    test_group.add_argument(
        "--load-only", action="store_true", help="Run only load testing"
    )

    # Configuration options
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for API testing (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/performance_results"),
        help="Output directory for test results",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP request timeout in seconds (default: 30)",
    )

    # CI/CD options
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Enable CI/CD mode with structured output and exit codes",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=0,
        help="Maximum allowed test failures before exit with error code",
    )
    parser.add_argument(
        "--min-health-score",
        type=int,
        default=70,
        help="Minimum health score required (0-100, default: 70)",
    )
    parser.add_argument(
        "--sla-compliance-threshold",
        type=float,
        default=0.95,
        help="Minimum SLA compliance rate required (0.0-1.0, default: 0.95)",
    )

    # Regression detection options
    parser.add_argument(
        "--establish-baselines",
        action="store_true",
        help="Establish performance baselines from test results",
    )
    parser.add_argument(
        "--skip-regression-detection",
        action="store_true",
        help="Skip performance regression detection",
    )
    parser.add_argument(
        "--regression-confidence",
        type=float,
        default=0.95,
        help="Confidence level for regression detection (default: 0.95)",
    )

    # Output options
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument(
        "--json-output", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--save-artifacts", action="store_true", help="Save detailed test artifacts"
    )

    args = parser.parse_args()

    # Default to full suite if no specific test selected
    if not any([args.api_only, args.database_only, args.memory_only, args.load_only]):
        args.full_suite = True

    try:
        # Initialize performance test suite
        if not args.quiet:
            print(f"Initializing performance test suite...")
            print(f"Base URL: {args.base_url}")
            print(f"Output directory: {args.output_dir}")

        suite = PerformanceTestSuite(
            base_url=args.base_url,
            output_dir=args.output_dir,
            enable_regression_detection=not args.skip_regression_detection,
        )

        # Run selected tests
        start_time = time.time()

        if args.full_suite:
            if not args.quiet:
                print("Running full performance test suite...")
            results = suite.run_full_performance_suite()

        elif args.api_only:
            if not args.quiet:
                print("Running API performance tests...")
            results = {"api_performance": suite.run_api_performance_tests()}

        elif args.database_only:
            if not args.quiet:
                print("Running database performance tests...")
            results = {"database_performance": suite.run_database_performance_tests()}

        elif args.memory_only:
            if not args.quiet:
                print("Running memory performance tests...")
            results = {"memory_performance": suite.run_memory_performance_tests()}

        elif args.load_only:
            if not args.quiet:
                print("Running load tests...")
            results = suite.run_load_tests()

        duration = time.time() - start_time

        # Establish baselines if requested
        if args.establish_baselines and suite.regression_detector:
            if not args.quiet:
                print("Establishing performance baselines...")

            # Establish baselines for key metrics
            baseline_metrics = [
                "api_response_time_/health",
                "api_response_time_/api/v1/datasets",
                "database_sqlite_avg_query_time_ms",
                "load_test_avg_response_time_50_users_ms",
            ]

            for metric in baseline_metrics:
                try:
                    suite.regression_detector.establish_baseline(
                        metric, minimum_samples=5, force_update=True
                    )
                    if not args.quiet:
                        print(f"Baseline established for: {metric}")
                except ValueError as e:
                    if not args.quiet:
                        print(f"Could not establish baseline for {metric}: {e}")

        # Analyze results for CI/CD mode
        if args.ci_mode:
            exit_code = analyze_ci_results(
                results,
                args.max_failures,
                args.min_health_score,
                args.sla_compliance_threshold,
                args.quiet,
            )
        else:
            exit_code = 0

        # Output results
        if args.json_output:
            print(json.dumps(results, indent=2, default=str))
        elif not args.quiet:
            print_results_summary(results, duration)

        # Cleanup
        suite.cleanup()

        if not args.quiet:
            print(f"\nPerformance testing completed in {duration:.1f} seconds")
            if exit_code == 0:
                print("✅ All tests completed successfully")
            else:
                print(f"❌ Tests completed with issues (exit code: {exit_code})")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n❌ Performance testing interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        if not args.quiet:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def analyze_ci_results(
    results: dict,
    max_failures: int,
    min_health_score: int,
    sla_compliance_threshold: float,
    quiet: bool,
) -> int:
    """Analyze results for CI/CD mode and return appropriate exit code."""

    issues = []

    # Check health score
    health_score = results.get("health_score", 0)
    if health_score < min_health_score:
        issues.append(f"Health score {health_score} below threshold {min_health_score}")

    # Check SLA compliance
    sla_compliance = results.get("sla_compliance", {})
    compliance_rate = sla_compliance.get("overall_compliance_rate", 1.0)
    if compliance_rate < sla_compliance_threshold:
        issues.append(
            f"SLA compliance {compliance_rate:.1%} below threshold {sla_compliance_threshold:.1%}"
        )

    # Check for regression alerts
    regression_alerts = results.get("regression_alerts", [])
    critical_alerts = [a for a in regression_alerts if a.get("severity") == "critical"]
    if critical_alerts:
        issues.append(
            f"{len(critical_alerts)} critical performance regressions detected"
        )

    # Check API failures
    api_results = results.get("api_performance", {})
    api_endpoints = api_results.get("endpoints", {})
    failing_endpoints = [
        ep for ep, data in api_endpoints.items() if not data.get("meets_sla", True)
    ]
    if len(failing_endpoints) > max_failures:
        issues.append(
            f"{len(failing_endpoints)} API endpoints failing SLA (max allowed: {max_failures})"
        )

    # Check load test failures
    load_results = results.get("load_testing", {})
    load_tests = load_results.get("tests", {})
    failing_load_tests = [
        test
        for test, data in load_tests.items()
        if data.get("success_rate", 1.0) < 0.95
    ]
    if failing_load_tests:
        issues.append(f"{len(failing_load_tests)} load tests with <95% success rate")

    # Output CI results
    if not quiet:
        print("\n" + "=" * 50)
        print("CI/CD ANALYSIS RESULTS")
        print("=" * 50)
        print(f"Health Score: {health_score}/100 (threshold: {min_health_score})")
        print(
            f"SLA Compliance: {compliance_rate:.1%} (threshold: {sla_compliance_threshold:.1%})"
        )
        print(
            f"Regression Alerts: {len(regression_alerts)} total, {len(critical_alerts)} critical"
        )
        print(
            f"Failing Endpoints: {len(failing_endpoints)}/{len(api_endpoints)} (max allowed: {max_failures})"
        )

        if issues:
            print(f"\n❌ {len(issues)} issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ All CI/CD checks passed")

    # Return appropriate exit code
    if len(issues) > 0:
        return 1  # Failure
    else:
        return 0  # Success


def print_results_summary(results: dict, duration: float):
    """Print a human-readable summary of test results."""

    print("\n" + "=" * 60)
    print("PERFORMANCE TEST RESULTS SUMMARY")
    print("=" * 60)

    print(f"Test Duration: {duration:.1f} seconds")
    print(f"Health Score: {results.get('health_score', 'N/A')}/100")

    # Overall insights
    insights = results.get("overall_insights", [])
    if insights:
        print(f"\nKey Insights:")
        for insight in insights[:5]:
            print(f"  • {insight}")

    # SLA Compliance
    sla_compliance = results.get("sla_compliance", {})
    compliance_rate = sla_compliance.get("overall_compliance_rate", 1.0)
    print(f"\nSLA Compliance: {compliance_rate:.1%}")

    failing_endpoints = sla_compliance.get("failing_endpoints", [])
    if failing_endpoints:
        print(f"Failing Endpoints: {len(failing_endpoints)}")
        for endpoint in failing_endpoints[:3]:
            print(
                f"  • {endpoint.get('endpoint', 'N/A')}: {endpoint.get('actual_ms', 0):.1f}ms (target: {endpoint.get('target_ms', 0):.1f}ms)"
            )

    # Actionable Recommendations
    recommendations = results.get("actionable_recommendations", [])
    if recommendations:
        print(f"\nTop Recommendations:")
        for rec in recommendations[:5]:
            print(f"  • {rec}")

    # Regression Alerts
    regression_alerts = results.get("regression_alerts", [])
    if regression_alerts:
        print(f"\nRegression Alerts: {len(regression_alerts)}")
        critical_alerts = [
            a for a in regression_alerts if a.get("severity") == "critical"
        ]
        if critical_alerts:
            print(f"  Critical: {len(critical_alerts)}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
