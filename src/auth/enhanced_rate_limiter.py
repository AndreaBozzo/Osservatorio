"""
Enhanced Rate Limiting System for Osservatorio ISTAT Data Platform

Advanced rate limiting features:
- Distributed rate limiting with Redis support
- Adaptive rate limiting based on API response times
- IP-based suspicious activity detection and blocking
- Comprehensive security monitoring and logging
- DoS protection and credential stuffing prevention
"""

import hashlib
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from src.database.sqlite.manager import SQLiteMetadataManager
from src.utils.logger import get_logger

from .models import APIKey
from .rate_limiter import RateLimitConfig, RateLimitResult

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = get_logger(__name__)


class ThreatLevel(Enum):
    """Security threat levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SuspiciousActivity:
    """Suspicious activity record"""

    identifier: str
    identifier_type: str
    threat_level: ThreatLevel
    activity_type: str
    details: Dict[str, Any]
    timestamp: datetime
    block_until: Optional[datetime] = None


@dataclass
class AdaptiveConfig:
    """Adaptive rate limiting configuration"""

    enable_adaptive: bool = True
    response_time_threshold_ms: float = 2000.0
    adjustment_factor: float = 0.8
    min_adjustment_ratio: float = 0.1
    max_adjustment_ratio: float = 2.0
    window_size: int = 100  # Number of requests to analyze


class EnhancedRateLimiter:
    """Enhanced rate limiter with distributed support and advanced security features"""

    def __init__(
        self,
        sqlite_manager: SQLiteMetadataManager,
        redis_url: Optional[str] = None,
        adaptive_config: Optional[AdaptiveConfig] = None,
    ):
        """Initialize enhanced rate limiter

        Args:
            sqlite_manager: SQLite database manager
            redis_url: Redis connection URL for distributed limiting
            adaptive_config: Adaptive rate limiting configuration
        """
        self.db = sqlite_manager
        self.adaptive_config = adaptive_config or AdaptiveConfig()
        self.logger = logger

        # Redis setup for distributed rate limiting
        self.redis_client = None
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis connected for distributed rate limiting")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to SQLite: {e}")
                self.redis_client = None

        # In-memory caches for performance
        self.response_time_cache = {}
        self.suspicious_ips = {}
        self.blocked_ips = {}

        # Ensure enhanced schema exists
        self._ensure_enhanced_schema()

        logger.info("Enhanced Rate Limiter initialized")

    def _ensure_enhanced_schema(self):
        """Ensure enhanced rate limiting tables exist"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Enhanced rate limits with adaptive features
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS enhanced_rate_limits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        identifier TEXT NOT NULL,
                        identifier_type TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        window_type TEXT NOT NULL,
                        request_count INTEGER DEFAULT 0,
                        adapted_limit INTEGER,
                        original_limit INTEGER,
                        avg_response_time REAL,
                        window_start TIMESTAMP NOT NULL,
                        window_end TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(identifier, identifier_type, endpoint, window_type, window_start)
                    )
                """
                )

                # Suspicious activity tracking
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS suspicious_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        identifier TEXT NOT NULL,
                        identifier_type TEXT NOT NULL,
                        threat_level TEXT NOT NULL,
                        activity_type TEXT NOT NULL,
                        details TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        block_until TIMESTAMP,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolution_notes TEXT
                    )
                """
                )

                # API response time tracking
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS api_response_times (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        identifier TEXT NOT NULL,
                        identifier_type TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        response_time_ms REAL NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status_code INTEGER,
                        request_size INTEGER,
                        response_size INTEGER
                    )
                """
                )

                # IP blocking records
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ip_blocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ip_hash TEXT UNIQUE NOT NULL,
                        reason TEXT NOT NULL,
                        threat_level TEXT NOT NULL,
                        blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        auto_generated BOOLEAN DEFAULT TRUE,
                        notes TEXT
                    )
                """
                )

                # Create performance indexes
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_enhanced_rate_limits_lookup
                    ON enhanced_rate_limits(identifier, identifier_type, endpoint, window_type)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_suspicious_activities_identifier
                    ON suspicious_activities(identifier, identifier_type, timestamp)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_api_response_times_endpoint
                    ON api_response_times(endpoint, timestamp)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ip_blocks_hash
                    ON ip_blocks(ip_hash, expires_at)
                """
                )

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to ensure enhanced rate limit schema: {e}")
            raise

    def check_enhanced_rate_limit(
        self,
        api_key: Optional[APIKey] = None,
        ip_address: Optional[str] = None,
        endpoint: str = "default",
        user_agent: Optional[str] = None,
        request_data: Optional[Dict] = None,
    ) -> RateLimitResult:
        """Enhanced rate limit check with security analysis

        Args:
            api_key: API key for authenticated requests
            ip_address: Client IP address
            endpoint: API endpoint being accessed
            user_agent: Client user agent
            request_data: Additional request metadata

        Returns:
            RateLimitResult with enhanced security analysis
        """
        try:
            # Check for IP blocks first
            if ip_address and self._is_ip_blocked(ip_address):
                return RateLimitResult(
                    allowed=False,
                    limit=0,
                    remaining=0,
                    reset_time=datetime.utcnow() + timedelta(hours=24),
                    retry_after=86400,  # 24 hours
                )

            # Analyze for suspicious activity
            suspicious_score = self._analyze_suspicious_activity(
                api_key, ip_address, endpoint, user_agent, request_data
            )

            # Get adaptive rate limit configuration
            config = self._get_adaptive_rate_limit_config(
                api_key, endpoint, suspicious_score
            )

            # Use distributed rate limiting if Redis is available
            if self.redis_client:
                result = self._check_distributed_rate_limit(
                    api_key, ip_address, endpoint, config
                )
            else:
                result = self._check_local_rate_limit(
                    api_key, ip_address, endpoint, config
                )

            # Log rate limit violation if blocked
            if not result.allowed:
                self._log_enhanced_violation(
                    api_key, ip_address, endpoint, result, suspicious_score, user_agent
                )

            return result

        except Exception as e:
            logger.error(f"Enhanced rate limit check failed: {e}")
            # Fail open but log the error
            return RateLimitResult(True, 1000, 1000, datetime.utcnow())

    def record_response_time(
        self,
        identifier: str,
        identifier_type: str,
        endpoint: str,
        response_time_ms: float,
        status_code: int = 200,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
    ):
        """Record API response time for adaptive rate limiting

        Args:
            identifier: API key ID or IP hash
            identifier_type: 'api_key' or 'ip'
            endpoint: API endpoint
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            request_size: Request size in bytes
            response_size: Response size in bytes
        """
        try:
            # Store in cache for quick access
            cache_key = f"{identifier}:{endpoint}"
            if cache_key not in self.response_time_cache:
                self.response_time_cache[cache_key] = []

            self.response_time_cache[cache_key].append(response_time_ms)

            # Keep only recent measurements
            if (
                len(self.response_time_cache[cache_key])
                > self.adaptive_config.window_size
            ):
                self.response_time_cache[cache_key] = self.response_time_cache[
                    cache_key
                ][-self.adaptive_config.window_size :]

            # Store in database for long-term analysis
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO api_response_times
                    (identifier, identifier_type, endpoint, response_time_ms,
                     status_code, request_size, response_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        identifier,
                        identifier_type,
                        endpoint,
                        response_time_ms,
                        status_code,
                        request_size,
                        response_size,
                    ),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Failed to record response time: {e}")

    def block_ip(
        self,
        ip_address: str,
        reason: str,
        threat_level: ThreatLevel = ThreatLevel.HIGH,
        duration_hours: Optional[int] = 24,
        notes: Optional[str] = None,
    ):
        """Block an IP address for security reasons

        Args:
            ip_address: IP address to block
            reason: Reason for blocking
            threat_level: Threat level assessment
            duration_hours: Block duration in hours (None for permanent)
            notes: Additional notes
        """
        try:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
            expires_at = None
            if duration_hours:
                expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO ip_blocks
                    (ip_hash, reason, threat_level, expires_at, notes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (ip_hash, reason, threat_level.value, expires_at, notes),
                )
                conn.commit()

            # Update in-memory cache
            self.blocked_ips[ip_hash] = {
                "reason": reason,
                "expires_at": expires_at,
                "threat_level": threat_level,
            }

            logger.warning(f"IP blocked: {ip_address[:8]}*** for {reason}")

        except Exception as e:
            logger.error(f"Failed to block IP: {e}")

    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        try:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]

            # Check in-memory cache first
            if ip_hash in self.blocked_ips:
                block_info = self.blocked_ips[ip_hash]
                if (
                    block_info["expires_at"]
                    and block_info["expires_at"] < datetime.utcnow()
                ):
                    del self.blocked_ips[ip_hash]
                    return False
                return True

            # Check database
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT expires_at FROM ip_blocks
                    WHERE ip_hash = ? AND (expires_at IS NULL OR expires_at > ?)
                """,
                    (ip_hash, datetime.utcnow()),
                )

                result = cursor.fetchone()
                if result:
                    # Update cache
                    self.blocked_ips[ip_hash] = {
                        "expires_at": result[0],
                        "reason": "Cached from DB",
                    }
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check IP block status: {e}")
            return False

    def _analyze_suspicious_activity(
        self,
        api_key: Optional[APIKey],
        ip_address: Optional[str],
        endpoint: str,
        user_agent: Optional[str],
        request_data: Optional[Dict],
    ) -> float:
        """Analyze request for suspicious activity patterns

        Returns:
            Suspicion score (0.0 = not suspicious, 1.0 = highly suspicious)
        """
        try:
            suspicion_score = 0.0

            # Check for rapid requests from same IP
            if ip_address:
                ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
                recent_requests = self._get_recent_requests(ip_hash, "ip", minutes=1)
                if recent_requests > 100:  # Very high request rate
                    suspicion_score += 0.4
                elif recent_requests > 50:
                    suspicion_score += 0.2

            # Check for suspicious user agents
            if user_agent:
                suspicious_agents = [
                    "bot",
                    "crawler",
                    "scraper",
                    "python",
                    "curl",
                    "wget",
                    "automated",
                    "script",
                    "spider",
                ]
                if any(agent in user_agent.lower() for agent in suspicious_agents):
                    suspicion_score += 0.1

            # Check for unusual endpoint access patterns
            if endpoint:
                # Multiple different endpoints accessed rapidly
                identifier = str(api_key.id) if api_key else ip_address
                if identifier:
                    unique_endpoints = self._get_recent_unique_endpoints(
                        identifier, minutes=5
                    )
                    if unique_endpoints > 10:
                        suspicion_score += 0.2

            # Check for failed authentication attempts
            if not api_key and ip_address:
                failed_auths = self._get_recent_failed_auths(ip_address, minutes=10)
                if failed_auths > 5:
                    suspicion_score += 0.3

            return min(suspicion_score, 1.0)

        except Exception as e:
            logger.error(f"Failed to analyze suspicious activity: {e}")
            return 0.0

    def _get_adaptive_rate_limit_config(
        self, api_key: Optional[APIKey], endpoint: str, suspicious_score: float
    ) -> RateLimitConfig:
        """Get adaptive rate limit configuration based on performance and security"""
        # Start with base configuration
        from .rate_limiter import SQLiteRateLimiter

        base_limiter = SQLiteRateLimiter(self.db)
        config = base_limiter._get_rate_limit_config(api_key)

        if not self.adaptive_config.enable_adaptive:
            return config

        try:
            # Get average response time for this endpoint
            avg_response_time = self._get_average_response_time(endpoint)

            # Calculate adjustment factor based on performance
            adjustment_factor = 1.0
            if avg_response_time > self.adaptive_config.response_time_threshold_ms:
                # Slow responses -> reduce rate limits
                adjustment_factor = self.adaptive_config.adjustment_factor

            # Apply security-based adjustments
            if suspicious_score > 0.5:
                adjustment_factor *= 0.5  # Significantly reduce for suspicious activity
            elif suspicious_score > 0.3:
                adjustment_factor *= 0.7  # Moderately reduce

            # Ensure adjustment is within bounds
            adjustment_factor = max(
                self.adaptive_config.min_adjustment_ratio,
                min(adjustment_factor, self.adaptive_config.max_adjustment_ratio),
            )

            # Apply adjustment
            return RateLimitConfig(
                requests_per_minute=int(config.requests_per_minute * adjustment_factor),
                requests_per_hour=int(config.requests_per_hour * adjustment_factor),
                requests_per_day=int(config.requests_per_day * adjustment_factor),
                burst_allowance=int(config.burst_allowance * adjustment_factor),
            )

        except Exception as e:
            logger.error(f"Failed to get adaptive config: {e}")
            return config

    def _check_distributed_rate_limit(
        self,
        api_key: Optional[APIKey],
        ip_address: Optional[str],
        endpoint: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check rate limit using Redis for distributed systems"""
        try:
            # Use API key or IP as identifier
            identifier = (
                str(api_key.id)
                if api_key
                else hashlib.sha256(ip_address.encode()).hexdigest()[:16]
            )

            now = time.time()
            pipe = self.redis_client.pipeline()

            # Check minute window
            minute_key = f"rl:{identifier}:{endpoint}:minute:{int(now // 60)}"
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)

            # Check hour window
            hour_key = f"rl:{identifier}:{endpoint}:hour:{int(now // 3600)}"
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)

            # Check day window
            day_key = f"rl:{identifier}:{endpoint}:day:{int(now // 86400)}"
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)

            results = pipe.execute()

            minute_count = results[0]
            hour_count = results[2]
            day_count = results[4]

            # Check limits
            if minute_count > config.requests_per_minute:
                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_minute,
                    remaining=0,
                    reset_time=datetime.fromtimestamp((int(now // 60) + 1) * 60),
                    retry_after=60 - int(now % 60),
                )

            if hour_count > config.requests_per_hour:
                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_hour,
                    remaining=0,
                    reset_time=datetime.fromtimestamp((int(now // 3600) + 1) * 3600),
                    retry_after=3600 - int(now % 3600),
                )

            if day_count > config.requests_per_day:
                return RateLimitResult(
                    allowed=False,
                    limit=config.requests_per_day,
                    remaining=0,
                    reset_time=datetime.fromtimestamp((int(now // 86400) + 1) * 86400),
                    retry_after=86400 - int(now % 86400),
                )

            # Request allowed
            return RateLimitResult(
                allowed=True,
                limit=config.requests_per_minute,
                remaining=max(0, config.requests_per_minute - minute_count),
                reset_time=datetime.fromtimestamp((int(now // 60) + 1) * 60),
            )

        except Exception as e:
            logger.error(f"Distributed rate limit check failed: {e}")
            # Fall back to local rate limiting
            from .rate_limiter import SQLiteRateLimiter

            local_limiter = SQLiteRateLimiter(self.db)
            return local_limiter.check_rate_limit(api_key, ip_address, endpoint)

    def _check_local_rate_limit(
        self,
        api_key: Optional[APIKey],
        ip_address: Optional[str],
        endpoint: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check rate limit using local SQLite (fallback)"""
        from .rate_limiter import SQLiteRateLimiter

        local_limiter = SQLiteRateLimiter(self.db)
        return local_limiter.check_rate_limit(api_key, ip_address, endpoint)

    def _get_average_response_time(self, endpoint: str, hours: int = 1) -> float:
        """Get average response time for endpoint"""
        try:
            cache_key = f"avg_rt:{endpoint}"
            if cache_key in self.response_time_cache:
                times = self.response_time_cache[cache_key]
                if times:
                    return statistics.mean(times)

            # Query database
            since = datetime.utcnow() - timedelta(hours=hours)
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT AVG(response_time_ms) FROM api_response_times
                    WHERE endpoint = ? AND timestamp > ?
                """,
                    (endpoint, since),
                )

                result = cursor.fetchone()
                return result[0] if result[0] else 0.0

        except Exception as e:
            logger.error(f"Failed to get average response time: {e}")
            return 0.0

    def _get_recent_requests(
        self, identifier: str, identifier_type: str, minutes: int = 1
    ) -> int:
        """Get recent request count for identifier"""
        try:
            since = datetime.utcnow() - timedelta(minutes=minutes)
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(request_count), 0) FROM rate_limits
                    WHERE identifier = ? AND identifier_type = ? AND updated_at > ?
                """,
                    (identifier, identifier_type, since),
                )

                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Failed to get recent requests: {e}")
            return 0

    def _get_recent_unique_endpoints(self, identifier: str, minutes: int = 5) -> int:
        """Get count of unique endpoints accessed recently"""
        try:
            since = datetime.utcnow() - timedelta(minutes=minutes)
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT endpoint) FROM rate_limits
                    WHERE identifier = ? AND updated_at > ?
                """,
                    (identifier, since),
                )

                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Failed to get unique endpoints: {e}")
            return 0

    def _get_recent_failed_auths(self, ip_address: str, minutes: int = 10) -> int:
        """Get recent failed authentication attempts"""
        try:
            # This would need to be integrated with authentication system
            # For now, return 0
            return 0

        except Exception as e:
            logger.error(f"Failed to get failed auth count: {e}")
            return 0

    def _log_enhanced_violation(
        self,
        api_key: Optional[APIKey],
        ip_address: Optional[str],
        endpoint: str,
        result: RateLimitResult,
        suspicious_score: float,
        user_agent: Optional[str],
    ):
        """Log enhanced rate limit violation with security context"""
        try:
            identifier = str(api_key.id) if api_key else ip_address
            identifier_type = "api_key" if api_key else "ip"

            # Determine threat level
            threat_level = ThreatLevel.LOW
            if suspicious_score > 0.7:
                threat_level = ThreatLevel.CRITICAL
            elif suspicious_score > 0.5:
                threat_level = ThreatLevel.HIGH
            elif suspicious_score > 0.3:
                threat_level = ThreatLevel.MEDIUM

            # Log suspicious activity
            activity = SuspiciousActivity(
                identifier=identifier,
                identifier_type=identifier_type,
                threat_level=threat_level,
                activity_type="rate_limit_violation",
                details={
                    "endpoint": endpoint,
                    "suspicious_score": suspicious_score,
                    "user_agent": user_agent,
                    "limit": result.limit,
                    "exceeded_by": result.limit - result.remaining,
                },
                timestamp=datetime.utcnow(),
            )

            # Store in database
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO suspicious_activities
                    (identifier, identifier_type, threat_level, activity_type, details)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        activity.identifier,
                        activity.identifier_type,
                        activity.threat_level.value,
                        activity.activity_type,
                        json.dumps(activity.details),
                    ),
                )
                conn.commit()

            # Auto-block if threat level is critical
            if threat_level == ThreatLevel.CRITICAL and ip_address:
                self.block_ip(
                    ip_address,
                    f"Automatic block: Critical threat level ({suspicious_score:.2f})",
                    threat_level,
                    duration_hours=24,
                )

            logger.warning(
                f"Enhanced rate limit violation: {identifier_type}={identifier}, "
                f"endpoint={endpoint}, threat_level={threat_level.value}, "
                f"suspicious_score={suspicious_score:.2f}"
            )

        except Exception as e:
            logger.error(f"Failed to log enhanced violation: {e}")

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        try:
            metrics = {}

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Rate limit violations by threat level
                cursor.execute(
                    """
                    SELECT threat_level, COUNT(*) FROM suspicious_activities
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY threat_level
                """
                )
                metrics["violations_by_threat_level"] = dict(cursor.fetchall())

                # Blocked IPs count
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM ip_blocks
                    WHERE expires_at IS NULL OR expires_at > datetime('now')
                """
                )
                metrics["blocked_ips_count"] = cursor.fetchone()[0]

                # Average response times by endpoint
                cursor.execute(
                    """
                    SELECT endpoint, AVG(response_time_ms) FROM api_response_times
                    WHERE timestamp > datetime('now', '-1 hour')
                    GROUP BY endpoint
                """
                )
                metrics["avg_response_times"] = dict(cursor.fetchall())

                # Total requests in last hour
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM api_response_times
                    WHERE timestamp > datetime('now', '-1 hour')
                """
                )
                metrics["requests_last_hour"] = cursor.fetchone()[0]

            return metrics

        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old rate limiting and security data

        Args:
            days: Number of days to retain data

        Returns:
            Dictionary with cleanup counts
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            cleanup_counts = {}

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Clean old response times
                cursor.execute(
                    """
                    DELETE FROM api_response_times WHERE timestamp < ?
                """,
                    (cutoff,),
                )
                cleanup_counts["response_times"] = cursor.rowcount

                # Clean resolved suspicious activities
                cursor.execute(
                    """
                    DELETE FROM suspicious_activities
                    WHERE timestamp < ? AND resolved = TRUE
                """,
                    (cutoff,),
                )
                cleanup_counts["suspicious_activities"] = cursor.rowcount

                # Clean expired IP blocks
                cursor.execute(
                    """
                    DELETE FROM ip_blocks
                    WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
                """,
                    (),
                )
                cleanup_counts["expired_blocks"] = cursor.rowcount

                conn.commit()

            logger.info(f"Cleaned up old data: {cleanup_counts}")
            return cleanup_counts

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {}
