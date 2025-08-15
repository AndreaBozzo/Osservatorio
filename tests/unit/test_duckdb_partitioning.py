"""Partitioning DuckDB functionality tests.

Tests partitioning strategies DuckDB functionality without the complex manager wrapper.
"""

import pytest

from src.database.duckdb.partitioning import (
    HybridPartitionStrategy,
    # PartitionManager,
    PartitionStrategy,
    TerritoryPartitionStrategy,
    YearPartitionStrategy,
)


class TestPartitionStrategy:
    def test_get_partition_key(self):
        """Test generation of partition key from data row."""
        strategy = PartitionStrategy(
            name="year_territory_partition", columns=["year", "territory_code"]
        )
        row = {"year": 2020, "territory_code": "IT"}
        assert strategy.get_partition_key(row) == "year_2020_territory_code_IT"

    def test_get_partition_filter(self):
        """Test generation of partition filter from data row."""
        strategy = PartitionStrategy(
            name="year_territory_partition", columns=["year", "territory_code"]
        )
        filters = strategy.get_partition_filter(year=2020, territory_code="IT")
        assert filters == "year = 2020 AND territory_code = 'IT'"


class TestYearPartitionStrategy:
    def test_get_partition_key(self):
        """Test year-based partition key generation."""
        strategy = YearPartitionStrategy()
        row = {"year": 2020}
        assert strategy.get_partition_key(row) == "year_2020"

    def test_get_partition_filter(self):
        """Test year-based partition filter generation."""
        strategy = YearPartitionStrategy()
        filters = strategy.get_partition_filter(start_year=2020)
        assert filters == "year >= 2020"
        filters = strategy.get_partition_filter(end_year=2020)
        assert filters == "year <= 2020"


class TestTerritoryPartitionStrategy:
    def test_get_partition_key(self):
        """Test territory-based partition key generation."""

        strategy = TerritoryPartitionStrategy()
        row = {"territory_code": "IT"}
        assert strategy.get_partition_key(row) == "territory_italy_IT"

    def test_get_partition_filter(self):
        """Test territory-based partition filter generation."""
        strategy = TerritoryPartitionStrategy()
        filters = strategy.get_partition_filter(territories=["IT"])
        assert filters == "territory_code IN ('IT')"


class TestHybridPartitionStrategy:
    def test_get_partition_key(self):
        """Test hybrid-based partition key generation."""

        strategy = HybridPartitionStrategy()
        row = {"year": 2020, "territory_code": "IT"}
        assert strategy.get_partition_key(row) == "hybrid_2020s_IT"

    def test_get_partition_filter(self):
        """Test hybrid-based partition filter generation."""

        strategy = HybridPartitionStrategy()
        filters = strategy.get_partition_filter(start_year=2020, territories=["IT"])
        assert filters == "year >= 2020 AND territory_code IN ('IT')"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
