"""
Unit tests for Tableau converter functionality.
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pandas as pd

from src.converters.tableau_converter import IstatXMLtoTableauConverter


class TestIstatXMLtoTableauConverter:
    """Test Tableau converter class."""

    def test_init_creates_converter(self):
        """Test converter initialization."""
        converter = IstatXMLtoTableauConverter()

        assert converter.path_validator is not None
        assert hasattr(converter, "datasets_config")
        assert isinstance(converter.datasets_config, dict)
        assert hasattr(converter, "conversion_results")
        assert isinstance(converter.conversion_results, list)

    def test_load_config_creates_sample_when_none_exists(self):
        """Test config loading works with SQLite first, then falls back to JSON."""
        converter = IstatXMLtoTableauConverter()
        config = converter.datasets_config

        # Should load from SQLite metadata (which has real data after migration)
        assert "total_datasets" in config
        assert "source" in config
        assert config["source"] == "sqlite_metadata"
        assert isinstance(config["datasets"], list)

    def test_create_sample_config_structure(self):
        """Test sample config creation structure."""
        converter = IstatXMLtoTableauConverter()

        with patch.object(
            converter.path_validator, "safe_open", return_value=mock_open().return_value
        ):
            with patch("json.dump"):
                config = converter._create_sample_config()

                assert isinstance(config, dict)
                assert "total_datasets" in config
                assert "categories" in config
                assert "datasets" in config
                assert isinstance(config["datasets"], list)
                assert len(config["datasets"]) > 0

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

        converter = IstatXMLtoTableauConverter()
        df = converter._parse_xml_content(xml_content)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "TERRITORIO" in df.columns
        assert "TIPO_DATO" in df.columns
        assert "Time" in df.columns
        assert "Value" in df.columns

    def test_categorize_dataset_popolazione(self):
        """Test dataset categorization for population data."""
        converter = IstatXMLtoTableauConverter()

        # Test population category
        category, priority = converter._categorize_dataset(
            "101_12", "Popolazione residente"
        )
        assert category == "popolazione"
        assert priority == 10

    def test_categorize_dataset_economia(self):
        """Test dataset categorization for economic data."""
        converter = IstatXMLtoTableauConverter()

        # Test economy category
        category, priority = converter._categorize_dataset(
            "123_45", "PIL e reddito nazionale"
        )
        assert category == "economia"
        assert priority == 9

    def test_categorize_dataset_unknown(self):
        """Test dataset categorization for unknown data."""
        converter = IstatXMLtoTableauConverter()

        # Test unknown category
        category, priority = converter._categorize_dataset("999_99", "Unknown dataset")
        assert category == "altro"
        assert priority == 1

    def test_generate_tableau_formats_creates_files(self):
        """Test Tableau format generation creates expected files."""
        converter = IstatXMLtoTableauConverter()

        # Create sample dataframe
        df = pd.DataFrame(
            {"TERRITORIO": ["IT", "IT"], "Time": ["2022", "2023"], "Value": [100, 200]}
        )

        dataset_info = {"id": "TEST_123", "name": "Test Dataset", "category": "test"}

        with patch.object(converter.path_validator, "validate_path", return_value=True):
            with patch.object(
                converter.path_validator,
                "get_safe_path",
                return_value=Path("tableau_output"),
            ):
                with patch("pandas.DataFrame.to_csv") as mock_csv:
                    with patch("pandas.DataFrame.to_json") as mock_json:
                        with patch("pandas.ExcelWriter") as mock_excel:
                            with patch("pandas.DataFrame.to_excel"):
                                # Mock the context manager for ExcelWriter
                                mock_excel.return_value.__enter__ = Mock(
                                    return_value=mock_excel.return_value
                                )
                                mock_excel.return_value.__exit__ = Mock(
                                    return_value=None
                                )

                                result = converter._generate_tableau_formats(
                                    df, dataset_info
                                )

                                assert "csv_file" in result
                                assert "excel_file" in result
                                assert "json_file" in result

                                # Verify methods were called
                                mock_csv.assert_called()
                                mock_json.assert_called()

    def test_validate_data_quality_high_quality(self):
        """Test data quality validation for high quality data."""
        converter = IstatXMLtoTableauConverter()

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
        converter = IstatXMLtoTableauConverter()

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

    def test_convert_xml_to_tableau_full_pipeline(self):
        """Test complete conversion pipeline."""
        converter = IstatXMLtoTableauConverter()

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
                    with patch("pandas.ExcelWriter"):
                        with patch("builtins.open", mock_open()):
                            result = converter.convert_xml_to_tableau(
                                xml_content, "TEST_123", "Test Dataset"
                            )

                            assert "success" in result
                            assert "files_created" in result
                            assert "data_quality" in result
                            assert "summary" in result

    def test_convert_xml_to_tableau_with_file_path(self):
        """Test conversion with file path input."""
        converter = IstatXMLtoTableauConverter()

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
                    with patch("pandas.ExcelWriter"):
                        with patch("builtins.open", mock_open()):
                            result = converter.convert_xml_to_tableau(
                                "test_file.xml", "TEST_123", "Test Dataset"
                            )

                            assert "success" in result
                            assert "files_created" in result

    def test_error_handling_invalid_xml_file(self):
        """Test error handling for invalid XML file."""
        converter = IstatXMLtoTableauConverter()

        # Test with non-existent file
        with patch.object(converter.path_validator, "safe_open", return_value=None):
            result = converter.convert_xml_to_tableau(
                "nonexistent.xml", "TEST_123", "Test Dataset"
            )

            assert result["success"] is False
            assert "error" in result

    def test_generate_tableau_instructions_creates_file(self):
        """Test Tableau instructions generation."""
        converter = IstatXMLtoTableauConverter()

        summary = {
            "dataset_id": "TEST_123",
            "name": "Test Dataset",
            "category": "test",
            "output_files": {
                "csv": "test.csv",
                "excel": "test.xlsx",
                "json": "test.json",
            },
            "cleaned_rows": 100,
            "columns": ["TERRITORIO", "Time", "Value"],
        }

        with patch.object(converter.path_validator, "validate_path", return_value=True):
            with patch.object(
                converter.path_validator,
                "safe_open",
                mock_open(),
            ):
                converter._generate_tableau_instructions([summary], "test_output")

                # Should not raise any exceptions
                assert True

    def test_generate_quick_start_guide_creates_file(self):
        """Test Quick Start guide generation."""
        converter = IstatXMLtoTableauConverter()

        with patch.object(converter.path_validator, "validate_path", return_value=True):
            with patch.object(
                converter.path_validator,
                "safe_open",
                return_value=mock_open().return_value,
            ):
                converter._generate_quick_start("test_output")

                # Should not raise any exceptions
                assert True
