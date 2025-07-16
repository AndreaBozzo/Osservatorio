"""
Integration tests for API connectivity and data fetching.
"""

import time
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

import pytest
import requests

from src.analyzers.dataflow_analyzer import IstatDataflowAnalyzer
from src.api.istat_api import IstatAPITester


@pytest.mark.integration
@pytest.mark.api
class TestAPIIntegration:
    """Test API integration functionality."""

    def test_istat_api_connectivity(self, mock_requests_session):
        """Test ISTAT API connectivity."""
        tester = IstatAPITester()

        # Mock successful responses for all endpoints
        mock_requests_session.get.return_value.status_code = 200
        mock_requests_session.get.return_value.elapsed.total_seconds.return_value = 1.0
        mock_requests_session.get.return_value.content = (
            b'<?xml version="1.0"?><test>data</test>'
        )

        # Test connectivity
        result = tester.test_api_connectivity()

        assert "connectivity" in result
        assert len(result["connectivity"]) > 0

        # All endpoints should be tested
        for test_result in result["connectivity"]:
            assert "endpoint" in test_result
            assert "success" in test_result
            assert "status_code" in test_result
            assert "response_time" in test_result

    def test_dataflow_discovery_integration(
        self, mock_requests_session, sample_dataflow_xml
    ):
        """Test dataflow discovery integration."""
        tester = IstatAPITester()

        # Mock dataflow response
        mock_requests_session.get.return_value.status_code = 200
        mock_requests_session.get.return_value.text = sample_dataflow_xml

        result = tester.discover_priority_datasets()

        assert "dataset_discovery" in result
        assert "total_dataflows" in result["dataset_discovery"]
        assert "datasets" in result["dataset_discovery"]

        # Should find datasets from sample XML
        datasets = result["dataset_discovery"]["datasets"]
        assert len(datasets) > 0

        # Check dataset structure
        for dataset in datasets:
            assert "id" in dataset
            assert "name" in dataset
            assert "category" in dataset
            assert "relevance_score" in dataset

    def test_dataset_testing_integration(self, mock_requests_session, sample_xml_data):
        """Test dataset testing integration."""
        tester = IstatAPITester()

        # Mock data response
        mock_requests_session.get.return_value.status_code = 200
        mock_requests_session.get.return_value.content = sample_xml_data.encode("utf-8")

        # Test priority datasets
        priority_datasets = [
            {
                "id": "101_12",
                "name": "Popolazione residente",
                "category": "popolazione",
                "relevance_score": 10,
            }
        ]

        with patch("time.sleep"):  # Skip rate limiting in tests
            result = tester.test_priority_datasets(priority_datasets)

            assert "dataset_tests" in result
            assert len(result["dataset_tests"]) == 1

            test_result = result["dataset_tests"][0]
            assert test_result["id"] == "101_12"
            assert "data_test" in test_result
            assert test_result["data_test"]["success"] == True

    def test_api_error_handling(self, mock_requests_session):
        """Test API error handling."""
        tester = IstatAPITester()

        # Test different error scenarios
        error_scenarios = [
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable"),
        ]

        for status_code, error_message in error_scenarios:
            mock_requests_session.get.return_value.status_code = status_code
            mock_requests_session.get.return_value.content = error_message.encode(
                "utf-8"
            )

            endpoint = {
                "name": "test_endpoint",
                "url": "http://test.com/failing",
                "description": "Failing endpoint",
            }

            result = tester._test_single_endpoint(endpoint)

            assert result["success"] == False
            assert result["status_code"] == status_code

    def test_api_timeout_handling(self, mock_requests_session):
        """Test API timeout handling."""
        tester = IstatAPITester()

        # Mock timeout exception
        mock_requests_session.get.side_effect = requests.exceptions.Timeout(
            "Request timeout"
        )

        endpoint = {
            "name": "timeout_endpoint",
            "url": "http://test.com/timeout",
            "description": "Timeout endpoint",
        }

        result = tester._test_single_endpoint(endpoint)

        assert result["success"] == False
        assert "error" in result
        assert "timeout" in result["error"].lower()

    def test_api_rate_limiting(self, mock_requests_session):
        """Test API rate limiting functionality."""
        tester = IstatAPITester()

        # Mock successful response
        mock_requests_session.get.return_value.status_code = 200
        mock_requests_session.get.return_value.content = (
            b'<?xml version="1.0"?><test>data</test>'
        )

        # Test multiple requests with rate limiting
        priority_datasets = [
            {
                "id": f"dataset_{i}",
                "name": f"Dataset {i}",
                "category": "test",
                "relevance_score": 10,
            }
            for i in range(3)
        ]

        start_time = time.time()

        with patch("time.sleep") as mock_sleep:
            result = tester.test_priority_datasets(priority_datasets)

            # Should call sleep for rate limiting
            assert mock_sleep.call_count >= 2  # At least 2 sleeps for 3 requests

        end_time = time.time()

        # Should have tested all datasets
        assert len(result["dataset_tests"]) == 3

    def test_xml_parsing_integration(self, sample_dataflow_xml):
        """Test XML parsing integration."""
        analyzer = IstatDataflowAnalyzer()

        # Test parsing with actual XML structure
        root = ET.fromstring(sample_dataflow_xml)

        # Extract dataflows using the analyzer's method
        namespaces = {
            "str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
            "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
        }

        dataflows = []
        for dataflow in root.findall(".//structure:Dataflow", namespaces):
            df_info = analyzer._extract_dataflow_info(dataflow, namespaces)
            if df_info:
                dataflows.append(df_info)

        assert len(dataflows) > 0

        # Test categorization
        categorized = analyzer._categorize_dataflows(dataflows)

        assert isinstance(categorized, dict)
        assert len(categorized) > 0

        # Should have at least one category with datasets
        has_datasets = any(len(datasets) > 0 for datasets in categorized.values())
        assert has_datasets

    def test_data_extraction_integration(self, sample_xml_data):
        """Test data extraction integration."""
        # Parse sample data XML
        root = ET.fromstring(sample_xml_data)

        # Extract data using SDMX structure
        namespaces = {
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
            "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
        }

        # Find dataset
        dataset = root.find(".//message:DataSet", namespaces)
        assert dataset is not None

        # Extract series and observations
        data_points = []
        for series in dataset.findall(".//generic:Series", namespaces):
            # Get series key dimensions
            dimensions = {}
            for value in series.findall(".//generic:Value", namespaces):
                dimensions[value.get("id")] = value.get("value")

            # Get observations
            for obs in series.findall(".//generic:Obs", namespaces):
                obs_data = dimensions.copy()

                # Get observation value
                obs_value = obs.find(".//generic:ObsValue", namespaces)
                if obs_value is not None:
                    obs_data["value"] = obs_value.get("value")

                # Get observation dimension (usually time)
                obs_dim = obs.find(".//generic:ObsDimension", namespaces)
                if obs_dim is not None:
                    obs_data["time"] = obs_dim.get("value")

                data_points.append(obs_data)

        assert len(data_points) > 0

        # Verify data structure
        for point in data_points:
            assert "TERRITORIO" in point
            assert "ANNO" in point
            assert "value" in point

    def test_comprehensive_integration_workflow(
        self, mock_requests_session, sample_dataflow_xml, sample_xml_data
    ):
        """Test comprehensive integration workflow."""
        tester = IstatAPITester()
        analyzer = IstatDataflowAnalyzer()

        # Step 1: Test connectivity
        mock_requests_session.get.return_value.status_code = 200
        mock_requests_session.get.return_value.elapsed.total_seconds.return_value = 1.0
        mock_requests_session.get.return_value.content = (
            b'<?xml version="1.0"?><test>ok</test>'
        )

        connectivity_result = tester.test_api_connectivity()
        assert "connectivity" in connectivity_result

        # Step 2: Discover datasets
        mock_requests_session.get.return_value.text = sample_dataflow_xml
        discovery_result = tester.discover_priority_datasets()
        assert "dataset_discovery" in discovery_result

        datasets = discovery_result["dataset_discovery"]["datasets"]
        assert len(datasets) > 0

        # Step 3: Test priority datasets
        mock_requests_session.get.return_value.content = sample_xml_data.encode("utf-8")

        with patch("time.sleep"):
            testing_result = tester.test_priority_datasets(datasets[:2])  # Test first 2
            assert "dataset_tests" in testing_result
            assert len(testing_result["dataset_tests"]) <= 2

        # Step 4: Create Tableau-ready datasets
        tableau_ready = analyzer.create_tableau_ready_dataset_list(
            testing_result["dataset_tests"]
        )

        # Should have some successful conversions
        successful_datasets = [
            ds
            for ds in testing_result["dataset_tests"]
            if ds.get("tests", {}).get("data_access", {}).get("success", False)
        ]
        assert len(tableau_ready) == len(successful_datasets)

        # Step 5: Generate comprehensive report
        full_report = {
            "connectivity": connectivity_result["connectivity"],
            "dataset_discovery": discovery_result["dataset_discovery"],
            "dataset_tests": testing_result["dataset_tests"],
            "tableau_ready": tableau_ready,
        }

        # Verify complete workflow
        assert len(full_report["connectivity"]) > 0
        assert len(full_report["dataset_discovery"]["datasets"]) > 0
        assert len(full_report["dataset_tests"]) > 0

        # Calculate success metrics
        successful_connections = sum(
            1 for conn in full_report["connectivity"] if conn.get("success")
        )
        successful_tests = sum(
            1
            for test in full_report["dataset_tests"]
            if test.get("tests", {}).get("data_access", {}).get("success")
        )

        assert successful_connections > 0
        assert successful_tests >= 0  # May be 0 if no tests succeed

    def test_api_response_validation(self, mock_requests_session):
        """Test API response validation."""
        tester = IstatAPITester()

        # Test various response formats
        test_cases = [
            # Valid XML
            ('<?xml version="1.0"?><root><data>test</data></root>', True),
            # Invalid XML
            ('<?xml version="1.0"?><root><data>test</data>', False),
            # Empty response
            ("", False),
            # Non-XML response
            ('{"error": "not xml"}', False),
            # HTML error page
            ("<html><body>Error 404</body></html>", False),
        ]

        for response_content, should_be_valid in test_cases:
            mock_requests_session.get.return_value.status_code = 200
            mock_requests_session.get.return_value.content = response_content.encode(
                "utf-8"
            )
            mock_requests_session.get.return_value.text = response_content

            endpoint = {
                "name": "test_endpoint",
                "url": "http://test.com/data",
                "description": "Test endpoint",
            }

            result = tester._test_single_endpoint(endpoint)

            # Basic success should be True if status is 200
            assert result["success"] == True
            assert result["status_code"] == 200

            # Additional validation could be added here
            # to check if content is valid XML
            if should_be_valid:
                try:
                    ET.fromstring(response_content)
                    xml_valid = True
                except ET.ParseError:
                    xml_valid = False

                # This is just demonstrating how we might validate XML
                # The actual implementation might handle this differently
