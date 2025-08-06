"""
Configuration management package for Kubernetes-ready services.

This package provides cloud-native configuration management with support for:
- Environment variables
- Kubernetes ConfigMaps and Secrets
- Hot reload capabilities
- Configuration validation
"""

from .environment_config import EnvironmentConfig
from .k8s_config_manager import K8sConfigManager

__all__ = ["EnvironmentConfig", "K8sConfigManager"]
