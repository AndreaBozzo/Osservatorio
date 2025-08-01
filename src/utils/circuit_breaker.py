"""Circuit breaker implementation for resilient system design.

This module provides a circuit breaker pattern to prevent cascading failures
and improve system resilience when dealing with external dependencies.
"""
import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Circuit breaker is open, rejecting calls
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back online


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation.

    The circuit breaker monitors failures and opens the circuit when
    the failure threshold is exceeded. After a recovery timeout,
    it allows a limited number of test calls to determine if the
    service has recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Union[type[Exception], tuple] = Exception,
        name: Optional[str] = None,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before allowing test calls
            expected_exception: Exception type(s) that count as failures
            name: Optional name for the circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "CircuitBreaker"

        # State tracking
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.success_count = 0

        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0

        logger.info(f"Circuit breaker '{self.name}' initialized")

    def __call__(self, func: Callable) -> Callable:
        """Make circuit breaker usable as a decorator.

        Args:
            func: Function to wrap with circuit breaker

        Returns:
            Wrapped function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function call through the circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Any: Result of the function call

        Raises:
            CircuitBreakerError: When circuit breaker is open
            Exception: Original exception from the function
        """
        self.total_calls += 1

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting call")
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure(e)
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.last_failure_time is None:
            return True

        return datetime.now() - self.last_failure_time > timedelta(
            seconds=self.recovery_timeout
        )

    def _on_success(self) -> None:
        """Handle successful function call."""
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # Reset circuit breaker after successful test
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' reset to CLOSED")

        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, exception: Exception) -> None:
        """Handle failed function call."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        logger.warning(
            f"Circuit breaker '{self.name}' recorded failure {self.failure_count}: {exception}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Failure during test, reopen circuit
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' reopened after test failure")

        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open circuit
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker '{self.name}' opened due to {self.failure_count} failures"
            )

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics.

        Returns:
            Dict containing circuit breaker statistics
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": self.total_failures / max(self.total_calls, 1),
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    def __str__(self) -> str:
        """String representation of circuit breaker."""
        return f"CircuitBreaker(name='{self.name}', state={self.state.value}, failures={self.failure_count})"


# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: Union[type[Exception], tuple] = Exception,
) -> CircuitBreaker:
    """Get or create a circuit breaker by name.

    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time in seconds before allowing test calls
        expected_exception: Exception type(s) that count as failures

    Returns:
        CircuitBreaker: The circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name,
        )

    return _circuit_breakers[name]


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: Union[type[Exception], tuple] = Exception,
    name: Optional[str] = None,
):
    """Decorator to wrap functions with circuit breaker.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time in seconds before allowing test calls
        expected_exception: Exception type(s) that count as failures
        name: Optional name for the circuit breaker
    """

    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = get_circuit_breaker(
            breaker_name, failure_threshold, recovery_timeout, expected_exception
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        # Attach circuit breaker to the wrapper for access
        wrapper.circuit_breaker = breaker

        return wrapper

    return decorator


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers.

    Returns:
        Dict mapping circuit breaker names to instances
    """
    return _circuit_breakers.copy()


def reset_all_circuit_breakers() -> None:
    """Reset all registered circuit breakers."""
    for breaker in _circuit_breakers.values():
        breaker.reset()
    logger.info("All circuit breakers reset")


def get_circuit_breaker_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all circuit breakers.

    Returns:
        Dict mapping circuit breaker names to their statistics
    """
    return {name: breaker.get_stats() for name, breaker in _circuit_breakers.items()}
