"""
Unit tests for LegacyDataflowAnalyzerAdapter.

Tests the backward-compatibility adapter that maintains the legacy interface
while using the modern DataflowAnalysisService internally.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.services.legacy_adapter import (
    LegacyDataflowAnalyzerAdapter,
    create_legacy_adapter,
)
from src.services.models import (
    AnalysisResult,
    ConnectionType,
    DataflowCategory,
    DataflowTest,
    DataflowTestResult,
    IstatDataflow,
    RefreshFrequency,
)


class TestLegacyDataflowAnalyzerAdapter:
    """Test legacy adapter functionality."""

    @pytest.fixture
    def adapter(self):
        """Create a legacy adapter instance for testing."""
        return LegacyDataflowAnalyzerAdapter()

    @pytest.fixture
    def mock_service(self):
        """Create a mock DataflowAnalysisService."""
        service = MagicMock()
        service.analyze_dataflows_from_xml = AsyncMock()
        service.test_dataflow_access = AsyncMock()
        service.bulk_analyze = AsyncMock()
        return service

    @pytest.fixture
    def sample_analysis_result(self):
        """Create a sample analysis result for testing."""
        dataflow = IstatDataflow(
            id="DCIS_POPRES1",
            name_it="Popolazione residente",
            name_en="Resident population",
            description="Popolazione residente per comune",
            category=DataflowCategory.POPOLAZIONE,
            relevance_score=95,  # Changed to int
        )

        test = DataflowTest(
            dataflow=dataflow,
            success=True,
            response_time_ms=150,
            observations_count=1000,
            size_bytes=50000,
            tableau_ready=True,
            connection_type=ConnectionType.DIRECT_CONNECTION,  # Use correct enum
            refresh_frequency=RefreshFrequency.MONTHLY,
        )

        test_result = DataflowTestResult(dataflow=dataflow, test=test)

        return AnalysisResult(
            total_analyzed=1,
            categorized_dataflows={DataflowCategory.POPOLAZIONE: [dataflow]},
            test_results=[test_result],
            processing_time_seconds=0.5,
            filters_applied={},
        )

    def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter is not None
        assert adapter.base_url == "https://sdmx.istat.it/SDMXWS/rest/"
        assert adapter._service is None
        assert adapter._analysis_result is None

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    def test_service_lazy_initialization(self, mock_get_service, adapter):
        """Test lazy initialization of the service."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # First access should initialize the service
        service = adapter.service
        assert service == mock_service
        mock_get_service.assert_called_once()

        # Second access should use cached service
        service2 = adapter.service
        assert service2 == mock_service
        assert mock_get_service.call_count == 1

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    @patch("builtins.open", new_callable=mock_open, read_data="<xml>test</xml>")
    @patch("pathlib.Path.exists", return_value=True)
    def test_parse_dataflow_xml_success(
        self, mock_exists, mock_file, mock_get_service, adapter, sample_analysis_result
    ):
        """Test successful XML parsing."""
        mock_service = MagicMock()
        mock_service.analyze_dataflows_from_xml = AsyncMock(
            return_value=sample_analysis_result
        )
        mock_get_service.return_value = mock_service

        result = adapter.parse_dataflow_xml("test.xml")

        assert isinstance(result, dict)
        assert DataflowCategory.POPOLAZIONE.value in result
        assert len(result[DataflowCategory.POPOLAZIONE.value]) == 1

        dataflow_data = result[DataflowCategory.POPOLAZIONE.value][0]
        assert dataflow_data["id"] == "DCIS_POPRES1"
        assert dataflow_data["name_it"] == "Popolazione residente"
        assert dataflow_data["category"] == DataflowCategory.POPOLAZIONE.value

    @patch("pathlib.Path.exists", return_value=False)
    def test_parse_dataflow_xml_file_not_found(self, mock_exists, adapter):
        """Test XML parsing when file doesn't exist."""
        result = adapter.parse_dataflow_xml("nonexistent.xml")
        assert result == {}

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    @patch("builtins.open", side_effect=IOError("File read error"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_parse_dataflow_xml_read_error(
        self, mock_exists, mock_file, mock_get_service, adapter
    ):
        """Test XML parsing with file read error."""
        result = adapter.parse_dataflow_xml("test.xml")
        assert result == {}

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    def test_analyze_dataflows_xml_success(
        self, mock_get_service, adapter, sample_analysis_result
    ):
        """Test async XML analysis."""
        mock_service = MagicMock()
        mock_service.analyze_dataflows_from_xml = AsyncMock(
            return_value=sample_analysis_result
        )
        mock_get_service.return_value = mock_service

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                adapter.analyze_dataflows_xml("<xml>test</xml>")
            )

            assert isinstance(result, dict)
            assert DataflowCategory.POPOLAZIONE.value in result
            mock_service.analyze_dataflows_from_xml.assert_called_once()
        finally:
            loop.close()

    def test_find_top_dataflows_by_category_with_data(
        self, adapter, sample_analysis_result
    ):
        """Test finding top dataflows by category."""
        adapter._analysis_result = sample_analysis_result

        # Create legacy format categorized dataflows
        categorized_data = {
            DataflowCategory.POPOLAZIONE.value: [
                {
                    "id": "DCIS_POPRES1",
                    "name_it": "Popolazione residente",
                    "display_name": "Popolazione residente",
                    "relevance_score": 95,
                    "description": "Test description",
                }
            ]
        }

        result = adapter.find_top_dataflows_by_category(categorized_data, top_n=5)

        assert isinstance(result, dict)
        assert DataflowCategory.POPOLAZIONE.value in result
        assert len(result[DataflowCategory.POPOLAZIONE.value]) == 1

    def test_find_top_dataflows_by_category_no_data(self, adapter):
        """Test finding top dataflows when no analysis result exists."""
        result = adapter.find_top_dataflows_by_category({}, top_n=5)
        assert result == {}

    def test_find_top_dataflows_by_category_invalid_category(
        self, adapter, sample_analysis_result
    ):
        """Test finding top dataflows with invalid category."""
        categorized_data = {"INVALID_CATEGORY": []}
        result = adapter.find_top_dataflows_by_category(categorized_data, top_n=5)
        assert result == {"INVALID_CATEGORY": []}

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    def test_test_priority_dataflows(
        self, mock_get_service, adapter, sample_analysis_result
    ):
        """Test testing priority dataflows."""
        mock_service = MagicMock()
        mock_service.bulk_analyze = AsyncMock(
            return_value=[sample_analysis_result.test_results[0]]
        )
        mock_get_service.return_value = mock_service

        # Create mock top_dataflows in expected format
        top_dataflows = {
            DataflowCategory.POPOLAZIONE.value: [
                {"id": "DCIS_POPRES1", "name": "Test dataflow"}
            ]
        }

        result = adapter.test_priority_dataflows(top_dataflows, max_tests=1)

        assert isinstance(result, list)

    def test_create_tableau_ready_dataset_list(self, adapter):
        """Test creating Tableau-ready dataset list."""
        tested_dataflows = [
            {
                "id": "DCIS_POPRES1",
                "name": "Test dataflow",
                "tests": {"data_access": {"success": True}, "response_time": 150},
            }
        ]

        result = adapter.create_tableau_ready_dataset_list(tested_dataflows)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_create_tableau_ready_dataset_list_no_data(self, adapter):
        """Test creating Tableau-ready dataset list with no data."""
        result = adapter.create_tableau_ready_dataset_list([])
        assert result == []

    def test_generate_tableau_implementation_guide(self, adapter):
        """Test generating Tableau implementation guide."""
        tested_dataflows = [
            {
                "id": "DCIS_POPRES1",
                "name": "Test dataflow",
                "tests": {"data_access": {"success": True}},
            }
        ]

        result = adapter.generate_tableau_implementation_guide(tested_dataflows)

        assert isinstance(result, dict)
        assert "datasets" in result
        assert "powershell_script" in result
        assert "prep_flow_template" in result

    def test_generate_summary_report(self, adapter):
        """Test generating summary report."""
        categorized_data = {
            DataflowCategory.POPOLAZIONE.value: [
                {"id": "DCIS_POPRES1", "name_it": "Popolazione residente"}
            ]
        }

        result = adapter.generate_summary_report(categorized_data)

        assert isinstance(result, str)
        assert "ISTAT Data Analysis" in result  # Correct text from actual method
        assert "DCIS_POPRES1" in result
        assert DataflowCategory.POPOLAZIONE.value.upper() in result

    def test_suggest_tableau_connection(self, adapter):
        """Test suggesting Tableau connection type."""
        # Create dataflow with tests structure expected by the method
        dataflow_small = {"id": "TEST_SMALL", "tests": {"observations_count": 500}}
        dataflow_large = {"id": "TEST_LARGE", "tests": {"observations_count": 50000}}

        result_small = adapter._suggest_tableau_connection(dataflow_small)
        result_large = adapter._suggest_tableau_connection(dataflow_large)

        assert result_small == ConnectionType.DIRECT_CONNECTION.value
        assert result_large == ConnectionType.BIGQUERY_EXTRACT.value

    def test_suggest_refresh_frequency(self, adapter):
        """Test suggesting refresh frequency by category."""
        freq_pop = adapter._suggest_refresh_frequency(
            DataflowCategory.POPOLAZIONE.value
        )
        freq_econ = adapter._suggest_refresh_frequency(DataflowCategory.ECONOMIA.value)
        freq_unknown = adapter._suggest_refresh_frequency("UNKNOWN")

        assert freq_pop == RefreshFrequency.YEARLY.value  # Correct enum value
        assert freq_econ == RefreshFrequency.QUARTERLY.value
        assert freq_unknown == RefreshFrequency.MONTHLY.value

    def test_calculate_priority(self, adapter):
        """Test calculating dataflow priority."""
        high_priority = {
            "category": DataflowCategory.POPOLAZIONE.value,
            "relevance_score": 0.95,
            "observations_count": 10000,
        }

        low_priority = {
            "category": DataflowCategory.ALTRI.value,
            "relevance_score": 0.3,
            "observations_count": 100,
        }

        result_high = adapter._calculate_priority(high_priority)
        result_low = adapter._calculate_priority(low_priority)

        assert result_high > result_low
        assert result_high > 0.8  # Should be high priority
        assert result_low < 0.5  # Should be low priority

    def test_generate_powershell_script(self, adapter):
        """Test generating PowerShell script."""
        datasets = [
            {
                "id": "DCIS_POPRES1",
                "name_it": "Popolazione residente",
                "connection_type": ConnectionType.DIRECT_CONNECTION.value,
            }
        ]

        result = adapter._generate_powershell_script(datasets)

        assert isinstance(result, str)
        assert "DCIS_POPRES1" in result
        assert "PowerShell" in result

    def test_generate_prep_flow_template(self, adapter):
        """Test generating Prep flow template."""
        datasets = [
            {
                "id": "DCIS_POPRES1",
                "name_it": "Popolazione residente",
                "connection_type": ConnectionType.DIRECT_CONNECTION.value,
            }
        ]

        result = adapter._generate_prep_flow_template(datasets)

        assert isinstance(result, dict)
        assert "flow_name" in result
        assert "steps" in result
        assert len(result["steps"]) > 0

    def test_create_legacy_adapter_factory(self):
        """Test factory function for creating legacy adapter."""
        adapter = create_legacy_adapter()
        assert isinstance(adapter, LegacyDataflowAnalyzerAdapter)


class TestLegacyAdapterErrorHandling:
    """Test error handling in legacy adapter."""

    @pytest.fixture
    def adapter(self):
        """Create a legacy adapter instance for testing."""
        return LegacyDataflowAnalyzerAdapter()

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    def test_service_initialization_error(self, mock_get_service, adapter):
        """Test handling of service initialization errors."""
        mock_get_service.side_effect = Exception("Service initialization failed")

        with pytest.raises(Exception):
            _ = adapter.service

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    @patch("builtins.open", new_callable=mock_open, read_data="<xml>test</xml>")
    @patch("pathlib.Path.exists", return_value=True)
    def test_parse_dataflow_xml_service_error(
        self, mock_exists, mock_file, mock_get_service, adapter
    ):
        """Test XML parsing with service error."""
        mock_service = MagicMock()
        mock_service.analyze_dataflows_from_xml = AsyncMock(
            side_effect=Exception("Service error")
        )
        mock_get_service.return_value = mock_service

        result = adapter.parse_dataflow_xml("test.xml")
        assert result == {}

    @patch("src.services.legacy_adapter.get_dataflow_analysis_service")
    def test_test_priority_dataflows_service_error(self, mock_get_service, adapter):
        """Test priority dataflow testing with service error."""
        mock_service = MagicMock()
        mock_service.bulk_analyze = AsyncMock(
            side_effect=Exception("Bulk analyze failed")
        )
        mock_get_service.return_value = mock_service

        # Create minimal top_dataflows in expected format
        top_dataflows = {DataflowCategory.POPOLAZIONE.value: []}

        result = adapter.test_priority_dataflows(top_dataflows, max_tests=1)

        # Should return empty result on error
        assert isinstance(result, list)
        assert result == []
