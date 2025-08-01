# Script Usage Guide - Issue #84 Modernization

## Overview

As part of Issue #84 modernization, all scripts have been updated to use proper Python package imports, eliminating unsafe `sys.path.append()` patterns and improving security and maintainability.

## New Usage Patterns

### ✅ Recommended Usage (Module Execution)

Run scripts as Python modules from the project root:

```bash
# General pattern
python -m scripts.script_name

# Specific examples
python -m scripts.validate_powerbi_offline
python -m scripts.run_performance_tests
python -m scripts.test_ci
python -m scripts.validate_issue6_implementation
```

### ✅ Legacy Support (Still Works)

Traditional script execution is still supported for backward compatibility:

```bash
# Run from project root directory
python scripts/script_name.py

# Examples
python scripts/validate_powerbi_offline.py
python scripts/run_performance_tests.py
```

## Available Scripts

### 🔧 **Validation & Testing**
- `scripts.validate_powerbi_offline` - PowerBI component offline validation
- `scripts.validate_issue6_implementation` - Issue #6 validation
- `scripts.test_ci` - CI/CD testing utilities
- `scripts.run_performance_tests` - Performance test automation

### 📊 **Data Processing**
- `scripts.analyze_data_formats` - ISTAT data format analysis
- `scripts.organize_data_files` - Data file organization
- `scripts.generate_test_data` - Test data generation

### ⚡ **Performance & Monitoring**
- `scripts.benchmark_istat_client` - API client benchmarking
- `scripts.performance_regression_detector` - Performance regression detection
- `scripts.health_check` - System health monitoring

### 🧹 **Maintenance**
- `scripts.cleanup_temp_files` - Temporary file cleanup
- `scripts.schedule_cleanup` - Scheduled cleanup tasks

### 🔑 **Security & APIs**
- `scripts.generate_api_key` - API key generation

### ☁️ **Cloud Integration**
- `scripts.setup_powerbi_azure` - PowerBI Azure setup
- `scripts.test_powerbi_upload` - PowerBI upload testing

### 🔄 **Migration**
- `scripts.day5_migration_script` - Data migration utilities

## Architecture Changes

### Before (Issue #84)
```python
# ❌ Old pattern - REMOVED
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.production_istat_client import ProductionIstatClient
```

### After (Issue #84)
```python
# ✅ New pattern - SECURE
try:
    from . import setup_project_path
    setup_project_path()
except ImportError:
    # Fallback for legacy usage
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.api.production_istat_client import ProductionIstatClient
```

## Benefits of New Approach

### 🔒 **Security Improvements**
- Eliminated unsafe `sys.path` manipulation
- Reduced attack surface for path injection
- Proper Python packaging standards compliance

### 🏗️ **Architecture Benefits**
- Clean module structure with `scripts/__init__.py`
- Centralized path management via `setup_project_path()`
- Consistent import patterns across all scripts

### 🧪 **Testing & Maintenance**
- Easier unit testing of individual scripts
- Better integration with CI/CD pipelines
- Simplified dependency management

### 🚀 **Distribution Ready**
- Scripts can be packaged as proper Python modules
- Support for entry points in `setup.py`
- Compatible with `pip install -e .` development mode

## Troubleshooting

### Module Not Found Errors

If you encounter import errors:

1. **Ensure you're in the project root directory**:
   ```bash
   cd /path/to/Osservatorio
   ```

2. **Use module execution syntax**:
   ```bash
   python -m scripts.script_name
   ```

3. **Check Python path** (for debugging):
   ```python
   import sys
   from pathlib import Path
   print(f"Current directory: {Path.cwd()}")
   print(f"Python path: {sys.path}")
   ```

### Import Warnings

If you see import warnings, they're likely from the fallback compatibility layer and can be safely ignored in most cases.

## Development Guidelines

### Adding New Scripts

1. **Create script in `scripts/` directory**
2. **Use the standard import pattern**:
   ```python
   # Issue #84: Use scripts package path setup
   try:
       from . import setup_project_path
       setup_project_path()
   except ImportError:
       # Fallback for legacy usage
       project_root = Path(__file__).parent.parent
       if str(project_root) not in sys.path:
           sys.path.insert(0, str(project_root))
   ```

3. **Add usage documentation**:
   ```python
   \"\"\"
   Script Description
   
   Usage:
       # Issue #84: Use proper package imports
       python -m scripts.new_script_name
       
       # Legacy support (run from project root):
       python scripts/new_script_name.py
   \"\"\"
   ```

4. **Update `scripts/__init__.py`** to include the new script in documentation

### Testing Scripts

Test both execution methods:

```bash
# Test module execution
python -m scripts.your_script

# Test legacy execution  
python scripts/your_script.py
```

## Migration Notes

All existing scripts have been updated automatically. The changes are:

- ✅ **Backward Compatible**: Old usage patterns still work
- ✅ **Non-Breaking**: No functional changes to script behavior
- ✅ **Secure**: Eliminated unsafe `sys.path` manipulations
- ✅ **Modern**: Follows Python packaging best practices

## See Also

- [Issue #84 Documentation](../project/ISSUE_84_MODERNIZATION.md)
- [Project Structure](../project/PROJECT_STRUCTURE.md)
- [Development Setup](../development/SETUP.md)