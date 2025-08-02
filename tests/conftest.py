"""
Test configuration and fixtures for osservatorio scuola tests.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

try:
    from osservatorio_istat.utils.config import Config
except ImportError:
    # Development mode fallback
    # sys and Path already imported at module level

    # Issue #84: Safe path addition for tests
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.utils.config import Config

# Issue #84: Removed unsafe sys.path manipulation
# Tests should run from project root via pytest


# Modern client fixtures for testing
@pytest.fixture
def production_client():
    """Create a ProductionIstatClient instance for testing."""
    from src.api.production_istat_client import ProductionIstatClient

    client = ProductionIstatClient(enable_cache_fallback=True)
    yield client
    # Cleanup
    if hasattr(client, "close"):
        client.close()


@pytest.fixture
def mock_client():
    """Create a mocked ProductionIstatClient for unit tests."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_client.base_url = "https://sdmx.istat.it/SDMXWS/rest/"
    mock_client.get_status.return_value = {"status": "ok", "metrics": {}}
    mock_client.fetch_dataset.return_value = {"status": "success", "data": {}}

    return mock_client


@pytest.fixture
def unified_repository():
    """Create a UnifiedDataRepository instance for testing."""
    from src.database.sqlite.repository import get_unified_repository

    repo = get_unified_repository()
    yield repo
    # Cleanup
    if hasattr(repo, "close"):
        repo.close()


@pytest.fixture
def dataflow_analysis_service():
    """Create a DataflowAnalysisService for testing."""
    from src.services.service_factory import get_dataflow_analysis_service

    service = get_dataflow_analysis_service()
    yield service
    # Cleanup if needed
    if hasattr(service, "close"):
        service.close()


@pytest.fixture(autouse=True)
def silent_temp_file_manager():
    """Enable silent mode for TempFileManager during tests."""
    # Set environment variable before any imports
    os.environ["TEMP_FILE_MANAGER_SILENT"] = "true"

    # Also reduce logging level for temp file manager
    import logging

    temp_logger = logging.getLogger("src.utils.temp_file_manager")
    original_level = temp_logger.level
    temp_logger.setLevel(logging.ERROR)

    yield

    # Restore logging level
    temp_logger.setLevel(original_level)

    # Clean up environment
    if "TEMP_FILE_MANAGER_SILENT" in os.environ:
        del os.environ["TEMP_FILE_MANAGER_SILENT"]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_xml_data():
    """Sample ISTAT XML data for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
    <message:Header>
        <message:ID>test_dataset</message:ID>
        <message:Test>false</message:Test>
        <message:Prepared>2025-01-01T00:00:00</message:Prepared>
    </message:Header>
    <message:DataSet>
        <generic:Series xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <generic:SeriesKey>
                <generic:Value id="TERRITORIO" value="IT"/>
                <generic:Value id="ANNO" value="2024"/>
            </generic:SeriesKey>
            <generic:Obs>
                <generic:ObsDimension value="2024"/>
                <generic:ObsValue value="1000000"/>
            </generic:Obs>
        </generic:Series>
    </message:DataSet>
</message:GenericData>"""


@pytest.fixture
def sample_dataflow_xml():
    """Sample ISTAT dataflow XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                   xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
                   xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
    <message:Header>
        <message:ID>dataflow_response</message:ID>
    </message:Header>
    <message:Structures>
        <structure:Dataflows>
            <structure:Dataflow id="101_12" version="1.0" agencyID="IT1">
                <common:Name xml:lang="it">Popolazione residente</common:Name>
                <common:Name xml:lang="en">Resident population</common:Name>
                <common:Description xml:lang="it">Dati popolazione per regione</common:Description>
            </structure:Dataflow>
            <structure:Dataflow id="163_156" version="1.0" agencyID="IT1">
                <common:Name xml:lang="it">PIL regionale</common:Name>
                <common:Name xml:lang="en">Regional GDP</common:Name>
                <common:Description xml:lang="it">Prodotto interno lordo regionale</common:Description>
            </structure:Dataflow>
        </structure:Dataflows>
    </message:Structures>
</message:Structure>"""


@pytest.fixture
def sample_converted_data():
    """Sample converted data for testing."""
    return pd.DataFrame(
        {
            "territorio": ["IT", "IT", "IT"],
            "anno": [2022, 2023, 2024],
            "valore": [1000000, 1050000, 1100000],
            "unita_misura": ["numero", "numero", "numero"],
        }
    )


@pytest.fixture
def mock_requests_session():
    """Mock requests session for API testing."""
    with patch("requests.Session") as mock_session:
        mock_instance = Mock()
        mock_session.return_value = mock_instance

        # Default successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<?xml version='1.0'?><root>test</root>"
        mock_response.content = b"<?xml version='1.0'?><root>test</root>"
        mock_instance.get.return_value = mock_response

        yield mock_instance


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch.object(Config, "ISTAT_API_BASE_URL", "http://test.api.url/"):
        with patch.object(Config, "ISTAT_API_TIMEOUT", 10):
            with patch.object(Config, "ENABLE_CACHE", False):
                yield Config


@pytest.fixture
def sample_tableau_datasets():
    """Sample Tableau-ready datasets for testing."""
    return [
        {
            "dataflow_id": "101_12",
            "name": "Popolazione residente",
            "category": "popolazione",
            "relevance_score": 10,
            "data_size_mb": 2.5,
            "observations_count": 1000,
            "priority": 15.2,
        },
        {
            "dataflow_id": "163_156",
            "name": "PIL regionale",
            "category": "economia",
            "relevance_score": 9,
            "data_size_mb": 1.8,
            "observations_count": 800,
            "priority": 13.1,
        },
    ]


@pytest.fixture
def sample_powerbi_datasets():
    """Sample PowerBI-ready datasets for testing."""
    return [
        {
            "id": "101_12",
            "name": "Popolazione residente",
            "category": "popolazione",
            "formats": ["csv", "excel", "parquet", "json"],
            "file_paths": {
                "csv": "data/processed/powerbi/popolazione_101_12.csv",
                "excel": "data/processed/powerbi/popolazione_101_12.xlsx",
                "parquet": "data/processed/powerbi/popolazione_101_12.parquet",
                "json": "data/processed/powerbi/popolazione_101_12.json",
            },
        }
    ]


@pytest.fixture
def test_xml_file(temp_dir, sample_xml_data):
    """Create a test XML file."""
    xml_file = temp_dir / "test_data.xml"
    xml_file.write_text(sample_xml_data, encoding="utf-8")
    return xml_file


@pytest.fixture
def test_dataflow_file(temp_dir, sample_dataflow_xml):
    """Create a test dataflow XML file."""
    xml_file = temp_dir / "dataflow_response.xml"
    xml_file.write_text(sample_dataflow_xml, encoding="utf-8")
    return xml_file


@pytest.fixture
def sample_conversion_summary():
    """Sample conversion summary for testing."""
    return {
        "conversion_timestamp": "2025-01-01T10:00:00",
        "total_datasets": 2,
        "successful_conversions": 2,
        "failed_conversions": 0,
        "success_rate": "100%",
        "successful_datasets": ["101_12", "163_156"],
        "failed_datasets": [],
        "files_generated": {
            "csv_files": 2,
            "excel_files": 2,
            "json_files": 2,
            "parquet_files": 2,
        },
    }


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield
    # Clean up any test files created during testing
    test_patterns = [
        "test_*.xml",
        "sample_*.xml",
        "test_*.json",
        "test_*.csv",
        "test_*.xlsx",
        "test_*.parquet",
    ]

    for pattern in test_patterns:
        for file in Path(".").glob(pattern):
            try:
                file.unlink()
            except OSError:
                pass


@pytest.fixture
def category_keywords():
    """Sample category keywords for testing."""
    return {
        "popolazione": {
            "keywords": ["popolazione", "popul", "residente", "demografic"],
            "priority": 10,
        },
        "economia": {"keywords": ["pil", "gdp", "economia", "economic"], "priority": 9},
        "lavoro": {"keywords": ["lavoro", "occupazione", "employment"], "priority": 8},
    }


@pytest.fixture
def mock_powerbi_client():
    """Mock PowerBI client for testing."""
    with patch("src.api.powerbi_api.PowerBIAPI") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance

        # Mock successful authentication
        mock_instance.authenticate.return_value = True
        mock_instance.get_workspaces.return_value = [
            {"id": "test-workspace-id", "name": "Test Workspace"}
        ]
        mock_instance.create_dataset.return_value = {"id": "test-dataset-id"}

        yield mock_instance


# Day 6: Centralized test data fixtures for hardcoded data elimination


@pytest.fixture
def sample_powerbi_test_data():
    """Centralized fixture for PowerBI integration test data."""
    return [
        {
            "dataset_id": "TEST_POWERBI_DATASET",
            "year": 2023,
            "territory_code": "01",
            "territory_name": "Piemonte",
            "obs_value": 4356406,
            "quality_score": 0.9,
            "measure_name": "Popolazione residente",
            "time_period": "2023-01-01",
            "last_updated": "2023-01-01T10:00:00",
        },
        {
            "dataset_id": "TEST_POWERBI_DATASET",
            "year": 2023,
            "territory_code": "02",
            "territory_name": "Valle d'Aosta",
            "obs_value": 125501,
            "quality_score": 0.8,
            "measure_name": "Popolazione residente",
            "time_period": "2023-01-01",
            "last_updated": "2023-01-01T10:00:00",
        },
        {
            "dataset_id": "TEST_POWERBI_DATASET",
            "year": 2024,
            "territory_code": "01",
            "territory_name": "Piemonte",
            "obs_value": 4378123,
            "quality_score": 0.92,
            "measure_name": "Popolazione residente",
            "time_period": "2024-01-01",
            "last_updated": "2024-01-01T10:00:00",
        },
    ]


@pytest.fixture
def sample_converter_test_data():
    """Centralized fixture for converter test data."""
    return {
        "territorio": ["IT", "IT", "FR"],
        "anno": [2023, 2024, 2023],
        "valore": [1000000, 1100000, 67000000],
        "unita_misura": ["numero", "numero", "numero"],
        "qualita": [0.9, 0.92, 0.85],
    }


@pytest.fixture
def sample_performance_test_data():
    """Centralized fixture for performance test data generation."""

    def generate_test_data(size: int = 1000, base_date: str = "2023-01-01"):
        """Generate performance test data of specified size."""
        from datetime import datetime, timedelta

        base_dt = datetime.fromisoformat(base_date)

        return {
            "dataset_id": [f"PERF_TEST_{i//100}" for i in range(size)],
            "territory_code": [f"IT_{i % 20:02d}" for i in range(size)],
            "territory_name": [f"Territory {i % 20}" for i in range(size)],
            "year": [2020 + (i % 5) for i in range(size)],
            "obs_value": [1000 + (i * 10) for i in range(size)],
            "quality_score": [0.8 + (i % 20) * 0.01 for i in range(size)],
            "time_period": [
                (base_dt + timedelta(days=i)).isoformat() for i in range(size)
            ],
        }

    return generate_test_data


@pytest.fixture
def sample_api_test_urls():
    """Centralized fixture for API test URLs and configurations."""
    return {
        "base_url": "http://localhost:8000",
        "test_base_url": "http://test.api.url/",
        "istat_base_url": "https://sdmx.istat.it/SDMXWS/rest/",
        "redis_url": "redis://localhost:6379/0",
        "test_redis_url": "redis://localhost:6379/1",
        "cors_origins": ["https://localhost:3000", "http://localhost:3000"],
        "powerbi_base_url": "https://api.powerbi.com/v1.0/",
    }


@pytest.fixture
def sample_test_configurations():
    """Centralized fixture for test configurations and timeouts."""
    return {
        "database_timeout": 1.0,
        "api_timeout": 5.0,
        "circuit_breaker": {
            "failure_threshold": 3,
            "recovery_timeout": 5,
            "test_recovery_timeout": 1,
        },
        "performance_thresholds": {
            "query_max_time_ms": 1000,
            "bulk_insert_max_time_ms": 5000,
            "api_response_max_time_ms": 2000,
        },
        "test_batch_sizes": [100, 500, 1000, 5000],
        "test_concurrency_levels": [1, 5, 10, 20],
    }


@pytest.fixture
def sample_dataset_metadata():
    """Centralized fixture for dataset metadata test data."""
    return [
        {
            "dataset_id": "101_12",
            "name": "Popolazione residente",
            "category": "popolazione",
            "description": "Dati popolazione per regione",
            "priority": 10,
            "quality_score": 0.95,
            "update_frequency": "annual",
            "geographic_level": "regioni",
            "relevance_score": 10,
            "data_size_mb": 2.5,
            "observations_count": 1000,
        },
        {
            "dataset_id": "163_156",
            "name": "PIL regionale",
            "category": "economia",
            "description": "Prodotto interno lordo regionale",
            "priority": 9,
            "quality_score": 0.88,
            "update_frequency": "quarterly",
            "geographic_level": "regioni",
            "relevance_score": 9,
            "data_size_mb": 1.8,
            "observations_count": 800,
        },
        {
            "dataset_id": "143_89",
            "name": "Tasso di disoccupazione",
            "category": "lavoro",
            "description": "Tasso di disoccupazione per regione",
            "priority": 8,
            "quality_score": 0.92,
            "update_frequency": "monthly",
            "geographic_level": "regioni",
            "relevance_score": 8,
            "data_size_mb": 1.2,
            "observations_count": 600,
        },
    ]


@pytest.fixture
def sample_territory_data():
    """Centralized fixture for Italian territory test data."""
    return [
        {"code": "01", "name": "Piemonte", "type": "regione"},
        {"code": "02", "name": "Valle d'Aosta", "type": "regione"},
        {"code": "03", "name": "Lombardia", "type": "regione"},
        {"code": "04", "name": "Trentino-Alto Adige", "type": "regione"},
        {"code": "05", "name": "Veneto", "type": "regione"},
        {"code": "001001", "name": "Torino", "type": "comune"},
        {"code": "001002", "name": "Vercelli", "type": "comune"},
        {"code": "003001", "name": "Milano", "type": "comune"},
        {"code": "003002", "name": "Bergamo", "type": "comune"},
    ]


@pytest.fixture
def sample_conversion_test_cases():
    """Centralized fixture for data conversion test cases."""
    return [
        {
            "name": "basic_xml_conversion",
            "input_format": "xml",
            "output_format": "csv",
            "expected_columns": ["territorio", "anno", "valore"],
            "expected_rows": 3,
        },
        {
            "name": "excel_conversion",
            "input_format": "xml",
            "output_format": "excel",
            "expected_columns": ["territorio", "anno", "valore", "unita_misura"],
            "expected_rows": 5,
        },
        {
            "name": "json_conversion",
            "input_format": "xml",
            "output_format": "json",
            "expected_structure": "nested",
            "expected_records": 10,
        },
        {
            "name": "parquet_conversion",
            "input_format": "csv",
            "output_format": "parquet",
            "expected_compression": "snappy",
            "expected_schema_version": "2.0",
        },
    ]


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line("markers", "performance: Performance and scalability tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: Tests requiring API access")
