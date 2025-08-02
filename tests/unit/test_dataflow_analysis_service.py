"""
Unit tests for DataflowAnalysisService.

Tests the modern dataflow analysis service with proper mocking
of dependencies and comprehensive coverage of all functionality.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.services.dataflow_analysis_service import DataflowAnalysisService
from src.services.models import (
    AnalysisFilters,
    AnalysisResult,
    BulkAnalysisRequest,
    CategorizationRule,
    DataflowCategory,
    DataflowTest,
    DataflowTestResult,
    IstatDataflow,
)


class TestDataflowAnalysisService:
    """Test suite for DataflowAnalysisService."""

    @pytest.fixture
    def mock_istat_client(self):
        """Mock ProductionIstatClient."""
        client = Mock()
        client.fetch_dataset = Mock()
        client.get_status = Mock(return_value={"status": "healthy"})
        return client

    @pytest.fixture
    def mock_repository(self):
        """Mock UnifiedDataRepository."""
        repo = Mock()
        repo.get_system_status = Mock(return_value={"status": "healthy"})
        return repo

    @pytest.fixture
    def mock_temp_manager(self):
        """Mock TempFileManager."""
        manager = Mock()
        manager.get_temp_path = Mock(return_value="/tmp/test_file.xml")
        manager.cleanup = Mock()
        return manager

    @pytest.fixture
    def service(self, mock_istat_client, mock_repository, mock_temp_manager):
        """Create DataflowAnalysisService with mocked dependencies."""
        return DataflowAnalysisService(
            istat_client=mock_istat_client,
            repository=mock_repository,
            temp_file_manager=mock_temp_manager,
        )

    @pytest.fixture
    def sample_xml_content(self):
        """Sample ISTAT dataflow XML content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <message:StructureSpecificData
            xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
            xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
            xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
            <message:DataSet>
                <str:Dataflow id="DCIS_POPRES1">
                    <com:Name xml:lang="it">Popolazione residente</com:Name>
                    <com:Name xml:lang="en">Resident population</com:Name>
                    <com:Description xml:lang="it">Dati sulla popolazione residente italiana</com:Description>
                </str:Dataflow>
                <str:Dataflow id="DCCN_PILN">
                    <com:Name xml:lang="it">PIL nazionale</com:Name>
                    <com:Name xml:lang="en">National GDP</com:Name>
                    <com:Description xml:lang="it">Prodotto interno lordo nazionale</com:Description>
                </str:Dataflow>
            </message:DataSet>
        </message:StructureSpecificData>"""

    @pytest.fixture
    def sample_dataflows(self):
        """Sample dataflow objects for testing."""
        return [
            IstatDataflow(
                id="DCIS_POPRES1",
                name_it="Popolazione residente",
                name_en="Resident population",
                display_name="Popolazione residente",
                description="Dati sulla popolazione residente italiana",
                category=DataflowCategory.POPOLAZIONE,
                relevance_score=20,
            ),
            IstatDataflow(
                id="DCCN_PILN",
                name_it="PIL nazionale",
                name_en="National GDP",
                display_name="PIL nazionale",
                description="Prodotto interno lordo nazionale",
                category=DataflowCategory.ECONOMIA,
                relevance_score=18,
            ),
        ]

    # Test initialization

    def test_service_initialization(self, service):
        """Test service initializes correctly with dependencies."""
        assert service.istat_client is not None
        assert service.repository is not None
        assert service.temp_file_manager is not None
        assert service.logger is not None
        assert service._categorization_rules is None  # Should be lazy loaded

    # Test XML parsing

    @pytest.mark.asyncio
    async def test_parse_dataflow_xml_with_namespaces(
        self, service, sample_xml_content
    ):
        """Test XML parsing with proper SDMX namespaces."""
        dataflows = await service._parse_dataflow_xml(sample_xml_content)

        assert len(dataflows) == 2

        # Check first dataflow
        df1 = dataflows[0]
        assert df1.id == "DCIS_POPRES1"
        assert df1.name_it == "Popolazione residente"
        assert df1.name_en == "Resident population"
        assert df1.description == "Dati sulla popolazione residente italiana"

        # Check second dataflow
        df2 = dataflows[1]
        assert df2.id == "DCCN_PILN"
        assert df2.name_it == "PIL nazionale"
        assert df2.name_en == "National GDP"

    @pytest.mark.asyncio
    async def test_parse_dataflow_xml_without_namespaces(self, service):
        """Test XML parsing fallback without namespaces."""
        xml_without_ns = """<?xml version="1.0" encoding="UTF-8"?>
        <DataSet>
            <Dataflow id="TEST_DF">
                <Name lang="it">Test Dataflow</Name>
                <Description>Test description</Description>
            </Dataflow>
        </DataSet>"""

        dataflows = await service._parse_dataflow_xml(xml_without_ns)

        assert len(dataflows) == 1
        assert dataflows[0].id == "TEST_DF"
        assert dataflows[0].name_it == "Test Dataflow"

    @pytest.mark.asyncio
    async def test_parse_invalid_xml(self, service):
        """Test handling of invalid XML content."""
        invalid_xml = "This is not XML content"

        with pytest.raises(Exception):  # Should raise ParseError
            await service._parse_dataflow_xml(invalid_xml)

    # Test categorization

    @pytest.mark.asyncio
    async def test_categorize_single_dataflow_population(self, service):
        """Test categorization of population dataflow."""
        dataflow = IstatDataflow(
            id="DCIS_POPRES1",
            display_name="Popolazione residente",
            description="Dati demografici popolazione italiana",
        )

        result = await service.categorize_single_dataflow(dataflow)

        assert result.category == DataflowCategory.POPOLAZIONE
        assert result.relevance_score > 0
        assert "popolazione" in result.matched_keywords
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_categorize_single_dataflow_economy(self, service):
        """Test categorization of economic dataflow."""
        dataflow = IstatDataflow(
            id="DCCN_PILN",
            display_name="PIL nazionale",
            description="Prodotto interno lordo economia italiana",
        )

        result = await service.categorize_single_dataflow(dataflow)

        assert result.category == DataflowCategory.ECONOMIA
        assert result.relevance_score > 0
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_categorize_single_dataflow_unknown(self, service):
        """Test categorization of unknown dataflow falls back to 'altri'."""
        dataflow = IstatDataflow(
            id="UNKNOWN_DF",
            display_name="Some random dataflow",
            description="No relevant keywords here",
        )

        result = await service.categorize_single_dataflow(dataflow)

        assert result.category == DataflowCategory.ALTRI
        assert result.relevance_score == 0
        assert len(result.matched_keywords) == 0
        assert result.confidence == 0.0

    # Test dataflow testing

    @pytest.mark.asyncio
    async def test_test_dataflow_access_success(
        self, mock_repository, mock_temp_manager
    ):
        """Test successful dataflow access testing."""
        # Mock successful API response
        mock_response_data = """<?xml version="1.0"?>
        <Data>
            <Obs value="1000"/>
            <Obs value="2000"/>
            <Obs value="3000"/>
        </Data>"""

        # Create a simple mock client that works properly
        mock_client = Mock()
        mock_client.fetch_dataset.return_value = {
            "success": True,
            "data": mock_response_data,
            "dataset_id": "DCIS_POPRES1",
        }

        # Create service with the proper mock
        service = DataflowAnalysisService(
            istat_client=mock_client,
            repository=mock_repository,
            temp_file_manager=mock_temp_manager,
        )

        result = await service.test_dataflow_access("DCIS_POPRES1", save_sample=False)

        assert result.dataflow_id == "DCIS_POPRES1"
        assert result.data_access_success is True
        assert result.status_code == 200
        assert result.size_bytes > 0
        assert result.observations_count == 3
        assert result.parse_error is False
        assert result.is_successful is True

    @pytest.mark.asyncio
    async def test_test_dataflow_access_with_sample_save(
        self, service, mock_istat_client
    ):
        """Test dataflow access testing with sample saving."""
        mock_response_data = '<Data><Obs value="1000"/></Data>'
        mock_istat_client.fetch_dataset.return_value = {
            "success": True,
            "data": mock_response_data,
            "dataset_id": "TEST_DF",
        }

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = await service.test_dataflow_access("TEST_DF", save_sample=True)

            assert result.sample_file is not None
            mock_open.assert_called_once()
            mock_file.write.assert_called_once_with(mock_response_data)

    @pytest.mark.asyncio
    async def test_test_dataflow_access_parse_error(self, service, mock_istat_client):
        """Test handling of XML parse errors during testing."""
        # Mock response with invalid XML
        mock_istat_client.fetch_dataset.return_value = {
            "success": True,
            "data": "Invalid XML content",
            "dataset_id": "BAD_DF",
        }

        result = await service.test_dataflow_access("BAD_DF")

        assert result.dataflow_id == "BAD_DF"
        assert result.data_access_success is True  # API call succeeded
        assert result.parse_error is True  # But parsing failed
        assert result.is_successful is False  # Overall test failed
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_test_dataflow_access_api_error(self, service, mock_istat_client):
        """Test handling of API errors during testing."""
        # Mock API client to raise exception
        mock_istat_client.fetch_dataset.side_effect = Exception("API Error")

        result = await service.test_dataflow_access("ERROR_DF")

        assert result.dataflow_id == "ERROR_DF"
        assert result.data_access_success is False
        assert result.error_message == "API Error"
        assert result.is_successful is False

    # Test complete analysis workflow

    @pytest.mark.asyncio
    async def test_analyze_dataflows_from_xml_complete_workflow(
        self, service, sample_xml_content, mock_istat_client
    ):
        """Test complete analysis workflow from XML."""
        # Mock successful API responses for testing
        mock_istat_client.fetch_dataset.return_value = {
            "success": True,
            "data": '<Data><Obs value="1000"/></Data>',
            "dataset_id": "test",
        }

        filters = AnalysisFilters(include_tests=True, max_results=10)
        result = await service.analyze_dataflows_from_xml(sample_xml_content, filters)

        assert isinstance(result, AnalysisResult)
        assert result.total_analyzed == 2
        assert len(result.categorized_dataflows) > 0
        assert len(result.test_results) > 0
        assert result.tableau_ready_count >= 0
        assert "analysis_duration_seconds" in result.performance_metrics

    @pytest.mark.asyncio
    async def test_analyze_dataflows_with_category_filter(
        self, service, sample_xml_content
    ):
        """Test analysis with category filtering."""
        filters = AnalysisFilters(
            categories=[DataflowCategory.POPOLAZIONE], include_tests=False
        )

        result = await service.analyze_dataflows_from_xml(sample_xml_content, filters)

        # Should only include population dataflows
        for category, dataflows in result.categorized_dataflows.items():
            if dataflows:  # If category has dataflows
                assert category == DataflowCategory.POPOLAZIONE

    @pytest.mark.asyncio
    async def test_analyze_dataflows_with_relevance_filter(
        self, service, sample_xml_content
    ):
        """Test analysis with relevance score filtering."""
        filters = AnalysisFilters(
            min_relevance_score=15,
            include_tests=False,  # High threshold
        )

        result = await service.analyze_dataflows_from_xml(sample_xml_content, filters)

        # Check that all returned dataflows meet the threshold
        for dataflows in result.categorized_dataflows.values():
            for df in dataflows:
                assert df.relevance_score >= 15

    # Test bulk analysis

    @pytest.mark.asyncio
    async def test_bulk_analyze(self, service, mock_istat_client):
        """Test bulk analysis of multiple dataflows."""
        # Mock API responses
        mock_istat_client.fetch_dataset.return_value = {
            "success": True,
            "data": '<Data><Obs value="1000"/></Data>',
            "dataset_id": "test",
        }

        request = BulkAnalysisRequest(
            dataflow_ids=["DF1", "DF2", "DF3"], include_tests=True, max_concurrent=2
        )

        results = await service.bulk_analyze(request)

        assert len(results) == 3
        for result in results:
            assert isinstance(result, DataflowTestResult)
            assert result.dataflow.id in ["DF1", "DF2", "DF3"]

    @pytest.mark.asyncio
    async def test_bulk_analyze_without_tests(self, service):
        """Test bulk analysis without running tests."""
        request = BulkAnalysisRequest(dataflow_ids=["DF1", "DF2"], include_tests=False)

        results = await service.bulk_analyze(request)

        assert len(results) == 2
        for result in results:
            # Tests should have default values when not run
            assert result.test.data_access_success is False
            assert result.test.observations_count == 0

    # Test error handling

    @pytest.mark.asyncio
    async def test_analyze_dataflows_handles_exceptions(self, service):
        """Test that analysis handles exceptions gracefully."""
        invalid_xml = "Not XML"

        with pytest.raises(Exception):
            await service.analyze_dataflows_from_xml(invalid_xml)

    # Test caching behavior

    @pytest.mark.asyncio
    async def test_categorization_rules_caching(self, service):
        """Test that categorization rules are cached properly."""
        # First call should load rules
        rules1 = await service._get_categorization_rules()
        assert len(rules1) > 0
        assert service._categorization_rules is not None
        assert service._rules_cache_time is not None

        # Second call should use cache
        rules2 = await service._get_categorization_rules()
        assert rules1 == rules2  # Should be same instance

    # Test helper methods

    def test_extract_dataflow_info_complete(self, service):
        """Test dataflow info extraction with complete data."""
        from xml.etree.ElementTree import fromstring

        xml_elem = fromstring(
            """
        <Dataflow id="TEST_DF">
            <Name xml:lang="it">Nome Italiano</Name>
            <Name xml:lang="en">English Name</Name>
            <Description xml:lang="it">Descrizione test</Description>
        </Dataflow>
        """
        )

        result = service._extract_dataflow_info(xml_elem, {})

        assert result is not None
        assert result.id == "TEST_DF"
        assert result.name_it == "Nome Italiano"
        assert result.name_en == "English Name"
        assert result.description == "Descrizione test"

    def test_extract_dataflow_info_minimal(self, service):
        """Test dataflow info extraction with minimal data."""
        from xml.etree.ElementTree import fromstring

        xml_elem = fromstring('<Dataflow id="MINIMAL_DF"></Dataflow>')

        result = service._extract_dataflow_info(xml_elem, {})

        assert result is not None
        assert result.id == "MINIMAL_DF"
        assert result.display_name == "MINIMAL_DF"  # Should fallback to ID

    def test_extract_dataflow_info_no_id(self, service):
        """Test that dataflow without ID returns None."""
        from xml.etree.ElementTree import fromstring

        xml_elem = fromstring("<Dataflow><Name>Test</Name></Dataflow>")

        result = service._extract_dataflow_info(xml_elem, {})

        assert result is None  # Should return None for missing ID

    # Test analysis result methods

    def test_analysis_result_get_top_by_category(self):
        """Test getting top dataflows by category."""
        dataflows = [
            IstatDataflow(id="DF1", display_name="DF1", relevance_score=10),
            IstatDataflow(id="DF2", display_name="DF2", relevance_score=20),
            IstatDataflow(id="DF3", display_name="DF3", relevance_score=15),
        ]

        result = AnalysisResult(
            total_analyzed=3,
            categorized_dataflows={DataflowCategory.POPOLAZIONE: dataflows},
        )

        top_dataflows = result.get_top_by_category(
            DataflowCategory.POPOLAZIONE, limit=2
        )

        assert len(top_dataflows) == 2
        assert top_dataflows[0].id == "DF2"  # Highest score first
        assert top_dataflows[1].id == "DF3"  # Second highest

    def test_analysis_result_get_summary_stats(self):
        """Test getting summary statistics."""
        # Create test results to drive the tableau_ready_count calculation
        test_results = [
            DataflowTestResult(
                dataflow=IstatDataflow(id="POP1", name_it="Popolazione 1"),
                test=DataflowTest(dataflow_id="POP1", data_access_success=True),
                tableau_ready=True,
            ),
            DataflowTestResult(
                dataflow=IstatDataflow(id="ECO1", name_it="Economia 1"),
                test=DataflowTest(dataflow_id="ECO1", data_access_success=True),
                tableau_ready=True,
            ),
        ]

        result = AnalysisResult(
            total_analyzed=5,
            categorized_dataflows={
                DataflowCategory.POPOLAZIONE: [
                    IstatDataflow(id="POP1", name_it="Popolazione 1"),
                    IstatDataflow(id="POP2", name_it="Popolazione 2"),
                ],
                DataflowCategory.ECONOMIA: [
                    IstatDataflow(id="ECO1", name_it="Economia 1")
                ],
            },
            test_results=test_results,
        )

        stats = result.get_summary_stats()

        assert stats["total_dataflows"] == 5
        assert stats["popolazione_count"] == 2
        assert stats["economia_count"] == 1
        assert stats["tableau_ready"] == 2

    # Test model validation

    def test_dataflow_model_display_name_validation(self):
        """Test that display_name is set correctly from available names."""
        # Test with Italian name
        df1 = IstatDataflow(id="DF1", name_it="Nome Italiano", name_en="English Name")
        assert df1.display_name == "Nome Italiano"

        # Test with only English name
        df2 = IstatDataflow(id="DF2", name_en="English Only")
        assert df2.display_name == "English Only"

        # Test fallback to ID
        df3 = IstatDataflow(id="DF3")
        assert df3.display_name == "DF3"

    def test_test_result_model_validation(self):
        """Test DataflowTestResult model field validation."""
        dataflow = IstatDataflow(
            id="DF1", display_name="Test DF", category=DataflowCategory.POPOLAZIONE
        )

        test = DataflowTest(
            dataflow_id="DF1",
            data_access_success=True,
            size_bytes=1024000,  # 1MB
            observations_count=500,
        )

        result = DataflowTestResult(dataflow=dataflow, test=test)

        assert result.tableau_ready is True  # Should be True for successful test
        assert result.suggested_connection.value == "direct_connection"  # Small file
        assert result.suggested_refresh.value == "monthly"  # Population category
        assert result.priority > 0  # Should calculate priority

    # Test categorization rules

    def test_categorization_rule_validation(self):
        """Test CategorizationRule model validation."""
        rule = CategorizationRule(
            category=DataflowCategory.POPOLAZIONE,
            keywords=["POPOLAZIONE", " residente ", "DEMO "],  # Mixed case with spaces
            priority=10,
        )

        # Keywords should be normalized to lowercase and stripped
        assert "popolazione" in rule.keywords
        assert "residente" in rule.keywords
        assert "demo" in rule.keywords
        assert all(kw == kw.lower().strip() for kw in rule.keywords)

    def test_analysis_filters_validation(self):
        """Test AnalysisFilters model validation."""
        # Test max_results bounds
        filters1 = AnalysisFilters(max_results=0)
        assert filters1.max_results == 1  # Should be clamped to minimum

        filters2 = AnalysisFilters(max_results=2000)
        assert filters2.max_results == 1000  # Should be clamped to maximum

    # Database Integration Tests for Categorization Rules

    @pytest.mark.asyncio
    async def test_get_categorization_rules_from_database(self, service):
        """Test loading categorization rules from database."""
        # Mock repository to return sample rules
        sample_rules = [
            {
                "rule_id": "test_rule",
                "category": "popolazione",
                "keywords": ["test", "popolazione"],
                "priority": 10,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        ]
        service.repository.get_categorization_rules = MagicMock(
            return_value=sample_rules
        )

        # Clear cache to force database load
        service._categorization_rules = None
        service._rules_cache_time = None

        rules = await service._get_categorization_rules()

        assert len(rules) == 1
        assert rules[0].id == "test_rule"
        assert rules[0].category == DataflowCategory.POPOLAZIONE
        assert "test" in rules[0].keywords
        service.repository.get_categorization_rules.assert_called_once_with(
            active_only=True
        )

    @pytest.mark.asyncio
    async def test_categorization_rules_cache(self, service):
        """Test categorization rules caching mechanism."""
        # Mock repository
        service.repository.get_categorization_rules = MagicMock(return_value=[])

        # First call should hit database
        await service._get_categorization_rules()
        assert service.repository.get_categorization_rules.call_count == 1

        # Second call should use cache
        await service._get_categorization_rules()
        assert service.repository.get_categorization_rules.call_count == 1  # Still 1

        # Clear cache and call again should hit database
        service._categorization_rules = None
        service._rules_cache_time = None
        await service._get_categorization_rules()
        assert service.repository.get_categorization_rules.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_rules_on_database_error(self, service):
        """Test fallback to hardcoded rules when database fails."""
        # Mock repository to raise exception
        service.repository.get_categorization_rules = MagicMock(
            side_effect=Exception("Database error")
        )

        # Clear cache to force database load
        service._categorization_rules = None
        service._rules_cache_time = None

        rules = await service._get_categorization_rules()

        # Should return fallback rules
        assert len(rules) > 0
        assert all(isinstance(rule.category, DataflowCategory) for rule in rules)
        service.repository.get_categorization_rules.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_category_in_database_rule(self, service):
        """Test handling of invalid category in database rules."""
        # Mock repository to return rule with invalid category
        sample_rules = [
            {
                "rule_id": "valid_rule",
                "category": "popolazione",
                "keywords": ["test"],
                "priority": 10,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
            {
                "rule_id": "invalid_rule",
                "category": "invalid_category",
                "keywords": ["test"],
                "priority": 5,
                "is_active": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        ]
        service.repository.get_categorization_rules = MagicMock(
            return_value=sample_rules
        )

        # Clear cache
        service._categorization_rules = None
        service._rules_cache_time = None

        rules = await service._get_categorization_rules()

        # Should only include valid rule
        assert len(rules) == 1
        assert rules[0].id == "valid_rule"
