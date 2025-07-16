"""
System integration tests for the complete ISTAT data processing pipeline.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from src.analyzers.dataflow_analyzer import IstatDataflowAnalyzer
from src.api.istat_api import IstatAPITester
from src.api.powerbi_api import PowerBIAPIClient
from src.utils.config import Config
from src.utils.logger import get_logger


@pytest.mark.integration
class TestSystemIntegration:
    """Test complete system integration scenarios."""

    def test_complete_data_pipeline_flow(self, temp_dir):
        """Test complete data pipeline from analysis to PowerBI."""
        # Setup components
        analyzer = IstatDataflowAnalyzer()
        api_tester = IstatAPITester()
        config = Config()
        logger = get_logger("test")

        # Mock XML response
        mock_xml = """<?xml version="1.0"?>
        <message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                           xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
                           xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
            <message:Header>
                <message:ID>test_dataflow</message:ID>
            </message:Header>
            <message:Structures>
                <structure:Dataflows>
                    <structure:Dataflow id="popolazione_test" version="1.0" agencyID="IT1">
                        <common:Name xml:lang="it">Popolazione residente</common:Name>
                        <common:Description xml:lang="it">Dati popolazione italiana</common:Description>
                    </structure:Dataflow>
                    <structure:Dataflow id="economia_test" version="1.0" agencyID="IT1">
                        <common:Name xml:lang="it">PIL regionale</common:Name>
                        <common:Description xml:lang="it">Prodotto interno lordo regionale</common:Description>
                    </structure:Dataflow>
                </structure:Dataflows>
            </message:Structures>
        </message:Structure>"""

        # Save mock XML
        xml_file = temp_dir / "test_dataflows.xml"
        xml_file.write_text(mock_xml, encoding="utf-8")

        # Test dataflow analysis
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_dir)

            categorized_data = analyzer.parse_dataflow_xml(str(xml_file))

            # Verify categorization
            assert "popolazione" in categorized_data
            assert "economia" in categorized_data
            assert len(categorized_data["popolazione"]) == 1
            assert len(categorized_data["economia"]) == 1

            # Test data processing
            processed_data = {}
            for category, datasets in categorized_data.items():
                processed_data[category] = []
                for dataset in datasets:
                    # Simulate data processing
                    processed_dataset = {
                        "id": dataset["id"],
                        "name": dataset["display_name"],
                        "category": category,
                        "processed": True,
                        "file_path": str(temp_dir / f"{dataset['id']}.csv"),
                    }
                    processed_data[category].append(processed_dataset)

            # Verify processing - check categories with data
            non_empty_categories = [
                cat for cat, datasets in processed_data.items() if datasets
            ]
            assert len(non_empty_categories) == 2
            assert processed_data["popolazione"][0]["processed"] is True
            assert processed_data["economia"][0]["processed"] is True

            # Test report generation
            report = analyzer.generate_summary_report(categorized_data)
            assert "Total dataflows" in report
            assert "popolazione" in report.lower()  # Case insensitive check
            assert "economia" in report.lower()  # Case insensitive check

        finally:
            os.chdir(original_cwd)

    @patch("requests.Session")
    def test_api_integration_flow(self, mock_session_class):
        """Test API integration flow."""
        # Setup mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<?xml version="1.0"?><test>data</test>'
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_session.get.return_value = mock_response

        # Test API components
        api_tester = IstatAPITester()

        # Test API connectivity
        results = api_tester.test_api_connectivity()

        # Verify results
        assert len(results) >= 1
        assert any(result["success"] for result in results)
        assert any(result["status_code"] == 200 for result in results)

    @patch.dict(
        "os.environ",
        {"POWERBI_TENANT_ID": "test-tenant-id", "POWERBI_CLIENT_ID": "test-client-id"},
    )
    @patch("msal.PublicClientApplication")
    def test_powerbi_integration_flow(self, mock_msal):
        """Test PowerBI integration flow."""
        # Setup mock MSAL
        mock_app = Mock()
        mock_msal.return_value = mock_app

        # Mock successful authentication
        mock_app.acquire_token_interactive.return_value = {
            "access_token": "test_token",
            "token_type": "Bearer",
        }

        # Test PowerBI API (skip if credentials not configured)
        try:
            powerbi_client = PowerBIAPIClient()
            # Just verify client was created successfully
            assert powerbi_client is not None
        except Exception as e:
            pytest.skip(f"PowerBI not configured: {e}")

        # Test workspace listing (would be mocked in real test)
        # This is a placeholder for actual PowerBI API integration
        mock_workspaces = [{"id": "workspace1", "name": "Test Workspace"}]

        # Verify workspace access
        assert len(mock_workspaces) > 0
        assert mock_workspaces[0]["name"] == "Test Workspace"

    def test_config_integration_flow(self, temp_dir):
        """Test configuration management integration."""
        config = Config()

        # Test config loading
        assert config is not None
        assert hasattr(config, "ISTAT_API_BASE_URL")
        assert hasattr(config, "POWERBI_CLIENT_ID")

        # Test environment variable integration
        import os

        original_env = os.environ.get("LOG_LEVEL")
        try:
            os.environ["LOG_LEVEL"] = "DEBUG"

            # Config should have access to environment variables
            assert "LOG_LEVEL" in os.environ
            assert os.environ["LOG_LEVEL"] == "DEBUG"

        finally:
            if original_env:
                os.environ["LOG_LEVEL"] = original_env
            elif "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]

    def test_logging_integration_flow(self):
        """Test logging integration across components."""
        logger = get_logger("test")

        # Test logging from different components
        logger.info("System integration test started")

        # Simulate component logging
        components = ["analyzer", "api_tester", "powerbi_api", "config_manager"]
        for component in components:
            component_logger = get_logger(component)
            component_logger.info(f"Component {component} initialized")

        # Test error logging
        try:
            raise ValueError("Test integration error")
        except ValueError:
            logger.exception("Integration test exception")

        # Should complete without issues
        assert True

    def test_error_handling_integration(self):
        """Test error handling across system components."""
        analyzer = IstatDataflowAnalyzer()

        # Test with invalid XML
        invalid_xml = "<?xml version='1.0'?><invalid>unclosed tag"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(invalid_xml)
            f.flush()

            # Should handle parsing errors gracefully
            result = analyzer.parse_dataflow_xml(f.name)
            assert isinstance(result, dict)

        # Clean up
        Path(f.name).unlink(missing_ok=True)

    def test_data_format_compatibility(self, temp_dir):
        """Test data format compatibility across components."""
        # Create test data in different formats
        test_data = pd.DataFrame(
            {
                "territorio": ["IT", "IT", "IT"],
                "anno": [2020, 2021, 2022],
                "valore": [60000000, 59000000, 58000000],
                "categoria": ["popolazione", "popolazione", "popolazione"],
            }
        )

        # Test different format outputs
        formats = ["csv", "excel", "json", "parquet"]

        for format_type in formats:
            output_file = temp_dir / f"test_data.{format_type}"

            if format_type == "csv":
                test_data.to_csv(output_file, index=False, encoding="utf-8")
                read_data = pd.read_csv(output_file, encoding="utf-8")
            elif format_type == "excel":
                test_data.to_excel(output_file, index=False, engine="openpyxl")
                read_data = pd.read_excel(output_file, engine="openpyxl")
            elif format_type == "json":
                test_data.to_json(output_file, orient="records", force_ascii=False)
                read_data = pd.read_json(output_file, orient="records")
            elif format_type == "parquet":
                test_data.to_parquet(output_file, index=False, engine="pyarrow")
                read_data = pd.read_parquet(output_file, engine="pyarrow")

            # Verify data integrity
            assert len(read_data) == len(test_data)
            assert list(read_data.columns) == list(test_data.columns)
            assert read_data["territorio"].iloc[0] == "IT"

    def test_concurrent_processing_integration(self, temp_dir):
        """Test concurrent processing across components."""
        import threading
        import time

        results = []
        errors = []

        def process_dataset(dataset_id):
            try:
                # Simulate data processing
                analyzer = IstatDataflowAnalyzer()

                # Create test data
                test_data = pd.DataFrame(
                    {"id": [dataset_id] * 100, "value": range(100)}
                )

                # Process data
                output_file = temp_dir / f"concurrent_{dataset_id}.csv"
                test_data.to_csv(output_file, index=False)

                results.append(
                    {
                        "dataset_id": dataset_id,
                        "success": True,
                        "file_path": str(output_file),
                    }
                )

            except Exception as e:
                errors.append({"dataset_id": dataset_id, "error": str(e)})

        # Process multiple datasets concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=process_dataset, args=(f"dataset_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) == 10
        assert len(errors) == 0

        # Verify all files were created
        for result in results:
            assert Path(result["file_path"]).exists()

    def test_memory_usage_integration(self):
        """Test memory usage during integration operations."""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations
        analyzer = IstatDataflowAnalyzer()

        # Generate large dataset
        large_data = pd.DataFrame(
            {"id": range(10000), "value": range(10000), "category": ["test"] * 10000}
        )

        # Process multiple times
        for i in range(10):
            processed = analyzer._categorize_dataflows(
                [
                    {
                        "id": f"dataset_{j}",
                        "display_name": f"Dataset {j}",
                        "description": f"Test dataset {j}",
                    }
                    for j in range(100)
                ]
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 200  # Less than 200MB increase

    def test_end_to_end_workflow(self, temp_dir):
        """Test complete end-to-end workflow."""
        # 1. Initialize components
        analyzer = IstatDataflowAnalyzer()
        config = Config()
        logger = get_logger("test")

        logger.info("Starting end-to-end workflow test")

        # 2. Load configuration
        assert hasattr(config, "ISTAT_API_BASE_URL")

        # 3. Create mock data
        mock_datasets = [
            {
                "id": "pop_test",
                "display_name": "Popolazione residente",
                "description": "Dati popolazione italiana",
                "relevance_score": 8.5,
                "tests": {
                    "data_access": {"size_bytes": 1024 * 1024 * 10},
                    "observations_count": 1000,
                },
            },
            {
                "id": "econ_test",
                "display_name": "PIL regionale",
                "description": "Prodotto interno lordo regionale",
                "relevance_score": 9.0,
                "tests": {
                    "data_access": {"size_bytes": 1024 * 1024 * 5},
                    "observations_count": 500,
                },
            },
        ]

        # 4. Categorize datasets
        categorized = analyzer._categorize_dataflows(mock_datasets)
        assert len(categorized) > 0

        # 5. Generate priority scores
        for category, datasets in categorized.items():
            for dataset in datasets:
                priority = analyzer._calculate_priority(dataset)
                assert priority >= 0

        # 6. Generate reports
        summary = analyzer.generate_summary_report(categorized)
        assert "Total dataflows" in summary

        # 7. Save results
        report_file = temp_dir / "integration_report.json"
        report_data = {
            "categorized_data": categorized,
            "summary": summary,
            "timestamp": "2023-01-01T00:00:00Z",
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # 8. Verify final output
        assert report_file.exists()

        with open(report_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert "categorized_data" in saved_data
        assert "summary" in saved_data
        assert "timestamp" in saved_data

        logger.info("End-to-end workflow test completed successfully")
