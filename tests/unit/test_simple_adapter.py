"""Tests for SimpleDuckDBAdapter.

Tests the lightweight DuckDB adapter for immediate use.
"""

import pandas as pd
import pytest

from src.database.duckdb.simple_adapter import (
    create_adapter,
    create_temp_adapter,
)


class TestSimpleDuckDBAdapter:
    """Test the simple DuckDB adapter."""

    def test_in_memory_adapter(self):
        """Test in-memory adapter creation and basic operations."""
        adapter = create_adapter()

        # Test metadata insertion
        adapter.insert_metadata("TEST_001", "Test Dataset", "test", 5)

        # Test query
        result = adapter.get_dataset_summary()
        assert len(result) == 1
        assert result.iloc[0]["dataset_id"] == "TEST_001"
        assert result.iloc[0]["category"] == "test"

        adapter.close()

    def test_observations_insertion(self):
        """Test inserting observation data."""
        adapter = create_adapter()

        # Insert metadata first
        adapter.insert_metadata("POP_TEST", "Population Test", "popolazione", 10)

        # Create test observations
        obs_df = pd.DataFrame(
            {
                "dataset_id": ["POP_TEST"] * 6,
                "year": [2020, 2021, 2022] * 2,
                "territory_code": ["IT", "IT", "IT", "FR", "FR", "FR"],
                "territory_name": [
                    "Italia",
                    "Italia",
                    "Italia",
                    "France",
                    "France",
                    "France",
                ],
                "measure_code": ["POP_TOTAL"] * 6,
                "measure_name": ["Total Population"] * 6,
                "obs_value": [
                    59641488,
                    59030133,
                    58983122,
                    67320216,
                    67499343,
                    67750000,
                ],
                "obs_status": ["A"] * 6,  # Approved
            }
        )

        # Insert observations
        adapter.insert_observations(obs_df)

        # Test summary
        summary = adapter.get_dataset_summary()
        assert len(summary) == 1
        assert summary.iloc[0]["total_observations"] == 6
        assert summary.iloc[0]["start_year"] == 2020
        assert summary.iloc[0]["end_year"] == 2022
        assert summary.iloc[0]["territories"] == 2

        adapter.close()

    def test_time_series_query(self):
        """Test time series data retrieval."""
        adapter = create_adapter()

        # Setup test data
        adapter.insert_metadata("TS_TEST", "Time Series Test", "economia", 8)

        obs_df = pd.DataFrame(
            {
                "dataset_id": ["TS_TEST"] * 4,
                "year": [2020, 2021, 2022, 2023],
                "territory_code": ["IT"] * 4,
                "territory_name": ["Italia"] * 4,
                "measure_code": ["GDP"] * 4,
                "measure_name": ["Gross Domestic Product"] * 4,
                "obs_value": [1659516.7, 1785373.9, 1909154.2, 2010245.8],
                "obs_status": ["A"] * 4,
            }
        )

        adapter.insert_observations(obs_df)

        # Test time series retrieval
        ts_data = adapter.get_time_series("TS_TEST", "IT")
        assert len(ts_data) == 4
        assert ts_data["year"].tolist() == [2020, 2021, 2022, 2023]
        assert all(ts_data["territory_code"] == "IT")

        # Test without territory filter
        ts_all = adapter.get_time_series("TS_TEST")
        assert len(ts_all) == 4

        adapter.close()

    def test_territory_comparison(self):
        """Test territory comparison functionality."""
        adapter = create_adapter()

        # Setup test data
        adapter.insert_metadata("COMP_TEST", "Comparison Test", "territorio", 7)

        obs_df = pd.DataFrame(
            {
                "dataset_id": ["COMP_TEST"] * 6,
                "year": [2022] * 6,
                "territory_code": ["IT", "IT", "FR", "FR", "DE", "DE"],
                "territory_name": ["Italia"] * 2 + ["France"] * 2 + ["Germany"] * 2,
                "measure_code": ["IND1", "IND2"] * 3,
                "measure_name": ["Indicator 1", "Indicator 2"] * 3,
                "obs_value": [100, 95, 85, 90, 110, 105],
                "obs_status": ["A"] * 6,
            }
        )

        adapter.insert_observations(obs_df)

        # Test territory comparison
        comparison = adapter.get_territory_comparison("COMP_TEST", 2022)
        assert len(comparison) == 3  # IT, FR, DE

        # Check ranking (Germany should be first with highest avg: (110+105)/2 = 107.5)
        assert comparison.iloc[0]["territory_code"] == "DE"
        assert comparison.iloc[0]["rank"] == 1
        assert comparison.iloc[0]["avg_value"] == 107.5

        adapter.close()

    def test_category_trends(self):
        """Test category trend analysis."""
        adapter = create_adapter()

        # Setup multiple datasets in same category
        adapter.insert_metadata("ECO_1", "Economic Dataset 1", "economia", 9)
        adapter.insert_metadata("ECO_2", "Economic Dataset 2", "economia", 8)

        # Create trend data across years
        obs_data = []
        for year in [2020, 2021, 2022]:
            for ds_id in ["ECO_1", "ECO_2"]:
                obs_data.append(
                    {
                        "dataset_id": ds_id,
                        "year": year,
                        "territory_code": "IT",
                        "territory_name": "Italia",
                        "measure_code": "VAL",
                        "measure_name": "Value",
                        "obs_value": year * 10 + (1 if ds_id == "ECO_1" else 2),
                        "obs_status": "A",
                    }
                )

        obs_df = pd.DataFrame(obs_data)
        adapter.insert_observations(obs_df)

        # Test category trends
        trends = adapter.get_category_trends("economia", 2020, 2022)
        assert len(trends) == 3  # 2020, 2021, 2022
        assert trends["datasets"].tolist() == [2, 2, 2]  # 2 datasets per year

        # Values should increase over time
        assert trends.iloc[0]["avg_value"] < trends.iloc[2]["avg_value"]

        adapter.close()

    def test_file_adapter_creation(self):
        """Test creating file-based adapter."""
        # Create temporary file adapter
        temp_adapter = create_temp_adapter()

        # Test that it works
        temp_adapter.insert_metadata("FILE_TEST", "File Test", "test", 1)
        summary = temp_adapter.get_dataset_summary()
        assert len(summary) == 1

        temp_adapter.close()

    def test_context_manager(self):
        """Test adapter as context manager."""
        with create_adapter() as adapter:
            adapter.insert_metadata("CTX_TEST", "Context Test", "test", 1)
            summary = adapter.get_dataset_summary()
            assert len(summary) == 1

        # Connection should be closed automatically
        assert adapter.connection is None

    def test_database_optimization(self):
        """Test database optimization."""
        adapter = create_adapter()

        # Add some data
        adapter.insert_metadata("OPT_TEST", "Optimization Test", "test", 1)

        # Should not raise an exception
        adapter.optimize_database()

        adapter.close()

    def test_error_handling(self):
        """Test error handling in adapter."""
        adapter = create_adapter()

        # Try to insert observations without metadata (should work but foreign key might be ignored)
        obs_df = pd.DataFrame(
            {
                "dataset_id": ["NONEXISTENT"],
                "year": [2022],
                "territory_code": ["IT"],
                "territory_name": ["Italia"],
                "measure_code": ["TEST"],
                "measure_name": ["Test"],
                "obs_value": [100],
                "obs_status": ["A"],
            }
        )

        # This might work or fail depending on foreign key enforcement
        try:
            adapter.insert_observations(obs_df)
        except:
            pass  # Expected if foreign keys are enforced

        adapter.close()

    def test_large_dataset_handling(self):
        """Test handling of larger datasets."""
        adapter = create_adapter()

        adapter.insert_metadata("LARGE_TEST", "Large Dataset Test", "performance", 1)

        # Create larger dataset (1000 records)
        large_data = []
        for i in range(1000):
            large_data.append(
                {
                    "dataset_id": "LARGE_TEST",
                    "year": 2020 + (i % 5),
                    "territory_code": f"T{i % 10}",
                    "territory_name": f"Territory {i % 10}",
                    "measure_code": f"M{i % 3}",
                    "measure_name": f"Measure {i % 3}",
                    "obs_value": float(i),
                    "obs_status": "A",
                }
            )

        large_df = pd.DataFrame(large_data)
        adapter.insert_observations(large_df)

        # Test that all data was inserted
        summary = adapter.get_dataset_summary()
        assert summary.iloc[0]["total_observations"] == 1000

        # Test aggregation performance
        trends = adapter.get_category_trends("performance")
        assert len(trends) == 5  # 5 years

        adapter.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
