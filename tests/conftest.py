"""
Test configuration and fixtures for osservatorio scuola tests.
"""

import json
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config


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
