# CLAUDE.md - Developer Context & Commands

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Italian data processing system for ISTAT (Italian National Institute of Statistics) data with Tableau/Power BI integration. The system fetches, processes, and converts ISTAT statistical data into formats suitable for visualization and analysis.

**Current Status**: Working prototype with basic dashboard functionality

**Documentation**: See [docs/README.md](docs/README.md) for organized documentation

**Important**: Always refer to [PROJECT_STATE.md](PROJECT_STATE.md) for current development context before making any changes to the codebase.

## Development Commands

### Core Commands, many from the first implementation of the project
### We'll look into these very closely during the development
- `python convert_to_tableau.py` - Main conversion script to convert ISTAT XML data to Tableau formats
- `python convert_to_powerbi.py` - Convert ISTAT XML data to PowerBI formats (CSV, Excel, Parquet, JSON)
- `python src/api/istat_api.py` - Test ISTAT API connectivity and data access
- `python src/api/powerbi_api.py` - Test PowerBI API connectivity and manage PowerBI resources
- `python scripts/setup_powerbi_azure.py` - Guided setup for Azure AD and PowerBI configuration
- `python scripts/test_powerbi_upload.py` - Test dataset upload to PowerBI Service
- `python src/analyzers/dataflow_analyzer.py` - Analyze available ISTAT dataflows
- `python src/scrapers/tableau_scraper.py` - Analyze Tableau server configuration
- `powershell scripts/download_istat_data.ps1` - Download ISTAT datasets via PowerShell

### CI/CD Commands
- `python scripts/test_ci.py --strategy auto --generate-data` - Run CI tests with automatic fallback and data generation
- `python scripts/test_ci.py --strategy quick` - Run essential tests for CI/CD
- `python scripts/test_ci.py --strategy minimal` - Run minimal ultra-robust tests for CI/CD
- `python scripts/generate_test_data.py` - Generate mock data for CI/CD testing
- `streamlit run dashboard/app.py` - Run dashboard locally

### File Management Commands
- `python scripts/cleanup_temp_files.py` - Clean up temporary files
- `python scripts/cleanup_temp_files.py --stats` - Show temporary files statistics
- `python scripts/cleanup_temp_files.py --max-age 48` - Clean files older than 48 hours
- `python scripts/organize_data_files.py` - Organize data files according to best practices
- `python scripts/organize_data_files.py --dry-run` - Preview file organization changes
- `python scripts/schedule_cleanup.py` - Set up automatic cleanup scheduling

### Development Environment
- `python -m venv venv` - Create virtual environment
- `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac) - Activate virtual environment
- `pip install -r requirements.txt` - Install dependencies

### Security & Monitoring Commands (NEW)
- `python -c "from src.utils.security_enhanced import security_manager; print(security_manager.get_security_headers())"` - Get security headers
- `python -c "from src.utils.circuit_breaker import get_circuit_breaker_stats; print(get_circuit_breaker_stats())"` - Get circuit breaker stats
- `python -c "from src.utils.security_enhanced import security_manager; security_manager.cleanup_old_entries()"` - Clean up rate limiter entries

### Testing
- `pytest` - Run all tests
- `pytest --cov=src tests/` - Run tests with coverage (173 pass, 100% success rate)
- `pytest tests/unit/` - Run unit tests only (139 tests)
- `pytest tests/integration/` - Run integration tests only (26 tests)
- `pytest tests/performance/` - Run performance tests only (8 tests)
- `pytest --cov=src --cov-report=html tests/` - Generate HTML coverage report

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

## Project Architecture

### Core Components

1. **Data Pipeline Flow**:
   - `src/api/istat_api.py` - ISTAT SDMX API client and data fetcher
   - `src/analyzers/dataflow_analyzer.py` - Analyzes available ISTAT dataflows and categorizes them
   - `src/converters/tableau_converter.py` - Converter for Tableau formats (CSV/Excel/JSON)
   - `src/converters/powerbi_converter.py` - PowerBI converter (CSV, Excel, Parquet, JSON)
   - `convert_to_tableau.py` - Wrapper script for Tableau conversions
   - `convert_to_powerbi.py` - Wrapper script for PowerBI conversions
   - `src/api/powerbi_api.py` - PowerBI REST API client
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

5. **Converter APIs** (New):
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

### Directory Structure
- `src/` - Source code modules
  - `api/` - API clients (ISTAT, PowerBI, Tableau)
  - `analyzers/` - Data analysis and categorization
  - `converters/` - Data format converters (Tableau, PowerBI)
  - `scrapers/` - Web scraping and data extraction
  - `utils/` - Configuration, logging, security utilities, and file management
- `data/` - Data storage
  - `raw/` - Raw ISTAT XML files
  - `processed/` - Converted files
    - `tableau/` - Tableau-ready files
    - `powerbi/` - PowerBI-optimized files (CSV, Excel, Parquet, JSON)
  - `cache/` - Cached API responses
  - `reports/` - Analysis reports and summaries
- `scripts/` - Automation scripts (PowerShell for data download, CI/CD utilities)
- `tests/` - Test suites (unit, integration, performance)
  - `unit/` - Unit tests for individual components (139 tests)
  - `integration/` - Integration tests for system components (26 tests)
  - `performance/` - Performance and scalability tests (8 tests)

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
The project includes a comprehensive test suite with 173 tests across all categories:

- **Unit Tests**: 139 tests covering all core components (100% success rate)
- **Integration Tests**: 26 end-to-end system integration tests
- **Performance Tests**: 8 scalability and performance benchmarks
- **Coverage**: HTML reports available in `htmlcov/` directory
- **Test Results**: All 173 tests passing with 100% success rate

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

#### Enhanced Testing Suite ✅ COMPREHENSIVE, BUT POOR COVERAGE.
- **Security Tests** (`tests/unit/test_security_enhanced.py`):
  - 15+ comprehensive security test cases
  - Path validation testing with Windows path support
  - Rate limiting verification with time-based testing
  - Input sanitization validation with injection prevention
  - Authentication system testing with OAuth flow

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
- **Test Suite**: 173 tests implemented (139 unit + 26 integration + 8 performance)
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
