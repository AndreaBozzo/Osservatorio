"""
Database Performance Benchmarking Tool.

This module provides comprehensive database performance testing for:
- SQLite query performance analysis
- DuckDB query optimization testing
- Connection pooling performance
- Memory usage during database operations
- Concurrent database access testing
"""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
import psutil
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

from src.database.duckdb.manager import DuckDBManager
from src.utils.config import get_config


@dataclass
class DatabaseBenchmarkResult:
    """Database benchmark result."""

    query_type: str
    database_type: str  # 'sqlite', 'duckdb'
    query: str
    execution_time_ms: float
    rows_processed: int
    memory_usage_mb: float
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class DatabaseBenchmarkSummary:
    """Summary of database benchmark results."""

    query_type: str
    database_type: str
    total_queries: int
    successful_queries: int
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    p95_execution_time_ms: float
    total_rows_processed: int
    queries_per_second: float
    avg_memory_usage_mb: float
    error_rate: float


class DatabaseBenchmark:
    """Database performance benchmarking tool."""

    def __init__(
        self, sqlite_path: Optional[str] = None, duckdb_path: Optional[str] = None
    ):
        """Initialize database benchmark tool."""
        self.sqlite_path = sqlite_path or "data/databases/osservatorio_metadata.db"
        self.duckdb_path = duckdb_path or "data/databases/osservatorio.duckdb"
        self.results: list[DatabaseBenchmarkResult] = []

        # Initialize connections
        self.sqlite_engine = self._create_sqlite_engine()
        self.duckdb_manager = self._create_duckdb_manager()

    def _create_sqlite_engine(self):
        """Create SQLite engine with connection pooling."""
        return create_engine(
            f"sqlite:///{self.sqlite_path}",
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

    def _create_duckdb_manager(self):
        """Create DuckDB manager."""
        try:
            config = get_config()
            return DuckDBManager(db_path=self.duckdb_path, config=config)
        except Exception:
            # Fallback to basic DuckDB connection
            return None

    def benchmark_sqlite_query(
        self, query: str, query_type: str = "select", params: Optional[dict] = None
    ) -> DatabaseBenchmarkResult:
        """Benchmark single SQLite query."""
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.perf_counter()
        rows_processed = 0
        success = True
        error_message = None

        try:
            with self.sqlite_engine.connect() as conn:
                result = conn.execute(text(query), params or {})

                if query_type.lower() in ["select", "query"]:
                    rows = result.fetchall()
                    rows_processed = len(rows)
                else:
                    rows_processed = result.rowcount or 0

        except Exception as e:
            success = False
            error_message = str(e)

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = memory_after - memory_before

        result = DatabaseBenchmarkResult(
            query_type=query_type,
            database_type="sqlite",
            query=query,
            execution_time_ms=execution_time_ms,
            rows_processed=rows_processed,
            memory_usage_mb=memory_usage,
            success=success,
            timestamp=datetime.now(),
            error_message=error_message,
        )

        self.results.append(result)
        return result

    def benchmark_duckdb_query(
        self, query: str, query_type: str = "select", params: Optional[dict] = None
    ) -> DatabaseBenchmarkResult:
        """Benchmark single DuckDB query."""
        if not self.duckdb_manager:
            # Fallback to direct DuckDB connection
            return self._benchmark_duckdb_direct(query, query_type, params)

        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.perf_counter()
        rows_processed = 0
        success = True
        error_message = None

        try:
            with self.duckdb_manager.get_connection() as conn:
                result = conn.execute(query, params or {})

                if query_type.lower() in ["select", "query"]:
                    rows = result.fetchall()
                    rows_processed = len(rows)
                else:
                    rows_processed = (
                        result.changes() if hasattr(result, "changes") else 0
                    )

        except Exception as e:
            success = False
            error_message = str(e)

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = memory_after - memory_before

        result = DatabaseBenchmarkResult(
            query_type=query_type,
            database_type="duckdb",
            query=query,
            execution_time_ms=execution_time_ms,
            rows_processed=rows_processed,
            memory_usage_mb=memory_usage,
            success=success,
            timestamp=datetime.now(),
            error_message=error_message,
        )

        self.results.append(result)
        return result

    def _benchmark_duckdb_direct(
        self, query: str, query_type: str = "select", params: Optional[dict] = None
    ) -> DatabaseBenchmarkResult:
        """Benchmark DuckDB query with direct connection."""
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.perf_counter()
        rows_processed = 0
        success = True
        error_message = None

        try:
            conn = duckdb.connect(self.duckdb_path)
            result = conn.execute(query, params or {})

            if query_type.lower() in ["select", "query"]:
                rows = result.fetchall()
                rows_processed = len(rows)
            else:
                rows_processed = conn.changes() if hasattr(conn, "changes") else 0

            conn.close()

        except Exception as e:
            success = False
            error_message = str(e)

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = memory_after - memory_before

        result = DatabaseBenchmarkResult(
            query_type=query_type,
            database_type="duckdb",
            query=query,
            execution_time_ms=execution_time_ms,
            rows_processed=rows_processed,
            memory_usage_mb=memory_usage,
            success=success,
            timestamp=datetime.now(),
            error_message=error_message,
        )

        self.results.append(result)
        return result

    def benchmark_common_queries(self) -> list[DatabaseBenchmarkResult]:
        """Benchmark common database queries."""
        common_queries = [
            {
                "query": "SELECT COUNT(*) FROM datasets",
                "type": "count",
                "description": "Count all datasets",
            },
            {
                "query": "SELECT * FROM datasets LIMIT 100",
                "type": "select",
                "description": "Select 100 datasets",
            },
            {
                "query": "SELECT * FROM datasets WHERE category = 'popolazione' LIMIT 50",
                "type": "select_filtered",
                "description": "Filtered select with category",
            },
            {
                "query": "SELECT category, COUNT(*) as count FROM datasets GROUP BY category",
                "type": "aggregation",
                "description": "Group by aggregation",
            },
            {
                "query": """
                SELECT d.*, dm.*
                FROM datasets d
                LEFT JOIN dataset_metadata dm ON d.id = dm.dataset_id
                LIMIT 20
                """,
                "type": "join",
                "description": "Join with metadata",
            },
        ]

        results = []

        # Test SQLite queries
        for query_config in common_queries:
            try:
                result = self.benchmark_sqlite_query(
                    query_config["query"], query_config["type"]
                )
                results.append(result)
            except Exception as e:
                print(f"SQLite query failed: {e}")

        # Test DuckDB queries (if available)
        if Path(self.duckdb_path).exists():
            for query_config in common_queries:
                try:
                    result = self.benchmark_duckdb_query(
                        query_config["query"], query_config["type"]
                    )
                    results.append(result)
                except Exception as e:
                    print(f"DuckDB query failed: {e}")

        return results

    def concurrent_database_test(
        self,
        queries: list[dict[str, str]],
        concurrent_connections: int = 10,
        database_type: str = "sqlite",
    ) -> list[DatabaseBenchmarkResult]:
        """Test concurrent database access."""
        results = []

        def execute_query(query_config: dict[str, str]) -> DatabaseBenchmarkResult:
            query = query_config["query"]
            query_type = query_config.get("type", "select")

            if database_type.lower() == "sqlite":
                return self.benchmark_sqlite_query(query, query_type)
            else:
                return self.benchmark_duckdb_query(query, query_type)

        # Use thread pool for concurrent queries
        with ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            futures = [
                executor.submit(execute_query, query_config) for query_config in queries
            ]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Create error result
                    error_result = DatabaseBenchmarkResult(
                        query_type="error",
                        database_type=database_type,
                        query="",
                        execution_time_ms=0,
                        rows_processed=0,
                        memory_usage_mb=0,
                        success=False,
                        timestamp=datetime.now(),
                        error_message=str(e),
                    )
                    results.append(error_result)

        self.results.extend(results)
        return results

    def stress_test_database(
        self,
        database_type: str = "sqlite",
        duration_seconds: int = 60,
        queries_per_second: int = 10,
    ) -> list[DatabaseBenchmarkResult]:
        """Stress test database with sustained load."""
        results = []
        start_time = time.time()
        query_interval = 1.0 / queries_per_second

        # Stress test queries
        stress_queries = [
            {"query": "SELECT COUNT(*) FROM datasets", "type": "count"},
            {"query": "SELECT * FROM datasets ORDER BY id LIMIT 50", "type": "select"},
            {
                "query": "SELECT category, COUNT(*) FROM datasets GROUP BY category",
                "type": "aggregation",
            },
        ]

        while (time.time() - start_time) < duration_seconds:
            query_config = stress_queries[len(results) % len(stress_queries)]

            try:
                if database_type.lower() == "sqlite":
                    result = self.benchmark_sqlite_query(
                        query_config["query"], query_config["type"]
                    )
                else:
                    result = self.benchmark_duckdb_query(
                        query_config["query"], query_config["type"]
                    )

                results.append(result)

            except Exception as e:
                error_result = DatabaseBenchmarkResult(
                    query_type="stress_error",
                    database_type=database_type,
                    query=query_config["query"],
                    execution_time_ms=0,
                    rows_processed=0,
                    memory_usage_mb=0,
                    success=False,
                    timestamp=datetime.now(),
                    error_message=str(e),
                )
                results.append(error_result)

            # Sleep to maintain desired QPS
            time.sleep(query_interval)

        return results

    def analyze_results(
        self, query_type: Optional[str] = None, database_type: Optional[str] = None
    ) -> DatabaseBenchmarkSummary:
        """Analyze benchmark results."""
        filtered_results = self.results

        if query_type:
            filtered_results = [
                r for r in filtered_results if r.query_type == query_type
            ]

        if database_type:
            filtered_results = [
                r for r in filtered_results if r.database_type == database_type
            ]

        if not filtered_results:
            raise ValueError("No results match the specified criteria")

        successful_results = [r for r in filtered_results if r.success]
        failed_results = [r for r in filtered_results if not r.success]

        if successful_results:
            execution_times = [r.execution_time_ms for r in successful_results]
            avg_execution_time = statistics.mean(execution_times)
            min_execution_time = min(execution_times)
            max_execution_time = max(execution_times)

            # Calculate P95
            sorted_times = sorted(execution_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_execution_time = (
                sorted_times[p95_index]
                if p95_index < len(sorted_times)
                else max_execution_time
            )

            total_rows = sum(r.rows_processed for r in successful_results)
            avg_memory = statistics.mean(
                [r.memory_usage_mb for r in successful_results]
            )

            # Calculate QPS
            total_time_seconds = (
                max(r.timestamp for r in filtered_results)
                - min(r.timestamp for r in filtered_results)
            ).total_seconds()
            queries_per_second = len(successful_results) / max(total_time_seconds, 1)

        else:
            avg_execution_time = 0
            min_execution_time = 0
            max_execution_time = 0
            p95_execution_time = 0
            total_rows = 0
            avg_memory = 0
            queries_per_second = 0

        error_rate = len(failed_results) / len(filtered_results)

        return DatabaseBenchmarkSummary(
            query_type=query_type or "all",
            database_type=database_type or "all",
            total_queries=len(filtered_results),
            successful_queries=len(successful_results),
            avg_execution_time_ms=avg_execution_time,
            min_execution_time_ms=min_execution_time,
            max_execution_time_ms=max_execution_time,
            p95_execution_time_ms=p95_execution_time,
            total_rows_processed=total_rows,
            queries_per_second=queries_per_second,
            avg_memory_usage_mb=avg_memory,
            error_rate=error_rate,
        )

    def generate_report(self, output_path: Optional[Path] = None) -> dict:
        """Generate comprehensive database performance report."""
        if not self.results:
            raise ValueError("No benchmark results available")

        # Analyze by database type
        database_types = list({r.database_type for r in self.results})
        query_types = list({r.query_type for r in self.results})

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(self.results),
            "database_types": database_types,
            "query_types": query_types,
            "results": {},
        }

        # Analyze by database type
        for db_type in database_types:
            try:
                summary = self.analyze_results(database_type=db_type)
                report["results"][db_type] = {
                    "total_queries": summary.total_queries,
                    "successful_queries": summary.successful_queries,
                    "avg_execution_time_ms": summary.avg_execution_time_ms,
                    "p95_execution_time_ms": summary.p95_execution_time_ms,
                    "queries_per_second": summary.queries_per_second,
                    "avg_memory_usage_mb": summary.avg_memory_usage_mb,
                    "error_rate": summary.error_rate,
                    "total_rows_processed": summary.total_rows_processed,
                }
            except ValueError:
                continue

        # Performance insights
        report["insights"] = self._generate_db_insights()

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def _generate_db_insights(self) -> list[str]:
        """Generate database performance insights."""
        insights = []

        try:
            # Compare SQLite vs DuckDB if both available
            sqlite_summary = self.analyze_results(database_type="sqlite")
            duckdb_summary = self.analyze_results(database_type="duckdb")

            if (
                sqlite_summary.avg_execution_time_ms
                > duckdb_summary.avg_execution_time_ms
            ):
                ratio = (
                    sqlite_summary.avg_execution_time_ms
                    / duckdb_summary.avg_execution_time_ms
                )
                insights.append(f"DuckDB is {ratio:.1f}x faster than SQLite on average")
            else:
                ratio = (
                    duckdb_summary.avg_execution_time_ms
                    / sqlite_summary.avg_execution_time_ms
                )
                insights.append(f"SQLite is {ratio:.1f}x faster than DuckDB on average")

        except ValueError:
            pass

        # Check for slow queries
        slow_queries = [
            r for r in self.results if r.success and r.execution_time_ms > 1000
        ]
        if slow_queries:
            insights.append(f"Found {len(slow_queries)} queries taking >1 second")

        # Check memory usage
        high_memory_queries = [r for r in self.results if r.memory_usage_mb > 100]
        if high_memory_queries:
            insights.append(
                f"Found {len(high_memory_queries)} queries using >100MB memory"
            )

        # Check error rates
        total_errors = len([r for r in self.results if not r.success])
        if total_errors > 0:
            error_rate = total_errors / len(self.results)
            insights.append(f"Database error rate: {error_rate:.1%}")

        if not insights:
            insights.append("Database performance is within acceptable limits")

        return insights

    def clear_results(self):
        """Clear all benchmark results."""
        self.results.clear()

    def close(self):
        """Close database connections."""
        if hasattr(self, "sqlite_engine"):
            self.sqlite_engine.dispose()

        if hasattr(self, "duckdb_manager") and self.duckdb_manager:
            # DuckDB manager cleanup if available
            pass
