"""
API Endpoint Performance Benchmarking Tool.

This module provides automated benchmarking for API endpoints with:
- Response time measurement (<100ms target)
- Throughput testing
- Concurrency testing
- Memory usage monitoring
- Performance regression detection
"""

import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
import psutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import JWT token generator
try:
    from .jwt_token_generator import PerformanceJWTGenerator
except ImportError:
    # Fallback for direct execution
    import sys

    sys.path.append(str(Path(__file__).parent))
    from jwt_token_generator import PerformanceJWTGenerator


@dataclass
class BenchmarkResult:
    """Performance benchmark result."""

    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    success: bool
    timestamp: datetime
    memory_usage_mb: float
    error_message: Optional[str] = None


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results."""

    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    meets_sla: bool
    sla_target_ms: float


class APIBenchmark:
    """API endpoint benchmarking tool."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize benchmark tool."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = self._create_session()
        self.results: List[BenchmarkResult] = []

        # Initialize JWT token generator for authentication
        try:
            self.jwt_generator = PerformanceJWTGenerator()
            self.auth_headers = self._get_auth_headers()
        except Exception as e:
            print(f"Warning: JWT authentication failed: {e}")
            self.jwt_generator = None
            self.auth_headers = {}

    def _create_session(self) -> requests.Session:
        """Create optimized requests session."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=20, pool_maxsize=20
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.timeout = self.timeout

        return session

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with JWT token."""
        try:
            if self.jwt_generator:
                token = self.jwt_generator.generate_jwt_token(
                    scopes=["read", "datasets", "odata", "admin"]
                )
                if token:
                    return {"Authorization": f"Bearer {token}"}
            return {}
        except Exception as e:
            print(f"Failed to get auth headers: {e}")
            return {}

    def benchmark_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        sla_target_ms: float = 100.0,
    ) -> BenchmarkResult:
        """Benchmark single endpoint request."""
        url = f"{self.base_url}{endpoint}"
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Merge auth headers with provided headers
        request_headers = self.auth_headers.copy()
        if headers:
            request_headers.update(headers)

        start_time = time.perf_counter()

        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(
                    url, headers=request_headers, params=params, json=json_data
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, headers=request_headers, params=params, json=json_data
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url, headers=request_headers, params=params
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000

            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = memory_after - memory_before

            result = BenchmarkResult(
                endpoint=endpoint,
                method=method.upper(),
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                success=200 <= response.status_code < 300,
                timestamp=datetime.now(),
                memory_usage_mb=memory_usage,
            )

        except Exception as e:
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000

            result = BenchmarkResult(
                endpoint=endpoint,
                method=method.upper(),
                response_time_ms=response_time_ms,
                status_code=0,
                success=False,
                timestamp=datetime.now(),
                memory_usage_mb=0,
                error_message=str(e),
            )

        self.results.append(result)
        return result

    def concurrent_benchmark(
        self,
        endpoint: str,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        method: str = "GET",
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        sla_target_ms: float = 100.0,
    ) -> List[BenchmarkResult]:
        """Run concurrent benchmark test."""
        results = []

        def make_request(_) -> BenchmarkResult:
            return self.benchmark_endpoint(
                endpoint, method, headers, params, sla_target_ms=sla_target_ms
            )

        # Use thread pool for concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit all requests
            futures = []
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    future = executor.submit(make_request, f"user_{user}_req_{request}")
                    futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Create error result
                    error_result = BenchmarkResult(
                        endpoint=endpoint,
                        method=method.upper(),
                        response_time_ms=0,
                        status_code=0,
                        success=False,
                        timestamp=datetime.now(),
                        memory_usage_mb=0,
                        error_message=str(e),
                    )
                    results.append(error_result)

        self.results.extend(results)
        return results

    async def async_benchmark(
        self,
        endpoints: List[Dict],
        concurrent_requests: int = 50,
        sla_target_ms: float = 100.0,
    ) -> List[BenchmarkResult]:
        """Run asynchronous benchmark test."""
        results = []

        async def make_async_request(client, endpoint_config):
            endpoint = endpoint_config["endpoint"]
            method = endpoint_config.get("method", "GET")
            headers = endpoint_config.get("headers")
            params = endpoint_config.get("params")

            url = f"{self.base_url}{endpoint}"
            start_time = time.perf_counter()

            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(
                        url,
                        headers=headers,
                        params=params,
                        json=endpoint_config.get("json"),
                    )
                else:
                    raise ValueError(f"Unsupported async method: {method}")

                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000

                return BenchmarkResult(
                    endpoint=endpoint,
                    method=method.upper(),
                    response_time_ms=response_time_ms,
                    status_code=response.status_code,
                    success=200 <= response.status_code < 300,
                    timestamp=datetime.now(),
                    memory_usage_mb=0,  # Memory tracking for async is complex
                )

            except Exception as e:
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000

                return BenchmarkResult(
                    endpoint=endpoint,
                    method=method.upper(),
                    response_time_ms=response_time_ms,
                    status_code=0,
                    success=False,
                    timestamp=datetime.now(),
                    memory_usage_mb=0,
                    error_message=str(e),
                )

        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def make_limited_request(client, endpoint_config):
            async with semaphore:
                return await make_async_request(client, endpoint_config)

        # Create async client and run requests
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [
                make_limited_request(client, endpoint_config)
                for endpoint_config in endpoints
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and add to results
        valid_results = [r for r in results if isinstance(r, BenchmarkResult)]
        self.results.extend(valid_results)

        return valid_results

    def analyze_results(
        self, endpoint: str, sla_target_ms: float = 100.0
    ) -> BenchmarkSummary:
        """Analyze benchmark results for specific endpoint."""
        endpoint_results = [r for r in self.results if r.endpoint == endpoint]

        if not endpoint_results:
            raise ValueError(f"No results found for endpoint: {endpoint}")

        successful_results = [r for r in endpoint_results if r.success]
        failed_results = [r for r in endpoint_results if not r.success]

        if successful_results:
            response_times = [r.response_time_ms for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)

            # Calculate percentiles
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time = (
                sorted_times[p95_index]
                if p95_index < len(sorted_times)
                else max_response_time
            )
            p99_response_time = (
                sorted_times[p99_index]
                if p99_index < len(sorted_times)
                else max_response_time
            )

            # Calculate throughput
            total_time_seconds = (
                max(r.timestamp for r in endpoint_results)
                - min(r.timestamp for r in endpoint_results)
            ).total_seconds()
            requests_per_second = len(successful_results) / max(total_time_seconds, 1)

        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
            p95_response_time = 0
            p99_response_time = 0
            requests_per_second = 0

        error_rate = len(failed_results) / len(endpoint_results)
        meets_sla = avg_response_time <= sla_target_ms if successful_results else False

        return BenchmarkSummary(
            endpoint=endpoint,
            total_requests=len(endpoint_results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            meets_sla=meets_sla,
            sla_target_ms=sla_target_ms,
        )

    def generate_report(self, output_path: Optional[Path] = None) -> Dict:
        """Generate comprehensive performance report."""
        if not self.results:
            raise ValueError("No benchmark results available")

        # Group results by endpoint
        endpoints = list(set(r.endpoint for r in self.results))
        endpoint_summaries = {}

        for endpoint in endpoints:
            try:
                summary = self.analyze_results(endpoint)
                endpoint_summaries[endpoint] = summary
            except ValueError:
                continue

        # Overall statistics
        all_successful = [r for r in self.results if r.success]
        overall_avg_response_time = (
            statistics.mean([r.response_time_ms for r in all_successful])
            if all_successful
            else 0
        )

        overall_error_rate = len([r for r in self.results if not r.success]) / len(
            self.results
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": len(self.results),
            "successful_requests": len(all_successful),
            "overall_avg_response_time_ms": overall_avg_response_time,
            "overall_error_rate": overall_error_rate,
            "endpoints": {
                endpoint: {
                    "total_requests": summary.total_requests,
                    "successful_requests": summary.successful_requests,
                    "avg_response_time_ms": summary.avg_response_time_ms,
                    "p95_response_time_ms": summary.p95_response_time_ms,
                    "p99_response_time_ms": summary.p99_response_time_ms,
                    "requests_per_second": summary.requests_per_second,
                    "error_rate": summary.error_rate,
                    "meets_sla": summary.meets_sla,
                    "sla_target_ms": summary.sla_target_ms,
                }
                for endpoint, summary in endpoint_summaries.items()
            },
            "performance_insights": self._generate_insights(endpoint_summaries),
        }

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def _generate_insights(self, summaries: Dict[str, BenchmarkSummary]) -> List[str]:
        """Generate actionable performance insights."""
        insights = []

        # SLA compliance
        sla_failing = [
            endpoint for endpoint, summary in summaries.items() if not summary.meets_sla
        ]

        if sla_failing:
            insights.append(
                f"SLA violations detected on endpoints: {', '.join(sla_failing)}"
            )

        # High error rates
        high_error_endpoints = [
            endpoint
            for endpoint, summary in summaries.items()
            if summary.error_rate > 0.05  # 5% error threshold
        ]

        if high_error_endpoints:
            insights.append(
                f"High error rates (>5%) on endpoints: {', '.join(high_error_endpoints)}"
            )

        # Slow endpoints
        slow_endpoints = [
            (endpoint, summary.avg_response_time_ms)
            for endpoint, summary in summaries.items()
            if summary.avg_response_time_ms > 200  # 200ms threshold
        ]

        if slow_endpoints:
            slow_list = [f"{ep} ({time:.1f}ms)" for ep, time in slow_endpoints]
            insights.append(f"Slow endpoints (>200ms): {', '.join(slow_list)}")

        # Performance variability
        variable_endpoints = [
            endpoint
            for endpoint, summary in summaries.items()
            if summary.p99_response_time_ms > summary.avg_response_time_ms * 3
        ]

        if variable_endpoints:
            insights.append(
                f"High performance variability on endpoints: {', '.join(variable_endpoints)}"
            )

        # Low throughput
        low_throughput_endpoints = [
            (endpoint, summary.requests_per_second)
            for endpoint, summary in summaries.items()
            if summary.requests_per_second < 10  # 10 RPS threshold
        ]

        if low_throughput_endpoints:
            throughput_list = [
                f"{ep} ({rps:.1f} RPS)" for ep, rps in low_throughput_endpoints
            ]
            insights.append(
                f"Low throughput endpoints (<10 RPS): {', '.join(throughput_list)}"
            )

        if not insights:
            insights.append("All endpoints meeting performance targets!")

        return insights

    def clear_results(self):
        """Clear all benchmark results."""
        self.results.clear()

    def close(self):
        """Close the benchmark session."""
        if self.session:
            self.session.close()
        if hasattr(self, "jwt_generator") and self.jwt_generator:
            self.jwt_generator.close()
