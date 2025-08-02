"""
FastAPI dependencies for Osservatorio ISTAT REST API

Provides authentication, authorization, rate limiting, and other
cross-cutting concerns as FastAPI dependencies.
"""

from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt_manager import JWTManager
from src.auth.models import APIKey, TokenClaims
from src.auth.rate_limiter import SQLiteRateLimiter
from src.auth.sqlite_auth import SQLiteAuthManager
from src.database.sqlite.repository import get_unified_repository
from src.utils.config import get_config
from src.utils.logger import get_logger

from .models import APIScope
from .production_istat_client import ProductionIstatClient

logger = get_logger(__name__)

# Security scheme for FastAPI OpenAPI
security = HTTPBearer(
    scheme_name="Bearer JWT",
    description="JWT token for API authentication. Obtain from /auth/token endpoint.",
    auto_error=False,
)

# Global instances
_jwt_manager: Optional[JWTManager] = None
_auth_manager: Optional[SQLiteAuthManager] = None
_rate_limiter: Optional[SQLiteRateLimiter] = None
_istat_client: Optional[ProductionIstatClient] = None


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance (singleton)"""
    global _jwt_manager
    if _jwt_manager is None:
        # Issue #84: Use UnifiedDataRepository instead of direct manager access
        repository = get_unified_repository()
        config = get_config()
        jwt_secret = config.get("jwt_secret_key")
        _jwt_manager = JWTManager(repository.metadata_manager, secret_key=jwt_secret)
    return _jwt_manager


def get_auth_manager() -> SQLiteAuthManager:
    """Get authentication manager instance (singleton)"""
    global _auth_manager
    if _auth_manager is None:
        # Issue #84: Use UnifiedDataRepository instead of direct manager access
        repository = get_unified_repository()
        _auth_manager = SQLiteAuthManager(repository.metadata_manager)
    return _auth_manager


def get_rate_limiter() -> SQLiteRateLimiter:
    """Get rate limiter instance (singleton)"""
    global _rate_limiter
    if _rate_limiter is None:
        # Issue #84: Use UnifiedDataRepository instead of direct manager access
        repository = get_unified_repository()
        _rate_limiter = SQLiteRateLimiter(repository.metadata_manager)
    return _rate_limiter


def get_istat_client() -> ProductionIstatClient:
    """Get production ISTAT client instance (singleton)"""
    global _istat_client
    if _istat_client is None:
        repository = get_unified_repository()
        _istat_client = ProductionIstatClient(repository=repository)
    return _istat_client


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    auth_manager: SQLiteAuthManager = Depends(get_auth_manager),
) -> TokenClaims:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        request: FastAPI request object
        credentials: Authorization credentials from header
        jwt_manager: JWT manager instance
        auth_manager: Authentication manager instance

    Returns:
        TokenClaims: Validated token claims

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify JWT token
        token_claims = jwt_manager.verify_token(credentials.credentials)
        if not token_claims:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # For API key validation, we rely on JWT validation
        # The JWT was generated from a valid API key, so we trust the claims
        # In a more secure implementation, we might still verify the key exists

        # Add request context to token claims
        token_claims.client_ip = request.client.host
        token_claims.user_agent = request.headers.get("user-agent")

        logger.debug(f"Authenticated user: {token_claims.api_key_name}")
        return token_claims

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_scope(required_scope: APIScope):
    """
    Dependency factory for scope-based authorization.

    Args:
        required_scope: Required API scope

    Returns:
        Dependency function that validates scope
    """

    def scope_dependency(
        current_user: TokenClaims = Depends(get_current_user),
    ) -> TokenClaims:
        user_scopes = current_user.scope.split()

        # Admin scope grants access to everything
        if APIScope.ADMIN in user_scopes:
            return current_user

        # Check specific scope
        if required_scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}",
            )

        return current_user

    return scope_dependency


def require_admin():
    """Dependency that requires admin scope"""
    return require_scope(APIScope.ADMIN)


def require_write():
    """Dependency that requires write scope"""
    return require_scope(APIScope.WRITE)


async def check_rate_limit(
    request: Request,
    current_user: TokenClaims = Depends(get_current_user),
    rate_limiter: SQLiteRateLimiter = Depends(get_rate_limiter),
):
    """
    Rate limiting dependency.

    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        rate_limiter: Rate limiter instance

    Raises:
        HTTPException: If rate limit exceeded
    """
    try:
        # Create API key object for rate limiting based on token claims
        api_key = APIKey(
            id=int(current_user.sub),
            name=current_user.api_key_name or "unknown",
            scopes=current_user.scope.split(),
            rate_limit=current_user.rate_limit,
        )

        # Check rate limit
        result = rate_limiter.check_rate_limit(
            api_key=api_key,
            ip_address=request.client.host,
            endpoint=request.url.path,
            user_agent=request.headers.get("user-agent"),
        )

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=result.to_headers(),
            )

        # Add rate limit headers to response (will be handled by middleware)
        rate_headers = result.to_headers()
        request.state.rate_limit_headers = rate_headers
        logger.info(f"Set rate limit headers: {rate_headers}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting error: {e}", exc_info=True)
        # Set default rate limit headers even if rate limiting fails
        default_headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "99",
            "X-RateLimit-Reset": str(
                int((datetime.now() + timedelta(hours=1)).timestamp())
            ),
        }
        request.state.rate_limit_headers = default_headers
        logger.info(f"Set default rate limit headers: {default_headers}")


def get_repository():
    """Dependency to get unified data repository"""
    return get_unified_repository()


def validate_pagination(page: int = 1, page_size: int = 50) -> tuple[int, int]:
    """
    Dependency for pagination validation.

    Args:
        page: Page number (1-based)
        page_size: Number of items per page

    Returns:
        Tuple of validated (page, page_size)

    Raises:
        HTTPException: If pagination parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be >= 1"
        )

    if page_size < 1 or page_size > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 1000",
        )

    return page, page_size


def validate_dataset_id(dataset_id: str) -> str:
    """
    Dependency for dataset ID validation.

    Args:
        dataset_id: Dataset identifier

    Returns:
        Validated dataset ID

    Raises:
        HTTPException: If dataset ID is invalid
    """
    if not dataset_id or len(dataset_id.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset ID is required"
        )

    # Basic format validation (ISTAT dataset IDs are typically alphanumeric with underscores)
    if not dataset_id.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dataset ID format"
        )

    return dataset_id.strip()


async def log_api_request(
    request: Request,
    current_user: TokenClaims = Depends(get_current_user),
    repository=Depends(get_repository),
):
    """
    Dependency to log API requests for audit purposes.

    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        repository: Unified data repository
    """
    try:
        # Extract request details
        method = request.method
        str(request.url)
        endpoint = request.url.path
        query_params = dict(request.query_params)

        # Log the request
        repository.metadata_manager.log_audit(
            user_id=current_user.api_key_name or current_user.sub,
            action="api_request",
            resource_type="api_endpoint",
            resource_id=endpoint,
            details={
                "method": method,
                "endpoint": endpoint,
                "query_params": query_params,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "api_key_id": current_user.sub,
            },
        )

    except Exception as e:
        logger.error(f"Failed to log API request: {e}")
        # Don't fail the request on logging errors


def handle_api_errors(func):
    """
    Decorator for consistent API error handling.

    Args:
        func: FastAPI route function

    Returns:
        Wrapped function with error handling
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return wrapper


def get_dataflow_service():
    """Get DataflowAnalysisService instance as FastAPI dependency."""
    from src.services.service_factory import get_dataflow_analysis_service

    return get_dataflow_analysis_service()


# Note: Dependencies are now used individually in endpoints
# for better clarity and customization
