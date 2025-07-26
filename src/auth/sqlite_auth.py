"""
SQLite-based Authentication Manager for Osservatorio ISTAT Data Platform

Provides secure API key management with SQLite backend:
- Cryptographically secure API key generation
- Bcrypt-based key hashing and verification
- Scope-based access control
- Usage tracking and rate limiting
- Audit logging for security events
"""

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import bcrypt

from src.database.sqlite.manager import SQLiteMetadataManager
from src.utils.logger import get_logger
from src.utils.security_enhanced import SecurityManager

from .models import APIKey, TokenClaims

logger = get_logger(__name__)
security = SecurityManager()


class SQLiteAuthManager:
    """SQLite-backed authentication manager for API keys and tokens"""

    # Available scopes for API keys
    VALID_SCOPES = [
        "read",  # Read-only access to datasets
        "write",  # Write access for data uploads
        "admin",  # Administrative access
        "analytics",  # Access to analytics endpoints
        "powerbi",  # PowerBI integration access
        "tableau",  # Tableau integration access
    ]

    # API key format configuration
    KEY_PREFIX = "osv_"
    KEY_LENGTH = 32

    def __init__(self, sqlite_manager: SQLiteMetadataManager):
        """Initialize auth manager with SQLite backend"""
        self.db = sqlite_manager
        self.logger = logger

        # Ensure auth schema exists
        self._ensure_auth_schema()

        logger.info("SQLite Authentication Manager initialized")

    def _ensure_auth_schema(self):
        """Ensure authentication schema exists in SQLite"""
        try:
            # Extend existing api_credentials table with auth-specific columns
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Add auth columns if they don't exist
                auth_columns = [
                    ("scopes_json", "TEXT DEFAULT '[]'"),
                    ("name", "TEXT"),
                    ("key_prefix", "TEXT"),
                    ("revoked_at", "TIMESTAMP"),
                    ("last_refresh", "TIMESTAMP"),
                ]

                for column_name, column_def in auth_columns:
                    try:
                        cursor.execute(
                            f"ALTER TABLE api_credentials ADD COLUMN {column_name} {column_def}"
                        )
                        logger.debug(f"Added auth column: {column_name}")
                    except sqlite3.OperationalError:
                        # Column already exists
                        pass

                # Create refresh tokens table (if not already created by JWT manager)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS refresh_tokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_key_id INTEGER NOT NULL,
                        token_hash TEXT NOT NULL UNIQUE,
                        expires_at TIMESTAMP NOT NULL,
                        is_revoked INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        revoked_at TIMESTAMP NULL,
                        FOREIGN KEY (api_key_id) REFERENCES api_credentials (id)
                    )
                """
                )

                # Create rate limiting table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_key_id INTEGER NOT NULL,
                        endpoint TEXT NOT NULL,
                        request_count INTEGER DEFAULT 0,
                        window_start TIMESTAMP NOT NULL,
                        window_end TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(api_key_id, endpoint, window_start),
                        FOREIGN KEY (api_key_id) REFERENCES api_credentials (id)
                    )
                """
                )

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to ensure auth schema: {e}")
            raise

    def generate_api_key(
        self, name: str, scopes: List[str], expires_days: Optional[int] = None
    ) -> APIKey:
        """Generate a new secure API key with specified scopes

        Args:
            name: Human-readable name for the API key
            scopes: List of permission scopes
            expires_days: Days until expiration (None for no expiration)

        Returns:
            APIKey object with generated key and metadata

        Raises:
            ValueError: If invalid scopes provided
            RuntimeError: If key generation fails
        """
        try:
            # Validate scopes
            invalid_scopes = set(scopes) - set(self.VALID_SCOPES)
            if invalid_scopes:
                raise ValueError(f"Invalid scopes: {invalid_scopes}")

            # Generate cryptographically secure API key
            key_suffix = secrets.token_urlsafe(self.KEY_LENGTH)
            api_key = f"{self.KEY_PREFIX}{key_suffix}"

            # Hash the key for storage
            key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

            # Calculate expiration
            expires_at = None
            if expires_days is not None:
                expires_at = datetime.now() + timedelta(days=expires_days)

            # Store in database
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO api_credentials
                    (service_name, api_key_hash, scopes_json, name, key_prefix,
                     is_active, expires_at, rate_limit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        f"api_key_{name.lower().replace(' ', '_')}",
                        key_hash,
                        security.encrypt_data(json.dumps(scopes)),  # Encrypted scopes
                        name,
                        self.KEY_PREFIX,
                        True,
                        expires_at,
                        100,  # Default rate limit
                        datetime.now(),
                        datetime.now(),
                    ),
                )

                api_key_id = cursor.lastrowid
                conn.commit()

            # Log creation
            self._log_auth_event(
                "api_key_created",
                f"api_key:{api_key_id}",
                {"name": name, "scopes": scopes},
            )

            return APIKey(
                id=api_key_id,
                name=name,
                key=api_key,  # Return actual key only on creation
                key_hash=key_hash,
                scopes=scopes,
                expires_at=expires_at,
                created_at=datetime.now(),
            )

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise RuntimeError(f"API key generation failed: {e}")

    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key and return associated metadata

        Args:
            api_key: The API key to verify

        Returns:
            APIKey object if valid, None if invalid/expired
        """
        try:
            if not api_key.startswith(self.KEY_PREFIX):
                return None

            with self.db.transaction() as conn:
                cursor = conn.cursor()

                # Get all active API keys for verification
                cursor.execute(
                    """
                    SELECT id, service_name, api_key_hash, scopes_json, name,
                           is_active, expires_at, last_used, usage_count,
                           rate_limit, created_at, updated_at
                    FROM api_credentials
                    WHERE key_prefix = ? AND is_active = 1
                    AND (expires_at IS NULL OR expires_at > ?)
                """,
                    (self.KEY_PREFIX, datetime.now()),
                )

                for row in cursor.fetchall():
                    (
                        key_id,
                        service_name,
                        key_hash,
                        scopes_json,
                        name,
                        is_active,
                        expires_at,
                        last_used,
                        usage_count,
                        rate_limit,
                        created_at,
                        updated_at,
                    ) = row

                    # Verify key hash
                    if bcrypt.checkpw(api_key.encode(), key_hash.encode()):
                        # Decrypt scopes
                        try:
                            scopes_str = security.decrypt_data(scopes_json)
                            scopes = json.loads(scopes_str)
                        except:
                            scopes = ["read"]  # Fallback

                        # Update usage tracking
                        self._update_key_usage(key_id)

                        return APIKey(
                            id=key_id,
                            name=name,
                            key_hash=key_hash,
                            scopes=scopes,
                            is_active=is_active,
                            expires_at=expires_at,
                            last_used=datetime.now(),
                            usage_count=usage_count + 1,
                            rate_limit=rate_limit,
                            created_at=created_at,
                            updated_at=updated_at,
                        )

            return None

        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return None

    def revoke_api_key(
        self, api_key_id: int, reason: str = "manual_revocation"
    ) -> bool:
        """Revoke an API key

        Args:
            api_key_id: ID of the API key to revoke
            reason: Reason for revocation

        Returns:
            True if successfully revoked, False otherwise
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE api_credentials
                    SET is_active = 0, revoked_at = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (datetime.now(), datetime.now(), api_key_id),
                )

                if cursor.rowcount > 0:
                    conn.commit()

                    # Log revocation
                    self._log_auth_event(
                        "api_key_revoked", f"api_key:{api_key_id}", {"reason": reason}
                    )

                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to revoke API key {api_key_id}: {e}")
            return False

    def list_api_keys(self, include_revoked: bool = False) -> List[APIKey]:
        """List all API keys

        Args:
            include_revoked: Whether to include revoked keys

        Returns:
            List of APIKey objects (without actual key values)
        """
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                if include_revoked:
                    query = """
                        SELECT id, service_name, scopes_json, name, is_active,
                               expires_at, last_used, usage_count, rate_limit,
                               created_at, updated_at, revoked_at
                        FROM api_credentials
                        WHERE key_prefix = ?
                        ORDER BY created_at DESC
                    """
                    params = (self.KEY_PREFIX,)
                else:
                    query = """
                        SELECT id, service_name, scopes_json, name, is_active,
                               expires_at, last_used, usage_count, rate_limit,
                               created_at, updated_at, revoked_at
                        FROM api_credentials
                        WHERE key_prefix = ? AND is_active = 1
                        ORDER BY created_at DESC
                    """
                    params = (self.KEY_PREFIX,)

                cursor.execute(query, params)

                keys = []
                for row in cursor.fetchall():
                    (
                        key_id,
                        service_name,
                        scopes_json,
                        name,
                        is_active,
                        expires_at,
                        last_used,
                        usage_count,
                        rate_limit,
                        created_at,
                        updated_at,
                        revoked_at,
                    ) = row

                    # Decrypt scopes
                    try:
                        scopes_str = security.decrypt_data(scopes_json)
                        scopes = json.loads(scopes_str)
                    except:
                        scopes = ["read"]

                    keys.append(
                        APIKey(
                            id=key_id,
                            name=name,
                            scopes=scopes,
                            is_active=is_active,
                            expires_at=expires_at,
                            last_used=last_used,
                            usage_count=usage_count,
                            rate_limit=rate_limit,
                            created_at=created_at,
                            updated_at=updated_at,
                        )
                    )

                return keys

        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    def check_scope_permission(self, api_key: APIKey, required_scope: str) -> bool:
        """Check if API key has required scope permission

        Args:
            api_key: APIKey object to check
            required_scope: Required permission scope

        Returns:
            True if permission granted, False otherwise
        """
        if not api_key or not api_key.is_active:
            return False

        # Admin scope grants all permissions
        if "admin" in api_key.scopes:
            return True

        # Check specific scope
        return required_scope in api_key.scopes

    def _update_key_usage(self, api_key_id: int):
        """Update API key usage statistics"""
        try:
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE api_credentials
                    SET usage_count = usage_count + 1,
                        last_used = ?,
                        updated_at = ?
                    WHERE id = ?
                """,
                    (datetime.now(), datetime.now(), api_key_id),
                )

                conn.commit()

        except Exception as e:
            logger.debug(f"Failed to update key usage: {e}")

    def _log_auth_event(self, action: str, resource_id: str, details: Dict):
        """Log authentication event to audit log"""
        try:
            audit_data = {
                "user_id": "system",
                "action": action,
                "resource_type": "api_key",
                "resource_id": resource_id,
                "details_json": security.encrypt_data(json.dumps(details)),
                "success": True,
                "timestamp": datetime.now(),
            }

            # Use existing audit logging from SQLite manager
            with self.db.transaction() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO audit_log
                    (user_id, action, resource_type, resource_id, details_json, success, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        audit_data["user_id"],
                        audit_data["action"],
                        audit_data["resource_type"],
                        audit_data["resource_id"],
                        audit_data["details_json"],
                        audit_data["success"],
                        audit_data["timestamp"],
                    ),
                )

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")
