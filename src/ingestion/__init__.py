"""
Simple Ingestion Module - Issue #149
Startup-first data ingestion pipeline.
"""

from .simple_pipeline import SimpleIngestionPipeline, create_simple_pipeline

__all__ = ["SimpleIngestionPipeline", "create_simple_pipeline"]
