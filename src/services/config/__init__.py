"""
Configuration management package for Docker-ready services.

This package provides simple configuration management with support for:
- Environment variables
- Docker environment files
- Configuration validation
"""

from .environment_config import EnvironmentConfig

__all__ = ["EnvironmentConfig"]
