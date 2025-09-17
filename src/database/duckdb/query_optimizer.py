"""Query optimization and indexing strategies for ISTAT DuckDB analytics.

This module provides:
- Optimized query patterns for common analytics
- Index management and recommendations
- Query performance monitoring
- Caching strategies for frequent queries
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import pandas as pd

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .config import get_schema_config
from .manager import DuckDBManager

logger = get_logger(__name__)


class QueryType(Enum):
    """Types of analytical queries for optimization."""

    TIME_SERIES = "time_series"
    TERRITORY_COMPARISON = "territory_comparison"
    CATEGORY_ANALYSIS = "category_analysis"
    TREND_ANALYSIS = "trend_analysis"
    AGGREGATION = "aggregation"
    RANKING = "ranking"


@dataclass
class QueryPerformance:
    """Query performance metrics."""

    query_hash: str
    query_type: QueryType
    execution_time: float
    rows_returned: int
    cache_hit: bool
    execution_plan: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class QueryOptimizer:
    """Advanced query optimizer for ISTAT analytics."""

    def __init__(self, manager: Optional[DuckDBManager] = None):
        """Initialize query optimizer.

        Args:
            manager: Optional DuckDB manager instance
        """
        self.manager = manager or DuckDBManager()
        self.schema_config = get_schema_config()
        self.query_cache: dict[str, Any] = {}  # Simple in-memory cache
        self.performance_log: list[QueryPerformance] = []
        self.cache_ttl = timedelta(minutes=30)

    def create_advanced_indexes(self) -> None:
        """Create advanced indexes for optimal query performance."""
        schema = self.schema_config["main_schema"]

        # Composite indexes for common query patterns
        advanced_indexes = [
            # Time series analysis indexes
            f"""CREATE INDEX IF NOT EXISTS idx_timeseries_composite
               ON {schema}.istat_datasets(dataset_id, year, territory_code, time_period);""",
            # Territory comparison indexes
            f"""CREATE INDEX IF NOT EXISTS idx_territory_year
               ON {schema}.istat_datasets(territory_code, year, measure_code);""",
            # Category analysis indexes
            f"""CREATE INDEX IF NOT EXISTS idx_category_analysis
               ON {schema}.dataset_metadata(category, priority, processing_status);""",
            # Value-based analysis indexes
            f"""CREATE INDEX IF NOT EXISTS idx_observations_value_range
               ON {schema}.istat_observations(dataset_id, obs_value, year);""",
            # Multi-dimensional analysis
            f"""CREATE INDEX IF NOT EXISTS idx_multidim_analysis
               ON {schema}.istat_datasets(dataset_id, year, measure_code, territory_code);""",
            # Quality analysis indexes
            f"""CREATE INDEX IF NOT EXISTS idx_quality_metrics
               ON {schema}.dataset_metadata(data_quality_score, completeness_score, category);""",
        ]

        for index_sql in advanced_indexes:
            try:
                self.manager.execute_statement(index_sql)
                logger.debug("Created advanced index successfully")
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")

    def get_time_series_data(
        self,
        dataset_ids: list[str],
        start_year: int,
        end_year: int,
        territories: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Optimized time series data retrieval.

        Args:
            dataset_ids: List of dataset IDs
            start_year: Start year for time series
            end_year: End year for time series
            territories: Optional list of territory codes

        Returns:
            DataFrame with time series data
        """
        # Generate cache key
        cache_key = f"timeseries_{hash(tuple(dataset_ids))}_{start_year}_{end_year}_{hash(tuple(territories or []))}"

        # Check cache
        cached_result = self._get_cached_result(cache_key, QueryType.TIME_SERIES)
        if cached_result is not None:
            return cached_result

        # Build optimized query
        self.schema_config["main_schema"]
        analytics_schema = self.schema_config["analytics_schema"]

        territory_filter = ""
        if territories:
            territory_list = "', '".join(territories)
            territory_filter = f"AND d.territory_code IN ('{territory_list}')"

        dataset_list = "', '".join(dataset_ids)

        query = f"""
        SELECT
            ts.dataset_id,
            ts.year,
            ts.time_period,
            ts.territory_code,
            ts.territory_name,
            ts.measure_code,
            ts.measure_name,
            ts.obs_value,
            ts.obs_status,
            ts.category,
            ts.unit_of_measure
        FROM {analytics_schema}.time_series ts
        WHERE ts.dataset_id IN ('{dataset_list}')
          AND ts.year BETWEEN {start_year} AND {end_year}
          {territory_filter}
        ORDER BY ts.dataset_id, ts.year, ts.territory_code;
        """

        start_time = time.time()
        result = self.manager.execute_query(query)
        execution_time = time.time() - start_time

        # Cache result
        self._cache_result(cache_key, result, QueryType.TIME_SERIES, execution_time)

        logger.info(
            f"Time series query executed in {execution_time:.3f}s, returned {len(result)} rows"
        )
        return result

    def get_territory_comparison(
        self,
        measure_codes: list[str],
        year: int,
        territories: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Optimized territory comparison query.

        Args:
            measure_codes: List of measure codes to compare
            year: Year for comparison
            territories: Optional list of specific territories

        Returns:
            DataFrame with territory comparison data
        """
        cache_key = f"territory_comp_{hash(tuple(measure_codes))}_{year}_{hash(tuple(territories or []))}"

        cached_result = self._get_cached_result(
            cache_key, QueryType.TERRITORY_COMPARISON
        )
        if cached_result is not None:
            return cached_result

        schema = self.schema_config["main_schema"]

        territory_filter = ""
        if territories:
            territory_list = "', '".join(territories)
            territory_filter = f"AND d.territory_code IN ('{territory_list}')"

        measure_list = "', '".join(measure_codes)

        query = f"""
        WITH territory_stats AS (
            SELECT
                d.territory_code,
                d.territory_name,
                d.measure_code,
                d.measure_name,
                AVG(o.obs_value) as avg_value,
                MIN(o.obs_value) as min_value,
                MAX(o.obs_value) as max_value,
                COUNT(o.obs_value) as obs_count,
                STDDEV(o.obs_value) as std_dev
            FROM {schema}.istat_datasets d
            JOIN {schema}.istat_observations o ON d.id = o.dataset_row_id
            WHERE d.year = {year}
              AND d.measure_code IN ('{measure_list}')
              {territory_filter}
              AND o.obs_value IS NOT NULL
            GROUP BY d.territory_code, d.territory_name, d.measure_code, d.measure_name
        )
        SELECT
            *,
            RANK() OVER (PARTITION BY measure_code ORDER BY avg_value DESC) as value_rank,
            NTILE(4) OVER (PARTITION BY measure_code ORDER BY avg_value) as quartile
        FROM territory_stats
        ORDER BY measure_code, value_rank;
        """

        start_time = time.time()
        result = self.manager.execute_query(query)
        execution_time = time.time() - start_time

        self._cache_result(
            cache_key, result, QueryType.TERRITORY_COMPARISON, execution_time
        )

        logger.info(f"Territory comparison query executed in {execution_time:.3f}s")
        return result

    def get_category_trends(
        self, categories: list[str], start_year: int, end_year: int
    ) -> pd.DataFrame:
        """Optimized category trend analysis.

        Args:
            categories: List of categories to analyze
            start_year: Start year for trend analysis
            end_year: End year for trend analysis

        Returns:
            DataFrame with trend analysis data
        """
        cache_key = f"category_trends_{hash(tuple(categories))}_{start_year}_{end_year}"

        cached_result = self._get_cached_result(cache_key, QueryType.TREND_ANALYSIS)
        if cached_result is not None:
            return cached_result

        schema = self.schema_config["main_schema"]
        category_list = "', '".join(categories)

        query = f"""
        WITH yearly_aggregates AS (
            SELECT
                m.category,
                d.year,
                COUNT(DISTINCT d.dataset_id) as dataset_count,
                COUNT(o.obs_value) as total_observations,
                AVG(o.obs_value) as avg_value,
                MEDIAN(o.obs_value) as median_value,
                STDDEV(o.obs_value) as std_dev
            FROM {schema}.dataset_metadata m
            JOIN {schema}.istat_datasets d ON m.dataset_id = d.dataset_id
            JOIN {schema}.istat_observations o ON d.id = o.dataset_row_id
            WHERE m.category IN ('{category_list}')
              AND d.year BETWEEN {start_year} AND {end_year}
              AND o.obs_value IS NOT NULL
            GROUP BY m.category, d.year
        ),
        trend_calculations AS (
            SELECT
                *,
                LAG(avg_value) OVER (PARTITION BY category ORDER BY year) as prev_avg_value,
                LEAD(avg_value) OVER (PARTITION BY category ORDER BY year) as next_avg_value
            FROM yearly_aggregates
        )
        SELECT
            *,
            CASE
                WHEN prev_avg_value IS NULL THEN NULL
                ELSE ((avg_value - prev_avg_value) / prev_avg_value) * 100
            END as year_over_year_change,
            CASE
                WHEN ROW_NUMBER() OVER (PARTITION BY category ORDER BY year) >= 3 THEN
                    AVG(avg_value) OVER (
                        PARTITION BY category
                        ORDER BY year
                        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                    )
            END as moving_avg_3yr
        FROM trend_calculations
        ORDER BY category, year;
        """

        start_time = time.time()
        result = self.manager.execute_query(query)
        execution_time = time.time() - start_time

        self._cache_result(cache_key, result, QueryType.TREND_ANALYSIS, execution_time)

        logger.info(f"Category trends query executed in {execution_time:.3f}s")
        return result

    def get_top_performers(
        self, category: str, measure_code: str, year: int, limit: int = 10
    ) -> pd.DataFrame:
        """Get top performing territories for a specific measure.

        Args:
            category: Category to analyze
            measure_code: Specific measure code
            year: Year to analyze
            limit: Number of top performers to return

        Returns:
            DataFrame with top performers
        """
        cache_key = f"top_performers_{category}_{measure_code}_{year}_{limit}"

        cached_result = self._get_cached_result(cache_key, QueryType.RANKING)
        if cached_result is not None:
            return cached_result

        schema = self.schema_config["main_schema"]

        query = f"""
        SELECT
            d.territory_code,
            d.territory_name,
            d.measure_code,
            d.measure_name,
            AVG(o.obs_value) as avg_value,
            COUNT(o.obs_value) as obs_count,
            m.unit_of_measure,
            RANK() OVER (ORDER BY AVG(o.obs_value) DESC) as rank
        FROM {schema}.dataset_metadata m
        JOIN {schema}.istat_datasets d ON m.dataset_id = d.dataset_id
        JOIN {schema}.istat_observations o ON d.id = o.dataset_row_id
        WHERE m.category = '{category}'
          AND d.measure_code = '{measure_code}'
          AND d.year = {year}
          AND o.obs_value IS NOT NULL
        GROUP BY d.territory_code, d.territory_name, d.measure_code,
                 d.measure_name, m.unit_of_measure
        ORDER BY avg_value DESC
        LIMIT {limit};
        """

        start_time = time.time()
        result = self.manager.execute_query(query)
        execution_time = time.time() - start_time

        self._cache_result(cache_key, result, QueryType.RANKING, execution_time)

        logger.info(f"Top performers query executed in {execution_time:.3f}s")
        return result

    def analyze_query_performance(self, query: str) -> dict[str, Any]:
        """Analyze query performance and provide optimization suggestions.

        Args:
            query: SQL query to analyze

        Returns:
            Dictionary with performance analysis
        """
        try:
            # Get query execution plan
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            plan_result = self.manager.execute_query(explain_query)

            # Extract performance metrics
            if not plan_result.empty:
                plan_data = plan_result.iloc[0, 0]  # First column of first row

                analysis = {
                    "execution_plan": plan_data,
                    "suggestions": self._get_optimization_suggestions(query, plan_data),
                    "estimated_cost": self._extract_cost_from_plan(plan_data),
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                return analysis

        except Exception as e:
            logger.warning(f"Query performance analysis failed: {e}")

        return {"error": "Performance analysis not available"}

    def optimize_table_statistics(self) -> None:
        """Update table statistics for query optimizer."""
        schema = self.schema_config["main_schema"]

        tables = [
            f"{schema}.dataset_metadata",
            f"{schema}.istat_datasets",
            f"{schema}.istat_observations",
        ]

        for table in tables:
            try:
                self.manager.execute_statement(f"ANALYZE {table};")
                logger.debug(f"Updated statistics for table: {table}")
            except Exception as e:
                logger.warning(f"Failed to update statistics for {table}: {e}")

    def clear_cache(self) -> None:
        """Clear query result cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        """
        now = datetime.now()
        valid_entries = sum(
            1
            for entry in self.query_cache.values()
            if now - entry["timestamp"] < self.cache_ttl
        )

        performance_by_type = {}
        for perf in self.performance_log:
            query_type = perf.query_type.value
            if query_type not in performance_by_type:
                performance_by_type[query_type] = {
                    "count": 0,
                    "total_time": 0.0,
                    "cache_hits": 0,
                }

            performance_by_type[query_type]["count"] += 1
            performance_by_type[query_type]["total_time"] += perf.execution_time
            if perf.cache_hit:
                performance_by_type[query_type]["cache_hits"] += 1

        # Calculate averages
        for stats in performance_by_type.values():
            if stats["count"] > 0:
                stats["avg_time"] = float(stats["total_time"]) / stats["count"]
                stats["cache_hit_rate"] = float(stats["cache_hits"]) / stats["count"]

        return {
            "total_entries": len(self.query_cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.query_cache) - valid_entries,
            "performance_by_type": performance_by_type,
            "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60,
        }

    def _get_cached_result(
        self, cache_key: str, query_type: QueryType
    ) -> Optional[pd.DataFrame]:
        """Get cached query result if valid.

        Args:
            cache_key: Cache key
            query_type: Type of query for performance tracking

        Returns:
            Cached DataFrame or None
        """
        if cache_key in self.query_cache:
            entry = self.query_cache[cache_key]
            if datetime.now() - entry["timestamp"] < self.cache_ttl:
                # Log cache hit
                self.performance_log.append(
                    QueryPerformance(
                        query_hash=cache_key,
                        query_type=query_type,
                        execution_time=0.0,
                        rows_returned=len(entry["result"]),
                        cache_hit=True,
                    )
                )
                logger.debug(f"Cache hit for key: {cache_key[:20]}...")
                return entry["result"]
            else:
                # Remove expired entry
                del self.query_cache[cache_key]

        return None

    def _cache_result(
        self,
        cache_key: str,
        result: pd.DataFrame,
        query_type: QueryType,
        execution_time: float,
    ) -> None:
        """Cache query result.

        Args:
            cache_key: Cache key
            result: Query result DataFrame
            query_type: Type of query
            execution_time: Execution time in seconds
        """
        self.query_cache[cache_key] = {
            "result": result.copy(),
            "timestamp": datetime.now(),
        }

        # Log performance
        self.performance_log.append(
            QueryPerformance(
                query_hash=cache_key,
                query_type=query_type,
                execution_time=execution_time,
                rows_returned=len(result),
                cache_hit=False,
            )
        )

        # Keep performance log size manageable
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-500:]

    def _get_optimization_suggestions(self, query: str, plan_data: Any) -> list[str]:
        """Generate optimization suggestions based on query and execution plan.

        Args:
            query: Original SQL query
            plan_data: Execution plan data

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        query_lower = query.lower()

        # Basic query pattern suggestions
        if "where" not in query_lower:
            suggestions.append("Consider adding WHERE clauses to filter data early")

        if "limit" not in query_lower and "group by" not in query_lower:
            suggestions.append("Consider adding LIMIT to prevent excessive result sets")

        if query_lower.count("join") > 3:
            suggestions.append("Complex joins detected - consider materialized views")

        if "order by" in query_lower and "limit" not in query_lower:
            suggestions.append("ORDER BY without LIMIT may be inefficient")

        return suggestions

    def _extract_cost_from_plan(self, plan_data: Any) -> Optional[float]:
        """Extract estimated cost from execution plan.

        Args:
            plan_data: Execution plan data

        Returns:
            Estimated query cost or None
        """
        try:
            # This would need to be implemented based on DuckDB's plan format
            # For now, return None
            return None
        except Exception:
            return None


def create_optimizer(manager: Optional[DuckDBManager] = None) -> QueryOptimizer:
    """Create and configure query optimizer.

    Args:
        manager: Optional DuckDB manager instance

    Returns:
        Configured QueryOptimizer instance
    """
    optimizer = QueryOptimizer(manager)
    optimizer.create_advanced_indexes()
    optimizer.optimize_table_statistics()
    return optimizer
