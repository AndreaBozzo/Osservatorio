"""
Environment-based configuration management for Kubernetes deployments.

Follows 12-factor app principles with configuration via environment variables.
"""

import os
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    url: str = Field(default="sqlite:///data/osservatorio.db")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)


class RedisConfig(BaseModel):
    """Redis distributed caching configuration."""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: Optional[str] = Field(default=None)
    ssl: bool = Field(default=False)
    socket_timeout: int = Field(default=5)
    socket_connect_timeout: int = Field(default=5)
    max_connections: int = Field(default=50)
    retry_on_timeout: bool = Field(default=True)


class IstatApiConfig(BaseModel):
    """ISTAT API client configuration."""

    base_url: str = Field(default="https://esploradati.istat.it/SDMXWS/rest")
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    backoff_factor: float = Field(default=0.3)
    rate_limit_calls: int = Field(default=100)
    rate_limit_period: int = Field(default=60)


class ObservabilityConfig(BaseModel):
    """Observability and monitoring configuration."""

    # OpenTelemetry
    otel_service_name: str = Field(default="dataflow-analyzer")
    otel_service_version: str = Field(default="1.0.0")
    otel_exporter_otlp_endpoint: str = Field(
        default="http://jaeger-collector:14268/api/traces"
    )

    # Prometheus metrics
    metrics_port: int = Field(default=8001)
    metrics_path: str = Field(default="/metrics")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


class ScalingConfig(BaseModel):
    """Horizontal scaling configuration."""

    worker_pool_size: int = Field(default=4)
    max_concurrent_requests: int = Field(default=100)
    request_timeout: int = Field(default=300)
    queue_max_size: int = Field(default=1000)
    batch_size: int = Field(default=10)
    scale_up_threshold: float = Field(default=0.8)
    scale_down_threshold: float = Field(default=0.2)


class HealthConfig(BaseModel):
    """Health check configuration."""

    startup_timeout: int = Field(default=30)
    liveness_timeout: int = Field(default=5)
    readiness_timeout: int = Field(default=5)
    health_check_interval: int = Field(default=10)
    unhealthy_threshold: int = Field(default=3)
    healthy_threshold: int = Field(default=2)


class EnvironmentConfig(BaseModel):
    """
    Complete environment-based configuration for Kubernetes deployment.

    All configuration values can be overridden via environment variables
    using the prefix pattern: DATAFLOW_<SECTION>_<KEY>

    Example:
        DATAFLOW_DATABASE_URL=postgresql://user:pass@host:5432/db
        DATAFLOW_REDIS_HOST=redis-cluster.default.svc.cluster.local
        DATAFLOW_OBSERVABILITY_LOG_LEVEL=DEBUG
    """

    # Service configuration
    service_name: str = Field(default="dataflow-analyzer")
    service_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    namespace: str = Field(default="default")

    # Core configuration sections
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    istat_api: IstatApiConfig = Field(default_factory=IstatApiConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    scaling: ScalingConfig = Field(default_factory=ScalingConfig)
    health: HealthConfig = Field(default_factory=HealthConfig)

    # Feature flags
    enable_distributed_caching: bool = Field(default=True)
    enable_tracing: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    enable_circuit_breaker: bool = Field(default=True)

    @classmethod
    def from_environment(cls) -> "EnvironmentConfig":
        """
        Create configuration instance from environment variables.

        Supports nested configuration with underscore separation:
        DATAFLOW_DATABASE_URL -> config.database.url
        DATAFLOW_REDIS_HOST -> config.redis.host
        """
        config_dict = {}

        # Parse environment variables with DATAFLOW_ prefix
        for key, value in os.environ.items():
            if key.startswith("DATAFLOW_"):
                # Remove prefix and convert to lowercase
                config_key = key[9:].lower()  # Remove 'DATAFLOW_'

                # Check if it's a top-level field that contains underscores
                top_level_fields_with_underscores = [
                    "service_name",
                    "service_version",
                    "enable_distributed_caching",
                    "enable_tracing",
                    "enable_metrics",
                    "enable_circuit_breaker",
                ]

                if config_key in top_level_fields_with_underscores:
                    config_dict[config_key] = cls._convert_env_value(value)
                # Handle nested configuration
                elif "_" in config_key:
                    parts = config_key.split("_", 1)
                    section, field = parts[0], parts[1]

                    if section not in config_dict:
                        config_dict[section] = {}

                    # Convert string values to appropriate types
                    config_dict[section][field] = cls._convert_env_value(value)
                else:
                    config_dict[config_key] = cls._convert_env_value(value)

        return cls(**config_dict)

    @staticmethod
    def _convert_env_value(value: str) -> Any:
        """Convert string environment variable to appropriate type."""
        # Boolean conversion
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Integer conversion
        if value.isdigit():
            return int(value)

        # Float conversion
        try:
            if "." in value:
                return float(value)
        except ValueError:
            pass

        # String value
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def validate_required_for_production(self) -> list[str]:
        """
        Validate that all required configuration for production is present.

        Returns list of missing or invalid configuration keys.
        """
        errors = []

        if self.environment == "production":
            # Validate database configuration
            if self.database.url.startswith("sqlite://"):
                errors.append("Production requires non-SQLite database")

            # Validate Redis configuration
            if self.redis.host == "localhost":
                errors.append("Production requires non-localhost Redis")

            # Validate observability
            if self.observability.log_level == "DEBUG":
                errors.append("Production should not use DEBUG log level")

        return errors

    def get_kubernetes_labels(self) -> dict[str, str]:
        """Get standard Kubernetes labels for this service."""
        return {
            "app.kubernetes.io/name": self.service_name,
            "app.kubernetes.io/version": self.service_version,
            "app.kubernetes.io/component": "dataflow-analyzer",
            "app.kubernetes.io/part-of": "osservatorio-platform",
            "app.kubernetes.io/managed-by": "helm",
        }

    def get_resource_requirements(self) -> dict[str, dict[str, str]]:
        """Get Kubernetes resource requirements based on configuration."""
        # Base requirements
        requests = {"cpu": "100m", "memory": "256Mi"}
        limits = {"cpu": "500m", "memory": "512Mi"}

        # Scale based on worker pool size
        if self.scaling.worker_pool_size > 4:
            requests["cpu"] = "200m"
            requests["memory"] = "512Mi"
            limits["cpu"] = "1000m"
            limits["memory"] = "1Gi"

        return {"requests": requests, "limits": limits}
