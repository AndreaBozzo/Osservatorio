"""
Performance Regression Detection System.

This module provides automated performance regression detection with:
- Baseline performance establishment
- Continuous performance monitoring
- Statistical regression analysis
- Alert generation for performance degradation
- Performance trend analysis
- CI/CD integration capabilities
"""
import json
import sqlite3
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats


class RegressionSeverity(Enum):
    """Regression severity levels."""

    NONE = "none"
    MINOR = "minor"  # 10-25% degradation
    MODERATE = "moderate"  # 25-50% degradation
    MAJOR = "major"  # 50-100% degradation
    CRITICAL = "critical"  # >100% degradation


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""

    metric_name: str
    baseline_value: float
    baseline_date: datetime
    sample_count: int
    standard_deviation: float
    percentile_95: float
    percentile_99: float
    threshold_minor: float  # 10% degradation
    threshold_moderate: float  # 25% degradation
    threshold_major: float  # 50% degradation
    threshold_critical: float  # 100% degradation


@dataclass
class RegressionAlert:
    """Performance regression alert."""

    alert_id: str
    metric_name: str
    severity: RegressionSeverity
    current_value: float
    baseline_value: float
    degradation_percent: float
    detection_date: datetime
    description: str
    recommendations: List[str] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    is_resolved: bool = False
    resolution_date: Optional[datetime] = None


@dataclass
class PerformanceTrend:
    """Performance trend analysis."""

    metric_name: str
    trend_direction: str  # "improving", "stable", "degrading"
    trend_strength: float  # -1 to 1 (negative = degrading, positive = improving)
    slope: float
    r_squared: float
    data_points: int
    time_period_days: int
    significance_level: float


class PerformanceRegressionDetector:
    """Automated performance regression detection system."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize regression detector."""
        self.db_path = db_path or "data/performance_results/performance_history.db"
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.alerts: List[RegressionAlert] = []
        self.trends: Dict[str, PerformanceTrend] = {}

        # Initialize database
        self._init_database()

        # Load existing baselines
        self._load_baselines()

    def _init_database(self):
        """Initialize SQLite database for performance history."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    test_type TEXT,
                    git_commit TEXT,
                    environment TEXT DEFAULT 'test',
                    metadata TEXT  -- JSON metadata
                );

                CREATE TABLE IF NOT EXISTS performance_baselines (
                    metric_name TEXT PRIMARY KEY,
                    baseline_value REAL NOT NULL,
                    baseline_date DATETIME NOT NULL,
                    sample_count INTEGER NOT NULL,
                    standard_deviation REAL NOT NULL,
                    percentile_95 REAL NOT NULL,
                    percentile_99 REAL NOT NULL,
                    threshold_minor REAL NOT NULL,
                    threshold_moderate REAL NOT NULL,
                    threshold_major REAL NOT NULL,
                    threshold_critical REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS regression_alerts (
                    alert_id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    baseline_value REAL NOT NULL,
                    degradation_percent REAL NOT NULL,
                    detection_date DATETIME NOT NULL,
                    description TEXT NOT NULL,
                    recommendations TEXT,  -- JSON array
                    affected_endpoints TEXT,  -- JSON array
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolution_date DATETIME
                );

                CREATE INDEX IF NOT EXISTS idx_metrics_name ON performance_metrics(metric_name);
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_severity ON regression_alerts(severity);
            """
            )

    def _load_baselines(self):
        """Load existing baselines from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT metric_name, baseline_value, baseline_date, sample_count,
                       standard_deviation, percentile_95, percentile_99,
                       threshold_minor, threshold_moderate, threshold_major, threshold_critical
                FROM performance_baselines
            """
            )

            for row in cursor.fetchall():
                baseline = PerformanceBaseline(
                    metric_name=row[0],
                    baseline_value=row[1],
                    baseline_date=datetime.fromisoformat(row[2]),
                    sample_count=row[3],
                    standard_deviation=row[4],
                    percentile_95=row[5],
                    percentile_99=row[6],
                    threshold_minor=row[7],
                    threshold_moderate=row[8],
                    threshold_major=row[9],
                    threshold_critical=row[10],
                )
                self.baselines[row[0]] = baseline

    def record_performance_metric(
        self,
        metric_name: str,
        metric_value: float,
        test_type: str = "automated",
        git_commit: Optional[str] = None,
        environment: str = "test",
        metadata: Optional[Dict] = None,
    ):
        """Record a performance metric measurement."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_metrics
                (metric_name, metric_value, timestamp, test_type, git_commit, environment, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric_name,
                    metric_value,
                    datetime.now().isoformat(),
                    test_type,
                    git_commit,
                    environment,
                    json.dumps(metadata) if metadata else None,
                ),
            )

    def establish_baseline(
        self,
        metric_name: str,
        minimum_samples: int = 10,
        days_back: int = 30,
        force_update: bool = False,
    ) -> PerformanceBaseline:
        """Establish performance baseline from historical data."""

        # Check if baseline already exists and is recent
        if not force_update and metric_name in self.baselines:
            baseline = self.baselines[metric_name]
            if (
                datetime.now() - baseline.baseline_date
            ).days < 7:  # Less than a week old
                return baseline

        # Get historical data
        cutoff_date = datetime.now() - timedelta(days=days_back)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT metric_value FROM performance_metrics
                WHERE metric_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (metric_name, cutoff_date.isoformat()),
            )

            values = [row[0] for row in cursor.fetchall()]

        if len(values) < minimum_samples:
            raise ValueError(
                f"Insufficient data for baseline: {len(values)} samples (need {minimum_samples})"
            )

        # Calculate baseline statistics
        baseline_value = statistics.median(values)  # Use median as it's more robust
        std_dev = statistics.stdev(values)
        percentile_95 = np.percentile(values, 95)
        percentile_99 = np.percentile(values, 99)

        # Calculate thresholds (assuming higher values are worse for performance metrics)
        threshold_minor = baseline_value * 1.10  # 10% degradation
        threshold_moderate = baseline_value * 1.25  # 25% degradation
        threshold_major = baseline_value * 1.50  # 50% degradation
        threshold_critical = baseline_value * 2.00  # 100% degradation

        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            baseline_date=datetime.now(),
            sample_count=len(values),
            standard_deviation=std_dev,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            threshold_minor=threshold_minor,
            threshold_moderate=threshold_moderate,
            threshold_major=threshold_major,
            threshold_critical=threshold_critical,
        )

        # Save baseline to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO performance_baselines
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    baseline.metric_name,
                    baseline.baseline_value,
                    baseline.baseline_date.isoformat(),
                    baseline.sample_count,
                    baseline.standard_deviation,
                    baseline.percentile_95,
                    baseline.percentile_99,
                    baseline.threshold_minor,
                    baseline.threshold_moderate,
                    baseline.threshold_major,
                    baseline.threshold_critical,
                ),
            )

        self.baselines[metric_name] = baseline
        return baseline

    def detect_regression(
        self, metric_name: str, current_value: float, confidence_level: float = 0.95
    ) -> Optional[RegressionAlert]:
        """Detect performance regression for a metric."""

        if metric_name not in self.baselines:
            # Try to establish baseline
            try:
                self.establish_baseline(metric_name)
            except ValueError:
                return None  # Not enough data for baseline

        baseline = self.baselines[metric_name]

        # Calculate degradation percentage
        degradation_percent = (
            (current_value - baseline.baseline_value) / baseline.baseline_value
        ) * 100

        # Determine severity
        severity = RegressionSeverity.NONE

        if current_value >= baseline.threshold_critical:
            severity = RegressionSeverity.CRITICAL
        elif current_value >= baseline.threshold_major:
            severity = RegressionSeverity.MAJOR
        elif current_value >= baseline.threshold_moderate:
            severity = RegressionSeverity.MODERATE
        elif current_value >= baseline.threshold_minor:
            severity = RegressionSeverity.MINOR

        # Statistical significance test
        if severity != RegressionSeverity.NONE:
            # Use z-test to check if degradation is statistically significant
            z_score = (
                current_value - baseline.baseline_value
            ) / baseline.standard_deviation
            p_value = 1 - stats.norm.cdf(z_score)  # One-tailed test

            if p_value > (1 - confidence_level):
                # Not statistically significant, reduce severity
                if severity == RegressionSeverity.CRITICAL:
                    severity = RegressionSeverity.MAJOR
                elif severity == RegressionSeverity.MAJOR:
                    severity = RegressionSeverity.MODERATE
                elif severity == RegressionSeverity.MODERATE:
                    severity = RegressionSeverity.MINOR
                else:
                    severity = RegressionSeverity.NONE

        if severity == RegressionSeverity.NONE:
            return None

        # Create alert
        alert_id = f"{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        alert = RegressionAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            severity=severity,
            current_value=current_value,
            baseline_value=baseline.baseline_value,
            degradation_percent=degradation_percent,
            detection_date=datetime.now(),
            description=self._generate_alert_description(
                metric_name, severity, degradation_percent
            ),
            recommendations=self._generate_recommendations(
                metric_name, severity, degradation_percent
            ),
        )

        # Save alert to database
        self._save_alert(alert)
        self.alerts.append(alert)

        return alert

    def _generate_alert_description(
        self, metric_name: str, severity: RegressionSeverity, degradation_percent: float
    ) -> str:
        """Generate alert description."""
        severity_text = {
            RegressionSeverity.MINOR: "Minor",
            RegressionSeverity.MODERATE: "Moderate",
            RegressionSeverity.MAJOR: "Major",
            RegressionSeverity.CRITICAL: "Critical",
        }

        return (
            f"{severity_text[severity]} performance regression detected in {metric_name}. "
            f"Performance degraded by {degradation_percent:.1f}% compared to baseline."
        )

    def _generate_recommendations(
        self, metric_name: str, severity: RegressionSeverity, degradation_percent: float
    ) -> List[str]:
        """Generate recommendations based on regression."""
        recommendations = []

        if "response_time" in metric_name.lower():
            recommendations.extend(
                [
                    "Check for database query performance issues",
                    "Review recent code changes that might affect API performance",
                    "Monitor system resource usage (CPU, memory, I/O)",
                    "Consider enabling query result caching",
                ]
            )

        if "memory" in metric_name.lower():
            recommendations.extend(
                [
                    "Investigate potential memory leaks",
                    "Review object lifecycle management",
                    "Consider increasing garbage collection frequency",
                    "Check for large data structure allocations",
                ]
            )

        if "throughput" in metric_name.lower() or "rps" in metric_name.lower():
            recommendations.extend(
                [
                    "Check for connection pool exhaustion",
                    "Review rate limiting configurations",
                    "Monitor system load and scaling needs",
                    "Investigate potential bottlenecks in request processing",
                ]
            )

        if severity in [RegressionSeverity.MAJOR, RegressionSeverity.CRITICAL]:
            recommendations.extend(
                [
                    "Consider immediate rollback if recent deployment caused regression",
                    "Alert on-call team for immediate investigation",
                    "Implement circuit breaker pattern if not already present",
                ]
            )

        return recommendations

    def _save_alert(self, alert: RegressionAlert):
        """Save alert to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO regression_alerts
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert.alert_id,
                    alert.metric_name,
                    alert.severity.value,
                    alert.current_value,
                    alert.baseline_value,
                    alert.degradation_percent,
                    alert.detection_date.isoformat(),
                    alert.description,
                    json.dumps(alert.recommendations),
                    json.dumps(alert.affected_endpoints),
                    alert.is_resolved,
                    alert.resolution_date.isoformat()
                    if alert.resolution_date
                    else None,
                ),
            )

    def analyze_performance_trends(
        self, metric_name: str, days_back: int = 30, minimum_points: int = 10
    ) -> Optional[PerformanceTrend]:
        """Analyze performance trends over time."""

        cutoff_date = datetime.now() - timedelta(days=days_back)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT metric_value, timestamp FROM performance_metrics
                WHERE metric_name = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """,
                (metric_name, cutoff_date.isoformat()),
            )

            data = [
                (row[0], datetime.fromisoformat(row[1])) for row in cursor.fetchall()
            ]

        if len(data) < minimum_points:
            return None

        # Convert to numeric arrays for analysis
        values = [d[0] for d in data]
        timestamps = [
            (d[1] - data[0][1]).total_seconds() / 86400 for d in data
        ]  # Days since first measurement

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            timestamps, values
        )

        # Determine trend direction and strength
        r_squared = r_value**2
        trend_strength = r_value  # -1 to 1

        if abs(slope) < std_err * 2:  # Not statistically significant
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "degrading"  # Assuming higher values are worse
        else:
            trend_direction = "improving"

        trend = PerformanceTrend(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            slope=slope,
            r_squared=r_squared,
            data_points=len(data),
            time_period_days=days_back,
            significance_level=p_value,
        )

        self.trends[metric_name] = trend
        return trend

    def get_performance_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get performance summary for recent period."""
        cutoff_date = datetime.now() - timedelta(days=days_back)

        with sqlite3.connect(self.db_path) as conn:
            # Get recent alerts
            cursor = conn.execute(
                """
                SELECT severity, COUNT(*) FROM regression_alerts
                WHERE detection_date >= ? AND is_resolved = FALSE
                GROUP BY severity
            """,
                (cutoff_date.isoformat(),),
            )

            alert_counts = dict(cursor.fetchall())

            # Get active metrics
            cursor = conn.execute(
                """
                SELECT DISTINCT metric_name FROM performance_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date.isoformat(),),
            )

            active_metrics = [row[0] for row in cursor.fetchall()]

            # Get recent measurements count
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM performance_metrics
                WHERE timestamp >= ?
            """,
                (cutoff_date.isoformat(),),
            )

            measurement_count = cursor.fetchone()[0]

        summary = {
            "period_days": days_back,
            "active_metrics": len(active_metrics),
            "total_measurements": measurement_count,
            "alert_counts": alert_counts,
            "total_unresolved_alerts": sum(alert_counts.values()),
            "baselines_established": len(self.baselines),
            "metrics_with_trends": len(self.trends),
        }

        return summary

    def generate_regression_report(
        self, output_path: Optional[Path] = None, include_trends: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive regression analysis report."""

        # Get recent performance summary
        summary = self.get_performance_summary()

        # Get all unresolved alerts
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT alert_id, metric_name, severity, current_value, baseline_value,
                       degradation_percent, detection_date, description
                FROM regression_alerts
                WHERE is_resolved = FALSE
                ORDER BY detection_date DESC
            """
            )

            unresolved_alerts = []
            for row in cursor.fetchall():
                unresolved_alerts.append(
                    {
                        "alert_id": row[0],
                        "metric_name": row[1],
                        "severity": row[2],
                        "current_value": row[3],
                        "baseline_value": row[4],
                        "degradation_percent": row[5],
                        "detection_date": row[6],
                        "description": row[7],
                    }
                )

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "baselines": {
                name: {
                    "baseline_value": baseline.baseline_value,
                    "baseline_date": baseline.baseline_date.isoformat(),
                    "sample_count": baseline.sample_count,
                    "standard_deviation": baseline.standard_deviation,
                }
                for name, baseline in self.baselines.items()
            },
            "unresolved_alerts": unresolved_alerts,
            "health_status": self._calculate_health_status(summary, unresolved_alerts),
        }

        # Add trend analysis if requested
        if include_trends:
            trends = {}
            for metric_name in self.baselines.keys():
                trend = self.analyze_performance_trends(metric_name)
                if trend:
                    trends[metric_name] = {
                        "trend_direction": trend.trend_direction,
                        "trend_strength": trend.trend_strength,
                        "slope": trend.slope,
                        "r_squared": trend.r_squared,
                        "significance_level": trend.significance_level,
                    }
            report["trends"] = trends

        # Generate insights
        report["insights"] = self._generate_regression_insights(
            summary, unresolved_alerts
        )

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def _calculate_health_status(
        self, summary: Dict[str, Any], unresolved_alerts: List[Dict]
    ) -> str:
        """Calculate overall performance health status."""

        critical_alerts = len(
            [a for a in unresolved_alerts if a["severity"] == "critical"]
        )
        major_alerts = len([a for a in unresolved_alerts if a["severity"] == "major"])
        total_alerts = len(unresolved_alerts)

        if critical_alerts > 0:
            return "critical"
        elif major_alerts > 2:
            return "degraded"
        elif total_alerts > 5:
            return "warning"
        elif total_alerts > 0:
            return "stable"
        else:
            return "healthy"

    def _generate_regression_insights(
        self, summary: Dict[str, Any], unresolved_alerts: List[Dict]
    ) -> List[str]:
        """Generate regression analysis insights."""
        insights = []

        total_alerts = summary.get("total_unresolved_alerts", 0)

        if total_alerts == 0:
            insights.append(
                "No performance regressions detected - system is performing well"
            )
        else:
            insights.append(f"Found {total_alerts} unresolved performance regressions")

        # Alert severity analysis
        alert_counts = summary.get("alert_counts", {})
        if "critical" in alert_counts:
            insights.append(
                f"{alert_counts['critical']} critical performance issues require immediate attention"
            )

        if "major" in alert_counts:
            insights.append(
                f"{alert_counts['major']} major performance degradations detected"
            )

        # Baseline coverage
        baselines_count = summary.get("baselines_established", 0)
        active_metrics = summary.get("active_metrics", 0)

        if baselines_count < active_metrics:
            missing = active_metrics - baselines_count
            insights.append(f"{missing} metrics missing performance baselines")

        # Trend analysis insights
        degrading_trends = len(
            [t for t in self.trends.values() if t.trend_direction == "degrading"]
        )
        if degrading_trends > 0:
            insights.append(
                f"{degrading_trends} metrics showing degrading performance trends"
            )

        improving_trends = len(
            [t for t in self.trends.values() if t.trend_direction == "improving"]
        )
        if improving_trends > 0:
            insights.append(
                f"{improving_trends} metrics showing improving performance trends"
            )

        return insights

    def resolve_alert(self, alert_id: str, resolution_notes: Optional[str] = None):
        """Mark an alert as resolved."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE regression_alerts
                SET is_resolved = TRUE, resolution_date = ?
                WHERE alert_id = ?
            """,
                (datetime.now().isoformat(), alert_id),
            )

        # Update in-memory alerts
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.is_resolved = True
                alert.resolution_date = datetime.now()
                break
