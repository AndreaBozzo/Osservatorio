"""
Security Monitoring Dashboard for Osservatorio ISTAT Data Platform

Real-time security monitoring and alerting system:
- Rate limiting metrics and violations
- Suspicious activity detection
- IP blocking management
- Performance monitoring
- Security alert system
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.auth.enhanced_rate_limiter import EnhancedRateLimiter
from src.auth.security_middleware import AuthenticationMiddleware
from src.database.sqlite.manager import SQLiteMetadataManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Security alert levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SecurityAlert:
    """Security alert data structure"""

    level: AlertLevel
    title: str
    description: str
    timestamp: datetime
    source: str
    details: dict[str, Any]


class SecurityMetrics(BaseModel):
    """Security metrics response model"""

    timestamp: datetime
    rate_limit_violations: dict[str, int]
    blocked_ips: int
    suspicious_activities: dict[str, int]
    response_times: dict[str, float]
    requests_per_hour: int
    active_api_keys: int
    threat_score: float


class SecurityDashboard:
    """Security monitoring dashboard"""

    def __init__(
        self,
        enhanced_limiter: EnhancedRateLimiter,
        auth_middleware: AuthenticationMiddleware,
        db_manager: SQLiteMetadataManager,
    ):
        """Initialize security dashboard

        Args:
            enhanced_limiter: Enhanced rate limiter instance
            auth_middleware: Authentication middleware
            db_manager: Database manager
        """
        self.enhanced_limiter = enhanced_limiter
        self.auth_middleware = auth_middleware
        self.db = db_manager
        self.logger = logger

        # Alert thresholds
        self.alert_thresholds = {
            "violations_per_hour": 100,
            "blocked_ips_threshold": 50,
            "avg_response_time_ms": 5000,
            "suspicious_activity_score": 0.7,
        }

        # Recent alerts cache
        self.recent_alerts: list[SecurityAlert] = []

        logger.info("Security Dashboard initialized")

    def get_real_time_metrics(self) -> SecurityMetrics:
        """Get real-time security metrics"""
        try:
            # Get metrics from enhanced rate limiter
            limiter_metrics = self.enhanced_limiter.get_security_metrics()

            # Calculate threat score
            threat_score = self._calculate_threat_score(limiter_metrics)

            # Get additional metrics
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Active API keys count
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM api_keys WHERE is_active = TRUE
                """
                )
                active_api_keys = cursor.fetchone()[0]

                # Requests in last hour
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM api_response_times
                    WHERE timestamp > datetime('now', '-1 hour')
                """
                )
                requests_per_hour = cursor.fetchone()[0]

            return SecurityMetrics(
                timestamp=datetime.utcnow(),
                rate_limit_violations=limiter_metrics.get(
                    "violations_by_threat_level", {}
                ),
                blocked_ips=limiter_metrics.get("blocked_ips_count", 0),
                suspicious_activities=self._get_suspicious_activity_stats(),
                response_times=limiter_metrics.get("avg_response_times", {}),
                requests_per_hour=requests_per_hour,
                active_api_keys=active_api_keys,
                threat_score=threat_score,
            )

        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

    def get_security_alerts(self, hours: int = 24) -> list[SecurityAlert]:
        """Get recent security alerts

        Args:
            hours: Number of hours to look back

        Returns:
            List of security alerts
        """
        try:
            alerts = []
            since = datetime.utcnow() - timedelta(hours=hours)

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Rate limit violations
                cursor.execute(
                    """
                    SELECT threat_level, COUNT(*), MIN(timestamp), MAX(timestamp)
                    FROM suspicious_activities
                    WHERE timestamp > ? AND activity_type = 'rate_limit_violation'
                    GROUP BY threat_level
                    HAVING COUNT(*) > 10
                """,
                    (since,),
                )

                for threat_level, count, first_time, last_time in cursor.fetchall():
                    level = (
                        AlertLevel.WARNING
                        if threat_level == "high"
                        else AlertLevel.INFO
                    )
                    if threat_level == "critical":
                        level = AlertLevel.CRITICAL

                    alerts.append(
                        SecurityAlert(
                            level=level,
                            title=f"High Rate Limit Violations ({threat_level})",
                            description=f"{count} rate limit violations detected",
                            timestamp=datetime.fromisoformat(last_time),
                            source="rate_limiter",
                            details={
                                "count": count,
                                "threat_level": threat_level,
                                "first_occurrence": first_time,
                                "last_occurrence": last_time,
                            },
                        )
                    )

                # New IP blocks
                cursor.execute(
                    """
                    SELECT COUNT(*), reason, threat_level, MAX(blocked_at)
                    FROM ip_blocks
                    WHERE blocked_at > ?
                    GROUP BY reason, threat_level
                """,
                    (since,),
                )

                for count, reason, threat_level, blocked_at in cursor.fetchall():
                    level = AlertLevel.WARNING
                    if threat_level == "critical":
                        level = AlertLevel.CRITICAL

                    alerts.append(
                        SecurityAlert(
                            level=level,
                            title="IP Addresses Blocked",
                            description=f"{count} IPs blocked for: {reason}",
                            timestamp=datetime.fromisoformat(blocked_at),
                            source="ip_blocker",
                            details={
                                "count": count,
                                "reason": reason,
                                "threat_level": threat_level,
                            },
                        )
                    )

            # Check for performance degradation
            avg_response_times = self.enhanced_limiter.get_security_metrics().get(
                "avg_response_times", {}
            )
            for endpoint, avg_time in avg_response_times.items():
                if avg_time > self.alert_thresholds["avg_response_time_ms"]:
                    alerts.append(
                        SecurityAlert(
                            level=AlertLevel.WARNING,
                            title=f"Performance Degradation: {endpoint}",
                            description=f"Average response time: {avg_time:.1f}ms",
                            timestamp=datetime.utcnow(),
                            source="performance_monitor",
                            details={
                                "endpoint": endpoint,
                                "avg_response_time": avg_time,
                                "threshold": self.alert_thresholds[
                                    "avg_response_time_ms"
                                ],
                            },
                        )
                    )

            # Sort alerts by timestamp (newest first)
            alerts.sort(key=lambda x: x.timestamp, reverse=True)

            return alerts

        except Exception as e:
            logger.error(f"Failed to get security alerts: {e}")
            return []

    def get_blocked_ips(self) -> list[dict[str, Any]]:
        """Get currently blocked IP addresses"""
        try:
            blocked_ips = []

            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT ip_hash, reason, threat_level, blocked_at, expires_at, notes
                    FROM ip_blocks
                    WHERE expires_at IS NULL OR expires_at > datetime('now')
                    ORDER BY blocked_at DESC
                """
                )

                for row in cursor.fetchall():
                    blocked_ips.append(
                        {
                            "ip_hash": row[0],
                            "reason": row[1],
                            "threat_level": row[2],
                            "blocked_at": row[3],
                            "expires_at": row[4],
                            "notes": row[5],
                            "is_permanent": row[4] is None,
                        }
                    )

            return blocked_ips

        except Exception as e:
            logger.error(f"Failed to get blocked IPs: {e}")
            return []

    def unblock_ip(self, ip_hash: str, reason: str = "Manual unblock") -> bool:
        """Unblock an IP address

        Args:
            ip_hash: Hashed IP address to unblock
            reason: Reason for unblocking

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE ip_blocks
                    SET expires_at = datetime('now'), notes = ?
                    WHERE ip_hash = ?
                """,
                    (f"Unblocked: {reason}", ip_hash),
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"IP unblocked: {ip_hash[:8]}*** - {reason}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to unblock IP: {e}")
            return False

    def get_rate_limit_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get rate limiting statistics

        Args:
            hours: Number of hours to analyze

        Returns:
            Rate limiting statistics
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            stats = {}

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Violations by endpoint
                cursor.execute(
                    """
                    SELECT JSON_EXTRACT(details, '$.endpoint') as endpoint, COUNT(*)
                    FROM suspicious_activities
                    WHERE timestamp > ? AND activity_type = 'rate_limit_violation'
                    GROUP BY endpoint
                    ORDER BY COUNT(*) DESC
                """,
                    (since,),
                )

                stats["violations_by_endpoint"] = dict(cursor.fetchall())

                # Violations by hour
                cursor.execute(
                    """
                    SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as hour, COUNT(*)
                    FROM suspicious_activities
                    WHERE timestamp > ? AND activity_type = 'rate_limit_violation'
                    GROUP BY hour
                    ORDER BY hour
                """,
                    (since,),
                )

                stats["violations_by_hour"] = dict(cursor.fetchall())

                # Top violating identifiers
                cursor.execute(
                    """
                    SELECT identifier, identifier_type, COUNT(*),
                           JSON_EXTRACT(details, '$.threat_level') as threat_level
                    FROM suspicious_activities
                    WHERE timestamp > ? AND activity_type = 'rate_limit_violation'
                    GROUP BY identifier, identifier_type
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """,
                    (since,),
                )

                stats["top_violators"] = [
                    {
                        "identifier": row[0][:8] + "***",  # Mask for privacy
                        "type": row[1],
                        "violations": row[2],
                        "threat_level": row[3],
                    }
                    for row in cursor.fetchall()
                ]

            return stats

        except Exception as e:
            logger.error(f"Failed to get rate limit stats: {e}")
            return {}

    def _calculate_threat_score(self, metrics: dict[str, Any]) -> float:
        """Calculate overall threat score based on metrics

        Args:
            metrics: Security metrics dictionary

        Returns:
            Threat score from 0.0 (safe) to 1.0 (critical)
        """
        try:
            threat_score = 0.0

            # Rate limit violations
            violations = metrics.get("violations_by_threat_level", {})
            critical_violations = violations.get("critical", 0)
            high_violations = violations.get("high", 0)

            threat_score += min(critical_violations * 0.1, 0.4)  # Max 0.4 for critical
            threat_score += min(high_violations * 0.05, 0.2)  # Max 0.2 for high

            # Blocked IPs
            blocked_count = metrics.get("blocked_ips_count", 0)
            if blocked_count > self.alert_thresholds["blocked_ips_threshold"]:
                threat_score += 0.2
            elif blocked_count > 10:
                threat_score += 0.1

            # Response times (performance impact)
            avg_times = metrics.get("avg_response_times", {})
            if avg_times:
                max_time = max(avg_times.values())
                if max_time > self.alert_thresholds["avg_response_time_ms"]:
                    threat_score += 0.2

            return min(threat_score, 1.0)

        except Exception as e:
            logger.error(f"Failed to calculate threat score: {e}")
            return 0.0

    def _get_suspicious_activity_stats(self) -> dict[str, int]:
        """Get suspicious activity statistics"""
        try:
            stats = {}
            since = datetime.utcnow() - timedelta(hours=24)

            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT activity_type, COUNT(*) FROM suspicious_activities
                    WHERE timestamp > ?
                    GROUP BY activity_type
                """,
                    (since,),
                )

                stats = dict(cursor.fetchall())

            return stats

        except Exception as e:
            logger.error(f"Failed to get suspicious activity stats: {e}")
            return {}

    def generate_dashboard_html(self) -> str:
        """Generate HTML dashboard for security monitoring"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Dashboard - Osservatorio ISTAT</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 2em; font-weight: bold; color: #333; }
                .metric-label { color: #666; font-size: 0.9em; margin-top: 5px; }
                .alert { padding: 15px; margin: 10px 0; border-radius: 4px; }
                .alert-critical { background: #fee; border-left: 4px solid #e74c3c; }
                .alert-warning { background: #fef9e7; border-left: 4px solid #f39c12; }
                .alert-info { background: #e8f4fd; border-left: 4px solid #3498db; }
                .threat-score { text-align: center; }
                .threat-low { color: #27ae60; }
                .threat-medium { color: #f39c12; }
                .threat-high { color: #e74c3c; }
                .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
                .refresh-btn:hover { background: #2980b9; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; }
            </style>
            <script>
                function refreshDashboard() {
                    window.location.reload();
                }

                function unblockIP(ipHash) {
                    if (confirm('Are you sure you want to unblock this IP?')) {
                        fetch('/api/security/unblock-ip', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ip_hash: ipHash, reason: 'Manual unblock from dashboard'})
                        }).then(() => refreshDashboard());
                    }
                }

                setInterval(refreshDashboard, 30000); // Auto-refresh every 30 seconds
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Security Dashboard</h1>
                    <p>Real-time security monitoring for Osservatorio ISTAT Data Platform</p>
                    <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
                </div>

                <div id="content">
                    <p>Loading security metrics...</p>
                </div>
            </div>

            <script>
                // Load dashboard content
                fetch('/api/security/metrics')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('content').innerHTML = generateDashboardContent(data);
                    });

                function generateDashboardContent(metrics) {
                    const threatClass = metrics.threat_score > 0.7 ? 'threat-high' :
                                      metrics.threat_score > 0.3 ? 'threat-medium' : 'threat-low';

                    return `
                        <div class="metrics-grid">
                            <div class="metric-card threat-score">
                                <div class="metric-value ${threatClass}">${(metrics.threat_score * 100).toFixed(1)}%</div>
                                <div class="metric-label">Threat Score</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${metrics.blocked_ips}</div>
                                <div class="metric-label">Blocked IPs</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${metrics.requests_per_hour}</div>
                                <div class="metric-label">Requests/Hour</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${metrics.active_api_keys}</div>
                                <div class="metric-label">Active API Keys</div>
                            </div>
                        </div>
                    `;
                }
            </script>
        </body>
        </html>
        """
        return html_template


# FastAPI router for security dashboard endpoints
def create_security_router(
    enhanced_limiter: EnhancedRateLimiter,
    auth_middleware: AuthenticationMiddleware,
    db_manager: SQLiteMetadataManager,
) -> APIRouter:
    """Create FastAPI router for security dashboard endpoints"""

    router = APIRouter(prefix="/api/security", tags=["security"])
    dashboard = SecurityDashboard(enhanced_limiter, auth_middleware, db_manager)

    @router.get("/metrics", response_model=SecurityMetrics)
    async def get_security_metrics():
        """Get real-time security metrics"""
        return dashboard.get_real_time_metrics()

    @router.get("/alerts")
    async def get_security_alerts(hours: int = Query(24, ge=1, le=168)):
        """Get security alerts for the specified time period"""
        alerts = dashboard.get_security_alerts(hours)
        return [asdict(alert) for alert in alerts]

    @router.get("/blocked-ips")
    async def get_blocked_ips():
        """Get currently blocked IP addresses"""
        return dashboard.get_blocked_ips()

    @router.post("/unblock-ip")
    async def unblock_ip(request: dict[str, str]):
        """Unblock an IP address"""
        ip_hash = request.get("ip_hash")
        reason = request.get("reason", "Manual unblock")

        if not ip_hash:
            raise HTTPException(status_code=400, detail="IP hash is required")

        success = dashboard.unblock_ip(ip_hash, reason)
        if success:
            return {"message": "IP unblocked successfully"}
        else:
            raise HTTPException(
                status_code=404, detail="IP not found or already unblocked"
            )

    @router.get("/rate-limit-stats")
    async def get_rate_limit_stats(hours: int = Query(24, ge=1, le=168)):
        """Get rate limiting statistics"""
        return dashboard.get_rate_limit_stats(hours)

    @router.get("/dashboard", response_class=HTMLResponse)
    async def get_dashboard_html():
        """Get HTML security dashboard"""
        return dashboard.generate_dashboard_html()

    return router
