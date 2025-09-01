"""
Unified Data Ingestion & Quality Framework (Issue #63)

This module provides a unified pipeline for orchestrating the complete flow:
ISTAT API → SDMX Parsing → Data Transformation → Quality Assessment → Storage

Key Components:
- UnifiedDataIngestionPipeline: Core pipeline orchestrator
- IngestionJobManager: Batch processing and job management
- PipelineService: High-level service interface
- PipelineConfig: Configurable processing parameters and quality thresholds

Usage:
    from pipeline import PipelineService, PipelineConfig

    config = PipelineConfig()
    service = PipelineService(config)
    result = await service.process_dataset("DCIS_POPRES1")
"""

from .job_manager import IngestionJobManager
from .models import (
    BatchResult,
    PipelineConfig,
    PipelineResult,
    PipelineStatus,
    QualityLevel,
    QualityScore,
)
from .pipeline_service import PipelineService
from .unified_ingestion import UnifiedDataIngestionPipeline

__all__ = [
    "UnifiedDataIngestionPipeline",
    "IngestionJobManager",
    "PipelineService",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStatus",
    "BatchResult",
    "QualityScore",
    "QualityLevel",
]

# Version info for Issue #63 implementation
__version__ = "1.0.0-dev"
__issue__ = "#63"
__description__ = "Unified Data Ingestion & Quality Framework"
