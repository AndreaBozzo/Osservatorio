"""
Integration tests for DataflowAnalysisService.

Tests the service with real dependencies and end-to-end workflows
to ensure proper integration with the rest of the system.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.services.dataflow_analysis_service import DataflowAnalysisService
from src.services.legacy_adapter import (
    LegacyDataflowAnalyzerAdapter,
    create_legacy_adapter,
)
from src.services.models import (
    AnalysisFilters,
    BulkAnalysisRequest,
    DataflowCategory,
    DataflowTest,
)
from src.services.service_factory import (
    create_dataflow_analysis_service,
    get_service_container,
)


class TestDataflowServiceIntegration:
    """Integration tests for the complete dataflow analysis system."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_dataflow_xml_file(self, temp_dir):
        """Create sample dataflow XML file for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:StructureSpecificData
            xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
            xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
            xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
            <message:DataSet>
                <str:Dataflow id="DCIS_POPRES1">
                    <com:Name xml:lang="it">Popolazione residente</com:Name>
                    <com:Name xml:lang="en">Resident population</com:Name>
                    <com:Description xml:lang="it">Dati sulla popolazione residente italiana per regioni e province</com:Description>
                </str:Dataflow>
                <str:Dataflow id="DCCN_PILN">
                    <com:Name xml:lang="it">Prodotto interno lordo</com:Name>
                    <com:Name xml:lang="en">Gross domestic product</com:Name>
                    <com:Description xml:lang="it">PIL nazionale e regionale per settori economici</com:Description>
                </str:Dataflow>
                <str:Dataflow id="DCCV_TAXOCCU">
                    <com:Name xml:lang="it">Tasso di occupazione</com:Name>
                    <com:Name xml:lang="en">Employment rate</com:Name>
                    <com:Description xml:lang="it">Tasso occupazione per regioni e fasce età lavoro</com:Description>
                </str:Dataflow>
                <str:Dataflow id="DCIS_SCUOLE">
                    <com:Name xml:lang="it">Scuole e studenti</com:Name>
                    <com:Name xml:lang="en">Schools and students</com:Name>
                    <com:Description xml:lang="it">Statistiche su istruzione scuole università studenti</com:Description>
                </str:Dataflow>
                <str:Dataflow id="MISC_OTHER">
                    <com:Name xml:lang="it">Dati vari</com:Name>
                    <com:Name xml:lang="en">Miscellaneous data</com:Name>
                    <com:Description xml:lang="it">Altri dati statistici vari</com:Description>
                </str:Dataflow>
            </message:DataSet>
        </message:StructureSpecificData>"""

        xml_file = temp_dir / "test_dataflow_response.xml"
        xml_file.write_text(xml_content, encoding="utf-8")
        return xml_file

    # Test service factory and dependency injection

    def test_service_factory_creates_service_with_dependencies(self):
        """Test that service factory creates properly configured service."""
        service = create_dataflow_analysis_service()

        assert isinstance(service, DataflowAnalysisService)
        assert service.istat_client is not None
        assert service.repository is not None
        assert service.temp_file_manager is not None
        assert service.logger is not None

    def test_service_container_initialization(self):
        """Test service container properly initializes all services."""
        from src.services.service_factory import initialize_services

        container = initialize_services()

        assert container is not None
        assert container.has(DataflowAnalysisService)

        # Get service from container
        service = container.get(DataflowAnalysisService)
        assert isinstance(service, DataflowAnalysisService)

    def test_service_container_health_check(self):
        """Test service health check functionality."""
        from src.services.service_factory import check_service_health

        # Mock the health check to avoid real database/API calls
        with patch(
            "src.services.service_factory.get_service_container"
        ) as mock_container:
            mock_container.return_value.has.return_value = True
            mock_container.return_value.get.return_value = Mock()

            result = asyncio.run(check_service_health())

            assert "overall" in result
            assert "services" in result
            assert "timestamp" in result

    # Test end-to-end analysis workflow

    @pytest.mark.asyncio
    async def test_end_to_end_analysis_workflow(self, sample_dataflow_xml_file):
        """Test complete end-to-end analysis workflow."""
        # Create service with mocked external dependencies
        service = create_dataflow_analysis_service()

        # Mock ISTAT client to avoid real API calls
        with patch.object(service, "test_dataflow_access") as mock_test:
            # Mock successful test results
            mock_test.return_value = DataflowTest(
                dataflow_id="test",
                data_access_success=True,
                status_code=200,
                size_bytes=1024,
                observations_count=100,
                parse_error=False,
                sample_file=None,
                error_message=None,
            )

            # Read XML content
            xml_content = sample_dataflow_xml_file.read_text(encoding="utf-8")

            # Run analysis
            filters = AnalysisFilters(include_tests=True, max_results=50)
            result = await service.analyze_dataflows_from_xml(xml_content, filters)

            # Verify results
            assert result.total_analyzed == 5
            assert len(result.categorized_dataflows) > 0

            # Check categorization worked correctly
            assert DataflowCategory.POPOLAZIONE in result.categorized_dataflows
            assert DataflowCategory.ECONOMIA in result.categorized_dataflows
            assert DataflowCategory.LAVORO in result.categorized_dataflows
            assert DataflowCategory.ISTRUZIONE in result.categorized_dataflows

            # Verify population dataflow was categorized correctly
            pop_dataflows = result.categorized_dataflows[DataflowCategory.POPOLAZIONE]
            assert len(pop_dataflows) > 0
            assert any(df.id == "DCIS_POPRES1" for df in pop_dataflows)

            # Verify economy dataflow was categorized correctly
            econ_dataflows = result.categorized_dataflows[DataflowCategory.ECONOMIA]
            assert len(econ_dataflows) > 0
            assert any(df.id == "DCCN_PILN" for df in econ_dataflows)

    @pytest.mark.asyncio
    async def test_categorization_accuracy(self, sample_dataflow_xml_file):
        """Test that categorization is accurate for known dataflows."""
        service = create_dataflow_analysis_service()
        xml_content = sample_dataflow_xml_file.read_text(encoding="utf-8")

        filters = AnalysisFilters(include_tests=False)  # Skip tests for speed
        result = await service.analyze_dataflows_from_xml(xml_content, filters)

        # Build a lookup dict for easier testing
        all_dataflows = {}
        for category, dfs in result.categorized_dataflows.items():
            for df in dfs:
                all_dataflows[df.id] = df

        # Test specific categorizations
        assert all_dataflows["DCIS_POPRES1"].category == DataflowCategory.POPOLAZIONE
        assert all_dataflows["DCCN_PILN"].category == DataflowCategory.ECONOMIA
        assert all_dataflows["DCCV_TAXOCCU"].category == DataflowCategory.LAVORO
        assert all_dataflows["DCIS_SCUOLE"].category == DataflowCategory.ISTRUZIONE

        # Check relevance scores are reasonable
        assert all_dataflows["DCIS_POPRES1"].relevance_score > 0
        assert all_dataflows["DCCN_PILN"].relevance_score > 0

    # Test legacy adapter integration

    def test_legacy_adapter_maintains_compatibility(
        self, sample_dataflow_xml_file, temp_dir
    ):
        """Test that legacy adapter maintains API compatibility."""
        # Change to temp directory for file operations
        import os

        original_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)

            # Copy XML file to expected location
            dataflow_xml = temp_dir / "dataflow_response.xml"
            dataflow_xml.write_text(sample_dataflow_xml_file.read_text())

            # Create legacy adapter
            adapter = create_legacy_adapter()

            # Test legacy API methods work
            categorized = adapter.parse_dataflow_xml("dataflow_response.xml")
            assert isinstance(categorized, dict)
            assert len(categorized) > 0

            # Test top dataflows method
            top_dataflows = adapter.find_top_dataflows_by_category(categorized, top_n=2)
            assert isinstance(top_dataflows, dict)

            # Test that we get expected categories
            assert "popolazione" in categorized
            assert "economia" in categorized

        finally:
            os.chdir(original_cwd)

    def test_legacy_adapter_generates_tableau_files(self, temp_dir):
        """Test that legacy adapter can generate Tableau files."""
        import os

        original_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)

            adapter = create_legacy_adapter()

            # Create sample tested dataflows data
            tested_dataflows = [
                {
                    "id": "DCIS_POPRES1",
                    "name": "Popolazione residente",
                    "category": "popolazione",
                    "relevance_score": 20,
                    "tests": {
                        "data_access": {
                            "success": True,
                            "status_code": 200,
                            "size_bytes": 1024000,
                        },
                        "observations_count": 1000,
                        "sample_file": "sample_DCIS_POPRES1.xml",
                    },
                }
            ]

            # Create Tableau-ready dataset list
            tableau_ready = adapter.create_tableau_ready_dataset_list(tested_dataflows)
            assert len(tableau_ready) == 1

            # Generate implementation guide
            files = adapter.generate_tableau_implementation_guide(tableau_ready)

            # Check files were created
            assert "config_file" in files
            assert "powershell_script" in files
            assert "prep_flow" in files

            # Verify files exist
            if files["config_file"]:
                config_path = Path(files["config_file"])
                assert config_path.exists()

                # Verify JSON content
                config_data = json.loads(config_path.read_text())
                assert "datasets" in config_data
                assert "timestamp" in config_data

        finally:
            os.chdir(original_cwd)

    # Test service context manager

    def test_service_context_manager(self):
        """Test service context manager for lifecycle management."""
        from src.services.service_factory import ServiceContext

        with ServiceContext() as container:
            assert container is not None
            assert container.has(DataflowAnalysisService)

            service = container.get(DataflowAnalysisService)
            assert isinstance(service, DataflowAnalysisService)

        # After context, global container should be cleared
        # (Testing this might be tricky due to global state)

    # Test bulk analysis integration

    @pytest.mark.asyncio
    async def test_bulk_analysis_integration(self):
        """Test bulk analysis with multiple dataflows."""
        service = create_dataflow_analysis_service()

        # Mock the individual test method to avoid real API calls
        with patch.object(service, "test_dataflow_access") as mock_test:
            mock_test.return_value = DataflowTest(
                dataflow_id="test",
                data_access_success=True,
                size_bytes=1024,
                observations_count=100,
                parse_error=False,
            )

            request = BulkAnalysisRequest(
                dataflow_ids=["DF1", "DF2", "DF3", "DF4", "DF5"],
                include_tests=True,
                max_concurrent=3,
            )

            results = await service.bulk_analyze(request)

            assert len(results) == 5
            assert all(result.tableau_ready for result in results)

            # Verify concurrent execution worked (all should be tested)
            assert mock_test.call_count == 5

    # Test error handling and resilience

    @pytest.mark.asyncio
    async def test_service_handles_invalid_xml_gracefully(self):
        """Test service handles invalid XML input gracefully."""
        service = create_dataflow_analysis_service()

        invalid_xml = "This is not valid XML content"

        with pytest.raises(Exception):
            await service.analyze_dataflows_from_xml(invalid_xml)

    @pytest.mark.asyncio
    async def test_service_handles_empty_xml_gracefully(self):
        """Test service handles empty XML gracefully."""
        service = create_dataflow_analysis_service()

        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <message:StructureSpecificData
            xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
            <message:DataSet>
            </message:DataSet>
        </message:StructureSpecificData>"""

        result = await service.analyze_dataflows_from_xml(empty_xml)

        assert result.total_analyzed == 0
        assert all(len(dfs) == 0 for dfs in result.categorized_dataflows.values())

    # Test performance and scalability

    @pytest.mark.asyncio
    async def test_analysis_performance_with_many_dataflows(self):
        """Test analysis performance with many dataflows."""
        # Create XML with many dataflows
        dataflows_xml = []
        for i in range(50):  # Test with 50 dataflows
            dataflows_xml.append(
                f"""
                <str:Dataflow id="DF_{i:03d}">
                    <com:Name xml:lang="it">Dataflow {i}</com:Name>
                    <com:Description xml:lang="it">Test dataflow numero {i}</com:Description>
                </str:Dataflow>
            """
            )

        large_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <message:StructureSpecificData
            xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
            xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
            xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
            <message:DataSet>
                {''.join(dataflows_xml)}
            </message:DataSet>
        </message:StructureSpecificData>"""

        service = create_dataflow_analysis_service()

        import time

        start_time = time.time()

        filters = AnalysisFilters(include_tests=False, max_results=100)
        result = await service.analyze_dataflows_from_xml(large_xml, filters)

        end_time = time.time()
        duration = end_time - start_time

        # Performance assertions
        assert result.total_analyzed == 50
        assert duration < 10.0  # Should complete within 10 seconds
        assert "analysis_duration_seconds" in result.performance_metrics

        # Verify performance metrics are recorded
        recorded_duration = result.performance_metrics["analysis_duration_seconds"]
        assert recorded_duration > 0
        assert recorded_duration < 10.0

    # Test configuration and customization

    @pytest.mark.asyncio
    async def test_custom_categorization_rules(self):
        """Test that custom categorization rules work correctly."""
        service = create_dataflow_analysis_service()

        # Test custom dataflow with specific keywords
        test_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <message:StructureSpecificData
            xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
            xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
            xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
            <message:DataSet>
                <str:Dataflow id="HEALTH_TEST">
                    <com:Name xml:lang="it">Dati sanitari</com:Name>
                    <com:Description xml:lang="it">Statistiche ospedale e salute pubblica</com:Description>
                </str:Dataflow>
            </message:DataSet>
        </message:StructureSpecificData>"""

        result = await service.analyze_dataflows_from_xml(test_xml)

        # Should categorize as health based on keywords "sanitari", "ospedale", "salute"
        health_dataflows = result.categorized_dataflows[DataflowCategory.SALUTE]
        assert len(health_dataflows) > 0
        assert health_dataflows[0].id == "HEALTH_TEST"
        assert health_dataflows[0].relevance_score > 0

    # Test logging and monitoring

    @pytest.mark.asyncio
    async def test_service_logging_integration(self, capsys):
        """Test that service logging works correctly."""
        service = create_dataflow_analysis_service()

        simple_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <DataSet>
            <Dataflow id="LOG_TEST">
                <Name>Test Logging</Name>
            </Dataflow>
        </DataSet>"""

        # Run analysis
        await service.analyze_dataflows_from_xml(simple_xml)

        # Capture stdout/stderr (where loguru outputs)
        captured = capsys.readouterr()
        output = captured.out + captured.err

        # Check that log messages were generated
        assert "Starting dataflow analysis" in output
        assert "Analysis completed" in output
        assert service is not None  # Verify service was created
