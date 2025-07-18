"""Enhanced security management for the Osservatorio project.

This module provides centralized security features including:
- Path validation to prevent directory traversal attacks
- Rate limiting to prevent abuse
- Input sanitization
- Security headers management
"""

import hashlib
import logging
import re
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Setup logging
logger = logging.getLogger(__name__)


class SecurityManager:
    """Centralized security management for the application."""

    def __init__(self):
        """Initialize the security manager."""
        self.rate_limiter: Dict[str, List[float]] = {}
        self.blocked_ips: Set[str] = set()
        self.blocked_patterns: Set[str] = {
            "..",  # Directory traversal
            "~",  # Home directory
            "/etc/",
            "/root/",  # System directories
            "C:\\Windows",
            "C:\\System32",  # Windows system directories
        }
        # Windows reserved names - match exact filenames only
        self.reserved_names: Set[str] = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        self.allowed_extensions: Set[str] = {
            ".json",
            ".csv",
            ".xlsx",
            ".xml",
            ".txt",
            ".log",
            ".md",
            ".py",
            ".yml",
            ".yaml",
            ".toml",
            ".ini",
            ".cfg",
        }

    def validate_path(self, path: str, base_dir: Optional[str] = None) -> bool:
        """Validate a file path against security threats.

        Args:
            path: The file path to validate
            base_dir: Optional base directory to restrict access to

        Returns:
            bool: True if the path is safe, False otherwise
        """
        if not path or not isinstance(path, str):
            return False

        try:
            # Normalize the path
            normalized_path = Path(path).resolve()

            # Check if base directory restriction is enforced
            if base_dir:
                base_path = Path(base_dir).resolve()
                try:
                    # Check if the path is within the base directory
                    normalized_path.relative_to(base_path)
                except ValueError:
                    logger.warning(f"Path {path} is outside base directory {base_dir}")
                    return False

            # Check for forbidden patterns
            path_str = str(normalized_path).lower()
            for pattern in self.blocked_patterns:
                if pattern.lower() in path_str:
                    logger.warning(f"Blocked pattern '{pattern}' found in path {path}")
                    return False

            # Check for Windows reserved names (exact filename match)
            filename = normalized_path.name.upper()
            if (
                filename in self.reserved_names
                or filename.split(".")[0] in self.reserved_names
            ):
                logger.warning(
                    f"Windows reserved name '{filename}' found in path {path}"
                )
                return False

            # Check file extension if it's a file
            if (
                normalized_path.suffix
                and normalized_path.suffix.lower() not in self.allowed_extensions
            ):
                logger.warning(f"File extension '{normalized_path.suffix}' not allowed")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating path {path}: {e}")
            return False

    def rate_limit(
        self, identifier: str, max_requests: int = 100, window: int = 3600
    ) -> bool:
        """Implement rate limiting for API requests.

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum number of requests allowed in the time window
            window: Time window in seconds

        Returns:
            bool: True if request is allowed, False if rate limited
        """
        if identifier in self.blocked_ips:
            return False

        current_time = time.time()

        # Initialize rate limiter for this identifier
        if identifier not in self.rate_limiter:
            self.rate_limiter[identifier] = []

        # Clean up old requests outside the window
        self.rate_limiter[identifier] = [
            t for t in self.rate_limiter[identifier] if current_time - t < window
        ]

        # Check if rate limit is exceeded
        if len(self.rate_limiter[identifier]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        # Add current request timestamp
        self.rate_limiter[identifier].append(current_time)
        return True

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input to prevent injection attacks.

        Args:
            input_str: Input string to sanitize

        Returns:
            str: Sanitized string
        """
        if not isinstance(input_str, str):
            return str(input_str)

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\\\]', "", input_str)

        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]

        return sanitized.strip()

    def generate_token(self, length: int = 32) -> str:
        """Generate a secure random token.

        Args:
            length: Length of the token

        Returns:
            str: Secure random token
        """
        return secrets.token_urlsafe(length)

    def hash_password(
        self, password: str, salt: Optional[str] = None
    ) -> Tuple[str, str]:
        """Hash a password with salt.

        Args:
            password: Password to hash
            salt: Optional salt, if not provided, a new one will be generated

        Returns:
            Tuple[str, str]: (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)

        # Use PBKDF2 with SHA-256
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # iterations
        )

        return hashed.hex(), salt

    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: Password to verify
            hashed_password: Stored hash
            salt: Salt used for hashing

        Returns:
            bool: True if password is correct
        """
        calculated_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(calculated_hash, hashed_password)

    def block_ip(self, ip: str) -> None:
        """Block an IP address.

        Args:
            ip: IP address to block
        """
        self.blocked_ips.add(ip)
        logger.warning(f"IP {ip} has been blocked")

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address.

        Args:
            ip: IP address to unblock
        """
        self.blocked_ips.discard(ip)
        logger.info(f"IP {ip} has been unblocked")

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses.

        Returns:
            Dict[str, str]: Security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    def cleanup_old_entries(self, max_age: int = 3600) -> None:
        """Clean up old rate limiter entries.

        Args:
            max_age: Maximum age in seconds for entries to keep
        """
        current_time = time.time()
        for identifier in list(self.rate_limiter.keys()):
            self.rate_limiter[identifier] = [
                t for t in self.rate_limiter[identifier] if current_time - t < max_age
            ]
            if not self.rate_limiter[identifier]:
                del self.rate_limiter[identifier]


# Singleton instance
security_manager = SecurityManager()


def rate_limit(max_requests: int = 100, window: int = 3600):
    """Decorator for rate limiting function calls.

    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as identifier
            identifier = f"{func.__module__}.{func.__name__}"

            if not security_manager.rate_limit(identifier, max_requests, window):
                raise Exception(f"Rate limit exceeded for {identifier}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_path(base_dir: Optional[str] = None):
    """Decorator for path validation.

    Args:
        base_dir: Base directory to restrict access to
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Look for path-like arguments
            for arg in args:
                if isinstance(arg, (str, Path)) and (
                    "/" in str(arg) or "\\" in str(arg)
                ):
                    if not security_manager.validate_path(str(arg), base_dir):
                        raise ValueError(f"Invalid or unsafe path: {arg}")

            for key, value in kwargs.items():
                if isinstance(value, (str, Path)) and (
                    "/" in str(value) or "\\" in str(value)
                ):
                    if not security_manager.validate_path(str(value), base_dir):
                        raise ValueError(f"Invalid or unsafe path in {key}: {value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator
