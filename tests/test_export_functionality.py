"""
Test suite for Issue #150 - Universal data export functionality.
Tests all export formats, filtering, and streaming capabilities.
"""

import json
from io import BytesIO
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.export.data_access import ExportDataAccess
from src.export.streaming_exporter import StreamingExporter
from src.export.universal_exporter import UniversalExporter


class TestUniversalExporter:
    """Test the UniversalExporter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = UniversalExporter()

        # Create test DataFrame
        self.test_data = pd.DataFrame(
            {
                "Time": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "Value": [100, 200, 300],
                "Category": ["A", "B", "C"],
                "TERRITORIO": ["IT", "IT", "IT"],
            }
        )

    def test_csv_export(self):
        """Test CSV export functionality."""
        result = self.exporter.export_dataframe(self.test_data, "csv", "test_dataset")

        assert isinstance(result, str)
        assert "Time,Value,Category,TERRITORIO" in result
        assert "2023-01-01,100,A,IT" in result
        assert result.count("\n") == 4  # Header + 3 data rows + final newline

    def test_json_export(self):
        """Test JSON export functionality."""
        result = self.exporter.export_dataframe(self.test_data, "json", "test_dataset")

        assert isinstance(result, str)
        data = json.loads(result)

        # Check metadata
        assert data["metadata"]["dataset_id"] == "test_dataset"
        assert data["metadata"]["total_records"] == 3
        assert set(data["metadata"]["columns"]) == {
            "Time",
            "Value",
            "Category",
            "TERRITORIO",
        }

        # Check data
        assert len(data["data"]) == 3
        assert data["data"][0]["Value"] == 100

    def test_parquet_export(self):
        """Test Parquet export functionality."""
        result = self.exporter.export_dataframe(
            self.test_data, "parquet", "test_dataset"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify we can read the parquet data back
        buffer = BytesIO(result)
        read_df = pd.read_parquet(buffer)

        assert len(read_df) == 3
        assert list(read_df.columns) == list(self.test_data.columns)

    def test_column_filtering(self):
        """Test column filtering functionality."""
        result = self.exporter.export_dataframe(
            self.test_data, "csv", "test_dataset", columns=["Time", "Value"]
        )

        assert "Time,Value" in result
        assert "Category" not in result
        assert "TERRITORIO" not in result

    def test_date_filtering(self):
        """Test date range filtering."""
        # Convert Time column to datetime for proper filtering
        test_data = self.test_data.copy()
        test_data["Time"] = pd.to_datetime(test_data["Time"])

        result = self.exporter.export_dataframe(
            test_data,
            "csv",
            "test_dataset",
            start_date="2023-01-02",
            end_date="2023-01-02",
        )

        # Should only include the middle row
        lines = result.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row
        assert "200" in result

    def test_limit_filtering(self):
        """Test row limit functionality."""
        result = self.exporter.export_dataframe(
            self.test_data, "csv", "test_dataset", limit=2
        )

        lines = result.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames."""
        empty_df = pd.DataFrame()

        csv_result = self.exporter.export_dataframe(empty_df, "csv", "empty_dataset")
        assert csv_result == ""

        json_result = self.exporter.export_dataframe(empty_df, "json", "empty_dataset")
        json_data = json.loads(json_result)
        assert json_data["metadata"]["total_records"] == 0
        assert json_data["data"] == []

    def test_unsupported_format(self):
        """Test error handling for unsupported formats."""
        with pytest.raises(ValueError, match="Unsupported format"):
            self.exporter.export_dataframe(self.test_data, "xml", "test_dataset")

    def test_content_types(self):
        """Test content type detection."""
        assert self.exporter.get_content_type("csv") == "text/csv"
        assert self.exporter.get_content_type("json") == "application/json"
        assert self.exporter.get_content_type("parquet") == "application/octet-stream"

    def test_file_extensions(self):
        """Test file extension detection."""
        assert self.exporter.get_file_extension("csv") == ".csv"
        assert self.exporter.get_file_extension("json") == ".json"
        assert self.exporter.get_file_extension("parquet") == ".parquet"


class TestStreamingExporter:
    """Test the StreamingExporter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = StreamingExporter(chunk_size=2)  # Small chunk for testing

        # Create larger test DataFrame
        self.test_data = pd.DataFrame(
            {
                "Time": [f"2023-01-{i:02d}" for i in range(1, 11)],
                "Value": list(range(100, 200, 10)),
                "Category": [chr(65 + (i % 3)) for i in range(10)],  # A, B, C pattern
            }
        )

    def test_csv_streaming_response(self):
        """Test CSV streaming response creation."""
        response = self.exporter.stream_csv_response(
            self.test_data, "test_dataset", "test.csv"
        )

        assert response.media_type == "text/csv"
        assert "filename=test.csv" in response.headers["Content-Disposition"]

        # Test the generator (convert async generator to list for testing)
        content = ""
        import asyncio

        async def collect_chunks():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect_chunks())
        content = "".join(chunks)

        assert "Time,Value,Category" in content
        assert content.count("\n") == 11  # Header + 10 data rows + final newline

    def test_json_streaming_response(self):
        """Test JSON streaming response creation."""
        response = self.exporter.stream_json_response(
            self.test_data, "test_dataset", "test.json"
        )

        assert response.media_type == "application/json"
        assert "filename=test.json" in response.headers["Content-Disposition"]

        # Test the generator produces valid JSON
        content = ""
        import asyncio

        async def collect_chunks():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect_chunks())
        content = "".join(chunks)

        data = json.loads(content)
        assert data["metadata"]["total_records"] == 10
        assert len(data["data"]) == 10

    def test_parquet_streaming_response(self):
        """Test Parquet streaming response creation."""
        response = self.exporter.stream_parquet_response(
            self.test_data, "test_dataset", "test.parquet"
        )

        assert response.media_type == "application/octet-stream"
        assert "filename=test.parquet" in response.headers["Content-Disposition"]

        # Collect all chunks
        content = b""
        import asyncio

        async def collect_chunks():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect_chunks())
        content = b"".join(chunks)

        # Verify we can read the parquet data
        buffer = BytesIO(content)
        read_df = pd.read_parquet(buffer)
        assert len(read_df) == 10

    def test_empty_dataframe_streaming(self):
        """Test streaming with empty DataFrame."""
        empty_df = pd.DataFrame()

        response = self.exporter.stream_csv_response(empty_df, "empty_dataset")

        content = ""
        import asyncio

        async def collect_chunks():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect_chunks())
        content = "".join(chunks)

        # Should handle empty data gracefully
        assert content == ""


class TestExportDataAccess:
    """Test the ExportDataAccess class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.data_access = ExportDataAccess()

    def test_get_dataset_data_with_mock(self):
        """Test dataset data retrieval with proper mocking."""
        # Mock the repository methods properly
        with (
            patch.object(
                self.data_access.repository, "get_dataset_complete"
            ) as mock_info,
            patch.object(
                self.data_access.repository, "execute_analytics_query"
            ) as mock_query,
        ):
            # Setup mocks
            mock_info.return_value = {"name": "Test Dataset"}
            mock_query.return_value = pd.DataFrame(
                {"Time": ["2023-01-01", "2023-01-02"], "Value": [100, 200]}
            )

            # Test data retrieval
            df = self.data_access.get_dataset_data("test_dataset")

            assert not df.empty
            assert len(df) == 2
            assert "Time" in df.columns
            assert "Value" in df.columns

    @patch("src.export.data_access.get_unified_repository")
    def test_dataset_not_found(self, mock_get_repo):
        """Test handling of non-existent dataset."""
        mock_repo = Mock()
        mock_repo.get_dataset_complete.return_value = None
        mock_get_repo.return_value = mock_repo

        df = self.data_access.get_dataset_data("nonexistent_dataset")

        assert df.empty

    def test_build_export_query(self):
        """Test SQL query building."""
        query = self.data_access._build_export_query(
            "test_dataset",
            columns=["Time", "Value"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            limit=1000,
        )

        assert "SELECT Time, Value FROM dataset_test_dataset" in query
        assert "WHERE Time >= '2023-01-01'" in query
        assert "AND Time <= '2023-12-31'" in query
        assert "LIMIT 1000" in query

    def test_estimate_export_size_with_mock(self):
        """Test export size estimation with proper mocking."""
        with patch.object(
            self.data_access.repository, "execute_analytics_query"
        ) as mock_query:
            mock_query.return_value = pd.DataFrame({"row_count": [10000]})

            size_info = self.data_access.estimate_export_size("test_dataset")

            assert size_info["row_count"] == 10000
            assert "estimated_sizes" in size_info
            assert not size_info["recommended_streaming"]  # < 50k threshold

    def test_large_dataset_streaming_recommendation_with_mock(self):
        """Test streaming recommendation for large datasets."""
        with patch.object(
            self.data_access.repository, "execute_analytics_query"
        ) as mock_query:
            mock_query.return_value = pd.DataFrame({"row_count": [75000]})

            size_info = self.data_access.estimate_export_size("large_dataset")

            assert size_info["row_count"] == 75000
            assert size_info["recommended_streaming"]  # > 50k threshold


# Integration test placeholder
class TestExportIntegration:
    """Integration tests for complete export workflow."""

    @pytest.mark.integration
    @patch("src.export.data_access.get_unified_repository")
    def test_full_export_workflow(self, mock_get_repo):
        """Test complete export workflow from API to file."""
        # Mock repository with test data
        mock_repo = Mock()
        mock_repo.get_dataset_complete.return_value = {"name": "Test Dataset"}
        mock_repo.execute_analytics_query.return_value = pd.DataFrame(
            {
                "Time": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "Value": [100, 200, 300],
                "TERRITORIO": ["IT", "IT", "IT"],
            }
        )
        mock_get_repo.return_value = mock_repo

        # Test data access
        data_access = ExportDataAccess()
        df = data_access.get_dataset_data("integration_test")

        # Test export
        exporter = UniversalExporter()
        csv_result = exporter.export_dataframe(df, "csv", "integration_test")

        # Verify end-to-end functionality
        assert "Time,Value,TERRITORIO" in csv_result
        assert "2023-01-01,100,IT" in csv_result
        assert len(csv_result.split("\n")) == 5  # Header + 3 rows + empty line
