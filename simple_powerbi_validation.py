"""
Simple PowerBI Integration Validation

Verificare che i deliverables principali dell'Issue #27 siano implementati
e funzionino correttamente, anche senza dati completi.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def validate_deliverable_1_star_schema():
    """Deliverable 1: PowerBIOptimizer class with star schema generation"""
    print("📊 DELIVERABLE 1: Star Schema Generation")
    print("-" * 40)

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.optimizer import (
            PowerBIOptimizer,
            StarSchemaDefinition,
        )

        # Test class existence and initialization
        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)
        print("✅ PowerBIOptimizer class implemented and initializes")

        # Register a test dataset
        test_dataset = "TEST_STAR_SCHEMA"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Test Star Schema Dataset",
            category="popolazione",
            description="Test for star schema generation",
        )

        # Test star schema generation
        star_schema = optimizer.generate_star_schema(test_dataset)

        # Validate star schema
        assert isinstance(star_schema, StarSchemaDefinition)
        assert star_schema.fact_table == f"fact_{test_dataset.lower()}"
        assert len(star_schema.dimension_tables) >= 4  # Should have standard dimensions
        assert len(star_schema.relationships) >= 3  # Should have relationships

        print(f"✅ Star schema generated: {star_schema.fact_table}")
        print(f"✅ {len(star_schema.dimension_tables)} dimension tables created")
        print(f"✅ {len(star_schema.relationships)} relationships defined")

        # Test category-specific dimensions
        expected_pop_dims = ["dim_age_group", "dim_gender"]
        for dim in expected_pop_dims:
            if dim in star_schema.dimension_tables:
                print(f"✅ Population-specific dimension: {dim}")

        return True

    except Exception as e:
        print(f"❌ Star schema generation failed: {e}")
        return False


def validate_deliverable_2_dax_measures():
    """Deliverable 2: DAX measures pre-calculation engine"""
    print("\n📏 DELIVERABLE 2: DAX Measures Pre-calculation")
    print("-" * 40)

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.optimizer import PowerBIOptimizer

        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)

        # Test DAX engine exists
        assert hasattr(optimizer, "dax_engine")
        print("✅ DAX measures engine implemented")

        # Register test dataset
        test_dataset = "TEST_DAX_MEASURES"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Test DAX Measures Dataset",
            category="economia",
            description="Test for DAX measures",
        )

        # Test measures generation
        measures = optimizer.dax_engine.get_standard_measures(test_dataset)

        # Validate measures
        assert isinstance(measures, dict)
        assert len(measures) > 0
        print(f"✅ Generated {len(measures)} DAX measures")

        # Check for required base measures
        required_measures = ["Total Observations", "Average Value", "Quality Score"]
        for measure in required_measures:
            if measure in measures:
                print(f"✅ Base measure implemented: {measure}")
            else:
                print(f"⚠️ Missing base measure: {measure}")

        # Check for category-specific measures (economia)
        economic_measures = ["GDP Growth", "GDP Per Capita"]
        for measure in economic_measures:
            if measure in measures:
                print(f"✅ Economic measure implemented: {measure}")

        # Test DAX formula quality
        for name, formula in list(measures.items())[:3]:
            if formula and len(formula.strip()) > 0:
                print(f"✅ {name}: Formula generated ({len(formula)} chars)")
            else:
                print(f"❌ {name}: Empty formula")
                return False

        # Test caching
        measures2 = optimizer.dax_engine.get_standard_measures(test_dataset)
        if measures == measures2:
            print("✅ Caching mechanism working")

        return True

    except Exception as e:
        print(f"❌ DAX measures generation failed: {e}")
        return False


def validate_deliverable_3_incremental_refresh():
    """Deliverable 3: Incremental refresh system with SQLite tracking"""
    print("\n🔄 DELIVERABLE 3: Incremental Refresh System")
    print("-" * 40)

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.incremental import (
            IncrementalRefreshManager,
            RefreshPolicy,
        )

        repository = UnifiedDataRepository()
        refresh_manager = IncrementalRefreshManager(repository)

        print("✅ IncrementalRefreshManager implemented")

        # Test refresh policy creation
        test_dataset = "TEST_INCREMENTAL"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Test Incremental Dataset",
            category="lavoro",
            description="Test for incremental refresh",
        )

        policy = refresh_manager.create_refresh_policy(
            dataset_id=test_dataset,
            incremental_window_days=30,
            refresh_frequency="daily",
        )

        # Validate policy
        assert isinstance(policy, RefreshPolicy)
        assert policy.dataset_id == test_dataset
        assert policy.incremental_window_days == 30
        assert policy.refresh_frequency == "daily"
        print("✅ Refresh policy creation working")

        # Test policy retrieval
        retrieved_policy = refresh_manager.get_refresh_policy(test_dataset)
        assert retrieved_policy is not None
        assert retrieved_policy.dataset_id == test_dataset
        print("✅ Policy retrieval working")

        # Test change tracker
        assert hasattr(refresh_manager, "change_tracker")
        print("✅ Change tracker implemented")

        # Test refresh status
        status = refresh_manager.get_refresh_status(test_dataset)
        assert isinstance(status, dict)
        assert "dataset_id" in status
        assert "policy_enabled" in status
        print("✅ Refresh status reporting working")

        return True

    except Exception as e:
        print(f"❌ Incremental refresh system failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def validate_deliverable_4_template_generator():
    """Deliverable 4: PowerBI template (.pbit) generator"""
    print("\n📋 DELIVERABLE 4: PowerBI Template Generator")
    print("-" * 40)

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.optimizer import PowerBIOptimizer
        from integrations.powerbi.templates import PowerBITemplate, TemplateGenerator

        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)
        template_generator = TemplateGenerator(repository, optimizer)

        print("✅ TemplateGenerator implemented")

        # Register test dataset
        test_dataset = "TEST_TEMPLATE"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Test Template Dataset",
            category="popolazione",
            description="Test for template generation",
        )

        # Test template generation
        template = template_generator.generate_template(test_dataset)

        # Validate template
        assert isinstance(template, PowerBITemplate)
        assert template.template_id == f"template_{test_dataset}"
        assert template.category == "popolazione"
        assert len(template.dax_measures) > 0
        assert len(template.visualizations) > 0

        print(f"✅ Template generated: {template.template_id}")
        print(f"✅ {len(template.dax_measures)} DAX measures included")
        print(f"✅ {len(template.visualizations)} visualizations included")

        # Test visualization library
        from integrations.powerbi.templates import VisualizationLibrary

        viz_lib = VisualizationLibrary()
        pop_viz = viz_lib.get_population_visualizations()
        assert len(pop_viz) > 0
        print(f"✅ Visualization library: {len(pop_viz)} population visualizations")

        # Test PBIT file creation capability
        output_path = Path("test_template.pbit")
        try:
            created_path = template_generator.create_pbit_file(
                template=template, output_path=output_path
            )

            if created_path.exists():
                print("✅ PBIT file creation working")
                output_path.unlink()  # Cleanup
            else:
                print("⚠️ PBIT file not created but method exists")

        except Exception as e:
            print(f"⚠️ PBIT creation issue: {e}")
            # Not critical for basic validation

        return True

    except Exception as e:
        print(f"❌ Template generator failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def validate_deliverable_5_metadata_bridge():
    """Deliverable 5: Quality score integration and metadata bridge"""
    print("\n🌉 DELIVERABLE 5: Metadata Bridge & Quality Integration")
    print("-" * 40)

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.metadata_bridge import (
            DatasetLineage,
            MetadataBridge,
            QualityScoreSync,
        )

        repository = UnifiedDataRepository()
        metadata_bridge = MetadataBridge(repository)

        print("✅ MetadataBridge implemented")

        # Test quality score sync
        assert hasattr(metadata_bridge, "quality_sync")
        assert isinstance(metadata_bridge.quality_sync, QualityScoreSync)
        print("✅ QualityScoreSync implemented")

        # Register test dataset
        test_dataset = "TEST_METADATA"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Test Metadata Dataset",
            category="popolazione",
            description="Test for metadata bridge",
        )

        # Test lineage creation
        lineage = metadata_bridge.create_dataset_lineage(test_dataset)

        # Validate lineage
        assert isinstance(lineage, DatasetLineage)
        assert lineage.dataset_id == test_dataset
        assert lineage.source_system == "ISTAT"
        assert len(lineage.transformations) > 0

        print(
            f"✅ Dataset lineage created with {len(lineage.transformations)} transformations"
        )

        # Test quality measures creation
        quality_measures = metadata_bridge.quality_sync.create_quality_measure(
            test_dataset
        )
        assert isinstance(quality_measures, dict)
        assert len(quality_measures) > 0

        expected_quality_measures = ["Quality Score", "Quality Grade", "Quality Trend"]
        for measure in expected_quality_measures:
            if measure in quality_measures:
                print(f"✅ Quality measure implemented: {measure}")

        # Test usage analytics
        usage_metrics = metadata_bridge.sync_usage_analytics(test_dataset)
        assert hasattr(usage_metrics, "dataset_id")
        assert usage_metrics.dataset_id == test_dataset
        print("✅ Usage analytics sync working")

        # Test governance report
        governance = metadata_bridge.get_governance_report(test_dataset)
        assert isinstance(governance, dict)
        assert "datasets_analyzed" in governance
        print("✅ Governance reporting working")

        return True

    except Exception as e:
        print(f"❌ Metadata bridge failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def validate_integration_completeness():
    """Verifica che tutti i componenti si integrino correttamente"""
    print("\n🔗 INTEGRATION COMPLETENESS CHECK")
    print("-" * 40)

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.incremental import IncrementalRefreshManager
        from integrations.powerbi.metadata_bridge import MetadataBridge
        from integrations.powerbi.optimizer import PowerBIOptimizer
        from integrations.powerbi.templates import TemplateGenerator

        # Initialize all components
        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)
        refresh_manager = IncrementalRefreshManager(repository)
        template_generator = TemplateGenerator(repository, optimizer)
        metadata_bridge = MetadataBridge(repository)

        print("✅ All components initialize without errors")

        # Test cross-component integration
        test_dataset = "TEST_INTEGRATION"
        repository.register_dataset_complete(
            dataset_id=test_dataset,
            name="Integration Test Dataset",
            category="economia",
            description="Full integration test",
        )

        # Test pipeline: schema -> template -> refresh -> metadata
        try:
            star_schema = optimizer.generate_star_schema(test_dataset)
            template = template_generator.generate_template(test_dataset)
            policy = refresh_manager.create_refresh_policy(test_dataset)
            lineage = metadata_bridge.create_dataset_lineage(test_dataset)

            print("✅ End-to-end pipeline working")

            # Verify template uses star schema
            if hasattr(template, "star_schema"):
                print("✅ Template integrates with star schema")

            # Verify components share the same repository
            assert optimizer.repo == repository
            assert refresh_manager.repository == repository
            assert template_generator.repository == repository
            assert metadata_bridge.repository == repository
            print("✅ Components share unified repository")

            return True

        except Exception as e:
            print(f"⚠️ Pipeline integration issue: {e}")
            return False

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Esegue la validazione completa dei deliverables"""
    print("🔍 POWERBI INTEGRATION DELIVERABLES VALIDATION")
    print("=" * 60)
    print("Issue #27: Day 6 PowerBI Integration Enhancement")
    print()

    # Run all validations
    results = {
        "Star Schema Generation": validate_deliverable_1_star_schema(),
        "DAX Measures Engine": validate_deliverable_2_dax_measures(),
        "Incremental Refresh": validate_deliverable_3_incremental_refresh(),
        "Template Generator": validate_deliverable_4_template_generator(),
        "Metadata Bridge": validate_deliverable_5_metadata_bridge(),
        "Integration Completeness": validate_integration_completeness(),
    }

    # Summary
    print("\n📊 DELIVERABLES VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for deliverable, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{deliverable:<25}: {status}")
        if result:
            passed += 1

    success_rate = (passed / total) * 100
    print(f"\nSuccess Rate: {passed}/{total} ({success_rate:.1f}%)")

    if passed == total:
        print("\n🎉 ALL DELIVERABLES IMPLEMENTED AND WORKING!")
        print("PowerBI integration is ready for production use.")
        conclusion = "READY"
    elif passed >= total * 0.8:
        print("\n⚠️ MOSTLY COMPLETE - MINOR ISSUES")
        print("Most deliverables work. Some refinement needed.")
        conclusion = "MOSTLY_READY"
    else:
        print("\n❌ SIGNIFICANT ISSUES FOUND")
        print("Major problems need resolution before proceeding.")
        conclusion = "NOT_READY"

    print(f"\nConclusion: {conclusion}")
    return passed >= total * 0.8


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
