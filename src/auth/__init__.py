"""
Authentication module for Osservatorio ISTAT Data Platform

Provides JWT-based authentication with SQLite backend for:
- API key management with scopes
- JWT token generation and validation
- Rate limiting and security middleware
"""

from .jwt_manager import JWTManager
from .models import APIKey, AuthToken, TokenClaims
from .sqlite_auth import SQLiteAuthManager

__all__ = ["SQLiteAuthManager", "JWTManager", "APIKey", "AuthToken", "TokenClaims"]
