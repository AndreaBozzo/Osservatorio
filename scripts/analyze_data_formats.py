#!/usr/bin/env python3
"""
Analizza formati dati e patterns di accesso per database design

Questo script analizza i dataset ISTAT disponibili per:
- Tipologie di dati (strutturati/semi-strutturati)
- Volumi per dataset
- Patterns di accesso
- Requisiti storage per DuckDB/PostgreSQL

Usage:
    python scripts/analyze_data_formats.py
    python scripts/analyze_data_formats.py --dataset DCIS_POPRES1
    python scripts/analyze_data_formats.py --format json
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.analyzers.dataflow_analyzer import IstatDataflowAnalyzer
from src.api.istat_api import IstatAPITester
from src.utils.logger import get_logger
from src.utils.temp_file_manager import TempFileManager

logger = get_logger(__name__)


class DataFormatAnalyzer:
    """Analizza formati dati ISTAT per database design"""

    def __init__(self):
        self.api_client = IstatAPITester()
        self.analyzer = IstatDataflowAnalyzer()
        self.temp_manager = TempFileManager()

    def analyze_istat_datasets(self, sample_size: int = 10) -> Dict[str, Any]:
        """
        Analizza tutti i dataset ISTAT disponibili

        Args:
            sample_size: Numero di dataset da analizzare in dettaglio

        Returns:
            Dict con analisi completa dei dataset
        """
        logger.info(f"Starting analysis of ISTAT datasets (sample_size={sample_size})")

        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "total_datasets": 0,
            "analyzed_datasets": 0,
            "data_types": {},
            "volume_distribution": {},
            "structure_patterns": {},
            "access_patterns": {},
            "storage_recommendations": {},
        }

        try:
            # Get all available dataflows
            logger.info("Discovering available datasets...")
            dataflows = self.api_client.discover_available_datasets()
            analysis_results["total_datasets"] = len(dataflows)

            # Analyze sample of datasets in detail
            sample_datasets = dataflows[:sample_size]
            analysis_results["analyzed_datasets"] = len(sample_datasets)

            structure_patterns = {}
            volume_data = []
            data_types = {"structured": 0, "semi_structured": 0, "time_series": 0}

            for i, dataflow in enumerate(sample_datasets):
                dataset_id = dataflow.get("id", f"unknown_{i}")
                logger.info(
                    f"Analyzing dataset {i+1}/{len(sample_datasets)}: {dataset_id}"
                )

                try:
                    # Fetch sample data
                    test_result = self.api_client.test_specific_dataset(dataset_id)
                    xml_data = test_result.get("data", "")

                    # Analyze structure
                    structure = self._analyze_xml_structure(xml_data)
                    structure_patterns[dataset_id] = structure

                    # Estimate volume
                    volume_mb = len(xml_data.encode("utf-8")) / (1024 * 1024)
                    volume_data.append(
                        {"dataset_id": dataset_id, "volume_mb": volume_mb}
                    )

                    # Classify data type
                    if self._is_time_series(structure):
                        data_types["time_series"] += 1
                    elif self._is_structured(structure):
                        data_types["structured"] += 1
                    else:
                        data_types["semi_structured"] += 1

                except Exception as e:
                    logger.warning(f"Error analyzing dataset {dataset_id}: {e}")
                    continue

            analysis_results["data_types"] = data_types
            analysis_results["volume_distribution"] = self._analyze_volume_distribution(
                volume_data
            )
            analysis_results["structure_patterns"] = self._summarize_structure_patterns(
                structure_patterns
            )
            analysis_results["access_patterns"] = self._analyze_access_patterns(
                sample_datasets
            )

        except Exception as e:
            logger.error(f"Error in dataset analysis: {e}")
            analysis_results["error"] = str(e)

        logger.info("Dataset analysis completed")
        return analysis_results

    def estimate_storage_requirements(
        self, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stima requisiti di storage

        Args:
            analysis_results: Risultati dall'analisi dei dataset

        Returns:
            Dict con stime di storage
        """
        logger.info("Estimating storage requirements")

        volume_dist = analysis_results.get("volume_distribution", {})
        total_datasets = analysis_results.get("total_datasets", 509)
        analyzed_datasets = analysis_results.get("analyzed_datasets", 1)

        # Calculate average volume per dataset
        avg_volume_mb = volume_dist.get("average_mb", 30)

        # Estimate total current storage
        current_raw_storage_gb = (total_datasets * avg_volume_mb) / 1024

        # Estimate processed storage (2x multiplier for different formats)
        current_processed_storage_gb = current_raw_storage_gb * 2

        # Annual growth estimates
        annual_new_datasets = 50  # Estimated new datasets per year
        annual_updates = 12  # Average updates per dataset per year

        annual_raw_growth_gb = (
            annual_new_datasets * avg_volume_mb + total_datasets * avg_volume_mb * 0.1
        ) / 1024  # 10% size growth
        annual_processed_growth_gb = annual_raw_growth_gb * 2

        storage_requirements = {
            "current_storage": {
                "raw_data_gb": round(current_raw_storage_gb, 2),
                "processed_data_gb": round(current_processed_storage_gb, 2),
                "total_gb": round(
                    current_raw_storage_gb + current_processed_storage_gb, 2
                ),
            },
            "annual_growth": {
                "raw_data_gb": round(annual_raw_growth_gb, 2),
                "processed_data_gb": round(annual_processed_growth_gb, 2),
                "total_gb": round(annual_raw_growth_gb + annual_processed_growth_gb, 2),
            },
            "5_year_projection": {
                "total_gb": round(
                    (current_raw_storage_gb + current_processed_storage_gb)
                    + (annual_raw_growth_gb + annual_processed_growth_gb) * 5,
                    2,
                )
            },
            "index_requirements": {
                "time_indexes": "Required for all time-series data",
                "territorial_indexes": "Required for geographic data",
                "category_indexes": "Required for dataset categorization",
                "estimated_index_overhead": "15-20% of data size",
            },
        }

        logger.info(
            f"Storage requirements estimated: {storage_requirements['current_storage']['total_gb']}GB current"
        )
        return storage_requirements

    def generate_database_recommendations(
        self, analysis_results: Dict[str, Any], storage_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera raccomandazioni per scelta database

        Args:
            analysis_results: Risultati analisi dataset
            storage_requirements: Requisiti di storage

        Returns:
            Dict con raccomandazioni database
        """
        logger.info("Generating database recommendations")

        recommendations = {
            "hybrid_approach": {
                "recommended": True,
                "rationale": "Different workloads require different database strengths",
            },
            "duckdb_usage": {
                "workloads": [
                    "Time-series analytics",
                    "Aggregation queries",
                    "Data warehouse operations",
                    "OLAP workloads",
                ],
                "advantages": [
                    "Columnar storage for analytics",
                    "Excellent compression",
                    "Fast aggregations",
                    "Embedded deployment",
                ],
                "schema_recommendations": {
                    "partitioning": "By year for time-series data",
                    "compression": "GZIP for historical data",
                    "indexes": "Composite indexes on (dataset_id, tempo, territorio)",
                },
            },
            "postgresql_usage": {
                "workloads": [
                    "Metadata management",
                    "User authentication",
                    "Configuration storage",
                    "Audit logging",
                ],
                "advantages": [
                    "ACID compliance",
                    "Rich ecosystem",
                    "Full-text search",
                    "JSON support",
                ],
                "schema_recommendations": {
                    "tables": ["users", "datasets_metadata", "api_keys", "audit_log"],
                    "indexes": "B-tree on primary keys, GIN on JSON columns",
                    "partitioning": "By date for audit logs",
                },
            },
            "migration_strategy": {
                "phase_1": "Implement DuckDB for analytics (Week 1)",
                "phase_2": "Add PostgreSQL for metadata (Week 2)",
                "phase_3": "Integrate both systems (Week 3)",
                "phase_4": "Performance optimization (Week 4)",
            },
            "performance_targets": {
                "dashboard_load_time": "<2 seconds",
                "bulk_conversion": "<30 seconds for 50MB dataset",
                "concurrent_users": "10+ simultaneous",
                "query_response": "<500ms for aggregated data",
            },
        }

        # Add storage-specific recommendations
        total_storage_gb = storage_requirements["current_storage"]["total_gb"]

        if total_storage_gb < 10:
            recommendations["deployment"] = "Single-node deployment sufficient"
        elif total_storage_gb < 100:
            recommendations["deployment"] = "Consider sharding for DuckDB"
        else:
            recommendations["deployment"] = "Distributed storage recommended"

        logger.info("Database recommendations generated")
        return recommendations

    def _analyze_xml_structure(self, xml_data: str) -> Dict[str, Any]:
        """Analizza la struttura di un dataset XML SDMX"""
        try:
            root = ET.fromstring(xml_data)

            # Count dimensions and measures
            dimensions = []
            measures = []

            # SDMX namespace handling
            namespaces = {
                "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
                "data": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
            }

            # Find observations
            observations = root.findall(".//data:Obs", namespaces)
            if not observations:
                # Try without namespace
                observations = root.findall(".//Obs")

            structure = {
                "observations_count": len(observations),
                "has_time_dimension": False,
                "has_geographic_dimension": False,
                "dimensions_count": 0,
                "measures_count": 0,
                "complexity": "simple",
            }

            # Analyze first observation for structure
            if observations:
                first_obs = observations[0]
                dims = first_obs.findall(".//data:ObsDimension", namespaces)
                if not dims:
                    dims = first_obs.findall(".//ObsDimension")

                structure["dimensions_count"] = len(dims)

                # Check for time and geographic dimensions
                for dim in dims:
                    concept = dim.get("concept", "").lower()
                    if "time" in concept or "tempo" in concept:
                        structure["has_time_dimension"] = True
                    if "geo" in concept or "territorio" in concept:
                        structure["has_geographic_dimension"] = True

            # Determine complexity
            if structure["observations_count"] > 10000:
                structure["complexity"] = "complex"
            elif structure["observations_count"] > 1000:
                structure["complexity"] = "medium"

            return structure

        except Exception as e:
            logger.warning(f"Error analyzing XML structure: {e}")
            return {"error": str(e), "complexity": "unknown"}

    def _is_time_series(self, structure: Dict[str, Any]) -> bool:
        """Determina se un dataset è una serie temporale"""
        return structure.get("has_time_dimension", False)

    def _is_structured(self, structure: Dict[str, Any]) -> bool:
        """Determina se un dataset è strutturato"""
        return structure.get("dimensions_count", 0) > 0

    def _analyze_volume_distribution(self, volume_data: List[Dict]) -> Dict[str, Any]:
        """Analizza la distribuzione dei volumi"""
        if not volume_data:
            return {"error": "No volume data available"}

        volumes = [item["volume_mb"] for item in volume_data]

        return {
            "count": len(volumes),
            "average_mb": round(sum(volumes) / len(volumes), 2),
            "min_mb": round(min(volumes), 2),
            "max_mb": round(max(volumes), 2),
            "total_mb": round(sum(volumes), 2),
        }

    def _summarize_structure_patterns(self, structure_patterns: Dict) -> Dict[str, Any]:
        """Riassume i pattern strutturali"""
        if not structure_patterns:
            return {"error": "No structure patterns available"}

        complexities = [
            p.get("complexity", "unknown") for p in structure_patterns.values()
        ]
        time_series_count = sum(
            1 for p in structure_patterns.values() if p.get("has_time_dimension")
        )
        geographic_count = sum(
            1 for p in structure_patterns.values() if p.get("has_geographic_dimension")
        )

        return {
            "total_analyzed": len(structure_patterns),
            "complexity_distribution": {
                "simple": complexities.count("simple"),
                "medium": complexities.count("medium"),
                "complex": complexities.count("complex"),
            },
            "time_series_datasets": time_series_count,
            "geographic_datasets": geographic_count,
            "time_series_percentage": round(
                (time_series_count / len(structure_patterns)) * 100, 1
            ),
            "geographic_percentage": round(
                (geographic_count / len(structure_patterns)) * 100, 1
            ),
        }

    def _analyze_access_patterns(self, datasets: List[Dict]) -> Dict[str, Any]:
        """Analizza i pattern di accesso"""
        # Simulate access patterns based on dataset categories
        categories = {}
        for dataset in datasets:
            category = dataset.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1

        return {
            "categories": categories,
            "estimated_patterns": {
                "dashboard_queries": "High frequency, small datasets",
                "bulk_conversions": "Low frequency, large datasets",
                "analytics_queries": "Medium frequency, aggregated data",
                "export_operations": "Low frequency, full datasets",
            },
            "peak_usage_times": {
                "business_hours": "09:00-18:00 (highest load)",
                "maintenance_window": "02:00-04:00 Saturday (ISTAT maintenance)",
                "optimal_batch_time": "22:00-06:00 (lowest API load)",
            },
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Analyze ISTAT data formats for database design"
    )
    parser.add_argument("--dataset", type=str, help="Analyze specific dataset ID")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Number of datasets to analyze in detail",
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    analyzer = DataFormatAnalyzer()

    try:
        if args.dataset:
            # Analyze single dataset
            logger.info(f"Analyzing single dataset: {args.dataset}")
            # Implementation for single dataset analysis
            print(f"Single dataset analysis for {args.dataset} not yet implemented")
            return

        # Full analysis
        logger.info("Starting full dataset analysis...")
        analysis_results = analyzer.analyze_istat_datasets(sample_size=args.sample_size)

        storage_requirements = analyzer.estimate_storage_requirements(analysis_results)
        analysis_results["storage_requirements"] = storage_requirements

        db_recommendations = analyzer.generate_database_recommendations(
            analysis_results, storage_requirements
        )
        analysis_results["database_recommendations"] = db_recommendations

        # Output results
        if args.format == "json":
            output = json.dumps(analysis_results, indent=2, ensure_ascii=False)
        else:
            output = _format_text_output(analysis_results)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            logger.info(f"Results saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


def _format_text_output(results: Dict[str, Any]) -> str:
    """Format results as readable text"""
    output = []
    output.append("# ISTAT Data Format Analysis Report")
    output.append(f"Generated: {results.get('timestamp', 'unknown')}")
    output.append("")

    # Summary
    output.append("## Summary")
    output.append(
        f"- Total datasets available: {results.get('total_datasets', 'unknown')}"
    )
    output.append(f"- Datasets analyzed: {results.get('analyzed_datasets', 'unknown')}")
    output.append("")

    # Data types
    data_types = results.get("data_types", {})
    output.append("## Data Types Distribution")
    for dtype, count in data_types.items():
        output.append(f"- {dtype.replace('_', ' ').title()}: {count}")
    output.append("")

    # Storage requirements
    storage = results.get("storage_requirements", {}).get("current_storage", {})
    output.append("## Storage Requirements")
    output.append(f"- Current total storage: {storage.get('total_gb', 'unknown')} GB")
    output.append(f"- Raw data: {storage.get('raw_data_gb', 'unknown')} GB")
    output.append(f"- Processed data: {storage.get('processed_data_gb', 'unknown')} GB")
    output.append("")

    # Database recommendations
    db_rec = results.get("database_recommendations", {})
    output.append("## Database Recommendations")
    output.append(
        f"- Hybrid approach recommended: {db_rec.get('hybrid_approach', {}).get('recommended', 'unknown')}"
    )
    output.append("- DuckDB for: Analytics, time-series, aggregations")
    output.append("- PostgreSQL for: Metadata, users, configuration")
    output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    main()
