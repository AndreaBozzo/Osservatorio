"""
Resource monitoring for Kubernetes deployments.

Provides monitoring of CPU, memory, and other system resources
for health checks and scaling decisions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import psutil


class ResourceMonitor:
    """
    Monitor system resources for Kubernetes health checks.

    Tracks CPU usage, memory consumption, disk space, and other
    system metrics relevant for containerized environments.
    """

    def __init__(self, check_interval_seconds: int = 30):
        """
        Initialize resource monitor.

        Args:
            check_interval_seconds: Interval between resource checks
        """
        self.check_interval = check_interval_seconds
        self.logger = logging.getLogger(__name__)

        # Resource thresholds
        self.cpu_threshold_percent = 80.0
        self.memory_threshold_percent = 85.0
        self.disk_threshold_percent = 90.0

        # Monitoring state
        self._is_monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._last_check: Optional[datetime] = None

        # Resource history
        self._resource_history: list = []
        self._max_history_size = 100

    def set_thresholds(
        self,
        cpu_percent: float = None,
        memory_percent: float = None,
        disk_percent: float = None,
    ) -> None:
        """
        Set resource usage thresholds.

        Args:
            cpu_percent: CPU usage threshold (0-100)
            memory_percent: Memory usage threshold (0-100)
            disk_percent: Disk usage threshold (0-100)
        """
        if cpu_percent is not None:
            self.cpu_threshold_percent = cpu_percent
        if memory_percent is not None:
            self.memory_threshold_percent = memory_percent
        if disk_percent is not None:
            self.disk_threshold_percent = disk_percent

        self.logger.info(
            f"Resource thresholds updated: CPU={self.cpu_threshold_percent}%, "
            f"Memory={self.memory_threshold_percent}%, "
            f"Disk={self.disk_threshold_percent}%"
        )

    def get_current_resources(self) -> dict[str, Any]:
        """
        Get current resource usage.

        Returns:
            Dictionary with current resource metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)

            # Disk usage (root filesystem)
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_total_gb = disk.total / (1024 * 1024 * 1024)

            # Process info
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            process_cpu_percent = process.cpu_percent()

            # Network I/O
            net_io = psutil.net_io_counters()

            resources = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "process_percent": process_cpu_percent,
                },
                "memory": {
                    "usage_percent": memory_percent,
                    "used_mb": memory_used_mb,
                    "total_mb": memory_total_mb,
                    "process_mb": process_memory_mb,
                },
                "disk": {
                    "usage_percent": disk_percent,
                    "used_gb": disk_used_gb,
                    "total_gb": disk_total_gb,
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                },
            }

            return resources

        except Exception as e:
            self.logger.error(f"Error getting resource metrics: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def check_resource_health(self) -> dict[str, Any]:
        """
        Check if resource usage is within healthy thresholds.

        Returns:
            Dictionary with health status and recommendations
        """
        resources = self.get_current_resources()

        if "error" in resources:
            return {
                "status": "unknown",
                "healthy": False,
                "message": f"Failed to get resource metrics: {resources['error']}",
            }

        issues = []
        warnings = []

        # Check CPU usage
        cpu_usage = resources["cpu"]["usage_percent"]
        if cpu_usage > self.cpu_threshold_percent:
            issues.append(
                f"High CPU usage: {cpu_usage:.1f}% > {self.cpu_threshold_percent}%"
            )
        elif cpu_usage > self.cpu_threshold_percent * 0.8:
            warnings.append(f"Elevated CPU usage: {cpu_usage:.1f}%")

        # Check memory usage
        memory_usage = resources["memory"]["usage_percent"]
        if memory_usage > self.memory_threshold_percent:
            issues.append(
                f"High memory usage: {memory_usage:.1f}% > {self.memory_threshold_percent}%"
            )
        elif memory_usage > self.memory_threshold_percent * 0.8:
            warnings.append(f"Elevated memory usage: {memory_usage:.1f}%")

        # Check disk usage
        disk_usage = resources["disk"]["usage_percent"]
        if disk_usage > self.disk_threshold_percent:
            issues.append(
                f"High disk usage: {disk_usage:.1f}% > {self.disk_threshold_percent}%"
            )
        elif disk_usage > self.disk_threshold_percent * 0.8:
            warnings.append(f"Elevated disk usage: {disk_usage:.1f}%")

        # Determine overall health
        if issues:
            status = "unhealthy"
            healthy = False
            message = f"Resource issues detected: {'; '.join(issues)}"
        elif warnings:
            status = "degraded"
            healthy = True
            message = f"Resource warnings: {'; '.join(warnings)}"
        else:
            status = "healthy"
            healthy = True
            message = "All resources within normal limits"

        return {
            "status": status,
            "healthy": healthy,
            "message": message,
            "resources": resources,
            "issues": issues,
            "warnings": warnings,
            "thresholds": {
                "cpu_percent": self.cpu_threshold_percent,
                "memory_percent": self.memory_threshold_percent,
                "disk_percent": self.disk_threshold_percent,
            },
        }

    def start_monitoring(self) -> None:
        """Start continuous resource monitoring."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(
            f"Started resource monitoring (interval: {self.check_interval}s)"
        )

    async def stop_monitoring(self) -> None:
        """Stop continuous resource monitoring."""
        if not self._is_monitoring:
            return

        self._is_monitoring = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        self.logger.info("Stopped resource monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._is_monitoring:
            try:
                health = self.check_resource_health()
                self._last_check = datetime.now()

                # Add to history
                self._resource_history.append(
                    {"timestamp": self._last_check, "health": health}
                )

                # Trim history
                if len(self._resource_history) > self._max_history_size:
                    self._resource_history = self._resource_history[
                        -self._max_history_size :
                    ]

                # Log warnings/issues
                if health["status"] == "unhealthy":
                    self.logger.warning(f"Resource health issue: {health['message']}")
                elif health["status"] == "degraded":
                    self.logger.info(f"Resource health warning: {health['message']}")

                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    def get_resource_history(self, minutes: int = 30) -> list:
        """
        Get resource history for the last N minutes.

        Args:
            minutes: Number of minutes of history to return

        Returns:
            List of resource snapshots
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        return [
            entry
            for entry in self._resource_history
            if entry["timestamp"] >= cutoff_time
        ]

    def is_monitoring(self) -> bool:
        """Check if monitoring is currently active."""
        return self._is_monitoring

    def get_monitoring_status(self) -> dict[str, Any]:
        """
        Get monitoring status information.

        Returns:
            Dictionary with monitoring status
        """
        return {
            "is_monitoring": self._is_monitoring,
            "check_interval_seconds": self.check_interval,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "history_size": len(self._resource_history),
            "thresholds": {
                "cpu_percent": self.cpu_threshold_percent,
                "memory_percent": self.memory_threshold_percent,
                "disk_percent": self.disk_threshold_percent,
            },
        }
