"""
Scripts package for Osservatorio ISTAT Data Platform.

Issue #84 - Day 3: Script Import Modernization
This package provides proper module structure for all scripts,
eliminating the need for sys.path manipulation patterns.

Usage:
    Run scripts from project root using Python module syntax:

    # OLD (deprecated):
    python scripts/script_name.py

    # NEW (recommended):
    python -m scripts.script_name

Available Scripts:
    - analyze_data_formats: ISTAT data formats analysis
    - benchmark_istat_client: Performance benchmarking
    - cleanup_temp_files: Temporary files cleanup
    - day5_migration_script: Migration utilities
    - generate_api_key: API key generation
    - generate_test_data: Test data generation
    - health_check: System health monitoring
    - organize_data_files: Data file organization
    - performance_regression_detector: Performance regression detection
    - run_performance_tests: Performance test suite
    - schedule_cleanup: Scheduled cleanup tasks
    - setup_powerbi_azure: PowerBI Azure setup
    - test_ci: CI/CD testing utilities
    - test_powerbi_upload: PowerBI upload testing
    - validate_issue6_implementation: Issue #6 validation
    - validate_powerbi_offline: Offline PowerBI validation

Architecture Notes:
    All scripts now use proper package imports without sys.path manipulation.
    This ensures:
    - Better security (no sys.path pollution)
    - Improved maintainability
    - Proper Python packaging standards compliance
    - Easier testing and distribution
"""

import sys
from pathlib import Path


def setup_project_path():
    """
    Setup project path for scripts package.

    This function provides a centralized way to handle path setup
    for the entire scripts package, replacing individual sys.path
    manipulations in each script file.
    """
    project_root = Path(__file__).parent.parent

    # Only add to path if not already present
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    return project_root


# Expose commonly used project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
DATA_ROOT = PROJECT_ROOT / "data"
TESTS_ROOT = PROJECT_ROOT / "tests"

__version__ = "1.0.0"
__author__ = "Osservatorio ISTAT Team"
