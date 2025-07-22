"""DuckDB Query Builder with fluent interface for ISTAT analytics.

This module provides a fluent query builder for DuckDB that:
- Supports common SQL operations (SELECT, WHERE, GROUP BY, ORDER BY)
- Implements intelligent query result caching with TTL
- Provides specialized methods for ISTAT data patterns
- Includes robust error handling and validation
- Optimizes performance for analytical workloads
"""

import hashlib
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from src.utils.logger import get_logger

from .manager import DuckDBManager, get_manager
from .schema import ISTATSchemaManager

logger = get_logger(__name__)


class QueryType(Enum):
    """Supported query types for optimization."""

    SELECT = auto()
    COUNT = auto()
    AGGREGATE = auto()
    TIME_SERIES = auto()
    TERRITORY_COMPARISON = auto()
    CATEGORY_ANALYSIS = auto()


class FilterOperator(Enum):
    """Supported filter operators."""

    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class AggregateFunction(Enum):
    """Supported aggregate functions."""

    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    STDDEV = "STDDEV"
    VARIANCE = "VAR_POP"
    MEDIAN = "MEDIAN"


@dataclass
class FilterCondition:
    """Represents a WHERE clause condition."""

    column: str
    operator: FilterOperator
    value: Any
    logical_operator: str = "AND"  # AND, OR

    def to_sql(self) -> Tuple[str, List[Any]]:
        """Convert condition to SQL with parameters.

        Returns:
            Tuple of (sql_fragment, parameters)
        """
        if self.operator == FilterOperator.IS_NULL:
            return f"{self.column} IS NULL", []
        elif self.operator == FilterOperator.IS_NOT_NULL:
            return f"{self.column} IS NOT NULL", []
        elif self.operator == FilterOperator.BETWEEN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError("BETWEEN operator requires a list/tuple with 2 values")
            return f"{self.column} BETWEEN ? AND ?", list(self.value)
        elif self.operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            if not isinstance(self.value, (list, tuple)):
                raise ValueError(
                    f"{self.operator.value} operator requires a list/tuple"
                )
            placeholders = ", ".join(["?" for _ in self.value])
            return f"{self.column} {self.operator.value} ({placeholders})", list(
                self.value
            )
        else:
            return f"{self.column} {self.operator.value} ?", [self.value]


@dataclass
class JoinCondition:
    """Represents a table join."""

    table: str
    on_condition: str
    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL


@dataclass
class OrderByClause:
    """Represents an ORDER BY clause."""

    column: str
    direction: str = "ASC"  # ASC, DESC

    def to_sql(self) -> str:
        """Convert to SQL fragment."""
        return f"{self.column} {self.direction}"


@dataclass
class CacheEntry:
    """Query cache entry with TTL."""

    result: pd.DataFrame
    created_at: float
    ttl_seconds: int
    query_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds


class QueryCache:
    """Thread-safe query cache with TTL support."""

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """Initialize cache.

        Args:
            default_ttl: Default TTL in seconds (5 minutes)
            max_size: Maximum number of cached entries
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

    def get(self, query_hash: str) -> Optional[pd.DataFrame]:
        """Get cached result if available and not expired."""
        with self._lock:
            if query_hash not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[query_hash]
            if entry.is_expired():
                del self._cache[query_hash]
                if query_hash in self._access_times:
                    del self._access_times[query_hash]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None

            self._access_times[query_hash] = time.time()
            self._stats["hits"] += 1
            return entry.result.copy()

    def put(
        self,
        query_hash: str,
        result: pd.DataFrame,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store result in cache."""
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            ttl = ttl or self.default_ttl
            entry = CacheEntry(
                result=result.copy(),
                created_at=time.time(),
                ttl_seconds=ttl,
                query_hash=query_hash,
                metadata=metadata or {},
            )

            self._cache[query_hash] = entry
            self._access_times[query_hash] = time.time()

    def _evict_oldest(self) -> None:
        """Evict least recently used entry."""
        if not self._access_times:
            return

        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        del self._cache[oldest_key]
        del self._access_times[oldest_key]
        self._stats["evictions"] += 1

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            return {
                **self._stats,
                "hit_rate_percent": hit_rate,
                "cache_size": len(self._cache),
                "max_size": self.max_size,
            }


class DuckDBQueryBuilder:
    """Fluent query builder for DuckDB with caching and ISTAT optimizations."""

    def __init__(
        self,
        manager: Optional[DuckDBManager] = None,
        cache: Optional[QueryCache] = None,
    ):
        """Initialize query builder.

        Args:
            manager: Optional DuckDB manager instance
            cache: Optional query cache instance
        """
        self.manager = manager or get_manager()
        self.schema_manager = ISTATSchemaManager(self.manager)
        self.cache = cache or QueryCache()

        # Query building state
        self._reset_query_state()

    def _reset_query_state(self) -> None:
        """Reset internal query building state."""
        self._select_columns: List[str] = []
        self._from_table: Optional[str] = None
        self._joins: List[JoinCondition] = []
        self._where_conditions: List[FilterCondition] = []
        self._group_by_columns: List[str] = []
        self._having_conditions: List[FilterCondition] = []
        self._order_by_clauses: List[OrderByClause] = []
        self._limit_count: Optional[int] = None
        self._offset_count: Optional[int] = None

        # Query metadata
        self._query_type: QueryType = QueryType.SELECT
        self._cache_ttl: Optional[int] = None
        self._explain_query: bool = False

    def select(self, *columns: str) -> "DuckDBQueryBuilder":
        """Add SELECT columns.

        Args:
            columns: Column names or expressions to select

        Returns:
            Self for method chaining
        """
        if not columns:
            raise ValueError("At least one column must be specified")

        # Validate column names (basic SQL injection prevention)
        for col in columns:
            if not isinstance(col, str):
                raise ValueError("Column names must be strings")
            # Allow common SQL functions and expressions
            if (
                not col.replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .replace(" ", "")
                .replace("*", "")
                .replace(".", "_")
                .replace("_", "")
                .isalnum()
            ):
                # More flexible validation for SQL expressions
                if not any(
                    func in col.upper()
                    for func in ["COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT", "AS"]
                ):
                    logger.warning(f"Potentially unsafe column expression: {col}")

        self._select_columns.extend(columns)
        return self

    def from_table(self, table_name: str) -> "DuckDBQueryBuilder":
        """Set FROM table.

        Args:
            table_name: Table name (can include schema and alias)

        Returns:
            Self for method chaining
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("Table name must be a non-empty string")

        # Basic validation for table name (allow spaces for aliases)
        # Split on space to handle "table_name alias" format
        parts = table_name.split()
        for part in parts:
            # Each part should be alphanumeric with dots/underscores
            if not part.replace(".", "_").replace("_", "").isalnum():
                raise ValueError(f"Invalid table name component: {part}")

        self._from_table = table_name
        return self

    def join(
        self, table: str, on_condition: str, join_type: str = "INNER"
    ) -> "DuckDBQueryBuilder":
        """Add JOIN clause.

        Args:
            table: Table to join
            on_condition: JOIN condition (e.g., "a.id = b.id")
            join_type: Type of join (INNER, LEFT, RIGHT, FULL)

        Returns:
            Self for method chaining
        """
        valid_join_types = {"INNER", "LEFT", "RIGHT", "FULL", "CROSS"}
        if join_type.upper() not in valid_join_types:
            raise ValueError(f"Invalid join type. Must be one of: {valid_join_types}")

        self._joins.append(JoinCondition(table, on_condition, join_type.upper()))
        return self

    def where(
        self, column: str, operator: Union[FilterOperator, str], value: Any = None
    ) -> "DuckDBQueryBuilder":
        """Add WHERE condition.

        Args:
            column: Column name
            operator: Filter operator
            value: Filter value (not needed for IS NULL/IS NOT NULL)

        Returns:
            Self for method chaining
        """
        if isinstance(operator, str):
            try:
                operator = FilterOperator(operator)
            except ValueError:
                # Try to match by name
                operator_map = {
                    "=": FilterOperator.EQ,
                    "!=": FilterOperator.NE,
                    ">": FilterOperator.GT,
                    ">=": FilterOperator.GTE,
                    "<": FilterOperator.LT,
                    "<=": FilterOperator.LTE,
                    "IN": FilterOperator.IN,
                    "NOT IN": FilterOperator.NOT_IN,
                    "LIKE": FilterOperator.LIKE,
                    "ILIKE": FilterOperator.ILIKE,
                    "BETWEEN": FilterOperator.BETWEEN,
                    "IS NULL": FilterOperator.IS_NULL,
                    "IS NOT NULL": FilterOperator.IS_NOT_NULL,
                }
                operator = operator_map.get(operator.upper())
                if operator is None:
                    raise ValueError(f"Invalid operator: {operator}")

        condition = FilterCondition(column, operator, value)
        self._where_conditions.append(condition)
        return self

    def where_in(self, column: str, values: List[Any]) -> "DuckDBQueryBuilder":
        """Add WHERE IN condition.

        Args:
            column: Column name
            values: List of values

        Returns:
            Self for method chaining
        """
        return self.where(column, FilterOperator.IN, values)

    def where_between(self, column: str, start: Any, end: Any) -> "DuckDBQueryBuilder":
        """Add WHERE BETWEEN condition.

        Args:
            column: Column name
            start: Start value
            end: End value

        Returns:
            Self for method chaining
        """
        return self.where(column, FilterOperator.BETWEEN, [start, end])

    def where_null(self, column: str) -> "DuckDBQueryBuilder":
        """Add WHERE IS NULL condition.

        Args:
            column: Column name

        Returns:
            Self for method chaining
        """
        return self.where(column, FilterOperator.IS_NULL)

    def where_not_null(self, column: str) -> "DuckDBQueryBuilder":
        """Add WHERE IS NOT NULL condition.

        Args:
            column: Column name

        Returns:
            Self for method chaining
        """
        return self.where(column, FilterOperator.IS_NOT_NULL)

    def group_by(self, *columns: str) -> "DuckDBQueryBuilder":
        """Add GROUP BY columns.

        Args:
            columns: Column names to group by

        Returns:
            Self for method chaining
        """
        if not columns:
            raise ValueError("At least one column must be specified for GROUP BY")

        self._group_by_columns.extend(columns)
        self._query_type = QueryType.AGGREGATE
        return self

    def having(
        self, column: str, operator: Union[FilterOperator, str], value: Any
    ) -> "DuckDBQueryBuilder":
        """Add HAVING condition.

        Args:
            column: Column name (usually an aggregate)
            operator: Filter operator
            value: Filter value

        Returns:
            Self for method chaining
        """
        if isinstance(operator, str):
            operator = FilterOperator(operator)

        condition = FilterCondition(column, operator, value)
        self._having_conditions.append(condition)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "DuckDBQueryBuilder":
        """Add ORDER BY clause.

        Args:
            column: Column name
            direction: Sort direction (ASC or DESC)

        Returns:
            Self for method chaining
        """
        direction = direction.upper()
        if direction not in ["ASC", "DESC"]:
            raise ValueError("Direction must be ASC or DESC")

        self._order_by_clauses.append(OrderByClause(column, direction))
        return self

    def limit(self, count: int) -> "DuckDBQueryBuilder":
        """Add LIMIT clause.

        Args:
            count: Number of rows to limit

        Returns:
            Self for method chaining
        """
        if not isinstance(count, int) or count < 0:
            raise ValueError("Limit count must be a non-negative integer")

        self._limit_count = count
        return self

    def offset(self, count: int) -> "DuckDBQueryBuilder":
        """Add OFFSET clause.

        Args:
            count: Number of rows to offset

        Returns:
            Self for method chaining
        """
        if not isinstance(count, int) or count < 0:
            raise ValueError("Offset count must be a non-negative integer")

        self._offset_count = count
        return self

    def cache_for(self, seconds: int) -> "DuckDBQueryBuilder":
        """Set cache TTL for this query.

        Args:
            seconds: Cache TTL in seconds

        Returns:
            Self for method chaining
        """
        if not isinstance(seconds, int) or seconds < 0:
            raise ValueError("Cache TTL must be a non-negative integer")

        self._cache_ttl = seconds
        return self

    def explain(self) -> "DuckDBQueryBuilder":
        """Enable EXPLAIN for query analysis.

        Returns:
            Self for method chaining
        """
        self._explain_query = True
        return self

    # Specialized ISTAT methods

    def select_time_series(self, dataset_id: str) -> "DuckDBQueryBuilder":
        """Select time series data for ISTAT dataset.

        Args:
            dataset_id: ISTAT dataset identifier

        Returns:
            Self for method chaining
        """
        self._query_type = QueryType.TIME_SERIES
        return (
            self.select(
                "d.year",
                "d.time_period",
                "d.territory_code",
                "d.territory_name",
                "d.measure_code",
                "d.measure_name",
                "o.obs_value",
                "m.category",
            )
            .from_table("main.istat_datasets d")
            .join("main.istat_observations o", "d.id = o.dataset_row_id")
            .join("main.dataset_metadata m", "d.dataset_id = m.dataset_id")
            .where("d.dataset_id", FilterOperator.EQ, dataset_id)
            .where_not_null("o.obs_value")
            .order_by("d.year")
            .order_by("d.time_period")
        )

    def select_territory_comparison(
        self, measure_code: str, year: int
    ) -> "DuckDBQueryBuilder":
        """Select data for territory comparison.

        Args:
            measure_code: Measure code to compare
            year: Year for comparison

        Returns:
            Self for method chaining
        """
        self._query_type = QueryType.TERRITORY_COMPARISON
        return (
            self.select(
                "d.territory_code",
                "d.territory_name",
                "AVG(o.obs_value) as avg_value",
                "COUNT(o.obs_value) as observation_count",
            )
            .from_table("main.istat_datasets d")
            .join("main.istat_observations o", "d.id = o.dataset_row_id")
            .where("d.measure_code", FilterOperator.EQ, measure_code)
            .where("d.year", FilterOperator.EQ, year)
            .where_not_null("o.obs_value")
            .group_by("d.territory_code", "d.territory_name")
            .order_by("avg_value", "DESC")
        )

    def select_category_trends(self, category: str) -> "DuckDBQueryBuilder":
        """Select trend data by category.

        Args:
            category: ISTAT category to analyze

        Returns:
            Self for method chaining
        """
        self._query_type = QueryType.CATEGORY_ANALYSIS
        return (
            self.select(
                "d.year",
                "COUNT(DISTINCT d.dataset_id) as dataset_count",
                "AVG(o.obs_value) as avg_value",
                "SUM(o.obs_value) as total_value",
            )
            .from_table("main.istat_datasets d")
            .join("main.istat_observations o", "d.id = o.dataset_row_id")
            .join("main.dataset_metadata m", "d.dataset_id = m.dataset_id")
            .where("m.category", FilterOperator.EQ, category)
            .where_not_null("o.obs_value")
            .group_by("d.year")
            .order_by("d.year")
        )

    def year_range(self, start_year: int, end_year: int) -> "DuckDBQueryBuilder":
        """Filter by year range.

        Args:
            start_year: Start year (inclusive)
            end_year: End year (inclusive)

        Returns:
            Self for method chaining
        """
        return self.where_between("d.year", start_year, end_year)

    def territories(self, territory_codes: List[str]) -> "DuckDBQueryBuilder":
        """Filter by territory codes.

        Args:
            territory_codes: List of territory codes

        Returns:
            Self for method chaining
        """
        return self.where_in("d.territory_code", territory_codes)

    def build_sql(self) -> Tuple[str, List[Any]]:
        """Build SQL query with parameters.

        Returns:
            Tuple of (sql_query, parameters)
        """
        if not self._from_table:
            raise ValueError("FROM table must be specified")

        if not self._select_columns:
            raise ValueError("SELECT columns must be specified")

        # Build query parts
        parts = []
        parameters = []

        # SELECT
        if self._explain_query:
            parts.append("EXPLAIN")

        select_clause = "SELECT " + ", ".join(self._select_columns)
        parts.append(select_clause)

        # FROM
        parts.append(f"FROM {self._from_table}")

        # JOINs
        for join in self._joins:
            parts.append(f"{join.join_type} JOIN {join.table} ON {join.on_condition}")

        # WHERE
        if self._where_conditions:
            where_parts = []
            for i, condition in enumerate(self._where_conditions):
                if i > 0:
                    where_parts.append(condition.logical_operator)

                sql_fragment, condition_params = condition.to_sql()
                where_parts.append(sql_fragment)
                parameters.extend(condition_params)

            parts.append("WHERE " + " ".join(where_parts))

        # GROUP BY
        if self._group_by_columns:
            parts.append("GROUP BY " + ", ".join(self._group_by_columns))

        # HAVING
        if self._having_conditions:
            having_parts = []
            for i, condition in enumerate(self._having_conditions):
                if i > 0:
                    having_parts.append(condition.logical_operator)

                sql_fragment, condition_params = condition.to_sql()
                having_parts.append(sql_fragment)
                parameters.extend(condition_params)

            parts.append("HAVING " + " ".join(having_parts))

        # ORDER BY
        if self._order_by_clauses:
            order_parts = [clause.to_sql() for clause in self._order_by_clauses]
            parts.append("ORDER BY " + ", ".join(order_parts))

        # LIMIT
        if self._limit_count is not None:
            parts.append(f"LIMIT {self._limit_count}")

        # OFFSET
        if self._offset_count is not None:
            parts.append(f"OFFSET {self._offset_count}")

        sql_query = "\n".join(parts)
        return sql_query, parameters

    def _generate_cache_key(self, sql: str, params: List[Any]) -> str:
        """Generate cache key for query.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Cache key hash
        """
        params_str = ""
        if params:
            # Handle both list and dict parameters
            if isinstance(params, dict):
                param_items = [(str(k), str(v)) for k, v in params.items()]
                params_str = str(sorted(param_items))
            else:
                # Convert list to sorted strings to avoid type comparison errors
                params_str = str([str(p) for p in params])
        content = sql + params_str
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def execute(self, use_cache: bool = True) -> pd.DataFrame:
        """Execute the query and return results.

        Args:
            use_cache: Whether to use query caching

        Returns:
            Query results as DataFrame
        """
        start_time = time.time()

        try:
            sql, params = self.build_sql()

            # Check cache first
            cache_key = None
            if use_cache:
                cache_key = self._generate_cache_key(sql, params)
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    execution_time = time.time() - start_time
                    logger.info(f"Cache hit! Query returned in {execution_time:.3f}s")
                    return cached_result

            # Execute query
            logger.debug(f"Executing query: {sql[:200]}...")
            if params:
                result = self.manager.execute_query(sql, params)
            else:
                result = self.manager.execute_query(sql)

            # Cache result
            if use_cache and cache_key:
                cache_ttl = self._cache_ttl or self.cache.default_ttl
                self.cache.put(
                    cache_key,
                    result,
                    cache_ttl,
                    {
                        "query_type": self._query_type.name,
                        "execution_time": time.time() - start_time,
                        "row_count": len(result),
                    },
                )

            execution_time = time.time() - start_time
            logger.info(
                f"Query executed successfully in {execution_time:.3f}s, returned {len(result)} rows"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed after {execution_time:.3f}s: {e}")
            raise
        finally:
            # Reset state for next query
            self._reset_query_state()

    def count(self) -> int:
        """Execute query and return row count.

        Returns:
            Number of rows that would be returned by the query
        """
        # Modify query to return count
        original_select = self._select_columns[:]
        original_order = self._order_by_clauses[:]
        original_limit = self._limit_count
        original_offset = self._offset_count

        try:
            self._select_columns = ["COUNT(*) as row_count"]
            self._order_by_clauses = []
            self._limit_count = None
            self._offset_count = None
            self._query_type = QueryType.COUNT

            result = self.execute()
            return int(result.iloc[0]["row_count"])

        finally:
            # Restore original state
            self._select_columns = original_select
            self._order_by_clauses = original_order
            self._limit_count = original_limit
            self._offset_count = original_offset

    def first(self) -> Optional[pd.Series]:
        """Execute query and return first row.

        Returns:
            First row as Series, or None if no results
        """
        result = self.limit(1).execute()
        return result.iloc[0] if not result.empty else None

    def exists(self) -> bool:
        """Check if query returns any results.

        Returns:
            True if query returns at least one row
        """
        return self.count() > 0


def create_query_builder(
    manager: Optional[DuckDBManager] = None, cache: Optional[QueryCache] = None
) -> DuckDBQueryBuilder:
    """Create a new query builder instance.

    Args:
        manager: Optional DuckDB manager instance
        cache: Optional query cache instance

    Returns:
        New query builder instance
    """
    return DuckDBQueryBuilder(manager, cache)


# Global cache instance
_global_cache = QueryCache()


def get_global_cache() -> QueryCache:
    """Get the global query cache instance."""
    return _global_cache
