"""Performance Regression Detection System for DuckDB Operations.

This module provides automated performance regression detection by comparing
current performance metrics with historical baselines and detecting significant
degradations in system performance.
"""
import json
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


try:
    from osservatorio_istat.utils.logger import get_logger
except ImportError:
    # Development mode fallback
    import sys

    # Issue #84: Removed unsafe sys.path manipulation
    from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement."""

    test_name: str
    metric_name: str
    value: float
    unit: str
    timestamp: str
    git_commit: Optional[str] = None
    environment: Optional[str] = None


@dataclass
class RegressionAlert:
    """Performance regression alert."""

    test_name: str
    metric_name: str
    current_value: float
    baseline_value: float
    regression_percent: float
    severity: str  # 'minor', 'moderate', 'severe'
    timestamp: str
    description: str


class PerformanceRegressionDetector:
    """Automated performance regression detection system."""

    def __init__(self, baseline_file: Optional[str] = None):
        """Initialize regression detector.

        Args:
            baseline_file: Path to baseline performance data file
        """
        self.project_root = Path(__file__).parent.parent
        self.baseline_file = (
            baseline_file or self.project_root / "data" / "performance_baselines.json"
        )
        self.results_dir = self.project_root / "data" / "performance_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Regression detection thresholds
        self.thresholds = {
            "minor": 10.0,  # 10% degradation
            "moderate": 25.0,  # 25% degradation
            "severe": 50.0,  # 50% degradation
        }

        self.baseline_data: List[PerformanceMetric] = []
        self.load_baseline_data()

    def load_baseline_data(self) -> None:
        """Load baseline performance data."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    data = json.load(f)
                    self.baseline_data = [
                        PerformanceMetric(**item) for item in data.get("baselines", [])
                    ]
                logger.info(f"Loaded {len(self.baseline_data)} baseline metrics")
            except Exception as e:
                logger.warning(f"Failed to load baseline data: {e}")
                self.baseline_data = []
        else:
            logger.info("No baseline data file found - will create on first run")

    def save_baseline_data(self) -> None:
        """Save baseline performance data."""
        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "last_updated": datetime.now().isoformat(),
                "baselines": [asdict(metric) for metric in self.baseline_data],
            }
            with open(self.baseline_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.baseline_data)} baseline metrics")
        except Exception as e:
            logger.error(f"Failed to save baseline data: {e}")

    def run_performance_tests(self) -> List[PerformanceMetric]:
        """Run performance tests and collect metrics."""
        logger.info("Running DuckDB performance tests...")

        # Run pytest with performance markers
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_bulk_insert_performance",
            "-v",
            "--tb=short",
            "-s",  # Show output
        ]

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            total_time = time.time() - start_time

            if result.returncode != 0:
                logger.warning(f"Performance tests failed: {result.stderr}")
                return []

            # Parse test results and extract metrics
            metrics = self._parse_test_output(result.stdout, total_time)
            logger.info(f"Collected {len(metrics)} performance metrics")
            return metrics

        except subprocess.TimeoutExpired:
            logger.error("Performance tests timed out after 5 minutes")
            return []
        except Exception as e:
            logger.error(f"Failed to run performance tests: {e}")
            return []

    def _parse_test_output(
        self, test_output: str, total_time: float
    ) -> List[PerformanceMetric]:
        """Parse pytest output to extract performance metrics."""
        metrics = []
        current_commit = self._get_current_git_commit()
        timestamp = datetime.now().isoformat()

        # Add overall test execution time
        metrics.append(
            PerformanceMetric(
                test_name="overall_test_suite",
                metric_name="execution_time",
                value=total_time,
                unit="seconds",
                timestamp=timestamp,
                git_commit=current_commit,
                environment="local",
            )
        )

        # Parse individual test timings from pytest output
        lines = test_output.split("\n")
        for line in lines:
            if "PASSED" in line and "::" in line:
                # Extract test name and timing if available
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]

                    # Look for timing information in the line
                    if "[" in line and "]" in line:
                        timing_info = line[line.find("[") + 1 : line.find("]")]
                        try:
                            # Extract percentage and convert to estimated time
                            if "%" in timing_info:
                                percent = float(timing_info.replace("%", "").strip())
                                estimated_time = (percent / 100.0) * total_time

                                metrics.append(
                                    PerformanceMetric(
                                        test_name=test_name,
                                        metric_name="execution_time",
                                        value=estimated_time,
                                        unit="seconds",
                                        timestamp=timestamp,
                                        git_commit=current_commit,
                                        environment="local",
                                    )
                                )
                        except ValueError:
                            pass  # Skip if can't parse timing

        return metrics

    def _get_current_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def detect_regressions(
        self, current_metrics: List[PerformanceMetric]
    ) -> List[RegressionAlert]:
        """Detect performance regressions by comparing with baseline."""
        regressions = []

        if not self.baseline_data:
            logger.info("No baseline data available - current run will become baseline")
            return regressions

        # Group baseline data by test and metric for comparison
        baseline_lookup = {}
        for metric in self.baseline_data:
            key = (metric.test_name, metric.metric_name)
            if key not in baseline_lookup:
                baseline_lookup[key] = []
            baseline_lookup[key].append(metric.value)

        # Calculate baseline statistics (median of recent measurements)
        baseline_stats = {}
        for key, values in baseline_lookup.items():
            # Use median of up to last 10 measurements for stability
            recent_values = values[-10:] if len(values) > 10 else values
            baseline_stats[key] = {
                "median": statistics.median(recent_values),
                "mean": statistics.mean(recent_values),
                "count": len(recent_values),
                "stddev": (
                    statistics.stdev(recent_values) if len(recent_values) > 1 else 0
                ),
            }

        # Compare current metrics with baseline
        for metric in current_metrics:
            key = (metric.test_name, metric.metric_name)

            if key in baseline_stats:
                baseline = baseline_stats[key]
                current_value = metric.value
                baseline_value = baseline["median"]

                # Calculate regression percentage (higher values = worse performance)
                if baseline_value > 0:
                    regression_percent = (
                        (current_value - baseline_value) / baseline_value
                    ) * 100

                    # Determine severity
                    severity = self._classify_regression(regression_percent)

                    if severity:  # Only alert if regression is significant
                        regressions.append(
                            RegressionAlert(
                                test_name=metric.test_name,
                                metric_name=metric.metric_name,
                                current_value=current_value,
                                baseline_value=baseline_value,
                                regression_percent=regression_percent,
                                severity=severity,
                                timestamp=metric.timestamp,
                                description=f"{metric.test_name}.{metric.metric_name} degraded by {regression_percent:.1f}% "
                                f"(current: {current_value:.3f}{metric.unit}, "
                                f"baseline: {baseline_value:.3f}{metric.unit})",
                            )
                        )

        return regressions

    def _classify_regression(self, regression_percent: float) -> Optional[str]:
        """Classify regression severity."""
        if regression_percent >= self.thresholds["severe"]:
            return "severe"
        elif regression_percent >= self.thresholds["moderate"]:
            return "moderate"
        elif regression_percent >= self.thresholds["minor"]:
            return "minor"
        return None  # No significant regression

    def update_baseline(self, new_metrics: List[PerformanceMetric]) -> None:
        """Update baseline with new performance metrics."""
        # Add new metrics to baseline data
        self.baseline_data.extend(new_metrics)

        # Keep only recent data (last 50 measurements per test/metric combination)
        baseline_by_key = {}
        for metric in self.baseline_data:
            key = (metric.test_name, metric.metric_name)
            if key not in baseline_by_key:
                baseline_by_key[key] = []
            baseline_by_key[key].append(metric)

        # Keep only recent measurements
        pruned_baseline = []
        for key, metrics in baseline_by_key.items():
            # Sort by timestamp and keep last 50
            metrics.sort(key=lambda m: m.timestamp)
            recent_metrics = metrics[-50:] if len(metrics) > 50 else metrics
            pruned_baseline.extend(recent_metrics)

        self.baseline_data = pruned_baseline
        self.save_baseline_data()

    def generate_performance_report(
        self, metrics: List[PerformanceMetric], regressions: List[RegressionAlert]
    ) -> str:
        """Generate comprehensive performance report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = [
            "# DuckDB Performance Regression Report",
            f"Generated: {timestamp}",
            f"Git Commit: {metrics[0].git_commit if metrics else 'unknown'}",
            "",
            "## Executive Summary",
        ]

        if regressions:
            regression_counts = {"severe": 0, "moderate": 0, "minor": 0}
            for regression in regressions:
                regression_counts[regression.severity] += 1

            report.extend(
                [
                    f"🚨 **{len(regressions)} performance regressions detected:**",
                    f"- Severe: {regression_counts['severe']}",
                    f"- Moderate: {regression_counts['moderate']}",
                    f"- Minor: {regression_counts['minor']}",
                    "",
                ]
            )
        else:
            report.extend(["✅ **No performance regressions detected**", ""])

        # Performance metrics summary
        report.extend(
            [
                "## Current Performance Metrics",
                "",
                "| Test | Metric | Value | Unit |",
                "|------|--------|-------|------|",
            ]
        )

        for metric in sorted(metrics, key=lambda m: (m.test_name, m.metric_name)):
            report.append(
                f"| {metric.test_name} | {metric.metric_name} | {metric.value:.3f} | {metric.unit} |"
            )

        # Regression details
        if regressions:
            report.extend(["", "## Regression Details", ""])

            for regression in sorted(
                regressions, key=lambda r: r.regression_percent, reverse=True
            ):
                severity_emoji = {"severe": "🔴", "moderate": "🟡", "minor": "🟠"}[
                    regression.severity
                ]
                report.extend(
                    [
                        f"### {severity_emoji} {regression.test_name}.{regression.metric_name}",
                        f"- **Regression**: {regression.regression_percent:.1f}%",
                        f"- **Current**: {regression.current_value:.3f}",
                        f"- **Baseline**: {regression.baseline_value:.3f}",
                        f"- **Description**: {regression.description}",
                        "",
                    ]
                )

        # Recommendations
        if regressions:
            severe_count = sum(1 for r in regressions if r.severity == "severe")
            if severe_count > 0:
                report.extend(
                    [
                        "## Recommendations",
                        "",
                        f"⚠️  **{severe_count} severe regressions require immediate attention:**",
                        "1. Review recent changes that may have impacted performance",
                        "2. Run performance profiling on affected tests",
                        "3. Consider reverting recent changes if performance is critical",
                        "4. Investigate database configuration and indexing strategies",
                        "",
                    ]
                )

        return "\n".join(report)

    def save_results(
        self,
        metrics: List[PerformanceMetric],
        regressions: List[RegressionAlert],
        report: str,
    ) -> None:
        """Save performance results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save metrics as JSON
        metrics_file = self.results_dir / f"performance_metrics_{timestamp}.json"
        with open(metrics_file, "w") as f:
            json.dump([asdict(m) for m in metrics], f, indent=2)

        # Save regressions as JSON
        if regressions:
            regressions_file = (
                self.results_dir / f"performance_regressions_{timestamp}.json"
            )
            with open(regressions_file, "w") as f:
                json.dump([asdict(r) for r in regressions], f, indent=2)

        # Save report as markdown
        report_file = self.results_dir / f"performance_report_{timestamp}.md"
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"Performance results saved to {self.results_dir}")

    def run_full_analysis(
        self,
    ) -> Tuple[List[PerformanceMetric], List[RegressionAlert], str]:
        """Run complete performance regression analysis."""
        logger.info("Starting performance regression analysis...")

        # Run performance tests
        metrics = self.run_performance_tests()
        if not metrics:
            logger.error("No performance metrics collected - analysis failed")
            return [], [], "Performance test execution failed"

        # Detect regressions
        regressions = self.detect_regressions(metrics)

        # Generate report
        report = self.generate_performance_report(metrics, regressions)

        # Save results
        self.save_results(metrics, regressions, report)

        # Update baseline (only if no severe regressions)
        severe_regressions = [r for r in regressions if r.severity == "severe"]
        if not severe_regressions:
            self.update_baseline(metrics)
            logger.info("Baseline updated with new metrics")
        else:
            logger.warning(
                f"Baseline NOT updated due to {len(severe_regressions)} severe regressions"
            )

        return metrics, regressions, report


def main():
    """Main entry point for performance regression detection."""
    detector = PerformanceRegressionDetector()

    try:
        metrics, regressions, report = detector.run_full_analysis()

        # Print summary to console
        print("\n" + "=" * 60)
        print("PERFORMANCE REGRESSION ANALYSIS COMPLETE")
        print("=" * 60)

        if regressions:
            print(f"\n🚨 {len(regressions)} regressions detected:")
            for regression in regressions:
                severity_symbol = {"severe": "🔴", "moderate": "🟡", "minor": "🟠"}[
                    regression.severity
                ]
                print(
                    f"  {severity_symbol} {regression.test_name}: {regression.regression_percent:.1f}% slower"
                )
        else:
            print("\n✅ No performance regressions detected!")

        print(f"\nDetailed report saved to: {detector.results_dir}")
        print("\n" + "=" * 60)

        # Exit with error code if severe regressions found
        severe_count = sum(1 for r in regressions if r.severity == "severe")
        if severe_count > 0:
            print(f"\n❌ Exiting with error due to {severe_count} severe regressions")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nPerformance analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
