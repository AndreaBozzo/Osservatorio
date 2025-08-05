"""
Redis-based distributed caching manager for Kubernetes scalability.

Provides distributed caching with TTL, serialization, and connection pooling.
"""

import asyncio
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from pydantic import BaseModel

from ...utils.logger import get_logger
from ..config.environment_config import RedisConfig


class CacheEntry(BaseModel):
    """Represents a cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime
    tags: List[str] = []
    size_bytes: int = 0


class CacheStats(BaseModel):
    """Cache statistics for monitoring."""

    total_keys: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    memory_usage_mb: float = 0.0
    avg_response_time_ms: float = 0.0
    operations_per_second: float = 0.0


class RedisCacheManager:
    """
    Distributed caching manager using Redis.

    Features:
    - Async Redis operations with connection pooling
    - TTL-based expiration
    - JSON and pickle serialization
    - Tag-based cache invalidation
    - Performance monitoring
    - Graceful degradation when Redis unavailable
    """

    def __init__(self, config: RedisConfig, key_prefix: str = "dataflow:cache:"):
        """
        Initialize Redis cache manager.

        Args:
            config: Redis configuration
            key_prefix: Prefix for all cache keys
        """
        self.config = config
        self.key_prefix = key_prefix
        self.logger = get_logger(__name__)

        # Connection pool
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

        # Statistics tracking
        self._stats = CacheStats()
        self._operation_times: List[float] = []
        self._hit_count = 0
        self._miss_count = 0

        # Circuit breaker state
        self._is_available = True
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 60  # seconds

    async def initialize(self) -> bool:
        """
        Initialize Redis connection pool.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create connection pool
            self._pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=False,  # We handle encoding ourselves
            )

            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()

            self.logger.info(
                f"Redis cache initialized: {self.config.host}:{self.config.port}/{self.config.db}"
            )
            self._is_available = True
            self._failure_count = 0

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Redis cache: {e}")
            self._mark_failure()
            return False

    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

        self.logger.info("Redis cache connections closed")

    def _build_key(self, key: str) -> str:
        """Build full cache key with prefix."""
        return f"{self.key_prefix}{key}"

    def _mark_failure(self) -> None:
        """Mark a Redis operation failure for circuit breaker."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._failure_count >= self._circuit_breaker_threshold:
            self._is_available = False
            self.logger.warning(
                f"Redis circuit breaker opened after {self._failure_count} failures"
            )

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should be reset."""
        if not self._is_available and self._last_failure_time:
            if (datetime.now() - self._last_failure_time).seconds > self._circuit_breaker_timeout:
                self.logger.info("Attempting to reset Redis circuit breaker")
                self._is_available = True
                self._failure_count = 0
                return True

        return self._is_available

    async def _execute_with_fallback(self, operation, *args, **kwargs) -> Any:
        """Execute Redis operation with circuit breaker and fallback."""
        if not self._check_circuit_breaker():
            return None

        if not self._client:
            await self.initialize()
            if not self._client:
                return None

        start_time = datetime.now()

        try:
            result = await operation(*args, **kwargs)

            # Reset failure count on success
            if self._failure_count > 0:
                self._failure_count = max(0, self._failure_count - 1)

            # Track performance
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self._operation_times.append(duration)

            # Keep only last 100 operations for moving average
            if len(self._operation_times) > 100:
                self._operation_times = self._operation_times[-100:]

            return result

        except Exception as e:
            self.logger.warning(f"Redis operation failed: {e}")
            self._mark_failure()
            return None

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        full_key = self._build_key(key)

        result = await self._execute_with_fallback(
            self._client.get, full_key
        )

        if result is not None:
            try:
                # Try JSON decode first, then pickle
                try:
                    value = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    value = pickle.loads(result)

                self._hit_count += 1
                self.logger.debug(f"Cache hit for key: {key}")
                return value

            except Exception as e:
                self.logger.warning(f"Failed to deserialize cached value for {key}: {e}")

        self._miss_count += 1
        self.logger.debug(f"Cache miss for key: {key}")
        return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Tags for cache invalidation

        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key)
        tags = tags or []

        try:
            # Try JSON serialization first, then pickle
            try:
                if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                    serialized = json.dumps(value, default=str)
                else:
                    raise TypeError("Use pickle for complex objects")
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)

            # Set value with TTL
            result = await self._execute_with_fallback(
                self._client.set, full_key, serialized, ex=ttl
            )

            if result:
                # Store tags for invalidation
                if tags:
                    for tag in tags:
                        tag_key = self._build_key(f"tag:{tag}")
                        await self._execute_with_fallback(
                            self._client.sadd, tag_key, full_key
                        )
                        # Set TTL for tag key as well
                        if ttl:
                            await self._execute_with_fallback(
                                self._client.expire, tag_key, ttl
                            )

                self.logger.debug(f"Cache set for key: {key} (TTL: {ttl})")
                return True

        except Exception as e:
            self.logger.warning(f"Failed to cache value for {key}: {e}")

        return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        full_key = self._build_key(key)

        result = await self._execute_with_fallback(
            self._client.delete, full_key
        )

        if result:
            self.logger.debug(f"Cache delete for key: {key}")
            return True

        return False

    async def delete_by_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.

        Args:
            pattern: Pattern to match (Redis pattern syntax)

        Returns:
            Number of keys deleted
        """
        full_pattern = self._build_key(pattern)

        keys = await self._execute_with_fallback(
            self._client.keys, full_pattern
        )

        if keys:
            deleted = await self._execute_with_fallback(
                self._client.delete, *keys
            )

            if deleted:
                self.logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted

        return 0

    async def delete_by_tags(self, tags: List[str]) -> int:
        """
        Delete all keys associated with given tags.

        Args:
            tags: List of tags

        Returns:
            Number of keys deleted
        """
        total_deleted = 0

        for tag in tags:
            tag_key = self._build_key(f"tag:{tag}")

            # Get all keys with this tag
            keys = await self._execute_with_fallback(
                self._client.smembers, tag_key
            )

            if keys:
                # Delete the keys
                deleted = await self._execute_with_fallback(
                    self._client.delete, *keys
                )

                if deleted:
                    total_deleted += deleted

                # Delete the tag key itself
                await self._execute_with_fallback(
                    self._client.delete, tag_key
                )

        if total_deleted > 0:
            self.logger.info(f"Deleted {total_deleted} keys for tags: {tags}")

        return total_deleted

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        full_key = self._build_key(key)

        result = await self._execute_with_fallback(
            self._client.exists, full_key
        )

        return bool(result)

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get TTL for key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, None if key doesn't exist or has no TTL
        """
        full_key = self._build_key(key)

        ttl = await self._execute_with_fallback(
            self._client.ttl, full_key
        )

        if ttl and ttl > 0:
            return ttl

        return None

    async def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """
        Extend TTL for existing key.

        Args:
            key: Cache key
            additional_seconds: Seconds to add to current TTL

        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key)

        current_ttl = await self.get_ttl(key)
        if current_ttl:
            new_ttl = current_ttl + additional_seconds
            result = await self._execute_with_fallback(
                self._client.expire, full_key, new_ttl
            )
            return bool(result)

        return False

    async def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            Current cache statistics
        """
        try:
            # Get Redis info
            info = await self._execute_with_fallback(self._client.info, "memory")

            total_operations = self._hit_count + self._miss_count

            self._stats = CacheStats(
                total_keys=await self._execute_with_fallback(self._client.dbsize) or 0,
                hit_rate=self._hit_count / total_operations if total_operations > 0 else 0,
                miss_rate=self._miss_count / total_operations if total_operations > 0 else 0,
                memory_usage_mb=(info.get("used_memory", 0) / 1024 / 1024) if info else 0,
                avg_response_time_ms=sum(self._operation_times) / len(self._operation_times) if self._operation_times else 0,
                operations_per_second=len(self._operation_times) / 60 if self._operation_times else 0,  # rough estimate
            )

        except Exception as e:
            self.logger.warning(f"Failed to get cache stats: {e}")

        return self._stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Get health status of Redis cache.

        Returns:
            Health status dictionary
        """
        status = {
            "status": "unknown",
            "available": self._is_available,
            "circuit_breaker_open": not self._is_available,
            "failure_count": self._failure_count,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
        }

        try:
            # Test Redis connection
            if self._client:
                latency_start = datetime.now()
                await self._client.ping()
                latency = (datetime.now() - latency_start).total_seconds() * 1000

                status.update({
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "connection_pool_size": self._pool.connection_kwargs if self._pool else None,
                })
            else:
                status["status"] = "disconnected"

        except Exception as e:
            status.update({
                "status": "unhealthy",
                "error": str(e),
            })

        return status

    async def flush_all(self) -> bool:
        """
        Flush all cache entries (use with caution).

        Returns:
            True if successful, False otherwise
        """
        result = await self._execute_with_fallback(self._client.flushdb)

        if result:
            self.logger.warning("All cache entries flushed")
            self._hit_count = 0
            self._miss_count = 0
            self._operation_times.clear()
            return True

        return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
