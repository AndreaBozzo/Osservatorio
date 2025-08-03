"""DuckDB Integration Demo for ISTAT Data Processing.

This script demonstrates how to use the new DuckDB functionality
for high-performance analytics on ISTAT statistical data.
"""

from pathlib import Path

import pandas as pd

# Use proper package imports
try:
    from osservatorio_istat.database.duckdb.simple_adapter import (
        create_adapter,
        create_file_adapter,
    )
except ImportError:
    # Development mode fallback

    # Issue #84: Removed unsafe sys.path manipulation
    from database.duckdb.simple_adapter import create_adapter, create_file_adapter


def demo_basic_functionality():
    """Demo basic DuckDB functionality."""
    print("🚀 DuckDB Basic Functionality Demo")
    print("=" * 50)

    # Create in-memory adapter
    with create_adapter() as adapter:
        # Insert sample ISTAT metadata
        print("\n📊 Creating sample ISTAT datasets...")

        datasets = [
            (
                "DCIS_POPRES1",
                "Popolazione residente per età, sesso e stato civile",
                "popolazione",
                10,
            ),
            ("DCCN_PILN", "Prodotto interno lordo ai prezzi di mercato", "economia", 9),
            ("DCCV_TAXOCCU", "Tasso di occupazione 15-64 anni", "lavoro", 8),
            ("DCIS_MORTALITA1", "Mortalità infantile", "salute", 7),
        ]

        for dataset_id, name, category, priority in datasets:
            adapter.insert_metadata(dataset_id, name, category, priority)

        # Show datasets summary
        summary = adapter.get_dataset_summary()
        print(f"Created {len(summary)} datasets:")
        for _, row in summary.iterrows():
            print(
                f"  • {row['dataset_id']}: {row['category']} (priority: {row['priority']})"
            )

        print("\n✅ Basic functionality working!")


def demo_data_insertion_and_queries():
    """Demo data insertion and analytical queries."""
    print("\n📈 Data Insertion & Analytics Demo")
    print("=" * 50)

    with create_adapter() as adapter:
        # Insert population data
        adapter.insert_metadata("DEMO_POP", "Demo Population Data", "popolazione", 10)

        # Create sample population data
        pop_data = pd.DataFrame(
            {
                "dataset_id": ["DEMO_POP"] * 12,
                "year": [2020, 2021, 2022] * 4,
                "territory_code": [
                    "IT",
                    "IT",
                    "IT",
                    "FR",
                    "FR",
                    "FR",
                    "DE",
                    "DE",
                    "DE",
                    "ES",
                    "ES",
                    "ES",
                ],
                "territory_name": ["Italia"] * 3
                + ["France"] * 3
                + ["Germany"] * 3
                + ["Spain"] * 3,
                "measure_code": ["POP_TOTAL"] * 12,
                "measure_name": ["Total Population"] * 12,
                "obs_value": [
                    59641488,
                    59030133,
                    58983122,  # Italy
                    67320216,
                    67499343,
                    67750000,  # France
                    83166711,
                    83237124,
                    83200000,  # Germany
                    47351567,
                    47398695,
                    47450000,  # Spain
                ],
                "obs_status": ["A"] * 12,  # All approved
            }
        )

        adapter.insert_observations(pop_data)
        print(f"✅ Inserted {len(pop_data)} population observations")

        # Demo time series query
        print("\n📊 Time Series Analysis:")
        ts_data = adapter.get_time_series("DEMO_POP", "IT")
        print("Italy population trend:")
        for _, row in ts_data.iterrows():
            print(f"  {row['year']}: {row['obs_value']:,} inhabitants")

        # Demo territory comparison
        print("\n🌍 Territory Comparison (2022):")
        comparison = adapter.get_territory_comparison("DEMO_POP", 2022)
        for _, row in comparison.iterrows():
            print(
                f"  {row['rank']}. {row['territory_name']}: {row['avg_value']:,.0f} inhabitants"
            )

        print("\n✅ Analytics queries working!")


def demo_category_trends():
    """Demo category trend analysis."""
    print("\n📈 Category Trends Demo")
    print("=" * 50)

    with create_adapter() as adapter:
        # Create multiple economic datasets
        economic_datasets = [
            ("GDP_NOMINAL", "GDP Nominal", "economia", 9),
            ("GDP_REAL", "GDP Real", "economia", 9),
            ("INFLATION", "Inflation Rate", "economia", 8),
        ]

        for dataset_id, name, category, priority in economic_datasets:
            adapter.insert_metadata(dataset_id, name, category, priority)

        # Generate trend data
        economic_data = []
        base_values = {"GDP_NOMINAL": 1800000, "GDP_REAL": 1600000, "INFLATION": 2.1}

        for year in range(2020, 2024):
            for ds_id in ["GDP_NOMINAL", "GDP_REAL", "INFLATION"]:
                growth = (
                    0.03 if "GDP" in ds_id else 0.02
                )  # 3% GDP growth, 2% inflation growth
                value = base_values[ds_id] * ((1 + growth) ** (year - 2020))

                economic_data.append(
                    {
                        "dataset_id": ds_id,
                        "year": year,
                        "territory_code": "IT",
                        "territory_name": "Italia",
                        "measure_code": "MAIN",
                        "measure_name": "Main Indicator",
                        "obs_value": value,
                        "obs_status": "A",
                    }
                )

        econ_df = pd.DataFrame(economic_data)
        adapter.insert_observations(econ_df)
        print(f"✅ Inserted economic data: {len(econ_df)} observations")

        # Analyze trends
        print("\n📊 Economic Category Trends (2020-2023):")
        trends = adapter.get_category_trends("economia", 2020, 2023)
        for _, row in trends.iterrows():
            print(
                f"  {row['year']}: {row['datasets']} datasets, avg value: {row['avg_value']:,.0f}"
            )

        print("\n✅ Trend analysis working!")


def demo_performance():
    """Demo performance with larger dataset."""
    print("\n⚡ Performance Demo")
    print("=" * 50)

    with create_adapter() as adapter:
        adapter.insert_metadata(
            "PERF_TEST", "Performance Test Dataset", "performance", 1
        )

        # Generate 10,000 observations
        print("Generating 10,000 test observations...")
        import time

        large_data = []
        for i in range(10000):
            large_data.append(
                {
                    "dataset_id": "PERF_TEST",
                    "year": 2020 + (i % 5),
                    "territory_code": f"REG_{i % 20:02d}",
                    "territory_name": f"Region {i % 20}",
                    "measure_code": f"IND_{i % 5}",
                    "measure_name": f"Indicator {i % 5}",
                    "obs_value": float(i * 1.5 + (i % 100)),
                    "obs_status": "A",
                }
            )

        large_df = pd.DataFrame(large_data)

        # Time the insertion
        start_time = time.time()
        adapter.insert_observations(large_df)
        insert_time = time.time() - start_time

        print(f"✅ Inserted 10,000 records in {insert_time:.2f} seconds")

        # Time aggregation query
        start_time = time.time()
        summary = adapter.get_dataset_summary()
        query_time = time.time() - start_time

        print(f"✅ Aggregation query completed in {query_time:.3f} seconds")
        print(f"   Total observations: {summary.iloc[0]['total_observations']:,}")
        print(
            f"   Years covered: {summary.iloc[0]['start_year']}-{summary.iloc[0]['end_year']}"
        )
        print(f"   Territories: {summary.iloc[0]['territories']}")

        # Optimize database
        print("\nOptimizing database...")
        start_time = time.time()
        adapter.optimize_database()
        opt_time = time.time() - start_time
        print(f"✅ Database optimization completed in {opt_time:.3f} seconds")


def demo_file_persistence():
    """Demo file-based persistence."""
    print("\n💾 File Persistence Demo")
    print("=" * 50)

    # Create file-based adapter
    file_adapter = create_file_adapter("demo_persistence.duckdb")

    try:
        # Insert data
        file_adapter.insert_metadata("PERSIST_TEST", "Persistence Test", "test", 5)

        test_data = pd.DataFrame(
            {
                "dataset_id": ["PERSIST_TEST"] * 3,
                "year": [2021, 2022, 2023],
                "territory_code": ["IT"] * 3,
                "territory_name": ["Italia"] * 3,
                "measure_code": ["TEST"] * 3,
                "measure_name": ["Test Measure"] * 3,
                "obs_value": [100, 110, 120],
                "obs_status": ["A"] * 3,
            }
        )

        file_adapter.insert_observations(test_data)
        file_adapter.close()

        print("✅ Data saved to file")

        # Reopen and verify
        file_adapter2 = create_file_adapter("demo_persistence.duckdb")
        summary = file_adapter2.get_dataset_summary()

        print(f"✅ Data persisted: {summary.iloc[0]['total_observations']} observations")
        print(f"   Dataset: {summary.iloc[0]['dataset_name']}")

        file_adapter2.close()

    finally:
        # Cleanup
        try:
            db_path = (
                Path(__file__).parent.parent
                / "data"
                / "databases"
                / "demo_persistence.duckdb"
            )
            if db_path.exists():
                db_path.unlink()
                print("🧹 Cleaned up demo database file")
        except Exception:
            pass


def main():
    """Run all demos."""
    print("🦆 DuckDB Integration for ISTAT Data - Complete Demo")
    print("=" * 60)

    try:
        demo_basic_functionality()
        demo_data_insertion_and_queries()
        demo_category_trends()
        demo_performance()
        demo_file_persistence()

        print("\n" + "=" * 60)
        print("🎉 All demos completed successfully!")
        print("\n📋 Summary of DuckDB Integration:")
        print("   ✅ High-performance analytics database")
        print("   ✅ ISTAT-optimized schema")
        print("   ✅ Time series analysis")
        print("   ✅ Territory comparisons")
        print("   ✅ Category trend analysis")
        print("   ✅ Fast bulk data insertion")
        print("   ✅ File persistence")
        print("   ✅ In-memory processing")
        print("\n🚀 Ready for integration with ISTAT data pipeline!")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
