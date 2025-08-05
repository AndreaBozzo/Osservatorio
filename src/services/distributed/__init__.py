"""
Distributed services package for Kubernetes scalability.

This package provides:
- Redis distributed caching
- Circuit breaker patterns
- Stateless service design
- Resilience patterns
"""

from .redis_cache_manager import RedisCacheManager
from .circuit_breaker import CircuitBreaker
from .state_manager import StatelessServiceManager

__all__ = ["RedisCacheManager", "CircuitBreaker", "StatelessServiceManager"]
