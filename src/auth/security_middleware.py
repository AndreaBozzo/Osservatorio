"""
Simplified Security Headers Middleware for MVP - Issue #153

Basic security headers middleware for MVP:
- Essential security headers only
- No complex OWASP features
- No integrated authentication/rate limiting
- Simplified CORS handling
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Simplified security headers middleware for MVP - Issue #153"""

    def __init__(self, app):
        super().__init__(app)
        logger.info(
            "Simplified SecurityHeadersMiddleware initialized for MVP - Issue #153"
        )

    async def dispatch(self, request: Request, call_next):
        """Add basic security headers to responses"""
        try:
            response = await call_next(request)

            # Add essential security headers for MVP
            response.headers.update(
                {
                    # Basic security headers
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                    # Basic cache control
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    # API identification
                    "X-API-Version": "mvp-0.5",
                    "Server": "Osservatorio-MVP",
                }
            )

            return response

        except Exception as e:
            logger.error(f"SecurityHeadersMiddleware error: {e}")
            # Return the response without additional headers if there's an error
            return await call_next(request)


# Backward compatibility - remove complex authentication features for MVP
class AuthenticationMiddleware:
    """Placeholder for removed complex authentication - Issue #153 MVP"""

    def __init__(self, *args, **kwargs):
        logger.warning(
            "AuthenticationMiddleware removed for MVP - Issue #153. Use basic JWT auth instead."
        )
        pass
