"""
PowerBI Integration Demo for Osservatorio ISTAT Data Platform

This demo showcases the complete PowerBI integration capabilities:
- Star schema generation for optimal PowerBI performance
- DAX measures pre-calculation and caching
- Incremental refresh with SQLite tracking
- PowerBI template (.pbit) generation
- Quality score integration
- Metadata bridge functionality

Usage:
    # Issue #84: Use proper package imports
    python -m examples.powerbi_integration_demo
    
    # Legacy support (run from project root):
    python examples/powerbi_integration_demo.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path


# Issue #84: Proper package imports without sys.path manipulation
try:
    # Try package imports first (when run as module)
    from src.database.sqlite.repository import UnifiedDataRepository
    from src.integrations.powerbi.incremental import IncrementalRefreshManager
except ImportError:
    # Fallback for legacy usage (when run as script)
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from src.database.sqlite.repository import UnifiedDataRepository
    from src.integrations.powerbi.incremental import IncrementalRefreshManager
    from src.integrations.powerbi.metadata_bridge import MetadataBridge
    from src.integrations.powerbi.optimizer import PowerBIOptimizer
    from src.integrations.powerbi.templates import TemplateGenerator


def setup_demo_data(repository: UnifiedDataRepository) -> str:
    """Set up demo dataset with sample ISTAT data."""
    print("🔧 Setting up demo dataset...")

    dataset_id = "DEMO_POPOLAZIONE_REGIONI"

    # Register dataset in metadata
    success = repository.register_dataset_complete(
        dataset_id=dataset_id,
        name="Popolazione Residente per Regioni (Demo)",
        category="popolazione",
        description="Dataset demo per integrazione PowerBI - popolazione per regioni italiane",
        istat_agency="ISTAT",
        priority=8,
        metadata={
            "update_frequency": "annual",
            "geographic_level": "regioni",
            "source_url": "https://sdmx.istat.it/SDMXWS/rest/data/DCIS_POPRES1",
            "last_istat_update": "2024-01-15",
            "quality_threshold": 0.8,
        },
    )

    if success:
        print(f"✅ Dataset {dataset_id} registered successfully")
    else:
        print(f"❌ Failed to register dataset {dataset_id}")

    return dataset_id


def demo_star_schema_generation(optimizer: PowerBIOptimizer, dataset_id: str):
    """Demo star schema generation for PowerBI optimization."""
    print("\n📊 DEMO: Star Schema Generation")
    print("=" * 50)

    try:
        # Generate star schema
        print(f"Generating star schema for dataset: {dataset_id}")
        star_schema = optimizer.generate_star_schema(dataset_id)

        print(f"✅ Star schema generated successfully!")
        print(f"   Fact Table: {star_schema.fact_table}")
        print(f"   Dimension Tables: {len(star_schema.dimension_tables)}")

        for dim_table in star_schema.dimension_tables:
            print(f"     - {dim_table}")

        print(f"   Relationships: {len(star_schema.relationships)}")
        for rel in star_schema.relationships:
            print(
                f"     - {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}"
            )

        # Get performance metrics
        print("\n📈 Performance Metrics:")
        metrics = optimizer.get_performance_metrics(dataset_id)

        if "error" not in metrics:
            print(
                f"   Estimated PowerBI Load Time: {metrics.get('estimated_powerbi_load_time_ms', 0)}ms"
            )
            print(
                f"   Recommended Refresh Frequency: {metrics.get('recommended_refresh_frequency', 'unknown')}"
            )
            print(
                f"   Star Schema Optimization Potential: {metrics.get('star_schema_optimization_potential', 0)*100:.1f}%"
            )
        else:
            print(f"   ⚠️ Could not retrieve performance metrics: {metrics['error']}")

    except Exception as e:
        print(f"❌ Error generating star schema: {e}")


def demo_dax_measures(optimizer: PowerBIOptimizer, dataset_id: str):
    """Demo DAX measures pre-calculation engine."""
    print("\n📏 DEMO: DAX Measures Pre-calculation")
    print("=" * 50)

    try:
        # Get DAX measures
        print(f"Generating DAX measures for dataset: {dataset_id}")
        measures = optimizer.dax_engine.get_standard_measures(dataset_id)

        print(f"✅ Generated {len(measures)} DAX measures:")

        for measure_name, dax_formula in measures.items():
            print(f"\n📊 {measure_name}:")
            # Truncate long formulas for display
            if len(dax_formula) > 100:
                print(f"   {dax_formula[:97]}...")
            else:
                print(f"   {dax_formula}")

        # Test caching
        print("\n🚀 Testing measure caching...")
        import time

        start_time = time.time()
        measures_cached = optimizer.dax_engine.get_standard_measures(dataset_id)
        cache_time = time.time() - start_time

        print(f"✅ Cached retrieval completed in {cache_time*1000:.2f}ms")
        print(f"   Cache hit: {measures == measures_cached}")

    except Exception as e:
        print(f"❌ Error generating DAX measures: {e}")


def demo_incremental_refresh(
    refresh_manager: IncrementalRefreshManager, dataset_id: str
):
    """Demo incremental refresh system with SQLite tracking."""
    print("\n🔄 DEMO: Incremental Refresh System")
    print("=" * 50)

    try:
        # Create refresh policy
        print(f"Creating incremental refresh policy for dataset: {dataset_id}")
        policy = refresh_manager.create_refresh_policy(
            dataset_id=dataset_id,
            incremental_window_days=30,
            historical_window_years=5,
            refresh_frequency="daily",
        )

        print(f"✅ Refresh policy created:")
        print(f"   Dataset ID: {policy.dataset_id}")
        print(f"   Incremental Window: {policy.incremental_window_days} days")
        print(f"   Historical Window: {policy.historical_window_years} years")
        print(f"   Refresh Frequency: {policy.refresh_frequency}")
        print(f"   Enabled: {policy.enabled}")

        # Test change detection
        print("\n🔍 Testing change detection...")
        since_date = datetime.now() - timedelta(days=7)
        changes = refresh_manager.change_tracker.detect_changes(dataset_id, since_date)

        print(f"✅ Change detection completed:")
        print(f"   Has Changes: {changes.get('has_changes', False)}")
        print(f"   Total Changes: {changes.get('total_changes', 0)}")
        print(f"   Summary: {changes.get('change_summary', 'No summary available')}")

        # Execute incremental refresh
        print("\n⚡ Executing incremental refresh...")
        refresh_result = refresh_manager.execute_incremental_refresh(
            dataset_id, force=True  # Force refresh for demo
        )

        if "error" not in refresh_result:
            print(f"✅ Incremental refresh completed:")
            print(f"   Records Processed: {refresh_result.get('records_processed', 0)}")
            print(
                f"   Refresh Timestamp: {refresh_result.get('refresh_timestamp', 'unknown')}"
            )
        else:
            print(
                f"⚠️ Refresh completed with info: {refresh_result.get('skipped', refresh_result.get('error'))}"
            )

        # Get refresh status
        print("\n📊 Refresh Status:")
        status = refresh_manager.get_refresh_status(dataset_id)
        print(f"   Policy Enabled: {status.get('policy_enabled', False)}")
        print(f"   Last Refresh: {status.get('last_refresh', 'never')}")
        print(f"   Status: {status.get('status', 'unknown')}")

    except Exception as e:
        print(f"❌ Error in incremental refresh demo: {e}")


def demo_template_generation(template_generator: TemplateGenerator, dataset_id: str):
    """Demo PowerBI template (.pbit) generation."""
    print("\n📋 DEMO: PowerBI Template Generation")
    print("=" * 50)

    try:
        # Generate template
        print(f"Generating PowerBI template for dataset: {dataset_id}")
        template = template_generator.generate_template(
            dataset_id=dataset_id, template_name="Demo Popolazione Regioni Template"
        )

        print(f"✅ Template generated successfully:")
        print(f"   Template ID: {template.template_id}")
        print(f"   Name: {template.name}")
        print(f"   Category: {template.category}")
        print(f"   Description: {template.description}")

        print(f"\n📊 Template Components:")
        print(f"   DAX Measures: {len(template.dax_measures)}")
        for measure_name in list(template.dax_measures.keys())[:5]:  # Show first 5
            print(f"     - {measure_name}")
        if len(template.dax_measures) > 5:
            print(f"     ... and {len(template.dax_measures) - 5} more")

        print(f"   Visualizations: {len(template.visualizations)}")
        for viz in template.visualizations:
            print(f"     - {viz['type']}: {viz['title']}")

        # Create PBIT file
        print(f"\n💾 Creating PBIT file...")
        output_path = Path("templates/powerbi/demo_popolazione_template.pbit")

        try:
            created_path = template_generator.create_pbit_file(
                template=template, output_path=output_path, include_sample_data=True
            )

            print(f"✅ PBIT file created: {created_path}")
            print(f"   File size: {created_path.stat().st_size} bytes")

            # Verify PBIT structure
            import zipfile

            if zipfile.is_zipfile(created_path):
                with zipfile.ZipFile(created_path, "r") as pbit:
                    files = pbit.namelist()
                    print(f"   PBIT contents: {len(files)} files")
                    for file in files:
                        print(f"     - {file}")

        except Exception as e:
            print(f"⚠️ Could not create PBIT file: {e}")

        # Show available templates
        print(f"\n📚 Available Templates:")
        templates = template_generator.get_available_templates()
        for tmpl in templates:
            print(
                f"   - {tmpl.get('name', 'Unknown')} ({tmpl.get('category', 'unknown')})"
            )

    except Exception as e:
        print(f"❌ Error in template generation demo: {e}")


def demo_metadata_bridge(metadata_bridge: MetadataBridge, dataset_id: str):
    """Demo metadata bridge functionality."""
    print("\n🌉 DEMO: Metadata Bridge")
    print("=" * 50)

    try:
        # Create dataset lineage
        print(f"Creating dataset lineage for: {dataset_id}")
        lineage = metadata_bridge.create_dataset_lineage(
            dataset_id=dataset_id,
            source_datasets=["ISTAT_SDMX_API"],
            transformation_steps=[
                {
                    "name": "data_enrichment",
                    "description": "Enriched with territory names and geographic metadata",
                    "metadata": {
                        "enrichment_version": "2.1",
                        "territory_mapping": "ISTAT_2024",
                    },
                },
                {
                    "name": "quality_validation",
                    "description": "Applied ISTAT quality validation rules",
                    "metadata": {"validation_rules": 15, "threshold": 0.8},
                },
            ],
        )

        print(f"✅ Dataset lineage created:")
        print(f"   Dataset ID: {lineage.dataset_id}")
        print(f"   Source System: {lineage.source_system}")
        print(f"   Dependencies: {lineage.dependencies}")
        print(f"   Transformation Steps: {len(lineage.transformations)}")

        for step in lineage.transformations:
            print(f"     - {step['step']}: {step['description']}")

        # Propagate quality scores
        print(f"\n🎯 Propagating quality scores...")
        quality_result = metadata_bridge.propagate_quality_scores(dataset_id)

        if "error" not in quality_result:
            quality_scores = quality_result["quality_scores"]
            print(f"✅ Quality scores propagated:")
            print(f"   Overall Quality: {quality_scores.get('overall_quality', 0):.3f}")
            print(
                f"   Territories Analyzed: {quality_scores.get('territories_analyzed', 0)}"
            )
            print(f"   Total Records: {quality_scores.get('total_records', 0)}")

            quality_measures = quality_result["quality_measures"]
            print(f"   Quality Measures Created: {len(quality_measures)}")
            for measure_name in quality_measures.keys():
                print(f"     - {measure_name}")
        else:
            print(f"⚠️ Quality propagation info: {quality_result['error']}")

        # Sync usage analytics
        print(f"\n📊 Syncing usage analytics...")
        usage_metrics = metadata_bridge.sync_usage_analytics(dataset_id)

        print(f"✅ Usage analytics synchronized:")
        print(f"   Dataset ID: {usage_metrics.dataset_id}")
        print(f"   Views: {usage_metrics.views}")
        print(f"   Refreshes: {usage_metrics.refreshes}")
        print(f"   Unique Users: {len(usage_metrics.unique_users)}")
        print(f"   Reports Using: {len(usage_metrics.reports_using)}")

        # Generate governance report
        print(f"\n📋 Generating governance report...")
        governance_report = metadata_bridge.get_governance_report(dataset_id)

        if "error" not in governance_report:
            print(f"✅ Governance report generated:")
            print(f"   Report Generated: {governance_report['report_generated']}")
            print(f"   Datasets Analyzed: {governance_report['datasets_analyzed']}")

            if governance_report["datasets"]:
                dataset_gov = governance_report["datasets"][0]
                print(f"   Dataset Governance:")
                print(f"     - Has Lineage: {dataset_gov.get('has_lineage', False)}")
                print(
                    f"     - Has Usage Data: {dataset_gov.get('has_usage_data', False)}"
                )
                print(
                    f"     - Quality Score: {dataset_gov.get('quality_score', 0):.3f}"
                )
                print(
                    f"     - PowerBI Integrated: {dataset_gov.get('powerbi_integrated', False)}"
                )
        else:
            print(f"⚠️ Governance report error: {governance_report['error']}")

    except Exception as e:
        print(f"❌ Error in metadata bridge demo: {e}")


def demo_end_to_end_integration(
    optimizer: PowerBIOptimizer,
    refresh_manager: IncrementalRefreshManager,
    template_generator: TemplateGenerator,
    metadata_bridge: MetadataBridge,
    dataset_id: str,
):
    """Demo complete end-to-end PowerBI integration pipeline."""
    print("\n🚀 DEMO: End-to-End PowerBI Integration Pipeline")
    print("=" * 60)

    pipeline_steps = [
        "Star Schema Generation",
        "Incremental Refresh Setup",
        "Template Generation",
        "Metadata Bridge Setup",
        "Quality Score Integration",
        "Governance Validation",
    ]

    print("Pipeline Steps:")
    for i, step in enumerate(pipeline_steps, 1):
        print(f"   {i}. {step}")

    print(f"\n🔄 Executing pipeline for dataset: {dataset_id}")

    try:
        # Step 1: Star Schema Generation
        print(f"\n1️⃣ Generating star schema...")
        star_schema = optimizer.generate_star_schema(dataset_id)
        print(
            f"   ✅ Star schema created with {len(star_schema.dimension_tables)} dimensions"
        )

        # Step 2: Incremental Refresh Setup
        print(f"\n2️⃣ Setting up incremental refresh...")
        refresh_policy = refresh_manager.create_refresh_policy(
            dataset_id, refresh_frequency="daily"
        )
        print(
            f"   ✅ Refresh policy created (frequency: {refresh_policy.refresh_frequency})"
        )

        # Step 3: Template Generation
        print(f"\n3️⃣ Generating PowerBI template...")
        template = template_generator.generate_template(dataset_id)
        print(
            f"   ✅ Template created with {len(template.visualizations)} visualizations"
        )

        # Step 4: Metadata Bridge Setup
        print(f"\n4️⃣ Setting up metadata bridge...")
        lineage = metadata_bridge.create_dataset_lineage(dataset_id)
        print(
            f"   ✅ Lineage created with {len(lineage.transformations)} transformation steps"
        )

        # Step 5: Quality Score Integration
        print(f"\n5️⃣ Integrating quality scores...")
        quality_result = metadata_bridge.propagate_quality_scores(dataset_id)
        if "error" not in quality_result:
            overall_quality = quality_result["quality_scores"].get("overall_quality", 0)
            print(f"   ✅ Quality scores integrated (overall: {overall_quality:.3f})")
        else:
            print(
                f"   ⚠️ Quality integration: {quality_result.get('error', 'No data available')}"
            )

        # Step 6: Governance Validation
        print(f"\n6️⃣ Validating governance...")
        governance = metadata_bridge.get_governance_report(dataset_id)
        if "error" not in governance and governance["datasets"]:
            dataset_gov = governance["datasets"][0]
            print(f"   ✅ Governance validated:")
            print(f"      - Lineage: {'✅' if dataset_gov.get('has_lineage') else '❌'}")
            print(
                f"      - Usage Data: {'✅' if dataset_gov.get('has_usage_data') else '❌'}"
            )
            print(
                f"      - PowerBI Integration: {'✅' if dataset_gov.get('powerbi_integrated') else '❌'}"
            )
        else:
            print(f"   ⚠️ Governance validation: Limited data available")

        print(f"\n🎉 End-to-end pipeline completed successfully!")
        print(f"   Dataset {dataset_id} is now fully integrated with PowerBI")

        # Summary
        print(f"\n📊 Integration Summary:")
        print(f"   - Star schema optimized for PowerBI performance")
        print(f"   - Incremental refresh configured for daily updates")
        print(f"   - PowerBI template ready for deployment")
        print(f"   - Data lineage tracked and documented")
        print(f"   - Quality scores integrated into reports")
        print(f"   - Governance controls in place")

    except Exception as e:
        print(f"❌ Pipeline error: {e}")


def main():
    """Main demo function."""
    print("🚀 Osservatorio PowerBI Integration Demo")
    print("=" * 60)
    print("This demo showcases the complete PowerBI integration capabilities")
    print("for the Osservatorio ISTAT Data Platform.\n")

    try:
        # Initialize components
        print("🔧 Initializing PowerBI integration components...")
        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)
        refresh_manager = IncrementalRefreshManager(repository)
        template_generator = TemplateGenerator(repository, optimizer)
        metadata_bridge = MetadataBridge(repository)

        print("✅ All components initialized successfully\n")

        # Setup demo data
        dataset_id = setup_demo_data(repository)

        # Run demos
        demo_star_schema_generation(optimizer, dataset_id)
        demo_dax_measures(optimizer, dataset_id)
        demo_incremental_refresh(refresh_manager, dataset_id)
        demo_template_generation(template_generator, dataset_id)
        demo_metadata_bridge(metadata_bridge, dataset_id)

        # End-to-end integration demo
        demo_end_to_end_integration(
            optimizer, refresh_manager, template_generator, metadata_bridge, dataset_id
        )

        print(f"\n🎯 Demo completed successfully!")
        print(f"All PowerBI integration features have been demonstrated.")

        # Cleanup note
        print(f"\n🧹 Note: Demo dataset '{dataset_id}' remains in the system.")
        print(f"You can use it for further testing or remove it manually if needed.")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
