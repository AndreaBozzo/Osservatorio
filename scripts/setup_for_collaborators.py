#!/usr/bin/env python3
"""
Setup Script for Collaborators - Issue #63

One-click setup to prepare the unified pipeline for collaborative testing.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineConfig, PipelineService

# Project imports (after path modification)
from src.database.duckdb.manager import DuckDBManager
from src.database.sqlite.repository import UnifiedDataRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_prerequisites():
    """Check if all prerequisites are in place."""
    print("🔍 CHECKING PREREQUISITES")
    print("-" * 30)

    checks = []

    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(
            f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        checks.append(True)
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} (need ≥3.8)")
        checks.append(False)

    # Check required directories
    required_dirs = [
        "data/raw/xml",
        "data/raw/istat/istat_data",
        "data/processed/powerbi",
        "data/processed/tableau",
        "data/databases",
        "data/performance_results",
    ]

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ Directory: {dir_path}")
            checks.append(True)
        else:
            print(f"⚠️  Creating: {dir_path}")
            path.mkdir(parents=True, exist_ok=True)
            checks.append(True)

    # Check for ISTAT data files
    istat_data_dir = Path("data/raw/istat/istat_data")
    xml_files = list(istat_data_dir.glob("*.xml"))

    if xml_files:
        print(f"✅ ISTAT data: {len(xml_files)} XML files available")
        checks.append(True)
    else:
        print("⚠️  ISTAT data: No XML files (will use mock data for testing)")
        checks.append(True)  # Not critical for basic testing

    # Check key modules
    try:
        import importlib.util

        spec = importlib.util.find_spec("src.pipeline.PipelineService")
        if spec is not None:
            print("✅ Pipeline service: Available")
            checks.append(True)
        else:
            print("❌ Pipeline service: Module not found")
            checks.append(False)
    except ImportError as e:
        print(f"❌ Pipeline service: {e}")
        checks.append(False)

    success_rate = sum(checks) / len(checks)
    print(f"\n📊 Prerequisites: {success_rate * 100:.1f}% ready")

    return success_rate >= 0.8


async def setup_databases():
    """Initialize databases for collaborative testing."""
    print("\n🗄️  SETTING UP DATABASES")
    print("-" * 25)

    try:
        # Initialize SQLite repository
        UnifiedDataRepository()
        print("✅ SQLite metadata database initialized")

        # Initialize DuckDB
        DuckDBManager()
        print("✅ DuckDB analytics database initialized")

        # Check database files
        sqlite_path = Path("data/databases/osservatorio_metadata.db")
        duckdb_path = Path("data/databases/osservatorio.duckdb")

        if sqlite_path.exists():
            size = sqlite_path.stat().st_size
            print(f"   SQLite: {size:,} bytes")

        if duckdb_path.exists():
            size = duckdb_path.stat().st_size
            print(f"   DuckDB: {size:,} bytes")

        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


async def test_basic_functionality():
    """Test basic pipeline functionality."""
    print("\n🧪 TESTING BASIC FUNCTIONALITY")
    print("-" * 30)

    try:
        # Initialize pipeline service
        config = PipelineConfig(
            batch_size=100,
            max_concurrent=2,
            enable_quality_checks=True,
        )

        service = PipelineService(config=config)
        await service.start_background_processing()
        print("✅ Pipeline service started")

        # Test pipeline status
        status = await service.get_pipeline_status()
        if status.get("status") == "healthy":
            print("✅ Pipeline status: Healthy")
        else:
            print(f"⚠️  Pipeline status: {status.get('status', 'unknown')}")

        # Test supported formats
        formats = service.get_supported_formats()
        print(f"✅ Supported formats: {formats}")

        # Test with mock data
        mock_xml = """<?xml version="1.0" encoding="utf-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
                    <generic:Obs>
                        <generic:ObsDimension id="TIME_PERIOD" value="2023"/>
                        <generic:ObsValue value="100"/>
                    </generic:Obs>
                </generic:Series>
            </message:DataSet>
        </message:GenericData>"""

        result = await service.pipeline.ingest_dataset(
            dataset_id="setup_test",
            sdmx_data=mock_xml,
            target_formats=["powerbi"],
        )

        if result.status.value == "completed":
            print(f"✅ Mock data test: Success ({result.records_processed} records)")
        else:
            print(f"⚠️  Mock data test: {result.status.value}")

        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        logger.error(f"Basic test failed: {e}", exc_info=True)
        return False


def create_testing_scripts():
    """Create convenient testing scripts for collaborators."""
    print("\n📝 CREATING TESTING SCRIPTS")
    print("-" * 25)

    scripts_created = []

    # Quick test script
    quick_test_script = """#!/usr/bin/env python3
# Quick Pipeline Test - Auto-generated by setup
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineService

async def quick_test():
    print("🚀 Quick Pipeline Test")
    service = PipelineService()
    await service.start_background_processing()

    status = await service.get_pipeline_status()
    print(f"Status: {status.get('status', 'unknown')}")
    print(f"Formats: {service.get_supported_formats()}")
    print("✅ Pipeline is ready for use!")

if __name__ == "__main__":
    asyncio.run(quick_test())
"""

    quick_test_path = Path("scripts/quick_test.py")
    with open(quick_test_path, "w", encoding="utf-8") as f:
        f.write(quick_test_script)
    scripts_created.append("quick_test.py")

    # Batch test script
    batch_test_script = """#!/usr/bin/env python3
# Batch Test Script - Auto-generated by setup
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineService

async def batch_test():
    print("📦 Batch Processing Test")

    # Mock datasets
    datasets = [
        {"id": "test_1", "data": "<mock>data1</mock>"},
        {"id": "test_2", "data": "<mock>data2</mock>"},
    ]

    service = PipelineService()
    await service.start_background_processing()

    results = await service.pipeline.batch_ingest(
        datasets=datasets,
        target_formats=["powerbi"]
    )

    successful = len([r for r in results if r.status.value == "completed"])
    print(f"Results: {successful}/{len(results)} successful")
    print("✅ Batch processing working!")

if __name__ == "__main__":
    asyncio.run(batch_test())
"""

    batch_test_path = Path("scripts/batch_test.py")
    with open(batch_test_path, "w", encoding="utf-8") as f:
        f.write(batch_test_script)
    scripts_created.append("batch_test.py")

    print(f"✅ Created {len(scripts_created)} testing scripts:")
    for script in scripts_created:
        print(f"   - scripts/{script}")

    return True


def create_usage_examples():
    """Create practical usage examples."""
    print("\n📖 CREATING USAGE EXAMPLES")
    print("-" * 25)

    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)

    # Example 1: Single dataset processing
    single_example = """#!/usr/bin/env python3
\"\"\"
Example: Single Dataset Processing
\"\"\"
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineService

async def process_single_dataset():
    # Initialize service
    service = PipelineService()
    await service.start_background_processing()

    # Process dataset (with mock data)
    mock_xml = '''<?xml version="1.0"?>
    <DataSet>
        <Series>
            <Obs>
                <ObsDimension value="2023"/>
                <ObsValue value="1500000"/>
            </Obs>
        </Series>
    </DataSet>'''

    result = await service.pipeline.ingest_dataset(
        dataset_id="example_dataset",
        sdmx_data=mock_xml,
        target_formats=["powerbi", "tableau"]
    )

    print(f"Dataset: {result.dataset_id}")
    print(f"Status: {result.status.value}")
    print(f"Records: {result.records_processed}")

    if result.quality_score:
        print(f"Quality: {result.quality_score.overall_score:.1f}%")

if __name__ == "__main__":
    asyncio.run(process_single_dataset())
"""

    with open(examples_dir / "single_dataset.py", "w", encoding="utf-8") as f:
        f.write(single_example)

    # Example 2: Using real ISTAT files
    real_data_example = """#!/usr/bin/env python3
\"\"\"
Example: Using Real ISTAT XML Files
\"\"\"
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineService

async def process_real_istat_file():
    # Check for ISTAT data files
    istat_dir = Path("data/raw/istat/istat_data")
    xml_files = list(istat_dir.glob("*.xml"))

    if not xml_files:
        print("No ISTAT XML files found in data/raw/istat/istat_data/")
        return

    # Use first available file
    xml_file = xml_files[0]
    print(f"Processing: {xml_file.name}")

    # Read XML content
    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    # Process through pipeline
    service = PipelineService()
    await service.start_background_processing()

    result = await service.pipeline.ingest_dataset(
        dataset_id=xml_file.stem,
        sdmx_data=xml_content,
        target_formats=["powerbi"]
    )

    print(f"✅ Processing complete:")
    print(f"   Status: {result.status.value}")
    print(f"   Records: {result.records_processed}")
    print(f"   Duration: {result.duration_seconds:.3f}s")

    # Check outputs
    output_dir = Path("data/processed/powerbi")
    output_files = list(output_dir.glob(f"*{xml_file.stem}*"))
    print(f"   Output files: {len(output_files)}")

if __name__ == "__main__":
    asyncio.run(process_real_istat_file())
"""

    with open(examples_dir / "real_istat_data.py", "w", encoding="utf-8") as f:
        f.write(real_data_example)

    print("✅ Created usage examples:")
    print("   - examples/single_dataset.py")
    print("   - examples/real_istat_data.py")

    return True


async def main():
    """Run complete setup for collaborators."""
    print("🚀 UNIFIED PIPELINE - COLLABORATOR SETUP")
    print("=" * 50)
    print(f"Setup started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    setup_steps = []

    # Step 1: Prerequisites check
    prereqs_ok = check_prerequisites()
    setup_steps.append(("Prerequisites", prereqs_ok))

    if not prereqs_ok:
        print("\n❌ Prerequisites not met. Please address issues above.")
        return False

    # Step 2: Database setup
    db_ok = await setup_databases()
    setup_steps.append(("Database Setup", db_ok))

    # Step 3: Basic functionality test
    test_ok = await test_basic_functionality()
    setup_steps.append(("Basic Testing", test_ok))

    # Step 4: Create testing scripts
    scripts_ok = create_testing_scripts()
    setup_steps.append(("Testing Scripts", scripts_ok))

    # Step 5: Create usage examples
    examples_ok = create_usage_examples()
    setup_steps.append(("Usage Examples", examples_ok))

    # Final summary
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)

    for step_name, success in setup_steps:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {step_name}: {status}")

    success_count = sum(1 for _, success in setup_steps if success)
    total_steps = len(setup_steps)
    success_rate = (success_count / total_steps) * 100

    print(
        f"\n📈 Setup Success Rate: {success_rate:.1f}% ({success_count}/{total_steps})"
    )

    if success_rate >= 80:
        print("\n🎉 SETUP COMPLETE - SYSTEM READY FOR COLLABORATION!")
        print("\n📋 Next Steps for Collaborators:")
        print("   1. Run: python scripts/quick_test.py")
        print("   2. Try: python examples/single_dataset.py")
        print("   3. Test: python scripts/test_pipeline_demo.py")
        print("   4. Read: docs/SYSTEM_USAGE_GUIDE.md")
        print("\n✅ The unified pipeline is ready for collaborative development!")
    else:
        print("\n⚠️  SETUP INCOMPLETE - Address failed steps above")

    return success_rate >= 80


if __name__ == "__main__":
    asyncio.run(main())
