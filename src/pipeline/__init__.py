"""
Unified Data Ingestion & Quality Framework (Issue #63)

This module provides a unified pipeline for orchestrating the complete flow:
ISTAT API → SDMX Parsing → Data Transformation → Quality Assessment → Storage

Key Components:
- PipelineController: Main orchestrator for end-to-end processing
- EnhancedSDMXParser: Complete ISTAT SDMX XML structure parsing  
- DataQualityValidator: Comprehensive data quality assessment
- PipelineConfig: Configurable processing parameters and quality thresholds

Usage:
    from src.pipeline import UnifiedPipelineController, PipelineConfig
    
    config = PipelineConfig()
    controller = UnifiedPipelineController(config)
    result = await controller.process_dataset("DCIS_POPRES1")
"""

from .models import PipelineConfig, PipelineResult, PipelineStatus, QualityScore

__all__ = [
    "PipelineConfig",
    "PipelineResult", 
    "PipelineStatus",
    "QualityScore",
]

# Version info for Issue #63 implementation
__version__ = "1.0.0-dev"
__issue__ = "#63"
__description__ = "Unified Data Ingestion & Quality Framework"