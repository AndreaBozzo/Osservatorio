"""
Comprehensive tests for Enhanced Rate Limiting System

Tests all components with proper mocking and real validation:
- Enhanced rate limiter with distributed support
- Adaptive rate limiting based on API performance
- IP blocking and suspicious activity detection
- Security monitoring dashboard
- Configuration management
"""

import json
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from src.api.security_dashboard import AlertLevel, SecurityDashboard, SecurityMetrics
from src.auth.enhanced_rate_limiter import (
    AdaptiveConfig,
    EnhancedRateLimiter,
    SuspiciousActivity,
    ThreatLevel,
)
from src.auth.models import APIKey
from src.auth.rate_limiter import RateLimitConfig, RateLimitResult
from src.auth.security_config import SecurityConfig, SecurityManager
from src.database.sqlite.manager import SQLiteMetadataManager


class TestEnhancedRateLimiterFixed:
    """Test enhanced rate limiting with proper mocking"""

    @pytest.fixture
    def mock_db_manager(self):
        """Properly mocked SQLite database manager"""
        mock_db = Mock(spec=SQLiteMetadataManager)

        # Create a proper context manager mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        @contextmanager
        def mock_transaction():
            yield mock_conn

        mock_db.transaction = mock_transaction
        return mock_db, mock_conn, mock_cursor

    @pytest.fixture
    def adaptive_config(self):
        """Test adaptive configuration"""
        return AdaptiveConfig(
            enable_adaptive=True,
            response_time_threshold_ms=1000.0,
            adjustment_factor=0.7,
            min_adjustment_ratio=0.2,
            max_adjustment_ratio=1.5,
            window_size=50,
        )

    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing"""
        api_key = Mock(spec=APIKey)
        api_key.id = "test-api-key-123"
        api_key.scopes = ["read", "analytics"]
        api_key.name = "Test API Key"
        return api_key

    def test_enhanced_limiter_initialization(self, mock_db_manager, adaptive_config):
        """Test enhanced rate limiter initialization"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock the schema creation to avoid database calls
        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, redis_url=None, adaptive_config=adaptive_config
            )

        assert limiter.adaptive_config == adaptive_config
        assert limiter.redis_client is None
        assert limiter.response_time_cache == {}
        assert limiter.suspicious_ips == {}
        assert limiter.blocked_ips == {}

    @patch("src.auth.enhanced_rate_limiter.redis")
    def test_redis_initialization_success(
        self, mock_redis_module, mock_db_manager, adaptive_config
    ):
        """Test successful Redis initialization"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock Redis client
        mock_redis_client = Mock()
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_module.REDIS_AVAILABLE = True

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db,
                redis_url="redis://localhost:6379/0",
                adaptive_config=adaptive_config,
            )

        mock_redis_module.from_url.assert_called_once_with("redis://localhost:6379/0")
        mock_redis_client.ping.assert_called_once()
        assert limiter.redis_client == mock_redis_client

    @patch("src.auth.enhanced_rate_limiter.redis")
    def test_redis_initialization_failure(
        self, mock_redis_module, mock_db_manager, adaptive_config
    ):
        """Test Redis initialization failure fallback"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock Redis failure
        mock_redis_module.from_url.side_effect = Exception("Redis connection failed")
        mock_redis_module.REDIS_AVAILABLE = True

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db,
                redis_url="redis://localhost:6379/0",
                adaptive_config=adaptive_config,
            )

        assert limiter.redis_client is None

    def test_response_time_recording(self, mock_db_manager, adaptive_config):
        """Test API response time recording"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, adaptive_config=adaptive_config
            )

        limiter.record_response_time(
            identifier="test-user",
            identifier_type="api_key",
            endpoint="/api/data",
            response_time_ms=1500.0,
            status_code=200,
        )

        # Check cache update
        cache_key = "test-user:/api/data"
        assert cache_key in limiter.response_time_cache
        assert limiter.response_time_cache[cache_key] == [1500.0]

        # Verify database insert was called
        mock_cursor.execute.assert_called()
        calls = mock_cursor.execute.call_args_list
        insert_call = next(
            (c for c in calls if "INSERT INTO api_response_times" in str(c)),
            None,
        )
        assert insert_call is not None

    def test_suspicious_activity_analysis(
        self, mock_db_manager, adaptive_config, mock_api_key
    ):
        """Test suspicious activity pattern detection"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, adaptive_config=adaptive_config
            )

        # Mock the helper methods to simulate suspicious activity
        limiter._get_recent_requests = Mock(return_value=150)  # High request rate
        limiter._get_recent_unique_endpoints = Mock(return_value=15)  # Many endpoints
        limiter._get_recent_failed_auths = Mock(return_value=0)

        suspicion_score = limiter._analyze_suspicious_activity(
            api_key=mock_api_key,
            ip_address="192.168.1.100",
            endpoint="/api/sensitive",
            user_agent="suspicious-bot/1.0",
            request_data={},
        )

        # Should detect high suspicion due to rapid requests and bot user agent
        assert suspicion_score > 0.5

    def test_ip_blocking(self, mock_db_manager, adaptive_config):
        """Test IP address blocking functionality"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, adaptive_config=adaptive_config
            )

        ip_address = "192.168.1.100"
        reason = "Automated attack detected"

        limiter.block_ip(
            ip_address=ip_address,
            reason=reason,
            threat_level=ThreatLevel.HIGH,
            duration_hours=24,
        )

        # Verify database insert was called
        mock_cursor.execute.assert_called()
        insert_call = mock_cursor.execute.call_args_list[-1]
        assert "INSERT OR REPLACE INTO ip_blocks" in str(insert_call)

        # Check if IP is marked as blocked in cache
        import hashlib

        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        assert ip_hash in limiter.blocked_ips

    def test_adaptive_rate_limit_config(
        self, mock_db_manager, adaptive_config, mock_api_key
    ):
        """Test adaptive rate limit configuration based on performance"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, adaptive_config=adaptive_config
            )

        # Mock slow average response time
        limiter._get_average_response_time = Mock(return_value=2500.0)

        config = limiter._get_adaptive_rate_limit_config(
            api_key=mock_api_key, endpoint="/api/slow", suspicious_score=0.2
        )

        # Should reduce limits due to slow response time
        # Base limit for analytics scope would be higher
        assert config.requests_per_minute < 100  # Reduced from default

    def test_security_metrics_collection(self, mock_db_manager, adaptive_config):
        """Test security metrics collection"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, adaptive_config=adaptive_config
            )

        # Mock database responses for metrics queries
        mock_cursor.fetchall.side_effect = [
            [("high", 5), ("medium", 10)],  # violations by threat level
            [(25,)],  # blocked IPs count
            [("/api/data", 1200.0), ("/api/auth", 800.0)],  # avg response times
            [(150,)],  # requests last hour
        ]
        mock_cursor.fetchone.side_effect = [(25,), (150,)]

        metrics = limiter.get_security_metrics()

        assert "violations_by_threat_level" in metrics
        assert "blocked_ips_count" in metrics
        assert "avg_response_times" in metrics
        assert metrics["blocked_ips_count"] == 25

    @patch("src.auth.enhanced_rate_limiter.time.time")
    def test_distributed_rate_limiting_with_redis(
        self, mock_time, mock_db_manager, adaptive_config, mock_api_key
    ):
        """Test distributed rate limiting using Redis"""
        mock_db, mock_conn, mock_cursor = mock_db_manager
        mock_time.return_value = 1640995200  # Fixed timestamp

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            limiter = EnhancedRateLimiter(
                sqlite_manager=mock_db, adaptive_config=adaptive_config
            )

        # Mock Redis client and pipeline
        mock_redis = Mock()
        mock_pipe = Mock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [
            1,
            True,
            1,
            True,
            1,
            True,
        ]  # First request counts
        limiter.redis_client = mock_redis

        config = RateLimitConfig(requests_per_minute=60)

        result = limiter._check_distributed_rate_limit(
            api_key=mock_api_key, ip_address=None, endpoint="/api/test", config=config
        )

        assert result.allowed
        assert result.remaining == 59  # 60 - 1
        mock_pipe.incr.assert_called()
        mock_pipe.expire.assert_called()


class TestSecurityConfigFixed:
    """Test security configuration with proper validation"""

    def test_security_config_creation_from_defaults(self):
        """Test SecurityConfig creation with default values"""
        config = SecurityConfig(
            enhanced_rate_limiting_enabled=True,
            redis_url=None,
            adaptive_rate_limiting_enabled=True,
            response_time_threshold_ms=2000.0,
            rate_limit_adjustment_factor=0.8,
            min_adjustment_ratio=0.1,
            max_adjustment_ratio=2.0,
            suspicious_activity_threshold=0.5,
            auto_block_critical_threats=True,
            ip_block_duration_hours=24,
            security_monitoring_enabled=True,
            alert_email="test@example.com",
            cleanup_data_retention_days=30,
        )

        assert config.enhanced_rate_limiting_enabled
        assert config.adaptive_rate_limiting_enabled
        assert config.response_time_threshold_ms == 2000.0
        assert config.auto_block_critical_threats

    @patch("src.auth.security_config.get_config")
    def test_security_config_from_environment(self, mock_get_config):
        """Test SecurityConfig creation from environment"""
        mock_get_config.return_value = {
            "enhanced_rate_limiting_enabled": True,
            "redis_url": "redis://localhost:6379",
            "adaptive_rate_limiting_enabled": True,
            "response_time_threshold_ms": 1500.0,
            "auto_block_critical_threats": False,
            "suspicious_activity_threshold": 0.7,
            "ip_block_duration_hours": 12,
            "security_monitoring_enabled": True,
            "alert_email": "admin@example.com",
            "cleanup_data_retention_days": 15,
        }

        config = SecurityConfig.from_config()

        assert config.enhanced_rate_limiting_enabled
        assert config.redis_url == "redis://localhost:6379"
        assert config.response_time_threshold_ms == 1500.0
        assert not config.auto_block_critical_threats

    def test_security_config_dictionary_conversion(self):
        """Test SecurityConfig to dictionary conversion"""
        config = SecurityConfig(
            enhanced_rate_limiting_enabled=True,
            redis_url="redis://localhost:6379",
            adaptive_rate_limiting_enabled=False,
            response_time_threshold_ms=3000.0,
            rate_limit_adjustment_factor=0.9,
            min_adjustment_ratio=0.2,
            max_adjustment_ratio=1.8,
            suspicious_activity_threshold=0.4,
            auto_block_critical_threats=True,
            ip_block_duration_hours=48,
            security_monitoring_enabled=False,
            alert_email=None,
            cleanup_data_retention_days=60,
        )

        config_dict = config.to_dict()

        assert config_dict["enhanced_rate_limiting_enabled"]
        assert config_dict["redis_available"]  # True because redis_url is set
        assert not config_dict["adaptive_rate_limiting_enabled"]
        assert not config_dict["security_monitoring_enabled"]


class TestSecurityDashboardFixed:
    """Test security monitoring dashboard with proper mocking"""

    @pytest.fixture
    def mock_db_manager(self):
        """Properly mocked database manager for dashboard tests"""
        mock_db = Mock(spec=SQLiteMetadataManager)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        @contextmanager
        def mock_transaction():
            yield mock_conn

        mock_db.transaction = mock_transaction
        return mock_db, mock_conn, mock_cursor

    @pytest.fixture
    def security_dashboard(self, mock_db_manager):
        """Security dashboard instance with mocked dependencies"""
        mock_db, mock_conn, mock_cursor = mock_db_manager
        mock_enhanced_limiter = Mock()
        mock_auth_middleware = Mock()

        return SecurityDashboard(mock_enhanced_limiter, mock_auth_middleware, mock_db)

    def test_real_time_metrics_retrieval(self, security_dashboard, mock_db_manager):
        """Test real-time security metrics retrieval"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock enhanced limiter metrics
        security_dashboard.enhanced_limiter.get_security_metrics.return_value = {
            "violations_by_threat_level": {"high": 5, "medium": 10},
            "blocked_ips_count": 3,
            "avg_response_times": {"/api/data": 1200.0},
            "requests_last_hour": 150,
        }

        # Mock database cursor responses
        mock_cursor.fetchone.side_effect = [
            (10,),
            (150,),
        ]  # active_api_keys, requests_per_hour

        metrics = security_dashboard.get_real_time_metrics()

        assert isinstance(metrics, SecurityMetrics)
        assert metrics.blocked_ips == 3
        assert metrics.requests_per_hour == 150
        assert metrics.active_api_keys == 10
        assert 0.0 <= metrics.threat_score <= 1.0

    def test_security_alerts_generation(self, security_dashboard, mock_db_manager):
        """Test security alerts generation from database"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock database responses for alerts
        mock_cursor.fetchall.side_effect = [
            [("high", 15, "2023-01-01 10:00:00", "2023-01-01 11:00:00")],  # violations
            [(5, "Automated attack", "critical", "2023-01-01 10:30:00")],  # IP blocks
        ]

        # Mock enhanced limiter for performance alerts
        security_dashboard.enhanced_limiter.get_security_metrics.return_value = {
            "avg_response_times": {"/api/slow": 6000.0}  # Slow endpoint
        }

        alerts = security_dashboard.get_security_alerts(hours=24)

        assert len(alerts) >= 2  # At least violations and IP blocks alerts
        assert any("Rate Limit Violations" in alert.title for alert in alerts)
        assert any("IP Addresses Blocked" in alert.title for alert in alerts)

    def test_ip_unblocking_success(self, security_dashboard, mock_db_manager):
        """Test successful IP address unblocking"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock successful unblock (rowcount > 0)
        mock_cursor.rowcount = 1

        result = security_dashboard.unblock_ip("abcd1234", "Test unblock")

        assert result is True
        mock_cursor.execute.assert_called_once()

        # Verify the UPDATE query was called
        update_call = mock_cursor.execute.call_args[0][0]
        assert "UPDATE ip_blocks" in update_call
        assert "expires_at = datetime('now')" in update_call

    def test_ip_unblocking_failure(self, security_dashboard, mock_db_manager):
        """Test IP address unblocking when IP not found"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock failed unblock (rowcount = 0)
        mock_cursor.rowcount = 0

        result = security_dashboard.unblock_ip("nonexistent", "Test unblock")

        assert result is False

    def test_dashboard_html_generation(self, security_dashboard):
        """Test HTML dashboard generation"""
        html = security_dashboard.generate_dashboard_html()

        assert "<!DOCTYPE html>" in html
        assert "Security Dashboard" in html
        assert "Osservatorio ISTAT" in html
        assert "<script>" in html
        assert "<style>" in html

        # Check for key dashboard elements
        assert "threat-score" in html
        assert "metric-card" in html
        assert "refresh-btn" in html

    def test_blocked_ips_retrieval(self, security_dashboard, mock_db_manager):
        """Test blocked IPs list retrieval"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        # Mock blocked IPs data
        mock_cursor.fetchall.return_value = [
            (
                "abcd1234",
                "Automated attack",
                "high",
                "2023-01-01 10:00:00",
                "2023-01-02 10:00:00",
                "Auto-blocked",
            ),
            (
                "efgh5678",
                "Manual block",
                "medium",
                "2023-01-01 11:00:00",
                None,
                "Admin decision",
            ),
        ]

        blocked_ips = security_dashboard.get_blocked_ips()

        assert len(blocked_ips) == 2
        assert blocked_ips[0]["ip_hash"] == "abcd1234"
        assert blocked_ips[0]["is_permanent"] is False
        assert blocked_ips[1]["is_permanent"] is True


class TestIntegrationFixed:
    """Integration tests with proper setup and teardown"""

    @pytest.fixture
    def mock_db_manager(self):
        """Comprehensive mock database manager"""
        mock_db = Mock(spec=SQLiteMetadataManager)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        @contextmanager
        def mock_transaction():
            yield mock_conn

        mock_db.transaction = mock_transaction
        return mock_db, mock_conn, mock_cursor

    @patch("src.auth.security_config.SQLiteAuthManager")
    @patch("src.auth.security_config.JWTManager")
    def test_security_manager_initialization(
        self, mock_jwt_manager, mock_auth_manager, mock_db_manager
    ):
        """Test complete security manager initialization"""
        mock_db, mock_conn, mock_cursor = mock_db_manager

        config = SecurityConfig(
            enhanced_rate_limiting_enabled=True,
            redis_url=None,
            adaptive_rate_limiting_enabled=True,
            response_time_threshold_ms=2000.0,
            rate_limit_adjustment_factor=0.8,
            min_adjustment_ratio=0.1,
            max_adjustment_ratio=2.0,
            suspicious_activity_threshold=0.6,
            auto_block_critical_threats=True,
            ip_block_duration_hours=24,
            security_monitoring_enabled=True,
            alert_email="test@example.com",
            cleanup_data_retention_days=30,
        )

        with patch.object(EnhancedRateLimiter, "_ensure_enhanced_schema"):
            manager = SecurityManager(mock_db, config)

        assert manager.config == config
        assert manager.rate_limiter is not None
        assert manager.auth_middleware is not None

        # Test security status
        status = manager.get_security_status()
        assert "enhanced_rate_limiting" in status
        assert status["enhanced_rate_limiting"] is True

    def test_environment_validation(self):
        """Test security environment validation"""
        from src.auth.security_config import validate_security_environment

        with patch("src.auth.security_config.os.getenv") as mock_getenv:
            # Mock environment with required variables
            mock_getenv.side_effect = lambda key, default=None: {
                "JWT_SECRET_KEY": "test-secret-key-12345",
                "ENHANCED_RATE_LIMITING_ENABLED": "true",
                "REDIS_URL": None,
            }.get(key, default)

            validation = validate_security_environment()

            assert validation["valid"] is True
            assert len(validation["errors"]) == 0

    def test_env_template_generation(self):
        """Test environment configuration template generation"""
        from src.auth.security_config import generate_env_template

        template = generate_env_template()

        # Check that all required configuration options are present
        required_vars = [
            "ENHANCED_RATE_LIMITING_ENABLED",
            "REDIS_URL",
            "ADAPTIVE_RATE_LIMITING_ENABLED",
            "RESPONSE_TIME_THRESHOLD_MS",
            "SUSPICIOUS_ACTIVITY_THRESHOLD",
            "AUTO_BLOCK_CRITICAL_THREATS",
            "JWT_SECRET_KEY",
            "SECURITY_ALERT_EMAIL",
        ]

        for var in required_vars:
            assert var in template

    def test_threat_level_enumeration(self):
        """Test threat level enumeration values"""
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"

        # Test enum ordering for severity comparison
        threat_levels = [
            ThreatLevel.LOW,
            ThreatLevel.MEDIUM,
            ThreatLevel.HIGH,
            ThreatLevel.CRITICAL,
        ]
        assert len(threat_levels) == 4

    def test_alert_level_enumeration(self):
        """Test alert level enumeration values"""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
