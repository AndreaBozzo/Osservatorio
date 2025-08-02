"""
Integration Tests for PowerBI Integration Components

Tests the complete PowerBI integration pipeline including:
- PowerBIOptimizer with star schema generation
- DAX measures pre-calculation
- Incremental refresh system
- Template generation
- Quality score integration
- Metadata bridge functionality
"""
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.database.sqlite.repository import UnifiedDataRepository
from src.integrations.powerbi.incremental import (
    IncrementalRefreshManager,
    RefreshPolicy,
)
from src.integrations.powerbi.metadata_bridge import DatasetLineage, MetadataBridge
from src.integrations.powerbi.optimizer import PowerBIOptimizer, StarSchemaDefinition
from src.integrations.powerbi.templates import PowerBITemplate, TemplateGenerator


class TestPowerBIIntegration:
    """Integration tests for PowerBI components."""

    def setup_method(self):
        """Set up test environment."""
        self.repository = UnifiedDataRepository()
        self.optimizer = PowerBIOptimizer(self.repository)
        self.incremental_manager = IncrementalRefreshManager(self.repository)
        self.template_generator = TemplateGenerator(self.repository, self.optimizer)
        self.metadata_bridge = MetadataBridge(self.repository)

        # Create test dataset
        self.test_dataset_id = "TEST_POWERBI_DATASET"
        self._create_test_dataset()

    def _create_test_dataset(self, sample_data=None):
        """Create test dataset with sample data."""
        # Register dataset in metadata
        success = self.repository.register_dataset_complete(
            dataset_id=self.test_dataset_id,
            name="Test PowerBI Dataset",
            category="popolazione",
            description="Test dataset for PowerBI integration",
            priority=8,
            metadata={
                "update_frequency": "daily",
                "geographic_level": "regioni",
                "quality_score": 0.85,
            },
        )
        assert success, "Failed to register test dataset"

        # Use provided sample data or fixture data
        if sample_data:
            # Insert data (would use actual DuckDB insert in real implementation)
            df = pd.DataFrame(sample_data)
            # This is a simplified version - real implementation would use DuckDB manager

    def test_star_schema_generation(self, sample_powerbi_test_data):
        """Test star schema generation for PowerBI optimization."""
        # Day 6: Use centralized fixture data
        self._create_test_dataset(sample_powerbi_test_data)

        # Generate star schema
        star_schema = self.optimizer.generate_star_schema(self.test_dataset_id)

        # Verify star schema structure
        assert isinstance(star_schema, StarSchemaDefinition)
        assert star_schema.fact_table == f"fact_{self.test_dataset_id.lower()}"

        # Check standard dimensions
        expected_dimensions = [
            "dim_time",
            "dim_territory",
            "dim_measure",
            "dim_dataset_metadata",
        ]
        for dim in expected_dimensions:
            assert dim in star_schema.dimension_tables

        # Check population-specific dimensions
        assert "dim_age_group" in star_schema.dimension_tables
        assert "dim_gender" in star_schema.dimension_tables

        # Verify relationships
        assert len(star_schema.relationships) >= 3
        for rel in star_schema.relationships:
            assert rel["cardinality"] == "many_to_one"
            assert rel["from_table"] == star_schema.fact_table

    def test_dax_measures_generation(self):
        """Test DAX measures pre-calculation engine."""
        # Get standard measures
        measures = self.optimizer.dax_engine.get_standard_measures(self.test_dataset_id)

        # Verify base measures
        expected_base_measures = [
            "Total Observations",
            "Average Value",
            "Latest Period",
            "Quality Score",
            "YoY Growth",
        ]

        for measure in expected_base_measures:
            assert measure in measures
            assert isinstance(measures[measure], str)
            assert len(measures[measure]) > 0

        # Verify population-specific measures
        assert "Total Population" in measures
        assert "Population Growth Rate" in measures
        assert "Population Density" in measures

        # Test measure caching
        measures2 = self.optimizer.dax_engine.get_standard_measures(
            self.test_dataset_id
        )
        assert measures == measures2  # Should return cached result

    def test_performance_metrics(self):
        """Test PowerBI performance metrics calculation."""
        metrics = self.optimizer.get_performance_metrics(self.test_dataset_id)

        # Verify metric structure
        assert "total_records" in metrics
        assert "territories" in metrics
        assert "avg_quality_score" in metrics
        assert "estimated_powerbi_load_time_ms" in metrics
        assert "recommended_refresh_frequency" in metrics

        # Verify optimization potential calculation
        assert "star_schema_optimization_potential" in metrics
        assert isinstance(metrics["star_schema_optimization_potential"], float)

    def test_incremental_refresh_policy(self):
        """Test incremental refresh policy creation and management."""
        # Create refresh policy
        policy = self.incremental_manager.create_refresh_policy(
            dataset_id=self.test_dataset_id,
            incremental_window_days=15,
            historical_window_years=3,
            refresh_frequency="daily",
        )

        # Verify policy creation
        assert isinstance(policy, RefreshPolicy)
        assert policy.dataset_id == self.test_dataset_id
        assert policy.incremental_window_days == 15
        assert policy.enabled == True

        # Test policy retrieval
        retrieved_policy = self.incremental_manager.get_refresh_policy(
            self.test_dataset_id
        )
        assert retrieved_policy is not None
        assert retrieved_policy.dataset_id == self.test_dataset_id
        assert retrieved_policy.refresh_frequency == "daily"

    def test_change_detection(self):
        """Test change detection for incremental refresh."""
        # Test change detection
        since_date = datetime.now() - timedelta(days=1)
        changes = self.incremental_manager.change_tracker.detect_changes(
            self.test_dataset_id, since_date
        )

        # Verify change detection structure
        assert "has_changes" in changes
        assert "total_changes" in changes
        assert "change_summary" in changes

        # Test incremental data retrieval
        incremental_data = self.incremental_manager.change_tracker.get_incremental_data(
            self.test_dataset_id, since_date, limit=100
        )

        # Verify incremental data is DataFrame
        assert isinstance(incremental_data, pd.DataFrame)

    def test_refresh_execution(self):
        """Test incremental refresh execution."""
        # Create refresh policy first
        self.incremental_manager.create_refresh_policy(self.test_dataset_id)

        # Execute refresh
        result = self.incremental_manager.execute_incremental_refresh(
            self.test_dataset_id, force=True  # Force refresh for testing
        )

        # Verify refresh result
        assert "dataset_id" in result
        assert result["dataset_id"] == self.test_dataset_id
        assert "refresh_timestamp" in result

        # Test refresh status
        status = self.incremental_manager.get_refresh_status(self.test_dataset_id)
        assert "dataset_id" in status
        assert "policy_enabled" in status
        assert "last_refresh" in status

    def test_template_generation(self):
        """Test PowerBI template generation."""
        # Generate template
        template = self.template_generator.generate_template(
            dataset_id=self.test_dataset_id, template_name="Test Population Template"
        )

        # Verify template structure
        assert isinstance(template, PowerBITemplate)
        assert template.template_id == f"template_{self.test_dataset_id}"
        assert template.category == "popolazione"
        assert len(template.visualizations) > 0
        assert len(template.dax_measures) > 0

        # Verify population-specific visualizations
        viz_types = [viz["type"] for viz in template.visualizations]
        assert "line_chart" in viz_types
        assert "map" in viz_types
        assert "donut_chart" in viz_types

    def test_pbit_file_creation(self):
        """Test PowerBI template (.pbit) file creation."""
        # Generate template
        template = self.template_generator.generate_template(self.test_dataset_id)

        # Create temporary output path
        output_path = Path("test_template.pbit")

        try:
            # Create PBIT file
            created_path = self.template_generator.create_pbit_file(
                template=template, output_path=output_path, include_sample_data=True
            )

            # Verify file creation
            assert created_path.exists()
            assert created_path.suffix == ".pbit"

            # Verify it's a valid ZIP file (PBIT files are ZIP archives)
            import zipfile

            assert zipfile.is_zipfile(created_path)

            # Test ZIP contents
            with zipfile.ZipFile(created_path, "r") as pbit_file:
                file_list = pbit_file.namelist()
                assert "Report/Layout" in file_list
                assert "DataModel" in file_list
                assert "Metadata" in file_list

        finally:
            # Cleanup test file
            if output_path.exists():
                output_path.unlink()

    def test_template_library(self):
        """Test template library functionality."""
        # Generate and store template
        template = self.template_generator.generate_template(self.test_dataset_id)

        # Get available templates
        templates = self.template_generator.get_available_templates()

        # Verify template in library
        assert len(templates) > 0
        template_ids = [t.get("template_id") for t in templates]
        assert template.template_id in template_ids

    def test_dataset_lineage_creation(self):
        """Test dataset lineage tracking."""
        # Create lineage
        lineage = self.metadata_bridge.create_dataset_lineage(
            dataset_id=self.test_dataset_id,
            source_datasets=["ISTAT_API"],
            transformation_steps=[
                {
                    "name": "territory_mapping",
                    "description": "Map ISTAT territory codes to names",
                    "metadata": {"mapping_version": "2.1"},
                }
            ],
        )

        # Verify lineage structure
        assert isinstance(lineage, DatasetLineage)
        assert lineage.dataset_id == self.test_dataset_id
        assert lineage.source_system == "ISTAT"
        assert len(lineage.transformations) >= 4  # 3 standard + 1 custom

        # Verify standard transformations
        transformation_steps = [t["step"] for t in lineage.transformations]
        assert "data_extraction" in transformation_steps
        assert "data_validation" in transformation_steps
        assert "quality_scoring" in transformation_steps
        assert "territory_mapping" in transformation_steps

    def test_quality_score_sync(self):
        """Test quality score synchronization."""
        # Get quality scores
        quality_scores = self.metadata_bridge.quality_sync.get_quality_scores(
            self.test_dataset_id
        )

        # Verify quality score structure
        assert "overall_quality" in quality_scores
        assert isinstance(quality_scores["overall_quality"], float)

        # Create quality measures
        quality_measures = self.metadata_bridge.quality_sync.create_quality_measure(
            self.test_dataset_id
        )

        # Verify quality measures
        expected_measures = ["Quality Score", "Quality Grade", "Quality Trend"]
        for measure in expected_measures:
            assert measure in quality_measures
            assert "fact_" in quality_measures[measure]  # Should reference fact table

    def test_quality_score_propagation(self):
        """Test quality score propagation to PowerBI."""
        # Propagate quality scores
        result = self.metadata_bridge.propagate_quality_scores(self.test_dataset_id)

        # Verify propagation result
        assert "dataset_id" in result
        assert result["dataset_id"] == self.test_dataset_id
        assert "quality_scores" in result
        assert "quality_measures" in result
        assert "propagated_at" in result

        # Verify quality scores structure
        quality_scores = result["quality_scores"]
        assert "overall_quality" in quality_scores

        # Verify quality measures
        quality_measures = result["quality_measures"]
        assert len(quality_measures) >= 3

    def test_usage_analytics_sync(self):
        """Test usage analytics synchronization."""
        # Sync usage analytics
        metrics = self.metadata_bridge.sync_usage_analytics(self.test_dataset_id)

        # Verify metrics structure
        assert metrics.dataset_id == self.test_dataset_id
        assert isinstance(metrics.views, int)
        assert isinstance(metrics.refreshes, int)
        assert isinstance(metrics.reports_using, list)
        assert isinstance(metrics.dashboards_using, list)

        # Test metrics serialization
        metrics_dict = metrics.to_dict()
        assert "dataset_id" in metrics_dict
        assert "unique_users" in metrics_dict

    def test_governance_report(self):
        """Test data governance report generation."""
        # Create lineage and sync usage for test dataset
        self.metadata_bridge.create_dataset_lineage(self.test_dataset_id)
        self.metadata_bridge.sync_usage_analytics(self.test_dataset_id)

        # Generate governance report for specific dataset
        report = self.metadata_bridge.get_governance_report(self.test_dataset_id)

        # Verify report structure
        assert "report_generated" in report
        assert "datasets_analyzed" in report
        assert "datasets" in report
        assert len(report["datasets"]) == 1

        # Verify dataset governance data
        dataset_gov = report["datasets"][0]
        assert dataset_gov["dataset_id"] == self.test_dataset_id
        assert "has_lineage" in dataset_gov
        assert "has_usage_data" in dataset_gov
        assert "quality_score" in dataset_gov
        assert "powerbi_integrated" in dataset_gov

        # Test full governance report
        full_report = self.metadata_bridge.get_governance_report()
        assert "summary" in full_report
        assert "datasets_analyzed" in full_report

    def test_end_to_end_powerbi_pipeline(self):
        """Test complete PowerBI integration pipeline."""
        # 1. Generate star schema
        star_schema = self.optimizer.generate_star_schema(self.test_dataset_id)
        assert star_schema is not None

        # 2. Create incremental refresh policy
        policy = self.incremental_manager.create_refresh_policy(self.test_dataset_id)
        assert policy is not None

        # 3. Generate PowerBI template
        template = self.template_generator.generate_template(self.test_dataset_id)
        assert template is not None

        # 4. Create dataset lineage
        lineage = self.metadata_bridge.create_dataset_lineage(self.test_dataset_id)
        assert lineage is not None

        # 5. Propagate quality scores
        quality_result = self.metadata_bridge.propagate_quality_scores(
            self.test_dataset_id
        )
        assert "error" not in quality_result

        # 6. Execute incremental refresh
        refresh_result = self.incremental_manager.execute_incremental_refresh(
            self.test_dataset_id, force=True
        )
        assert "error" not in refresh_result

        # 7. Generate governance report
        governance = self.metadata_bridge.get_governance_report(self.test_dataset_id)
        assert "error" not in governance

        # Verify end-to-end integration
        dataset_gov = governance["datasets"][0]
        assert dataset_gov["has_lineage"] == True
        assert dataset_gov["powerbi_integrated"] == True
        assert dataset_gov["quality_score"] > 0

    def test_error_handling(self):
        """Test error handling in PowerBI integration."""
        # Test with non-existent dataset
        invalid_dataset = "INVALID_DATASET_ID"

        # Should handle missing dataset gracefully
        with pytest.raises(ValueError):
            self.optimizer.generate_star_schema(invalid_dataset)

        # Incremental refresh should return error info
        refresh_result = self.incremental_manager.execute_incremental_refresh(
            invalid_dataset
        )
        assert "error" in refresh_result

        # Template generation should raise ValueError
        with pytest.raises(ValueError):
            self.template_generator.generate_template(invalid_dataset)

        # Quality sync should return error info
        quality_result = self.metadata_bridge.propagate_quality_scores(invalid_dataset)
        assert "error" in quality_result

    def test_caching_performance(self):
        """Test caching mechanisms for performance."""
        # Test star schema caching
        schema1 = self.optimizer.generate_star_schema(self.test_dataset_id)
        schema2 = self.optimizer.generate_star_schema(self.test_dataset_id)

        # Should return same instance from cache
        assert schema1.created_at == schema2.created_at

        # Test DAX measures caching
        measures1 = self.optimizer.dax_engine.get_standard_measures(
            self.test_dataset_id
        )
        measures2 = self.optimizer.dax_engine.get_standard_measures(
            self.test_dataset_id
        )

        # Should return same measures from cache
        assert measures1 == measures2

    def teardown_method(self):
        """Clean up test environment."""
        # Basic cleanup - close any connections
        try:
            if hasattr(self, "repository"):
                del self.repository
        except:
            pass


class TestPowerBIPerformance:
    """Performance tests for PowerBI integration."""

    def test_star_schema_generation_performance(self):
        """Test star schema generation performance."""
        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)

        # Create test dataset
        test_dataset = "PERF_TEST_DATASET"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Performance Test Dataset",
            category="economia",
            description="Performance testing",
        )

        import time

        start_time = time.time()

        # Generate star schema
        star_schema = optimizer.generate_star_schema(test_dataset)

        end_time = time.time()
        generation_time = end_time - start_time

        # Should complete within reasonable time
        assert generation_time < 5.0  # 5 second limit
        assert star_schema is not None

    def test_template_generation_performance(self):
        """Test template generation performance."""
        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)
        template_gen = TemplateGenerator(repository, optimizer)

        # Create test dataset
        test_dataset = "TEMPLATE_PERF_TEST"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Template Performance Test",
            category="popolazione",
            description="Template performance testing",
        )

        import time

        start_time = time.time()

        # Generate template
        template = template_gen.generate_template(test_dataset)

        end_time = time.time()
        generation_time = end_time - start_time

        # Should complete within reasonable time
        assert generation_time < 3.0  # 3 second limit
        assert template is not None
        assert len(template.visualizations) > 0
