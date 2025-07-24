"""
PowerBI Integration Package for Osservatorio ISTAT Data Platform

This package provides PowerBI-specific optimizations and integration capabilities
for the unified SQLite + DuckDB architecture.

Components:
- PowerBIOptimizer: Star schema generation and DAX optimization
- IncrementalRefreshManager: SQLite-tracked incremental updates
- TemplateGenerator: PowerBI template (.pbit) generation
- MetadataBridge: PowerBI ↔ SQLite metadata synchronization
"""

from .powerbi.incremental import IncrementalRefreshManager
from .powerbi.optimizer import PowerBIOptimizer
from .powerbi.templates import TemplateGenerator

__all__ = [
    "PowerBIOptimizer",
    "IncrementalRefreshManager",
    "TemplateGenerator",
]
