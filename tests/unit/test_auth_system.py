"""
Authentication System Test Suite for Osservatorio ISTAT Data Platform

Comprehensive tests for:
- SQLite API key management
- JWT token generation and validation
- Rate limiting with SQLite backend
- Security headers middleware
- Authentication middleware integration

Test Categories:
- Unit tests for individual components
- Integration tests for full authentication flow
- Security tests for attack scenarios
- Performance tests for rate limiting
"""

import hashlib
import secrets
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.auth.jwt_manager import JWTManager

# Import authentication components
from src.auth.models import APIKey, AuthToken, TokenClaims
from src.auth.rate_limiter import RateLimitConfig, SQLiteRateLimiter
from src.auth.security_middleware import (
    AuthenticationMiddleware,
    SecurityHeadersMiddleware,
)
from src.auth.sqlite_auth import SQLiteAuthManager
from src.database.sqlite.manager import SQLiteMetadataManager


class TestAPIKeyManagement(unittest.TestCase):
    """Test SQLite API key management"""

    def setUp(self):
        """Set up test database and auth manager"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.sqlite_manager = SQLiteMetadataManager(self.temp_db.name)
        self.auth_manager = SQLiteAuthManager(self.sqlite_manager)

    def tearDown(self):
        """Clean up test database"""
        # Close database connections properly
        self.sqlite_manager.close_connections()

        # Wait for Windows to release file locks
        time.sleep(0.1)

        # Retry file deletion with timeout
        for attempt in range(5):
            try:
                Path(self.temp_db.name).unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.2)
                else:
                    # If we can't delete, at least log it
                    print(f"Warning: Could not delete {self.temp_db.name}")

    def test_generate_api_key_success(self):
        """Test successful API key generation"""
        name = "Test App"
        scopes = ["read", "write"]

        api_key = self.auth_manager.generate_api_key(name, scopes)

        self.assertIsNotNone(api_key)
        self.assertEqual(api_key.name, name)
        self.assertEqual(api_key.scopes, scopes)
        self.assertTrue(api_key.key.startswith("osv_"))
        self.assertTrue(api_key.is_active)
        self.assertIsNotNone(api_key.key_hash)
        self.assertNotEqual(api_key.key, api_key.key_hash)  # Key should be hashed

    def test_generate_api_key_invalid_scopes(self):
        """Test API key generation with invalid scopes"""
        with self.assertRaises(ValueError):
            self.auth_manager.generate_api_key("Test", ["invalid_scope"])

    def test_generate_api_key_with_expiration(self):
        """Test API key generation with expiration"""
        api_key = self.auth_manager.generate_api_key("Test", ["read"], expires_days=30)

        self.assertIsNotNone(api_key.expires_at)
        expected_expiry = datetime.now() + timedelta(days=30)
        self.assertAlmostEqual(
            api_key.expires_at.timestamp(),
            expected_expiry.timestamp(),
            delta=60,  # Within 1 minute
        )

    def test_verify_api_key_success(self):
        """Test successful API key verification"""
        # Generate key
        api_key = self.auth_manager.generate_api_key("Test", ["read"])
        original_key = api_key.key

        # Verify key
        verified_key = self.auth_manager.verify_api_key(original_key)

        self.assertIsNotNone(verified_key)
        self.assertEqual(verified_key.id, api_key.id)
        self.assertEqual(verified_key.name, api_key.name)
        self.assertEqual(verified_key.scopes, api_key.scopes)

    def test_verify_api_key_invalid(self):
        """Test verification of invalid API key"""
        invalid_key = "osv_invalid_key_123456789"

        verified_key = self.auth_manager.verify_api_key(invalid_key)

        self.assertIsNone(verified_key)

    def test_verify_api_key_wrong_prefix(self):
        """Test verification of key with wrong prefix"""
        wrong_key = "wrong_prefix_123456789"

        verified_key = self.auth_manager.verify_api_key(wrong_key)

        self.assertIsNone(verified_key)

    def test_verify_expired_api_key(self):
        """Test verification of expired API key"""
        # Generate key that expires immediately
        api_key = self.auth_manager.generate_api_key("Test", ["read"], expires_days=0)

        # Wait a moment and verify (should fail)
        import time

        time.sleep(0.1)

        verified_key = self.auth_manager.verify_api_key(api_key.key)

        self.assertIsNone(verified_key)

    def test_revoke_api_key(self):
        """Test API key revocation"""
        # Generate and verify key works
        api_key = self.auth_manager.generate_api_key("Test", ["read"])
        self.assertIsNotNone(self.auth_manager.verify_api_key(api_key.key))

        # Revoke key
        success = self.auth_manager.revoke_api_key(api_key.id, "test_revocation")
        self.assertTrue(success)

        # Verify key no longer works
        verified_key = self.auth_manager.verify_api_key(api_key.key)
        self.assertIsNone(verified_key)

    def test_list_api_keys(self):
        """Test listing API keys"""
        # Create multiple keys
        key1 = self.auth_manager.generate_api_key("App1", ["read"])
        key2 = self.auth_manager.generate_api_key("App2", ["write"])

        # List active keys
        active_keys = self.auth_manager.list_api_keys(include_revoked=False)
        self.assertEqual(len(active_keys), 2)

        # Revoke one key
        self.auth_manager.revoke_api_key(key1.id)

        # List active keys (should be 1)
        active_keys = self.auth_manager.list_api_keys(include_revoked=False)
        self.assertEqual(len(active_keys), 1)

        # List all keys (should be 2)
        all_keys = self.auth_manager.list_api_keys(include_revoked=True)
        self.assertEqual(len(all_keys), 2)

    def test_scope_permission_check(self):
        """Test scope permission checking"""
        # Create key with specific scopes
        api_key = APIKey(scopes=["read", "analytics"], is_active=True)

        # Test valid scopes
        self.assertTrue(self.auth_manager.check_scope_permission(api_key, "read"))
        self.assertTrue(self.auth_manager.check_scope_permission(api_key, "analytics"))

        # Test invalid scope
        self.assertFalse(self.auth_manager.check_scope_permission(api_key, "write"))

        # Test admin scope (should grant all permissions)
        admin_key = APIKey(scopes=["admin"], is_active=True)
        self.assertTrue(self.auth_manager.check_scope_permission(admin_key, "write"))
        self.assertTrue(self.auth_manager.check_scope_permission(admin_key, "read"))

        # Test inactive key
        inactive_key = APIKey(scopes=["read"], is_active=False)
        self.assertFalse(self.auth_manager.check_scope_permission(inactive_key, "read"))


class TestJWTManager(unittest.TestCase):
    """Test JWT token management"""

    def setUp(self):
        """Set up test database and JWT manager"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.sqlite_manager = SQLiteMetadataManager(self.temp_db.name)
        self.jwt_manager = JWTManager(self.sqlite_manager, secret_key="test_secret_key")

    def tearDown(self):
        """Clean up test database"""
        # Close database connections properly
        self.sqlite_manager.close_connections()

        # Wait for Windows to release file locks
        time.sleep(0.1)

        # Retry file deletion with timeout
        for attempt in range(5):
            try:
                Path(self.temp_db.name).unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.2)
                else:
                    # If we can't delete, at least log it
                    print(f"Warning: Could not delete {self.temp_db.name}")

    def test_create_access_token(self):
        """Test JWT access token creation"""
        api_key = APIKey(id=1, name="Test App", scopes=["read", "write"])

        auth_token = self.jwt_manager.create_access_token(api_key)

        self.assertIsNotNone(auth_token.access_token)
        self.assertEqual(auth_token.token_type, "bearer")
        self.assertGreater(auth_token.expires_in, 0)
        self.assertIsNotNone(auth_token.refresh_token)
        self.assertEqual(auth_token.scope, "read write")

    def test_verify_token_success(self):
        """Test successful JWT token verification"""
        api_key = APIKey(id=1, name="Test App", scopes=["read"])

        # Create token
        auth_token = self.jwt_manager.create_access_token(api_key)

        # Verify token
        claims = self.jwt_manager.verify_token(auth_token.access_token)

        self.assertIsNotNone(claims)
        self.assertEqual(claims.sub, "1")
        self.assertEqual(claims.iss, "osservatorio-istat")
        self.assertEqual(claims.aud, "osservatorio-api")
        self.assertEqual(claims.scope, "read")
        self.assertEqual(claims.api_key_name, "Test App")

    def test_verify_token_invalid(self):
        """Test verification of invalid JWT token"""
        invalid_token = "invalid.jwt.token"

        claims = self.jwt_manager.verify_token(invalid_token)

        self.assertIsNone(claims)

    def test_verify_token_expired(self):
        """Test verification of expired JWT token"""
        # Create JWT manager with very short expiration
        short_jwt = JWTManager(self.sqlite_manager, secret_key="test_secret")
        short_jwt.access_token_expire_minutes = 0.01  # ~0.6 seconds

        api_key = APIKey(id=1, name="Test", scopes=["read"])
        auth_token = short_jwt.create_access_token(api_key)

        # Wait for expiration
        import time

        time.sleep(1)

        # Verify expired token
        claims = short_jwt.verify_token(auth_token.access_token)

        self.assertIsNone(claims)

    def test_revoke_token(self):
        """Test JWT token revocation (blacklisting)"""
        api_key = APIKey(id=1, name="Test", scopes=["read"])
        auth_token = self.jwt_manager.create_access_token(api_key)

        # Verify token works initially
        claims = self.jwt_manager.verify_token(auth_token.access_token)
        self.assertIsNotNone(claims)

        # Revoke token
        success = self.jwt_manager.revoke_token(
            auth_token.access_token, "test_revocation"
        )
        self.assertTrue(success)

        # Verify token no longer works
        claims = self.jwt_manager.verify_token(auth_token.access_token)
        self.assertIsNone(claims)

    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens"""
        # Create some tokens (refresh tokens will be created)
        api_key = APIKey(id=1, name="Test", scopes=["read"])
        self.jwt_manager.create_access_token(api_key)
        self.jwt_manager.create_access_token(api_key)

        # Run cleanup (should find no expired tokens yet)
        cleaned = self.jwt_manager.cleanup_expired_tokens()

        # Should return number of cleaned tokens (0 for non-expired)
        self.assertIsInstance(cleaned, int)


class TestRateLimiter(unittest.TestCase):
    """Test SQLite rate limiter"""

    def setUp(self):
        """Set up test database and rate limiter"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.sqlite_manager = SQLiteMetadataManager(self.temp_db.name)
        self.rate_limiter = SQLiteRateLimiter(self.sqlite_manager)

        # Create test API key
        self.test_api_key = APIKey(
            id=1, name="Test", scopes=["read"], is_active=True, rate_limit=10
        )

    def tearDown(self):
        """Clean up test database"""
        # Close database connections properly
        self.sqlite_manager.close_connections()

        # Wait for Windows to release file locks
        time.sleep(0.1)

        # Retry file deletion with timeout
        for attempt in range(5):
            try:
                Path(self.temp_db.name).unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.2)
                else:
                    # If we can't delete, at least log it
                    print(f"Warning: Could not delete {self.temp_db.name}")

    def test_rate_limit_allow_first_request(self):
        """Test that first request is allowed"""
        result = self.rate_limiter.check_rate_limit(
            api_key=self.test_api_key, endpoint="test_endpoint"
        )

        self.assertTrue(result.allowed)
        self.assertGreater(result.limit, 0)
        self.assertGreaterEqual(result.remaining, 0)
        self.assertIsInstance(result.reset_time, datetime)

    def test_rate_limit_headers(self):
        """Test rate limit headers generation"""
        result = self.rate_limiter.check_rate_limit(
            api_key=self.test_api_key, endpoint="test_endpoint"
        )

        headers = result.to_headers()

        self.assertIn("X-RateLimit-Limit", headers)
        self.assertIn("X-RateLimit-Remaining", headers)
        self.assertIn("X-RateLimit-Reset", headers)

    def test_rate_limit_ip_based(self):
        """Test IP-based rate limiting"""
        ip_address = "192.168.1.100"

        # First request should be allowed
        result1 = self.rate_limiter.check_rate_limit(
            ip_address=ip_address, endpoint="test_endpoint"
        )
        self.assertTrue(result1.allowed)

        # Second request should also be allowed (within limits)
        result2 = self.rate_limiter.check_rate_limit(
            ip_address=ip_address, endpoint="test_endpoint"
        )
        self.assertTrue(result2.allowed)

    def test_rate_limit_different_endpoints(self):
        """Test rate limiting across different endpoints"""
        # Requests to different endpoints should be tracked separately
        result1 = self.rate_limiter.check_rate_limit(
            api_key=self.test_api_key, endpoint="endpoint1"
        )

        result2 = self.rate_limiter.check_rate_limit(
            api_key=self.test_api_key, endpoint="endpoint2"
        )

        self.assertTrue(result1.allowed)
        self.assertTrue(result2.allowed)

    def test_rate_limit_cleanup(self):
        """Test rate limit window cleanup"""
        # Make some requests to create rate limit records
        self.rate_limiter.check_rate_limit(
            api_key=self.test_api_key, endpoint="test_endpoint"
        )

        # Run cleanup
        cleaned = self.rate_limiter.cleanup_expired_windows()

        # Should return number of cleaned windows
        self.assertIsInstance(cleaned, int)

    def test_rate_limit_stats(self):
        """Test rate limit statistics"""
        # Make a request to create data
        self.rate_limiter.check_rate_limit(
            api_key=self.test_api_key, endpoint="test_endpoint"
        )

        # Get stats
        stats = self.rate_limiter.get_rate_limit_stats("1", "api_key")

        self.assertIsInstance(stats, dict)
        self.assertIn("minute", stats)


class TestSecurityMiddleware(unittest.TestCase):
    """Test security headers middleware"""

    def setUp(self):
        """Set up security middleware"""
        self.middleware = SecurityHeadersMiddleware()

    def test_apply_security_headers(self):
        """Test security headers application"""
        headers = {}

        result_headers = self.middleware.apply_security_headers(headers)

        # Check for key security headers
        self.assertIn("Content-Security-Policy", result_headers)
        self.assertIn("Strict-Transport-Security", result_headers)
        self.assertIn("X-Frame-Options", result_headers)
        self.assertIn("X-Content-Type-Options", result_headers)
        self.assertIn("X-XSS-Protection", result_headers)
        self.assertIn("Referrer-Policy", result_headers)

    def test_apply_cors_headers(self):
        """Test CORS headers application"""
        headers = {}
        origin = "https://localhost:3000"

        result_headers = self.middleware.apply_cors_headers(headers, origin)

        # Check for CORS headers
        self.assertIn("Access-Control-Allow-Origin", result_headers)
        self.assertIn("Access-Control-Allow-Methods", result_headers)
        self.assertIn("Access-Control-Allow-Headers", result_headers)

    def test_security_report(self):
        """Test security configuration report"""
        report = self.middleware.get_security_report()

        self.assertIsInstance(report, dict)
        self.assertIn("csp_enabled", report)
        self.assertIn("hsts_enabled", report)
        self.assertIn("cors_enabled", report)


class TestAuthenticationIntegration(unittest.TestCase):
    """Test full authentication integration"""

    def setUp(self):
        """Set up full authentication stack"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        # Initialize components
        self.sqlite_manager = SQLiteMetadataManager(self.temp_db.name)
        self.auth_manager = SQLiteAuthManager(self.sqlite_manager)
        self.jwt_manager = JWTManager(self.sqlite_manager, secret_key="test_secret")
        self.rate_limiter = SQLiteRateLimiter(self.sqlite_manager)

        # Initialize middleware
        self.auth_middleware = AuthenticationMiddleware(
            self.auth_manager, self.jwt_manager, self.rate_limiter
        )

        # Create test API key
        self.test_api_key = self.auth_manager.generate_api_key(
            "Integration Test", ["read", "write"]
        )

    def tearDown(self):
        """Clean up test database"""
        # Close database connections properly
        self.sqlite_manager.close_connections()

        # Wait for Windows to release file locks
        time.sleep(0.1)

        # Retry file deletion with timeout
        for attempt in range(5):
            try:
                Path(self.temp_db.name).unlink(missing_ok=True)
                break
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.2)
                else:
                    # If we can't delete, at least log it
                    print(f"Warning: Could not delete {self.temp_db.name}")

    def test_full_api_key_authentication_flow(self):
        """Test complete API key authentication flow"""
        headers = {"X-API-Key": self.test_api_key.key, "User-Agent": "Test Client"}

        # Authenticate request
        result = self.auth_middleware.authenticate_request(
            headers, "192.168.1.100", "test_endpoint"
        )

        # Verify authentication successful
        self.assertTrue(result["authenticated"])
        self.assertIsNotNone(result["user"])
        self.assertEqual(result["user"]["type"], "api_key")
        self.assertEqual(result["user"]["api_key_name"], "Integration Test")

        # Verify rate limiting info included
        self.assertIn("rate_limit", result)
        self.assertIn("rate_limit_headers", result)

    def test_full_jwt_authentication_flow(self):
        """Test complete JWT authentication flow"""
        # Generate JWT token
        auth_token = self.jwt_manager.create_access_token(
            APIKey(
                id=self.test_api_key.id,
                name=self.test_api_key.name,
                scopes=self.test_api_key.scopes,
            )
        )

        headers = {
            "Authorization": f"Bearer {auth_token.access_token}",
            "User-Agent": "Test Client",
        }

        # Authenticate request
        result = self.auth_middleware.authenticate_request(
            headers, "192.168.1.100", "test_endpoint"
        )

        # Verify authentication successful
        self.assertTrue(result["authenticated"])
        self.assertIsNotNone(result["user"])
        self.assertEqual(result["user"]["type"], "jwt")
        self.assertEqual(result["user"]["api_key_name"], "Integration Test")

    def test_scope_permission_middleware(self):
        """Test scope permission checking in middleware"""
        # Create user with limited scopes
        user = {"type": "api_key", "scopes": ["read"], "api_key_name": "Read Only"}

        # Test allowed scope
        self.assertTrue(self.auth_middleware.check_scope_permission(user, "read"))

        # Test denied scope
        self.assertFalse(self.auth_middleware.check_scope_permission(user, "write"))

    def test_authentication_failure_scenarios(self):
        """Test various authentication failure scenarios"""
        # Test with no credentials
        result1 = self.auth_middleware.authenticate_request(
            {}, "192.168.1.100", "test_endpoint"
        )
        self.assertFalse(result1["authenticated"])

        # Test with invalid API key
        result2 = self.auth_middleware.authenticate_request(
            {"X-API-Key": "invalid_key"}, "192.168.1.100", "test_endpoint"
        )
        self.assertFalse(result2["authenticated"])

        # Test with invalid JWT token
        result3 = self.auth_middleware.authenticate_request(
            {"Authorization": "Bearer invalid_token"}, "192.168.1.100", "test_endpoint"
        )
        self.assertFalse(result3["authenticated"])


if __name__ == "__main__":
    # Run specific test categories
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "security":
        # Run only security-focused tests
        suite = unittest.TestSuite()
        suite.addTest(TestAPIKeyManagement("test_verify_api_key_invalid"))
        suite.addTest(TestAPIKeyManagement("test_verify_expired_api_key"))
        suite.addTest(TestJWTManager("test_verify_token_expired"))
        suite.addTest(TestJWTManager("test_revoke_token"))
        suite.addTest(TestSecurityMiddleware("test_apply_security_headers"))
        suite.addTest(
            TestAuthenticationIntegration("test_authentication_failure_scenarios")
        )

        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        # Run all tests
        unittest.main(verbosity=2)
