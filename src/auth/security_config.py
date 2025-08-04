"""
Security Configuration and Setup for Enhanced Rate Limiting

This module provides configuration management and factory functions
for setting up the enhanced security features including:
- Enhanced rate limiting with Redis support
- Adaptive rate limiting based on API performance
- IP blocking and suspicious activity detection
- Security monitoring dashboard
"""

import os
from dataclasses import dataclass
from typing import Any, Optional

from src.database.sqlite.manager import SQLiteMetadataManager
from src.utils.config import get_config
from src.utils.logger import get_logger

from .enhanced_rate_limiter import AdaptiveConfig, EnhancedRateLimiter
from .rate_limiter import SQLiteRateLimiter
from .security_middleware import AuthenticationMiddleware

logger = get_logger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration data class"""

    enhanced_rate_limiting_enabled: bool
    redis_url: Optional[str]
    adaptive_rate_limiting_enabled: bool
    response_time_threshold_ms: float
    rate_limit_adjustment_factor: float
    min_adjustment_ratio: float
    max_adjustment_ratio: float
    suspicious_activity_threshold: float
    auto_block_critical_threats: bool
    ip_block_duration_hours: int
    security_monitoring_enabled: bool
    alert_email: Optional[str]
    cleanup_data_retention_days: int

    @classmethod
    def from_config(cls) -> "SecurityConfig":
        """Create SecurityConfig from environment configuration"""
        config = get_config()
        return cls(
            enhanced_rate_limiting_enabled=config.get(
                "enhanced_rate_limiting_enabled", True
            ),
            redis_url=config.get("redis_url"),
            adaptive_rate_limiting_enabled=config.get(
                "adaptive_rate_limiting_enabled", True
            ),
            response_time_threshold_ms=config.get("response_time_threshold_ms", 2000.0),
            rate_limit_adjustment_factor=config.get(
                "rate_limit_adjustment_factor", 0.8
            ),
            min_adjustment_ratio=config.get("min_adjustment_ratio", 0.1),
            max_adjustment_ratio=config.get("max_adjustment_ratio", 2.0),
            suspicious_activity_threshold=config.get(
                "suspicious_activity_threshold", 0.5
            ),
            auto_block_critical_threats=config.get("auto_block_critical_threats", True),
            ip_block_duration_hours=config.get("ip_block_duration_hours", 24),
            security_monitoring_enabled=config.get("security_monitoring_enabled", True),
            alert_email=config.get("alert_email"),
            cleanup_data_retention_days=config.get("cleanup_data_retention_days", 30),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "enhanced_rate_limiting_enabled": self.enhanced_rate_limiting_enabled,
            "redis_available": self.redis_url is not None,
            "adaptive_rate_limiting_enabled": self.adaptive_rate_limiting_enabled,
            "response_time_threshold_ms": self.response_time_threshold_ms,
            "auto_block_critical_threats": self.auto_block_critical_threats,
            "security_monitoring_enabled": self.security_monitoring_enabled,
            "cleanup_retention_days": self.cleanup_data_retention_days,
        }


class SecurityManager:
    """Central security manager for enhanced rate limiting and monitoring"""

    def __init__(
        self, db_manager: SQLiteMetadataManager, config: Optional[SecurityConfig] = None
    ):
        """Initialize security manager

        Args:
            db_manager: SQLite database manager
            config: Security configuration (auto-loaded if None)
        """
        self.db_manager = db_manager
        self.config = config or SecurityConfig.from_config()

        # Initialize components
        self.rate_limiter = self._create_rate_limiter()
        self.auth_middleware = self._create_auth_middleware()

        logger.info(f"Security Manager initialized: {self.config.to_dict()}")

    def _create_rate_limiter(self):
        """Create appropriate rate limiter based on configuration"""
        if self.config.enhanced_rate_limiting_enabled:
            # Create adaptive configuration
            adaptive_config = AdaptiveConfig(
                enable_adaptive=self.config.adaptive_rate_limiting_enabled,
                response_time_threshold_ms=self.config.response_time_threshold_ms,
                adjustment_factor=self.config.rate_limit_adjustment_factor,
                min_adjustment_ratio=self.config.min_adjustment_ratio,
                max_adjustment_ratio=self.config.max_adjustment_ratio,
            )

            # Create enhanced rate limiter
            return EnhancedRateLimiter(
                sqlite_manager=self.db_manager,
                redis_url=self.config.redis_url,
                adaptive_config=adaptive_config,
            )
        else:
            # Use basic SQLite rate limiter
            logger.info("Using basic SQLite rate limiter")
            return SQLiteRateLimiter(self.db_manager)

    def _create_auth_middleware(self):
        """Create authentication middleware with rate limiting"""
        from .jwt_manager import JWTManager
        from .sqlite_auth import SQLiteAuthManager

        # This assumes these components exist and are properly configured
        auth_manager = SQLiteAuthManager(self.db_manager)
        jwt_manager = JWTManager()

        return AuthenticationMiddleware(
            auth_manager=auth_manager,
            jwt_manager=jwt_manager,
            rate_limiter=self.rate_limiter,
        )

    def create_security_dashboard(self):
        """Create security monitoring dashboard"""
        if not self.config.security_monitoring_enabled:
            logger.info("Security monitoring disabled")
            return None

        from src.api.security_dashboard import SecurityDashboard

        return SecurityDashboard(
            enhanced_limiter=self.rate_limiter,
            auth_middleware=self.auth_middleware,
            db_path=self.db_path,
        )

    def create_security_router(self):
        """Create FastAPI router for security endpoints"""
        if not self.config.security_monitoring_enabled:
            return None

        from src.api.security_dashboard import create_security_router

        return create_security_router(
            enhanced_limiter=self.rate_limiter,
            auth_middleware=self.auth_middleware,
            db_path=self.db_path,
        )

    def run_security_maintenance(self):
        """Run security maintenance tasks"""
        try:
            logger.info("Running security maintenance tasks")

            # Cleanup old data if enhanced rate limiter
            if isinstance(self.rate_limiter, EnhancedRateLimiter):
                cleanup_results = self.rate_limiter.cleanup_old_data(
                    days=self.config.cleanup_data_retention_days
                )
                logger.info(f"Security cleanup completed: {cleanup_results}")

            # Cleanup expired rate limit windows
            cleanup_count = self.rate_limiter.cleanup_expired_windows()
            logger.info(f"Cleaned up {cleanup_count} expired rate limit windows")

        except Exception as e:
            logger.error(f"Security maintenance failed: {e}")

    def get_security_status(self) -> dict[str, Any]:
        """Get current security system status"""
        try:
            status = {
                "enhanced_rate_limiting": self.config.enhanced_rate_limiting_enabled,
                "adaptive_rate_limiting": self.config.adaptive_rate_limiting_enabled,
                "security_monitoring": self.config.security_monitoring_enabled,
                "redis_connected": False,
                "database_connected": True,  # Assumed if we got this far
                "rate_limiter_type": type(self.rate_limiter).__name__,
            }

            # Check Redis connection if enhanced limiter
            if isinstance(self.rate_limiter, EnhancedRateLimiter):
                status["redis_connected"] = self.rate_limiter.redis_client is not None

                # Get security metrics if available
                try:
                    metrics = self.rate_limiter.get_security_metrics()
                    status["security_metrics"] = metrics
                except Exception as e:
                    logger.warning(f"Failed to get security metrics: {e}")
                    status["security_metrics"] = {}

            return status

        except Exception as e:
            logger.error(f"Failed to get security status: {e}")
            return {"error": str(e)}

    def block_ip_address(
        self, ip_address: str, reason: str, duration_hours: Optional[int] = None
    ):
        """Block an IP address for security reasons

        Args:
            ip_address: IP address to block
            reason: Reason for blocking
            duration_hours: Duration in hours (uses config default if None)
        """
        if not isinstance(self.rate_limiter, EnhancedRateLimiter):
            logger.warning("IP blocking not available with basic rate limiter")
            return False

        duration = duration_hours or self.config.ip_block_duration_hours

        from .enhanced_rate_limiter import ThreatLevel

        self.rate_limiter.block_ip(
            ip_address=ip_address,
            reason=reason,
            threat_level=ThreatLevel.HIGH,
            duration_hours=duration,
            notes="Manual block via SecurityManager",
        )

        logger.info(f"IP blocked via SecurityManager: {ip_address[:8]}*** for {reason}")
        return True

    def record_api_response(
        self,
        identifier: str,
        identifier_type: str,
        endpoint: str,
        response_time_ms: float,
        status_code: int = 200,
    ):
        """Record API response time for adaptive rate limiting

        Args:
            identifier: API key ID or IP hash
            identifier_type: 'api_key' or 'ip'
            endpoint: API endpoint
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
        """
        if isinstance(self.rate_limiter, EnhancedRateLimiter):
            self.rate_limiter.record_response_time(
                identifier=identifier,
                identifier_type=identifier_type,
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                status_code=status_code,
            )


def create_security_manager(
    db_manager: SQLiteMetadataManager, config: Optional[SecurityConfig] = None
) -> SecurityManager:
    """Factory function to create security manager

    Args:
        db_manager: SQLite database manager
        config: Security configuration (auto-loaded if None)

    Returns:
        Configured SecurityManager instance
    """
    return SecurityManager(db_manager=db_manager, config=config)


def validate_security_environment() -> dict[str, Any]:
    """Validate security environment configuration

    Returns:
        Dictionary with validation results
    """
    validation = {"valid": True, "warnings": [], "errors": [], "recommendations": []}

    config = SecurityConfig.from_config()

    # Check Redis availability for distributed rate limiting
    if config.enhanced_rate_limiting_enabled and config.redis_url:
        try:
            import redis

            client = redis.from_url(config.redis_url)
            client.ping()
            validation["redis_available"] = True
        except Exception as e:
            validation["warnings"].append(f"Redis not available: {e}")
            validation["redis_available"] = False
    else:
        validation["redis_available"] = False
        if config.enhanced_rate_limiting_enabled:
            validation["warnings"].append(
                "Enhanced rate limiting enabled but no Redis URL configured"
            )

    # Check JWT secret key
    if not os.getenv("JWT_SECRET_KEY"):
        validation["errors"].append("JWT_SECRET_KEY environment variable not set")
        validation["valid"] = False

    # Check security alert email
    if config.security_monitoring_enabled and not config.alert_email:
        validation["recommendations"].append(
            "Set SECURITY_ALERT_EMAIL for security notifications"
        )

    # Validate thresholds
    if config.response_time_threshold_ms < 100:
        validation["warnings"].append(
            "Response time threshold very low, may cause aggressive rate limiting"
        )

    if config.suspicious_activity_threshold > 0.9:
        validation["warnings"].append(
            "Suspicious activity threshold very high, may miss threats"
        )

    return validation


# Example environment configuration template
def generate_env_template() -> str:
    """Generate .env template for security configuration"""
    template = """
# Enhanced Security Configuration for Osservatorio ISTAT Data Platform

# Enhanced Rate Limiting
ENHANCED_RATE_LIMITING_ENABLED=true
REDIS_URL=redis://localhost:6379/0
ADAPTIVE_RATE_LIMITING_ENABLED=true
RESPONSE_TIME_THRESHOLD_MS=2000
RATE_LIMIT_ADJUSTMENT_FACTOR=0.8
MIN_ADJUSTMENT_RATIO=0.1
MAX_ADJUSTMENT_RATIO=2.0

# Security Monitoring
SUSPICIOUS_ACTIVITY_THRESHOLD=0.5
AUTO_BLOCK_CRITICAL_THREATS=true
IP_BLOCK_DURATION_HOURS=24
SECURITY_MONITORING_ENABLED=true
SECURITY_ALERT_EMAIL=admin@example.com

# Data Management
CLEANUP_DATA_RETENTION_DAYS=30

# JWT Configuration (Required)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Basic Rate Limiting (Fallback)
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_REQUESTS_PER_DAY=10000
"""
    return template.strip()
