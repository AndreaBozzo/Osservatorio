"""
Unit tests for RedisCacheManager

Tests the distributed Redis caching functionality.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.config.environment_config import RedisConfig
from src.services.distributed.redis_cache_manager import RedisCacheManager


class TestRedisCacheManager:
    """Test RedisCacheManager functionality"""

    @pytest.fixture
    def redis_config(self):
        """Create Redis configuration for testing"""
        return RedisConfig(
            host="localhost",
            port=6379,
            db=0,
            password=None,
            ssl=False,
            socket_timeout=5,
            socket_connect_timeout=5,
            max_connections=10,
            retry_on_timeout=True
        )

    @pytest.fixture
    def cache_manager(self, redis_config):
        """Create RedisCacheManager instance for testing"""
        return RedisCacheManager(
            config=redis_config,
            key_prefix="test:cache:"
        )

    def test_cache_manager_initialization(self, redis_config):
        """Test RedisCacheManager initialization"""
        manager = RedisCacheManager(
            config=redis_config,
            key_prefix="test:cache:"
        )

        assert manager.config == redis_config
        assert manager.key_prefix == "test:cache:"
        assert manager._client is None
        assert manager._pool is None

    def test_key_building(self, cache_manager):
        """Test cache key building with prefix"""
        key = cache_manager._build_key("test_key")
        assert key == "test:cache:test_key"

    def test_circuit_breaker_functionality(self, cache_manager):
        """Test circuit breaker state management"""
        # Initially should be available
        assert cache_manager._is_available is True
        assert cache_manager._failure_count == 0

        # Mark failures
        for _ in range(cache_manager._circuit_breaker_threshold):
            cache_manager._mark_failure()

        # Should open circuit breaker
        assert cache_manager._is_available is False

    @pytest.mark.asyncio
    async def test_cache_set_get_without_redis(self, cache_manager):
        """Test cache operations without Redis connection (fallback behavior)"""
        # Without Redis connection, operations should return defaults
        result = await cache_manager.get("test_key", "default_value")
        assert result == "default_value"

        success = await cache_manager.set("test_key", "test_value")
        assert success is False

    @pytest.mark.asyncio
    async def test_cache_operations_with_mock_redis(self, cache_manager):
        """Test cache operations with mocked Redis"""
        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = json.dumps("cached_value").encode()
        mock_client.set.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = 1
        mock_client.ttl.return_value = 300
        mock_client.dbsize.return_value = 10

        # Mock connection pool
        mock_pool = MagicMock()

        cache_manager._client = mock_client
        cache_manager._pool = mock_pool
        cache_manager._is_available = True

        # Test get operation
        result = await cache_manager.get("test_key")
        assert result == "cached_value"
        mock_client.get.assert_called_once()

        # Test set operation
        success = await cache_manager.set("test_key", "test_value", ttl=300)
        assert success is True
        mock_client.set.assert_called()

        # Test delete operation
        deleted = await cache_manager.delete("test_key")
        assert deleted is True
        mock_client.delete.assert_called()

        # Test exists operation
        exists = await cache_manager.exists("test_key")
        assert exists is True
        mock_client.exists.assert_called()

        # Test TTL operation
        ttl = await cache_manager.get_ttl("test_key")
        assert ttl == 300
        mock_client.ttl.assert_called()

    @pytest.mark.asyncio
    async def test_cache_serialization(self, cache_manager):
        """Test different data type serialization"""
        mock_client = AsyncMock()
        cache_manager._client = mock_client
        cache_manager._is_available = True

        # Test JSON serializable data
        test_data = {"key": "value", "number": 123, "boolean": True}
        mock_client.set.return_value = True

        success = await cache_manager.set("json_test", test_data)
        assert success is True

        # Verify the call was made with JSON-serialized data
        mock_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_cache_with_tags(self, cache_manager):
        """Test cache operations with tags for invalidation"""
        mock_client = AsyncMock()
        mock_client.set.return_value = True
        mock_client.sadd.return_value = 1
        mock_client.expire.return_value = True

        cache_manager._client = mock_client
        cache_manager._is_available = True

        # Set value with tags
        success = await cache_manager.set(
            "tagged_key",
            "tagged_value",
            ttl=300,
            tags=["tag1", "tag2"]
        )
        assert success is True

        # Should have called set for the value and sadd for tags
        mock_client.set.assert_called()
        assert mock_client.sadd.call_count == 2  # One for each tag

    @pytest.mark.asyncio
    async def test_delete_by_pattern(self, cache_manager):
        """Test deleting keys by pattern"""
        mock_client = AsyncMock()
        mock_client.keys.return_value = [b"test:cache:key1", b"test:cache:key2"]
        mock_client.delete.return_value = 2

        cache_manager._client = mock_client
        cache_manager._is_available = True

        deleted_count = await cache_manager.delete_by_pattern("key*")
        assert deleted_count == 2

        mock_client.keys.assert_called_once()
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_tags(self, cache_manager):
        """Test deleting keys by tags"""
        mock_client = AsyncMock()
        mock_client.smembers.return_value = {b"test:cache:key1", b"test:cache:key2"}
        mock_client.delete.side_effect = [2, 1]  # First call deletes 2 keys, second deletes tag key

        cache_manager._client = mock_client
        cache_manager._is_available = True

        deleted_count = await cache_manager.delete_by_tags(["tag1"])
        assert deleted_count == 2

        mock_client.smembers.assert_called_once()
        assert mock_client.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_health_check(self, cache_manager):
        """Test cache health check"""
        # Without connection
        health = await cache_manager.health_check()
        assert health["status"] in ["unknown", "disconnected", "unhealthy"]

        # With mocked connection
        mock_client = AsyncMock()
        mock_client.ping.return_value = True

        cache_manager._client = mock_client

        health = await cache_manager.health_check()
        assert "status" in health
        assert "latency_ms" in health

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager):
        """Test cache statistics collection"""
        mock_client = AsyncMock()
        mock_client.info.return_value = {"used_memory": 1024 * 1024}  # 1MB
        mock_client.dbsize.return_value = 100

        cache_manager._client = mock_client
        cache_manager._is_available = True
        cache_manager._hit_count = 80
        cache_manager._miss_count = 20
        cache_manager._operation_times = [10.0, 20.0, 15.0]

        stats = await cache_manager.get_stats()

        assert stats.total_keys == 100
        assert stats.hit_rate == 0.8  # 80/100
        assert stats.miss_rate == 0.2  # 20/100
        assert stats.memory_usage_mb == 1.0
        assert stats.avg_response_time_ms > 0

    @pytest.mark.asyncio
    async def test_context_manager(self, redis_config):
        """Test async context manager"""
        with patch('src.services.distributed.redis_cache_manager.redis') as mock_redis:
            mock_pool = MagicMock()
            mock_client = AsyncMock()
            mock_client.ping.return_value = True

            mock_redis.ConnectionPool.return_value = mock_pool
            mock_redis.Redis.return_value = mock_client

            async with RedisCacheManager(redis_config) as cache_manager:
                assert cache_manager is not None
                assert cache_manager._client == mock_client

    @pytest.mark.asyncio
    async def test_extend_ttl(self, cache_manager):
        """Test TTL extension functionality"""
        mock_client = AsyncMock()
        mock_client.ttl.return_value = 300  # Current TTL
        mock_client.expire.return_value = True

        cache_manager._client = mock_client
        cache_manager._is_available = True

        success = await cache_manager.extend_ttl("test_key", 100)
        assert success is True

        # Should set new TTL to 400 (300 + 100)
        mock_client.expire.assert_called_with(
            cache_manager._build_key("test_key"),
            400
        )

    @pytest.mark.asyncio
    async def test_flush_all(self, cache_manager):
        """Test flushing all cache entries"""
        mock_client = AsyncMock()
        mock_client.flushdb.return_value = True

        cache_manager._client = mock_client
        cache_manager._is_available = True
        cache_manager._hit_count = 10
        cache_manager._miss_count = 5

        success = await cache_manager.flush_all()
        assert success is True

        # Stats should be reset
        assert cache_manager._hit_count == 0
        assert cache_manager._miss_count == 0
        assert len(cache_manager._operation_times) == 0
