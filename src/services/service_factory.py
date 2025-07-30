"""
Service factory for dependency injection and service creation.

This module provides factory functions to create service instances
with proper dependency injection, following the dependency inversion principle.
"""

from functools import lru_cache
from typing import Optional

from ..api.production_istat_client import ProductionIstatClient
from ..database.sqlite.repository import UnifiedDataRepository, get_unified_repository
from ..utils.logger import get_logger
from ..utils.temp_file_manager import TempFileManager, get_temp_manager
from .dataflow_analysis_service import DataflowAnalysisService


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


# Global service container instance
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """Get or create the global service container."""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


@lru_cache(maxsize=1)
def create_dataflow_analysis_service(
    istat_client: Optional[ProductionIstatClient] = None,
    repository: Optional[UnifiedDataRepository] = None,
    temp_file_manager: Optional[TempFileManager] = None,
) -> DataflowAnalysisService:
    """
    Create DataflowAnalysisService with proper dependency injection.

    This factory function creates the service with all required dependencies,
    using default implementations where not provided.

    Args:
        istat_client: Optional ISTAT client (will create default if None)
        repository: Optional repository (will create default if None)
        temp_file_manager: Optional temp file manager (will create default if None)

    Returns:
        Configured DataflowAnalysisService instance
    """
    logger = get_logger(__name__)
    logger.info("Creating DataflowAnalysisService with dependency injection")

    # Create dependencies if not provided
    if istat_client is None:
        logger.debug("Creating default ProductionIstatClient")
        istat_client = ProductionIstatClient()

    if repository is None:
        logger.debug("Creating default UnifiedDataRepository")
        repository = get_unified_repository()

    if temp_file_manager is None:
        logger.debug("Creating default TempFileManager")
        temp_file_manager = get_temp_manager()

    # Create and configure the service
    service = DataflowAnalysisService(
        istat_client=istat_client,
        repository=repository,
        temp_file_manager=temp_file_manager,
    )

    logger.info("DataflowAnalysisService created successfully")
    return service


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

        # Create and register business services
        dataflow_service = DataflowAnalysisService(
            istat_client=istat_client,
            repository=repository,
            temp_file_manager=temp_file_manager,
        )
        container.register(DataflowAnalysisService, dataflow_service)

        logger.info("Service container initialized successfully")
        return container

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise


def get_dataflow_analysis_service() -> DataflowAnalysisService:
    """
    Get or create DataflowAnalysisService instance.

    This is the main entry point for getting the dataflow analysis service.
    It will use the service container if available, or create a new instance.

    Returns:
        DataflowAnalysisService instance
    """
    container = get_service_container()

    if container.has(DataflowAnalysisService):
        return container.get(DataflowAnalysisService)

    # If not in container, create with default dependencies
    return create_dataflow_analysis_service()


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

        # Check DataflowAnalysisService health
        if container.has(DataflowAnalysisService):
            health_status["services"]["dataflow_analysis"] = {
                "status": "healthy",
                "details": "Service available",
            }

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


def get_dataflow_service_dependency() -> DataflowAnalysisService:
    """
    FastAPI dependency function for DataflowAnalysisService.

    Use this function as a FastAPI dependency to inject the service
    into your endpoint handlers.

    Example:
        @app.get("/api/analysis/dataflows")
        async def analyze_dataflows(
            service: DataflowAnalysisService = Depends(get_dataflow_service_dependency)
        ):
            return await service.analyze_dataflows_from_xml(xml_content)
    """
    return get_dataflow_analysis_service()


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
