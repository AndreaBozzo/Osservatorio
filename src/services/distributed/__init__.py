"""
Distributed services package for Kubernetes scalability.

This package provides:
- Redis distributed caching
- Circuit breaker patterns
- Stateless service design
- Resilience patterns
"""

from .circuit_breaker import CircuitBreaker
from .redis_cache_manager import RedisCacheManager
from .state_manager import StatelessServiceManager

__all__ = ["RedisCacheManager", "CircuitBreaker", "StatelessServiceManager"]
