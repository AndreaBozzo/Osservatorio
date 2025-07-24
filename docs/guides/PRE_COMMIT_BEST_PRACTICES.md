# 🔧 Pre-Commit Best Practices - Day 5 Optimized

## 📋 Overview

Following Day 5 testing optimization, our pre-commit strategy balances **speed for developers** with **quality for production**.

## 🎯 Multi-Layer Strategy

### 1. **Developer Experience** (Pre-Commit)
- **Fast critical tests**: ~5s execution
- **Essential quality checks**: Format, lint, critical functionality
- **Stop on first failure**: Quick feedback

### 2. **Integration Validation** (Pre-Push)
- **Extended test suite**: ~30s execution
- **Integration tests**: Cross-component validation
- **Complete linting**: Full codebase check

### 3. **Production Quality** (CI/CD)
- **Complete test suite**: ~300s execution
- **Full coverage reporting**: Quality metrics
- **Performance benchmarks**: Regression detection

## 🔧 Configuration Files

### `.pre-commit-config.yaml`
```yaml
# Critical path tests (always run)
- id: pytest-critical
  name: pytest-critical-path
  entry: pytest
  args: [-c, pytest-fast.ini,
         tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration,
         tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration,
         --tb=short, -x]

# Full unit tests (manual trigger)
- id: pytest-fast-unit
  name: pytest-fast-unit-tests
  stages: [manual]
  args: [-c, pytest-fast.ini, tests/unit/, -k, "not slow and not performance"]
```

### `pytest-fast.ini`
```ini
# Optimized for development speed
[tool:pytest]
addopts =
    --tb=short
    --disable-warnings
    --no-cov
    -n auto
    -m "not slow and not performance and not benchmark"
```

## 📊 Performance Comparison

| Hook Type | Tests | Time | Use Case |
|-----------|-------|------|----------|
| **Critical** | 2 tests | ~5s | Every commit |
| **Fast Unit** | 50+ tests | ~30s | Manual/Pre-push |
| **Full Suite** | 400+ tests | ~300s | CI/CD only |

## 🚀 Usage Commands

### Standard Workflow
```bash
# Automatic on commit (critical tests)
git commit -m "feature: add new functionality"

# Manual extended testing
pre-commit run pytest-fast-unit --all-files

# Full pre-commit suite
pre-commit run --all-files
```

### Makefile Integration
```bash
# Development workflow
make dev-commit    # Format + critical tests (~5s)
make dev-push      # Format + test + lint (~30s)
make ci           # Full CI/CD simulation (~300s)

# Testing specific
make test-critical    # Critical path only (~5s)
make test-fast       # Fast unit tests (~20s)
make test-full       # Complete with coverage (~300s)
```

### Direct Commands
```bash
# Critical tests (pre-commit style)
pytest -c pytest-fast.ini \
  tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration \
  tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration \
  --tb=short -x

# Fast unit tests
pytest -c pytest-fast.ini tests/unit/ -k "not slow and not performance" --maxfail=3

# Integration sample
pytest tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_user_preferences_with_cache --tb=short
```

## 🎯 Best Practices

### 1. **Gradual Quality Gates**
- ✅ **Pre-commit**: Critical functionality (5s)
- ✅ **Pre-push**: Extended validation (30s)
- ✅ **CI/CD**: Complete quality (300s)

### 2. **Smart Test Selection**
- **Always run**: Core functionality tests
- **Manual trigger**: Extended unit tests
- **CI/CD only**: Performance, slow, benchmark tests

### 3. **Developer Productivity**
- **Fast feedback**: Sub-10s for critical checks
- **Fail fast**: Stop on first failure (`-x`)
- **Parallel execution**: Use all CPU cores (`-n auto`)

### 4. **Configuration Management**
- **Separate configs**: `pytest-fast.ini` vs `pytest.ini`
- **Markers**: `@pytest.mark.slow`, `@pytest.mark.performance`
- **Staged hooks**: Manual vs automatic triggers

## 🔧 Maintenance

### Adding New Tests
```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset_processing():
    # Long-running test
    pass

# Mark performance tests
@pytest.mark.performance
def test_query_performance():
    # Performance benchmark
    pass

# Regular tests run in all configurations
def test_core_functionality():
    # Fast, essential test
    pass
```

### Updating Hooks
```bash
# Update critical path when core changes
# Edit .pre-commit-config.yaml pytest-critical args

# Test hook performance
time pre-commit run pytest-critical --all-files

# Validate configuration
pre-commit validate-config
```

## 📈 Benefits Achieved

### Before Day 5 Optimization
- ❌ **Slow pre-commit**: >180s execution
- ❌ **Developer friction**: Long waiting times
- ❌ **Inconsistent quality**: Developers skipped checks

### After Day 5 Optimization
- ✅ **Fast pre-commit**: <10s execution
- ✅ **Better DX**: Quick feedback loop
- ✅ **Layered quality**: Right checks at right time
- ✅ **90% performance improvement**: From 300s to 30s workflow

## 🎯 Hook Selection Criteria

### Critical Path Tests (Always Run)
```python
# Essential functionality that must never break
tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration
tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration
```

### Extended Tests (Manual/Pre-Push)
```python
# Broader validation but not time-critical
pytest -c pytest-fast.ini tests/unit/ -k "not slow and not performance"
```

### Full Suite (CI/CD Only)
```python
# Complete validation with coverage
pytest --cov=src --cov-report=html tests/
```

## 🚨 Troubleshooting

### Hook Too Slow
```bash
# Profile hook execution
time pre-commit run pytest-critical --all-files

# Check test selection
pytest -c pytest-fast.ini --collect-only tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration
```

### Hook Failing
```bash
# Run hook manually with verbose output
pre-commit run pytest-critical --all-files --verbose

# Debug specific test
pytest tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration -v -s
```

### Configuration Issues
```bash
# Validate pre-commit config
pre-commit validate-config

# Check pytest config
pytest --help config
```

---

## 📋 Summary

The Day 5 optimized pre-commit strategy provides:

1. **⚡ Fast developer feedback**: <10s critical checks
2. **🎯 Layered validation**: Right tests at right time
3. **🚀 90% performance improvement**: Workflow optimization
4. **🔧 Maintainable structure**: Clear separation of concerns

This approach balances developer productivity with code quality, ensuring both fast iteration and robust production code.

---
*Pre-commit best practices following Day 5 testing optimization*
*Achieving 90% performance improvement while maintaining quality*
