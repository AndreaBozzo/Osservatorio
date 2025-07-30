"""
Resource Utilization Monitoring System.

This module provides comprehensive system resource monitoring during load testing:
- CPU usage tracking
- Memory utilization monitoring
- Disk I/O performance
- Network traffic analysis
- Database connection monitoring
- Resource bottleneck detection
"""

import json
import sqlite3
import statistics
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class ResourceSnapshot:
    """System resource usage snapshot."""

    timestamp: datetime

    # CPU metrics
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: float
    cpu_freq_max: float

    # Memory metrics
    memory_total_gb: float
    memory_available_gb: float
    memory_used_gb: float
    memory_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_percent: float

    # Disk metrics
    disk_usage_percent: float
    disk_read_bytes_per_sec: float
    disk_write_bytes_per_sec: float
    disk_read_iops: float
    disk_write_iops: float

    # Network metrics
    network_bytes_sent_per_sec: float
    network_bytes_recv_per_sec: float
    network_packets_sent_per_sec: float
    network_packets_recv_per_sec: float
    active_connections: int

    # Process-specific metrics
    process_cpu_percent: float
    process_memory_mb: float
    process_memory_percent: float
    process_num_threads: int
    process_num_fds: int  # File descriptors

    # Optional CPU load metrics (Unix-like systems only)
    load_avg_1min: Optional[float] = None
    load_avg_5min: Optional[float] = None
    load_avg_15min: Optional[float] = None


@dataclass
class ResourceAlert:
    """Resource usage alert."""

    alert_type: str
    severity: str  # "warning", "critical"
    resource: str
    threshold: float
    current_value: float
    timestamp: datetime
    description: str
    duration_seconds: float = 0


@dataclass
class ResourceAnalysis:
    """Resource usage analysis result."""

    monitoring_duration_seconds: float
    total_snapshots: int
    snapshot_interval_seconds: float

    # CPU analysis
    avg_cpu_percent: float
    max_cpu_percent: float
    cpu_utilization_distribution: Dict[
        str, float
    ]  # e.g., {"0-25%": 0.3, "25-50%": 0.4, ...}

    # Memory analysis
    avg_memory_percent: float
    max_memory_percent: float
    memory_trend: str  # "stable", "increasing", "decreasing"

    # Disk analysis
    avg_disk_usage_percent: float
    max_disk_read_mbps: float
    max_disk_write_mbps: float

    # Network analysis
    avg_network_mbps: float
    max_network_mbps: float

    # Process analysis
    avg_process_cpu: float
    avg_process_memory_mb: float
    max_process_memory_mb: float

    # Alerts and issues
    alerts: List[ResourceAlert] = field(default_factory=list)
    bottlenecks_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ResourceMonitor:
    """System resource monitoring and analysis."""

    def __init__(self, process_name: Optional[str] = None):
        """Initialize resource monitor."""
        self.process_name = process_name
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.snapshots: List[ResourceSnapshot] = []
        self.alerts: List[ResourceAlert] = []

        # Get process to monitor
        if process_name:
            self.target_process = self._find_process_by_name(process_name)
        else:
            self.target_process = psutil.Process()

        # Previous values for calculating rates
        self._prev_disk_io = None
        self._prev_network_io = None
        self._prev_timestamp = None

        # Alert thresholds
        self.thresholds = {
            "cpu_warning": 70.0,  # 70% CPU
            "cpu_critical": 90.0,  # 90% CPU
            "memory_warning": 80.0,  # 80% Memory
            "memory_critical": 95.0,  # 95% Memory
            "disk_warning": 85.0,  # 85% Disk
            "disk_critical": 95.0,  # 95% Disk
            "disk_io_warning": 100.0,  # 100 MB/s
            "disk_io_critical": 500.0,  # 500 MB/s
            "network_warning": 100.0,  # 100 MB/s
            "network_critical": 500.0,  # 500 MB/s
            "connections_warning": 500,  # 500 connections
            "connections_critical": 1000,  # 1000 connections
        }

    def _find_process_by_name(self, name: str) -> Optional[psutil.Process]:
        """Find process by name."""
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if name.lower() in proc.info["name"].lower():
                    return psutil.Process(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start resource monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.snapshots.clear()
        self.alerts.clear()

        def monitor():
            while self.monitoring_active:
                try:
                    snapshot = self._take_snapshot()
                    self.snapshots.append(snapshot)

                    # Check for alerts
                    alerts = self._check_alerts(snapshot)
                    self.alerts.extend(alerts)

                    time.sleep(interval_seconds)

                except Exception as e:
                    print(f"Resource monitoring error: {e}")
                    time.sleep(interval_seconds)

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a system resource snapshot."""
        current_time = datetime.now()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else 0
        cpu_freq_max = cpu_freq.max if cpu_freq else 0

        # Load averages (Unix-like systems only)
        load_avg = None
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            pass  # Windows doesn't have load averages

        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk metrics
        disk_usage = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()

        # Calculate disk I/O rates
        disk_read_rate = 0
        disk_write_rate = 0
        disk_read_iops = 0
        disk_write_iops = 0

        if self._prev_disk_io and self._prev_timestamp:
            time_delta = (current_time - self._prev_timestamp).total_seconds()
            if time_delta > 0:
                disk_read_rate = (
                    disk_io.read_bytes - self._prev_disk_io.read_bytes
                ) / time_delta
                disk_write_rate = (
                    disk_io.write_bytes - self._prev_disk_io.write_bytes
                ) / time_delta
                disk_read_iops = (
                    disk_io.read_count - self._prev_disk_io.read_count
                ) / time_delta
                disk_write_iops = (
                    disk_io.write_count - self._prev_disk_io.write_count
                ) / time_delta

        # Network metrics
        network_io = psutil.net_io_counters()
        network_connections = len(psutil.net_connections())

        # Calculate network rates
        network_sent_rate = 0
        network_recv_rate = 0
        network_sent_packets_rate = 0
        network_recv_packets_rate = 0

        if self._prev_network_io and self._prev_timestamp:
            time_delta = (current_time - self._prev_timestamp).total_seconds()
            if time_delta > 0:
                network_sent_rate = (
                    network_io.bytes_sent - self._prev_network_io.bytes_sent
                ) / time_delta
                network_recv_rate = (
                    network_io.bytes_recv - self._prev_network_io.bytes_recv
                ) / time_delta
                network_sent_packets_rate = (
                    network_io.packets_sent - self._prev_network_io.packets_sent
                ) / time_delta
                network_recv_packets_rate = (
                    network_io.packets_recv - self._prev_network_io.packets_recv
                ) / time_delta

        # Process-specific metrics
        process_cpu = 0
        process_memory_mb = 0
        process_memory_percent = 0
        process_threads = 0
        process_fds = 0

        if self.target_process:
            try:
                process_cpu = self.target_process.cpu_percent()
                memory_info = self.target_process.memory_info()
                process_memory_mb = memory_info.rss / 1024 / 1024  # MB
                process_memory_percent = self.target_process.memory_percent()
                process_threads = self.target_process.num_threads()
                try:
                    process_fds = self.target_process.num_fds()
                except AttributeError:
                    # Windows doesn't have num_fds
                    process_fds = len(self.target_process.open_files())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Create snapshot
        snapshot = ResourceSnapshot(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq_current=cpu_freq_current,
            cpu_freq_max=cpu_freq_max,
            load_avg_1min=load_avg[0] if load_avg else None,
            load_avg_5min=load_avg[1] if load_avg else None,
            load_avg_15min=load_avg[2] if load_avg else None,
            memory_total_gb=memory.total / 1024**3,
            memory_available_gb=memory.available / 1024**3,
            memory_used_gb=memory.used / 1024**3,
            memory_percent=memory.percent,
            swap_total_gb=swap.total / 1024**3,
            swap_used_gb=swap.used / 1024**3,
            swap_percent=swap.percent,
            disk_usage_percent=disk_usage.percent,
            disk_read_bytes_per_sec=disk_read_rate,
            disk_write_bytes_per_sec=disk_write_rate,
            disk_read_iops=disk_read_iops,
            disk_write_iops=disk_write_iops,
            network_bytes_sent_per_sec=network_sent_rate,
            network_bytes_recv_per_sec=network_recv_rate,
            network_packets_sent_per_sec=network_sent_packets_rate,
            network_packets_recv_per_sec=network_recv_packets_rate,
            active_connections=network_connections,
            process_cpu_percent=process_cpu,
            process_memory_mb=process_memory_mb,
            process_memory_percent=process_memory_percent,
            process_num_threads=process_threads,
            process_num_fds=process_fds,
        )

        # Update previous values
        self._prev_disk_io = disk_io
        self._prev_network_io = network_io
        self._prev_timestamp = current_time

        return snapshot

    def _check_alerts(self, snapshot: ResourceSnapshot) -> List[ResourceAlert]:
        """Check for resource usage alerts."""
        alerts = []
        current_time = snapshot.timestamp

        # CPU alerts
        if snapshot.cpu_percent >= self.thresholds["cpu_critical"]:
            alerts.append(
                ResourceAlert(
                    alert_type="cpu",
                    severity="critical",
                    resource="cpu",
                    threshold=self.thresholds["cpu_critical"],
                    current_value=snapshot.cpu_percent,
                    timestamp=current_time,
                    description=f"Critical CPU usage: {snapshot.cpu_percent:.1f}%",
                )
            )
        elif snapshot.cpu_percent >= self.thresholds["cpu_warning"]:
            alerts.append(
                ResourceAlert(
                    alert_type="cpu",
                    severity="warning",
                    resource="cpu",
                    threshold=self.thresholds["cpu_warning"],
                    current_value=snapshot.cpu_percent,
                    timestamp=current_time,
                    description=f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                )
            )

        # Memory alerts
        if snapshot.memory_percent >= self.thresholds["memory_critical"]:
            alerts.append(
                ResourceAlert(
                    alert_type="memory",
                    severity="critical",
                    resource="memory",
                    threshold=self.thresholds["memory_critical"],
                    current_value=snapshot.memory_percent,
                    timestamp=current_time,
                    description=f"Critical memory usage: {snapshot.memory_percent:.1f}%",
                )
            )
        elif snapshot.memory_percent >= self.thresholds["memory_warning"]:
            alerts.append(
                ResourceAlert(
                    alert_type="memory",
                    severity="warning",
                    resource="memory",
                    threshold=self.thresholds["memory_warning"],
                    current_value=snapshot.memory_percent,
                    timestamp=current_time,
                    description=f"High memory usage: {snapshot.memory_percent:.1f}%",
                )
            )

        # Disk alerts
        if snapshot.disk_usage_percent >= self.thresholds["disk_critical"]:
            alerts.append(
                ResourceAlert(
                    alert_type="disk_space",
                    severity="critical",
                    resource="disk",
                    threshold=self.thresholds["disk_critical"],
                    current_value=snapshot.disk_usage_percent,
                    timestamp=current_time,
                    description=f"Critical disk usage: {snapshot.disk_usage_percent:.1f}%",
                )
            )
        elif snapshot.disk_usage_percent >= self.thresholds["disk_warning"]:
            alerts.append(
                ResourceAlert(
                    alert_type="disk_space",
                    severity="warning",
                    resource="disk",
                    threshold=self.thresholds["disk_warning"],
                    current_value=snapshot.disk_usage_percent,
                    timestamp=current_time,
                    description=f"High disk usage: {snapshot.disk_usage_percent:.1f}%",
                )
            )

        # Disk I/O alerts
        total_disk_io_mbps = (
            snapshot.disk_read_bytes_per_sec + snapshot.disk_write_bytes_per_sec
        ) / 1024**2
        if total_disk_io_mbps >= self.thresholds["disk_io_critical"]:
            alerts.append(
                ResourceAlert(
                    alert_type="disk_io",
                    severity="critical",
                    resource="disk_io",
                    threshold=self.thresholds["disk_io_critical"],
                    current_value=total_disk_io_mbps,
                    timestamp=current_time,
                    description=f"Critical disk I/O: {total_disk_io_mbps:.1f} MB/s",
                )
            )
        elif total_disk_io_mbps >= self.thresholds["disk_io_warning"]:
            alerts.append(
                ResourceAlert(
                    alert_type="disk_io",
                    severity="warning",
                    resource="disk_io",
                    threshold=self.thresholds["disk_io_warning"],
                    current_value=total_disk_io_mbps,
                    timestamp=current_time,
                    description=f"High disk I/O: {total_disk_io_mbps:.1f} MB/s",
                )
            )

        # Network alerts
        total_network_mbps = (
            snapshot.network_bytes_sent_per_sec + snapshot.network_bytes_recv_per_sec
        ) / 1024**2
        if total_network_mbps >= self.thresholds["network_critical"]:
            alerts.append(
                ResourceAlert(
                    alert_type="network",
                    severity="critical",
                    resource="network",
                    threshold=self.thresholds["network_critical"],
                    current_value=total_network_mbps,
                    timestamp=current_time,
                    description=f"Critical network usage: {total_network_mbps:.1f} MB/s",
                )
            )
        elif total_network_mbps >= self.thresholds["network_warning"]:
            alerts.append(
                ResourceAlert(
                    alert_type="network",
                    severity="warning",
                    resource="network",
                    threshold=self.thresholds["network_warning"],
                    current_value=total_network_mbps,
                    timestamp=current_time,
                    description=f"High network usage: {total_network_mbps:.1f} MB/s",
                )
            )

        # Connection alerts
        if snapshot.active_connections >= self.thresholds["connections_critical"]:
            alerts.append(
                ResourceAlert(
                    alert_type="connections",
                    severity="critical",
                    resource="connections",
                    threshold=self.thresholds["connections_critical"],
                    current_value=snapshot.active_connections,
                    timestamp=current_time,
                    description=f"Critical connection count: {snapshot.active_connections}",
                )
            )
        elif snapshot.active_connections >= self.thresholds["connections_warning"]:
            alerts.append(
                ResourceAlert(
                    alert_type="connections",
                    severity="warning",
                    resource="connections",
                    threshold=self.thresholds["connections_warning"],
                    current_value=snapshot.active_connections,
                    timestamp=current_time,
                    description=f"High connection count: {snapshot.active_connections}",
                )
            )

        return alerts

    def analyze_resource_usage(self) -> ResourceAnalysis:
        """Analyze collected resource usage data."""
        if not self.snapshots:
            raise ValueError("No resource snapshots available for analysis")

        # Basic metrics
        duration = (
            self.snapshots[-1].timestamp - self.snapshots[0].timestamp
        ).total_seconds()
        total_snapshots = len(self.snapshots)
        interval = duration / max(total_snapshots - 1, 1)

        # CPU analysis
        cpu_values = [s.cpu_percent for s in self.snapshots]
        avg_cpu = statistics.mean(cpu_values)
        max_cpu = max(cpu_values)

        # CPU utilization distribution
        cpu_dist = {"0-25%": 0, "25-50%": 0, "50-75%": 0, "75-100%": 0}
        for cpu in cpu_values:
            if cpu < 25:
                cpu_dist["0-25%"] += 1
            elif cpu < 50:
                cpu_dist["25-50%"] += 1
            elif cpu < 75:
                cpu_dist["50-75%"] += 1
            else:
                cpu_dist["75-100%"] += 1

        # Convert to percentages
        for key in cpu_dist:
            cpu_dist[key] = cpu_dist[key] / total_snapshots

        # Memory analysis
        memory_values = [s.memory_percent for s in self.snapshots]
        avg_memory = statistics.mean(memory_values)
        max_memory = max(memory_values)

        # Memory trend analysis
        memory_trend = "stable"
        if len(memory_values) > 10:
            first_half = memory_values[: len(memory_values) // 2]
            second_half = memory_values[len(memory_values) // 2 :]

            avg_first = statistics.mean(first_half)
            avg_second = statistics.mean(second_half)

            change_percent = ((avg_second - avg_first) / avg_first) * 100

            if change_percent > 5:
                memory_trend = "increasing"
            elif change_percent < -5:
                memory_trend = "decreasing"

        # Disk analysis
        disk_values = [s.disk_usage_percent for s in self.snapshots]
        avg_disk = statistics.mean(disk_values)

        disk_read_mbps = [s.disk_read_bytes_per_sec / 1024**2 for s in self.snapshots]
        disk_write_mbps = [
            s.disk_write_bytes_per_sec / 1024**2 for s in self.snapshots
        ]
        max_disk_read = max(disk_read_mbps) if disk_read_mbps else 0
        max_disk_write = max(disk_write_mbps) if disk_write_mbps else 0

        # Network analysis
        network_mbps = [
            (s.network_bytes_sent_per_sec + s.network_bytes_recv_per_sec) / 1024**2
            for s in self.snapshots
        ]
        avg_network = statistics.mean(network_mbps) if network_mbps else 0
        max_network = max(network_mbps) if network_mbps else 0

        # Process analysis
        process_cpu_values = [s.process_cpu_percent for s in self.snapshots]
        process_memory_values = [s.process_memory_mb for s in self.snapshots]

        avg_process_cpu = (
            statistics.mean(process_cpu_values) if process_cpu_values else 0
        )
        avg_process_memory = (
            statistics.mean(process_memory_values) if process_memory_values else 0
        )
        max_process_memory = max(process_memory_values) if process_memory_values else 0

        # Detect bottlenecks
        bottlenecks = []
        if max_cpu > 80:
            bottlenecks.append("CPU bottleneck detected")
        if max_memory > 85:
            bottlenecks.append("Memory bottleneck detected")
        if max_disk_read > 100 or max_disk_write > 100:
            bottlenecks.append("Disk I/O bottleneck detected")
        if max_network > 100:
            bottlenecks.append("Network bottleneck detected")

        # Generate recommendations
        recommendations = []
        if avg_cpu > 70:
            recommendations.append("Consider CPU optimization or scaling up")
        if avg_memory > 75:
            recommendations.append("Consider memory optimization or adding more RAM")
        if max_disk_read > 50 or max_disk_write > 50:
            recommendations.append("Consider disk optimization or using faster storage")
        if avg_network > 50:
            recommendations.append(
                "Consider network optimization or bandwidth increase"
            )
        if len([a for a in self.alerts if a.severity == "critical"]) > 0:
            recommendations.append("Address critical resource alerts immediately")

        return ResourceAnalysis(
            monitoring_duration_seconds=duration,
            total_snapshots=total_snapshots,
            snapshot_interval_seconds=interval,
            avg_cpu_percent=avg_cpu,
            max_cpu_percent=max_cpu,
            cpu_utilization_distribution=cpu_dist,
            avg_memory_percent=avg_memory,
            max_memory_percent=max_memory,
            memory_trend=memory_trend,
            avg_disk_usage_percent=avg_disk,
            max_disk_read_mbps=max_disk_read,
            max_disk_write_mbps=max_disk_write,
            avg_network_mbps=avg_network,
            max_network_mbps=max_network,
            avg_process_cpu=avg_process_cpu,
            avg_process_memory_mb=avg_process_memory,
            max_process_memory_mb=max_process_memory,
            alerts=self.alerts,
            bottlenecks_detected=bottlenecks,
            recommendations=recommendations,
        )

    def generate_resource_report(
        self, output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive resource utilization report."""
        analysis = self.analyze_resource_usage()

        # Organize alerts by severity
        alerts_by_severity = {}
        for alert in analysis.alerts:
            severity = alert.severity
            if severity not in alerts_by_severity:
                alerts_by_severity[severity] = []
            alerts_by_severity[severity].append(
                {
                    "type": alert.alert_type,
                    "resource": alert.resource,
                    "value": alert.current_value,
                    "threshold": alert.threshold,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                }
            )

        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_summary": {
                "duration_seconds": analysis.monitoring_duration_seconds,
                "total_snapshots": analysis.total_snapshots,
                "snapshot_interval_seconds": analysis.snapshot_interval_seconds,
            },
            "cpu_analysis": {
                "average_percent": analysis.avg_cpu_percent,
                "maximum_percent": analysis.max_cpu_percent,
                "utilization_distribution": analysis.cpu_utilization_distribution,
            },
            "memory_analysis": {
                "average_percent": analysis.avg_memory_percent,
                "maximum_percent": analysis.max_memory_percent,
                "trend": analysis.memory_trend,
            },
            "disk_analysis": {
                "average_usage_percent": analysis.avg_disk_usage_percent,
                "max_read_mbps": analysis.max_disk_read_mbps,
                "max_write_mbps": analysis.max_disk_write_mbps,
            },
            "network_analysis": {
                "average_mbps": analysis.avg_network_mbps,
                "maximum_mbps": analysis.max_network_mbps,
            },
            "process_analysis": {
                "average_cpu_percent": analysis.avg_process_cpu,
                "average_memory_mb": analysis.avg_process_memory_mb,
                "maximum_memory_mb": analysis.max_process_memory_mb,
            },
            "alerts": {
                "total_alerts": len(analysis.alerts),
                "by_severity": alerts_by_severity,
            },
            "bottlenecks": analysis.bottlenecks_detected,
            "recommendations": analysis.recommendations,
            "health_status": self._calculate_resource_health(analysis),
        }

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def _calculate_resource_health(self, analysis: ResourceAnalysis) -> str:
        """Calculate overall resource health status."""
        critical_alerts = len([a for a in analysis.alerts if a.severity == "critical"])
        warning_alerts = len([a for a in analysis.alerts if a.severity == "warning"])

        if critical_alerts > 0:
            return "critical"
        elif len(analysis.bottlenecks_detected) > 2:
            return "degraded"
        elif warning_alerts > 5:
            return "warning"
        elif analysis.max_cpu_percent > 80 or analysis.max_memory_percent > 80:
            return "stressed"
        else:
            return "healthy"

    def clear_data(self):
        """Clear all monitoring data."""
        self.snapshots.clear()
        self.alerts.clear()
        self._prev_disk_io = None
        self._prev_network_io = None
        self._prev_timestamp = None
