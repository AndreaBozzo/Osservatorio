"""
Concurrent User Simulation Tool.

This module provides comprehensive concurrent user simulation for:
- Scaling from 1 to 1000+ concurrent users
- Realistic user behavior patterns
- Load testing with gradual ramp-up
- Connection pooling optimization
- Resource utilization monitoring during load
"""

import json
import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .memory_profiler import MemoryProfiler


@dataclass
class UserSession:
    """Individual user session data."""

    user_id: str
    session_start: datetime
    requests_made: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    api_key: Optional[str] = None
    user_type: str = "basic"
    current_operation: Optional[str] = None


@dataclass
class ConcurrentTestResult:
    """Result of concurrent user test."""

    test_name: str
    concurrent_users: int
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    errors_per_second: float
    peak_memory_mb: float
    avg_cpu_percent: float
    resource_snapshots: list[dict] = field(default_factory=list)
    user_sessions: list[UserSession] = field(default_factory=list)
    error_details: list[dict] = field(default_factory=list)


class UserBehaviorPattern:
    """Defines user behavior patterns."""

    @staticmethod
    def basic_api_user() -> list[dict]:
        """Basic API user pattern."""
        return [
            {"endpoint": "/health", "weight": 1, "method": "GET"},
            {"endpoint": "/api/v1/datasets", "weight": 5, "method": "GET"},
            {"endpoint": "/api/v1/datasets/{dataset_id}", "weight": 3, "method": "GET"},
        ]

    @staticmethod
    def powerbi_user() -> list[dict]:
        """PowerBI user pattern."""
        return [
            {
                "endpoint": "/odata/v1/datasets/{dataset_id}/$metadata",
                "weight": 2,
                "method": "GET",
            },
            {
                "endpoint": "/odata/v1/datasets/{dataset_id}",
                "weight": 8,
                "method": "GET",
            },
            {"endpoint": "/api/v1/datasets", "weight": 1, "method": "GET"},
        ]

    @staticmethod
    def heavy_user() -> list[dict]:
        """Heavy usage user pattern."""
        return [
            {"endpoint": "/api/v1/datasets", "weight": 2, "method": "GET"},
            {"endpoint": "/api/v1/datasets/{dataset_id}", "weight": 5, "method": "GET"},
            {
                "endpoint": "/api/v1/datasets/{dataset_id}/data",
                "weight": 6,
                "method": "GET",
            },
            {
                "endpoint": "/odata/v1/datasets/{dataset_id}",
                "weight": 4,
                "method": "GET",
            },
            {
                "endpoint": "/api/v1/datasets/{dataset_id}/aggregate",
                "weight": 2,
                "method": "GET",
            },
        ]

    @staticmethod
    def admin_user() -> list[dict]:
        """Admin user pattern."""
        return [
            {"endpoint": "/api/v1/admin/stats", "weight": 3, "method": "GET"},
            {"endpoint": "/api/v1/admin/health", "weight": 2, "method": "GET"},
            {"endpoint": "/api/v1/datasets", "weight": 3, "method": "GET"},
            {"endpoint": "/api/v1/protected/datasets", "weight": 2, "method": "GET"},
        ]


class ConcurrentUserSimulator:
    """Concurrent user simulation system."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize concurrent user simulator."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.sessions: dict[str, UserSession] = {}
        self.results: list[ConcurrentTestResult] = []
        self.memory_profiler = MemoryProfiler()
        self.resource_monitor_active = False
        self.resource_snapshots: list[dict] = []

        # Sample data for realistic requests
        self.sample_datasets = [
            "DCIS_POPRES1",
            "DCCN_PILN",
            "DCCV_TAXOCCU",
            "DCIS_MORTALITA1",
            "DCIS_POPSTRRES1",
        ]
        self.sample_territories = ["IT", "ITC1", "ITF1", "ITG1", "ITH1"]
        self.sample_years = [2018, 2019, 2020, 2021, 2022, 2023]

    def _create_session(self) -> requests.Session:
        """Create optimized HTTP session."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=50, pool_maxsize=50
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.timeout = self.timeout

        return session

    def _start_resource_monitoring(self, interval: float = 1.0):
        """Start resource monitoring in background thread."""
        self.resource_monitor_active = True
        self.resource_snapshots.clear()

        def monitor():
            process = psutil.Process()
            while self.resource_monitor_active:
                try:
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    system_memory = psutil.virtual_memory()

                    snapshot = {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": cpu_percent,
                        "memory_rss_mb": memory_info.rss / 1024 / 1024,
                        "memory_vms_mb": memory_info.vms / 1024 / 1024,
                        "system_memory_percent": system_memory.percent,
                        "system_memory_available_mb": system_memory.available
                        / 1024
                        / 1024,
                        "active_connections": len(self.sessions),
                    }

                    self.resource_snapshots.append(snapshot)

                except Exception as e:
                    print(f"Resource monitoring error: {e}")

                time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def _stop_resource_monitoring(self):
        """Stop resource monitoring."""
        self.resource_monitor_active = False

    def _make_request(
        self,
        session: requests.Session,
        user_session: UserSession,
        endpoint_config: dict,
    ) -> dict:
        """Make a single HTTP request."""
        endpoint = endpoint_config["endpoint"]
        method = endpoint_config.get("method", "GET")

        # Replace placeholders with sample data
        if "{dataset_id}" in endpoint:
            endpoint = endpoint.replace(
                "{dataset_id}", random.choice(self.sample_datasets)
            )

        url = f"{self.base_url}{endpoint}"

        # Add realistic query parameters
        params = {}
        if "odata" in endpoint.lower():
            params = {
                "$filter": f"Territory eq '{random.choice(self.sample_territories)}'",
                "$top": str(random.randint(100, 1000)),
                "$skip": str(random.randint(0, 100)),
            }
        elif "/data" in endpoint:
            params = {
                "territory": random.choice(self.sample_territories),
                "year": random.choice(self.sample_years),
                "limit": random.randint(100, 500),
            }

        # Add authentication if needed
        headers = {}
        if user_session.api_key:
            headers["Authorization"] = f"Bearer {user_session.api_key}"

        start_time = time.perf_counter()

        try:
            if method.upper() == "GET":
                response = session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = session.post(url, headers=headers, json=params)
            else:
                response = session.request(method, url, headers=headers, params=params)

            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000

            success = 200 <= response.status_code < 300

            # Update user session
            user_session.requests_made += 1
            user_session.total_response_time += response_time_ms

            if success:
                user_session.successful_requests += 1
            else:
                user_session.failed_requests += 1

            return {
                "success": success,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "endpoint": endpoint,
                "method": method,
                "user_id": user_session.user_id,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000

            user_session.requests_made += 1
            user_session.failed_requests += 1

            return {
                "success": False,
                "status_code": 0,
                "response_time_ms": response_time_ms,
                "endpoint": endpoint,
                "method": method,
                "user_id": user_session.user_id,
                "timestamp": datetime.now(),
                "error": str(e),
            }

    def simulate_user(
        self,
        user_id: str,
        behavior_pattern: list[dict],
        duration_seconds: int,
        requests_per_minute: int = 60,
        user_type: str = "basic",
    ) -> UserSession:
        """Simulate a single user's behavior."""
        user_session = UserSession(
            user_id=user_id,
            session_start=datetime.now(),
            api_key=f"test-key-{user_id}",
            user_type=user_type,
        )

        self.sessions[user_id] = user_session
        session = self._create_session()

        request_interval = 60.0 / requests_per_minute  # seconds between requests
        end_time = time.time() + duration_seconds

        results = []

        try:
            while time.time() < end_time:
                # Choose endpoint based on weights
                total_weight = sum(
                    config.get("weight", 1) for config in behavior_pattern
                )
                rand_weight = random.uniform(0, total_weight)

                current_weight = 0
                selected_config = behavior_pattern[0]  # fallback

                for config in behavior_pattern:
                    current_weight += config.get("weight", 1)
                    if rand_weight <= current_weight:
                        selected_config = config
                        break

                # Make request
                user_session.current_operation = selected_config["endpoint"]
                result = self._make_request(session, user_session, selected_config)
                results.append(result)

                # Wait before next request
                time.sleep(request_interval)

        finally:
            session.close()
            user_session.current_operation = None

        return user_session

    def run_concurrent_test(
        self,
        test_name: str,
        concurrent_users: int,
        duration_seconds: int = 300,  # 5 minutes
        ramp_up_seconds: int = 60,  # 1 minute ramp-up
        user_distribution: Optional[dict[str, float]] = None,
    ) -> ConcurrentTestResult:
        """Run a concurrent user test."""

        # Default user distribution
        if user_distribution is None:
            user_distribution = {
                "basic": 0.6,  # 60% basic users
                "powerbi": 0.2,  # 20% PowerBI users
                "heavy": 0.15,  # 15% heavy users
                "admin": 0.05,  # 5% admin users
            }

        # Start resource monitoring
        self._start_resource_monitoring()

        # Start memory profiling
        with self.memory_profiler.profile_operation(
            f"concurrent_test_{test_name}"
        ) as memory_result:
            start_time = time.time()
            user_sessions = []

            # Calculate user distribution
            user_types = []
            for user_type, ratio in user_distribution.items():
                count = int(concurrent_users * ratio)
                user_types.extend([user_type] * count)

            # Fill remaining slots with basic users
            while len(user_types) < concurrent_users:
                user_types.append("basic")

            # Prepare user configurations
            user_configs = []
            for i in range(concurrent_users):
                user_type = user_types[i]
                user_id = f"user_{i:04d}_{user_type}"

                if user_type == "basic":
                    pattern = UserBehaviorPattern.basic_api_user()
                    rpm = 30
                elif user_type == "powerbi":
                    pattern = UserBehaviorPattern.powerbi_user()
                    rpm = 45
                elif user_type == "heavy":
                    pattern = UserBehaviorPattern.heavy_user()
                    rpm = 60
                elif user_type == "admin":
                    pattern = UserBehaviorPattern.admin_user()
                    rpm = 20
                else:
                    pattern = UserBehaviorPattern.basic_api_user()
                    rpm = 30

                user_configs.append(
                    {
                        "user_id": user_id,
                        "pattern": pattern,
                        "rpm": rpm,
                        "user_type": user_type,
                    }
                )

            # Gradual ramp-up
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = []

                for i, config in enumerate(user_configs):
                    # Stagger user start times for gradual ramp-up
                    delay = (i / concurrent_users) * ramp_up_seconds

                    def delayed_start(cfg, delay_time):
                        time.sleep(delay_time)
                        return self.simulate_user(
                            cfg["user_id"],
                            cfg["pattern"],
                            duration_seconds
                            - int(delay_time),  # Adjust duration for delayed start
                            cfg["rpm"],
                            cfg["user_type"],
                        )

                    future = executor.submit(delayed_start, config, delay)
                    futures.append(future)

                # Collect results
                for future in as_completed(futures):
                    try:
                        user_session = future.result()
                        user_sessions.append(user_session)
                    except Exception as e:
                        print(f"User simulation error: {e}")

            end_time = time.time()
            actual_duration = end_time - start_time

        # Stop resource monitoring
        self._stop_resource_monitoring()

        # Calculate metrics
        total_requests = sum(session.requests_made for session in user_sessions)
        successful_requests = sum(
            session.successful_requests for session in user_sessions
        )
        failed_requests = sum(session.failed_requests for session in user_sessions)

        # Calculate response time statistics
        all_response_times = []
        for session in user_sessions:
            if session.requests_made > 0:
                avg_time = session.total_response_time / session.requests_made
                all_response_times.extend([avg_time] * session.requests_made)

        if all_response_times:
            avg_response_time_ms = statistics.mean(all_response_times)
            sorted_times = sorted(all_response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time_ms = (
                sorted_times[p95_index]
                if p95_index < len(sorted_times)
                else max(all_response_times)
            )
            p99_response_time_ms = (
                sorted_times[p99_index]
                if p99_index < len(sorted_times)
                else max(all_response_times)
            )
        else:
            avg_response_time_ms = 0
            p95_response_time_ms = 0
            p99_response_time_ms = 0

        # Calculate throughput
        requests_per_second = (
            total_requests / actual_duration if actual_duration > 0 else 0
        )
        errors_per_second = (
            failed_requests / actual_duration if actual_duration > 0 else 0
        )

        # Resource usage statistics
        peak_memory_mb = memory_result.peak_memory_mb if memory_result else 0
        avg_cpu_percent = (
            statistics.mean([s["cpu_percent"] for s in self.resource_snapshots])
            if self.resource_snapshots
            else 0
        )

        # Create result
        result = ConcurrentTestResult(
            test_name=test_name,
            concurrent_users=concurrent_users,
            duration_seconds=actual_duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            p99_response_time_ms=p99_response_time_ms,
            requests_per_second=requests_per_second,
            errors_per_second=errors_per_second,
            peak_memory_mb=peak_memory_mb,
            avg_cpu_percent=avg_cpu_percent,
            resource_snapshots=self.resource_snapshots.copy(),
            user_sessions=user_sessions,
        )

        self.results.append(result)
        return result

    def run_scaling_test(
        self,
        test_name: str,
        user_counts: list[int],
        duration_per_test: int = 180,  # 3 minutes per test
    ) -> list[ConcurrentTestResult]:
        """Run scaling tests with different user counts."""
        scaling_results = []

        for user_count in user_counts:
            print(f"Running scaling test with {user_count} users...")

            result = self.run_concurrent_test(
                f"{test_name}_users_{user_count}",
                user_count,
                duration_per_test,
                ramp_up_seconds=min(
                    60, duration_per_test // 3
                ),  # Ramp up time scales with test duration
            )

            scaling_results.append(result)

            # Cool down period between tests
            time.sleep(30)

        return scaling_results

    def generate_load_test_report(
        self,
        results: Optional[list[ConcurrentTestResult]] = None,
        output_path: Optional[Path] = None,
    ) -> dict:
        """Generate comprehensive load testing report."""
        if results is None:
            results = self.results

        if not results:
            raise ValueError("No test results available")

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "tests": {},
            "scaling_analysis": {},
            "performance_insights": [],
        }

        # Analyze each test
        for result in results:
            report["tests"][result.test_name] = {
                "concurrent_users": result.concurrent_users,
                "duration_seconds": result.duration_seconds,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "success_rate": (
                    result.successful_requests / result.total_requests
                    if result.total_requests > 0
                    else 0
                ),
                "avg_response_time_ms": result.avg_response_time_ms,
                "p95_response_time_ms": result.p95_response_time_ms,
                "p99_response_time_ms": result.p99_response_time_ms,
                "requests_per_second": result.requests_per_second,
                "errors_per_second": result.errors_per_second,
                "peak_memory_mb": result.peak_memory_mb,
                "avg_cpu_percent": result.avg_cpu_percent,
                "meets_sla": result.avg_response_time_ms <= 100,  # 100ms SLA
                "user_distribution": self._analyze_user_distribution(
                    result.user_sessions
                ),
            }

        # Scaling analysis
        if len(results) > 1:
            report["scaling_analysis"] = self._analyze_scaling_performance(results)

        # Performance insights
        report["performance_insights"] = self._generate_load_test_insights(results)

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def _analyze_user_distribution(self, user_sessions: list[UserSession]) -> dict:
        """Analyze user type distribution and performance."""
        distribution = {}

        for session in user_sessions:
            user_type = session.user_type
            if user_type not in distribution:
                distribution[user_type] = {
                    "count": 0,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "avg_response_time_ms": 0,
                }

            dist = distribution[user_type]
            dist["count"] += 1
            dist["total_requests"] += session.requests_made
            dist["successful_requests"] += session.successful_requests

            if session.requests_made > 0:
                session_avg = session.total_response_time / session.requests_made
                dist["avg_response_time_ms"] = (
                    dist["avg_response_time_ms"] * (dist["count"] - 1) + session_avg
                ) / dist["count"]

        return distribution

    def _analyze_scaling_performance(self, results: list[ConcurrentTestResult]) -> dict:
        """Analyze performance scaling characteristics."""
        sorted_results = sorted(results, key=lambda r: r.concurrent_users)

        scaling_metrics = {
            "linear_scaling_score": 0,
            "throughput_scaling": [],
            "response_time_scaling": [],
            "error_rate_scaling": [],
            "memory_scaling": [],
        }

        # Calculate scaling metrics
        for result in sorted_results:
            scaling_metrics["throughput_scaling"].append(
                {"users": result.concurrent_users, "rps": result.requests_per_second}
            )

            scaling_metrics["response_time_scaling"].append(
                {
                    "users": result.concurrent_users,
                    "avg_ms": result.avg_response_time_ms,
                    "p95_ms": result.p95_response_time_ms,
                }
            )

            error_rate = (
                result.failed_requests / result.total_requests
                if result.total_requests > 0
                else 0
            )
            scaling_metrics["error_rate_scaling"].append(
                {"users": result.concurrent_users, "error_rate": error_rate}
            )

            scaling_metrics["memory_scaling"].append(
                {
                    "users": result.concurrent_users,
                    "peak_memory_mb": result.peak_memory_mb,
                }
            )

        # Calculate linear scaling score (0-100)
        # Based on how close throughput scaling is to linear
        if len(scaling_metrics["throughput_scaling"]) > 1:
            first_rps = scaling_metrics["throughput_scaling"][0]["rps"]
            first_users = scaling_metrics["throughput_scaling"][0]["users"]

            theoretical_scaling = []
            actual_scaling = []

            for point in scaling_metrics["throughput_scaling"]:
                users_ratio = point["users"] / first_users
                theoretical_rps = first_rps * users_ratio
                actual_rps = point["rps"]

                theoretical_scaling.append(theoretical_rps)
                actual_scaling.append(actual_rps)

            # Calculate correlation coefficient as scaling score
            if len(theoretical_scaling) > 1:
                correlation = statistics.correlation(
                    theoretical_scaling, actual_scaling
                )
                scaling_metrics["linear_scaling_score"] = max(0, correlation * 100)

        return scaling_metrics

    def _generate_load_test_insights(
        self, results: list[ConcurrentTestResult]
    ) -> list[str]:
        """Generate load testing insights."""
        insights = []

        # Overall performance insights
        max_users_tested = max(r.concurrent_users for r in results)
        insights.append(f"Maximum concurrent users tested: {max_users_tested}")

        # SLA compliance
        sla_passing_tests = [r for r in results if r.avg_response_time_ms <= 100]
        if len(sla_passing_tests) != len(results):
            failing_tests = len(results) - len(sla_passing_tests)
            insights.append(f"{failing_tests} tests failed to meet 100ms SLA")

        # Error rate analysis
        high_error_tests = [
            r for r in results if r.failed_requests / r.total_requests > 0.01
        ]  # >1% error rate
        if high_error_tests:
            insights.append(f"{len(high_error_tests)} tests had error rates >1%")

        # Memory usage analysis
        high_memory_tests = [r for r in results if r.peak_memory_mb > 1000]  # >1GB
        if high_memory_tests:
            insights.append(f"{len(high_memory_tests)} tests used >1GB peak memory")

        # Performance degradation
        if len(results) > 1:
            sorted_results = sorted(results, key=lambda r: r.concurrent_users)
            response_time_increase = (
                sorted_results[-1].avg_response_time_ms
                / sorted_results[0].avg_response_time_ms
            )

            if response_time_increase > 5:  # 5x slower
                insights.append(
                    f"Response time increased {response_time_increase:.1f}x with scale"
                )
            elif response_time_increase > 2:  # 2x slower
                insights.append(
                    f"Moderate performance degradation: {response_time_increase:.1f}x slower"
                )

        # Throughput analysis
        max_throughput = max(r.requests_per_second for r in results)
        insights.append(
            f"Peak throughput achieved: {max_throughput:.1f} requests/second"
        )

        if not any(
            "fail" in insight.lower() or "error" in insight.lower()
            for insight in insights
        ):
            insights.append("System demonstrates good scalability characteristics")

        return insights

    def clear_results(self):
        """Clear all test results."""
        self.results.clear()
        self.sessions.clear()
        self.resource_snapshots.clear()

    def close(self):
        """Clean up simulator resources."""
        self._stop_resource_monitoring()
        self.memory_profiler.close()
