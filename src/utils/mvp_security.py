"""
Simple MVP security utilities for basic data encryption/decryption.

This module provides minimal security functionality needed for MVP:
- Basic data encryption/decryption
- Simple replacements for removed enhanced security features
"""

import base64
import hashlib
import secrets

from cryptography.fernet import Fernet


class SimpleSecurity:
    """Simple security manager with basic encryption for MVP."""

    def __init__(self):
        """Initialize with a simple key derivation."""
        # For MVP, we'll use a simple key. In production, use proper key management
        self._key = self._derive_key()
        self._cipher = Fernet(self._key)

    def _derive_key(self) -> bytes:
        """Derive a key for encryption. In MVP, use a static derivation."""
        # For MVP - in production, use proper key derivation
        key_material = "mvp_osservatorio_key_2025"  # Static for MVP simplicity
        digest = hashlib.sha256(key_material.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt_data(self, data: str) -> str:
        """Encrypt string data."""
        try:
            if not data:
                return ""
            encrypted = self._cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception:
            # If encryption fails in MVP, return original data
            return data

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        try:
            if not encrypted_data:
                return ""
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            # If decryption fails in MVP, assume it's already decrypted
            return encrypted_data

    def generate_token(self) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    def hash_password(self, password: str) -> str:
        """Simple password hashing for MVP."""
        return hashlib.sha256(password.encode()).hexdigest()


# Global security instance for MVP
security = SimpleSecurity()


def get_security_manager() -> SimpleSecurity:
    """Get the security manager instance."""
    return security
