"""
Circuit breaker pattern implementation for resilient service calls.

Provides automatic failure detection and recovery for external dependencies.
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union

from ...utils.logger import get_logger


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5           # Failures before opening
    success_threshold: int = 3           # Successes to close from half-open
    timeout: float = 60.0               # Seconds to wait before half-open
    expected_exception: type = Exception # Exception type to count as failure


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with async support.

    Protects external service calls by:
    - Tracking failure/success rates
    - Opening circuit after threshold failures
    - Allowing test calls after timeout
    - Closing circuit after successful recovery
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name for logging
            config: Configuration settings
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.logger = get_logger(f"{__name__}.{name}")

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._last_success_time = 0.0
        self._next_attempt_time = 0.0

        # Statistics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._state_changes = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking calls)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN

    def _change_state(self, new_state: CircuitState) -> None:
        """Change circuit breaker state with logging."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._state_changes += 1

            self.logger.info(
                f"Circuit breaker state changed: {old_state.value} -> {new_state.value}"
            )

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        return (
            self._state == CircuitState.OPEN and
            time.time() >= self._next_attempt_time
        )

    def _record_success(self) -> None:
        """Record a successful call."""
        self._total_calls += 1
        self._total_successes += 1
        self._last_success_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1

            if self._success_count >= self.config.success_threshold:
                self._reset()

        elif self._state == CircuitState.CLOSED:
            # Reset failure count on successful call
            self._failure_count = 0

    def _record_failure(self) -> None:
        """Record a failed call."""
        self._total_calls += 1
        self._total_failures += 1
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self.config.failure_threshold:
                self._open()

        elif self._state == CircuitState.HALF_OPEN:
            # Return to open state on any failure during testing
            self._open()

    def _open(self) -> None:
        """Open the circuit breaker."""
        self._change_state(CircuitState.OPEN)
        self._next_attempt_time = time.time() + self.config.timeout
        self._success_count = 0

    def _reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._change_state(CircuitState.CLOSED)
        self._failure_count = 0
        self._success_count = 0

    def _half_open(self) -> None:
        """Set circuit breaker to half-open state."""
        self._change_state(CircuitState.HALF_OPEN)
        self._success_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function call through circuit breaker.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from the function call
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._half_open()

        # Block calls if circuit is open
        if self._state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is open. "
                f"Next attempt in {self._next_attempt_time - time.time():.1f}s"
            )

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._record_success()
            return result

        except self.config.expected_exception as e:
            self._record_failure()
            raise e

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to wrap function with circuit breaker.

        Args:
            func: Function to protect

        Returns:
            Wrapped function
        """
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                return await self.call(func, *args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(self.call(func, *args, **kwargs))
            return sync_wrapper

    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Statistics dictionary
        """
        current_time = time.time()

        return {
            "name": self.name,
            "state": self._state.value,
            "total_calls": self._total_calls,
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "current_failure_count": self._failure_count,
            "current_success_count": self._success_count,
            "failure_rate": (
                self._total_failures / self._total_calls
                if self._total_calls > 0 else 0
            ),
            "success_rate": (
                self._total_successes / self._total_calls
                if self._total_calls > 0 else 0
            ),
            "last_failure_time": self._last_failure_time,
            "last_success_time": self._last_success_time,
            "next_attempt_time": self._next_attempt_time,
            "time_until_next_attempt": max(0, self._next_attempt_time - current_time),
            "state_changes": self._state_changes,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
                "expected_exception": self.config.expected_exception.__name__,
            }
        }

    def reset_stats(self) -> None:
        """Reset all statistics (keep current state)."""
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        self._state_changes = 0

        self.logger.info(f"Circuit breaker '{self.name}' statistics reset")

    def force_open(self) -> None:
        """Force circuit breaker to open state."""
        self._open()
        self.logger.warning(f"Circuit breaker '{self.name}' forced to open state")

    def force_close(self) -> None:
        """Force circuit breaker to closed state."""
        self._reset()
        self.logger.info(f"Circuit breaker '{self.name}' forced to closed state")

    def force_half_open(self) -> None:
        """Force circuit breaker to half-open state."""
        self._half_open()
        self.logger.info(f"Circuit breaker '{self.name}' forced to half-open state")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger(__name__)

    def register(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.

        Args:
            name: Circuit breaker name
            config: Configuration settings

        Returns:
            Circuit breaker instance
        """
        if name in self._breakers:
            self.logger.warning(f"Circuit breaker '{name}' already registered")
            return self._breakers[name]

        breaker = CircuitBreaker(name, config)
        self._breakers[name] = breaker

        self.logger.info(f"Registered circuit breaker: {name}")
        return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered circuit breakers."""
        return {
            name: breaker.get_stats()
            for name, breaker in self._breakers.items()
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all circuit breakers."""
        total_breakers = len(self._breakers)
        open_breakers = sum(1 for b in self._breakers.values() if b.is_open)
        half_open_breakers = sum(1 for b in self._breakers.values() if b.is_half_open)

        return {
            "total_circuit_breakers": total_breakers,
            "healthy_breakers": total_breakers - open_breakers - half_open_breakers,
            "open_breakers": open_breakers,
            "half_open_breakers": half_open_breakers,
            "overall_health": "healthy" if open_breakers == 0 else "degraded",
            "breaker_states": {
                name: breaker.state.value
                for name, breaker in self._breakers.items()
            }
        }

    def reset_all_stats(self) -> None:
        """Reset statistics for all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset_stats()

        self.logger.info("Reset statistics for all circuit breakers")


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()
