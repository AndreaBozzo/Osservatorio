"""
Test configuration and fixtures for Osservatorio tests.
Simplified for MVP - Issue #159.
"""

import gc
import os
import shutil
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

try:
    from osservatorio_istat.utils.config import Config
except ImportError:
    # Development mode fallback
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.utils.config import Config


# =============================================================================
# CORE CLIENT FIXTURES
# =============================================================================


@pytest.fixture
def production_client():
    """Create a ProductionIstatClient instance for testing."""
    from src.api.production_istat_client import ProductionIstatClient

    client = ProductionIstatClient(enable_cache_fallback=True)
    yield client
    if hasattr(client, "close"):
        client.close()


@pytest.fixture
def mock_client():
    """Create a mocked ProductionIstatClient for unit tests."""
    mock_client = Mock()
    mock_client.base_url = "https://sdmx.istat.it/SDMXWS/rest/"
    mock_client.get_status.return_value = {"status": "ok", "metrics": {}}
    mock_client.fetch_dataset.return_value = {"status": "success", "data": {}}
    return mock_client


# =============================================================================
# DATABASE FIXTURES
# =============================================================================


@contextmanager
def temporary_database():
    """Context manager for creating and cleaning up temporary databases."""
    temp_db = tempfile.mktemp(suffix=".db")

    try:
        from src.database.sqlite.schema import MetadataSchema

        schema_manager = MetadataSchema(temp_db)
        schema_manager.create_schema()
        schema_manager.close_connections()
        del schema_manager

        yield temp_db

    finally:
        gc.collect()
        try:
            for obj in gc.get_objects():
                if isinstance(obj, sqlite3.Connection):
                    try:
                        if hasattr(obj, "close"):
                            obj.close()
                    except Exception:
                        pass
        except Exception:
            pass

        import time

        time.sleep(0.1)

        try:
            if os.path.exists(temp_db):
                os.remove(temp_db)
        except (PermissionError, OSError):
            pass


@pytest.fixture
def temp_db():
    """Provide a temporary database path for tests."""
    with temporary_database() as db_path:
        yield db_path


@pytest.fixture(scope="class")
def temp_db_class():
    """Provide a temporary database path for class-scoped tests."""
    with temporary_database() as db_path:
        yield db_path


@pytest.fixture
def unified_repository():
    """Create a UnifiedDataRepository instance for testing."""
    from src.database.sqlite.repository import get_unified_repository

    repo = get_unified_repository()
    yield repo
    if hasattr(repo, "close"):
        repo.close()


# =============================================================================
# TEMPORARY FILE FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def silent_temp_file_manager():
    """Enable silent mode for TempFileManager during tests."""
    os.environ["TEMP_FILE_MANAGER_SILENT"] = "true"

    import logging

    temp_logger = logging.getLogger("src.utils.temp_file_manager")
    original_level = temp_logger.level
    temp_logger.setLevel(logging.ERROR)

    yield

    temp_logger.setLevel(original_level)
    if "TEMP_FILE_MANAGER_SILENT" in os.environ:
        del os.environ["TEMP_FILE_MANAGER_SILENT"]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test."""
    yield
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


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================


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
def simple_mock_sdmx():
    """Simple SDMX data for testing."""
    return "<GenericData><DataSet><Obs><ObsValue value='1000'/></Obs></DataSet></GenericData>"


# =============================================================================
# MOCK FIXTURES
# =============================================================================


@pytest.fixture
def mock_requests_session():
    """Mock requests session for API testing."""
    with patch("requests.Session") as mock_session:
        mock_instance = Mock()
        mock_session.return_value = mock_instance

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


# =============================================================================
# TEST FILE FIXTURES
# =============================================================================


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


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: Tests requiring API access")
    config.addinivalue_line(
        "markers", "simple_pipeline: Tests specific to SimpleIngestionPipeline"
    )
