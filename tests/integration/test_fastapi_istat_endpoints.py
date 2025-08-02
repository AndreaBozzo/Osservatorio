"""
Integration tests for FastAPI ISTAT endpoints.

Tests the 4 production ISTAT endpoints:
- GET /api/istat/status
- GET /api/istat/dataflows
- GET /api/istat/dataset/{dataset_id}
- POST /api/istat/sync/{dataset_id}
"""
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.api.fastapi_app import app
from src.api.production_istat_client import ProductionIstatClient
from src.database.sqlite.repository import reset_unified_repository


@pytest.fixture(autouse=True)
def cleanup_resources():
    """Cleanup database resources before and after each test to prevent ResourceWarnings."""
    # Reset before test
    reset_unified_repository()
    app.dependency_overrides.clear()

    yield

    # Cleanup after test
    try:
        from src.database.sqlite.repository import get_unified_repository

        repository = get_unified_repository()
        repository.close()
    except Exception:
        pass  # Ignore cleanup errors

    reset_unified_repository()
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for authentication."""
    return "test-jwt-token"


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Authentication headers."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


class TestIstatStatusEndpoint:
    """Test /api/istat/status endpoint."""

    @pytest.mark.integration
    def test_status_endpoint_success(self, client, auth_headers):
        """Test status endpoint returns client status."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.get_status.return_value = {
            "status": "healthy",
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "circuit_breaker_state": "closed",
            "rate_limit_remaining": 85,
        }
        mock_client.health_check.return_value = {"status": "healthy"}

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.get("/api/istat/status", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["client_status"]["status"] == "healthy"
            assert data["client_status"]["total_requests"] == 100
            assert data["client_status"]["successful_requests"] == 95
            assert "circuit_breaker_state" in data["client_status"]
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @pytest.mark.integration
    def test_status_endpoint_error(self, client, auth_headers):
        """Test status endpoint handles errors."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client that raises exception in methods, not initialization
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.get_status.side_effect = Exception("Client initialization failed")
        mock_client.health_check.side_effect = Exception("Client initialization failed")

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.get("/api/istat/status", headers=auth_headers)

            assert response.status_code == 500
            data = response.json()
            assert "Internal server error" in data["detail"]
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


class TestIstatDataflowsEndpoint:
    """Test /api/istat/dataflows endpoint."""

    @pytest.mark.integration
    def test_dataflows_endpoint_success(self, client, auth_headers):
        """Test dataflows endpoint returns dataset list."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.fetch_dataflows.return_value = {
            "dataflows": [
                {"id": "101_1015", "name": "Test Dataset 1", "agency": "IT1"},
                {"id": "101_1016", "name": "Test Dataset 2", "agency": "IT1"},
            ],
            "total_count": 2,
            "source": "live_api",
        }

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.get("/api/istat/dataflows?limit=5", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data["dataflows"]) == 2
            assert data["total_count"] == 2
            assert data["dataflows"][0]["id"] == "101_1015"
            mock_client.fetch_dataflows.assert_called_once_with(limit=5)
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @pytest.mark.integration
    def test_dataflows_endpoint_unauthorized(self, client):
        """Test dataflows endpoint requires authentication."""
        response = client.get("/api/istat/dataflows")

        assert response.status_code == 401

    @pytest.mark.integration
    def test_dataflows_endpoint_with_cache_fallback(self, client, auth_headers):
        """Test dataflows endpoint with cache fallback."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.fetch_dataflows.return_value = {
            "dataflows": [
                {"id": "POPULATION_2023", "name": "Cached Dataset", "agency": "IT1"}
            ],
            "total_count": 1,
            "source": "cache_fallback",
            "note": "Cached data - ISTAT API unavailable",
        }

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.get("/api/istat/dataflows", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "cache_fallback"
            assert "note" in data
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


class TestIstatDatasetEndpoint:
    """Test /api/istat/dataset/{dataset_id} endpoint."""

    @pytest.mark.integration
    def test_dataset_endpoint_success(self, client, auth_headers):
        """Test dataset endpoint returns dataset data."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.fetch_dataset.return_value = {
            "dataset_id": "101_1015",
            "timestamp": "2025-07-29T14:00:00",
            "source": "live_api",
            "structure": {"status": "success", "content_type": "application/xml"},
            "data": {
                "status": "success",
                "content_type": "application/xml",
                "observations_count": 1500,
                "size": 450000,
            },
        }

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.get(
                "/api/istat/dataset/101_1015?include_data=true", headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["dataset_id"] == "101_1015"
            assert data["data"]["status"] == "success"
            assert data["data"]["observations_count"] == 1500
            mock_client.fetch_dataset.assert_called_once_with(
                "101_1015", include_data=True
            )
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @pytest.mark.integration
    def test_dataset_endpoint_not_found(self, client, auth_headers):
        """Test dataset endpoint handles non-existent datasets."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.fetch_dataset.return_value = {
            "dataset_id": "NONEXISTENT",
            "timestamp": "2025-07-29T14:00:00",
            "source": "cache_fallback",
            "structure": {
                "status": "error",
                "error": "Dataset NONEXISTENT not found in cached data",
            },
            "data": {
                "status": "error",
                "error": "Dataset NONEXISTENT not available",
            },
        }

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.get(
                "/api/istat/dataset/NONEXISTENT", headers=auth_headers
            )

            assert (
                response.status_code == 200
            )  # Client handles gracefully with cache fallback
            data = response.json()
            assert data["source"] == "cache_fallback"
            assert data["data"]["status"] == "error"
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @pytest.mark.integration
    def test_dataset_endpoint_unauthorized(self, client):
        """Test dataset endpoint requires authentication."""
        response = client.get("/api/istat/dataset/101_1015")

        assert response.status_code == 401


class TestIstatSyncEndpoint:
    """Test POST /api/istat/sync/{dataset_id} endpoint."""

    @pytest.mark.integration
    def test_sync_endpoint_success(self, client, auth_headers):
        """Test sync endpoint successfully syncs dataset."""
        from src.api.dependencies import (
            check_rate_limit,
            get_istat_client,
            log_api_request,
            require_write,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)

        # Mock fetch_dataset first
        mock_client.fetch_dataset.return_value = {
            "dataset_id": "101_1015",
            "data": {"status": "success", "observations_count": 1500},
        }

        # Mock sync_to_repository result
        from datetime import datetime

        from src.api.production_istat_client import SyncResult

        mock_sync_result = SyncResult(
            dataset_id="101_1015",
            records_synced=1500,
            sync_time=2.5,
            metadata_updated=True,
            timestamp=datetime.now(),
        )
        mock_client.sync_to_repository.return_value = mock_sync_result

        # Override FastAPI dependencies
        app.dependency_overrides[require_write] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            sync_request = {"include_data": True, "force_refresh": False}

            response = client.post(
                "/api/istat/sync/101_1015", json=sync_request, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sync_result"]["dataset_id"] == "101_1015"
            assert data["sync_result"]["records_synced"] == 1500
            assert data["sync_result"]["metadata_updated"] is True
            assert data["sync_result"]["sync_time"] == 2.5
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    @pytest.mark.integration
    def test_sync_endpoint_unauthorized(self, client):
        """Test sync endpoint requires authentication."""
        sync_request = {"include_data": True}
        response = client.post("/api/istat/sync/101_1015", json=sync_request)

        assert response.status_code == 401

    @pytest.mark.integration
    def test_sync_endpoint_error(self, client, auth_headers):
        """Test sync endpoint handles sync errors."""
        from src.api.dependencies import (
            check_rate_limit,
            get_istat_client,
            log_api_request,
            require_write,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client that raises exception
        mock_client = Mock(spec=ProductionIstatClient)
        mock_client.fetch_dataset.side_effect = Exception("Dataset fetch failed")

        # Override FastAPI dependencies
        app.dependency_overrides[require_write] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            sync_request = {"include_data": True}

            response = client.post(
                "/api/istat/sync/101_1015", json=sync_request, headers=auth_headers
            )

            assert response.status_code == 503
            data = response.json()
            assert "Sync error" in data["detail"]
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()


class TestIstatEndpointsIntegration:
    """Integration tests across multiple ISTAT endpoints."""

    @pytest.mark.integration
    def test_complete_istat_workflow(self, client, auth_headers):
        """Test complete workflow: status -> dataflows -> dataset -> sync."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_istat_client,
            log_api_request,
            require_write,
        )
        from src.auth.models import TokenClaims

        # Create mock user
        mock_user = TokenClaims(
            sub="test_user",
            api_key_name="test_key",
            scope="read write",
            rate_limit=100,
            exp=9999999999,
        )

        # Create mock client
        mock_client = Mock(spec=ProductionIstatClient)

        # Mock all endpoints
        mock_client.get_status.return_value = {"status": "healthy"}
        mock_client.health_check.return_value = {"status": "healthy"}
        mock_client.fetch_dataflows.return_value = {
            "dataflows": [{"id": "101_1015", "name": "Test Dataset"}],
            "total_count": 1,
        }
        mock_client.fetch_dataset.return_value = {
            "dataset_id": "101_1015",
            "data": {"status": "success", "observations_count": 1000},
        }

        from datetime import datetime

        from src.api.production_istat_client import SyncResult

        mock_client.sync_to_repository.return_value = SyncResult(
            dataset_id="101_1015",
            records_synced=1000,
            sync_time=1.5,
            metadata_updated=True,
            timestamp=datetime.now(),
        )

        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_istat_client] = lambda: mock_client
        app.dependency_overrides[require_write] = lambda: mock_user
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            # 1. Check status
            status_response = client.get("/api/istat/status", headers=auth_headers)
            assert status_response.status_code == 200

            # 2. Get dataflows
            dataflows_response = client.get(
                "/api/istat/dataflows", headers=auth_headers
            )
            assert dataflows_response.status_code == 200
            dataset_id = dataflows_response.json()["dataflows"][0]["id"]

            # 3. Fetch dataset
            dataset_response = client.get(
                f"/api/istat/dataset/{dataset_id}", headers=auth_headers
            )
            assert dataset_response.status_code == 200

            # 4. Sync dataset
            sync_response = client.post(
                f"/api/istat/sync/{dataset_id}",
                json={"include_data": True},
                headers=auth_headers,
            )
            assert sync_response.status_code == 200
            assert sync_response.json()["sync_result"]["records_synced"] == 1000
        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
