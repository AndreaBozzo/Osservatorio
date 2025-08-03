#!/usr/bin/env python3
"""
Example: Single Dataset Processing
"""
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
    mock_xml = """<?xml version="1.0"?>
    <DataSet>
        <Series>
            <Obs>
                <ObsDimension value="2023"/>
                <ObsValue value="1500000"/>
            </Obs>
        </Series>
    </DataSet>"""

    result = await service.pipeline.ingest_dataset(
        dataset_id="example_dataset",
        sdmx_data=mock_xml,
        target_formats=["powerbi", "tableau"],
    )

    print(f"Dataset: {result.dataset_id}")
    print(f"Status: {result.status.value}")
    print(f"Records: {result.records_processed}")

    if result.quality_score:
        print(f"Quality: {result.quality_score.overall_score:.1f}%")


if __name__ == "__main__":
    asyncio.run(process_single_dataset())
