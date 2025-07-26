"""
Security Headers Middleware for Osservatorio ISTAT Data Platform

OWASP-compliant security headers middleware:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options, X-Content-Type-Options
- X-XSS-Protection, Referrer-Policy
- Permissions-Policy and Feature-Policy
- CORS configuration for cross-origin requests
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityHeadersConfig:
    """Configuration for security headers"""

    def __init__(self):
        # Content Security Policy
        self.csp_enabled = True
        self.csp_directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],  # Adjust as needed
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https:"],
            "connect-src": ["'self'"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
        }

        # HSTS (HTTP Strict Transport Security)
        self.hsts_enabled = True
        self.hsts_max_age = 31536000  # 1 year in seconds
        self.hsts_include_subdomains = True
        self.hsts_preload = True

        # Frame Options
        self.frame_options = "DENY"  # DENY, SAMEORIGIN, or ALLOW-FROM

        # Content Type Options
        self.content_type_options = "nosniff"

        # XSS Protection
        self.xss_protection = "1; mode=block"

        # Referrer Policy
        self.referrer_policy = "strict-origin-when-cross-origin"

        # Permissions Policy (Feature Policy successor)
        self.permissions_policy = {
            "camera": [],
            "microphone": [],
            "geolocation": [],
            "payment": [],
            "usb": [],
            "magnetometer": [],
            "accelerometer": [],
            "gyroscope": [],
        }

        # CORS settings
        self.cors_enabled = True
        self.cors_allow_origins = ["https://localhost:3000"]  # Adjust for frontend
        self.cors_allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.cors_allow_headers = ["Content-Type", "Authorization", "X-API-Key"]
        self.cors_max_age = 86400  # 24 hours

        # Additional security headers
        self.server_header = "Osservatorio-API"  # Hide server info
        self.x_powered_by = None  # Remove X-Powered-By


class SecurityHeadersMiddleware:
    """OWASP-compliant security headers middleware"""

    def __init__(self, config: Optional[SecurityHeadersConfig] = None):
        """Initialize security middleware

        Args:
            config: Security configuration (uses default if None)
        """
        self.config = config or SecurityHeadersConfig()
        self.logger = logger

        # Generate nonce for CSP if using inline scripts
        self.nonce_cache = {}

        logger.info("Security Headers Middleware initialized")

    def apply_security_headers(
        self,
        response_headers: Dict[str, str],
        request_path: str = "/",
        request_method: str = "GET",
    ) -> Dict[str, str]:
        """Apply security headers to response

        Args:
            response_headers: Existing response headers
            request_path: Request path for context-specific headers
            request_method: HTTP method

        Returns:
            Updated headers dictionary
        """
        headers = response_headers.copy()

        try:
            # Content Security Policy
            if self.config.csp_enabled:
                headers["Content-Security-Policy"] = self._build_csp(request_path)

            # HTTP Strict Transport Security
            if self.config.hsts_enabled:
                headers["Strict-Transport-Security"] = self._build_hsts()

            # Frame Options
            if self.config.frame_options:
                headers["X-Frame-Options"] = self.config.frame_options

            # Content Type Options
            if self.config.content_type_options:
                headers["X-Content-Type-Options"] = self.config.content_type_options

            # XSS Protection
            if self.config.xss_protection:
                headers["X-XSS-Protection"] = self.config.xss_protection

            # Referrer Policy
            if self.config.referrer_policy:
                headers["Referrer-Policy"] = self.config.referrer_policy

            # Permissions Policy
            permissions_policy = self._build_permissions_policy()
            if permissions_policy:
                headers["Permissions-Policy"] = permissions_policy

            # Hide server information
            if self.config.server_header:
                headers["Server"] = self.config.server_header

            # Remove X-Powered-By
            if "X-Powered-By" in headers and self.config.x_powered_by is None:
                del headers["X-Powered-By"]
            elif self.config.x_powered_by:
                headers["X-Powered-By"] = self.config.x_powered_by

            # Additional security headers
            headers["X-Robots-Tag"] = "noindex, nofollow"  # Prevent indexing
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            headers["Pragma"] = "no-cache"
            headers["Expires"] = "0"

            return headers

        except Exception as e:
            logger.error(f"Failed to apply security headers: {e}")
            return response_headers

    def apply_cors_headers(
        self,
        response_headers: Dict[str, str],
        request_origin: Optional[str] = None,
        request_method: str = "GET",
    ) -> Dict[str, str]:
        """Apply CORS headers to response

        Args:
            response_headers: Existing response headers
            request_origin: Origin header from request
            request_method: HTTP method

        Returns:
            Updated headers dictionary
        """
        if not self.config.cors_enabled:
            return response_headers

        headers = response_headers.copy()

        try:
            # Check if origin is allowed
            if request_origin and self._is_origin_allowed(request_origin):
                headers["Access-Control-Allow-Origin"] = request_origin
            elif "*" in self.config.cors_allow_origins:
                headers["Access-Control-Allow-Origin"] = "*"

            # Allow methods
            headers["Access-Control-Allow-Methods"] = ", ".join(
                self.config.cors_allow_methods
            )

            # Allow headers
            headers["Access-Control-Allow-Headers"] = ", ".join(
                self.config.cors_allow_headers
            )

            # Max age for preflight cache
            headers["Access-Control-Max-Age"] = str(self.config.cors_max_age)

            # Allow credentials if needed
            if request_origin and self._is_origin_allowed(request_origin):
                headers["Access-Control-Allow-Credentials"] = "true"

            # Expose headers that client can access
            headers[
                "Access-Control-Expose-Headers"
            ] = "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset"

            return headers

        except Exception as e:
            logger.error(f"Failed to apply CORS headers: {e}")
            return response_headers

    def _build_csp(self, request_path: str) -> str:
        """Build Content Security Policy header"""
        try:
            # Generate nonce for inline scripts if needed
            nonce = self._get_or_create_nonce(request_path)

            directives = []
            for directive, sources in self.config.csp_directives.items():
                # Add nonce to script-src if using inline scripts
                if directive == "script-src" and "'unsafe-inline'" in sources and nonce:
                    sources = [s for s in sources if s != "'unsafe-inline'"]
                    sources.append(f"'nonce-{nonce}'")

                directive_value = f"{directive} {' '.join(sources)}"
                directives.append(directive_value)

            return "; ".join(directives)

        except Exception as e:
            logger.error(f"Failed to build CSP: {e}")
            return "default-src 'self'"

    def _build_hsts(self) -> str:
        """Build HSTS header"""
        hsts_parts = [f"max-age={self.config.hsts_max_age}"]

        if self.config.hsts_include_subdomains:
            hsts_parts.append("includeSubDomains")

        if self.config.hsts_preload:
            hsts_parts.append("preload")

        return "; ".join(hsts_parts)

    def _build_permissions_policy(self) -> str:
        """Build Permissions Policy header"""
        if not self.config.permissions_policy:
            return ""

        policies = []
        for feature, allowlist in self.config.permissions_policy.items():
            if not allowlist:
                # Feature disabled
                policies.append(f"{feature}=()")
            else:
                # Feature enabled for specific origins
                origins = " ".join(f'"{origin}"' for origin in allowlist)
                policies.append(f"{feature}=({origins})")

        return ", ".join(policies)

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed for CORS"""
        if "*" in self.config.cors_allow_origins:
            return True

        return origin in self.config.cors_allow_origins

    def _get_or_create_nonce(self, request_path: str) -> Optional[str]:
        """Get or create CSP nonce for request"""
        # Simple nonce caching by path (in production, use per-request nonces)
        if request_path not in self.nonce_cache:
            self.nonce_cache[request_path] = secrets.token_urlsafe(16)

        return self.nonce_cache.get(request_path)

    def get_security_report(self) -> Dict[str, Union[str, bool, int]]:
        """Generate security configuration report

        Returns:
            Dictionary with current security settings
        """
        return {
            "csp_enabled": self.config.csp_enabled,
            "hsts_enabled": self.config.hsts_enabled,
            "hsts_max_age": self.config.hsts_max_age,
            "frame_options": self.config.frame_options,
            "content_type_options": self.config.content_type_options,
            "xss_protection": self.config.xss_protection,
            "referrer_policy": self.config.referrer_policy,
            "cors_enabled": self.config.cors_enabled,
            "cors_origins_count": len(self.config.cors_allow_origins),
            "permissions_policies_count": len(self.config.permissions_policy),
        }


class AuthenticationMiddleware:
    """Authentication middleware for request processing"""

    def __init__(self, auth_manager, jwt_manager, rate_limiter):
        """Initialize authentication middleware

        Args:
            auth_manager: SQLiteAuthManager instance
            jwt_manager: JWTManager instance
            rate_limiter: SQLiteRateLimiter instance
        """
        self.auth_manager = auth_manager
        self.jwt_manager = jwt_manager
        self.rate_limiter = rate_limiter
        self.logger = logger

        logger.info("Authentication Middleware initialized")

    def authenticate_request(
        self, headers: Dict[str, str], ip_address: str, endpoint: str
    ) -> Dict[str, Union[bool, dict, str]]:
        """Authenticate incoming request

        Args:
            headers: Request headers
            ip_address: Client IP address
            endpoint: API endpoint being accessed

        Returns:
            Authentication result dictionary
        """
        try:
            # Extract authentication credentials
            api_key = self._extract_api_key(headers)
            jwt_token = self._extract_jwt_token(headers)

            authenticated_user = None

            # Try JWT authentication first
            if jwt_token:
                token_claims = self.jwt_manager.verify_token(jwt_token)
                if token_claims:
                    authenticated_user = {
                        "type": "jwt",
                        "user_id": token_claims.sub,
                        "scopes": token_claims.scope.split(),
                        "api_key_name": token_claims.api_key_name,
                    }

            # Try API key authentication
            elif api_key:
                api_key_obj = self.auth_manager.verify_api_key(api_key)
                if api_key_obj:
                    authenticated_user = {
                        "type": "api_key",
                        "user_id": str(api_key_obj.id),
                        "scopes": api_key_obj.scopes,
                        "api_key_name": api_key_obj.name,
                        "api_key_obj": api_key_obj,
                    }

            # Check rate limiting
            rate_limit_result = self.rate_limiter.check_rate_limit(
                api_key=authenticated_user.get("api_key_obj")
                if authenticated_user
                else None,
                ip_address=ip_address,
                endpoint=endpoint,
                user_agent=headers.get("User-Agent"),
            )

            return {
                "authenticated": authenticated_user is not None,
                "user": authenticated_user,
                "rate_limit": rate_limit_result,
                "rate_limit_headers": rate_limit_result.to_headers(),
            }

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {"authenticated": False, "user": None, "error": str(e)}

    def check_scope_permission(self, user: Dict, required_scope: str) -> bool:
        """Check if authenticated user has required scope

        Args:
            user: Authenticated user dictionary
            required_scope: Required permission scope

        Returns:
            True if permission granted, False otherwise
        """
        if not user:
            return False

        user_scopes = user.get("scopes", [])

        # Admin scope grants all permissions
        if "admin" in user_scopes:
            return True

        # Check specific scope
        return required_scope in user_scopes

    def _extract_api_key(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract API key from headers"""
        # Try X-API-Key header first
        api_key = headers.get("X-API-Key") or headers.get("x-api-key")

        if not api_key:
            # Try Authorization header with ApiKey scheme
            auth_header = headers.get("Authorization") or headers.get("authorization")
            if auth_header and auth_header.startswith("ApiKey "):
                api_key = auth_header[7:]  # Remove "ApiKey " prefix

        return api_key

    def _extract_jwt_token(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract JWT token from headers"""
        auth_header = headers.get("Authorization") or headers.get("authorization")

        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix

        return None
