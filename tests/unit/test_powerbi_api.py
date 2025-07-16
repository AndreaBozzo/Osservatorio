"""
Unit tests for PowerBI API client.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.api.powerbi_api import PowerBIAPIClient


@pytest.mark.unit
class TestPowerBIAPIClient:
    """Test PowerBI API client functionality."""

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_client_initialization(self, mock_msal, mock_config):
        """Test PowerBI client initialization."""
        # Mock configuration
        mock_config.POWERBI_CLIENT_ID = "test_client_id"
        mock_config.POWERBI_CLIENT_SECRET = "test_client_secret"
        mock_config.POWERBI_TENANT_ID = "test_tenant_id"
        mock_config.POWERBI_WORKSPACE_ID = "test_workspace_id"

        # Mock MSAL app
        mock_app = Mock()
        mock_msal.return_value = mock_app

        client = PowerBIAPIClient()

        assert client.base_url == "https://api.powerbi.com/v1.0/myorg"
        assert client.client_id == "test_client_id"
        assert client.client_secret == "test_client_secret"
        assert client.tenant_id == "test_tenant_id"
        assert client.workspace_id == "test_workspace_id"

        # Verify MSAL initialization
        mock_msal.assert_called_once_with(
            "test_client_id",
            authority="https://login.microsoftonline.com/test_tenant_id",
            client_credential="test_client_secret",
        )

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_authentication_success(self, mock_msal, mock_config):
        """Test successful authentication."""
        # Mock configuration
        mock_config.POWERBI_CLIENT_ID = "test_client_id"
        mock_config.POWERBI_CLIENT_SECRET = "test_client_secret"
        mock_config.POWERBI_TENANT_ID = "test_tenant_id"
        mock_config.POWERBI_WORKSPACE_ID = "test_workspace_id"

        # Mock MSAL app
        mock_app = Mock()
        mock_msal.return_value = mock_app

        # Mock successful token acquisition
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600,
        }

        client = PowerBIAPIClient()
        result = client.authenticate()

        assert result == True
        assert client.access_token == "test_access_token"
        assert client.token_expires_at > datetime.now()
        assert "Bearer test_access_token" in client.session.headers["Authorization"]

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_authentication_failure(self, mock_msal, mock_config):
        """Test authentication failure."""
        # Mock configuration
        mock_config.POWERBI_CLIENT_ID = "test_client_id"
        mock_config.POWERBI_CLIENT_SECRET = "test_client_secret"
        mock_config.POWERBI_TENANT_ID = "test_tenant_id"
        mock_config.POWERBI_WORKSPACE_ID = "test_workspace_id"

        # Mock MSAL app
        mock_app = Mock()
        mock_msal.return_value = mock_app

        # Mock failed token acquisition
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials",
        }

        client = PowerBIAPIClient()
        result = client.authenticate()

        assert result == False
        assert client.access_token is None

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_token_renewal(self, mock_msal, mock_config):
        """Test automatic token renewal."""
        # Mock configuration
        mock_config.POWERBI_CLIENT_ID = "test_client_id"
        mock_config.POWERBI_CLIENT_SECRET = "test_client_secret"
        mock_config.POWERBI_TENANT_ID = "test_tenant_id"
        mock_config.POWERBI_WORKSPACE_ID = "test_workspace_id"

        # Mock MSAL app
        mock_app = Mock()
        mock_msal.return_value = mock_app

        client = PowerBIAPIClient()

        # Set expired token
        client.access_token = "expired_token"
        client.token_expires_at = datetime.now() - timedelta(minutes=10)

        # Mock token renewal
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }

        result = client._ensure_authenticated()

        assert result == True
        assert client.access_token == "new_access_token"

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_get_workspaces(self, mock_msal, mock_config):
        """Test getting workspaces."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        # Mock successful API response
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "value": [
                    {"id": "workspace1", "name": "Test Workspace 1"},
                    {"id": "workspace2", "name": "Test Workspace 2"},
                ]
            }
            mock_get.return_value = mock_response

            workspaces = client.get_workspaces()

            assert len(workspaces) == 2
            assert workspaces[0]["id"] == "workspace1"
            assert workspaces[1]["name"] == "Test Workspace 2"

            mock_get.assert_called_once_with(
                "https://api.powerbi.com/v1.0/myorg/groups"
            )

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_get_datasets(self, mock_msal, mock_config):
        """Test getting datasets."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        # Mock successful API response
        with patch.object(client.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "value": [
                    {"id": "dataset1", "name": "Test Dataset 1"},
                    {"id": "dataset2", "name": "Test Dataset 2"},
                ]
            }
            mock_get.return_value = mock_response

            datasets = client.get_datasets("test_workspace_id")

            assert len(datasets) == 2
            assert datasets[0]["id"] == "dataset1"
            assert datasets[1]["name"] == "Test Dataset 2"

            mock_get.assert_called_once_with(
                "https://api.powerbi.com/v1.0/myorg/groups/test_workspace_id/datasets"
            )

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_create_dataset(self, mock_msal, mock_config):
        """Test creating a dataset."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        dataset_definition = {
            "name": "Test Dataset",
            "tables": [
                {
                    "name": "TestTable",
                    "columns": [
                        {"name": "ID", "dataType": "Int64"},
                        {"name": "Name", "dataType": "String"},
                    ],
                }
            ],
        }

        # Mock successful API response
        with patch.object(client.session, "post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "id": "new_dataset_id",
                "name": "Test Dataset",
            }
            mock_post.return_value = mock_response

            result = client.create_dataset(dataset_definition, "test_workspace_id")

            assert result["id"] == "new_dataset_id"
            assert result["name"] == "Test Dataset"

            mock_post.assert_called_once_with(
                "https://api.powerbi.com/v1.0/myorg/groups/test_workspace_id/datasets",
                json=dataset_definition,
            )

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_push_data_to_dataset(self, mock_msal, mock_config):
        """Test pushing data to a dataset."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        test_data = [{"ID": 1, "Name": "Test 1"}, {"ID": 2, "Name": "Test 2"}]

        # Mock successful API response
        with patch.object(client.session, "post") as mock_post:
            mock_response = Mock()
            mock_post.return_value = mock_response

            result = client.push_data_to_dataset(
                "test_dataset_id", "TestTable", test_data, "test_workspace_id"
            )

            assert result == True

            mock_post.assert_called_once_with(
                "https://api.powerbi.com/v1.0/myorg/groups/test_workspace_id/datasets/test_dataset_id/tables/TestTable/rows",
                json={"rows": test_data},
            )

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_refresh_dataset(self, mock_msal, mock_config):
        """Test dataset refresh."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        # Mock successful API response
        with patch.object(client.session, "post") as mock_post:
            mock_response = Mock()
            mock_post.return_value = mock_response

            result = client.refresh_dataset("test_dataset_id", "test_workspace_id")

            assert result == True

            mock_post.assert_called_once_with(
                "https://api.powerbi.com/v1.0/myorg/groups/test_workspace_id/datasets/test_dataset_id/refreshes"
            )

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_test_connection(self, mock_msal, mock_config):
        """Test connection testing functionality."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        # Mock successful authentication
        with patch.object(client, "authenticate", return_value=True):
            with patch.object(
                client, "get_workspaces", return_value=[{"id": "ws1"}, {"id": "ws2"}]
            ):
                with patch.object(client, "get_datasets", return_value=[{"id": "ds1"}]):
                    result = client.test_connection()

                    assert result["authentication"] == True
                    assert result["workspaces_accessible"] == True
                    assert result["workspace_count"] == 2
                    assert result["datasets_accessible"] == True
                    assert result["dataset_count"] == 1
                    assert len(result["errors"]) == 0

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_api_error_handling(self, mock_msal, mock_config):
        """Test API error handling."""
        # Mock configuration and authentication
        self._setup_authenticated_client(mock_config, mock_msal)

        client = PowerBIAPIClient()

        # Mock API error (use requests.RequestException which is handled)
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = requests.RequestException("API Error")

            workspaces = client.get_workspaces()

            assert workspaces == []

    @patch("src.api.powerbi_api.Config")
    @patch("src.api.powerbi_api.msal.ConfidentialClientApplication")
    def test_missing_workspace_id(self, mock_msal, mock_config):
        """Test behavior with missing workspace ID."""
        # Mock configuration without workspace ID
        mock_config.POWERBI_CLIENT_ID = "test_client_id"
        mock_config.POWERBI_CLIENT_SECRET = "test_client_secret"
        mock_config.POWERBI_TENANT_ID = "test_tenant_id"
        mock_config.POWERBI_WORKSPACE_ID = None

        # Mock MSAL app
        mock_app = Mock()
        mock_msal.return_value = mock_app

        client = PowerBIAPIClient()

        # Should return empty list when workspace ID is missing
        datasets = client.get_datasets()
        assert datasets == []

        reports = client.get_reports()
        assert reports == []

    def _setup_authenticated_client(self, mock_config, mock_msal):
        """Helper to setup authenticated client mocks."""
        # Mock configuration
        mock_config.POWERBI_CLIENT_ID = "test_client_id"
        mock_config.POWERBI_CLIENT_SECRET = "test_client_secret"
        mock_config.POWERBI_TENANT_ID = "test_tenant_id"
        mock_config.POWERBI_WORKSPACE_ID = "test_workspace_id"

        # Mock MSAL app
        mock_app = Mock()
        mock_msal.return_value = mock_app

        # Mock successful authentication
        mock_app.acquire_token_silent.return_value = None
        mock_app.acquire_token_for_client.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600,
        }

        return mock_app


@pytest.mark.unit
class TestPowerBIDataTypes:
    """Test PowerBI data type handling."""

    def test_dataset_definition_structure(self):
        """Test dataset definition structure."""
        dataset_def = {
            "name": "ISTAT Dataset",
            "tables": [
                {
                    "name": "IstatData",
                    "columns": [
                        {"name": "Territorio", "dataType": "String"},
                        {"name": "Anno", "dataType": "Int64"},
                        {"name": "Valore", "dataType": "Double"},
                        {"name": "UnitaMisura", "dataType": "String"},
                    ],
                }
            ],
        }

        # Verify structure
        assert "name" in dataset_def
        assert "tables" in dataset_def
        assert len(dataset_def["tables"]) == 1

        table = dataset_def["tables"][0]
        assert table["name"] == "IstatData"
        assert len(table["columns"]) == 4

        # Verify column types
        column_types = {col["name"]: col["dataType"] for col in table["columns"]}
        assert column_types["Territorio"] == "String"
        assert column_types["Anno"] == "Int64"
        assert column_types["Valore"] == "Double"
        assert column_types["UnitaMisura"] == "String"

    def test_data_row_formatting(self):
        """Test data row formatting for PowerBI."""
        raw_data = [
            {"territorio": "IT", "anno": 2024, "valore": 1000000.5, "unita": "numero"},
            {"territorio": "FR", "anno": 2023, "valore": 950000.0, "unita": "numero"},
        ]

        # Format for PowerBI (capitalize field names)
        formatted_data = []
        for row in raw_data:
            formatted_row = {
                "Territorio": row["territorio"],
                "Anno": row["anno"],
                "Valore": row["valore"],
                "UnitaMisura": row["unita"],
            }
            formatted_data.append(formatted_row)

        assert len(formatted_data) == 2
        assert formatted_data[0]["Territorio"] == "IT"
        assert formatted_data[0]["Anno"] == 2024
        assert formatted_data[1]["Valore"] == 950000.0
