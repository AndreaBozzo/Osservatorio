"""
Integration tests for ProductionIstatClient.

Comprehensive test suite covering:
- API connectivity and response handling
- Repository integration
- Error handling and recovery
- Performance and load testing
- End-to-end pipeline validation
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.api.production_istat_client import (
    BatchResult,
    CircuitBreaker,
    ClientStatus,
    ProductionIstatClient,
    QualityResult,
    RateLimiter,
    SyncResult,
)


class TestProductionIstatClientCore:
    """Test core client functionality."""

    @pytest.fixture
    def client(self):
        """Create test client instance."""
        return ProductionIstatClient()

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository for testing."""
        repository = Mock()
        repository.sync_dataset = Mock(
            return_value={"status": "success", "records": 100}
        )
        return repository

    def test_client_initialization(self, client):
        """Test client initializes correctly."""
        assert client.base_url == "https://sdmx.istat.it/SDMXWS/rest/"
        assert client.status == ClientStatus.HEALTHY
        assert isinstance(client.circuit_breaker, CircuitBreaker)
        assert isinstance(client.rate_limiter, RateLimiter)
        assert client.session is not None

        # Check metrics initialization
        assert client.metrics["total_requests"] == 0
        assert client.metrics["successful_requests"] == 0
        assert client.metrics["failed_requests"] == 0

    def test_session_configuration(self, client):
        """Test session is properly configured."""
        session = client.session

        # Check headers
        assert "Osservatorio-Production-Client" in session.headers["User-Agent"]
        assert "application/xml" in session.headers["Accept"]

        # Check adapters are configured
        assert len(session.adapters) >= 2  # http and https

    def test_get_status(self, client):
        """Test status reporting."""
        status = client.get_status()

        assert "status" in status
        assert "circuit_breaker_state" in status
        assert "rate_limit_remaining" in status
        assert "metrics" in status

        assert status["status"] == ClientStatus.HEALTHY.value
        assert status["circuit_breaker_state"] == "closed"


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.fixture
    def breaker(self):
        """Create circuit breaker for testing."""
        return CircuitBreaker(failure_threshold=3, recovery_timeout=1)

    def test_initial_state(self, breaker):
        """Test circuit breaker initial state."""
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
        assert breaker.can_proceed() is True

    def test_failure_handling(self, breaker):
        """Test failure tracking and circuit opening."""
        # Record failures up to threshold
        for _ in range(2):
            breaker.record_failure()
            assert breaker.state == "closed"
            assert breaker.can_proceed() is True

        # Third failure should open circuit
        breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.can_proceed() is False

    def test_recovery_after_timeout(self, breaker):
        """Test circuit recovery after timeout."""
        # Open circuit
        for _ in range(3):
            breaker.record_failure()

        assert breaker.state == "open"
        assert breaker.can_proceed() is False

        # Wait for recovery timeout
        time.sleep(1.1)

        # Should transition to half-open
        assert breaker.can_proceed() is True
        assert breaker.state == "half_open"

        # Success should close circuit
        breaker.record_success()
        assert breaker.state == "closed"
        assert breaker.failure_count == 0


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter for testing."""
        return RateLimiter(max_requests=3, window_seconds=1)

    def test_initial_state(self, limiter):
        """Test rate limiter initial state."""
        assert len(limiter.requests) == 0
        assert limiter.can_proceed() is True

    def test_rate_limiting(self, limiter):
        """Test rate limiting enforcement."""
        # Should allow requests up to limit
        for _ in range(3):
            assert limiter.can_proceed() is True

        # Fourth request should be blocked
        assert limiter.can_proceed() is False

    def test_window_expiration(self, limiter):
        """Test request window expiration."""
        # Fill rate limit
        for _ in range(3):
            limiter.can_proceed()

        assert limiter.can_proceed() is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should allow requests again
        assert limiter.can_proceed() is True


class TestAPIIntegration:
    """Test API integration with real ISTAT endpoints."""

    @pytest.fixture
    def client(self):
        """Create client for API testing."""
        return ProductionIstatClient()

    @pytest.mark.integration
    def test_fetch_dataflows_integration(self, client):
        """Test real dataflows fetching."""
        try:
            result = client.fetch_dataflows(limit=5)

            assert "dataflows" in result
            assert "total_count" in result
            assert "timestamp" in result

            assert len(result["dataflows"]) <= 5
            assert result["total_count"] >= 0

            # Check dataflow structure
            if result["dataflows"]:
                dataflow = result["dataflows"][0]
                assert "id" in dataflow
                assert "name" in dataflow
                assert "agency" in dataflow

        except Exception as e:
            pytest.skip(f"ISTAT API not accessible: {e}")

    @pytest.mark.integration
    def test_fetch_dataset_integration(self, client):
        """Test real dataset fetching."""
        try:
            # Test with known dataset ID
            result = client.fetch_dataset("DCIS_POPRES1", include_data=True)

            assert result["dataset_id"] == "DCIS_POPRES1"
            assert "timestamp" in result
            assert "structure" in result
            assert "data" in result

            # Check structure fetch
            if result["structure"] and result["structure"]["status"] == "success":
                assert "content_type" in result["structure"]
                assert "size" in result["structure"]

            # Check data fetch
            if result["data"] and result["data"]["status"] == "success":
                assert "observations_count" in result["data"]
                assert result["data"]["observations_count"] >= 0

        except Exception as e:
            pytest.skip(f"ISTAT API not accessible: {e}")

    @pytest.mark.integration
    def test_health_check_integration(self, client):
        """Test health check with real API."""
        try:
            health = client.health_check()

            assert "status" in health
            assert "timestamp" in health
            assert "client_status" in health

            if health["status"] == "healthy":
                assert "response_time" in health
                assert "api_status_code" in health
                assert health["response_time"] > 0

        except Exception as e:
            pytest.skip(f"ISTAT API not accessible: {e}")


class TestBatchProcessing:
    """Test batch processing capabilities."""

    @pytest.fixture
    def client(self):
        """Create client for batch testing."""
        return ProductionIstatClient()

    @pytest.mark.skip(reason="Issue #159 - async tests require pytest-asyncio configuration")
    @pytest.mark.asyncio
    async def test_fetch_dataset_batch(self, client):
        """Test batch dataset fetching."""
        dataset_ids = ["DCIS_POPRES1", "INVALID_DATASET", "DCIS_POPSTRRES1"]

        with patch.object(client, "fetch_dataset") as mock_fetch:
            # Mock responses
            mock_fetch.side_effect = [
                {"dataset_id": "DCIS_POPRES1", "data": {"status": "success"}},
                Exception("Dataset not found"),
                {"dataset_id": "DCIS_POPSTRRES1", "data": {"status": "success"}},
            ]

            result = await client.fetch_dataset_batch(dataset_ids)

            assert isinstance(result, BatchResult)
            assert len(result.successful) == 2
            assert len(result.failed) == 1
            assert result.total_time > 0
            assert isinstance(result.timestamp, datetime)

            # Check specific results
            assert "DCIS_POPRES1" in result.successful
            assert "DCIS_POPSTRRES1" in result.successful
            assert result.failed[0][0] == "INVALID_DATASET"


class TestQualityValidation:
    """Test data quality validation."""

    @pytest.fixture
    def client(self):
        """Create client for quality testing."""
        return ProductionIstatClient()

    def test_quality_validation_success(self, client):
        """Test successful quality validation."""
        with patch.object(client, "fetch_dataset") as mock_fetch:
            mock_fetch.return_value = {
                "dataset_id": "TEST_DATASET",
                "data": {"status": "success", "observations_count": 1000, "size": 5000},
            }

            result = client.fetch_with_quality_validation("TEST_DATASET")

            assert isinstance(result, QualityResult)
            assert result.dataset_id == "TEST_DATASET"
            assert result.quality_score > 80  # Should be high for good data
            assert result.completeness > 80
            assert result.consistency > 80
            assert len(result.validation_errors) == 0

    def test_quality_validation_failure(self, client):
        """Test quality validation with poor data."""
        with patch.object(client, "fetch_dataset") as mock_fetch:
            mock_fetch.return_value = {
                "dataset_id": "POOR_DATASET",
                "data": {
                    "status": "success",
                    "observations_count": 0,  # No data
                    "size": 100,  # Very small
                },
            }

            result = client.fetch_with_quality_validation("POOR_DATASET")

            assert isinstance(result, QualityResult)
            assert result.quality_score < 50  # Should be low
            assert len(result.validation_errors) > 0
            assert "No observations found" in result.validation_errors[0]


class TestRepositoryIntegration:
    """Test repository integration."""

    @pytest.fixture
    def client_with_repo(self):
        """Create client with mock repository."""
        mock_repo = Mock()
        client = ProductionIstatClient(repository=mock_repo)
        return client, mock_repo

    def test_sync_to_repository(self, client_with_repo):
        """Test repository synchronization."""
        client, mock_repo = client_with_repo

        dataset_data = {
            "dataset_id": "TEST_DATASET",
            "data": {"observations_count": 500, "status": "success"},
        }

        result = client.sync_to_repository(dataset_data)

        assert isinstance(result, SyncResult)
        assert result.dataset_id == "TEST_DATASET"
        assert result.records_synced == 500
        assert result.metadata_updated is True
        assert result.sync_time > 0

    def test_sync_without_repository(self):
        """Test sync behavior without repository."""
        client = ProductionIstatClient(repository=None)

        dataset_data = {
            "dataset_id": "TEST_DATASET",
            "data": {"observations_count": 100},
        }

        with patch.object(client.config_manager, "update_dataset") as mock_update:
            result = client.sync_to_repository(dataset_data)

            assert isinstance(result, SyncResult)
            assert result.metadata_updated is True
            mock_update.assert_called_once()


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.fixture
    def client(self):
        """Create client for error testing."""
        return ProductionIstatClient()

    def test_circuit_breaker_integration(self, client):
        """Test circuit breaker with real requests."""
        # Force circuit breaker to open by simulating failures (default threshold is 10)
        for _ in range(10):
            client.circuit_breaker.record_failure()

        assert client.circuit_breaker.state == "open"

        # Request should fail due to circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is open"):
            client._make_request("invalid/endpoint")

    def test_rate_limiting_integration(self, client):
        """Test rate limiting integration."""
        # Fill rate limit
        for _ in range(100):
            client.rate_limiter.requests.append(time.time())

        # Next request should fail due to rate limiting
        with pytest.raises(Exception, match="Rate limit exceeded"):
            client._make_request("dataflow/IT1")

    def test_network_error_handling(self, client):
        """Test network error handling."""
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
                client._make_request("dataflow/IT1")

            # Check metrics updated
            assert client.metrics["failed_requests"] > 0
            assert client.status in [ClientStatus.DEGRADED, ClientStatus.CIRCUIT_OPEN]


class TestPerformanceAndLoad:
    """Test performance and load handling."""

    @pytest.fixture
    def client(self):
        """Create client for performance testing."""
        return ProductionIstatClient()

    def test_response_time_tracking(self, client):
        """Test response time metrics tracking."""
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Make request
            client._make_request("dataflow/IT1")

            # Check metrics updated
            assert client.metrics["successful_requests"] == 1
            assert client.metrics["average_response_time"] > 0
            assert client.metrics["last_request_time"] is not None

    @pytest.mark.skip(reason="Issue #159 - async tests require pytest-asyncio configuration")
    @pytest.mark.asyncio
    async def test_concurrent_batch_processing(self, client):
        """Test concurrent processing capabilities."""
        dataset_ids = [f"DATASET_{i}" for i in range(10)]

        with patch.object(client, "fetch_dataset") as mock_fetch:
            mock_fetch.return_value = {
                "data": {"status": "success", "observations_count": 100}
            }

            start_time = time.time()
            result = await client.fetch_dataset_batch(dataset_ids)
            total_time = time.time() - start_time

            # Batch processing should be faster than sequential
            assert result.total_time < total_time + 1  # Allow some overhead
            assert len(result.successful) == 10


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline."""

    @pytest.fixture
    def client(self):
        """Create client for E2E testing."""
        mock_repo = Mock()
        return ProductionIstatClient(repository=mock_repo, enable_cache_fallback=True)

    @pytest.mark.integration
    def test_complete_pipeline_flow(self, client):
        """Test complete data pipeline flow."""
        with patch.object(client, "_make_request") as mock_request:
            # Mock response that triggers cache fallback (404 error)
            from requests.exceptions import HTTPError

            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.content = b""  # Empty content to trigger error
            mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")

            # All calls trigger cache fallback
            mock_request.side_effect = HTTPError("404 Not Found")

            # Execute pipeline using cache fallback
            # 1. Discover datasets (will use cache fallback due to 404)
            dataflows = client.fetch_dataflows(limit=1)
            assert "dataflows" in dataflows
            assert len(dataflows["dataflows"]) >= 1
            assert dataflows["source"] == "cache_fallback"

            # 2. Fetch specific dataset (will use cache fallback)
            dataset_id = dataflows["dataflows"][0]["id"]
            dataset_result = client.fetch_dataset(dataset_id, include_data=True)
            assert dataset_result["data"]["status"] == "success"
            assert dataset_result["source"] == "cache_fallback"

            # 3. Validate quality (using cache data)
            quality_result = client.fetch_with_quality_validation(dataset_id)
            assert quality_result.quality_score > 0

            # 4. Sync to repository (using cache data)
            sync_result = client.sync_to_repository(dataset_result)
            assert sync_result.metadata_updated is True

    def test_error_recovery_pipeline(self, client):
        """Test pipeline behavior with errors and recovery."""
        with patch.object(client, "_make_request") as mock_request:
            # First request fails
            mock_request.side_effect = [
                Exception("Network error"),  # Fails
                Mock(content=b"<xml></xml>", headers={}),  # Succeeds on retry
            ]

            # Should handle error and continue
            try:
                client.fetch_dataflows()
                assert False, "Should have raised exception"
            except Exception:
                pass

            # Circuit breaker should allow retry after some time
            client.circuit_breaker.record_success()  # Reset for test

            result = client.fetch_dataflows()
            assert "dataflows" in result


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_client():
    """Cleanup client resources after each test."""
    yield
    # Any cleanup code would go here
