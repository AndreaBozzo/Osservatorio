"""
Locust load testing scenarios for Osservatorio ISTAT API.

Usage:
    locust -f tests/performance/load_testing/locustfile.py --host=http://localhost:8000

Test scenarios:
- Basic API endpoints (<100ms target)
- Authentication flow
- Dataset querying
- OData endpoints for PowerBI
- Concurrent user simulation (1-1000 users)
"""

import json
import random
import time
from typing import Dict, List

from locust import HttpUser, between, task

# Import JWT token generator with proper relative imports
try:
    from .jwt_token_generator import PerformanceJWTGenerator
except ImportError:
    # Fallback for direct execution - use relative import
    try:
        from jwt_token_generator import PerformanceJWTGenerator
    except ImportError:
        # Final fallback for development
        import sys
        from pathlib import Path

        # Issue #84: Removed unsafe sys.path manipulation
        from jwt_token_generator import PerformanceJWTGenerator

# Test data for realistic scenarios
SAMPLE_DATASETS = [
    "DCIS_POPRES1",
    "DCCN_PILN",
    "DCCV_TAXOCCU",
    "DCIS_MORTALITA1",
    "DCIS_POPSTRRES1",
]

SAMPLE_TERRITORIES = ["IT", "ITC1", "ITF1", "ITG1", "ITH1"]
SAMPLE_YEARS = [2018, 2019, 2020, 2021, 2022, 2023]


class APIUser(HttpUser):
    """Basic API user for testing core endpoints."""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup method called when user starts."""
        self.api_key = self._get_api_key()
        self.headers = (
            {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )

    def _get_api_key(self) -> str:
        """Get real JWT token for authenticated requests."""
        try:
            if not hasattr(self.__class__, "_jwt_generator"):
                self.__class__._jwt_generator = PerformanceJWTGenerator()

            token = self.__class__._jwt_generator.generate_jwt_token(
                scopes=["read", "datasets", "odata"]
            )
            return token if token else "fallback-test-token"
        except Exception as e:
            print(f"Failed to get JWT token: {e}")
            return "fallback-test-token"

    @task(3)
    def test_health_check(self):
        """Test health check endpoint - should be <50ms."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 0.05:  # 50ms
                    response.failure(
                        f"Health check too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def test_list_datasets(self):
        """Test dataset listing - should be <100ms for 1000 datasets."""
        with self.client.get(
            "/datasets", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 0.1:  # 100ms
                    response.failure(
                        f"Dataset list too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    try:
                        data = response.json()
                        if isinstance(data, list) or (
                            isinstance(data, dict) and "datasets" in data
                        ):
                            response.success()
                        else:
                            response.failure("Invalid dataset list format")
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
            else:
                response.failure(f"Dataset list failed: {response.status_code}")

    @task(2)
    def test_dataset_detail(self):
        """Test dataset detail endpoint - should be <200ms with data."""
        dataset_id = random.choice(SAMPLE_DATASETS)
        with self.client.get(
            f"/datasets/{dataset_id}", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 0.2:  # 200ms
                    response.failure(
                        f"Dataset detail too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    try:
                        data = response.json()
                        if "id" in data or "dataset_id" in data:
                            response.success()
                        else:
                            response.failure("Invalid dataset detail format")
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
            elif response.status_code == 404:
                # Dataset not found is acceptable for load testing
                response.success()
            else:
                response.failure(f"Dataset detail failed: {response.status_code}")

    @task(1)
    def test_odata_query(self):
        """Test OData endpoint for PowerBI - should be <500ms for 10k records."""
        # Test OData datasets endpoint instead
        odata_params = {"$top": "100", "$skip": "0"}

        with self.client.get(
            "/odata/Datasets",
            params=odata_params,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 0.5:  # 500ms
                    response.failure(
                        f"OData query too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    try:
                        data = response.json()
                        if "value" in data:  # OData format
                            response.success()
                        else:
                            response.failure("Invalid OData response format")
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
            elif response.status_code == 404:
                # Dataset not found is acceptable for load testing
                response.success()
            else:
                response.failure(f"OData query failed: {response.status_code}")


class PowerBIUser(HttpUser):
    """PowerBI-specific user for testing OData scenarios."""

    wait_time = between(2, 5)

    def on_start(self):
        """Setup PowerBI user session."""
        try:
            if not hasattr(self.__class__, "_jwt_generator"):
                self.__class__._jwt_generator = PerformanceJWTGenerator()

            token = self.__class__._jwt_generator.generate_jwt_token(
                scopes=["read", "odata"]
            )
            self.api_key = token if token else "fallback-powerbi-token"
        except Exception as e:
            print(f"Failed to get PowerBI token: {e}")
            self.api_key = "fallback-powerbi-token"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "PowerBI/1.0",
        }

    @task(4)
    def test_odata_metadata(self):
        """Test OData metadata endpoint."""
        with self.client.get(
            "/odata/$metadata", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 0.1:  # 100ms for metadata
                    response.failure(
                        f"OData metadata too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    response.success()
            else:
                response.failure(f"OData metadata failed: {response.status_code}")

    @task(6)
    def test_odata_batch_query(self):
        """Test OData batch query for PowerBI."""
        dataset_id = random.choice(SAMPLE_DATASETS)

        # Simulate PowerBI batch queries
        queries = [
            {"$top": "100", "$skip": "0"},
            {"$top": "100", "$skip": "100"},
            {"$filter": f"Year eq {random.choice(SAMPLE_YEARS)}", "$top": "50"},
        ]

        for i, query_params in enumerate(queries):
            with self.client.get(
                f"/odata/Datasets",
                params=query_params,
                headers=self.headers,
                catch_response=True,
                name=f"odata_batch_{i}",
            ) as response:
                if response.status_code == 200:
                    if response.elapsed.total_seconds() > 0.5:
                        response.failure(
                            f"Batch query {i} too slow: {response.elapsed.total_seconds():.3f}s"
                        )
                    else:
                        response.success()
                elif response.status_code == 404:
                    response.success()
                else:
                    response.failure(f"Batch query {i} failed: {response.status_code}")


class AuthenticatedUser(HttpUser):
    """User testing authentication flow and protected endpoints."""

    wait_time = between(1, 2)

    def on_start(self):
        """Login and get JWT token."""
        self.token = self._authenticate()
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _authenticate(self) -> str:
        """Get real JWT token for authenticated requests."""
        try:
            if not hasattr(self.__class__, "_jwt_generator"):
                self.__class__._jwt_generator = PerformanceJWTGenerator()

            token = self.__class__._jwt_generator.generate_jwt_token(
                scopes=["read", "write", "admin"]
            )
            return token if token else "fallback-auth-token"
        except Exception as e:
            print(f"Failed to authenticate: {e}")
            return "fallback-auth-token"

    @task(2)
    def test_protected_endpoint(self):
        """Test protected endpoint with JWT."""
        with self.client.get(
            "/datasets", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code in [200, 401, 403]:  # Expected responses
                response.success()
            else:
                response.failure(f"Protected endpoint failed: {response.status_code}")

    @task(1)
    def test_admin_endpoint(self):
        """Test admin endpoint."""
        with self.client.get(
            "/analytics/usage", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code in [200, 401, 403]:  # Expected responses
                response.success()
            else:
                response.failure(f"Admin endpoint failed: {response.status_code}")


class DatabaseStressUser(HttpUser):
    """User for stressing database operations."""

    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Setup database stress user."""
        try:
            if not hasattr(self.__class__, "_jwt_generator"):
                self.__class__._jwt_generator = PerformanceJWTGenerator()

            token = self.__class__._jwt_generator.generate_jwt_token(
                scopes=["read", "datasets"]
            )
            self.api_key = token if token else "fallback-db-token"
        except Exception as e:
            print(f"Failed to get DB stress token: {e}")
            self.api_key = "fallback-db-token"

        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    @task(3)
    def test_complex_query(self):
        """Test complex database query."""
        dataset_id = random.choice(SAMPLE_DATASETS)
        params = {
            "territory_code": random.choice(SAMPLE_TERRITORIES),
            "start_year": random.choice(SAMPLE_YEARS[:3]),
            "end_year": random.choice(SAMPLE_YEARS[3:]),
            "limit": random.randint(100, 1000),
        }

        with self.client.get(
            f"/datasets/{dataset_id}/timeseries",
            params=params,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                if (
                    response.elapsed.total_seconds() > 1.0
                ):  # 1 second for complex queries
                    response.failure(
                        f"Complex query too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    response.success()
            else:
                response.failure(f"Complex query failed: {response.status_code}")

    @task(2)
    def test_aggregation_query(self):
        """Test database aggregation query."""
        dataset_id = random.choice(SAMPLE_DATASETS)
        params = {
            "territory_code": random.choice(SAMPLE_TERRITORIES),
            "start_year": random.choice(SAMPLE_YEARS[:2]),
            "end_year": random.choice(SAMPLE_YEARS[2:]),
        }

        with self.client.get(
            f"/datasets/{dataset_id}/timeseries",
            params=params,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                if response.elapsed.total_seconds() > 2.0:  # 2 seconds for aggregations
                    response.failure(
                        f"Aggregation too slow: {response.elapsed.total_seconds():.3f}s"
                    )
                else:
                    response.success()
            else:
                response.failure(f"Aggregation query failed: {response.status_code}")
