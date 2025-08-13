"""
Unit tests for K8s CircuitBreaker

Tests the circuit breaker pattern implementation for Kubernetes resilience.
"""

import asyncio

import pytest

from src.services.distributed.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitState,
    circuit_breaker_registry,
)


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout == 60.0
        assert config.expected_exception is Exception

    def test_custom_config(self):
        """Test custom configuration values"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=30.0,
            expected_exception=ValueError,
        )

        assert config.failure_threshold == 3
        assert config.success_threshold == 2
        assert config.timeout == 30.0
        assert config.expected_exception is ValueError


class TestK8sCircuitBreaker:
    """Test K8s CircuitBreaker functionality"""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a CircuitBreaker instance for testing"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1.0,  # Short timeout for testing
        )
        return CircuitBreaker("test_breaker", config)

    def test_circuit_breaker_initialization(self, circuit_breaker):
        """Test CircuitBreaker initialization"""
        assert circuit_breaker.name == "test_breaker"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed is True
        assert circuit_breaker.is_open is False
        assert circuit_breaker.is_half_open is False

    @pytest.mark.asyncio
    async def test_successful_calls(self, circuit_breaker):
        """Test circuit breaker with successful calls"""

        async def successful_function():
            return "success"

        # Make several successful calls
        for _ in range(5):
            result = await circuit_breaker.call(successful_function)
            assert result == "success"

        # Circuit should remain closed
        assert circuit_breaker.is_closed is True

        stats = circuit_breaker.get_stats()
        assert stats["total_calls"] == 5
        assert stats["total_successes"] == 5
        assert stats["total_failures"] == 0

    @pytest.mark.asyncio
    async def test_circuit_opening_on_failures(self, circuit_breaker):
        """Test circuit breaker opening after threshold failures"""

        async def failing_function():
            raise ValueError("Test failure")

        # Make calls that will fail
        for i in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_function)

            if i < 2:
                assert circuit_breaker.is_closed is True
            else:
                assert circuit_breaker.is_open is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_error_when_open(self, circuit_breaker):
        """Test CircuitBreakerError when circuit is open"""

        async def failing_function():
            raise ValueError("Test failure")

        # Trigger circuit opening
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_function)

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(failing_function)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self, circuit_breaker):
        """Test transition from open to half-open state"""

        async def failing_function():
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_function)

        assert circuit_breaker.is_open is True

        # Wait for timeout to pass
        await asyncio.sleep(1.1)

        # Next call should attempt reset (half-open)
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_function)

        # Should be open again after failure in half-open state
        assert circuit_breaker.is_open is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery from open to closed"""
        call_count = 0

        async def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise ValueError("Initial failure")
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(sometimes_failing_function)

        assert circuit_breaker.is_open is True

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Make successful calls to close the circuit
        for _ in range(2):  # success_threshold = 2
            result = await circuit_breaker.call(sometimes_failing_function)
            assert result == "success"

        # Circuit should be closed now
        assert circuit_breaker.is_closed is True

    def test_circuit_breaker_decorator(self, circuit_breaker):
        """Test circuit breaker as decorator"""

        @circuit_breaker
        async def decorated_function(value):
            if value == "fail":
                raise ValueError("Decorated failure")
            return f"decorated_{value}"

        # Test successful call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(decorated_function("success"))
            assert result == "decorated_success"
        finally:
            loop.close()

    def test_circuit_breaker_stats(self, circuit_breaker):
        """Test circuit breaker statistics"""
        stats = circuit_breaker.get_stats()

        required_fields = [
            "name",
            "state",
            "total_calls",
            "total_successes",
            "total_failures",
            "current_failure_count",
            "current_success_count",
            "failure_rate",
            "success_rate",
            "config",
        ]

        for field in required_fields:
            assert field in stats

        assert stats["name"] == "test_breaker"
        assert stats["state"] == CircuitState.CLOSED.value
        assert stats["total_calls"] == 0

    def test_force_state_changes(self, circuit_breaker):
        """Test forcing circuit breaker state changes"""
        # Force open
        circuit_breaker.force_open()
        assert circuit_breaker.is_open is True

        # Force closed
        circuit_breaker.force_close()
        assert circuit_breaker.is_closed is True

        # Force half-open
        circuit_breaker.force_half_open()
        assert circuit_breaker.is_half_open is True

    def test_reset_stats(self, circuit_breaker):
        """Test resetting circuit breaker statistics"""
        # Set some stats
        circuit_breaker._total_calls = 10
        circuit_breaker._total_failures = 3
        circuit_breaker._total_successes = 7

        stats_before = circuit_breaker.get_stats()
        assert stats_before["total_calls"] == 10

        # Reset stats
        circuit_breaker.reset_stats()

        stats_after = circuit_breaker.get_stats()
        assert stats_after["total_calls"] == 0
        assert stats_after["total_failures"] == 0
        assert stats_after["total_successes"] == 0


class TestCircuitBreakerRegistry:
    """Test CircuitBreakerRegistry functionality"""

    @pytest.fixture
    def registry(self):
        """Create a fresh CircuitBreakerRegistry for testing"""
        return CircuitBreakerRegistry()

    def test_registry_registration(self, registry):
        """Test circuit breaker registration"""
        config = CircuitBreakerConfig(failure_threshold=2)

        breaker = registry.register("test_service", config)

        assert breaker.name == "test_service"
        assert breaker.config.failure_threshold == 2
        assert registry.get("test_service") == breaker

    def test_registry_duplicate_registration(self, registry):
        """Test duplicate registration returns existing breaker"""
        breaker1 = registry.register("test_service")
        breaker2 = registry.register("test_service")

        assert breaker1 is breaker2

    def test_registry_get_nonexistent(self, registry):
        """Test getting non-existent circuit breaker"""
        breaker = registry.get("nonexistent")
        assert breaker is None

    def test_registry_get_all_stats(self, registry):
        """Test getting statistics for all circuit breakers"""
        registry.register("service1")
        registry.register("service2")

        all_stats = registry.get_all_stats()

        assert len(all_stats) == 2
        assert "service1" in all_stats
        assert "service2" in all_stats

    def test_registry_health_summary(self, registry):
        """Test getting health summary"""
        breaker1 = registry.register("service1")
        registry.register("service2")

        # Force one breaker open
        breaker1.force_open()

        health = registry.get_health_summary()

        assert health["total_circuit_breakers"] == 2
        assert health["open_breakers"] == 1
        assert health["healthy_breakers"] == 1
        assert health["overall_health"] == "degraded"

    def test_registry_reset_all_stats(self, registry):
        """Test resetting all circuit breaker statistics"""
        breaker1 = registry.register("service1")
        breaker2 = registry.register("service2")

        # Set some stats
        breaker1._total_calls = 5
        breaker2._total_calls = 10

        registry.reset_all_stats()

        assert breaker1.get_stats()["total_calls"] == 0
        assert breaker2.get_stats()["total_calls"] == 0

    def test_global_registry(self):
        """Test global circuit breaker registry"""
        # Test that global registry is available
        assert circuit_breaker_registry is not None

        # Register a breaker
        breaker = circuit_breaker_registry.register("global_test")
        assert breaker.name == "global_test"

        # Retrieve it
        retrieved = circuit_breaker_registry.get("global_test")
        assert retrieved is breaker
