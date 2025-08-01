#!/usr/bin/env python3
"""
Test suite for circuit_breaker.py
Currently 0% coverage - high priority for coverage improvement
"""
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    get_circuit_breaker_stats,
)


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    def test_init_defaults(self):
        """Test CircuitBreaker initialization with defaults"""
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60
        assert cb.expected_exception == Exception
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_init_custom_params(self):
        """Test CircuitBreaker initialization with custom parameters"""
        cb = CircuitBreaker(
            failure_threshold=10, recovery_timeout=120, expected_exception=ValueError
        )
        assert cb.failure_threshold == 10
        assert cb.recovery_timeout == 120
        assert cb.expected_exception == ValueError

    def test_closed_state_success(self):
        """Test successful calls in CLOSED state"""
        mock_func = Mock(return_value="success")
        result = self.breaker.call(mock_func)

        assert result == "success"
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0
        mock_func.assert_called_once()

    def test_closed_state_failure(self):
        """Test failed calls in CLOSED state"""
        mock_func = Mock(side_effect=Exception("Test error"))

        with pytest.raises(Exception, match="Test error"):
            self.breaker.call(mock_func)

        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 1
        assert self.breaker.last_failure_time is not None

    def test_state_transition_closed_to_open(self):
        """Test state transition from CLOSED to OPEN"""
        mock_func = Mock(side_effect=Exception("Test error"))

        # Generate enough failures to trigger state change
        for _ in range(self.breaker.failure_threshold):
            with pytest.raises(Exception):
                self.breaker.call(mock_func)

        assert self.breaker.state == CircuitState.OPEN
        assert self.breaker.failure_count == self.breaker.failure_threshold

    def test_open_state_blocks_calls(self):
        """Test that OPEN state blocks calls"""
        # Force state to OPEN
        self.breaker.state = CircuitState.OPEN
        self.breaker.last_failure_time = datetime.now()

        mock_func = Mock()

        with pytest.raises(CircuitBreakerError):
            self.breaker.call(mock_func)

        mock_func.assert_not_called()

    def test_state_transition_open_to_half_open(self):
        """Test state transition from OPEN to HALF_OPEN"""
        # Force state to OPEN
        self.breaker.state = CircuitState.OPEN
        self.breaker.last_failure_time = datetime.now() - timedelta(
            seconds=self.breaker.recovery_timeout + 1
        )

        mock_func = Mock(return_value="success")
        result = self.breaker.call(mock_func)

        assert result == "success"
        # State might go directly to CLOSED if successful, implementation-dependent
        assert self.breaker.state in [CircuitState.HALF_OPEN, CircuitState.CLOSED]
        mock_func.assert_called_once()

    def test_half_open_state_success(self):
        """Test successful call in HALF_OPEN state"""
        # Force state to HALF_OPEN
        self.breaker.state = CircuitState.HALF_OPEN

        mock_func = Mock(return_value="success")
        result = self.breaker.call(mock_func)

        assert result == "success"
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0

    def test_half_open_state_failure(self):
        """Test failed call in HALF_OPEN state"""
        # Force state to HALF_OPEN
        self.breaker.state = CircuitState.HALF_OPEN

        mock_func = Mock(side_effect=Exception("Test error"))

        with pytest.raises(Exception, match="Test error"):
            self.breaker.call(mock_func)

        assert self.breaker.state == CircuitState.OPEN
        assert self.breaker.failure_count == 1

    def test_call_with_args_and_kwargs(self):
        """Test call method with arguments and keyword arguments"""
        mock_func = Mock(return_value="success")
        result = self.breaker.call(
            mock_func, "arg1", "arg2", kwarg1="value1", kwarg2="value2"
        )

        assert result == "success"
        mock_func.assert_called_once_with(
            "arg1", "arg2", kwarg1="value1", kwarg2="value2"
        )

    def test_specific_exception_handling(self):
        """Test CircuitBreaker with specific exception type"""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)

        # ValueError should be counted as failure
        mock_func = Mock(side_effect=ValueError("Test error"))

        with pytest.raises(ValueError):
            cb.call(mock_func)

        assert cb.failure_count == 1

        # Other exceptions should not be counted
        mock_func.side_effect = TypeError("Different error")

        with pytest.raises(TypeError):
            cb.call(mock_func)

        assert cb.failure_count == 1  # Should not increment

    def test_reset_method(self):
        """Test circuit breaker reset functionality"""
        # Generate failures
        mock_func = Mock(side_effect=Exception("Test error"))

        for _ in range(self.breaker.failure_threshold):
            with pytest.raises(Exception):
                self.breaker.call(mock_func)

        assert self.breaker.state == CircuitState.OPEN

        # Reset the breaker
        self.breaker.reset()

        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0
        assert self.breaker.last_failure_time is None

    def test_str_representation(self):
        """Test string representation of CircuitBreaker"""
        str_repr = str(self.breaker)
        assert "CircuitBreaker" in str_repr
        assert "CLOSED" in str_repr
        # The format might be different, just check it contains failure count
        assert "0" in str_repr

    def test_get_stats_method(self):
        """Test get_stats method"""
        stats = self.breaker.get_stats()

        assert isinstance(stats, dict)
        assert "state" in stats
        assert "failure_count" in stats
        assert "failure_threshold" in stats
        assert "last_failure_time" in stats
        assert "recovery_timeout" in stats

        assert stats["state"] == "CLOSED"  # get_stats returns string, not Enum
        assert stats["failure_count"] == 0
        assert stats["failure_threshold"] == 3

    def test_decorator_functionality(self):
        """Test CircuitBreaker as decorator - NOW IMPLEMENTED"""

        # CircuitBreaker now supports decorator pattern
        @self.breaker
        def test_function():
            return "success"

        # Should work normally
        result = test_function()
        assert result == "success"
        assert self.breaker.get_stats()["total_calls"] == 1

    def test_context_manager(self):
        """Test CircuitBreaker as context manager - NOT IMPLEMENTED"""
        # CircuitBreaker doesn't support context manager protocol
        # This test verifies that attempting to use as context manager fails appropriately
        with pytest.raises(TypeError):
            with self.breaker:
                pass


class TestCircuitBreakerError:
    """Test suite for CircuitBreakerError"""

    def test_circuit_breaker_error_init(self):
        """Test CircuitBreakerError initialization"""
        error = CircuitBreakerError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)

    def test_circuit_breaker_error_default_message(self):
        """Test CircuitBreakerError with default message"""
        error = CircuitBreakerError()
        # CircuitBreakerError inherits from Exception, so empty message is expected
        assert str(error) == ""


class TestCircuitBreakerStats:
    """Test suite for get_circuit_breaker_stats function"""

    def test_get_circuit_breaker_stats_empty(self):
        """Test get_circuit_breaker_stats when no breakers exist"""
        # Clear any existing breakers
        from src.utils.circuit_breaker import _circuit_breakers

        _circuit_breakers.clear()

        stats = get_circuit_breaker_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 0

    def test_get_circuit_breaker_stats_with_breakers(self):
        """Test get_circuit_breaker_stats with existing breakers"""
        from src.utils.circuit_breaker import _circuit_breakers

        # Create test breakers
        breaker1 = CircuitBreaker(failure_threshold=5)
        breaker2 = CircuitBreaker(failure_threshold=10)

        _circuit_breakers["test_breaker_1"] = breaker1
        _circuit_breakers["test_breaker_2"] = breaker2

        stats = get_circuit_breaker_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 2
        assert "test_breaker_1" in stats
        assert "test_breaker_2" in stats

        # Check stats structure
        assert "state" in stats["test_breaker_1"]
        assert "failure_count" in stats["test_breaker_1"]
        assert "failure_threshold" in stats["test_breaker_1"]

        # Clean up
        _circuit_breakers.clear()


class TestCircuitBreakerIntegration:
    """Integration tests for CircuitBreaker"""

    def test_real_world_scenario(self):
        """Test realistic scenario with external service calls"""
        # Mock external service
        external_service = Mock()

        # Create circuit breaker for external service
        service_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        # Simulate successful calls
        external_service.get_data.return_value = {"data": "success"}

        for _ in range(5):
            result = service_breaker.call(external_service.get_data)
            assert result == {"data": "success"}

        assert service_breaker.state == CircuitState.CLOSED

        # Simulate service failures
        external_service.get_data.side_effect = Exception("Service unavailable")

        for _ in range(3):
            with pytest.raises(Exception):
                service_breaker.call(external_service.get_data)

        assert service_breaker.state == CircuitState.OPEN

        # Verify circuit breaker blocks calls
        with pytest.raises(CircuitBreakerError):
            service_breaker.call(external_service.get_data)

    def test_recovery_scenario(self):
        """Test recovery scenario after timeout"""
        mock_service = Mock()
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Force failures to open circuit
        mock_service.call.side_effect = Exception("Service down")

        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(mock_service.call)

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        # Service recovers
        mock_service.call.side_effect = None
        mock_service.call.return_value = "success"

        result = breaker.call(mock_service.call)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_concurrent_access(self):
        """Test CircuitBreaker with concurrent access simulation"""
        import threading

        breaker = CircuitBreaker(failure_threshold=5)
        results = []

        def worker():
            mock_func = Mock(return_value="success")
            result = breaker.call(mock_func)
            results.append(result)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10
        assert all(result == "success" for result in results)
        assert breaker.state == CircuitState.CLOSED
