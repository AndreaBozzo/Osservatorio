"""
Stateless Service Manager for Kubernetes deployments.

Provides utilities for managing stateless services in a Kubernetes environment,
ensuring services can be scaled horizontally without state dependencies.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional


class StatelessServiceManager:
    """
    Manager for stateless service design patterns in Kubernetes.

    Ensures services follow cloud-native principles:
    - No local state dependencies
    - Horizontal scalability
    - Graceful shutdown handling
    - Resource cleanup
    """

    def __init__(self, service_name: str = "unknown"):
        """
        Initialize the stateless service manager.

        Args:
            service_name: Name of the service for logging and identification
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

        # Resource tracking
        self._active_resources: set[str] = set()
        self._cleanup_callbacks: dict[str, callable] = {}

        # Service state
        self._is_shutting_down = False
        self._startup_time = datetime.now()

        # Resource limits
        self._max_memory_mb: Optional[int] = None
        self._max_cpu_cores: Optional[float] = None

    def register_resource(
        self, resource_id: str, cleanup_callback: callable = None
    ) -> None:
        """
        Register a resource that needs cleanup on shutdown.

        Args:
            resource_id: Unique identifier for the resource
            cleanup_callback: Function to call when cleaning up this resource
        """
        self._active_resources.add(resource_id)
        if cleanup_callback:
            self._cleanup_callbacks[resource_id] = cleanup_callback

        self.logger.debug(f"Registered resource: {resource_id}")

    def unregister_resource(self, resource_id: str) -> None:
        """
        Unregister a resource (typically when it's no longer needed).

        Args:
            resource_id: Unique identifier for the resource
        """
        self._active_resources.discard(resource_id)
        self._cleanup_callbacks.pop(resource_id, None)

        self.logger.debug(f"Unregistered resource: {resource_id}")

    async def graceful_shutdown(self, timeout_seconds: int = 30) -> bool:
        """
        Perform graceful shutdown of all registered resources.

        Args:
            timeout_seconds: Maximum time to wait for cleanup

        Returns:
            True if shutdown completed successfully, False if timeout
        """
        self.logger.info(f"Starting graceful shutdown for {self.service_name}")
        self._is_shutting_down = True

        start_time = datetime.now()

        try:
            # Execute cleanup callbacks
            cleanup_tasks = []
            for resource_id, callback in self._cleanup_callbacks.items():
                self.logger.debug(f"Cleaning up resource: {resource_id}")

                if asyncio.iscoroutinefunction(callback):
                    cleanup_tasks.append(callback())
                else:
                    # Run sync callbacks in executor
                    loop = asyncio.get_event_loop()
                    cleanup_tasks.append(loop.run_in_executor(None, callback))

            # Wait for all cleanup tasks with timeout
            if cleanup_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=timeout_seconds,
                )

            # Clear resource tracking
            self._active_resources.clear()
            self._cleanup_callbacks.clear()

            shutdown_duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Graceful shutdown completed in {shutdown_duration:.2f}s")

            return True

        except asyncio.TimeoutError:
            shutdown_duration = (datetime.now() - start_time).total_seconds()
            self.logger.warning(
                f"Graceful shutdown timed out after {shutdown_duration:.2f}s"
            )
            return False

        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            return False

    def is_shutting_down(self) -> bool:
        """Check if the service is currently shutting down."""
        return self._is_shutting_down

    def get_active_resources(self) -> set[str]:
        """Get set of currently active resource IDs."""
        return self._active_resources.copy()

    def get_service_info(self) -> dict[str, Any]:
        """
        Get service information for monitoring and debugging.

        Returns:
            Dictionary with service information
        """
        uptime = datetime.now() - self._startup_time

        return {
            "service_name": self.service_name,
            "startup_time": self._startup_time.isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "active_resources": len(self._active_resources),
            "is_shutting_down": self._is_shutting_down,
            "resource_ids": list(self._active_resources),
        }

    def set_resource_limits(
        self, max_memory_mb: Optional[int] = None, max_cpu_cores: Optional[float] = None
    ) -> None:
        """
        Set resource limits for monitoring (informational only).

        Args:
            max_memory_mb: Maximum memory usage in MB
            max_cpu_cores: Maximum CPU cores to use
        """
        self._max_memory_mb = max_memory_mb
        self._max_cpu_cores = max_cpu_cores

        self.logger.info(
            f"Resource limits set: memory={max_memory_mb}MB, cpu={max_cpu_cores} cores"
        )

    def validate_stateless_design(self) -> dict[str, Any]:
        """
        Validate that the service follows stateless design principles.

        Returns:
            Dictionary with validation results and recommendations
        """
        validation_results = {
            "is_stateless_compliant": True,
            "issues": [],
            "recommendations": [],
            "score": 100,
        }

        # Check for long-running resources (potential state)
        long_running_threshold = timedelta(hours=1)
        current_time = datetime.now()
        uptime = current_time - self._startup_time

        if uptime > long_running_threshold and len(self._active_resources) > 10:
            validation_results["issues"].append(
                f"High resource count ({len(self._active_resources)}) after {uptime}"
            )
            validation_results["recommendations"].append(
                "Consider implementing resource pooling or cleanup strategies"
            )
            validation_results["score"] -= 10

        # Check for missing cleanup callbacks
        resources_without_cleanup = len(self._active_resources) - len(
            self._cleanup_callbacks
        )
        if resources_without_cleanup > 0:
            validation_results["issues"].append(
                f"{resources_without_cleanup} resources registered without cleanup callbacks"
            )
            validation_results["recommendations"].append(
                "Register cleanup callbacks for all resources to ensure proper shutdown"
            )
            validation_results["score"] -= 20

        # Final compliance check
        validation_results["is_stateless_compliant"] = (
            len(validation_results["issues"]) == 0
        )

        return validation_results


class ResourceManager:
    """
    Context manager for automatic resource cleanup.

    Ensures resources are properly cleaned up even if exceptions occur.
    """

    def __init__(self, service_manager: StatelessServiceManager, resource_id: str):
        """
        Initialize resource manager.

        Args:
            service_manager: Parent service manager
            resource_id: Unique identifier for this resource
        """
        self.service_manager = service_manager
        self.resource_id = resource_id
        self._cleanup_func: Optional[callable] = None

    def set_cleanup(self, cleanup_func: callable) -> "ResourceManager":
        """
        Set cleanup function for this resource.

        Args:
            cleanup_func: Function to call during cleanup

        Returns:
            Self for method chaining
        """
        self._cleanup_func = cleanup_func
        return self

    def __enter__(self) -> "ResourceManager":
        """Enter context manager."""
        self.service_manager.register_resource(self.resource_id, self._cleanup_func)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager with cleanup."""
        self.service_manager.unregister_resource(self.resource_id)

        # If cleanup function was provided, call it
        if self._cleanup_func:
            try:
                if asyncio.iscoroutinefunction(self._cleanup_func):
                    # Can't await in __exit__, so schedule it
                    loop = asyncio.get_event_loop()
                    loop.create_task(self._cleanup_func())
                else:
                    self._cleanup_func()
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Error during resource cleanup for {self.resource_id}: {e}"
                )


# Singleton instance for global access
_default_service_manager: Optional[StatelessServiceManager] = None


def get_default_service_manager() -> StatelessServiceManager:
    """Get or create the default service manager instance."""
    global _default_service_manager
    if _default_service_manager is None:
        _default_service_manager = StatelessServiceManager("default")
    return _default_service_manager


def create_resource_manager(
    resource_id: str, service_manager: Optional[StatelessServiceManager] = None
) -> ResourceManager:
    """
    Create a resource manager for automatic cleanup.

    Args:
        resource_id: Unique identifier for the resource
        service_manager: Service manager to use (default if None)

    Returns:
        ResourceManager instance
    """
    if service_manager is None:
        service_manager = get_default_service_manager()

    return ResourceManager(service_manager, resource_id)
