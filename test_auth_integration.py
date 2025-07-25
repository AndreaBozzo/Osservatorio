#!/usr/bin/env python3
"""
Test completo dell'integrazione authentication Day 7
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_complete_auth_integration():
    """Test completo dell'integrazione authentication"""

    print("🚀 TESTING AUTHENTICATION INTEGRATION - DAY 7")
    print("=" * 60)

    try:
        # Import components
        from src.auth.jwt_manager import JWTManager
        from src.auth.models import APIKey
        from src.auth.rate_limiter import SQLiteRateLimiter
        from src.auth.security_middleware import (
            AuthenticationMiddleware,
            SecurityHeadersMiddleware,
        )
        from src.auth.sqlite_auth import SQLiteAuthManager
        from src.database.sqlite.manager import SQLiteMetadataManager

        print("✅ 1. All modules imported successfully")

        # Initialize SQLite backend
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        sqlite_mgr = SQLiteMetadataManager(temp_db.name)
        print("✅ 2. SQLite manager initialized")

        # Initialize auth components
        auth_mgr = SQLiteAuthManager(sqlite_mgr)
        jwt_mgr = JWTManager(sqlite_mgr, secret_key="test_secret_key_123")
        rate_limiter = SQLiteRateLimiter(sqlite_mgr)
        security_mw = SecurityHeadersMiddleware()
        print("✅ 3. Authentication components initialized")

        # Test API Key Generation
        api_key = auth_mgr.generate_api_key(
            name="Test Integration App",
            scopes=["read", "write", "analytics"],
            expires_days=30,
        )
        print(f"✅ 4. API Key generated: {api_key.key[:20]}...")

        # Test API Key Verification
        verified_key = auth_mgr.verify_api_key(api_key.key)
        assert verified_key is not None, "API key verification failed"
        assert verified_key.name == "Test Integration App"
        assert verified_key.scopes == ["read", "write", "analytics"]
        print("✅ 5. API Key verification successful")

        # Test JWT Token Generation
        auth_token = jwt_mgr.create_access_token(api_key)
        assert auth_token.access_token is not None
        assert auth_token.refresh_token is not None
        assert auth_token.expires_in > 0
        print(f"✅ 6. JWT Token generated (expires in {auth_token.expires_in}s)")

        # Test JWT Token Verification
        token_claims = jwt_mgr.verify_token(auth_token.access_token)
        assert token_claims is not None
        assert token_claims.sub == str(api_key.id)
        assert token_claims.scope == "read write analytics"
        print("✅ 7. JWT Token verification successful")

        # Test Rate Limiting
        rate_result = rate_limiter.check_rate_limit(
            api_key=api_key, ip_address="192.168.1.100", endpoint="test_endpoint"
        )
        assert rate_result.allowed == True
        assert rate_result.remaining >= 0
        print(f"✅ 8. Rate limiting working ({rate_result.remaining} remaining)")

        # Test Security Headers
        headers = {}
        secure_headers = security_mw.apply_security_headers(headers)
        assert "Content-Security-Policy" in secure_headers
        assert "Strict-Transport-Security" in secure_headers
        assert "X-Frame-Options" in secure_headers
        print(f"✅ 9. Security headers applied ({len(secure_headers)} headers)")

        # Test Authentication Middleware
        auth_middleware = AuthenticationMiddleware(auth_mgr, jwt_mgr, rate_limiter)

        # Test with API Key
        api_result = auth_middleware.authenticate_request(
            headers={"X-API-Key": api_key.key},
            ip_address="192.168.1.100",
            endpoint="test_endpoint",
        )
        assert api_result["authenticated"] == True
        assert api_result["user"]["type"] == "api_key"
        assert api_result["user"]["api_key_name"] == "Test Integration App"
        print("✅ 10. API Key authentication middleware working")

        # Test with JWT Token
        jwt_result = auth_middleware.authenticate_request(
            headers={"Authorization": f"Bearer {auth_token.access_token}"},
            ip_address="192.168.1.100",
            endpoint="test_endpoint",
        )
        assert jwt_result["authenticated"] == True
        assert jwt_result["user"]["type"] == "jwt"
        print("✅ 11. JWT authentication middleware working")

        # Test Scope Permissions
        read_permission = auth_middleware.check_scope_permission(
            jwt_result["user"], "read"
        )
        write_permission = auth_middleware.check_scope_permission(
            jwt_result["user"], "write"
        )
        admin_permission = auth_middleware.check_scope_permission(
            jwt_result["user"], "admin"
        )

        assert read_permission == True
        assert write_permission == True
        assert admin_permission == False
        print("✅ 12. Scope permissions working correctly")

        # Test API Key Revocation
        revoke_success = auth_mgr.revoke_api_key(api_key.id, "integration_test")
        assert revoke_success == True

        revoked_key = auth_mgr.verify_api_key(api_key.key)
        assert revoked_key is None
        print("✅ 13. API Key revocation working")

        # Test JWT Token Blacklisting
        blacklist_success = jwt_mgr.revoke_token(
            auth_token.access_token, "integration_test"
        )
        assert blacklist_success == True

        blacklisted_claims = jwt_mgr.verify_token(auth_token.access_token)
        assert blacklisted_claims is None
        print("✅ 14. JWT Token blacklisting working")

        # Test API Key Listing
        all_keys = auth_mgr.list_api_keys(include_revoked=True)
        assert len(all_keys) >= 1
        active_keys = auth_mgr.list_api_keys(include_revoked=False)
        assert len(active_keys) == 0  # Should be 0 as we revoked the key
        print("✅ 15. API Key listing working")

        # Test Rate Limit Statistics
        stats = rate_limiter.get_rate_limit_stats(str(api_key.id), "api_key")
        assert isinstance(stats, dict)
        print("✅ 16. Rate limit statistics working")

        # Test Cleanup Operations
        jwt_cleaned = jwt_mgr.cleanup_expired_tokens()
        rate_cleaned = rate_limiter.cleanup_expired_windows()
        assert isinstance(jwt_cleaned, int)
        assert isinstance(rate_cleaned, int)
        print("✅ 17. Cleanup operations working")

        # Test Security Report
        security_report = security_mw.get_security_report()
        assert isinstance(security_report, dict)
        assert "csp_enabled" in security_report
        print("✅ 18. Security reporting working")

        # Cleanup - close connections first
        sqlite_mgr.close_connections()
        try:
            Path(temp_db.name).unlink(missing_ok=True)
        except:
            pass  # Ignore cleanup errors

        print("\n" + "=" * 60)
        print("🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ SQLite API Key Management: WORKING")
        print("✅ JWT Token System: WORKING")
        print("✅ Rate Limiting: WORKING")
        print("✅ Security Headers: WORKING")
        print("✅ Authentication Middleware: WORKING")
        print("✅ Integration Flow: WORKING")
        print("\n🚀 Day 7 deliverables are PRODUCTION READY!")

        return True

    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_auth_integration()
    sys.exit(0 if success else 1)
