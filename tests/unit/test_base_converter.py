"""
Test cases for BaseIstatConverter
Tests the abstract base class functionality shared by PowerBI and Tableau converters.
"""

import unittest
from unittest.mock import Mock, patch

import pandas as pd

from src.converters.base_converter import BaseIstatConverter
from src.converters.factory import ConverterFactory


class TestBaseIstatConverter(unittest.TestCase):
    """Test cases for BaseIstatConverter abstract class."""

    def setUp(self):
        """Set up test environment before each test."""

        # Create a concrete implementation for testing
        class ConcreteConverter(BaseIstatConverter):
            def _format_output(self, df, dataset_info):
                return {"formatted": True}

            def _generate_metadata(self, dataset_info):
                return {"metadata": True}

            def convert_xml_to_target(self, xml_input, dataset_id, dataset_name):
                return {"converted": True}

        with patch("src.converters.base_converter.get_dataset_config_manager"):
            self.converter = ConcreteConverter()

    def test_init_sets_common_properties(self):
        """Test that initialization sets up common properties."""
        self.assertIsNotNone(self.converter.namespaces)
        self.assertIn("message", self.converter.namespaces)
        self.assertIn("generic", self.converter.namespaces)
        self.assertIsNotNone(self.converter.path_validator)
        self.assertIsNotNone(self.converter.datasets_config)
        self.assertIsInstance(self.converter.conversion_results, list)

    def test_namespaces_structure(self):
        """Test that SDMX namespaces are correctly defined."""
        expected_namespaces = {
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
            "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
            "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
            "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xml": "http://www.w3.org/XML/1998/namespace",
        }
        self.assertEqual(self.converter.namespaces, expected_namespaces)

    @patch("src.converters.base_converter.get_dataset_config_manager")
    def test_load_datasets_config_sqlite_success(self, mock_config):
        """Test successful SQLite config loading."""
        mock_manager = Mock()
        mock_manager.get_datasets_config.return_value = {
            "total_datasets": 5,
            "categories": {"test": ["TEST1"]},
            "datasets": [],
        }
        mock_config.return_value = mock_manager

        class TestConverter(BaseIstatConverter):
            def _format_output(self, df, dataset_info):
                return {}

            def _generate_metadata(self, dataset_info):
                return {}

            def convert_xml_to_target(self, xml_input, dataset_id, dataset_name):
                return {}

        converter = TestConverter()

        self.assertEqual(converter.datasets_config["total_datasets"], 5)
        self.assertIn("test", converter.datasets_config["categories"])

    @patch("src.converters.base_converter.get_dataset_config_manager")
    def test_load_datasets_config_sqlite_error_fallback(self, mock_config):
        """Test fallback when SQLite fails (returns empty config)."""
        # Mock SQLite failure
        mock_manager = Mock()
        mock_manager.get_datasets_config.side_effect = Exception("SQLite failed")
        mock_config.return_value = mock_manager

        class TestConverter(BaseIstatConverter):
            def _format_output(self, df, dataset_info):
                return {}

            def _generate_metadata(self, dataset_info):
                return {}

            def convert_xml_to_target(self, xml_input, dataset_id, dataset_name):
                return {}

        converter = TestConverter()

        self.assertEqual(converter.datasets_config["total_datasets"], 0)
        self.assertEqual(converter.datasets_config["source"], "sqlite_error")

    def test_categorize_dataset_popolazione(self):
        """Test dataset categorization for population data."""
        category, priority = self.converter._categorize_dataset(
            "DCIS_POPRES1", "Popolazione residente"
        )
        self.assertEqual(category, "popolazione")
        self.assertEqual(priority, 10)

    def test_categorize_dataset_economia(self):
        """Test dataset categorization for economic data."""
        category, priority = self.converter._categorize_dataset(
            "PIL_GDP", "Prodotto interno lordo"
        )
        self.assertEqual(category, "economia")
        self.assertEqual(priority, 9)

    def test_categorize_dataset_unknown(self):
        """Test dataset categorization for unknown data."""
        category, priority = self.converter._categorize_dataset(
            "UNKNOWN", "Unknown dataset"
        )
        self.assertEqual(category, "altro")
        self.assertEqual(priority, 1)

    def test_validate_data_quality_empty(self):
        """Test data quality validation with empty DataFrame."""
        df = pd.DataFrame()
        quality = self.converter._validate_data_quality(df)

        self.assertEqual(quality["total_rows"], 0)
        self.assertEqual(quality["total_columns"], 0)
        self.assertEqual(quality["completeness_score"], 0.0)
        self.assertIn("Empty dataset", quality["issues"])

    def test_validate_data_quality_high_quality(self):
        """Test data quality validation with high quality data."""
        df = pd.DataFrame(
            {
                "A": [1, 2, 3, 4, 5],
                "B": ["a", "b", "c", "d", "e"],
                "C": [1.1, 2.2, 3.3, 4.4, 5.5],
            }
        )
        quality = self.converter._validate_data_quality(df)

        self.assertEqual(quality["total_rows"], 5)
        self.assertEqual(quality["total_columns"], 3)
        self.assertEqual(quality["completeness_score"], 1.0)
        self.assertGreaterEqual(quality["data_quality_score"], 0.9)

    def test_validate_data_quality_low_quality(self):
        """Test data quality validation with low quality data."""
        df = pd.DataFrame(
            {
                "A": [1, None, 3, None, 5],
                "B": [None, "b", None, "d", None],
                "C": [1.1, None, None, 4.4, None],
            }
        )
        quality = self.converter._validate_data_quality(df)

        self.assertEqual(quality["total_rows"], 5)
        self.assertEqual(quality["total_columns"], 3)
        self.assertLess(quality["completeness_score"], 0.8)
        self.assertIn("Low completeness score", quality["issues"])

    def test_parse_xml_content_basic(self):
        """Test basic XML content parsing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
            <Obs>
                <ObsDimension value="2023"/>
                <ObsValue value="100"/>
            </Obs>
        </message:GenericData>"""

        df = self.converter._parse_xml_content(xml_content)

        self.assertFalse(df.empty)
        self.assertGreater(len(df.columns), 0)

    def test_parse_xml_content_invalid(self):
        """Test XML content parsing with invalid XML."""
        import xml.etree.ElementTree as ET

        invalid_xml = "<invalid>unclosed tag"

        # This should raise ParseError for truly invalid XML
        with self.assertRaises(ET.ParseError):
            self.converter._parse_xml_content(invalid_xml)

    def test_extract_observation_from_element(self):
        """Test observation extraction from XML element."""
        import xml.etree.ElementTree as ET

        xml_content = """<Obs>
            <ObsDimension value="2023"/>
            <ObsValue value="100"/>
        </Obs>"""

        elem = ET.fromstring(xml_content)
        obs_data = self.converter._extract_observation_from_element(elem)

        self.assertIsNotNone(obs_data)
        self.assertIsInstance(obs_data, dict)


class TestConverterFactory(unittest.TestCase):
    """Test cases for ConverterFactory."""

    def test_create_unsupported_converter(self):
        """Test that creating unsupported converter raises error."""
        with self.assertRaises(ValueError):
            ConverterFactory.create_converter("csv")

    def test_create_another_unsupported_converter(self):
        """Test that creating another unsupported converter raises error."""
        with self.assertRaises(ValueError):
            ConverterFactory.create_converter("json")

    def test_unsupported_target(self):
        """Test error handling for unsupported target."""
        with self.assertRaises(ValueError):
            ConverterFactory.create_converter("unsupported")

    def test_get_available_targets(self):
        """Test getting list of available targets."""
        targets = ConverterFactory.get_available_targets()
        self.assertEqual(len(targets), 0)  # No converters registered in MVP

    def test_is_target_supported(self):
        """Test checking if target is supported."""
        targets = ConverterFactory.get_available_targets()
        if targets:
            self.assertTrue(ConverterFactory.is_target_supported(targets[0]))
        self.assertFalse(ConverterFactory.is_target_supported("unsupported"))


if __name__ == "__main__":
    unittest.main()
