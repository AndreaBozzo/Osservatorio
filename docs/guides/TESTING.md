# 🧪 Testing Guide

## Overview

Osservatorio has a comprehensive test suite with **401 tests** achieving **67% coverage** across unit, integration, and performance testing.

## Test Structure

```
tests/
├── unit/                   # 287 unit tests
│   ├── test_duckdb_*.py   # DuckDB component tests
│   ├── test_istat_api.py  # API testing
│   └── test_*.py          # Other components
├── integration/           # 90 integration tests
│   ├── test_api_integration.py
│   ├── test_end_to_end_pipeline.py
│   └── test_system_integration.py
└── performance/           # 24 performance tests
    ├── test_duckdb_performance.py
    ├── test_query_builder_performance.py
    └── test_scalability.py
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/performance/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Performance Testing
```bash
# Run performance benchmarks
pytest tests/performance/ -v --benchmark-only

# Performance regression detection
python scripts/performance_regression_detector.py
```

## Test Configuration

### pytest.ini
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
markers = [
    "integration: marks tests as integration tests",
    "performance: marks tests as performance tests",
    "slow: marks tests as slow running",
    "benchmark: marks tests as benchmarks"
]
```

### Test Markers
```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run performance tests only
pytest -m performance
```

## Performance Baselines

### Current Benchmarks
- **Bulk Insert**: >2,000 records/sec
- **Query Execution**: <100ms average
- **Memory Usage**: <1KB per record
- **Cache Hit Rate**: >85%

### Regression Thresholds
- **Minor**: 10% performance degradation
- **Moderate**: 25% performance degradation
- **Severe**: 50% performance degradation

## Writing Tests

### Unit Test Example
```python
import pytest
from src.database.duckdb.manager import DuckDBManager

class TestDuckDBManager:
    def test_connection_creation(self):
        manager = DuckDBManager()
        assert manager.is_connected()

    def test_query_execution(self):
        manager = DuckDBManager()
        result = manager.execute_query("SELECT 1 as test")
        assert result.iloc[0]['test'] == 1
```

### Performance Test Example
```python
import pytest
import time

@pytest.mark.performance
def test_bulk_insert_performance():
    start_time = time.time()
    # ... bulk insert logic
    duration = time.time() - start_time

    # Assert performance threshold
    records_per_second = record_count / duration
    assert records_per_second > 2000, f"Too slow: {records_per_second:.0f} records/sec"
```

## Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Push to main branch
- Scheduled nightly runs

### Quality Gates
- All tests must pass
- Coverage must be >65%
- Performance regressions blocked
- Code formatting enforced

## Coverage Targets

| Component | Current | Target |
|-----------|---------|---------|
| Overall | 67% | 70% |
| DuckDB Module | 85% | 90% |
| API Clients | 60% | 70% |
| Utils | 45% | 60% |

## Troubleshooting

### Common Issues
- **Test timeouts**: Performance tests may timeout on slower systems
- **DuckDB locks**: Ensure proper connection cleanup
- **Memory limits**: Large dataset tests require >4GB RAM

### Solutions
```bash
# Increase timeout for slow tests
pytest --timeout=300

# Run tests with more memory
export DUCKDB_MEMORY_LIMIT=8GB
pytest tests/performance/
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External APIs**: Use fixtures for API calls
3. **Performance Testing**: Set realistic thresholds
4. **Error Testing**: Test error conditions and edge cases
5. **Documentation**: Document complex test scenarios

---

For more testing examples, see existing test files in the `tests/` directory.
