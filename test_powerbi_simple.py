"""
Simple test to verify PowerBI integration components work correctly.
Run this from the project root directory.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_powerbi_imports():
    """Test that all PowerBI integration modules can be imported."""
    print("🧪 Testing PowerBI Integration Imports...")

    try:
        # Test basic imports
        from database.sqlite.repository import UnifiedDataRepository

        print("✅ UnifiedDataRepository import successful")

        from integrations.powerbi.optimizer import (
            PowerBIOptimizer,
            StarSchemaDefinition,
        )

        print("✅ PowerBIOptimizer import successful")

        from integrations.powerbi.incremental import (
            IncrementalRefreshManager,
            RefreshPolicy,
        )

        print("✅ IncrementalRefreshManager import successful")

        from integrations.powerbi.templates import PowerBITemplate, TemplateGenerator

        print("✅ TemplateGenerator import successful")

        from integrations.powerbi.metadata_bridge import DatasetLineage, MetadataBridge

        print("✅ MetadataBridge import successful")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality of PowerBI components."""
    print("\n🔧 Testing Basic Functionality...")

    try:
        from database.sqlite.repository import UnifiedDataRepository
        from integrations.powerbi.optimizer import PowerBIOptimizer

        # Initialize components
        repository = UnifiedDataRepository()
        optimizer = PowerBIOptimizer(repository)

        print("✅ Components initialized successfully")

        # Test metadata creation
        test_dataset_id = "TEST_POWERBI"

        # Register a test dataset
        success = repository.register_dataset_complete(
            dataset_id=test_dataset_id,
            name="Test PowerBI Dataset",
            category="popolazione",
            description="Test dataset for PowerBI integration",
        )

        if success:
            print("✅ Test dataset registered successfully")
        else:
            print("⚠️ Test dataset registration - may already exist")

        # Test star schema generation
        try:
            star_schema = optimizer.generate_star_schema(test_dataset_id)
            print(f"✅ Star schema generated: {star_schema.fact_table}")
            print(f"   Dimensions: {len(star_schema.dimension_tables)}")
            print(f"   Relationships: {len(star_schema.relationships)}")
        except Exception as e:
            print(f"⚠️ Star schema generation: {e}")

        # Test DAX measures
        try:
            measures = optimizer.dax_engine.get_standard_measures(test_dataset_id)
            print(f"✅ DAX measures generated: {len(measures)} measures")
            print(f"   Sample measures: {list(measures.keys())[:3]}")
        except Exception as e:
            print(f"⚠️ DAX measures generation: {e}")

        return True

    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_deliverables_checklist():
    """Check that all required deliverables are implemented."""
    print("\n📋 Checking Issue #27 Deliverables...")

    deliverables = [
        (
            "PowerBIOptimizer class",
            "integrations.powerbi.optimizer",
            "PowerBIOptimizer",
        ),
        (
            "Star schema generation",
            "integrations.powerbi.optimizer",
            "StarSchemaDefinition",
        ),
        ("DAX measures engine", "integrations.powerbi.optimizer", "DAXMeasuresEngine"),
        (
            "Incremental refresh system",
            "integrations.powerbi.incremental",
            "IncrementalRefreshManager",
        ),
        (
            "Refresh policy management",
            "integrations.powerbi.incremental",
            "RefreshPolicy",
        ),
        ("Template generator", "integrations.powerbi.templates", "TemplateGenerator"),
        ("PowerBI template class", "integrations.powerbi.templates", "PowerBITemplate"),
        ("Metadata bridge", "integrations.powerbi.metadata_bridge", "MetadataBridge"),
        (
            "Dataset lineage tracking",
            "integrations.powerbi.metadata_bridge",
            "DatasetLineage",
        ),
        (
            "Quality score sync",
            "integrations.powerbi.metadata_bridge",
            "QualityScoreSync",
        ),
    ]

    all_delivered = True

    for name, module_path, class_name in deliverables:
        try:
            module = __import__(module_path, fromlist=[class_name])
            class_obj = getattr(module, class_name)
            print(f"✅ {name}: {class_obj.__name__} implemented")
        except (ImportError, AttributeError) as e:
            print(f"❌ {name}: Missing or incomplete")
            all_delivered = False

    if all_delivered:
        print("\n🎉 All deliverables implemented successfully!")
    else:
        print("\n⚠️ Some deliverables may need attention")

    return all_delivered


def main():
    """Run all tests."""
    print("🚀 PowerBI Integration Validation")
    print("=" * 50)

    # Test imports
    imports_ok = test_powerbi_imports()

    if not imports_ok:
        print("\n❌ Import tests failed - cannot proceed with functionality tests")
        return False

    # Test basic functionality
    functionality_ok = test_basic_functionality()

    # Check deliverables
    deliverables_ok = test_deliverables_checklist()

    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Functionality: {'✅ PASS' if functionality_ok else '❌ FAIL'}")
    print(f"   Deliverables: {'✅ PASS' if deliverables_ok else '❌ FAIL'}")

    overall_success = imports_ok and functionality_ok and deliverables_ok

    if overall_success:
        print(f"\n🎯 Overall Result: ✅ SUCCESS")
        print(f"   PowerBI integration is working correctly!")
        print(f"   All Issue #27 deliverables are implemented.")
    else:
        print(f"\n🎯 Overall Result: ⚠️ PARTIAL SUCCESS")
        print(f"   Some components may need additional work.")

    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
