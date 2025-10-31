"""
JWT Token Manager with Refresh Token Support

JWT token generation and validation:
- HS256 JWT token support
- Access and refresh token generation
- Token expiration and refresh
- Token blacklisting for logout
- Claims validation
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

try:
    import jwt
except ImportError:
    raise ImportError("JWT dependencies not installed. Run: pip install PyJWT")

from src.utils.config import get_config

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .models import APIKey, AuthToken, TokenClaims

logger = get_logger(__name__)


class JWTManager:
    """JWT token manager with refresh token support"""

    # Default token configuration
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days

    # JWT algorithm
    ALGORITHM_HS256 = "HS256"

    def __init__(
        self,
        db_path: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """Initialize JWT manager with refresh token support

        Args:
            db_path: Optional database path (kept for compatibility)
            secret_key: JWT signing secret (if None, will generate or load from config)
        """
        self.algorithm = self.ALGORITHM_HS256
        self.logger = logger

        # Initialize secret key
        self._init_secret_key(secret_key)

        # Load configuration
        config = get_config()
        self.access_token_expire_minutes = config.get(
            "jwt_access_token_expire_minutes", self.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.refresh_token_expire_days = config.get(
            "jwt_refresh_token_expire_days", self.DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        # In-memory token blacklist for logout
        self._blacklisted_tokens = set()

        logger.info("JWT Manager initialized with refresh token support")

    def _init_secret_key(self, secret_key: Optional[str]):
        """Initialize HMAC secret key for HS256"""
        if secret_key:
            self.secret_key = secret_key
        else:
            # Try to load from config or generate new one
            config = get_config()
            self.secret_key = config.get("jwt_secret_key")

            if not self.secret_key:
                # Generate cryptographically secure secret
                self.secret_key = secrets.token_urlsafe(64)
                logger.warning(
                    "Generated new JWT secret key. Set JWT_SECRET_KEY environment variable for production."
                )

    def create_access_token(
        self, api_key: APIKey, custom_claims: Optional[dict] = None
    ) -> AuthToken:
        """Create simplified JWT access token for API key

        Args:
            api_key: APIKey object to create token for
            custom_claims: Additional claims to include (optional)

        Returns:
            AuthToken with access token only (no refresh token for MVP)
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=self.access_token_expire_minutes)

            # Build simplified token claims
            claims = {
                "sub": str(api_key.id),  # Subject (API key ID)
                "iss": "osservatorio-istat",  # Issuer
                "aud": "osservatorio-api",  # Audience
                "exp": expires_at,  # Expiration
                "iat": now,  # Issued at
                "api_key_name": api_key.name,
                "jti": secrets.token_urlsafe(16),  # JWT ID for tracking
            }

            # Add custom claims if provided
            if custom_claims:
                claims.update(custom_claims)

            # Create JWT token
            access_token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

            # Create AuthToken object (no refresh token for MVP)
            token = AuthToken(
                access_token=access_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                scope=" ".join(api_key.scopes) if api_key.scopes else "read",
            )

            logger.debug(f"Access token created for API key: {api_key.name}")
            return token

        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise

    def create_refresh_token(
        self, user_id: str, username: str, scopes: Optional[list] = None
    ) -> str:
        """Create refresh token with longer expiration

        Args:
            user_id: User identifier
            username: Username (email)
            scopes: Optional list of scopes

        Returns:
            JWT refresh token string
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(days=self.refresh_token_expire_days)

            claims = {
                "sub": user_id,
                "username": username,
                "email": username,
                "user_type": "user",
                "token_type": "refresh",
                "exp": expires_at,
                "iat": now,
                "iss": "osservatorio-istat",
                "scopes": scopes or ["read"],
                "jti": secrets.token_urlsafe(16),
            }

            token = jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Refresh token created for: {username}")
            return token

        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise

    def verify_refresh_token(self, token: str) -> Optional[dict]:
        """Verify refresh token and return user info

        Args:
            token: JWT refresh token string

        Returns:
            Dict with user info if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning("Refresh token is blacklisted")
                return None

            # Verify it's a refresh token
            if payload.get("token_type") != "refresh":
                logger.warning("Token is not a refresh token")
                return None

            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "scopes": payload.get("scopes", ["read"]),
            }
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None
        except Exception as e:
            logger.error(f"Refresh token verification failed: {e}")
            return None

    def verify_token(self, token: str) -> Optional[TokenClaims]:
        """Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            TokenClaims if token is valid, None if invalid/expired
        """
        try:
            # Decode and verify token (MVP: disable audience validation for simplicity)
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False},  # Disable audience verification for MVP
            )

            # Check if token is blacklisted (logout invalidation)
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning("Token is blacklisted (logged out)")
                return None

            # Extract claims (fixed field names for TokenClaims model)
            token_claims = TokenClaims(
                sub=payload.get("sub"),
                iss=payload.get("iss", "osservatorio-istat"),
                aud=payload.get("aud", "osservatorio-api"),
                exp=datetime.fromtimestamp(payload.get("exp", 0))
                if payload.get("exp")
                else None,
                iat=datetime.fromtimestamp(payload.get("iat", 0))
                if payload.get("iat")
                else None,
                scope=payload.get("scope", "read"),
                api_key_name=payload.get("api_key_name"),
                email=payload.get("email"),
                user_type=payload.get("user_type", "api_key"),
            )

            logger.debug(
                f"Token verified successfully for: {token_claims.api_key_name}"
            )
            return token_claims

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    def create_token_for_user(
        self, user_id: str, username: str, scopes: Optional[list] = None
    ) -> dict:
        """Create access and refresh tokens for user authentication

        Args:
            user_id: User identifier
            username: Username (email)
            scopes: Optional list of scopes

        Returns:
            Dict with access_token and refresh_token
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=self.access_token_expire_minutes)

            # Create access token
            access_claims = {
                "sub": user_id,
                "username": username,
                "email": username,  # username is email for users
                "user_type": "user",
                "token_type": "access",
                "exp": expires_at,
                "iat": now,
                "iss": "osservatorio-istat",
                "scopes": scopes or ["read"],
                "jti": secrets.token_urlsafe(16),
            }

            access_token = jwt.encode(access_claims, self.secret_key, algorithm=self.algorithm)

            # Create refresh token
            refresh_token = self.create_refresh_token(user_id, username, scopes)

            logger.debug(f"User tokens created for: {username}")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
            }

        except Exception as e:
            logger.error(f"Failed to create user tokens: {e}")
            raise

    def verify_user_token(self, token: str) -> Optional[dict]:
        """Verify user token and return user info

        Args:
            token: JWT token string

        Returns:
            Dict with user info if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "scopes": payload.get("scopes", ["read"]),
                "exp": payload.get("exp"),
            }
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
        except Exception as e:
            logger.error(f"User token verification failed: {e}")
            return None

    def get_token_info(self, token: str) -> Optional[dict]:
        """Get basic token information without full verification

        Args:
            token: JWT token string

        Returns:
            Dict with token info if decodable, None otherwise
        """
        try:
            # Decode without verification to get info
            payload = jwt.decode(token, options={"verify_signature": False})
            return {
                "subject": payload.get("sub"),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "api_key_name": payload.get("api_key_name"),
                "username": payload.get("username"),
            }
        except Exception:
            return None

    def revoke_token(self, token: str, reason: Optional[str] = None) -> bool:
        """MVP: Token revocation not implemented (no blacklist for simplicity)

        Returns True for compatibility but doesn't actually revoke anything
        """
        logger.info("Token revocation called but not implemented in MVP - Issue #153")
        return True

    def cleanup_expired_tokens(self) -> int:
        """MVP: Token cleanup not implemented (no persistent storage)

        Returns 0 for compatibility
        """
        logger.info("Token cleanup called but not implemented in MVP - Issue #153")
        return 0

    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist to invalidate it"""
        try:
            # Extract jti from token for blacklisting
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jti = payload.get("jti")
            if jti:
                self._blacklisted_tokens.add(jti)
                logger.debug(f"Token blacklisted: {jti}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        return jti in self._blacklisted_tokens


# Convenience functions for backward compatibility
def create_jwt_manager(
    db_path: Optional[str] = None, secret_key: Optional[str] = None
) -> JWTManager:
    """Create JWTManager instance"""
    return JWTManager(db_path, secret_key)


def get_default_jwt_manager() -> JWTManager:
    """Get default JWTManager instance"""
    return JWTManager()
