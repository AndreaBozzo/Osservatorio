"""
Unit tests for tableau_api module.
Testing TableauServerAnalyzer class with comprehensive coverage.
"""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.api.tableau_api import TableauServerAnalyzer


class TestTableauServerAnalyzer:
    """Test TableauServerAnalyzer class."""

    @pytest.fixture
    def sample_data(self):
        """Sample Tableau Server data for testing."""
        return {
            "result": {
                "user": {
                    "username": "test_user",
                    "displayName": "Test User",
                    "domainName": "test.com",
                    "locale": "en_US",
                    "userTimeZone": {"displayName": "UTC"},
                    "numberOfSites": 3,
                    "canWebEditFlow": True,
                },
                "server": {
                    "version": {
                        "externalVersion": {
                            "major": "2023",
                            "minor": "3",
                            "patch": "0",
                        },
                        "build": "20230101.123456",
                        "platform": "win64",
                        "bitness": "64",
                    },
                    "podId": "pod-123",
                    "betaPod": False,
                    "oauthSettings": [
                        {
                            "type": "google_bigquery",
                            "displayNames": {"en": "Google BigQuery"},
                            "supportsGenericAuth": True,
                            "supportsTestToken": False,
                            "supportsCustomDomain": True,
                        },
                        {
                            "type": "google_sheets",
                            "displayNames": {"en": "Google Sheets"},
                            "supportsGenericAuth": True,
                            "supportsTestToken": True,
                            "supportsCustomDomain": False,
                        },
                        {
                            "type": "box",
                            "displayNames": {"en": "Box"},
                            "supportsGenericAuth": False,
                            "supportsTestToken": False,
                            "supportsCustomDomain": False,
                        },
                    ],
                },
                "site": {
                    "role": "SiteAdministrator",
                    "settings": {
                        "webEditingEnabled": True,
                        "flowAutoSaveEnabled": True,
                        "collectionsEnabled": False,
                        "dataAlertsEnabled": True,
                        "commentingMentionsEnabled": True,
                        "pulseEnabled": False,
                        "generativeAiEnabled": True,
                        "explainDataEnabled": True,
                        "recycleBinEnabled": True,
                        "catalogObfuscationEnabled": False,
                    },
                    "versioningEnabled": True,
                    "dataManagementEnabled": True,
                    "extractEncryptionMode": "enforced",
                    "userVisibility": "limited",
                    "mfaEnabled": True,
                    "mfaRequired": False,
                },
            }
        }

    @pytest.fixture
    def analyzer(self, sample_data):
        """Create analyzer instance with sample data."""
        return TableauServerAnalyzer(sample_data)

    def test_init(self, sample_data):
        """Test analyzer initialization."""
        analyzer = TableauServerAnalyzer(sample_data)
        assert analyzer.data == sample_data
        assert analyzer.result == sample_data["result"]
        assert analyzer.user == sample_data["result"]["user"]
        assert analyzer.server == sample_data["result"]["server"]
        assert analyzer.site == sample_data["result"]["site"]

    def test_init_empty_data(self):
        """Test initialization with empty data."""
        analyzer = TableauServerAnalyzer({})
        assert analyzer.data == {}
        assert analyzer.result == {}
        assert analyzer.user == {}
        assert analyzer.server == {}
        assert analyzer.site == {}

    def test_get_user_info(self, analyzer):
        """Test user information extraction."""
        user_info = analyzer.get_user_info()

        expected = {
            "username": "test_user",
            "display_name": "Test User",
            "role": "SiteAdministrator",
            "domain": "test.com",
            "locale": "en_US",
            "timezone": "UTC",
            "sites_count": 3,
            "can_web_edit": True,
        }

        assert user_info == expected

    def test_get_user_info_partial_data(self):
        """Test user info with partial data."""
        partial_data = {"result": {"user": {"username": "partial"}, "site": {}}}
        analyzer = TableauServerAnalyzer(partial_data)
        user_info = analyzer.get_user_info()

        assert user_info["username"] == "partial"
        assert user_info["display_name"] is None
        assert user_info["role"] is None

    def test_get_server_info(self, analyzer):
        """Test server information extraction."""
        server_info = analyzer.get_server_info()

        expected = {
            "version": "2023.3.0",
            "build": "20230101.123456",
            "platform": "win64",
            "bitness": "64",
            "pod_id": "pod-123",
            "is_beta": False,
        }

        assert server_info == expected

    def test_get_server_info_missing_version(self):
        """Test server info with missing version data."""
        data = {"result": {"server": {"podId": "pod-456"}}}
        analyzer = TableauServerAnalyzer(data)
        server_info = analyzer.get_server_info()

        assert "." in server_info["version"]  # Should handle None values gracefully
        assert server_info["pod_id"] == "pod-456"

    def test_get_available_connectors(self, analyzer):
        """Test connector extraction and sorting."""
        connectors = analyzer.get_available_connectors()

        assert len(connectors) == 3
        # Should be sorted by name
        assert connectors[0]["name"] == "Box"
        assert connectors[1]["name"] == "Google BigQuery"
        assert connectors[2]["name"] == "Google Sheets"

        # Check connector properties
        bigquery = connectors[1]
        assert bigquery["type"] == "google_bigquery"
        assert bigquery["supports_oauth"] is True
        assert bigquery["supports_custom_domain"] is True

    def test_get_available_connectors_empty(self):
        """Test connectors with empty oauth settings."""
        data = {"result": {"server": {"oauthSettings": []}}}
        analyzer = TableauServerAnalyzer(data)
        connectors = analyzer.get_available_connectors()

        assert connectors == []

    def test_get_site_capabilities(self, analyzer):
        """Test site capabilities extraction."""
        capabilities = analyzer.get_site_capabilities()

        expected = {
            "web_authoring": True,
            "flows_enabled": True,
            "collections_enabled": False,
            "data_alerts": True,
            "commenting": True,
            "pulse_enabled": False,
            "generative_ai": True,
            "explain_data": True,
            "recycling_bin": True,
            "versioning": True,
        }

        assert capabilities == expected

    def test_get_site_capabilities_defaults(self):
        """Test site capabilities with default values."""
        data = {"result": {"site": {"settings": {}}}}
        analyzer = TableauServerAnalyzer(data)
        capabilities = analyzer.get_site_capabilities()

        # All should default to False
        assert not any(capabilities.values())

    def test_get_governance_settings(self, analyzer):
        """Test governance settings extraction."""
        governance = analyzer.get_governance_settings()

        expected = {
            "catalog_enabled": False,
            "data_management": True,
            "extract_encryption": "enforced",
            "user_visibility": "limited",
            "mfa_enabled": True,
            "mfa_required": False,
        }

        assert governance == expected

    def test_get_governance_settings_defaults(self):
        """Test governance settings with defaults."""
        data = {"result": {"site": {"settings": {}}}}
        analyzer = TableauServerAnalyzer(data)
        governance = analyzer.get_governance_settings()

        assert governance["catalog_enabled"] is False
        assert governance["mfa_enabled"] is False

    def test_find_data_sources(self, analyzer):
        """Test data source filtering."""
        sources = analyzer.find_data_sources()

        # Should find Google connectors and Box
        assert len(sources) == 3
        source_names = [s["name"] for s in sources]
        assert "Google BigQuery" in source_names
        assert "Google Sheets" in source_names
        assert "Box" in source_names

    def test_find_data_sources_no_matches(self):
        """Test data sources with no useful connectors."""
        data = {
            "result": {
                "server": {
                    "oauthSettings": [
                        {
                            "type": "other_connector",
                            "displayNames": {"en": "Other Connector"},
                            "supportsGenericAuth": False,
                        }
                    ]
                }
            }
        }
        analyzer = TableauServerAnalyzer(data)
        sources = analyzer.find_data_sources()

        assert sources == []

    def test_generate_scraping_strategy(self, analyzer):
        """Test scraping strategy generation."""
        strategy = analyzer.generate_scraping_strategy()

        assert "direct_api" in strategy
        assert "web_scraping" in strategy
        assert "file_upload" in strategy
        assert "recommendations" in strategy

        # Should have recommendations for Google services
        assert len(strategy["direct_api"]) > 0
        assert len(strategy["recommendations"]) == 4

        # Check specific recommendations
        google_apis = [api for api in strategy["direct_api"] if "Google" in api]
        assert len(google_apis) >= 1

    def test_generate_scraping_strategy_no_connectors(self):
        """Test strategy with no useful connectors."""
        data = {"result": {"server": {"oauthSettings": []}}}
        analyzer = TableauServerAnalyzer(data)
        strategy = analyzer.generate_scraping_strategy()

        assert strategy["direct_api"] == []
        assert len(strategy["recommendations"]) == 4  # Static recommendations

    @patch("builtins.print")
    def test_print_full_analysis(self, mock_print, analyzer):
        """Test full analysis printing."""
        analyzer.print_full_analysis()

        # Should have called print multiple times
        assert mock_print.call_count > 20

        # Check some key outputs were printed
        call_args = [str(call) for call in mock_print.call_args_list]
        analysis_text = " ".join(call_args)

        assert "ANALISI TABLEAU SERVER" in analysis_text
        assert "INFORMAZIONI UTENTE" in analysis_text
        assert "INFORMAZIONI SERVER" in analysis_text
        assert "CAPACITÀ SITO" in analysis_text
        assert "test_user" in analysis_text

    def test_main_execution_simulation(self):
        """Test main execution logic without mocking imports."""
        # Simulate the main execution logic
        tableau_data = {"result": {"user": {"username": "test"}}}

        analyzer = TableauServerAnalyzer(tableau_data)
        connectors = analyzer.get_available_connectors()

        # Verify basic functionality
        assert isinstance(connectors, list)
        assert analyzer.get_user_info()["username"] == "test"

    def test_edge_case_malformed_oauth_settings(self):
        """Test handling of malformed OAuth settings."""
        data = {
            "result": {
                "server": {
                    "oauthSettings": [
                        {},  # Empty setting
                        {"type": "incomplete"},  # Missing displayNames
                        {"displayNames": {"en": "No Type"}},  # Missing type
                    ]
                }
            }
        }
        analyzer = TableauServerAnalyzer(data)
        connectors = analyzer.get_available_connectors()

        # Should handle gracefully
        assert len(connectors) == 3
        assert connectors[0]["type"] == ""  # Empty string for missing type

    def test_version_string_edge_cases(self):
        """Test version string formatting with None values."""
        data = {
            "result": {
                "server": {
                    "version": {
                        "externalVersion": {"major": None, "minor": "3", "patch": None}
                    }
                }
            }
        }
        analyzer = TableauServerAnalyzer(data)
        server_info = analyzer.get_server_info()

        # Should handle None values in version
        assert "None" in server_info["version"] or "." in server_info["version"]
