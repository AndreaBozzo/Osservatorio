# CLAUDE.md - Developer Context & Commands

This file provides essential guidance to Claude Code when working with this repository.
***DO NOT MODIFY BELOW***
A few rules for Claude:
1-Use tokens efficiently
2-Refer to PROJECT_STATE.md to track progresses.
3-Best practices, always.
4-As this is an early-stage startup, YOU MUST prioritize simple, readable code with minimal abstraction—avoid premature optimization. 5-Strive for elegant, minimal solutions that reduce complexity.Focus on clear implementation that’s easy to understand and iterate on as the product evolves.
6-DO NOT use preserve backward compatibility unless the user specifically requests it
7-The user expect maximum realism and can accept criticism
8-NO SED COMMANDS.
***DO NOT MODIFY ABOVE***

## Project Overview

Osservatorio is an Italian statistical data processing and visualization
platform. It processes public open datas into insightful resources, while unifying the sources.

**Status**: MVP v0.5 Development Phase - Post-Cleanup (Aug 2025)
**Architecture**: FastAPI + JWT Auth + DuckDB/SQLite + Docker Compose (simplified)
**Functional**: API server, database layer, authentication, core data processing
**Current Focus**: MVP delivery, removed K8s complexity and BI over-engineering
**Documentation**: [README.md](../../README.md) and [docs/](../)

## Essential Commands

### Modern Development Commands
- `make help` - Show all available commands
- `make install` - Install with modern dependency management
- `make test-fast` - Fast unit tests
- `make quality` - Run all quality checks (lint, format, security)
- `docker-compose up -d` - Start development environment

### Testing & Validation
- `pytest tests/unit/` - Unit tests
- `pytest tests/integration/` - Integration tests
- `pytest tests/performance/` - Performance benchmarks
- `make security-check` - Security scanning with Bandit

### FastAPI Development
- `uvicorn src.api.fastapi_app:app --reload` - Start FastAPI server
- `curl http://localhost:8000/health` - Health check
- `curl http://localhost:8000/docs` - OpenAPI documentation
- `pytest tests/unit/test_fastapi_integration.py -v` - API tests

### Infrastructure Status (August 2025 - Post MVP Cleanup)
- ✅ Multi-stage Docker builds ready (tested: app loads)
- ✅ Security middleware and authentication system (JWT + rate limiting functional)
- ✅ Docker Compose deployment strategy (dev/staging/prod)
- ✅ Removed K8s over-engineering for MVP focus (Issue #152)
- ✅ Removed PowerBI/Tableau complexity (Issue #151)
- ⚠️ CI/CD pipeline basic (unit tests only)

### Makefile Commands (Recommended)
- `make help` - Show all commands
- `make status` - Project status
- `make test-fast` - Fast tests (~20s)
- `make test` - Development workflow (~30s)
- `make powerbi-validate` - PowerBI validation
- `make format` - Code formatting
- `make lint` - Code linting
- `make clean` - Clean temp files
- `make dashboard` - Run Streamlit dashboard

### Data Ingestion
- `python scripts/download_istat_data.ps1`
Primordial ingestion layer with a shell script, needs to be
revamped/rehauled for unified pipeline, orchestration
and automation, work in progress.

### Data Processing
- `python -c "from src.services.dataflow_analysis_service import DataflowAnalysisService; print('Service ready')"` - Dataflow service
- `python -m scripts.organize_data_files` - Organize data files (Issue #84: modernized)
- `python -m scripts.cleanup_temp_files` - Clean temporary files (Issue #84: modernized)

### PowerBI Integration (NEEDS REWORK)
- `python -m examples.powerbi_integration_demo` - PowerBI demo (structure present)
- `python -m scripts.validate_powerbi_offline` - Offline validation (templates don't work)
- `pytest tests/unit/test_powerbi_api.py -v` - PowerBI tests (API structure only)
- **⚠️ STATUS**: Templates fail in PowerBI Desktop, integration needs complete rework

### CI/CD & Dashboard
- `python -m scripts.test_ci --strategy auto` - CI tests with fallback (Issue #84: modernized)
- `streamlit run dashboard/app.py` - Run dashboard locally
- **Live Dashboard**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)

### Utilities (Issue #84: All scripts modernized)
- `python -m scripts.cleanup_temp_files` - Clean temp files
- `python -m scripts.organize_data_files` - Organize data files
- `python -m scripts.health_check` - System health check
- `python -m scripts.generate_test_data` - Generate test data
- `python -m scripts.run_performance_tests` - Performance testing
- `python -m scripts.validate_issue6_implementation` - Issue #6 validation

**📖 See [Script Usage Guide](../scripts/SCRIPT_USAGE_GUIDE.md) for complete documentation**

### Development Environment
- **Python Version**: 3.13.3 (verified 20/07/2025)
- **Testing Framework**: pytest 8.3.5 (verified 20/07/2025)
- `python -m venv venv` - Create virtual environment
- `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac) - Activate virtual environment
- `pip install -r requirements.txt` - Install dependencies
- `pip install -r requirements-dev.txt` - Install development dependencies

### SQLite + DuckDB Hybrid Commands (UPDATED 28/07/2025 - Issues #59 & #62 Complete)
#### DuckDB Analytics (Production Ready)
- `python examples/duckdb_demo.py` - Complete DuckDB demonstration with real ISTAT data
- `python -c "from src.database.duckdb import SimpleDuckDBAdapter; adapter = SimpleDuckDBAdapter(); adapter.create_istat_schema(); print('Schema created')"` - Quick schema setup
- `python -c "from src.database.duckdb import DuckDBManager; manager = DuckDBManager(); print(manager.get_performance_stats())"` - Get performance statistics
- `pytest tests/unit/test_duckdb_basic.py -v` - Run basic DuckDB tests (focused on core functionality)
- `pytest tests/unit/test_duckdb_integration.py -v` - Run comprehensive DuckDB integration tests (45 tests)
- `pytest tests/unit/test_simple_adapter.py -v` - Run simple adapter tests (lightweight usage patterns)

#### SQLite Metadata Management (UPDATED 28/07/2025 - Issue #59 Complete)
- `python examples/sqlite_metadata_demo.py` - SQLite metadata layer demonstration (IMPLEMENTED)
- `python -c "from src.database.sqlite import SQLiteMetadataManager; manager = SQLiteMetadataManager(); print('SQLite schema ready')"` - Initialize SQLite metadata schema
- `pytest tests/unit/test_sqlite_metadata.py -v` - Run SQLite metadata tests (22 tests, 100% pass rate)
- `python -c "from src.database.sqlite import get_metadata_manager; manager = get_metadata_manager(); print(manager.get_database_stats())"` - Get SQLite database statistics
- **NEW! JSON to SQLite Migration (Issue #59)**:
  - `python scripts/migrate_json_to_sqlite.py` - Migrate JSON dataset configs to SQLite with backup and validation
  - `python -c "from src.database.sqlite.dataset_config import get_dataset_config_manager; manager = get_dataset_config_manager(); print(f'Datasets: {manager.get_datasets_config()[\"total_datasets\"]}')"` - Test dataset config manager
  - `pytest tests/unit/test_json_sqlite_migration.py -v` - Run JSON migration tests (19 tests, comprehensive coverage)

#### BaseConverter Architecture (NEW 28/07/2025 - Issue #62 Complete)
- **NEW! Unified Converter Foundation (Issue #62)**:
  - `pytest tests/unit/test_base_converter.py -v` - Run BaseConverter architecture tests (18 tests)
  - `python -c "from src.converters.factory import create_powerbi_converter, create_tableau_converter; print('Factory pattern ready')"` - Test converter factory
  - **Code Reduction**: ~500 lines eliminated (~23% reduction in converter modules)
  - **Architecture**: Abstract BaseIstatConverter with PowerBI/Tableau specializations
  - **Factory Pattern**: Centralized converter creation with `ConverterFactory.create_converter(target)`

#### Unified Data Repository (Day 4 COMPLETED)
- `python -c "from src.database.sqlite.repository import UnifiedDataRepository; repo = UnifiedDataRepository(); print('Unified repo ready')"` - Test unified data access
- `pytest tests/integration/test_unified_repository.py -v` - Run unified repository integration tests (18 tests, 100% pass rate)
- `python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print(repo.get_system_status())"` - Get hybrid system status

### DuckDB Performance Testing Commands (NEW 21/07/2025)
> **NOTE**: GitHub Actions performance workflow (Issue #74) was removed due to unsatisfactory implementation. Local performance tests remain available.

- `pytest tests/performance/test_duckdb_performance.py -v` - Run comprehensive performance test suite (7 categories)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_bulk_insert_performance -v` - Test bulk insert performance (1k-100k records)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_query_optimization_performance -v` - Test query optimizer with cache analysis
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_concurrent_query_performance -v` - Test concurrent execution (1-8 threads)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_large_dataset_performance -v` - Test large dataset handling (100k+ records)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_indexing_performance_impact -v` - Test indexing strategies impact
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_memory_usage_patterns -v` - Test memory usage patterns and scaling

### Performance Regression Detection Commands (NEW 21/07/2025)
> **NOTE**: GitHub Actions workflow removed (Issue #74). Local regression detection scripts remain functional.

- `python scripts/performance_regression_detector.py` - Run complete performance regression analysis
- `python -c "from scripts.performance_regression_detector import PerformanceRegressionDetector; detector = PerformanceRegressionDetector(); print('Detector ready')"` - Initialize regression detector
- `python -c "from scripts.performance_regression_detector import PerformanceRegressionDetector; detector = PerformanceRegressionDetector(); metrics = detector.run_performance_tests(); print(f'Collected {len(metrics)} metrics')"` - Run performance tests only
- Performance reports saved to: `data/performance_results/performance_report_YYYYMMDD_HHMMSS.md`
- Performance baselines stored in: `data/performance_baselines.json`

### Security & Monitoring Commands (UPDATED 22/07/2025 - SQLite Era)
#### General Security
- `python -c "from src.utils.security_enhanced import security_manager; print(security_manager.get_security_headers())"` - Get security headers
- `python -c "from src.utils.circuit_breaker import get_circuit_breaker_stats; print(get_circuit_breaker_stats())"` - Get circuit breaker stats
- `python -c "from src.utils.security_enhanced import security_manager; security_manager.cleanup_old_entries()"` - Clean up rate limiter entries

#### Database Security Scans
- `bandit -r src/database/duckdb/` - Security scan for DuckDB modules (enterprise-grade)
- `bandit -r src/database/sqlite/` - Security scan for SQLite metadata layer (Day 4 complete)
- `bandit -r src/utils/security_enhanced.py` - Security scan for enhanced security manager
- `bandit -r src/` - Full codebase security scan (currently 2 non-critical issues)

#### SQLite Security Validation (Day 4 COMPLETED)
- `python -c "from src.database.sqlite import SQLiteMetadataManager; manager = SQLiteMetadataManager(); print('✅ SQLite security validated')"` - Verify SQLite security features
- `python -c "from src.utils.security_enhanced import SecurityManager; sm = SecurityManager(); print(sm.encrypt_data('test'))"` - Test encryption functionality

### DuckDB Security Audit Commands (UPDATED 22/07/2025 - Day 3 Security Complete)
- `mypy src/database/duckdb/ --ignore-missing-imports` - Run MyPy type safety check (note: may timeout on large codebases)
- `bandit -r src/database/duckdb/ -f json` - Comprehensive security scan with JSON output
- `bandit -r src/database/duckdb/ --severity-level high` - Check for HIGH severity issues only
- `pytest tests/unit/test_duckdb_integration.py -v` - Run all 45 security-enhanced DuckDB tests
- `python -c "from src.database.duckdb.manager import DuckDBManager; m = DuckDBManager(); print('✅ SQL injection protection active')"` - Verify security features
- **Security Status**: ✅ 0 HIGH severity issues, all MEDIUM warnings are false positives, enterprise-grade SQL injection protection

### Testing Status (August 2025)
- `pytest` - Run all tests (core functionality tested)
- `pytest --cov=src tests/` - Run tests with coverage
- `pytest tests/unit/` - Unit tests (database, auth, core APIs)
- `pytest tests/integration/` - Integration tests (repository, client)
- **Note**: Test numbers/coverage in old docs were inflated - focus on functionality verification
- `pytest tests/unit/test_tableau_api.py -v` - Run specific tableau API tests (20 tests)
- `pytest tests/unit/test_temp_file_manager.py -v` - Run temp file manager tests (26 tests)
- `pytest tests/unit/test_istat_api.py -v` - Run expanded ISTAT API tests (25 tests)
- `pytest tests/unit/test_sqlite_metadata.py -v` - Run SQLite metadata tests (22 tests, Day 4 complete)
- `pytest tests/integration/test_unified_repository.py -v` - Run unified repository tests (18 tests, Day 4 complete)
- `pytest --cov=src --cov-report=term tests/unit/ --tb=no -q` - Quick coverage check for unit tests

### Performance Testing Specific (UPDATED 22/07/2025 - All Tests Passing)
- `pytest tests/performance/test_scalability.py -v` - Run original scalability tests (8 tests)
- `pytest tests/performance/test_duckdb_performance.py -v` - Run comprehensive DuckDB performance tests (6 test methods)
- `pytest tests/performance/test_query_builder_performance.py -v` - Run query builder performance tests (10 test methods)
- `pytest tests/performance/ --tb=short` - Run all 24 performance tests (all passing)
- `pytest tests/performance/test_duckdb_performance.py -k "bulk_insert" -v` - Run only bulk insert performance tests
- `pytest tests/performance/test_duckdb_performance.py -k "concurrent" -v` - Run only concurrent query tests
- `pytest tests/performance/test_duckdb_performance.py -k "memory" -v` - Run only memory usage pattern tests
- `pytest tests/performance/ -m benchmark` - Run benchmark-specific performance tests

### MVP Deployment Strategy (August 2025 - Simplified)
#### Docker Compose Commands (TESTED)
- `docker-compose up -d` - Start complete development environment
- `docker-compose -f docker-compose.yml up` - Production deployment
- `docker-compose logs -f osservatorio-api` - Check application logs
- `docker-compose down` - Stop all services
- **✅ VERIFIED**: All Docker Compose commands tested and functional

#### MVP Architecture Components
- Multi-environment support (dev/staging/prod namespaces)
- Persistent storage with performance tiers (SSD/standard/backup)
- Network policies for security isolation
- Automated backup CronJobs (scripts need testing)
- Health check integrations (endpoints exist, monitoring untested)

### Code Quality
- `black .` - Format code with Black
- `flake8 .` - Lint code with Flake8
- `isort .` - Sort imports with isort
- `pre-commit run --all-files` - Run pre-commit hooks

### Security Features
- **Path Validation**: Directory traversal protection, secure file operations
- **Input Sanitization**: XSS/injection prevention, safe XML parsing
- **Rate Limiting**: API protection with sliding window algorithm
- **JWT Authentication**: Secure API keys with bcrypt hashing

## Project Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                 🚀 ProductionIstatClient                       │
│    Circuit Breaker • Connection Pool • Rate Limiter            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              🔄 Unified Repository (Facade Pattern)            │
│  📊 DuckDB Analytics • 🗃️ SQLite Metadata • 💾 Cache Fallback  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 ISTAT SDMX API                          │
│            509+ datasets with intelligent fallback            │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

1. **ProductionIstatClient** (`src/api/production_istat_client.py`):
   - Enterprise-ready ISTAT client with circuit breaker, connection pooling, rate limiting
   - Cache fallback system for offline capability (<100ms response)

2. **Authentication System** (`src/auth/`):
   - JWT tokens with bcrypt hashing (`sqlite_auth.py`, `jwt_manager.py`)
   - Rate limiting and security middleware (`rate_limiter.py`, `security_middleware.py`)

3. **Database Architecture** (`src/database/`):
   - **DuckDB**: Analytics engine (`duckdb/manager.py`, `query_builder.py`)
   - **SQLite**: Metadata and configuration (`sqlite/repository.py`, `dataset_config.py`)
   - **Unified Repository**: Facade pattern combining both databases

4. **Data Processing** (`src/converters/`, `src/services/`):
   - **BaseConverter Architecture**: Unified foundation (`base_converter.py`, `factory.py`)
   - **PowerBI Integration**: Converter, optimizer, templates (`powerbi_converter.py`, `integrations/powerbi/`)
   - **Tableau Integration**: Converter and API client (`tableau_converter.py`, `api/tableau_api.py`)
   - **Dataflow Analysis**: Modern service with REST endpoints (`services/dataflow_analysis_service.py`)

5. **Utilities & Configuration** (`src/utils/`):
   - **Security**: Path validation, temp file management (`secure_path.py`, `temp_file_manager.py`)
   - **Configuration**: Centralized config and logging (`config.py`, `logger.py`)
   - **Resilience**: Circuit breaker patterns (`circuit_breaker.py`, `security_enhanced.py`)

### Data Flow
1. **ISTAT SDMX API** → **ProductionIstatClient** (with circuit breaker & cache fallback)
2. **XML Processing** → **BaseConverter** → **PowerBI/Tableau formats**
3. **Storage** → **DuckDB** (analytics) + **SQLite** (metadata) via **Unified Repository**
4. **Authentication** → **JWT tokens** + **Rate limiting** + **Security middleware**

### Directory Structure (Current)
```
src/
├── analyzers/          # Data analysis (minimal)
├── api/               # API clients & endpoints
│   ├── production_istat_client.py    # Main ISTAT client
│   ├── powerbi_api.py                # PowerBI integration
│   ├── tableau_api.py                # Tableau integration
│   ├── dataflow_analysis_api.py      # Analysis endpoints
│   └── fastapi_app.py                # FastAPI application
├── auth/              # JWT Authentication System
│   ├── sqlite_auth.py    # API key management
│   ├── jwt_manager.py    # JWT tokens
│   ├── rate_limiter.py   # Rate limiting
│   └── security_middleware.py # Security headers
├── converters/        # Data format converters
│   ├── base_converter.py      # Unified foundation
│   ├── powerbi_converter.py   # PowerBI formats
│   ├── tableau_converter.py   # Tableau formats
│   └── factory.py             # Factory pattern
├── database/          # Hybrid database architecture
│   ├── duckdb/        # Analytics engine
│   │   ├── manager.py          # Connection management
│   │   ├── query_builder.py    # Query interface
│   │   └── simple_adapter.py   # Lightweight interface
│   └── sqlite/        # Metadata & configuration
│       ├── repository.py       # Unified repository
│       ├── dataset_config.py   # Configuration manager
│       └── manager.py          # SQLite management
├── integrations/      # External service integrations
│   └── powerbi/       # PowerBI enterprise features
├── services/          # Business logic services
│   └── dataflow_analysis_service.py
└── utils/             # Core utilities
    ├── config.py           # Configuration
    ├── logger.py           # Logging
    ├── secure_path.py      # Path validation
    ├── circuit_breaker.py  # Resilience patterns
    └── temp_file_manager.py # File management
```

## Key Features

### Data Categories (ISTAT SDGs)
1. **Popolazione** (Population) - Priority 10
2. **Economia** (Economy) - Priority 9
3. **Lavoro** (Employment) - Priority 8
4. **Territorio** (Territory) - Priority 7
5. **Istruzione** (Education) - Priority 6
6. **Salute** (Health) - Priority 5
7. **Altro** (Other) - Priority 1

### Output Formats
- **PowerBI**: CSV, Excel, Parquet, JSON
- **Tableau**: CSV, Excel, JSON
- **Quality Assessment**: Completeness scoring, data validation

### Testing Infrastructure
- **540+ Tests**: 100% passing rate
- **Coverage**: Unit, integration, performance tests
- **Quality Score**: 83.3% EXCELLENT rating

## Integration Points
- **ISTAT SDMX API**: `http://sdmx.istat.it/SDMXWS/rest/` (509+ datasets)
- **PowerBI Service**: REST API with MSAL authentication
- **Tableau Server**: OAuth connections
- **Live Dashboard**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)

## Important Characteristics
- All data from official ISTAT SDMX endpoints
- Italian regional data with geographic mapping
- Rate limiting: 100 requests/hour with sliding window
- Automatic temporary file management with cleanup
- Enterprise-grade security and resilience patterns

## Environment Variables
Key environment variables (all optional, defaults provided):
- `ISTAT_API_BASE_URL`, `ISTAT_API_TIMEOUT` - ISTAT API configuration
- `POWERBI_CLIENT_ID`, `POWERBI_CLIENT_SECRET`, `POWERBI_TENANT_ID` - PowerBI Azure AD
- `TABLEAU_SERVER_URL`, `TABLEAU_USERNAME`, `TABLEAU_PASSWORD` - Tableau server
- `LOG_LEVEL`, `ENABLE_CACHE` - System configuration

---

## 🚨 Known Limitations & Testing Status

### Infrastructure
- **Docker Compose**: Complete deployment setup tested and functional
- **Docker Images**: No production images built/pushed to registry
- **CI/CD**: Basic unit tests only, no integration/deployment testing

### Business Logic
- **PowerBI Integration**: Structure present but templates FAIL in PowerBI Desktop
- **Tableau Integration**: Basic client only, extract generation incomplete
- **Analytics Dashboard**: Mock data only, no real ISTAT integration
- **Monitoring**: Health endpoints exist, metrics collection untested

### Priority Rework Needed
1. **PowerBI Integration** - Complete redesign required (templates don't work)
2. **Production Deployment** - Need hosting environment and CI/CD pipeline
3. **End-to-End Workflows** - Core works, user workflows need completion

---

**Version**: 12.0.0-dev | **Status**: Core Functional, Infrastructure Untested
**Last Updated**: August 6, 2025
