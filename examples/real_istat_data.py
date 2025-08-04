#!/usr/bin/env python3
"""
Example: Using Real ISTAT XML Files
"""

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
    with open(xml_file, encoding="utf-8") as f:
        xml_content = f.read()

    # Process through pipeline
    service = PipelineService()
    await service.start_background_processing()

    result = await service.pipeline.ingest_dataset(
        dataset_id=xml_file.stem, sdmx_data=xml_content, target_formats=["powerbi"]
    )

    print("✅ Processing complete:")
    print(f"   Status: {result.status.value}")
    print(f"   Records: {result.records_processed}")
    print(f"   Duration: {result.duration_seconds:.3f}s")

    # Check outputs
    output_dir = Path("data/processed/powerbi")
    output_files = list(output_dir.glob(f"*{xml_file.stem}*"))
    print(f"   Output files: {len(output_files)}")


if __name__ == "__main__":
    asyncio.run(process_real_istat_file())
