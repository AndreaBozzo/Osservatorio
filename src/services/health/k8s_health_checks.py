"""
Kubernetes-compatible health checks for dataflow analyzer service.

Provides startup, liveness, and readiness probes with dependency checking.
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import psutil
from pydantic import BaseModel

from ...utils.logger import get_logger
from ..config.environment_config import HealthConfig
from ..distributed.circuit_breaker import circuit_breaker_registry


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"


class HealthCheck(BaseModel):
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    last_check: datetime
    check_count: int = 0
    failure_count: int = 0


class ServiceHealth(BaseModel):
    """Overall service health status."""

    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    checks: list[HealthCheck]
    system_info: dict[str, Any]
    dependencies: dict[str, Any]


class K8sHealthManager:
    """
    Kubernetes health check manager.

    Provides:
    - Startup probe: Service is starting up
    - Liveness probe: Service is alive (not deadlocked)
    - Readiness probe: Service is ready to serve traffic
    - Custom health checks for dependencies
    """

    def __init__(self, config: HealthConfig):
        """
        Initialize health manager.

        Args:
            config: Health check configuration
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Service state
        self._start_time = time.time()
        self._is_starting = True
        self._is_ready = False
        self._shutdown_requested = False

        # Health checks registry
        self._health_checks: dict[str, Callable] = {}
        self._check_results: dict[str, HealthCheck] = {}

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default system health checks."""
        self.register_health_check("system_resources", self._check_system_resources)
        self.register_health_check("circuit_breakers", self._check_circuit_breakers)

    def register_health_check(self, name: str, check_func: Callable) -> None:
        """
        Register a custom health check.

        Args:
            name: Health check name
            check_func: Async function that returns (status, message)
        """
        self._health_checks[name] = check_func
        self.logger.debug(f"Registered health check: {name}")

    def unregister_health_check(self, name: str) -> None:
        """Remove a health check."""
        if name in self._health_checks:
            del self._health_checks[name]
            if name in self._check_results:
                del self._check_results[name]
            self.logger.debug(f"Unregistered health check: {name}")

    async def _run_health_check(self, name: str, check_func: Callable) -> HealthCheck:
        """Run a single health check with timeout and error handling."""
        start_time = time.time()

        # Get previous check for stats
        previous = self._check_results.get(name)
        check_count = (previous.check_count + 1) if previous else 1
        failure_count = previous.failure_count if previous else 0

        try:
            # Run check with timeout
            if asyncio.iscoroutinefunction(check_func):
                status, message = await asyncio.wait_for(
                    check_func(), timeout=self.config.liveness_timeout
                )
            else:
                status, message = check_func()

            # Reset failure count on success
            if status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                failure_count = 0
            else:
                failure_count += 1

        except asyncio.TimeoutError:
            status = HealthStatus.UNHEALTHY
            message = f"Health check timeout after {self.config.liveness_timeout}s"
            failure_count += 1

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Health check error: {str(e)}"
            failure_count += 1
            self.logger.warning(f"Health check '{name}' failed: {e}")

        response_time = (time.time() - start_time) * 1000

        return HealthCheck(
            name=name,
            status=status,
            message=message,
            response_time_ms=round(response_time, 2),
            last_check=datetime.now(),
            check_count=check_count,
            failure_count=failure_count,
        )

    async def _check_system_resources(self) -> tuple[HealthStatus, str]:
        """Check system resource usage."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # CPU usage (1-second average)
            cpu_percent = psutil.cpu_percent(interval=1)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            # Determine status based on thresholds
            if memory_percent > 90 or cpu_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High resource usage - Memory: {memory_percent:.1f}%, CPU: {cpu_percent:.1f}%, Disk: {disk_percent:.1f}%"
            elif memory_percent > 75 or cpu_percent > 75 or disk_percent > 75:
                status = HealthStatus.DEGRADED
                message = f"Elevated resource usage - Memory: {memory_percent:.1f}%, CPU: {cpu_percent:.1f}%, Disk: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Resource usage normal - Memory: {memory_percent:.1f}%, CPU: {cpu_percent:.1f}%, Disk: {disk_percent:.1f}%"

            return status, message

        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Failed to check system resources: {e}"

    async def _check_circuit_breakers(self) -> tuple[HealthStatus, str]:
        """Check circuit breaker status."""
        try:
            health_summary = circuit_breaker_registry.get_health_summary()

            if health_summary["open_breakers"] > 0:
                status = HealthStatus.DEGRADED
                message = f"{health_summary['open_breakers']} circuit breakers are open"
            elif health_summary["half_open_breakers"] > 0:
                status = HealthStatus.DEGRADED
                message = f"{health_summary['half_open_breakers']} circuit breakers are half-open"
            else:
                status = HealthStatus.HEALTHY
                message = f"All {health_summary['total_circuit_breakers']} circuit breakers are healthy"

            return status, message

        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Failed to check circuit breakers: {e}"

    async def startup_probe(self) -> bool:
        """
        Kubernetes startup probe.

        Returns True when service has finished starting up.
        Used to determine when to start liveness and readiness probes.
        """
        if self._shutdown_requested:
            return False

        uptime = time.time() - self._start_time

        # Service is considered started after minimum startup time
        # and when basic initialization is complete
        if uptime >= self.config.startup_timeout or not self._is_starting:
            self._is_starting = False
            return True

        return False

    async def liveness_probe(self) -> bool:
        """
        Kubernetes liveness probe.

        Returns True if service is alive and not deadlocked.
        If this fails, Kubernetes will restart the pod.
        """
        if self._shutdown_requested:
            return False

        try:
            # Quick health check to ensure service is not deadlocked
            start_time = time.time()

            # Run critical health checks
            critical_checks = ["system_resources"]

            for check_name in critical_checks:
                if check_name in self._health_checks:
                    result = await self._run_health_check(
                        check_name, self._health_checks[check_name]
                    )

                    # Fail if critical check is unhealthy
                    if result.status == HealthStatus.UNHEALTHY:
                        self.logger.error(f"Liveness probe failed: {result.message}")
                        return False

            # Check for excessive response time
            response_time = time.time() - start_time
            if response_time > self.config.liveness_timeout:
                self.logger.error(f"Liveness probe timeout: {response_time:.2f}s")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Liveness probe error: {e}")
            return False

    async def readiness_probe(self) -> bool:
        """
        Kubernetes readiness probe.

        Returns True if service is ready to serve traffic.
        If this fails, service will be removed from load balancer.
        """
        if self._shutdown_requested or self._is_starting:
            return False

        try:
            # Run all health checks
            all_healthy = True

            for name, check_func in self._health_checks.items():
                result = await self._run_health_check(name, check_func)
                self._check_results[name] = result

                # Service not ready if any critical check fails
                if result.status == HealthStatus.UNHEALTHY:
                    all_healthy = False

                # Allow degraded state but log warning
                elif result.status == HealthStatus.DEGRADED:
                    self.logger.warning(
                        f"Degraded health check: {name} - {result.message}"
                    )

            self._is_ready = all_healthy
            return all_healthy

        except Exception as e:
            self.logger.error(f"Readiness probe error: {e}")
            self._is_ready = False
            return False

    async def get_detailed_health(self) -> ServiceHealth:
        """
        Get detailed health status for monitoring and debugging.

        Returns:
            Complete service health information
        """
        # Run all health checks
        check_results = []

        for name, check_func in self._health_checks.items():
            result = await self._run_health_check(name, check_func)
            self._check_results[name] = result
            check_results.append(result)

        # Determine overall status
        if any(check.status == HealthStatus.UNHEALTHY for check in check_results):
            overall_status = HealthStatus.UNHEALTHY
        elif any(check.status == HealthStatus.DEGRADED for check in check_results):
            overall_status = HealthStatus.DEGRADED
        elif self._is_starting:
            overall_status = HealthStatus.STARTING
        else:
            overall_status = HealthStatus.HEALTHY

        # Collect system information
        system_info = {
            "uptime_seconds": time.time() - self._start_time,
            "is_starting": self._is_starting,
            "is_ready": self._is_ready,
            "shutdown_requested": self._shutdown_requested,
            "process_id": psutil.Process().pid,
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.Process().cpu_percent(),
        }

        # Collect dependency information
        dependencies = {
            "circuit_breakers": circuit_breaker_registry.get_health_summary(),
        }

        return ServiceHealth(
            status=overall_status,
            timestamp=datetime.now(),
            uptime_seconds=system_info["uptime_seconds"],
            checks=check_results,
            system_info=system_info,
            dependencies=dependencies,
        )

    def mark_ready(self) -> None:
        """Mark service as ready to serve traffic."""
        self._is_starting = False
        self._is_ready = True
        self.logger.info("Service marked as ready")

    def mark_not_ready(self) -> None:
        """Mark service as not ready to serve traffic."""
        self._is_ready = False
        self.logger.info("Service marked as not ready")

    def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        self._shutdown_requested = True
        self._is_ready = False
        self.logger.info("Graceful shutdown requested")

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_requested

    async def wait_for_readiness(self, timeout: float = 30.0) -> bool:
        """
        Wait for service to become ready.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if service became ready, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await self.readiness_probe():
                return True

            await asyncio.sleep(1.0)

        return False

    def get_probe_endpoints(self) -> dict[str, str]:
        """
        Get standard Kubernetes probe endpoint paths.

        Returns:
            Dictionary mapping probe types to URL paths
        """
        return {
            "startup": "/health/startup",
            "liveness": "/health/live",
            "readiness": "/health/ready",
            "detailed": "/health/status",
        }
