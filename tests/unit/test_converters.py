"""
Unit tests for data conversion functionality.
"""
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest


class TestDataConversion:
    """Test data conversion functionality."""

    def test_xml_to_dataframe_basic(self):
        """Test basic XML to DataFrame conversion."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                           xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
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

        root = ET.fromstring(xml_content)

        # Test XML parsing
        assert root is not None

        # Test namespace handling
        namespaces = {
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
            "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
        }

        dataset = root.find(".//message:DataSet", namespaces)
        assert dataset is not None

        series = dataset.find(".//generic:Series", namespaces)
        assert series is not None

        # Extract dimensions and values
        dimensions = {}
        for value in series.findall(".//generic:Value", namespaces):
            dimensions[value.get("id")] = value.get("value")

        assert dimensions["TERRITORIO"] == "IT"
        assert dimensions["ANNO"] == "2024"

        # Extract observations
        obs = series.find(".//generic:Obs", namespaces)
        assert obs is not None

        obs_value = obs.find(".//generic:ObsValue", namespaces)
        assert obs_value.get("value") == "1000000"

    def test_dataframe_to_csv_conversion(self):
        """Test DataFrame to CSV conversion."""
        df = pd.DataFrame(
            {
                "territorio": ["IT", "IT", "IT"],
                "anno": [2022, 2023, 2024],
                "valore": [1000000, 1050000, 1100000],
                "unita_misura": ["numero", "numero", "numero"],
            }
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            # Test CSV export
            df.to_csv(temp_file, index=False, encoding="utf-8")

            # Verify file was created
            assert os.path.exists(temp_file)

            # Read back and verify
            df_read = pd.read_csv(temp_file, encoding="utf-8")
            assert len(df_read) == 3
            assert list(df_read.columns) == [
                "territorio",
                "anno",
                "valore",
                "unita_misura",
            ]
            assert df_read["territorio"].iloc[0] == "IT"
            assert df_read["valore"].iloc[0] == 1000000

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_dataframe_to_excel_conversion(self):
        """Test DataFrame to Excel conversion."""
        df = pd.DataFrame(
            {
                "territorio": ["IT", "IT", "IT"],
                "anno": [2022, 2023, 2024],
                "valore": [1000000, 1050000, 1100000],
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_file = f.name

        try:
            # Test Excel export
            df.to_excel(temp_file, index=False, engine="openpyxl")

            # Verify file was created
            assert os.path.exists(temp_file)

            # Read back and verify
            df_read = pd.read_excel(temp_file, engine="openpyxl")
            assert len(df_read) == 3
            assert list(df_read.columns) == ["territorio", "anno", "valore"]
            assert df_read["territorio"].iloc[0] == "IT"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_dataframe_to_json_conversion(self):
        """Test DataFrame to JSON conversion."""
        df = pd.DataFrame(
            {
                "territorio": ["IT", "IT"],
                "anno": [2023, 2024],
                "valore": [1000000, 1100000],
            }
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Test JSON export
            df.to_json(temp_file, orient="records", indent=2, force_ascii=False)

            # Verify file was created
            assert os.path.exists(temp_file)

            # Read back and verify
            with open(temp_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) == 2
            assert data[0]["territorio"] == "IT"
            assert data[0]["anno"] == 2023
            assert data[0]["valore"] == 1000000

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_dataframe_to_parquet_conversion(self):
        """Test DataFrame to Parquet conversion."""
        df = pd.DataFrame(
            {
                "territorio": ["IT", "IT"],
                "anno": [2023, 2024],
                "valore": [1000000, 1100000],
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            temp_file = f.name

        try:
            # Test Parquet export
            df.to_parquet(temp_file, index=False, engine="pyarrow")

            # Verify file was created
            assert os.path.exists(temp_file)

            # Read back and verify
            df_read = pd.read_parquet(temp_file, engine="pyarrow")
            assert len(df_read) == 2
            assert list(df_read.columns) == ["territorio", "anno", "valore"]
            assert df_read["territorio"].iloc[0] == "IT"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_data_validation_and_cleaning(self):
        """Test data validation and cleaning functions."""
        # Test with dirty data
        df = pd.DataFrame(
            {
                "territorio": ["IT", "IT", None, "IT"],
                "anno": [2023, 2024, 2023, "invalid"],
                "valore": [1000000, None, 1100000, 1200000],
            }
        )

        # Test null value detection
        null_counts = df.isnull().sum()
        assert null_counts["territorio"] == 1
        assert null_counts["valore"] == 1

        # Test data cleaning
        df_clean = df.dropna()
        assert (
            len(df_clean) == 2
        )  # Two rows remain (row with 'invalid' is kept by dropna)

        # Test data type conversion
        df_clean = df.copy()
        df_clean = df_clean.dropna()
        df_clean["anno"] = pd.to_numeric(df_clean["anno"], errors="coerce")
        df_clean = df_clean.dropna()

        assert len(df_clean) == 1
        assert df_clean["anno"].dtype in ["int64", "float64"]

    def test_metadata_extraction(self):
        """Test metadata extraction from XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
            <message:Header>
                <message:ID>DCIS_POPRES1</message:ID>
                <message:Test>false</message:Test>
                <message:Prepared>2025-01-01T10:00:00</message:Prepared>
                <message:Sender id="IT1"/>
            </message:Header>
            <message:DataSet>
                <!-- Data content -->
            </message:DataSet>
        </message:GenericData>"""

        root = ET.fromstring(xml_content)

        # Extract metadata
        namespaces = {
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
        }

        header = root.find(".//message:Header", namespaces)
        assert header is not None

        dataset_id = header.find(".//message:ID", namespaces)
        assert dataset_id is not None
        assert dataset_id.text == "DCIS_POPRES1"

        prepared = header.find(".//message:Prepared", namespaces)
        assert prepared is not None
        assert "2025-01-01" in prepared.text

        sender = header.find(".//message:Sender", namespaces)
        assert sender is not None
        assert sender.get("id") == "IT1"

    def test_category_classification(self):
        """Test dataset category classification."""
        datasets = [
            {
                "id": "101_12",
                "name": "Popolazione residente",
                "description": "Dati demografici popolazione",
            },
            {
                "id": "163_156",
                "name": "PIL regionale",
                "description": "Prodotto interno lordo economia",
            },
            {
                "id": "151_1176",
                "name": "Tasso di occupazione",
                "description": "Dati sul lavoro e occupazione",
            },
        ]

        category_keywords = {
            "popolazione": ["popolazione", "demografic", "residente"],
            "economia": ["pil", "economia", "gdp"],
            "lavoro": ["lavoro", "occupazione", "employment"],
        }

        # Test categorization logic
        for dataset in datasets:
            text = (dataset["name"] + " " + dataset["description"]).lower()

            best_category = None
            best_score = 0

            for category, keywords in category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score > best_score:
                    best_score = score
                    best_category = category

            dataset["category"] = best_category or "altri"
            dataset["score"] = best_score

        # Verify categorization
        assert datasets[0]["category"] == "popolazione"
        assert datasets[1]["category"] == "economia"
        assert datasets[2]["category"] == "lavoro"

        assert datasets[0]["score"] > 0
        assert datasets[1]["score"] > 0
        assert datasets[2]["score"] > 0

    def test_file_format_validation(self):
        """Test file format validation."""
        # Test valid formats
        valid_formats = ["csv", "excel", "json", "parquet"]

        for format_type in valid_formats:
            assert format_type in ["csv", "excel", "json", "parquet"]

        # Test format-specific validation
        test_data = {
            "territorio": ["IT", "IT"],
            "anno": [2023, 2024],
            "valore": [1000000, 1100000],
        }

        df = pd.DataFrame(test_data)

        # CSV validation
        csv_string = df.to_csv(index=False)
        assert "territorio,anno,valore" in csv_string
        assert "IT,2023,1000000" in csv_string

        # JSON validation
        json_string = df.to_json(orient="records")
        json_data = json.loads(json_string)
        assert len(json_data) == 2
        assert json_data[0]["territorio"] == "IT"

    def test_conversion_summary_generation(self):
        """Test conversion summary generation."""
        conversion_results = {
            "successful_datasets": ["101_12", "163_156"],
            "failed_datasets": ["999_999"],
            "files_generated": {
                "csv_files": 2,
                "excel_files": 2,
                "json_files": 2,
                "parquet_files": 1,
            },
        }

        total_datasets = len(conversion_results["successful_datasets"]) + len(
            conversion_results["failed_datasets"]
        )
        success_rate = (
            len(conversion_results["successful_datasets"]) / total_datasets
        ) * 100

        summary = {
            "total_datasets": total_datasets,
            "successful_conversions": len(conversion_results["successful_datasets"]),
            "failed_conversions": len(conversion_results["failed_datasets"]),
            "success_rate": f"{success_rate:.1f}%",
            "files_generated": conversion_results["files_generated"],
        }

        assert summary["total_datasets"] == 3
        assert summary["successful_conversions"] == 2
        assert summary["failed_conversions"] == 1
        assert summary["success_rate"] == "66.7%"
        assert summary["files_generated"]["csv_files"] == 2
