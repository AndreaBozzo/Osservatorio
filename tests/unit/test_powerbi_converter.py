"""
Unit tests for PowerBI converter functionality.
"""

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from src.converters.powerbi_converter import IstatXMLToPowerBIConverter


class TestIstatXMLToPowerBIConverter:
    """Test PowerBI converter class."""

    def test_init_creates_converter(self):
        """Test converter initialization."""
        converter = IstatXMLToPowerBIConverter()

        assert converter.powerbi_output_dir is not None
        assert converter.path_validator is not None
        assert hasattr(converter, "datasets_config")
        assert isinstance(converter.datasets_config, dict)
        assert hasattr(converter, "conversion_results")
        assert isinstance(converter.conversion_results, list)

    def test_load_config_creates_sample_when_none_exists(self):
        """Test config loading creates sample when none exists."""
        with patch("glob.glob", return_value=[]):
            with patch.object(
                IstatXMLToPowerBIConverter, "_create_sample_config"
            ) as mock_create:
                mock_create.return_value = {"test": "config"}
                converter = IstatXMLToPowerBIConverter()
                config = converter._load_datasets_config()

                assert config == {"test": "config"}
                mock_create.assert_called_once()

    def test_create_sample_config_structure(self):
        """Test sample config creation structure."""
        converter = IstatXMLToPowerBIConverter()

        with patch.object(
            converter.path_validator, "safe_open", return_value=mock_open().return_value
        ):
            with patch("json.dump"):
                config = converter._create_sample_config()

                assert isinstance(config, dict)
                assert "powerbi_settings" in config
                assert "output_formats" in config
                assert "data_quality" in config

    def test_parse_xml_content_with_valid_data(self):
        """Test XML parsing with valid SDMX data."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                           xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
                    <generic:SeriesKey>
                        <generic:Value id="TERRITORIO" value="IT"/>
                        <generic:Value id="TIPO_DATO" value="STOCK"/>
                    </generic:SeriesKey>
                    <generic:Obs>
                        <generic:ObsDimension value="2023"/>
                        <generic:ObsValue value="59240329"/>
                    </generic:Obs>
                </generic:Series>
            </message:DataSet>
        </message:GenericData>"""

        converter = IstatXMLToPowerBIConverter()
        df = converter._parse_xml_content(xml_content)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "TERRITORIO" in df.columns
        assert "TIPO_DATO" in df.columns
        assert "Time" in df.columns
        assert "Value" in df.columns

    def test_parse_xml_content_with_invalid_data(self):
        """Test XML parsing with invalid data."""
        converter = IstatXMLToPowerBIConverter()

        # Test with invalid XML
        with pytest.raises(ET.ParseError):
            converter._parse_xml_content("invalid xml")

        # Test with empty content
        df = converter._parse_xml_content("")
        assert df.empty

    def test_categorize_dataset_popolazione(self):
        """Test dataset categorization for population data."""
        converter = IstatXMLToPowerBIConverter()

        # Test population category
        category, priority = converter._categorize_dataset(
            "101_12", "Popolazione residente"
        )
        assert category == "popolazione"
        assert priority == 10

    def test_categorize_dataset_economia(self):
        """Test dataset categorization for economic data."""
        converter = IstatXMLToPowerBIConverter()

        # Test economy category
        category, priority = converter._categorize_dataset(
            "123_45", "PIL e reddito nazionale"
        )
        assert category == "economia"
        assert priority == 9

    def test_categorize_dataset_unknown(self):
        """Test dataset categorization for unknown data."""
        converter = IstatXMLToPowerBIConverter()

        # Test unknown category
        category, priority = converter._categorize_dataset("999_99", "Unknown dataset")
        assert category == "altro"
        assert priority == 1

    def test_generate_powerbi_formats_creates_files(self):
        """Test PowerBI format generation creates expected files."""
        converter = IstatXMLToPowerBIConverter()

        # Create sample dataframe
        df = pd.DataFrame(
            {"TERRITORIO": ["IT", "IT"], "Time": ["2022", "2023"], "Value": [100, 200]}
        )

        dataset_info = {"id": "TEST_123", "name": "Test Dataset", "category": "test"}

        with patch.object(converter.path_validator, "validate_path", return_value=True):
            with patch("pandas.DataFrame.to_csv") as mock_csv:
                with patch("pandas.DataFrame.to_parquet") as mock_parquet:
                    with patch("builtins.open", mock_open()):
                        result = converter._generate_powerbi_formats(df, dataset_info)

                        assert "csv_file" in result
                        assert "parquet_file" in result
                        assert "json_file" in result
                        assert "excel_file" in result

                        # Verify CSV and Parquet were called
                        mock_csv.assert_called()
                        mock_parquet.assert_called()

    def test_validate_data_quality_high_quality(self):
        """Test data quality validation for high quality data."""
        converter = IstatXMLToPowerBIConverter()

        # Create high quality dataframe
        df = pd.DataFrame(
            {
                "TERRITORIO": ["IT"] * 100,
                "Time": [str(2000 + i) for i in range(100)],
                "Value": [1000 + i for i in range(100)],
            }
        )

        quality_report = converter._validate_data_quality(df)

        assert quality_report["total_rows"] == 100
        assert quality_report["total_columns"] == 3
        assert quality_report["completeness_score"] > 0.8
        assert quality_report["data_quality_score"] > 0.8

    def test_validate_data_quality_low_quality(self):
        """Test data quality validation for low quality data."""
        converter = IstatXMLToPowerBIConverter()

        # Create low quality dataframe with many nulls
        df = pd.DataFrame(
            {
                "TERRITORIO": ["IT", None, "IT", None, "IT"],
                "Time": [None, "2022", None, "2024", None],
                "Value": [100, None, None, 400, None],
            }
        )

        quality_report = converter._validate_data_quality(df)

        assert quality_report["total_rows"] == 5
        assert quality_report["total_columns"] == 3
        assert quality_report["completeness_score"] < 0.7
        assert quality_report["data_quality_score"] < 0.7

    def test_convert_xml_to_powerbi_full_pipeline(self):
        """Test complete conversion pipeline."""
        converter = IstatXMLToPowerBIConverter()

        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                           xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
                    <generic:SeriesKey>
                        <generic:Value id="TERRITORIO" value="IT"/>
                    </generic:SeriesKey>
                    <generic:Obs>
                        <generic:ObsDimension value="2023"/>
                        <generic:ObsValue value="100"/>
                    </generic:Obs>
                </generic:Series>
            </message:DataSet>
        </message:GenericData>"""

        with patch.object(converter.path_validator, "validate_path", return_value=True):
            with patch.object(
                converter.path_validator,
                "safe_open",
                return_value=mock_open().return_value,
            ):
                with patch("pandas.DataFrame.to_csv"):
                    with patch("pandas.DataFrame.to_parquet"):
                        with patch("builtins.open", mock_open()):
                            result = converter.convert_xml_to_powerbi(
                                xml_content, "TEST_123", "Test Dataset"
                            )

                            assert "success" in result
                            assert "files_created" in result
                            assert "data_quality" in result
                            assert "summary" in result

    def test_convert_xml_to_powerbi_with_file_path(self):
        """Test conversion with file path input."""
        converter = IstatXMLToPowerBIConverter()

        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                           xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
                    <generic:SeriesKey>
                        <generic:Value id="TERRITORIO" value="IT"/>
                    </generic:SeriesKey>
                    <generic:Obs>
                        <generic:ObsDimension value="2023"/>
                        <generic:ObsValue value="100"/>
                    </generic:Obs>
                </generic:Series>
            </message:DataSet>
        </message:GenericData>"""

        with patch.object(
            converter.path_validator,
            "safe_open",
            return_value=mock_open(read_data=xml_content).return_value,
        ):
            with patch.object(
                converter.path_validator, "validate_path", return_value=True
            ):
                with patch("pandas.DataFrame.to_csv"):
                    with patch("pandas.DataFrame.to_parquet"):
                        with patch("builtins.open", mock_open()):
                            result = converter.convert_xml_to_powerbi(
                                "test_file.xml", "TEST_123", "Test Dataset"
                            )

                            assert "success" in result
                            assert "files_created" in result

    def test_error_handling_invalid_xml_file(self):
        """Test error handling for invalid XML file."""
        converter = IstatXMLToPowerBIConverter()

        # Test with non-existent file
        with patch.object(converter.path_validator, "safe_open", return_value=None):
            result = converter.convert_xml_to_powerbi(
                "nonexistent.xml", "TEST_123", "Test Dataset"
            )

            assert result["success"] is False
            assert "error" in result
