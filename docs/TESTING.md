# Testing Guidelines

## 🧪 Testing Overview

This document describes testing guidelines for the Osservatorio ISTAT Data Platform. A focused testing strategy ensures quality, reliability, and maintainability while keeping the test suite manageable for an MVP.

**Note:** This testing strategy was simplified in Issue #159 to focus on MVP essentials. Performance tests were removed as premature optimization for a startup-stage project.

## 📋 Test Strategy (Simplified for MVP)

### Test Pyramid - MVP Focus

```text
        /\
       /  \    Integration Tests (Few - Critical paths only)
      /____\
     /      \
    /________\
   /          \ Unit Tests (Many - Core functionality)
  /__________\
```

### Test Categories

| Test Type | Scope | Speed | Coverage | Status |
|-----------|-------|--------|----------|--------|
| **Unit** | Single function/class | <100ms | 70%+ | ✅ Active |
| **Integration** | Multiple components | <5s | Key flows | ✅ Active |
| **Smoke** | Basic functionality | <10s | Critical paths | ✅ Active |
| **Performance** | System performance | <30s | N/A | ❌ Archived ([#159](https://github.com/AndreaBozzo/Osservatorio/issues/159); revisit after MVP validation or when user base exceeds 1,000 active users) |

**Test Suite Metrics (After Issue #159):**

- Total lines: ~12,890 (reduced from 20,406)
- Collection time: ~14s (reduced from 25s)
- Total tests: ~519 (focused on essentials)

## 🚀 Quick Start

### Setup Test Environment

```bash
# Install test dependencies
pip install -e .
pip install pytest pytest-cov pytest-asyncio httpx

# Run all tests (excluding manual/slow tests)
python -m pytest tests/unit tests/integration -v

# Run with coverage
python -m pytest tests/unit --cov=src --cov-report=html

# Run specific test category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v -m "not slow"

# Run slow/API tests (optional, requires real API access)
python -m pytest -m "slow or api" -v
```

### Test Structure

```text
tests/
├── conftest.py             # Shared fixtures (simplified for MVP)
├── unit/                   # Unit tests (fast, isolated)
│   ├── test_audit_manager.py
│   ├── test_config_manager.py
│   ├── test_dataset_manager.py
│   └── ... (core component tests)
├── integration/            # Integration tests (minimal)
│   ├── test_simple_pipeline_smoke.py  # Smoke tests
│   ├── test_production_istat_client.py
│   └── test_api_integration.py
├── manual/                 # Manual/exploratory tests
│   └── test_production_client_real_api.py
└── test_export_functionality.py
```

**Note:** Performance tests were removed in [Issue #159](https://github.com/AndreaBozzo/Osservatorio/issues/159).

**When to reintroduce performance tests:**

- After successful MVP validation with real users
- User base exceeds 1,000 active users
- Response times become a critical business requirement
- Team has bandwidth for maintaining complex test infrastructure

## ✅ Unit Testing

### Writing Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from src.database.sqlite.repository import DatasetRepository

class TestDatasetRepository:
    """Unit tests for DatasetRepository class."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        return Mock()

    @pytest.fixture
    def repository(self, mock_db):
        """Repository instance with mocked database."""
        return DatasetRepository(mock_db)

    def test_get_dataset_success(self, repository, mock_db):
        """Test successful dataset retrieval."""
        # Arrange
        mock_db.execute.return_value.fetchone.return_value = {
            'id': 1,
            'dataset_id': 'TEST_DATASET',
            'name': 'Test Dataset'
        }

        # Act
        result = repository.get_dataset('TEST_DATASET')

        # Assert
        assert result is not None
        assert result['dataset_id'] == 'TEST_DATASET'
        mock_db.execute.assert_called_once()
```

### Best Practices

- **Test Naming**: Descriptive names che spiegano lo scenario
- **Arrange-Act-Assert**: Struttura chiara dei test
- **Mock Dependencies**: Isola il codice sotto test
- **Edge Cases**: Testa casi limite e condizioni di errore

## 🔗 Integration Testing

### Database Integration Tests

```python
import pytest
from src.database.sqlite.manager import SQLiteMetadataManager

class TestDatabaseIntegration:
    """Integration tests for database layer."""

    @pytest.fixture(scope="class")
    def test_db(self):
        """Test database with real schema."""
        manager = SQLiteMetadataManager(":memory:")
        manager.schema.create_schema()
        yield manager
        manager.close()

    def test_dataset_crud_operations(self, test_db):
        """Test complete CRUD operations for datasets."""
        # Test implementation...
```

### API Integration Tests

```python
from fastapi.testclient import TestClient
from src.api.fastapi_app import app

class TestAPIIntegration:
    """Integration tests for FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_dataset_list_integration(self, client, auth_token):
        """Test dataset listing with real database."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/datasets", headers=headers)
        assert response.status_code == 200
```

## ⚡ Performance Testing

### Performance Test Examples

```python
import time
import pytest

class TestPerformance:
    """Performance tests for critical paths."""

    def test_dataset_list_performance(self, client, auth_headers):
        """Test dataset list endpoint performance."""
        # Target: <100ms for dataset list
        start_time = time.time()

        response = client.get("/datasets", headers=auth_headers)

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time < 100, f"Response took {response_time}ms, target: <100ms"
```

## 📊 Test Coverage

### Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| **Database Layer** | 90%+ | 🟢 92% |
| **API Endpoints** | 85%+ | 🟡 78% |
| **Authentication** | 95%+ | 🟢 96% |
| **Utilities** | 80%+ | 🟢 85% |
| **Overall** | 80%+ | 🟢 83% |

### Coverage Commands

```bash
# Generate coverage report
python -m pytest --cov=src --cov-report=html

# Coverage with missing lines
python -m pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
python -m pytest --cov=src --cov-fail-under=80
```

## 🏃‍♂️ Running Tests

### Local Development

```bash
# Quick test run (unit tests only)
python -m pytest tests/unit/ -v

# Full test suite
python -m pytest

# Specific test file
python -m pytest tests/unit/test_database/test_repository.py -v

# Tests with specific marker
python -m pytest -m "unit" -v
python -m pytest -m "not slow" -v
```

### pytest Configuration

```ini
[tool:pytest]
testpaths = tests
addopts =
    -v
    --tb=short
    --cov=src
    --cov-report=html:htmlcov
    --cov-fail-under=80

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests
    performance: Performance tests
    slow: Tests that take >5 seconds
```

## 🚨 Testing Best Practices

### Do's ✅

- **Write tests first** (TDD approach when possible)
- **Test edge cases** and error conditions
- **Use descriptive test names**
- **Keep tests independent**
- **Mock external dependencies** in unit tests
- **Test business logic** more than implementation details

### Don'ts ❌

- **Don't test framework code**
- **Don't write tests that depend on order**
- **Don't use real external services** in automated tests
- **Don't ignore failing tests**
- **Don't write overly complex tests**

## 🔍 Debugging Tests

### Common Issues

```bash
# Test database issues
pytest tests/integration/ -v -s --pdb

# Import path issues
python -c "import sys; print('\n'.join(sys.path))"

# Show available fixtures
pytest --fixtures
```

---

## 📞 Testing Support

- **Documentation**: `docs/testing/` for detailed guides
- **Questions**: Use GitHub Discussions
- **Issues**: Report via GitHub Issues

**Happy Testing! 🧪✨**
