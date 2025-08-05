"""
Kubernetes-native configuration manager with ConfigMap and Secret support.

Provides hot reload capabilities and configuration validation for cloud-native deployments.
"""

import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import ValidationError

from ...utils.logger import get_logger
from .environment_config import EnvironmentConfig


class K8sConfigManager:
    """
    Kubernetes-native configuration manager.

    Features:
    - ConfigMap and Secret mounting support
    - Hot reload with file watching
    - Configuration validation
    - Thread-safe configuration updates
    - Event-driven change notifications
    """

    def __init__(
        self,
        config_dir: str = "/etc/config",
        secrets_dir: str = "/etc/secrets",
        watch_interval: int = 5,
        enable_hot_reload: bool = True,
    ):
        """
        Initialize K8s configuration manager.

        Args:
            config_dir: Directory where ConfigMaps are mounted
            secrets_dir: Directory where Secrets are mounted
            watch_interval: File watching interval in seconds
            enable_hot_reload: Whether to enable hot configuration reload
        """
        self.config_dir = Path(config_dir)
        self.secrets_dir = Path(secrets_dir)
        self.watch_interval = watch_interval
        self.enable_hot_reload = enable_hot_reload

        self.logger = get_logger(__name__)
        self._config: Optional[EnvironmentConfig] = None
        self._file_checksums: dict[str, str] = {}
        self._change_callbacks: list[Callable[[EnvironmentConfig], None]] = []
        self._watch_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._config_lock = threading.RLock()

        # Load initial configuration
        self._load_configuration()

        # Start file watching if enabled
        if self.enable_hot_reload:
            self.start_watching()

    def _load_configuration(self) -> None:
        """Load configuration from environment and mounted files."""
        try:
            with self._config_lock:
                # Start with environment-based configuration
                config_dict = {}

                # Load from environment variables
                env_config = EnvironmentConfig.from_environment()
                config_dict.update(env_config.to_dict())

                # Override with ConfigMap files
                config_overrides = self._load_configmap_files()
                if config_overrides:
                    config_dict.update(config_overrides)

                # Override with Secret files
                secret_overrides = self._load_secret_files()
                if secret_overrides:
                    config_dict.update(secret_overrides)

                # Create validated configuration
                self._config = EnvironmentConfig(**config_dict)

                # Validate for production environment
                if self._config.environment == "production":
                    validation_errors = self._config.validate_required_for_production()
                    if validation_errors:
                        self.logger.warning(
                            f"Production validation warnings: {validation_errors}"
                        )

                self.logger.info(
                    f"Configuration loaded successfully for environment: {self._config.environment}"
                )

        except ValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def _load_configmap_files(self) -> dict[str, Any]:
        """Load configuration from mounted ConfigMaps."""
        config_overrides = {}

        if not self.config_dir.exists():
            self.logger.debug(f"ConfigMap directory not found: {self.config_dir}")
            return config_overrides

        for config_file in self.config_dir.glob("*"):
            if config_file.is_file():
                try:
                    content = config_file.read_text().strip()

                    # Try to parse as JSON first
                    try:
                        data = json.loads(content)
                        config_overrides.update(data)
                        self.logger.debug(f"Loaded JSON config from {config_file.name}")
                    except json.JSONDecodeError:
                        # Treat as key-value pair
                        key = config_file.name.lower().replace("-", "_")
                        config_overrides[key] = content
                        self.logger.debug(f"Loaded config value for {key}")

                except Exception as e:
                    self.logger.warning(
                        f"Failed to load config file {config_file}: {e}"
                    )

        return config_overrides

    def _load_secret_files(self) -> dict[str, Any]:
        """Load configuration from mounted Secrets."""
        secret_overrides = {}

        if not self.secrets_dir.exists():
            self.logger.debug(f"Secrets directory not found: {self.secrets_dir}")
            return secret_overrides

        for secret_file in self.secrets_dir.glob("*"):
            if secret_file.is_file():
                try:
                    content = secret_file.read_text().strip()
                    key = secret_file.name.lower().replace("-", "_")

                    # Parse nested keys (e.g., database_password -> database.password)
                    if "_" in key:
                        parts = key.split("_", 1)
                        section, field = parts[0], parts[1]

                        if section not in secret_overrides:
                            secret_overrides[section] = {}
                        secret_overrides[section][field] = content
                    else:
                        secret_overrides[key] = content

                    self.logger.debug(f"Loaded secret for {key}")

                except Exception as e:
                    self.logger.warning(
                        f"Failed to load secret file {secret_file}: {e}"
                    )

        return secret_overrides

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate checksum of a file."""
        import hashlib

        try:
            return hashlib.md5(file_path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _has_files_changed(self) -> bool:
        """Check if any configuration files have changed."""
        current_checksums = {}

        # Check ConfigMap files
        if self.config_dir.exists():
            for config_file in self.config_dir.glob("*"):
                if config_file.is_file():
                    current_checksums[str(config_file)] = self._calculate_checksum(
                        config_file
                    )

        # Check Secret files
        if self.secrets_dir.exists():
            for secret_file in self.secrets_dir.glob("*"):
                if secret_file.is_file():
                    current_checksums[str(secret_file)] = self._calculate_checksum(
                        secret_file
                    )

        # Compare with previous checksums
        changed = current_checksums != self._file_checksums
        self._file_checksums = current_checksums

        return changed

    def _watch_files(self) -> None:
        """Watch configuration files for changes."""
        self.logger.info("Starting configuration file watching")

        while not self._shutdown_event.is_set():
            try:
                if self._has_files_changed():
                    self.logger.info("Configuration files changed, reloading...")
                    old_config = self._config

                    try:
                        self._load_configuration()

                        # Notify callbacks of configuration change
                        for callback in self._change_callbacks:
                            try:
                                callback(self._config)
                            except Exception as e:
                                self.logger.error(
                                    f"Configuration change callback failed: {e}"
                                )

                        self.logger.info("Configuration reloaded successfully")

                    except Exception as e:
                        self.logger.error(f"Failed to reload configuration: {e}")
                        # Restore previous configuration on error
                        self._config = old_config

                self._shutdown_event.wait(self.watch_interval)

            except Exception as e:
                self.logger.error(f"Error in configuration watching: {e}")
                self._shutdown_event.wait(self.watch_interval)

    def start_watching(self) -> None:
        """Start file watching in background thread."""
        if self._watch_thread is None or not self._watch_thread.is_alive():
            self._watch_thread = threading.Thread(
                target=self._watch_files, daemon=True, name="config-watcher"
            )
            self._watch_thread.start()
            self.logger.info("Configuration file watching started")

    def stop_watching(self) -> None:
        """Stop file watching."""
        self._shutdown_event.set()
        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=5)
            self.logger.info("Configuration file watching stopped")

    def get_config(self) -> EnvironmentConfig:
        """Get current configuration (thread-safe)."""
        with self._config_lock:
            if self._config is None:
                raise RuntimeError("Configuration not loaded")
            return self._config

    def register_change_callback(
        self, callback: Callable[[EnvironmentConfig], None]
    ) -> None:
        """Register callback for configuration changes."""
        self._change_callbacks.append(callback)
        self.logger.debug(
            f"Registered configuration change callback: {callback.__name__}"
        )

    def unregister_change_callback(
        self, callback: Callable[[EnvironmentConfig], None]
    ) -> None:
        """Unregister configuration change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            self.logger.debug(
                f"Unregistered configuration change callback: {callback.__name__}"
            )

    def validate_configuration(self) -> list[str]:
        """Validate current configuration and return any errors."""
        config = self.get_config()

        errors = []

        # Validate production requirements
        if config.environment == "production":
            errors.extend(config.validate_required_for_production())

        # Validate connectivity (basic checks)
        try:
            # Check if Redis configuration is valid
            if config.enable_distributed_caching and config.redis.host == "localhost":
                errors.append("Redis host should not be localhost in production")

            # Check database configuration
            if config.database.pool_size <= 0:
                errors.append("Database pool size must be positive")

            # Check scaling configuration
            if config.scaling.worker_pool_size <= 0:
                errors.append("Worker pool size must be positive")

        except Exception as e:
            errors.append(f"Configuration validation error: {e}")

        return errors

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of configuration manager."""
        config = self.get_config()
        validation_errors = self.validate_configuration()

        return {
            "status": "healthy" if not validation_errors else "degraded",
            "environment": config.environment,
            "service_name": config.service_name,
            "service_version": config.service_version,
            "hot_reload_enabled": self.enable_hot_reload,
            "watching_active": self._watch_thread is not None
            and self._watch_thread.is_alive(),
            "validation_errors": validation_errors,
            "last_reload": time.time(),
            "monitored_files": len(self._file_checksums),
        }

    def reload_configuration(self) -> bool:
        """Manually trigger configuration reload."""
        try:
            self._load_configuration()
            self.logger.info("Configuration manually reloaded")
            return True
        except Exception as e:
            self.logger.error(f"Manual configuration reload failed: {e}")
            return False

    def export_for_debugging(self) -> dict[str, Any]:
        """Export configuration for debugging (sensitive values masked)."""
        config = self.get_config()
        config_dict = config.to_dict()

        # Mask sensitive values
        if config_dict.get("database", {}).get("url"):
            config_dict["database"]["url"] = self._mask_sensitive_value(
                config_dict["database"]["url"]
            )

        if config_dict.get("redis", {}).get("password"):
            config_dict["redis"]["password"] = "***MASKED***"

        return {
            "configuration": config_dict,
            "health": self.get_health_status(),
            "file_checksums": {
                k: v[:8] + "..." for k, v in self._file_checksums.items()
            },
        }

    @staticmethod
    def _mask_sensitive_value(value: str) -> str:
        """Mask sensitive parts of configuration values."""
        if "://" in value:
            # URL format - mask credentials
            parts = value.split("://")
            if len(parts) == 2 and "@" in parts[1]:
                protocol = parts[0]
                rest = parts[1]
                if "@" in rest:
                    credentials, host_part = rest.split("@", 1)
                    return f"{protocol}://***MASKED***@{host_part}"

        return "***MASKED***"

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.stop_watching()
