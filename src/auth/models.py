"""
Authentication models for Osservatorio ISTAT Data Platform

Data models for API keys, JWT tokens, and authentication claims.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class APIKey:
    """API Key model for authentication"""

    id: Optional[int] = None
    name: str = ""
    key: str = ""
    key_hash: str = ""
    scopes: List[str] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    rate_limit: int = 100
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["read"]


@dataclass
class AuthToken:
    """JWT Authentication Token model"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour default
    refresh_token: Optional[str] = None
    scope: str = "read"


@dataclass
class TokenClaims:
    """JWT Token Claims model"""

    sub: str  # subject (api key id)
    iss: str = "osservatorio-istat"  # issuer
    aud: str = "osservatorio-api"  # audience
    exp: Optional[datetime] = None  # expiration
    iat: Optional[datetime] = None  # issued at
    scope: str = "read"
    api_key_name: Optional[str] = None
    rate_limit: int = 100
