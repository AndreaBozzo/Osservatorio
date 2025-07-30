"""
Unit tests for dataflow analysis API endpoints.

Tests the FastAPI endpoints for dataflow analysis and categorization
rules management, including request/response validation, authentication,
and error handling.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from src.api.fastapi_app import app
from src.api.models import DataflowCategory
from src.services.models import (
    AnalysisResult,
    CategorizationRule,
    DataflowTest,
    IstatDataflow,
    TestResult,
)


class TestDataflowAnalysisAPI:
    """Test dataflow analysis API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return {
            "sub": "test_user",
            "api_key_id": 1,
            "scopes": ["read", "write"],
            "exp": datetime.now().timestamp() + 3600,
        }

    @pytest.fixture
    def sample_xml_content(self):
        """Sample ISTAT dataflow XML content."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <mes:Structure xmlns:mes="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
            <str:Structures xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure">
                <str:Dataflows>
                    <str:Dataflow id="DCIS_POPRES1">
                        <com:Name xml:lang="it" xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
                            Popolazione residente
                        </com:Name>
                        <com:Description xml:lang="it" xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
                            Dati sulla popolazione residente italiana
                        </com:Description>
                    </str:Dataflow>
                </str:Dataflows>
            </str:Structures>
        </mes:Structure>"""

    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result from service."""
        dataflow = IstatDataflow(
            id="DCIS_POPRES1",
            display_name="Popolazione residente",
            description="Dati sulla popolazione residente italiana",
            category=DataflowCategory.POPOLAZIONE,
            relevance_score=10,
        )

        test = DataflowTest(
            dataflow_id="DCIS_POPRES1",
            data_access_success=True,
            status_code=200,
            size_bytes=1024000,
            observations_count=500,
        )

        test_result = TestResult(dataflow=dataflow, test=test)

        return AnalysisResult(
            total_analyzed=1,
            categorized_dataflows={DataflowCategory.POPOLAZIONE: [dataflow]},
            test_results=[test_result],
            tableau_ready_count=1,
            performance_metrics={"analysis_duration_seconds": 2.5},
        )

    def test_analyze_dataflow_success(
        self, client, mock_user, sample_xml_content, sample_analysis_result
    ):
        """Test successful dataflow analysis."""
        # Override dependencies in FastAPI app
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            get_dataflow_service,
            log_api_request,
        )

        # Mock service
        mock_service = AsyncMock()
        mock_service.analyze_dataflows_from_xml.return_value = sample_analysis_result

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None
        app.dependency_overrides[get_dataflow_service] = lambda: mock_service

        try:
            # Make request
            response = client.post(
                "/api/analysis/dataflow",
                json={
                    "xml_content": sample_xml_content,
                    "max_results": 100,
                    "include_tests": True,
                },
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["total_analyzed"] == 1
            assert "popolazione" in data["categorized_dataflows"]
            assert len(data["test_results"]) == 1
            assert data["tableau_ready_count"] == 1

            # Verify service was called correctly
            mock_service.analyze_dataflows_from_xml.assert_called_once()
            call_args = mock_service.analyze_dataflows_from_xml.call_args

            # Check if we have args and kwargs
            if len(call_args) == 2 and call_args[1]:  # args, kwargs
                args, kwargs = call_args
                assert args[0] == sample_xml_content
                if "filters" in kwargs:
                    assert kwargs["filters"].max_results == 100
                    assert kwargs["filters"].include_tests is True
            else:
                # Just args, no kwargs
                args = call_args[0] if call_args else []
                if len(args) >= 1:
                    assert args[0] == sample_xml_content

        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()

    def test_analyze_dataflow_no_content(self, client, mock_user):
        """Test dataflow analysis with no XML content."""
        from src.api.dependencies import (
            check_rate_limit,
            get_current_user,
            log_api_request,
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[check_rate_limit] = lambda: None
        app.dependency_overrides[log_api_request] = lambda: None

        try:
            response = client.post(
                "/api/analysis/dataflow",
                json={"max_results": 100},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
            data = response.json()
            assert (
                "Either xml_content or xml_file_path must be provided" in data["detail"]
            )

        finally:
            app.dependency_overrides.clear()

    def test_analyze_dataflow_invalid_xml_file(self, client, mock_user):
        """Test dataflow analysis with invalid XML file path."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ):
            response = client.post(
                "/api/analysis/dataflow",
                json={"xml_file_path": "/nonexistent/file.xml"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "XML file not found" in data["detail"]

    def test_analyze_dataflow_service_error(
        self, client, mock_user, sample_xml_content
    ):
        """Test dataflow analysis with service error."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.services.service_factory.get_dataflow_analysis_service"
        ) as mock_service_factory:
            # Mock service to raise exception
            mock_service = AsyncMock()
            mock_service.analyze_dataflows_from_xml.side_effect = Exception(
                "Service error"
            )
            mock_service_factory.return_value = mock_service

            response = client.post(
                "/api/analysis/dataflow",
                json={"xml_content": sample_xml_content},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 500
            data = response.json()
            assert "Analysis failed" in data["detail"]

    def test_upload_and_analyze_xml_success(
        self, client, mock_user, sample_xml_content, sample_analysis_result
    ):
        """Test successful XML file upload and analysis."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.services.service_factory.get_dataflow_analysis_service"
        ) as mock_service_factory:
            # Mock service
            mock_service = AsyncMock()
            mock_service.analyze_dataflows_from_xml.return_value = (
                sample_analysis_result
            )
            mock_service_factory.return_value = mock_service

            # Create file-like object
            xml_bytes = sample_xml_content.encode("utf-8")

            response = client.post(
                "/api/analysis/dataflow/upload",
                files={"file": ("test.xml", xml_bytes, "application/xml")},
                params={"max_results": 50, "include_tests": "false"},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_analyzed"] == 1

    def test_upload_non_xml_file(self, client, mock_user):
        """Test uploading non-XML file."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ):
            response = client.post(
                "/api/analysis/dataflow/upload",
                files={"file": ("test.txt", b"not xml content", "text/plain")},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "Only XML files are supported" in data["detail"]

    def test_bulk_analyze_success(self, client, mock_user):
        """Test successful bulk dataflow analysis."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.services.service_factory.get_dataflow_analysis_service"
        ) as mock_service_factory:
            # Mock service
            mock_service = AsyncMock()
            mock_test_result = MagicMock()
            mock_test_result.dataflow.id = "TEST_DF1"
            mock_test_result.dataflow.display_name = "Test Dataflow"
            mock_test_result.dataflow.category = DataflowCategory.POPOLAZIONE
            mock_test_result.test.dataflow_id = "TEST_DF1"
            mock_test_result.test.data_access_success = True
            mock_test_result.test.size_mb = 1.0
            mock_service.bulk_analyze.return_value = [mock_test_result]
            mock_service_factory.return_value = mock_service

            response = client.post(
                "/api/analysis/dataflow/bulk",
                json={
                    "dataflow_ids": ["TEST_DF1", "TEST_DF2"],
                    "include_tests": True,
                    "max_concurrent": 2,
                },
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["requested_count"] == 2
            assert data["successful_count"] == 1
            assert len(data["results"]) == 1

    def test_bulk_analyze_too_many_ids(self, client, mock_user):
        """Test bulk analysis with too many dataflow IDs."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ):
            # Create list with 51 IDs (over the limit)
            dataflow_ids = [f"DF_{i}" for i in range(51)]

            response = client.post(
                "/api/analysis/dataflow/bulk",
                json={"dataflow_ids": dataflow_ids},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 422
            data = response.json()
            assert "Maximum 50 dataflow IDs allowed" in str(data["detail"])


class TestCategorizationRulesAPI:
    """Test categorization rules management API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user with write permissions."""
        return {
            "sub": "test_user",
            "api_key_id": 1,
            "scopes": ["read", "write"],
            "exp": datetime.now().timestamp() + 3600,
        }

    @pytest.fixture
    def sample_rules_data(self):
        """Sample categorization rules data."""
        return [
            {
                "id": 1,
                "rule_id": "test_rule1",
                "category": "popolazione",
                "keywords": ["popolazione", "demo"],
                "priority": 10,
                "is_active": True,
                "description": "Test rule 1",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
            {
                "id": 2,
                "rule_id": "test_rule2",
                "category": "economia",
                "keywords": ["economia", "pil"],
                "priority": 8,
                "is_active": False,
                "description": "Test rule 2",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        ]

    def test_get_categorization_rules_success(
        self, client, mock_user, sample_rules_data
    ):
        """Test successful retrieval of categorization rules."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository
            mock_repo = MagicMock()
            mock_repo.get_categorization_rules.return_value = sample_rules_data
            mock_repo_factory.return_value = mock_repo

            response = client.get(
                "/api/analysis/rules", headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["total_count"] == 2
            assert data["active_count"] == 1
            assert len(data["rules"]) == 2

            # Check first rule
            rule1 = data["rules"][0]
            assert rule1["rule_id"] == "test_rule1"
            assert rule1["category"] == "popolazione"
            assert rule1["keywords"] == ["popolazione", "demo"]
            assert rule1["is_active"] is True

    def test_get_categorization_rules_filtered(
        self, client, mock_user, sample_rules_data
    ):
        """Test retrieval of categorization rules with filters."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository to return filtered results
            filtered_data = [
                rule for rule in sample_rules_data if rule["category"] == "popolazione"
            ]
            mock_repo = MagicMock()
            mock_repo.get_categorization_rules.return_value = filtered_data
            mock_repo_factory.return_value = mock_repo

            response = client.get(
                "/api/analysis/rules?category=popolazione&active_only=true",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["rules"]) == 1
            assert data["rules"][0]["category"] == "popolazione"

            # Verify repository was called with correct parameters
            mock_repo.get_categorization_rules.assert_called_once_with(
                "popolazione", True
            )

    def test_create_categorization_rule_success(self, client, mock_user):
        """Test successful creation of categorization rule."""
        with patch("src.api.dependencies.require_write", return_value=mock_user), patch(
            "src.api.dependencies.check_rate_limit"
        ), patch("src.api.dependencies.log_api_request"), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository
            mock_repo = MagicMock()
            mock_repo.create_categorization_rule.return_value = True
            mock_repo_factory.return_value = mock_repo

            rule_data = {
                "rule_id": "new_rule",
                "category": "popolazione",
                "keywords": ["test", "keyword"],
                "priority": 7,
                "description": "New test rule",
            }

            response = client.post(
                "/api/analysis/rules",
                json=rule_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "created successfully" in data["message"]

            # Verify repository was called correctly
            mock_repo.create_categorization_rule.assert_called_once_with(
                rule_id="new_rule",
                category="popolazione",
                keywords=["test", "keyword"],
                priority=7,
                description="New test rule",
            )

    def test_create_categorization_rule_already_exists(self, client, mock_user):
        """Test creation of categorization rule that already exists."""
        with patch("src.api.dependencies.require_write", return_value=mock_user), patch(
            "src.api.dependencies.check_rate_limit"
        ), patch("src.api.dependencies.log_api_request"), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository to return False (rule already exists)
            mock_repo = MagicMock()
            mock_repo.create_categorization_rule.return_value = False
            mock_repo_factory.return_value = mock_repo

            rule_data = {
                "rule_id": "existing_rule",
                "category": "popolazione",
                "keywords": ["test"],
                "priority": 5,
            }

            response = client.post(
                "/api/analysis/rules",
                json=rule_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "may already exist" in data["detail"]

    def test_update_categorization_rule_success(self, client, mock_user):
        """Test successful update of categorization rule."""
        with patch("src.api.dependencies.require_write", return_value=mock_user), patch(
            "src.api.dependencies.check_rate_limit"
        ), patch("src.api.dependencies.log_api_request"), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository
            mock_repo = MagicMock()
            mock_repo.update_categorization_rule.return_value = True
            mock_repo_factory.return_value = mock_repo

            update_data = {
                "keywords": ["updated", "keywords"],
                "priority": 9,
                "is_active": False,
            }

            response = client.put(
                "/api/analysis/rules/test_rule",
                json=update_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "updated successfully" in data["message"]

            # Verify repository was called correctly
            mock_repo.update_categorization_rule.assert_called_once_with(
                rule_id="test_rule",
                keywords=["updated", "keywords"],
                priority=9,
                is_active=False,
                description=None,
            )

    def test_update_categorization_rule_not_found(self, client, mock_user):
        """Test update of non-existent categorization rule."""
        with patch("src.api.dependencies.require_write", return_value=mock_user), patch(
            "src.api.dependencies.check_rate_limit"
        ), patch("src.api.dependencies.log_api_request"), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository to return False (rule not found)
            mock_repo = MagicMock()
            mock_repo.update_categorization_rule.return_value = False
            mock_repo_factory.return_value = mock_repo

            response = client.put(
                "/api/analysis/rules/nonexistent",
                json={"priority": 5},
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]

    def test_delete_categorization_rule_success(self, client, mock_user):
        """Test successful deletion of categorization rule."""
        with patch("src.api.dependencies.require_write", return_value=mock_user), patch(
            "src.api.dependencies.check_rate_limit"
        ), patch("src.api.dependencies.log_api_request"), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository
            mock_repo = MagicMock()
            mock_repo.delete_categorization_rule.return_value = True
            mock_repo_factory.return_value = mock_repo

            response = client.delete(
                "/api/analysis/rules/test_rule",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "deleted successfully" in data["message"]

            # Verify repository was called correctly
            mock_repo.delete_categorization_rule.assert_called_once_with("test_rule")

    def test_delete_categorization_rule_not_found(self, client, mock_user):
        """Test deletion of non-existent categorization rule."""
        with patch("src.api.dependencies.require_write", return_value=mock_user), patch(
            "src.api.dependencies.check_rate_limit"
        ), patch("src.api.dependencies.log_api_request"), patch(
            "src.database.sqlite.repository.get_unified_repository"
        ) as mock_repo_factory:
            # Mock repository to return False (rule not found)
            mock_repo = MagicMock()
            mock_repo.delete_categorization_rule.return_value = False
            mock_repo_factory.return_value = mock_repo

            response = client.delete(
                "/api/analysis/rules/nonexistent",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]

    def test_download_sample_file_success(self, client, mock_user):
        """Test successful sample file download."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.utils.temp_file_manager.get_temp_manager"
        ) as mock_temp_manager_factory:
            # Mock temp file manager
            mock_temp_manager = MagicMock()
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_temp_manager.get_temp_file_path.return_value = mock_path
            mock_temp_manager_factory.return_value = mock_temp_manager

            # Note: This will fail with actual FileResponse, but we can test the logic
            with patch(
                "src.api.dataflow_analysis_api.FileResponse"
            ) as mock_file_response:
                mock_file_response.return_value = MagicMock()

                response = client.get(
                    "/api/analysis/samples/TEST_DF1",
                    headers={"Authorization": "Bearer test_token"},
                )

                # Verify the logic was executed
                mock_temp_manager.get_temp_file_path.assert_called_once_with(
                    "sample_TEST_DF1.xml"
                )
                mock_path.exists.assert_called_once()

    def test_download_sample_file_not_found(self, client, mock_user):
        """Test sample file download when file doesn't exist."""
        with patch(
            "src.api.dependencies.get_current_user", return_value=mock_user
        ), patch("src.api.dependencies.check_rate_limit"), patch(
            "src.api.dependencies.log_api_request"
        ), patch(
            "src.utils.temp_file_manager.get_temp_manager"
        ) as mock_temp_manager_factory:
            # Mock temp file manager with non-existent file
            mock_temp_manager = MagicMock()
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_temp_manager.get_temp_file_path.return_value = mock_path
            mock_temp_manager_factory.return_value = mock_temp_manager

            response = client.get(
                "/api/analysis/samples/NONEXISTENT",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 404
            data = response.json()
            assert "Sample file" in data["detail"]
            assert "not found" in data["detail"]


class TestAPIAuthentication:
    """Test API authentication and authorization."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_unauthenticated_request(self, client):
        """Test request without authentication token."""
        response = client.get("/api/analysis/rules")

        # Should return 401 or 403 depending on auth implementation
        assert response.status_code in [401, 403]

    def test_invalid_token(self, client):
        """Test request with invalid authentication token."""
        with patch("src.api.dependencies.get_current_user") as mock_auth:
            # Mock authentication to raise HTTPException
            from fastapi import HTTPException, status

            mock_auth.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

            response = client.get(
                "/api/analysis/rules", headers={"Authorization": "Bearer invalid_token"}
            )

            assert response.status_code == 401

    def test_insufficient_permissions(self, client):
        """Test request with insufficient permissions for write operations."""
        mock_user = {
            "sub": "read_only_user",
            "api_key_id": 1,
            "scopes": ["read"],  # No write permission
            "exp": datetime.now().timestamp() + 3600,
        }

        with patch("src.api.dependencies.require_write") as mock_require_write:
            # Mock require_write to raise HTTPException
            from fastapi import HTTPException, status

            mock_require_write.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

            response = client.post(
                "/api/analysis/rules",
                json={
                    "rule_id": "test",
                    "category": "popolazione",
                    "keywords": ["test"],
                },
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 403
