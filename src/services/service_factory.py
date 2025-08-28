"""
Service factory for dependency injection and service creation.

This module provides factory functions to create service instances
with proper dependency injection, following the dependency inversion principle.
"""

from datetime import datetime
from typing import Any, Optional

from ..api.production_istat_client import ProductionIstatClient
from ..database.sqlite.repository import UnifiedDataRepository, get_unified_repository
from ..utils.logger import get_logger
from ..utils.temp_file_manager import TempFileManager, get_temp_manager


class ServiceContainer:
    """
    Simple service container for dependency injection.

    Manages service instances and their dependencies, ensuring
    proper initialization order and singleton behavior where appropriate.
    """

    def __init__(self):
        self._services = {}
        self._logger = get_logger(__name__)

    def register(self, service_type: type, instance: object) -> None:
        """Register a service instance."""
        self._services[service_type] = instance
        self._logger.debug(f"Registered service: {service_type.__name__}")

    def get(self, service_type: type) -> object:
        """Get a service instance."""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} not registered")
        return self._services[service_type]

    def has(self, service_type: type) -> bool:
        """Check if a service is registered."""
        return service_type in self._services

    def health_check(self) -> dict[str, Any]:
        """
        Perform health check on registered services.

        Returns:
            Dict containing health status of all services
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "registered_count": len(self._services),
        }

        for service_type, service_instance in self._services.items():
            service_name = service_type.__name__

            try:
                # Check if service has its own health_check method
                if hasattr(service_instance, "health_check"):
                    service_health = service_instance.health_check()
                    health_status["services"][service_name] = service_health
                elif hasattr(service_instance, "get_status"):
                    service_health = service_instance.get_status()
                    health_status["services"][service_name] = service_health
                else:
                    # Basic check - service exists and is not None
                    health_status["services"][service_name] = {
                        "status": (
                            "healthy" if service_instance is not None else "unhealthy"
                        ),
                        "type": str(type(service_instance)),
                    }

            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health_status["status"] = "degraded"

        return health_status


# Global service container instance
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """Get or create the global service container."""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


def initialize_services() -> ServiceContainer:
    """
    Initialize all services with proper dependency injection.

    This function creates and registers all services in the container,
    ensuring proper initialization order and dependency resolution.

    Returns:
        Configured service container
    """
    logger = get_logger(__name__)
    logger.info("Initializing service container")

    container = get_service_container()

    try:
        # Create core dependencies
        istat_client = ProductionIstatClient()
        repository = get_unified_repository()
        temp_file_manager = get_temp_manager()

        # Register core services
        container.register(ProductionIstatClient, istat_client)
        container.register(UnifiedDataRepository, repository)
        container.register(TempFileManager, temp_file_manager)

        # Core services registered

        logger.info("Service container initialized successfully")
        return container

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise


# Service health check utilities


async def check_service_health() -> dict:
    """
    Check health of all registered services.

    Returns:
        Dictionary with health status of each service
    """
    logger = get_logger(__name__)
    container = get_service_container()
    health_status = {"overall": "healthy", "services": {}, "timestamp": None}

    try:
        from datetime import datetime

        health_status["timestamp"] = datetime.now().isoformat()

        # Check ProductionIstatClient health
        if container.has(ProductionIstatClient):
            try:
                client = container.get(ProductionIstatClient)
                status = client.get_status()  # Assuming this method exists
                health_status["services"]["istat_client"] = {
                    "status": "healthy",
                    "details": status,
                }
            except Exception as e:
                health_status["services"]["istat_client"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health_status["overall"] = "degraded"

        # Check UnifiedDataRepository health
        if container.has(UnifiedDataRepository):
            try:
                repository = container.get(UnifiedDataRepository)
                # Test database connectivity
                test_result = (
                    repository.get_system_status()
                )  # Assuming this method exists
                health_status["services"]["repository"] = {
                    "status": "healthy",
                    "details": test_result,
                }
            except Exception as e:
                health_status["services"]["repository"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health_status["overall"] = "degraded"

        logger.info(
            f"Service health check completed - Overall status: {health_status['overall']}"
        )

    except Exception as e:
        logger.error(f"Service health check failed: {e}", exc_info=True)
        health_status["overall"] = "unhealthy"
        health_status["error"] = str(e)

    return health_status


# Context manager for service lifecycle


class ServiceContext:
    """Context manager for service lifecycle management."""

    def __init__(self):
        self.container = None
        self.logger = get_logger(__name__)

    def __enter__(self) -> ServiceContainer:
        """Initialize services when entering context."""
        self.logger.info("Entering service context")
        self.container = initialize_services()
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup services when exiting context."""
        self.logger.info("Exiting service context")

        if self.container:
            # Cleanup services if they have cleanup methods
            try:
                if self.container.has(TempFileManager):
                    temp_manager = self.container.get(TempFileManager)
                    temp_manager.cleanup()  # Assuming this method exists

            except Exception as e:
                self.logger.error(f"Error during service cleanup: {e}")

        # Clear global container
        global _service_container
        _service_container = None


# Convenience functions for FastAPI dependency injection


def get_repository_dependency() -> UnifiedDataRepository:
    """FastAPI dependency function for UnifiedDataRepository."""
    container = get_service_container()
    if container.has(UnifiedDataRepository):
        return container.get(UnifiedDataRepository)
    return get_unified_repository()


def get_istat_client_dependency() -> ProductionIstatClient:
    """FastAPI dependency function for ProductionIstatClient."""
    container = get_service_container()
    if container.has(ProductionIstatClient):
        return container.get(ProductionIstatClient)
    return ProductionIstatClient()
