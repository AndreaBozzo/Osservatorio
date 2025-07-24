"""
PowerBI Integration Module for Osservatorio ISTAT Data Platform

This module provides comprehensive PowerBI integration capabilities optimized
for the SQLite + DuckDB hybrid architecture.

Key Features:
- Star schema generation for optimal PowerBI performance
- DAX measures pre-calculation and caching
- Incremental refresh with SQLite metadata tracking
- PowerBI template (.pbit) generation
- Quality score integration
- Metadata-driven export scheduling

Architecture Integration:
- Leverages UnifiedDataRepository for data access
- Extends existing PowerBI API client
- Integrates with SQLite metadata layer
- Optimizes DuckDB analytics queries for PowerBI consumption
"""

from .incremental import IncrementalRefreshManager
from .metadata_bridge import MetadataBridge
from .optimizer import PowerBIOptimizer
from .templates import TemplateGenerator

__all__ = [
    "PowerBIOptimizer",
    "IncrementalRefreshManager",
    "TemplateGenerator",
    "MetadataBridge",
]
