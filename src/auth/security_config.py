"""
Simplified Security Configuration for MVP - Issue #153

Basic security configuration for MVP:
- Simple rate limiting configuration
- Basic JWT settings
- No Redis/adaptive/monitoring features
- Essential security settings only
"""

from dataclasses import dataclass
from typing import Optional

from src.utils.config import get_config
from src.utils.logger import get_logger

from .rate_limiter import SQLiteRateLimiter

logger = get_logger(__name__)


@dataclass
class SecurityConfig:
    """Simplified security configuration for MVP - Issue #153"""

    # Basic rate limiting
    rate_limiting_enabled: bool = True
    default_rate_limit: int = 100  # requests per hour
    burst_rate_limit: int = 10  # requests per minute

    # Basic JWT
    jwt_expiry_hours: int = 1
    jwt_secret_rotation_days: int = 30

    # Basic security
    require_api_key: bool = True
    enable_audit_logging: bool = True


def get_security_config() -> SecurityConfig:
    """Get simplified security configuration for MVP"""
    try:
        config = get_config()

        return SecurityConfig(
            rate_limiting_enabled=config.get("security_rate_limiting_enabled", True),
            default_rate_limit=config.get("security_default_rate_limit", 100),
            burst_rate_limit=config.get("security_burst_rate_limit", 10),
            jwt_expiry_hours=config.get("security_jwt_expiry_hours", 1),
            jwt_secret_rotation_days=config.get("security_jwt_rotation_days", 30),
            require_api_key=config.get("security_require_api_key", True),
            enable_audit_logging=config.get("security_audit_logging", True),
        )
    except Exception as e:
        logger.warning(f"Error loading security config, using defaults: {e}")
        return SecurityConfig()


def create_rate_limiter(db_path: Optional[str] = None) -> SQLiteRateLimiter:
    """Create basic SQLite rate limiter for MVP

    Issue #153: Removed enhanced/adaptive rate limiting
    """
    try:
        return SQLiteRateLimiter(db_path=db_path)
    except Exception as e:
        logger.error(f"Failed to create rate limiter: {e}")
        raise


# Backward compatibility
def setup_security() -> dict:
    """Setup basic security components for MVP

    Returns dict with basic security components
    """
    config = get_security_config()

    components = {
        "config": config,
        "rate_limiter": create_rate_limiter() if config.rate_limiting_enabled else None,
    }

    logger.info("Simplified security setup completed for MVP - Issue #153")
    return components


# Remove complex enterprise features for MVP
def get_enhanced_rate_limiter(*args, **kwargs):
    """Enhanced rate limiter removed for MVP - Issue #153"""
    logger.warning(
        "Enhanced rate limiter removed for MVP. Use basic SQLiteRateLimiter instead."
    )
    return create_rate_limiter()


def setup_enhanced_security(*args, **kwargs):
    """Enhanced security removed for MVP - Issue #153"""
    logger.warning(
        "Enhanced security features removed for MVP. Use setup_security() instead."
    )
    return setup_security()
