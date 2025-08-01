# Issue #84 - IstatAPITester REMOVED - Use ProductionIstatClient instead
# 
# This file maintained for backwards compatibility documentation only.
# All functionality has been migrated to:
# - src.api.production_istat_client.ProductionIstatClient (production use)
# - src.api.mock_istat_data (testing/development)
#
# For migration guide, see: docs/migration/ISTAT_API_MIGRATION.md

import warnings


class IstatAPITester:
    """
    Issue #84: IstatAPITester has been REMOVED.
    
    This stub class exists only to provide clear migration guidance.
    Use ProductionIstatClient for production workflows.
    """
    
    def __init__(self):
        raise ImportError(
            "\n" + "=" * 80 + "\n"
            "🚨 IstatAPITester has been REMOVED in Issue #84\n"
            "\n"
            "🔄 MIGRATION REQUIRED:\n"
            "  - Replace with ProductionIstatClient for production workflows\n"
            "  - Use MockIstatData for testing/development\n"
            "  - See docs/migration/ISTAT_API_MIGRATION.md\n"
            "\n"
            "Example migration:\n"
            "  OLD: from src.api.istat_api import IstatAPITester\n"
            "  NEW: from src.api.production_istat_client import ProductionIstatClient\n"
            "\n"
            + "=" * 80 + "\n"
        )


# For any remaining imports, provide clear error
def __getattr__(name):
    if name == 'IstatAPITester':
        raise ImportError(
            f"IstatAPITester has been removed. Use ProductionIstatClient instead."
        )
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")