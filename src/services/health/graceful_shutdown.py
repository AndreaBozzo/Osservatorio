"""
Graceful shutdown handler for Kubernetes deployments.

Provides utilities for handling SIGTERM signals and graceful service shutdown
in containerized environments.
"""

import asyncio
import logging
import signal
import sys
from typing import Callable, List, Optional
from datetime import datetime


class GracefulShutdownHandler:
    """
    Handler for graceful service shutdown in Kubernetes environments.

    Manages shutdown hooks, signal handling, and ensures clean service termination
    when receiving SIGTERM from Kubernetes.
    """

    def __init__(self, service_name: str = "unknown", timeout_seconds: int = 30):
        """
        Initialize graceful shutdown handler.

        Args:
            service_name: Name of the service for logging
            timeout_seconds: Maximum time to wait for shutdown completion
        """
        self.service_name = service_name
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

        # Shutdown hooks
        self._shutdown_hooks: List[Callable] = []
        self._is_shutting_down = False
        self._shutdown_event = asyncio.Event()

        # Signal handling
        self._original_handlers = {}
        self._signals_registered = False

    def add_shutdown_hook(self, hook: Callable) -> None:
        """
        Add a shutdown hook function.

        Args:
            hook: Function to call during shutdown (can be sync or async)
        """
        self._shutdown_hooks.append(hook)
        self.logger.debug(f"Added shutdown hook: {hook.__name__}")

    def register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        if self._signals_registered:
            return

        # Handle SIGTERM (Kubernetes pod termination)
        if hasattr(signal, 'SIGTERM'):
            self._original_handlers[signal.SIGTERM] = signal.signal(
                signal.SIGTERM, self._signal_handler
            )

        # Handle SIGINT (Ctrl+C)
        if hasattr(signal, 'SIGINT'):
            self._original_handlers[signal.SIGINT] = signal.signal(
                signal.SIGINT, self._signal_handler
            )

        self._signals_registered = True
        self.logger.info("Signal handlers registered for graceful shutdown")

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        self.logger.info(f"Received {signal_name}, initiating graceful shutdown")

        # Trigger shutdown in async context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.shutdown())
            else:
                # If no event loop is running, create one
                asyncio.run(self.shutdown())
        except RuntimeError:
            # Fallback: set shutdown event and let main loop handle it
            self._is_shutting_down = True
            if not self._shutdown_event.is_set():
                self._shutdown_event.set()

    async def shutdown(self) -> bool:
        """
        Perform graceful shutdown.

        Returns:
            True if shutdown completed successfully, False if timeout
        """
        if self._is_shutting_down:
            return True

        self._is_shutting_down = True
        self._shutdown_event.set()

        self.logger.info(f"Starting graceful shutdown for {self.service_name}")
        start_time = datetime.now()

        try:
            # Execute all shutdown hooks
            shutdown_tasks = []

            for hook in self._shutdown_hooks:
                try:
                    self.logger.debug(f"Executing shutdown hook: {hook.__name__}")

                    if asyncio.iscoroutinefunction(hook):
                        shutdown_tasks.append(hook())
                    else:
                        # Run sync hooks in executor to avoid blocking
                        loop = asyncio.get_event_loop()
                        shutdown_tasks.append(loop.run_in_executor(None, hook))

                except Exception as e:
                    self.logger.error(f"Error preparing shutdown hook {hook.__name__}: {e}")

            # Wait for all hooks to complete with timeout
            if shutdown_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*shutdown_tasks, return_exceptions=True),
                    timeout=self.timeout_seconds
                )

            shutdown_duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Graceful shutdown completed in {shutdown_duration:.2f}s")

            return True

        except asyncio.TimeoutError:
            shutdown_duration = (datetime.now() - start_time).total_seconds()
            self.logger.warning(f"Graceful shutdown timed out after {shutdown_duration:.2f}s")
            return False

        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            return False

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._is_shutting_down

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()

    def restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._original_handlers.items():
            signal.signal(sig, handler)

        self._original_handlers.clear()
        self._signals_registered = False
        self.logger.debug("Original signal handlers restored")

    async def __aenter__(self):
        """Async context manager entry."""
        self.register_signal_handlers()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if not self._is_shutting_down:
            await self.shutdown()
        self.restore_signal_handlers()


def create_shutdown_handler(service_name: str = "service",
                          timeout_seconds: int = 30) -> GracefulShutdownHandler:
    """
    Create a graceful shutdown handler.

    Args:
        service_name: Name of the service
        timeout_seconds: Shutdown timeout

    Returns:
        GracefulShutdownHandler instance
    """
    return GracefulShutdownHandler(service_name, timeout_seconds)
