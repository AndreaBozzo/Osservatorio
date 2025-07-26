# CLAUDE.md - Developer Context & Commands

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Italian data processing system for ISTAT (Italian National Institute of Statistics) data with Tableau/Power BI integration. The system fetches, processes, and converts ISTAT statistical data into formats suitable for visualization and analysis.

**Current Status**: Working prototype with basic dashboard functionality

**Documentation**: See [docs/README.md](docs/README.md) for organized documentation

**Important**: Always refer to [PROJECT_STATE.md](docs/project/PROJECT_STATE.md) for current development context before making any changes to the codebase.

**Strategic Update (v8.0.0)**: Following ADR-002, the project has pivoted from PostgreSQL to SQLite + DuckDB architecture for pragmatic metadata management and high-performance analytics.

## Development Commands

### JWT Authentication Commands (NEW 25/07/2025 - Day 7 Complete)
#### API Key Management
- `python scripts/generate_api_key.py create --name "MyApp" --scopes read,write` - Create new API key
- `python scripts/generate_api_key.py list` - List active API keys
- `python scripts/generate_api_key.py revoke --id 123 --reason "Security"` - Revoke API key
- `python scripts/generate_api_key.py test --key osv_your_key_here` - Test API key validity
- `python scripts/generate_api_key.py stats` - Show usage statistics
- `python scripts/generate_api_key.py cleanup` - Clean expired tokens

#### Authentication Testing
- `pytest tests/unit/test_auth_system.py -v` - Run authentication unit tests (29 tests)
- `python test_auth_integration.py` - Run complete integration test (18 scenarios)
- `bandit -r src/auth/` - Run security scan on authentication modules
- `python -c "from src.auth import SQLiteAuthManager; print('✅ Auth system ready')"` - Verify auth system

#### JWT Security Features
- **API Keys**: Cryptographically secure with bcrypt hashing
- **JWT Tokens**: HS256/RS256 with blacklisting support
- **Rate Limiting**: Sliding window algorithm per API key/IP
- **Security Headers**: OWASP-compliant middleware
- **Scopes**: read, write, admin, analytics, powerbi, tableau

### Makefile Commands (Recommended)
The project includes a comprehensive Makefile for streamlined development workflows:

#### Quick Start
- `make help` - Show all available commands
- `make dev-setup` - Complete development environment setup
- `make status` - Show project status and health check
- `make examples` - Show common development workflow examples

#### Testing Workflows
- `make test-fast` - Fast unit tests (~20s)
- `make test-critical` - Critical path tests (~10s)
- `make test-integration` - Integration tests (~10s)
- `make test` - Optimized development testing workflow (~30s)
- `make test-full` - Complete test suite with coverage (~300s)

#### PowerBI Integration
- `make powerbi-validate` - Validate PowerBI integration offline (100% success rate)
- `make powerbi-demo` - Run PowerBI integration demonstration
- `make powerbi-test` - Run PowerBI specific tests

#### Code Quality
- `make format` - Format code with black and isort
- `make lint` - Run linting tools (black, isort, flake8)
- `make pre-commit` - Run pre-commit hooks manually

#### Development Workflows
- `make dev-commit` - Pre-commit workflow (format + critical tests)
- `make dev-push` - Pre-push workflow (format + test + lint)
- `make ci` - Simulate CI/CD pipeline

#### Database Management
- `make db-init` - Initialize database schemas (SQLite + DuckDB)
- `make db-status` - Check database status and health

#### Utilities
- `make clean` - Clean temporary files and caches
- `make benchmark` - Run performance benchmarks
- `make dashboard` - Run Streamlit dashboard

### Core Commands (Direct Python)
- `python convert_to_tableau.py` - Main conversion script to convert ISTAT XML data to Tableau formats
- `python src/api/istat_api.py` - Test ISTAT API connectivity and data access
- `python src/analyzers/dataflow_analyzer.py` - Analyze available ISTAT dataflows
- `python src/scrapers/tableau_scraper.py` - Analyze Tableau server configuration
- `powershell scripts/download_istat_data.ps1` - Download ISTAT datasets via PowerShell

### PowerBI Integration Commands (Enterprise-Ready)
- `python examples/powerbi_integration_demo.py` - Complete PowerBI integration demonstration
- `python scripts/validate_powerbi_offline.py` - Comprehensive offline validation (100% success rate)
- `python src/api/powerbi_api.py` - Test PowerBI API connectivity and diagnostics
- `python scripts/setup_powerbi_azure.py` - Guided setup for Azure AD and PowerBI configuration
- `python scripts/test_powerbi_upload.py` - Test dataset upload to PowerBI Service

### PowerBI Components Testing
- `pytest tests/unit/test_powerbi_api.py -v` - PowerBI API client unit tests
- `pytest tests/unit/test_powerbi_converter.py -v` - PowerBI converter tests
- `pytest tests/integration/test_powerbi_integration.py -v` - Full integration tests
- `python -c "from src.integrations.powerbi.optimizer import PowerBIOptimizer; print('✅ Star Schema Optimizer loaded')"` - Test optimizer
- `python -c "from src.integrations.powerbi.templates import TemplateGenerator; print('✅ Template Generator loaded')"` - Test template generator

### CI/CD Commands
- `python scripts/test_ci.py --strategy auto --generate-data` - Run CI tests with automatic fallback and data generation
- `python scripts/test_ci.py --strategy quick` - Run essential tests for CI/CD
- `python scripts/test_ci.py --strategy minimal` - Run minimal ultra-robust tests for CI/CD
- `python scripts/generate_test_data.py` - Generate mock data for CI/CD testing
- `streamlit run dashboard/app.py` - Run dashboard locally (Streamlit 1.45.0, verified 20/07/2025)
- **Dashboard live**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/) ✅ OPERATIVO

### File Management Commands
- `python scripts/cleanup_temp_files.py` - Clean up temporary files
- `python scripts/cleanup_temp_files.py --stats` - Show temporary files statistics
- `python scripts/cleanup_temp_files.py --max-age 48` - Clean files older than 48 hours
- `python scripts/organize_data_files.py` - Organize data files according to best practices
- `python scripts/organize_data_files.py --dry-run` - Preview file organization changes
- `python scripts/schedule_cleanup.py` - Set up automatic cleanup scheduling

### Development Environment
- **Python Version**: 3.13.3 (verified 20/07/2025)
- **Testing Framework**: pytest 8.3.5 (verified 20/07/2025)
- `python -m venv venv` - Create virtual environment
- `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac) - Activate virtual environment
- `pip install -r requirements.txt` - Install dependencies
- `pip install -r requirements-dev.txt` - Install development dependencies

### SQLite + DuckDB Hybrid Commands (UPDATED 22/07/2025 - Strategic Pivot)
#### DuckDB Analytics (Production Ready)
- `python examples/duckdb_demo.py` - Complete DuckDB demonstration with real ISTAT data
- `python -c "from src.database.duckdb import SimpleDuckDBAdapter; adapter = SimpleDuckDBAdapter(); adapter.create_istat_schema(); print('Schema created')"` - Quick schema setup
- `python -c "from src.database.duckdb import DuckDBManager; manager = DuckDBManager(); print(manager.get_performance_stats())"` - Get performance statistics
- `pytest tests/unit/test_duckdb_basic.py -v` - Run basic DuckDB tests (focused on core functionality)
- `pytest tests/unit/test_duckdb_integration.py -v` - Run comprehensive DuckDB integration tests (45 tests)
- `pytest tests/unit/test_simple_adapter.py -v` - Run simple adapter tests (lightweight usage patterns)

#### SQLite Metadata Management (Day 4 COMPLETED)
- `python examples/sqlite_metadata_demo.py` - SQLite metadata layer demonstration (IMPLEMENTED)
- `python -c "from src.database.sqlite import SQLiteMetadataManager; manager = SQLiteMetadataManager(); print('SQLite schema ready')"` - Initialize SQLite metadata schema
- `pytest tests/unit/test_sqlite_metadata.py -v` - Run SQLite metadata tests (22 tests, 100% pass rate)
- `python -c "from src.database.sqlite import get_metadata_manager; manager = get_metadata_manager(); print(manager.get_database_stats())"` - Get SQLite database statistics

#### Unified Data Repository (Day 4 COMPLETED)
- `python -c "from src.database.sqlite.repository import UnifiedDataRepository; repo = UnifiedDataRepository(); print('Unified repo ready')"` - Test unified data access
- `pytest tests/integration/test_unified_repository.py -v` - Run unified repository integration tests (18 tests, 100% pass rate)
- `python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print(repo.get_system_status())"` - Get hybrid system status

### DuckDB Performance Testing Commands (NEW 21/07/2025)
- `pytest tests/performance/test_duckdb_performance.py -v` - Run comprehensive performance test suite (7 categories)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_bulk_insert_performance -v` - Test bulk insert performance (1k-100k records)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_query_optimization_performance -v` - Test query optimizer with cache analysis
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_concurrent_query_performance -v` - Test concurrent execution (1-8 threads)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_large_dataset_performance -v` - Test large dataset handling (100k+ records)
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_indexing_performance_impact -v` - Test indexing strategies impact
- `pytest tests/performance/test_duckdb_performance.py::TestDuckDBPerformance::test_memory_usage_patterns -v` - Test memory usage patterns and scaling

### Performance Regression Detection Commands (NEW 21/07/2025)
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

### Testing (UPDATED 23/07/2025 - Day 4 SQLite Complete)
- `pytest` - Run all tests (491 tests total, 100% passing as of 25/07/2025)
- `pytest --cov=src tests/` - Run tests with coverage (70.34% total coverage achieved)
- `pytest tests/unit/` - Run unit tests only (includes 22 SQLite metadata tests)
- `pytest tests/integration/` - Run integration tests only (includes 18 unified repository tests)
- `pytest tests/performance/` - Run performance tests only (DuckDB performance suite)
- `pytest --cov=src --cov-report=html tests/` - Generate HTML coverage report
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

### Code Quality
- `black .` - Format code with Black
- `flake8 .` - Lint code with Flake8
- `isort .` - Sort imports with isort
- `pre-commit run --all-files` - Run pre-commit hooks

### Security Features
- **Secure Path Validation**: All file operations use `SecurePathValidator` to prevent directory traversal attacks
- **HTTPS Enforcement**: All API endpoints use HTTPS for secure communication
- **Input Sanitization**: Filenames and paths are sanitized to prevent injection attacks
- **Safe File Operations**: Custom `safe_open()` method validates paths before file operations
- **Extension Validation**: Only approved file extensions are allowed (.json, .csv, .xlsx, .ps1, etc.)
- **Path Traversal Protection**: Prevents `../` and absolute path attacks
- **Windows Path Support**: Proper handling of Windows drive letters (C:\) and path separators
- **Reserved Name Handling**: Prevents use of Windows reserved names (CON, PRN, AUX, etc.)
- **Enhanced Error Handling**: All converter operations include robust error handling with secure error messages
- **XML Parsing Security**: ET.fromstring() used instead of ET.parse() for direct XML content parsing
- **Path Validation Integration**: All converter methods use secure path validation for file operations

## Project Architecture (Updated 25/07/2025 - Day 7 Complete)

### System Architecture Overview
```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   DuckDB Engine     │     │  SQLite Metadata    │     │   PowerBI Service   │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ • ISTAT Analytics   │     │ • Dataset Registry  │     │ • Workspaces        │
│ • Time Series       │     │ • User Preferences  │     │ • Datasets          │
│ • Aggregations      │     │ • API Keys/Auth     │     │ • Reports           │
│ • Performance Data  │     │ • Audit Logging     │     │ • Dashboards        │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         ↓                           ↓                           ↑
    ┌────────────────────────────────┐                           │
    │   Unified Data Repository      │                           │
    │   (Facade Pattern)             │                           │
    └────────────────────────────────┘                           │
                 ↓                                               │
    ┌────────────────────────────────────────────────────────────┤
    │                  🔐 JWT Authentication Layer               │
    │   API Keys • JWT Tokens • Rate Limiting • Security Headers │
    └─────────────────────────────────────────────────────────────┘
                                    ↓
              ┌─────────────────────────────────────┐
              │          REST API Layer             │
              │    (FastAPI - Future Implementation) │
              └─────────────────────────────────────┘
```

### Core Components

1. **Authentication System (Day 7 - NEW!)**:
   - `src/auth/sqlite_auth.py` - SQLite-backed API key management with bcrypt hashing
   - `src/auth/jwt_manager.py` - JWT token creation, validation, and blacklisting
   - `src/auth/rate_limiter.py` - Sliding window rate limiting per API key/IP
   - `src/auth/security_middleware.py` - OWASP security headers and auth middleware
   - `scripts/generate_api_key.py` - CLI tool for API key management
   - `tests/unit/test_auth_system.py` - Comprehensive authentication test suite (29 tests)

2. **Data Pipeline Flow**:
   - `src/api/istat_api.py` - ISTAT SDMX API client and data fetcher
   - `src/analyzers/dataflow_analyzer.py` - Analyzes available ISTAT dataflows and categorizes them
   - `src/converters/tableau_converter.py` - Converter for Tableau formats (CSV/Excel/JSON)
   - `src/converters/powerbi_converter.py` - PowerBI converter (CSV, Excel, Parquet, JSON)
   - `convert_to_tableau.py` - Wrapper script for Tableau conversions
   - `src/api/powerbi_api.py` - Enterprise PowerBI REST API client with MSAL authentication
   - `src/integrations/powerbi/optimizer.py` - Star Schema Optimizer with DAX measures generation
   - `src/integrations/powerbi/templates.py` - PowerBI Template Generator (.pbit files)
   - `src/integrations/powerbi/incremental.py` - Incremental Refresh Manager with change detection
   - `src/integrations/powerbi/metadata_bridge.py` - Data governance and lineage tracking
   - `examples/powerbi_integration_demo.py` - Complete PowerBI enterprise demo
   - `scripts/validate_powerbi_offline.py` - 100% offline validation system
   - `src/scrapers/tableau_scraper.py` - Tableau server integration

2. **Data Processing Architecture**:
   - Raw ISTAT data is fetched via SDMX API endpoints
   - XML data is parsed and categorized by topic (popolazione, economia, lavoro, territorio, istruzione, salute)
   - Data is cleaned, standardized, and converted to multiple formats
   - Basic generation of import instructions and metadata
   - Direct XML content parsing with `_parse_xml_content()` methods
   - Automatic dataset categorization with priority scoring
   - Data quality validation with completeness scoring
   - Programmatic conversion APIs for both PowerBI and Tableau

3. **Configuration System**:
   - `src/utils/config.py` - Centralized configuration management with environment variables
   - `src/utils/logger.py` - Loguru-based logging configuration
   - `tableau_config.json` - Tableau server configuration and capabilities

4. **Security & Utilities**:
   - `src/utils/secure_path.py` - Secure path validation and file operations
   - `src/utils/temp_file_manager.py` - Temporary file management with automatic cleanup
   - All file operations use validated paths and safe file handling
   - HTTPS enforcement for all external API calls

5. **DuckDB Analytics Engine** (UPDATED 21/07/2025):
   - **DuckDBManager**: Full-featured connection manager
     - `execute_query(query, parameters)` - Parameterized query execution
     - `execute_statement(statement, parameters)` - DDL/DML operations
     - `bulk_insert(table_name, data)` - Optimized bulk data insertion
     - `get_performance_stats()` - Real-time performance monitoring
   - **SimpleDuckDBAdapter**: Lightweight interface for immediate use
     - `create_istat_schema()` - Automatic ISTAT schema creation
     - `insert_observations(df)` - Direct DataFrame insertion
     - `get_time_series(dataset_id, territory_code)` - Analytics queries
   - **QueryOptimizer**: Advanced query optimization
     - `create_advanced_indexes()` - Automatic index management
     - `get_cache_stats()` - Cache performance monitoring
     - `optimize_table_statistics()` - Query plan optimization
   - **PartitionManager**: Data partitioning strategies
     - Year-based, territory-based, and hybrid partitioning
     - Automatic partition pruning for optimal performance

6. **Performance Testing & Monitoring System** (NEW 21/07/2025):
   - **DuckDBPerformanceProfiler**: Advanced performance profiler (`tests/performance/test_duckdb_performance.py`)
     - `start_profiling()` - Begin performance measurement session
     - `end_profiling()` - End session and return metrics (execution time, memory, CPU)
     - Memory usage tracking with psutil integration
     - Real-time CPU percentage monitoring
   - **PerformanceRegressionDetector**: Automated regression detection (`scripts/performance_regression_detector.py`)
     - `run_full_analysis()` - Complete regression analysis pipeline
     - `detect_regressions(metrics)` - Compare against baselines with statistical analysis
     - `generate_performance_report()` - Markdown reports with trends and alerts
     - Configurable thresholds (minor 10%, moderate 25%, severe 50%)
     - Baseline management with historical data retention (50 measurements per metric)
   - **Performance Test Categories**: Comprehensive test coverage
     - Bulk insert performance (1k to 100k+ records)
     - Query optimization with cache hit/miss analysis
     - Concurrent execution testing (1-8 threads)
     - Memory usage patterns and scaling analysis
     - Indexing impact measurement
     - Large dataset performance validation

7. **Converter APIs**:
   - **PowerBI Converter**: `IstatXMLToPowerBIConverter`
     - `convert_xml_to_powerbi(xml_input, dataset_id, dataset_name)` - Main conversion API
     - `_parse_xml_content(xml_content)` - Direct XML parsing to DataFrame
     - `_categorize_dataset(dataset_id, dataset_name)` - Auto-categorization with priority
     - `_validate_data_quality(df)` - Data quality assessment
     - `_generate_powerbi_formats(df, dataset_info)` - Multi-format generation
   - **Tableau Converter**: `IstatXMLtoTableauConverter`
     - `convert_xml_to_tableau(xml_input, dataset_id, dataset_name)` - Main conversion API
     - `_parse_xml_content(xml_content)` - Direct XML parsing to DataFrame
     - `_categorize_dataset(dataset_id, dataset_name)` - Auto-categorization with priority
     - `_validate_data_quality(df)` - Data quality assessment
     - `_generate_tableau_formats(df, dataset_info)` - Multi-format generation

### Directory Structure (Updated 25/07/2025 - Day 7 Complete)
- `src/` - Source code modules
  - `api/` - API clients (ISTAT, PowerBI, Tableau)
  - `analyzers/` - Data analysis and categorization
  - `auth/` - **NEW! JWT Authentication System (Day 7)**
    - `models.py` - Authentication data models (APIKey, AuthToken, TokenClaims)
    - `sqlite_auth.py` - SQLite API key management with bcrypt
    - `jwt_manager.py` - JWT token creation, validation, blacklisting
    - `rate_limiter.py` - Sliding window rate limiting with SQLite
    - `security_middleware.py` - OWASP security headers & auth middleware
  - `converters/` - Data format converters (Tableau, PowerBI)
  - `database/` - Hybrid database architecture
    - `duckdb/` - DuckDB analytics engine (7 files)
      - `manager.py` - Connection management & pooling
      - `schema.py` - ISTAT data schemas
      - `simple_adapter.py` - Lightweight interface
      - `query_builder.py` - Fluent query interface
      - `query_optimizer.py` - Query optimization & caching
      - `partitioning.py` - Data partitioning strategies
      - `config.py` - DuckDB configuration
    - `sqlite/` - SQLite metadata layer (3 files)
      - `manager.py` - SQLite connection & transaction management
      - `schema.py` - Metadata schema (6 tables)
      - `repository.py` - Unified data repository facade
  - `integrations/` - External service integrations
    - `powerbi/` - PowerBI enterprise integration (5 files)
      - `optimizer.py` - Star schema optimizer
      - `templates.py` - .pbit template generator
      - `incremental.py` - Incremental refresh manager
      - `metadata_bridge.py` - Data governance bridge
  - `scrapers/` - Web scraping and data extraction
  - `utils/` - Core utilities (7 files)
    - `security_enhanced.py` - Security management
    - `circuit_breaker.py` - Resilience patterns
    - `config.py` - Configuration management
    - `logger.py` - Structured logging
    - `secure_path.py` - Secure file operations
    - `temp_file_manager.py` - Temporary file management
- `data/` - Data storage
  - `raw/` - Raw ISTAT XML files
  - `processed/` - Converted files
    - `tableau/` - Tableau-ready files
    - `powerbi/` - PowerBI-optimized files (CSV, Excel, Parquet, JSON)
  - `cache/` - Cached API responses
  - `reports/` - Analysis reports and summaries
- `scripts/` - Automation scripts (PowerShell for data download, CI/CD utilities)
- `tests/` - Test suites (unit, integration, performance) - SIGNIFICANTLY EXPANDED!
  - `unit/` - Unit tests for individual components (270+ tests)
    - `test_duckdb_basic.py` - NEW! Basic DuckDB functionality tests
    - `test_duckdb_integration.py` - NEW! Comprehensive DuckDB tests (45 tests)
    - `test_simple_adapter.py` - NEW! Simple DuckDB adapter tests
    - `test_tableau_api.py` - Comprehensive Tableau API tests (20 tests)
    - `test_temp_file_manager.py` - Temp file management tests (26 tests)
    - `test_istat_api.py` - Enhanced ISTAT API tests (25 tests)
    - `test_final_coverage.py` - Edge cases and utilities (17 tests)
    - Plus existing: config, logger, dataflow_analyzer, converters, security, etc.
  - `integration/` - Integration tests for system components (26 tests)
  - `performance/` - Performance and scalability tests (8 tests)
- `examples/` - NEW! Usage examples
  - `duckdb_demo.py` - Complete DuckDB demonstration

### Key Data Flow Categories, this might be a residual from the very
### first data pull from ISTAT API, from an SDGs, we'll look into this
The system categorizes ISTAT data into 7 main areas with priority scoring:
1. **Popolazione** (Population) - Priority 10
2. **Economia** (Economy) - Priority 9
3. **Lavoro** (Employment) - Priority 8
4. **Territorio** (Territory) - Priority 7
5. **Istruzione** (Education) - Priority 6
6. **Salute** (Health) - Priority 5
7. **Altro** (Other) - Priority 1

### Data Quality Validation
The system now includes comprehensive data quality assessment:
- **Completeness Score**: Percentage of non-null values in dataset
- **Data Quality Score**: Overall quality assessment including numeric data validation
- **Metrics Reporting**: Total rows, columns, and quality scoring for each dataset
- **Validation Integration**: Automatic quality assessment during conversion process

### Integration Points
- **ISTAT SDMX API**: `http://sdmx.istat.it/SDMXWS/rest/` - Primary data source
- **Tableau Server**: OAuth-enabled connections for BigQuery, Google Sheets, Box, Dropbox
- **PowerBI Service**: REST API integration with Microsoft identity platform (MSAL)
- **Output Formats**:
  - Tableau: CSV (direct import), Excel (with metadata), JSON (for APIs)
  - PowerBI: CSV, Excel, Parquet (optimized performance), JSON

## Important Notes

- All ISTAT data is fetched from official SDMX endpoints
- The system handles Italian regional data with proper geographic mapping
- Tableau integration supports both Server and Public versions
- PowerShell scripts are optimized for Windows environments
- Rate limiting is implemented for API calls (2-3 second delays)
- Data validation includes completeness scoring and quality reports

## File Management

### Temporary Files
- All temporary files are managed by `TempFileManager` class
- Files are stored in system temp directory under `osservatorio_istat/`
- Automatic cleanup on application exit
- Manual cleanup available via `cleanup_temp_files.py` script

### Directory Structure for Temporary Files
- `temp/api_responses/` - API response files (dataflow_response.xml, data_DCIS_*.xml, structure_DCIS_*.xml)
- `temp/samples/` - Sample data files
- `temp/misc/` - Other temporary files

### Best Practices
- Temporary files are automatically organized and cleaned up
- Use `--dry-run` flag to preview changes before applying
- Schedule regular cleanup with `schedule_cleanup.py`
- Monitor temp file usage with `--stats` option

## Environment Configuration

Required environment variables (optional, defaults provided):
- `ISTAT_API_BASE_URL` - ISTAT API base URL
- `ISTAT_API_TIMEOUT` - API request timeout
- `TABLEAU_SERVER_URL` - Tableau server URL
- `TABLEAU_USERNAME` - Tableau username
- `TABLEAU_PASSWORD` - Tableau password
- `POWERBI_CLIENT_ID` - PowerBI App registration client ID
- `POWERBI_CLIENT_SECRET` - PowerBI App registration client secret
- `POWERBI_TENANT_ID` - Azure AD tenant ID
- `POWERBI_WORKSPACE_ID` - PowerBI workspace ID (optional)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)
- `ENABLE_CACHE` - Enable data caching

## Testing Infrastructure

### Test Suite Overview
The project includes a developing test framework with basic coverage:

- **Test Infrastructure**: 215 tests collected across unit, integration, and performance categories
- **Current Focus**: Core functionality testing for dashboard and data processing
- **Coverage**: Basic test coverage with HTML reports in `htmlcov/` directory
- **Status**: Test framework in development, improving coverage incrementally
- **Quality**: Focus on critical functionality rather than comprehensive coverage

### Test Categories
1. **Core Components** (139 unit tests passing):
   - `test_config.py` - Configuration management
   - `test_logger.py` - Logging system
   - `test_dataflow_analyzer.py` - ISTAT dataflow analysis
   - `test_istat_api.py` - ISTAT API connectivity
   - `test_powerbi_api.py` - PowerBI API integration
   - `test_tableau_scraper.py` - Tableau server analysis
   - `test_converters.py` - Data format conversions
   - `test_secure_path.py` - Security utilities and path validation
   - `test_powerbi_converter.py` - PowerBI converter functionality (14 tests)
   - `test_tableau_converter.py` - Tableau converter functionality (15 tests)

2. **Performance Tests**:
   - Scalability tests with 1000+ dataflows
   - Concurrent API request handling
   - Memory usage optimization
   - File I/O performance benchmarks

3. **Integration Tests**:
   - Complete pipeline testing
   - API integration workflows
   - System component integration

### Test Configuration
- **pytest.ini** - Test configuration with performance markers
- **conftest.py** - Shared test fixtures and setup
- **Requirements**: `pytest`, `pytest-cov`, `pytest-mock`, `psutil`, `seaborn`, `matplotlib`

### New Dependencies
- **numpy** - Added for numerical data validation in quality assessment
- **pandas** - Enhanced usage for DataFrame operations and data quality validation
- **pathlib** - Improved path handling for secure file operations

## Programmatic API Usage

### PowerBI Converter API
```python
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter

# Initialize converter
converter = IstatXMLToPowerBIConverter()

# Convert XML content directly
result = converter.convert_xml_to_powerbi(
    xml_input="<xml content>",  # or path to XML file
    dataset_id="DCIS_POPRES1",
    dataset_name="Popolazione residente"
)

# Result structure
{
    "success": True,
    "files_created": {
        "csv_file": "path/to/file.csv",
        "excel_file": "path/to/file.xlsx",
        "parquet_file": "path/to/file.parquet",
        "json_file": "path/to/file.json"
    },
    "data_quality": {
        "total_rows": 1000,
        "total_columns": 5,
        "completeness_score": 0.95,
        "data_quality_score": 0.87
    },
    "summary": {
        "dataset_id": "DCIS_POPRES1",
        "category": "popolazione",
        "priority": 10,
        "files_created": 4
    }
}
```

### Tableau Converter API
```python
from src.converters.tableau_converter import IstatXMLtoTableauConverter

# Initialize converter
converter = IstatXMLtoTableauConverter()

# Convert XML content directly
result = converter.convert_xml_to_tableau(
    xml_input="<xml content>",  # or path to XML file
    dataset_id="DCIS_POPRES1",
    dataset_name="Popolazione residente"
)

# Result structure (similar to PowerBI but with Tableau-specific formats)
{
    "success": True,
    "files_created": {
        "csv_file": "path/to/file.csv",
        "excel_file": "path/to/file.xlsx",
        "json_file": "path/to/file.json"
    },
    "data_quality": {...},
    "summary": {...}
}
```

### Individual Method Usage
```python
# Parse XML content to DataFrame
df = converter._parse_xml_content(xml_content)

# Categorize dataset
category, priority = converter._categorize_dataset("DCIS_POPRES1", "Popolazione residente")

# Validate data quality
quality_report = converter._validate_data_quality(df)

# Generate multiple formats
files = converter._generate_powerbi_formats(df, dataset_info)
```

## Common Tasks

- To process new ISTAT data: Run the PowerShell download script, then execute the main conversion script
- To analyze available datasets: Use the dataflow analyzer to categorize and prioritize datasets
- To test API connectivity: Run the ISTAT API tester with comprehensive reporting
- To generate Tableau imports: The converter automatically creates import instructions and metadata
- To generate PowerBI imports: Run `istat_xml_to_powerbi.py` to create optimized PowerBI formats with integration guide
- To setup PowerBI integration: Run `python scripts/setup_powerbi_azure.py` for guided Azure AD configuration
- To test PowerBI connectivity: Use `python src/api/powerbi_api.py` to verify authentication and workspace access
- To test PowerBI upload: Run `python scripts/test_powerbi_upload.py` to test dataset upload to PowerBI Service
- **New**: To convert XML programmatically: Use the converter APIs directly in your Python code
- **New**: To validate data quality: Use `_validate_data_quality()` method for quality assessment
- **New**: To categorize datasets: Use `_categorize_dataset()` for automatic categorization with priority

## Recent Updates (January 2025)

### Major Achievements
- **Dashboard Live**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)
- **Security Implementation**: SecurityManager with path validation and rate limiting
- **CI/CD Setup**: GitHub Actions workflow with automated testing
- **Rate Limiting**: Basic API protection (ISTAT: 50 req/hr, PowerBI: 100 req/hr)
- **Data Pipeline**: ISTAT API integration with available datasets
- **Performance**: Caching system with 30min TTL

### 🔧 Core Components Status

#### Security Management System ✅ ADDED, MORE TESTING NEEDED.
- **SecurityManager Class** (`src/utils/security_enhanced.py`):
  - Path validation with directory traversal protection
  - Rate limiting with configurable thresholds (ISTAT: 50 req/hr, PowerBI: 100 req/hr)
  - Input sanitization and validation across all endpoints
  - Secure password hashing with PBKDF2
  - IP blocking and security headers
  - Comprehensive security decorators

#### Circuit Breaker Implementation ✅ ACTIVE, MORE TESTS NEEDED.
- **Circuit Breaker Pattern** (`src/utils/circuit_breaker.py`):
  - Resilient external API calls with automatic recovery
  - Automatic failure detection and recovery
  - Configurable failure thresholds
  - State management (CLOSED/OPEN/HALF_OPEN)
  - Statistics and monitoring with real-time metrics

#### Real-Time Data Pipeline ✅ OPERATIONAL, but barebone.
- **IstatRealTimeDataLoader** (`dashboard/data_loader.py`):
  - Live ISTAT API integration with 509+ datasets
  - Automatic retry mechanism with exponential backoff
  - Intelligent caching with 30min TTL
  - Progress indicators and loading states
  - Graceful fallback to cached data when API unavailable

#### Enhanced Testing Suite ✅ SIGNIFICANTLY IMPROVED COVERAGE (19/01/2025)
- **Security Tests** (`tests/unit/test_security_enhanced.py`):
  - 15+ comprehensive security test cases
  - Path validation testing with Windows path support
  - Rate limiting verification with time-based testing
  - Input sanitization validation with injection prevention
  - Authentication system testing with OAuth flow

- **NEW! Tableau API Tests** (`tests/unit/test_tableau_api.py`):
  - 20 comprehensive test cases for TableauServerAnalyzer
  - Full coverage of data extraction, categorization, and strategy generation
  - Edge cases for malformed data and error handling
  - Mock-based testing for external dependencies

- **NEW! Temp File Manager Tests** (`tests/unit/test_temp_file_manager.py`):
  - 26 test cases covering singleton pattern, context managers
  - File and directory lifecycle management
  - Error handling and cleanup verification
  - Thread safety and integration testing

- **EXPANDED! ISTAT API Tests** (`tests/unit/test_istat_api.py`):
  - 25+ enhanced test cases for IstatAPITester
  - Rate limiting, error handling, and timeout scenarios
  - XML parsing and data quality validation
  - Comprehensive mock-based API testing

### 🚀 Dashboard Deployment ✅ LIVE, BUT BAREBONE.
- **Live Dashboard**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)
- **Deployment Guide**: Complete documentation in `STREAMLIT_DEPLOYMENT.md`
- **Configuration**: Streamlit config optimized for production with security headers
- **Performance**: Load time optimized with caching and async loading
- **Real-Time Data**: Live ISTAT API integration with progress indicators
- **Error Handling**: Graceful degradation with fallback mechanisms

### 🛡️ Security Implementations ✅ BASIC AND NOT FULLY TESTED
- **API Rate Limiting**:
  - ISTAT API: 50 requests/hour per endpoint (actively enforced)
  - PowerBI API: 100 requests/hour per endpoint (actively enforced)
  - Automatic rate limit enforcement with IP blocking
  - Configurable per-endpoint limits with time-based windows

- **Path Security**:
  - Directory traversal protection (all file operations secured)
  - File extension validation with whitelist approach
  - Windows reserved name handling with comprehensive detection
  - Base directory restrictions with absolute path validation

- **Input Validation**:
  - XSS prevention with automatic sanitization
  - SQL injection protection with parameterized queries
  - Command injection prevention with input validation
  - Path traversal prevention with secure path validation

### 🔧 CI/CD Improvements ✅ OPERATIONAL
- **GitHub Actions**: Fixed workflow blocking issues with comprehensive testing
- **Security Scanning**: Integrated Bandit and Safety checks with automated reports
- **Deployment Pipeline**: Automated testing and deployment with zero-downtime
- **Error Handling**: Robust fallback mechanisms with circuit breaker pattern
- **Performance Testing**: Automated performance benchmarks with trend analysis

## Previous Updates (July 2025)

### Major Enhancements
- **Test Framework**: Basic testing infrastructure with pytest (developing coverage)
- **Converter APIs**: Programmatic APIs for both PowerBI and Tableau converters
- **Security**: Integration of SecurePathValidator across file operations
- **Data Quality**: Basic data quality assessment system
- **Auto-Categorization**: Dataset categorization with priority scoring

### New Methods Added
- `convert_xml_to_powerbi()` and `convert_xml_to_tableau()` - Main conversion APIs
- `_parse_xml_content()` - Direct XML content parsing
- `_categorize_dataset()` - Automatic categorization with priority scoring
- `_validate_data_quality()` - Comprehensive data quality assessment
- `_generate_powerbi_formats()` and `_generate_tableau_formats()` - Multi-format generation

### Testing Improvements
- **Unit Tests**: 139 tests covering core functionality
- **Integration Tests**: 26 system integration tests
- **Performance Tests**: 8 basic performance benchmarks
- **Test Coverage**: Coverage of main APIs and methods

### Security Enhancements
- **SecurityManager Class**: Basic security management with path validation and rate limiting
- **Circuit Breaker Pattern**: Basic resilience for external API calls
- **Rate Limiting**: Basic implementation on ISTAT API (50 req/hr) and PowerBI API (100 req/hr)
- **Path Traversal Protection**: Basic validation against directory traversal attacks
- **Input Sanitization**: Basic sanitization of user inputs
- **Security Headers**: HTTP security headers for dashboard
- **Password Hashing**: Basic password handling with PBKDF2
- **IP Blocking**: Basic IP blocking for suspicious activities
- Basic error handling with secure error messages
- XML parsing security improvements
- Path validation integration in converter methods
- Secure file operations

## 📝 Documentation & Process (UPDATED 20/07/2025)

### Documentation Structure ✅ VERIFICATA
- **Main Documentation**: [docs/README.md](docs/README.md) - Organized project documentation
- **API Reference**: [docs/api-mapping.md](docs/api-mapping.md) - Complete ISTAT endpoint mapping
- **Architecture Decisions**: [docs/adr/](docs/adr/) - ADR records per decisioni tecniche
- **Contributing Guide**: [docs/guides/CONTRIBUTING.md](docs/guides/CONTRIBUTING.md) - Formattato e strutturato
- **Project State**: [PROJECT_STATE.md](PROJECT_STATE.md) - Stato sviluppo corrente

### Development Process ✅ ATTIVO
- **Git Workflow**: Feature branches con commit convenzionali
- **Code Quality**: black, flake8, isort, pre-commit hooks
- **Testing**: pytest con coverage reporting (292 tests verificati)
- **CI/CD**: GitHub Actions con testing automatico
- **Security**: Bandit e Safety checks integrati

### Environment Specs ✅ VERIFICATE 21/07/2025
- **Python**: 3.13.3 (tags/v3.13.3:6280bb5, Apr 8 2025)
- **Testing**: pytest 8.3.5
- **Dashboard**: Streamlit 1.45.0
- **Total Tests**: 319+ (all passing, significantly expanded)
- **Coverage**: Improved with DuckDB modules
- **NEW: DuckDB**: High-performance analytics engine integrated

## Recent Updates (25/07/2025) - Day 7: JWT Authentication System Complete

### 🔐 Major Security Implementation (Day 7)
- **Complete JWT Authentication System** - Enterprise-grade authentication with SQLite backend
  - SQLite API key management with bcrypt hashing and scope-based permissions
  - JWT token system with HS256/RS256 support and token blacklisting
  - Sliding window rate limiting per API key and IP address
  - OWASP-compliant security headers middleware
  - CLI tool for API key management with full CRUD operations
- **Security Validation** - Comprehensive security audit and testing
  - Bandit security scan: 0 high severity issues (1 minor false positive)
  - SQL injection protection with parameterized queries
  - Database connection cleanup and transaction safety
  - Cross-platform testing (Windows/Linux compatibility)
- **Testing Infrastructure** - Robust test suite for authentication
  - 29 unit test methods covering all authentication components
  - Integration test with 18 scenarios for complete authentication flows
  - Database cleanup fixes for Windows file lock issues
  - Nested transaction handling improvements

### 🔧 Database & Security Improvements (Day 7)
- **Transaction Safety** - Enhanced SQLite transaction management
  - Automatic nested transaction detection and handling
  - Proper connection cleanup with retry mechanism for Windows
  - Fixed ResourceWarning and PermissionError in test cleanup
- **SQL Security** - Complete protection against SQL injection
  - Replaced f-string SQL construction with parameterized queries
  - All database queries use prepared statements
  - Security compliance verified with Bandit scan

## Previous Updates (21/07/2025) - Day 3: DuckDB Performance Testing & Optimization

### 🚀 Major Additions
- **Comprehensive Performance Testing Suite** - 7 test categories with advanced profiling (670+ lines of code)
- **Performance Regression Detection** - Automated monitoring and alerting system (520+ lines of code)
- **Outstanding Performance Results** - Record-breaking benchmarks documented and validated
- **Enhanced Test Infrastructure** - Fixed performance test issues with tolerance handling
- **Production-Ready Monitoring** - Real-time performance tracking and baseline management

### 🔧 Technical Improvements
- **Advanced Profiling** - Memory, CPU, and execution time monitoring with psutil integration
- **Statistical Analysis** - Baseline tracking with median-based regression detection
- **Concurrent Testing** - Multi-threaded performance validation (1-8 threads)
- **Scalability Testing** - Large dataset performance validation (100k+ records)
- **Memory Analysis** - Linear scaling validation and memory usage patterns

### 📊 Performance Achievements (Day 3)
- **High-performance bulk insert** - >2k records/second validated in tests
- **Fast queries** - Aggregation queries optimized for large datasets
- **5x+ speedup** - Query caching effectiveness validated
- **<1KB per record** - Memory usage with linear scaling confirmed
- **8-thread concurrency** - Concurrent execution scaling tested and validated

### 🛡️ Quality & Reliability
- **Flake8 Compliance** - All modulo operator spacing and import issues fixed
- **Pre-commit Hooks** - All quality checks passing (black, isort, flake8)
- **Test Reliability** - All 319+ tests passing consistently
- **Regression Prevention** - Automated performance monitoring prevents degradation

## Important Instructions
Respect existing implementations and verify functionality before making changes.
ALWAYS check current test status and coverage before modifying code.
Use the CONTRIBUTING.md guide for development standards and processes.
Refer to PROJECT_STATE.md for current development context.
