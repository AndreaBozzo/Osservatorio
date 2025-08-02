"""
Rate Limiting Middleware for Osservatorio ISTAT Data Platform

SQLite-backed rate limiting with sliding window algorithm:
- Per-API-key rate limiting
- Per-IP rate limiting
- Configurable time windows (minute, hour, day)
- Graceful degradation with HTTP 429 responses
- Rate limit headers (X-RateLimit-*)
- Burst allowance for short-term spikes
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.database.sqlite.manager import SQLiteMetadataManager
from src.utils.logger import get_logger

from .models import APIKey

logger = get_logger(__name__)


class RateLimitConfig:
    """Rate limit configuration"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        burst_allowance: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.burst_allowance = burst_allowance


class RateLimitResult:
    """Rate limiting check result"""

    def __init__(
        self,
        allowed: bool,
        limit: int,
        remaining: int,
        reset_time: datetime,
        retry_after: Optional[int] = None,
    ):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after  # Seconds until reset

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers"""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_time.timestamp())),
        }

        if not self.allowed and self.retry_after:
            headers["Retry-After"] = str(self.retry_after)

        return headers


class SQLiteRateLimiter:
    """SQLite-backed rate limiter with sliding window algorithm"""

    # Default rate limit configurations by scope
    DEFAULT_LIMITS = {
        "read": RateLimitConfig(60, 1000, 10000, 10),
        "write": RateLimitConfig(30, 500, 5000, 5),
        "admin": RateLimitConfig(120, 2000, 20000, 20),
        "analytics": RateLimitConfig(100, 1500, 15000, 15),
        "powerbi": RateLimitConfig(200, 3000, 30000, 30),
        "tableau": RateLimitConfig(200, 3000, 30000, 30),
    }

    # Time window types
    WINDOW_MINUTE = "minute"
    WINDOW_HOUR = "hour"
    WINDOW_DAY = "day"

    def __init__(self, sqlite_manager: SQLiteMetadataManager):
        """Initialize rate limiter with SQLite backend"""
        self.db = sqlite_manager
        self.logger = logger

        # Ensure rate limiting schema exists
        self._ensure_rate_limit_schema()

        logger.info("SQLite Rate Limiter initialized")

    def _ensure_rate_limit_schema(self):
        """Ensure rate limiting tables exist"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Check if rate_limits table exists and has old schema
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='rate_limits'
                """
                )
                table_exists = cursor.fetchone() is not None

                if table_exists:
                    # Check if table has new columns
                    cursor.execute("PRAGMA table_info(rate_limits)")
                    columns = [col[1] for col in cursor.fetchall()]

                    if "identifier" not in columns:
                        # Drop old table and recreate with new schema
                        cursor.execute("DROP TABLE rate_limits")
                        table_exists = False

                if not table_exists:
                    # Create new rate_limits table with enhanced schema
                    cursor.execute(
                        """
                        CREATE TABLE rate_limits (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            identifier TEXT NOT NULL,  -- API key ID or IP hash
                            identifier_type TEXT NOT NULL,  -- 'api_key' or 'ip'
                            endpoint TEXT NOT NULL,
                            window_type TEXT NOT NULL,  -- 'minute', 'hour', 'day'
                            request_count INTEGER DEFAULT 0,
                            window_start TIMESTAMP NOT NULL,
                            window_end TIMESTAMP NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(identifier, identifier_type, endpoint, window_type, window_start)
                        )
                    """
                    )

                # Rate limit violations log
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limit_violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        identifier TEXT NOT NULL,
                        identifier_type TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        window_type TEXT NOT NULL,
                        exceeded_by INTEGER NOT NULL,
                        limit_value INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_agent TEXT,
                        ip_address TEXT
                    )
                """
                )

                # Create indexes for performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup
                    ON rate_limits(identifier, identifier_type, endpoint, window_type, window_start)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_rate_limits_cleanup
                    ON rate_limits(window_end)
                """
                )

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to ensure rate limit schema: {e}")
            raise

    def check_rate_limit(
        self,
        api_key: Optional[APIKey] = None,
        ip_address: Optional[str] = None,
        endpoint: str = "default",
        user_agent: Optional[str] = None,
    ) -> RateLimitResult:
        """Check if request should be rate limited

        Args:
            api_key: API key for authenticated requests
            ip_address: Client IP address
            endpoint: API endpoint being accessed
            user_agent: Client user agent

        Returns:
            RateLimitResult with decision and metadata
        """
        try:
            # Determine rate limit configuration
            config = self._get_rate_limit_config(api_key)

            # Check API key rate limit if available
            if api_key:
                api_result = self._check_api_key_limit(api_key, endpoint, config)
                if not api_result.allowed:
                    self._log_violation(
                        str(api_key.id),
                        "api_key",
                        endpoint,
                        api_result,
                        user_agent,
                        ip_address,
                    )
                    return api_result

            # Check IP rate limit
            if ip_address:
                ip_result = self._check_ip_limit(ip_address, endpoint, config)
                if not ip_result.allowed:
                    self._log_violation(
                        ip_address, "ip", endpoint, ip_result, user_agent, ip_address
                    )
                    return ip_result

            # If we get here, request is allowed
            # Return the most restrictive remaining count
            if api_key and ip_address:
                return self._merge_results(api_result, ip_result)
            elif api_key:
                return api_result
            elif ip_address:
                return ip_result
            else:
                # No rate limiting if no identifier
                return RateLimitResult(True, 1000, 1000, datetime.utcnow())

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request on error (fail open)
            return RateLimitResult(True, 1000, 1000, datetime.utcnow())

    def _get_rate_limit_config(self, api_key: Optional[APIKey]) -> RateLimitConfig:
        """Get rate limit configuration based on API key scopes"""
        if not api_key:
            return self.DEFAULT_LIMITS["read"]  # Default for unauthenticated

        # Use highest scope's limits
        if "admin" in api_key.scopes:
            return self.DEFAULT_LIMITS["admin"]
        elif "powerbi" in api_key.scopes:
            return self.DEFAULT_LIMITS["powerbi"]
        elif "tableau" in api_key.scopes:
            return self.DEFAULT_LIMITS["tableau"]
        elif "analytics" in api_key.scopes:
            return self.DEFAULT_LIMITS["analytics"]
        elif "write" in api_key.scopes:
            return self.DEFAULT_LIMITS["write"]
        else:
            return self.DEFAULT_LIMITS["read"]

    def _check_api_key_limit(
        self, api_key: APIKey, endpoint: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Check rate limit for API key"""
        identifier = str(api_key.id)
        return self._check_sliding_window_limit(identifier, "api_key", endpoint, config)

    def _check_ip_limit(
        self, ip_address: str, endpoint: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Check rate limit for IP address"""
        # Hash IP for privacy
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        return self._check_sliding_window_limit(ip_hash, "ip", endpoint, config)

    def _check_sliding_window_limit(
        self,
        identifier: str,
        identifier_type: str,
        endpoint: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check sliding window rate limit"""
        now = datetime.utcnow()

        # Check each time window (minute, hour, day)
        windows = [
            (self.WINDOW_MINUTE, 1, config.requests_per_minute),
            (self.WINDOW_HOUR, 60, config.requests_per_hour),
            (self.WINDOW_DAY, 1440, config.requests_per_day),
        ]

        for window_type, minutes, limit in windows:
            window_start = now.replace(second=0, microsecond=0)

            if window_type == self.WINDOW_HOUR:
                window_start = window_start.replace(minute=0)
            elif window_type == self.WINDOW_DAY:
                window_start = window_start.replace(hour=0, minute=0)

            window_end = window_start + timedelta(minutes=minutes)

            # Get current count in window
            current_count = self._get_window_count(
                identifier, identifier_type, endpoint, window_type, window_start
            )

            # Check if limit exceeded
            if current_count >= limit:
                retry_after = int((window_end - now).total_seconds())
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=window_end,
                    retry_after=retry_after,
                )

        # All windows are under limit - increment counter and return success
        self._increment_window_count(identifier, identifier_type, endpoint, now)

        # Return most restrictive remaining count
        minute_count = self._get_window_count(
            identifier,
            identifier_type,
            endpoint,
            self.WINDOW_MINUTE,
            now.replace(second=0, microsecond=0),
        )

        return RateLimitResult(
            allowed=True,
            limit=config.requests_per_minute,
            remaining=max(0, config.requests_per_minute - minute_count - 1),
            reset_time=now.replace(second=0, microsecond=0) + timedelta(minutes=1),
        )

    def _get_window_count(
        self,
        identifier: str,
        identifier_type: str,
        endpoint: str,
        window_type: str,
        window_start: datetime,
    ) -> int:
        """Get request count for time window"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(request_count), 0)
                    FROM rate_limits
                    WHERE identifier = ? AND identifier_type = ?
                    AND endpoint = ? AND window_type = ?
                    AND window_start >= ? AND window_end > ?
                """,
                    (
                        identifier,
                        identifier_type,
                        endpoint,
                        window_type,
                        window_start,
                        datetime.utcnow(),
                    ),
                )

                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Failed to get window count: {e}")
            return 0

    def _increment_window_count(
        self, identifier: str, identifier_type: str, endpoint: str, timestamp: datetime
    ):
        """Increment request count for all time windows"""
        try:
            windows = [
                (self.WINDOW_MINUTE, 1),
                (self.WINDOW_HOUR, 60),
                (self.WINDOW_DAY, 1440),
            ]

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                for window_type, minutes in windows:
                    window_start = timestamp.replace(second=0, microsecond=0)

                    if window_type == self.WINDOW_HOUR:
                        window_start = window_start.replace(minute=0)
                    elif window_type == self.WINDOW_DAY:
                        window_start = window_start.replace(hour=0, minute=0)

                    window_end = window_start + timedelta(minutes=minutes)

                    # Insert or increment counter
                    cursor.execute(
                        """
                        INSERT INTO rate_limits
                        (identifier, identifier_type, endpoint, window_type,
                         request_count, window_start, window_end, updated_at)
                        VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                        ON CONFLICT(identifier, identifier_type, endpoint, window_type, window_start)
                        DO UPDATE SET
                            request_count = request_count + 1,
                            updated_at = ?
                    """,
                        (
                            identifier,
                            identifier_type,
                            endpoint,
                            window_type,
                            window_start,
                            window_end,
                            timestamp,
                            timestamp,
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to increment window count: {e}")

    def _merge_results(
        self, api_result: RateLimitResult, ip_result: RateLimitResult
    ) -> RateLimitResult:
        """Merge API key and IP rate limit results"""
        if not api_result.allowed or not ip_result.allowed:
            # Return the more restrictive result
            if not api_result.allowed:
                return api_result
            else:
                return ip_result

        # Both allowed - return most restrictive remaining count
        return RateLimitResult(
            allowed=True,
            limit=min(api_result.limit, ip_result.limit),
            remaining=min(api_result.remaining, ip_result.remaining),
            reset_time=min(api_result.reset_time, ip_result.reset_time),
        )

    def _log_violation(
        self,
        identifier: str,
        identifier_type: str,
        endpoint: str,
        result: RateLimitResult,
        user_agent: Optional[str],
        ip_address: Optional[str],
    ):
        """Log rate limit violation"""
        try:
            exceeded_by = result.limit - result.remaining

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO rate_limit_violations
                    (identifier, identifier_type, endpoint, window_type,
                     exceeded_by, limit_value, user_agent, ip_address)
                    VALUES (?, ?, ?, 'minute', ?, ?, ?, ?)
                """,
                    (
                        identifier,
                        identifier_type,
                        endpoint,
                        exceeded_by,
                        result.limit,
                        user_agent,
                        ip_address,
                    ),
                )

                conn.commit()

            logger.warning(
                f"Rate limit violation: {identifier_type}={identifier}, "
                f"endpoint={endpoint}, exceeded_by={exceeded_by}"
            )

        except Exception as e:
            logger.error(f"Failed to log rate limit violation: {e}")

    def cleanup_expired_windows(self) -> int:
        """Clean up expired rate limit windows

        Returns:
            Number of expired windows cleaned up
        """
        try:
            now = datetime.utcnow()

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM rate_limits WHERE window_end <= ?
                """,
                    (now,),
                )

                cleaned = cursor.rowcount
                conn.commit()

            if cleaned > 0:
                logger.debug(f"Cleaned up {cleaned} expired rate limit windows")

            return cleaned

        except Exception as e:
            logger.error(f"Rate limit cleanup failed: {e}")
            return 0

    def get_rate_limit_stats(
        self, identifier: str, identifier_type: str
    ) -> Dict[str, Dict]:
        """Get rate limit statistics for identifier

        Args:
            identifier: API key ID or IP hash
            identifier_type: 'api_key' or 'ip'

        Returns:
            Dictionary with current usage stats
        """
        try:
            stats = {}
            now = datetime.utcnow()

            windows = [
                (self.WINDOW_MINUTE, 1),
                (self.WINDOW_HOUR, 60),
                (self.WINDOW_DAY, 1440),
            ]

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                for window_type, minutes in windows:
                    window_start = now.replace(second=0, microsecond=0)

                    if window_type == self.WINDOW_HOUR:
                        window_start = window_start.replace(minute=0)
                    elif window_type == self.WINDOW_DAY:
                        window_start = window_start.replace(hour=0, minute=0)

                    cursor.execute(
                        """
                        SELECT COALESCE(SUM(request_count), 0)
                        FROM rate_limits
                        WHERE identifier = ? AND identifier_type = ?
                        AND window_type = ? AND window_start >= ?
                    """,
                        (identifier, identifier_type, window_type, window_start),
                    )

                    count = cursor.fetchone()[0]
                    stats[window_type] = {
                        "current_count": count,
                        "window_start": window_start.isoformat(),
                        "window_end": (
                            window_start + timedelta(minutes=minutes)
                        ).isoformat(),
                    }

            return stats

        except Exception as e:
            logger.error(f"Failed to get rate limit stats: {e}")
            return {}
