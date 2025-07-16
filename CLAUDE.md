# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Italian data processing system for ISTAT (Italian National Institute of Statistics) data with Tableau integration. The system fetches, processes, and converts ISTAT statistical data into Tableau/Power BI- friendly formats for visualization and analysis.

## Development Commands

### Core Commands
- `python istat_xml_to_tableau.py` - Main conversion script to convert ISTAT XML data to Tableau formats
- `python istat_xml_to_powerbi.py` - Convert ISTAT XML data to PowerBI formats (CSV, Excel, Parquet, JSON)
- `python src/api/istat_api.py` - Test ISTAT API connectivity and data access
- `python src/api/powerbi_api.py` - Test PowerBI API connectivity and manage PowerBI resources
- `python src/analyzers/dataflow_analyzer.py` - Analyze available ISTAT dataflows
- `python src/scrapers/tableau_scraper.py` - Analyze Tableau server configuration
- `powershell scripts/download_istat_data.ps1` - Download ISTAT datasets via PowerShell

### Development Environment
- `python -m venv venv` - Create virtual environment
- `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac) - Activate virtual environment
- `pip install -r requirements.txt` - Install dependencies

### Testing
- `pytest` - Run all tests
- `pytest --cov=src tests/` - Run tests with coverage
- `pytest tests/unit/` - Run unit tests only
- `pytest tests/integration/` - Run integration tests only

### Code Quality
- `black .` - Format code with Black
- `flake8 .` - Lint code with Flake8
- `isort .` - Sort imports with isort
- `pre-commit run --all-files` - Run pre-commit hooks

## Project Architecture

### Core Components

1. **Data Pipeline Flow**:
   - `src/api/istat_api.py` - ISTAT SDMX API client and data fetcher
   - `src/analyzers/dataflow_analyzer.py` - Analyzes 509+ available ISTAT dataflows and categorizes them
   - `istat_xml_to_tableau.py` - Main converter that transforms SDMX XML to CSV/Excel/JSON formats
   - `istat_xml_to_powerbi.py` - PowerBI converter that transforms SDMX XML to PowerBI-optimized formats (CSV, Excel, Parquet, JSON)
   - `src/api/powerbi_api.py` - PowerBI REST API client for workspace and dataset management
   - `src/scrapers/tableau_scraper.py` - Tableau server integration and configuration analysis

2. **Data Processing Architecture**:
   - Raw ISTAT data is fetched via SDMX API endpoints
   - XML data is parsed and categorized by topic (popolazione, economia, lavoro, territorio, istruzione, salute)
   - Data is cleaned, standardized, and converted to multiple formats for Tableau/Power Bi import
   - Automatic generation of Tableau/Power BI import instructions and metadata

3. **Configuration System**:
   - `src/utils/config.py` - Centralized configuration management with environment variables
   - `src/utils/logger.py` - Loguru-based logging configuration
   - `tableau_config.json` - Tableau server configuration and capabilities

### Directory Structure
- `src/` - Source code modules
  - `api/` - API clients (ISTAT, Tableau)
  - `analyzers/` - Data analysis and categorization
  - `scrapers/` - Web scraping and data extraction
  - `utils/` - Configuration, logging, and utilities
- `data/` - Data storage
  - `raw/` - Raw ISTAT XML files
  - `processed/` - Converted files
    - `tableau/` - Tableau-ready files
    - `powerbi/` - PowerBI-optimized files (CSV, Excel, Parquet, JSON)
  - `cache/` - Cached API responses
  - `reports/` - Analysis reports and summaries
- `scripts/` - Automation scripts (PowerShell for data download)
- `tests/` - Test suites (unit and integration)

### Key Data Flow Categories
The system categorizes ISTAT data into 6 main areas with priority scoring:
1. **Popolazione** (Population) - Priority 10
2. **Economia** (Economy) - Priority 9  
3. **Lavoro** (Employment) - Priority 8
4. **Territorio** (Territory) - Priority 7
5. **Istruzione** (Education) - Priority 6
6. **Salute** (Health) - Priority 5

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

## Common Tasks

- To process new ISTAT data: Run the PowerShell download script, then execute the main conversion script
- To analyze available datasets: Use the dataflow analyzer to categorize and prioritize datasets
- To test API connectivity: Run the ISTAT API tester with comprehensive reporting
- To generate Tableau imports: The converter automatically creates import instructions and metadata
- To generate PowerBI imports: Run `istat_xml_to_powerbi.py` to create optimized PowerBI formats with integration guide
- To test PowerBI connectivity: Use `python src/api/powerbi_api.py` to verify authentication and workspace access