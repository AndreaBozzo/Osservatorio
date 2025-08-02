"""
JWT Token Generator for Performance Testing

This module generates valid JWT tokens for performance testing by:
- Reading existing API keys from SQLite database
- Using the actual JWT manager to create valid tokens
- Providing tokens with appropriate scopes for testing

Usage:
    # Issue #84: Run from project root
    python -m tests.performance.load_testing.jwt_token_generator
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

try:
    # Try direct imports when run as module
    from src.auth.jwt_manager import JWTManager
    from src.auth.models import APIKey
    from src.database.sqlite.manager import get_metadata_manager
    from src.utils.logger import get_logger
except ImportError:
    # Fallback for legacy usage
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.auth.jwt_manager import JWTManager
    from src.auth.models import APIKey
    from src.database.sqlite.manager import get_metadata_manager
    from src.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceJWTGenerator:
    """JWT token generator for performance testing."""

    def __init__(self):
        """Initialize JWT generator with SQLite backend."""
        try:
            self.metadata_manager = get_metadata_manager()
            # Use consistent JWT secret key for performance testing
            jwt_secret = os.environ.get(
                "JWT_SECRET_KEY", "performance_test_secret_key_for_testing_12345"
            )
            self.jwt_manager = JWTManager(self.metadata_manager, secret_key=jwt_secret)
            logger.info("JWT generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize JWT generator: {e}")
            raise

    def get_available_api_keys(self) -> list[dict[str, Any]]:
        """Get all available API keys from database."""
        try:
            with self.metadata_manager.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, service_name, api_key_hash, is_active,
                           rate_limit, expires_at, created_at, last_used, usage_count
                    FROM api_credentials
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """
                )

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                api_keys = []
                for row in rows:
                    api_key_data = dict(zip(columns, row))
                    api_keys.append(api_key_data)

                logger.info(f"Found {len(api_keys)} active API keys")
                return api_keys

        except Exception as e:
            logger.error(f"Failed to get API keys: {e}")
            return []

    def create_test_api_key_if_needed(self) -> Optional[dict[str, Any]]:
        """Create a test API key for performance testing if none exist."""
        try:
            # Check if any performance test keys exist
            with self.metadata_manager.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id FROM api_credentials
                    WHERE service_name LIKE 'performance_test%'
                    AND is_active = 1
                """
                )

                if cursor.fetchone():
                    logger.info("Performance test API key already exists")
                    return None

                # Create new performance test API key
                test_key_data = {
                    "service_name": "performance_test_key",
                    "api_key_hash": "perf_test_hash_"
                    + datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "is_active": True,
                    "rate_limit": 1000,  # High rate limit for testing
                    "expires_at": datetime.now() + timedelta(days=30),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "usage_count": 0,
                }

                cursor.execute(
                    """
                    INSERT INTO api_credentials
                    (service_name, api_key_hash, is_active, rate_limit, expires_at, created_at, updated_at, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        test_key_data["service_name"],
                        test_key_data["api_key_hash"],
                        test_key_data["is_active"],
                        test_key_data["rate_limit"],
                        test_key_data["expires_at"],
                        test_key_data["created_at"],
                        test_key_data["updated_at"],
                        test_key_data["usage_count"],
                    ),
                )

                test_key_data["id"] = cursor.lastrowid
                conn.commit()

                logger.info(
                    f"Created performance test API key with ID: {test_key_data['id']}"
                )
                return test_key_data

        except Exception as e:
            logger.error(f"Failed to create test API key: {e}")
            return None

    def generate_jwt_token(
        self,
        api_key_id: Optional[int] = None,
        scopes: Optional[list[str]] = None,
        rate_limit: int = 1000,
    ) -> Optional[str]:
        """Generate a JWT token for performance testing.

        Args:
            api_key_id: Specific API key ID to use (if None, uses first available)
            scopes: Token scopes (default: ['read', 'datasets'])
            rate_limit: Rate limit for the token

        Returns:
            JWT token string if successful, None otherwise
        """
        try:
            # Get API keys if no specific ID provided
            if api_key_id is None:
                api_keys = self.get_available_api_keys()
                if not api_keys:
                    # Try to create a test key
                    test_key = self.create_test_api_key_if_needed()
                    if test_key:
                        api_key_id = test_key["id"]
                    else:
                        logger.error(
                            "No API keys available and couldn't create test key"
                        )
                        return None
                else:
                    api_key_id = api_keys[0]["id"]

            # Default scopes for performance testing
            if scopes is None:
                scopes = ["read", "datasets", "odata"]

            # Create APIKey object
            api_key = APIKey(
                id=api_key_id,
                name=f"performance_test_{api_key_id}",
                scopes=scopes,
                rate_limit=rate_limit,
                is_active=True,
            )

            # Generate JWT token
            auth_token = self.jwt_manager.create_access_token(api_key)

            logger.info(
                f"Generated JWT token for API key {api_key_id} with scopes: {scopes}"
            )
            logger.debug(f"Token expires in {auth_token.expires_in} seconds")

            return auth_token.access_token

        except Exception as e:
            logger.error(f"Failed to generate JWT token: {e}")
            return None

    def generate_multiple_tokens(
        self, count: int = 5, scopes: Optional[list[str]] = None
    ) -> list[str]:
        """Generate multiple JWT tokens for concurrent testing.

        Args:
            count: Number of tokens to generate
            scopes: Token scopes

        Returns:
            List of JWT token strings
        """
        tokens = []

        try:
            api_keys = self.get_available_api_keys()

            # Ensure we have at least one API key
            if not api_keys:
                test_key = self.create_test_api_key_if_needed()
                if test_key:
                    api_keys = [test_key]

            if not api_keys:
                logger.error("No API keys available for token generation")
                return tokens

            # Generate tokens, cycling through available API keys
            for i in range(count):
                api_key_data = api_keys[i % len(api_keys)]
                token = self.generate_jwt_token(
                    api_key_id=api_key_data["id"], scopes=scopes
                )
                if token:
                    tokens.append(token)

            logger.info(f"Generated {len(tokens)} JWT tokens for performance testing")
            return tokens

        except Exception as e:
            logger.error(f"Failed to generate multiple tokens: {e}")
            return tokens

    def verify_token(self, token: str) -> bool:
        """Verify that a generated token is valid.

        Args:
            token: JWT token to verify

        Returns:
            True if token is valid, False otherwise
        """
        try:
            token_claims = self.jwt_manager.verify_token(token)
            return token_claims is not None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return False

    def get_token_info(self, token: str) -> Optional[dict[str, Any]]:
        """Get information about a JWT token.

        Args:
            token: JWT token to analyze

        Returns:
            Token information dict if valid, None otherwise
        """
        try:
            token_claims = self.jwt_manager.verify_token(token)
            if not token_claims:
                return None

            return {
                "api_key_id": token_claims.sub,
                "api_key_name": token_claims.api_key_name,
                "scopes": token_claims.scope.split(),
                "rate_limit": token_claims.rate_limit,
                "expires_at": token_claims.exp.isoformat(),
                "issued_at": token_claims.iat.isoformat(),
                "issuer": token_claims.iss,
                "audience": token_claims.aud,
            }

        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None

    def close(self):
        """Close database connections."""
        try:
            if hasattr(self.metadata_manager, "close"):
                self.metadata_manager.close()
        except Exception as e:
            logger.error(f"Error closing JWT generator: {e}")


def main():
    """Test the JWT generator."""
    print("🔑 Testing JWT Token Generator...")

    generator = PerformanceJWTGenerator()

    try:
        # Show available API keys
        api_keys = generator.get_available_api_keys()
        print(f"\n📋 Found {len(api_keys)} API keys:")
        for key in api_keys:
            print(
                f"  - ID: {key['id']}, Name: {key['service_name']}, Rate Limit: {key['rate_limit']}"
            )

        # Generate a test token
        print("\n🎫 Generating JWT token...")
        token = generator.generate_jwt_token()

        if token:
            print("✅ Token generated successfully!")
            print(f"Token (first 50 chars): {token[:50]}...")

            # Verify the token
            is_valid = generator.verify_token(token)
            print(f"🔍 Token validation: {'✅ Valid' if is_valid else '❌ Invalid'}")

            # Get token info
            token_info = generator.get_token_info(token)
            if token_info:
                print("\n📊 Token Information:")
                for key, value in token_info.items():
                    print(f"  - {key}: {value}")

            # Test multiple tokens
            print("\n🔄 Generating multiple tokens...")
            tokens = generator.generate_multiple_tokens(count=3)
            print(f"Generated {len(tokens)} tokens for concurrent testing")

        else:
            print("❌ Failed to generate token")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        generator.close()
        print("\n✅ JWT generator test completed!")


if __name__ == "__main__":
    main()
