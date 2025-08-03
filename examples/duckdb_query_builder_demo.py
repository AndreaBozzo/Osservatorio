"""DuckDB Query Builder Usage Examples.

This script demonstrates how to use the DuckDB Query Builder for ISTAT analytics:
- Basic query building with fluent interface
- ISTAT-specific query patterns
- Query caching for performance
- Complex analytical queries
- Error handling best practices
"""

from src.database.duckdb import (
    DuckDBQueryBuilder,
    FilterOperator,
    QueryCache,
    create_query_builder,
)


def basic_query_examples():
    """Demonstrate basic query building patterns."""
    print("=== Basic Query Examples ===")

    # Create query builder
    builder = create_query_builder()

    # Example 1: Simple SELECT
    print("\n1. Simple SELECT query:")
    sql, params = (
        builder.select("id", "name", "value")
        .from_table("users")
        .where("active", FilterOperator.EQ, True)
        .order_by("name")
        .limit(10)
        .build_sql()
    )

    print(f"SQL: {sql}")
    print(f"Params: {params}")

    # Example 2: Query with JOINs
    print("\n2. Query with JOINs:")
    sql, params = (
        builder.select("u.name", "p.title", "c.name as category")
        .from_table("users u")
        .join("posts p", "u.id = p.user_id", "LEFT")
        .join("categories c", "p.category_id = c.id", "INNER")
        .where("u.created_at", FilterOperator.GT, "2023-01-01")
        .where_in("p.status", ["published", "featured"])
        .order_by("u.name")
        .build_sql()
    )

    print(f"SQL: {sql}")
    print(f"Params: {params}")

    # Example 3: Aggregate query
    print("\n3. Aggregate query with GROUP BY:")
    sql, params = (
        builder.select("category", "COUNT(*) as post_count", "AVG(views) as avg_views")
        .from_table("posts")
        .where_between("created_at", "2023-01-01", "2023-12-31")
        .group_by("category")
        .having("COUNT(*)", FilterOperator.GT, 10)
        .order_by("avg_views", "DESC")
        .build_sql()
    )

    print(f"SQL: {sql}")
    print(f"Params: {params}")


def istat_specific_examples():
    """Demonstrate ISTAT-specific query patterns."""
    print("\n=== ISTAT-Specific Query Examples ===")

    builder = create_query_builder()

    # Example 1: Time series analysis
    print("\n1. Time Series Analysis:")
    sql, params = (
        builder.select_time_series("DCIS_POPRES1")  # Population dataset
        .year_range(2020, 2023)
        .territories(["IT", "ITC1", "ITF1"])  # Italy, Lombardy, Campania
        .build_sql()
    )

    print(f"SQL: {sql[:200]}...")  # Truncated for readability
    print(f"Params: {params}")

    # Example 2: Territory comparison
    print("\n2. Territory Comparison:")
    sql, params = (
        builder.select_territory_comparison("POP_TOT", 2023)
        .territories(["ITC1", "ITC4", "ITF1"])  # Compare specific regions
        .build_sql()
    )

    print(f"SQL: {sql[:200]}...")
    print(f"Params: {params}")

    # Example 3: Category trends
    print("\n3. Category Trends Analysis:")
    sql, params = (
        builder.select_category_trends("popolazione").year_range(2015, 2023).build_sql()
    )

    print(f"SQL: {sql[:200]}...")
    print(f"Params: {params}")


def caching_examples():
    """Demonstrate query caching capabilities."""
    print("\n=== Query Caching Examples ===")

    # Create cache with custom settings
    cache = QueryCache(default_ttl=600, max_size=1000)  # 10-minute TTL, 1000 entries
    builder = DuckDBQueryBuilder(cache=cache)

    # Note: These examples show query building, not execution
    # In real usage, you would call .execute() to run the query

    print("\n1. Query with custom cache TTL:")
    sql, params = (
        builder.select("*")
        .from_table("large_dataset")
        .where("year", FilterOperator.EQ, 2023)
        .cache_for(1800)  # Cache for 30 minutes
        .build_sql()
    )

    print("Query built with 30-minute cache TTL")

    # Example of cache statistics
    stats = cache.get_stats()
    print("\nCache Statistics:")
    print(f"  Hit rate: {stats['hit_rate_percent']:.1f}%")
    print(f"  Cache size: {stats['cache_size']}/{stats['max_size']}")
    print(f"  Total hits: {stats['hits']}")
    print(f"  Total misses: {stats['misses']}")


def advanced_analytical_queries():
    """Demonstrate advanced analytical query patterns."""
    print("\n=== Advanced Analytical Queries ===")

    builder = create_query_builder()

    # Example 1: Complex demographic analysis
    print("\n1. Complex Demographic Analysis:")
    sql, params = (
        builder.select(
            "d.year",
            "d.territory_code",
            "d.territory_name",
            "AVG(CASE WHEN d.measure_code = 'POP_MALE' THEN o.obs_value END) as male_pop",
            "AVG(CASE WHEN d.measure_code = 'POP_FEMALE' THEN o.obs_value END) as female_pop",
            "COUNT(DISTINCT d.dataset_id) as dataset_count",
        )
        .from_table("main.istat_datasets d")
        .join("main.istat_observations o", "d.id = o.dataset_row_id")
        .join("main.dataset_metadata m", "d.dataset_id = m.dataset_id")
        .where("m.category", FilterOperator.EQ, "popolazione")
        .where_in("d.measure_code", ["POP_MALE", "POP_FEMALE"])
        .where_between("d.year", 2020, 2023)
        .where_not_null("o.obs_value")
        .group_by("d.year", "d.territory_code", "d.territory_name")
        .having("COUNT(DISTINCT d.dataset_id)", FilterOperator.GT, 1)
        .order_by("d.year", "DESC")
        .order_by("male_pop", "DESC")
        .limit(100)
        .build_sql()
    )

    print(f"SQL length: {len(sql)} characters")
    print(f"Parameters: {len(params)} params")

    # Example 2: Year-over-year growth analysis
    print("\n2. Year-over-Year Growth Analysis:")
    sql, params = (
        builder.select(
            "current.territory_code",
            "current.territory_name",
            "current.year",
            "current.obs_value as current_value",
            "previous.obs_value as previous_value",
            "((current.obs_value - previous.obs_value) / previous.obs_value * 100) as growth_rate",
        )
        .from_table("main.istat_observations current")
        .join("main.istat_datasets d1", "current.dataset_row_id = d1.id")
        .join(
            "main.istat_observations previous",
            "current.dataset_id = previous.dataset_id AND current.territory_code = previous.territory_code",
        )
        .join("main.istat_datasets d2", "previous.dataset_row_id = d2.id")
        .where("d1.year", FilterOperator.EQ, 2023)
        .where("d2.year", FilterOperator.EQ, 2022)
        .where_not_null("current.obs_value")
        .where_not_null("previous.obs_value")
        .where("previous.obs_value", FilterOperator.GT, 0)  # Avoid division by zero
        .order_by("growth_rate", "DESC")
        .limit(50)
        .build_sql()
    )

    print(f"SQL length: {len(sql)} characters")
    print(f"Parameters: {len(params)} params")


def query_optimization_examples():
    """Demonstrate query optimization techniques."""
    print("\n=== Query Optimization Examples ===")

    builder = create_query_builder()

    # Example 1: Using EXPLAIN to analyze query
    print("\n1. Query Analysis with EXPLAIN:")
    sql, params = (
        builder.select("d.territory_code", "AVG(o.obs_value) as avg_value")
        .from_table("main.istat_datasets d")
        .join("main.istat_observations o", "d.id = o.dataset_row_id")
        .where("d.year", FilterOperator.EQ, 2023)
        .group_by("d.territory_code")
        .explain()  # Add EXPLAIN to analyze query plan
        .build_sql()
    )

    print("Query with EXPLAIN enabled")
    print(f"SQL starts with: {sql[:50]}...")

    # Example 2: Optimized query with proper indexing hints
    print("\n2. Optimized Query Structure:")
    sql, params = (
        builder.select(
            "d.dataset_id",
            "d.year",
            "COUNT(*) as observation_count",
            "AVG(o.obs_value) as avg_value",
        )
        .from_table("main.istat_datasets d")
        .join("main.istat_observations o", "d.id = o.dataset_row_id")
        .where(
            "d.year", FilterOperator.BETWEEN, [2020, 2023]
        )  # Range query on indexed column
        .where(
            "d.dataset_id", FilterOperator.IN, ["DCIS_POPRES1", "DCIS_POPRES2"]
        )  # IN query
        .where_not_null("o.obs_value")
        .group_by("d.dataset_id", "d.year")
        .having("COUNT(*)", FilterOperator.GT, 100)  # Filter after aggregation
        .order_by("d.year")  # Order by indexed column
        .order_by("avg_value", "DESC")
        .build_sql()
    )

    print("Optimized query structure created")


def error_handling_examples():
    """Demonstrate error handling and validation."""
    print("\n=== Error Handling Examples ===")

    builder = create_query_builder()

    # Example 1: Validation errors
    print("\n1. Validation Error Examples:")

    try:
        # This should fail - no SELECT columns
        builder.from_table("users").build_sql()
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")

    try:
        # This should fail - no FROM table
        builder.select("id").build_sql()
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")

    try:
        # This should fail - negative limit
        builder.limit(-5)
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")

    # Example 2: Safe parameter handling
    print("\n2. Safe Parameter Handling:")

    # All values are properly parameterized
    sql, params = (
        builder.select("*")
        .from_table("users")
        .where("name", FilterOperator.LIKE, "%admin%")  # Safe parameterization
        .where_in("role", ["admin", "moderator"])  # Safe IN clause
        .where_between("created_at", "2023-01-01", "2023-12-31")  # Safe BETWEEN
        .build_sql()
    )

    print("✓ All parameters properly escaped and safe")
    print(f"Parameters: {params}")


def helper_method_examples():
    """Demonstrate convenience helper methods."""
    print("\n=== Helper Method Examples ===")

    builder = create_query_builder()

    # Example 1: Convenience methods
    print("\n1. Convenience Methods:")

    # Using helper methods instead of generic where()
    sql, params = (
        builder.select("*")
        .from_table("products")
        .where_in("category", ["electronics", "books"])  # Helper for IN
        .where_between("price", 10.00, 100.00)  # Helper for BETWEEN
        .where_null("discontinued_at")  # Helper for IS NULL
        .where_not_null("description")  # Helper for IS NOT NULL
        .build_sql()
    )

    print("Helper methods used successfully")

    # Example 2: Query execution helpers
    print("\n2. Query Execution Helpers:")

    # Note: These would work with a real database connection
    # count_query = builder.select("*").from_table("products").count()
    # first_row = builder.select("*").from_table("products").first()
    # exists_check = builder.select("*").from_table("products").where("id", FilterOperator.EQ, 123).exists()

    print("✓ count(), first(), and exists() methods available")


def performance_tips():
    """Demonstrate performance optimization tips."""
    print("\n=== Performance Tips ===")

    print(
        """
Performance Optimization Guidelines:

1. **Use Caching Effectively:**
   - Set appropriate TTL based on data freshness requirements
   - Use longer cache times for reference data (territories, categories)
   - Use shorter cache times for frequently changing data

2. **Query Structure Optimization:**
   - Filter early and often (WHERE clauses)
   - Use indexed columns in WHERE and JOIN conditions
   - Limit result sets with LIMIT when possible
   - Use specific column names instead of SELECT *

3. **ISTAT Data Patterns:**
   - Year-based filtering is highly optimized
   - Territory code filtering uses indexes
   - Dataset ID filtering is very fast
   - Combine filters for maximum effectiveness

4. **Caching Strategy:**
   - Common queries: 10-30 minutes TTL
   - Reference data: 1-24 hours TTL
   - Real-time analytics: 1-5 minutes TTL
   - Historical analysis: 1+ hours TTL

5. **Memory Management:**
   - Use reasonable cache sizes (default: 1000 entries)
   - Monitor cache hit rates (aim for >50%)
   - Clear cache periodically if needed
    """
    )


def main():
    """Run all examples."""
    print("DuckDB Query Builder Usage Examples")
    print("=" * 50)

    try:
        basic_query_examples()
        istat_specific_examples()
        caching_examples()
        advanced_analytical_queries()
        query_optimization_examples()
        error_handling_examples()
        helper_method_examples()
        performance_tips()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
