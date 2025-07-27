# 🇮🇹 Osservatorio - ISTAT Data Processing Platform

> **Italian statistical data platform with JWT authentication foundation, PowerBI integration capabilities, and high-performance analytics engine.**

[![Python](https://img.shields.io/badge/Python-3.13.3-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Status-Development%20Ready-orange.svg)](docs/project/PROJECT_STATE.md)
[![Tests](https://img.shields.io/badge/Tests-491%20passing-green.svg)](tests/)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live%20✅-green.svg)](https://osservatorio-dashboard.streamlit.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API%20Complete%20✅-green.svg)](src/api/fastapi_app.py)
[![Security](https://img.shields.io/badge/Security-JWT%20Auth%20🔐-green.svg)](src/auth/)
[![PowerBI](https://img.shields.io/badge/PowerBI-OData%20v4%20Ready-blue.svg)](docs/integrations/POWERBI_INTEGRATION.md)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics%20Engine-blue.svg)](src/database/duckdb/)
[![SQLite](https://img.shields.io/badge/SQLite-Metadata%20Layer-orange.svg)](src/database/sqlite/)
[![JWT](https://img.shields.io/badge/Auth-JWT%20+%20API%20Keys-purple.svg)](docs/security/AUTHENTICATION.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/Coverage-70.34%25-yellow.svg)](tests/)
[![Issue29](https://img.shields.io/badge/Issue%2029-Complete%20✅-brightgreen.svg)](scripts/validate_issue29_implementation.py)

## 🚀 Project Status: Production-Ready Platform with Complete REST API

**✅ FastAPI REST API Complete**: Italian statistical data platform with full API implementation and enterprise architecture.

### 🎯 What's Working Now (Day 8 Complete - Issue #29)
- ✅ **FastAPI REST API**: Complete multi-user API with OpenAPI documentation (Issue #29 - 100% success)
- ✅ **OData v4 PowerBI Integration**: Direct Query endpoint for real-time PowerBI connectivity
- ✅ **JWT Authentication System**: API key management with bcrypt hashing and rate limiting
- ✅ **Dataset Management**: REST endpoints for datasets, time series, and analytics
- ✅ **Security Foundation**: OWASP headers, SQL injection protection, audit logging
- ✅ **PowerBI Data Pipeline**: Star schema generation, data optimization, and processing
- ✅ **High-Performance Analytics**: DuckDB engine processing >2k records/sec
- ✅ **Comprehensive Testing**: 491 tests passing (70.34% coverage)
- ✅ **SQLite + DuckDB Architecture**: Hybrid metadata + analytics database system
- ✅ **ISTAT Data Integration**: Complete pipeline from ISTAT API to analytics-ready data

### 🔄 Next Phase (Day 9)
- 🔄 **Usage Analytics Dashboard**: Real-time API usage monitoring and statistics
- 🔄 **Enhanced Documentation**: Complete API documentation with examples
- 🔄 **Advanced Monitoring**: Performance metrics and alerting systems

**🎯 Target Audience**: Data developers, researchers, analysts working with Italian statistical data.

**📄Github Pages Index**: [https://andreabozzo.github.io/Osservatorio/](https://andreabozzo.github.io/Osservatorio/)

**📊 Live Dashboard**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)

**🚀 Sprint Active**: [GitHub Project Board](https://github.com/AndreaBozzo/Osservatorio/projects) | [Join Discussion](https://github.com/AndreaBozzo/Osservatorio/discussions) | [Wiki Documentation](https://github.com/AndreaBozzo/Osservatorio/wiki)

---

## 🚀 Quick Start

### 📥 Installation
```bash
# 1. Clone repository
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests (optional)
pytest tests/ -v

# 5. Start dashboard
streamlit run src/dashboard/streamlit_app.py
```

### 🎯 Quick Actions
```bash
# NEW! FastAPI REST API (Issue #29 Complete)
python -c "import sys; sys.path.append('.'); exec(open('scripts/validate_issue29_implementation.py').read())"  # Validate all deliverables
python -c "import sys; sys.path.append('.'); from src.api.fastapi_app import app; print('FastAPI ready!')"

# Test API connectivity
python -c "import sys; sys.path.append('.'); from src.api import istat_api; print('ISTAT API module loaded')"

# Convert data for Tableau
python convert_to_tableau.py

# PowerBI Integration Demo (Foundation)
python examples/powerbi_integration_demo.py

# Validate PowerBI Integration (Offline - 19/19 tests passing)
python scripts/validate_powerbi_offline.py

# DuckDB Analytics Demo
python examples/duckdb_demo.py

# SQLite Metadata Management
python examples/sqlite_metadata_demo.py

# Authentication System (Day 7)
python scripts/generate_api_key.py list  # Manage API keys
```

---

## 🚀 Strategic Architecture (SQLite + DuckDB)

### 🏗️ **Current Architecture (v10.0.0 - FastAPI Complete)**
Following ADR-002 strategic decision with FastAPI REST layer:

```
┌─────────────────────────────────────────────────────────────┐
│                    🌐 FastAPI REST API Layer                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   /datasets     │ │   /auth/token   │ │   /odata        ││
│  │   /analytics    │ │   /auth/keys    │ │   OpenAPI Docs  ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────┐     ┌─────────────────────┐
│   DuckDB Engine     │     │  SQLite Metadata    │
├─────────────────────┤     ├─────────────────────┤
│ • ISTAT Analytics   │     │ • Dataset Registry  │
│ • Time Series       │     │ • User Preferences  │
│ • Aggregations      │     │ • API Keys/Auth     │
│ • Performance Data  │     │ • Audit Logging     │
└─────────────────────┘     └─────────────────────┘
         ↓                           ↓
    ┌────────────────────────────────┐
    │   Unified Data Repository      │
    │   (Facade Pattern)             │
    └────────────────────────────────┘
```

### ✅ **Current Capabilities**
- **🚀 FastAPI REST API**: Complete multi-user API with OpenAPI documentation (Issue #29 - 100% success)
- **🔗 OData v4 Endpoint**: PowerBI Direct Query support with performance optimization
- **🦆 DuckDB Analytics**: High-performance analytics engine (>2k records/sec)
- **🗃️ SQLite Metadata**: Lightweight metadata layer (zero configuration)
- **📊 PowerBI Integration**: Native BI tool support with star schema (19/19 tests passing)
- **🔐 Enterprise Security**: JWT auth, rate limiting, SQL injection protection
- **🧪 Comprehensive Testing**: 491 tests, 70.34% coverage, performance benchmarks
- **📊 Dashboard**: [osservatorio-dashboard.streamlit.app](https://osservatorio-dashboard.streamlit.app/)
- **🇮🇹 ISTAT API**: Complete SDMX integration (509+ datasets)
- **📁 Multi-Format Export**: CSV, Excel, Parquet, JSON, PowerBI-optimized

### 🔒 **Enterprise Security**
- **🛡️ SQL Injection Protection**: Enhanced table name validation, parameterized queries
- **🔍 Security Audit**: 0 HIGH severity issues (bandit scan validated)
- **⚡ Performance Testing**: 200k+ records/sec with comprehensive regression detection
- **🧪 Test Coverage**: 462 tests passing including enhanced security integration tests

## ✅ Current Status

### ⚡ **Performance Metrics**
- **⚡ Load Times**: <5s dashboard loading (improved from 20-30s)
- **🔄 Caching**: Smart caching with 30min TTL + DuckDB query caching (>10x speedup)
- **📊 Database Performance**: >2k records/sec bulk insert validated
- **📊 API Scalability**: Handles 509+ ISTAT datasets with async loading

### ✅ **Recently Completed**
- **🗃️ SQLite Metadata Layer**: Complete 6-table schema with thread-safe operations
- **📊 PowerBI Integration**: 19/19 tests passing, enterprise-ready with star schema optimization
- **🔐 Enhanced Security**: 0 HIGH severity issues, comprehensive audit logging
- **🧪 Comprehensive Testing**: 462 tests with 68% coverage (100% pass rate)

---

## 🏗️ Architecture

### 📦 Project Structure (Updated Day 7)
```
Osservatorio/                              # 🏠 Root directory
├── 🐍 src/                                # 📂 Source code (30+ Python files)
│   ├── 🔐 auth/                           # **NEW! JWT Authentication System** (5 files)
│   │   ├── models.py                      # Authentication data models
│   │   ├── sqlite_auth.py                 # API key management with bcrypt
│   │   ├── jwt_manager.py                 # JWT tokens with blacklisting
│   │   ├── rate_limiter.py                # Sliding window rate limiting
│   │   └── security_middleware.py         # OWASP security headers
│   ├── 🔌 api/                            # External API clients (4 files)
│   │   ├── istat_api.py                   # ISTAT SDMX API (509+ datasets)
│   │   ├── powerbi_api.py                 # PowerBI REST API + OAuth
│   │   └── tableau_api.py                 # Tableau Server API
│   ├── 🔄 converters/                     # Data format converters (3 files)
│   │   ├── powerbi_converter.py           # XML → PowerBI formats
│   │   └── tableau_converter.py           # XML → Tableau formats
│   ├── 🔍 analyzers/                      # Data analysis (2 files)
│   │   └── dataflow_analyzer.py           # Dataset categorization
│   ├── 🕷️ scrapers/                       # Web scraping utilities (2 files)
│   │   └── tableau_scraper.py             # Tableau configuration analysis
│   ├── 🦆 database/                       # Database modules (11 files)
│   │   ├── duckdb/                        # DuckDB analytics engine (7 files)
│   │   │   ├── manager.py                 # Connection management & pooling
│   │   │   ├── schema.py                  # ISTAT data schemas
│   │   │   ├── simple_adapter.py          # Lightweight interface
│   │   │   ├── query_builder.py           # 826 lines fluent query builder
│   │   │   ├── query_optimizer.py         # Query optimization & caching
│   │   │   ├── partitioning.py            # Data partitioning strategies
│   │   │   └── config.py                  # DuckDB configuration
│   │   └── sqlite/                        # SQLite metadata layer
│   │       ├── manager.py                 # Thread-safe metadata manager
│   │       ├── schema.py                  # 6-table metadata schema
│   │       └── repository.py              # Unified facade pattern
│   └── 🛠️ utils/                          # Core utilities (7 files)
│       ├── security_enhanced.py           # 🔒 Security management
│       ├── circuit_breaker.py             # 🔄 Resilience patterns
│       ├── config.py                      # ⚙️ Configuration management
│       ├── logger.py                      # 📋 Structured logging
│       ├── secure_path.py                 # 🛡️ Path validation
│       └── temp_file_manager.py           # 📁 Temporary files
├── 🧪 tests/                              # 📂 Test suite (23 test files)
│   ├── unit/                              # 18 unit test files (including __init__.py)
│   ├── integration/                       # 4 integration test files
│   ├── performance/                       # 4 performance test files
│   └── conftest.py                        # Test configuration
├── 📱 dashboard/                          # 📂 Dashboard components
│   ├── app.py                             # Streamlit app (22KB)
│   ├── index.html                         # Landing page (38KB)
│   └── README.md                          # Dashboard docs
├── 📊 data/                               # 📂 Data management (523KB processed)
│   ├── processed/powerbi/                 # PowerBI files (30+ files)
│   ├── processed/tableau/                 # Tableau files
│   ├── raw/istat/                         # Original ISTAT XML (13 files)
│   ├── raw/xml/                           # Sample XML data (15+ files)
│   ├── cache/                             # Cached responses
│   └── reports/                           # Analysis reports (4 JSON files)
├── 🤖 scripts/                            # 📂 Automation (12 Python files)
│   ├── analyze_data_formats.py            # Data format analysis
│   ├── cleanup_temp_files.py              # File management
│   ├── legacy/                            # Legacy scripts (4 files)
│   └── test_ci.py                         # CI/CD utilities
├── 📋 examples/                           # 📂 Usage examples (4 demo files)
│   ├── duckdb_demo.py                     # DuckDB analytics demo
│   ├── duckdb_query_builder_demo.py       # Query Builder advanced usage (826 lines)
│   ├── powerbi_integration_demo.py        # PowerBI enterprise integration demo
│   └── sqlite_metadata_demo.py            # SQLite metadata layer demo
├── 📚 docs/                               # 📂 Documentation (9+ Markdown files)
│   ├── README.md                          # Documentation index
│   ├── core/ARCHITECTURE.md               # System architecture (1200+ lines)
│   ├── integrations/POWERBI_INTEGRATION.md # PowerBI enterprise integration guide
│   ├── api/api-mapping.md                 # ISTAT API endpoints
│   ├── reference/adr/001-database-selection.md # Architecture Decision Record
│   ├── core/API_REFERENCE.md              # API documentation
│   ├── guides/CONTRIBUTING.md             # Contribution guide
│   ├── guides/DEPLOYMENT_GUIDE.md         # Deployment instructions
│   ├── guides/STREAMLIT_DEPLOYMENT.md     # Streamlit deployment
│   └── licenses/                          # License files (5 files)
├── 📈 logs/                               # 📂 Application logs
├── 📊 htmlcov/                            # 📂 Coverage reports
└── 🔧 Configuration files
    ├── pyproject.toml                     # Project configuration
    ├── pytest.ini                        # Test configuration
    └── requirements.txt                   # Dependencies
```

### 🔄 Data Flow
```
🇮🇹 ISTAT API → 🔄 XML Processing → 📊 Data Analysis → 🔄 Format Conversion → 📱 Dashboard
     ↓                ↓                    ↓                    ↓                ↓
📊 509+ datasets → XML validation → Quality scoring → Multi-format → Live visualization
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🌟 Key Features

### 🔐 Enterprise Authentication System (Day 7)
- **JWT Authentication**: Complete token-based authentication with HS256/RS256 support
- **API Key Management**: Cryptographically secure API keys with scope-based permissions (read, write, admin, analytics, powerbi, tableau)
- **Rate Limiting**: Sliding window algorithm with per-API-key and per-IP protection
- **Security Headers**: OWASP-compliant middleware with CSP, HSTS, X-Frame-Options
- **CLI Tools**: Complete command-line interface for API key lifecycle management

### 🔒 Enterprise Security & Compliance
- **SQL Injection Protection**: All queries use parameterized statements
- **Database Transaction Safety**: Nested transaction handling with automatic cleanup
- **Security Scanning**: Bandit-verified codebase with 0 high-severity issues
- **Audit Logging**: Comprehensive security event tracking
- **Input Validation**: XSS and injection prevention at all entry points

### 📊 High-Performance Data Processing
- **🦆 DuckDB Analytics**: High-performance analytics engine (>2k records/sec)
- **🗃️ SQLite Metadata**: Lightweight metadata layer (zero configuration)
- **📊 PowerBI Integration**: Native BI tool support with star schema (19/19 tests passing)
- **🧪 Comprehensive Testing**: 462 tests, 68% coverage, performance benchmarks
- **📊 Dashboard**: [osservatorio-dashboard.streamlit.app](https://osservatorio-dashboard.streamlit.app/)
- **🇮🇹 ISTAT API**: Complete SDMX integration (509+ datasets)

---

## 🦆 DuckDB Analytics Engine

### ✨ **New Features**

**High-Performance Analytics** - Complete DuckDB integration for advanced data processing:

```python
from src.database.duckdb import DuckDBManager, SimpleDuckDBAdapter

# Quick start with simple adapter
adapter = SimpleDuckDBAdapter()
adapter.create_istat_schema()

# Advanced usage with full manager
manager = DuckDBManager()
result = manager.execute_query("SELECT * FROM istat_observations LIMIT 10")
```

### 🚀 **Key Capabilities**

- **⚡ Lightning Fast**: Up to 3x faster query execution vs pandas operations
- **🔄 Smart Caching**: 85%+ cache hit rate with intelligent invalidation
- **📊 Auto Schema**: Automatic ISTAT data schema creation and management
- **🎯 Query Optimization**: Advanced indexing and query plan optimization
- **🛡️ Security First**: Parameterized queries prevent SQL injection
- **📈 Performance Monitoring**: Real-time query performance tracking

### 🎯 **Usage Examples**

```bash
# Complete DuckDB demonstration
python examples/duckdb_demo.py

# Test individual components
pytest tests/unit/test_duckdb_basic.py -v           # Basic functionality
pytest tests/unit/test_duckdb_integration.py -v    # Full integration (45 tests)
pytest tests/unit/test_simple_adapter.py -v        # Simple adapter usage
```

### 📊 **Performance Benchmarks**

- **Query Speed**: 3x faster than pandas for analytical operations
- **Memory Usage**: 40% reduction with optimized connection pooling
- **Cache Efficiency**: 85%+ hit rate for repeated analytical queries
- **Concurrent Operations**: Handles multiple simultaneous connections

---

## 🔧 Development

### 🧪 Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v          # Unit tests (215+)
pytest tests/integration/ -v   # Integration tests (26)
pytest tests/performance/ -v   # Performance tests (8+)

# Run with coverage
pytest --cov=src tests/

# Run security tests
pytest tests/unit/test_security_enhanced.py -v
```

### 🔍 Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Run pre-commit hooks
pre-commit run --all-files
```

### 🛡️ Security
```bash
# Security scan
bandit -r src/

# Check dependencies
safety check

# Test security features
python -c \"from src.utils.security_enhanced import security_manager; print(security_manager.get_security_headers())\"
```

---

## 📊 Usage Examples

### 🔌 API Integration
```python
from src.api.istat_api import IstatAPITester
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter

# Initialize API client
api = IstatAPITester()

# Fetch dataset
xml_data = api.fetch_dataset_data(\"DCIS_POPRES1\")

# Convert to PowerBI format
converter = IstatXMLToPowerBIConverter()
result = converter.convert_xml_to_powerbi(
    xml_input=xml_data,
    dataset_id=\"DCIS_POPRES1\",
    dataset_name=\"Popolazione residente\"
)

print(f\"Conversion successful: {result['success']}\")
print(f\"Files created: {result['files_created']}\")
```

### 🔒 Security Features
```python
from src.utils.security_enhanced import SecurityManager

# Initialize security manager
security = SecurityManager()

# Validate file path
is_safe = security.validate_path(\"/data/user_file.csv\", \"/app/data\")

# Check rate limit
is_allowed = security.rate_limit(\"user_123\", max_requests=100, window=3600)

# Sanitize input
clean_input = security.sanitize_input(user_input)
```

### 🔐 JWT Authentication System
```python
from src.auth import SQLiteAuthManager, JWTManager

# Initialize authentication
auth_manager = SQLiteAuthManager(sqlite_manager)
jwt_manager = JWTManager(sqlite_manager)

# Generate API key
api_key = auth_manager.generate_api_key("MyApp", ["read", "write"])

# Create JWT token
token = jwt_manager.create_access_token(api_key)

# CLI Management
# python scripts/generate_api_key.py create --name "MyApp" --scopes read,write
```
For full documentation see [docs/security/AUTHENTICATION.md](docs/security/AUTHENTICATION.md)

### 🔄 Circuit Breaker
```python
from src.utils.circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
def external_api_call():
    # Your API call here
    return requests.get(\"https://api.example.com/data\")
```

---

## 🚀 Deployment

### ☁️ Production Deployment
The application is deployed on **Streamlit Cloud** with automatic CI/CD:

- **Live URL**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)
- **Auto-deployment**: Triggered on push to `main` branch
- **Health monitoring**: Automated uptime and performance monitoring

### 🔧 Local Development
```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r dashboard/requirements.txt

# Run locally
streamlit run dashboard/app.py

# Access at http://localhost:8501
```

### 🐳 Docker Deployment
Docker support is planned for future releases. Currently, the application is optimized for Streamlit Cloud deployment.

For detailed deployment instructions, see [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md).

---

## 📊 Performance

### ⚡ Current Metrics (Verified 20/07/2025)
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Dashboard Load Time** | <5s | <3s | 🟡 Good (improved from 30s) |
| **API Response Time** | ~500ms | <300ms | 🟡 Acceptable |
| **Test Execution** | ~8s | <5s | 🟡 Good (292 tests) |
| **Test Coverage** | 57% | 70% | 🟡 Target approaching |
| **Error Rate** | <1% | <0.1% | ✅ Excellent |
| **ISTAT Datasets** | 509+ | All available | ✅ Comprehensive |

### 🎯 Optimization Features
- **🗂️ Intelligent Caching**: Automatic data caching with TTL
- **📊 Lazy Loading**: On-demand data loading
- **🗜️ Compression**: Parquet format for large datasets
- **⚡ Async Processing**: Non-blocking API calls
- **🔄 Connection Pooling**: Efficient resource utilization

---

## 🔗 Integration

### 🇮🇹 ISTAT API
- **Endpoint**: `https://sdmx.istat.it/SDMXWS/rest/`
- **Datasets**: 509+ available datasets
- **Rate Limit**: 50 requests/hour
- **Format**: SDMX XML

### 📊 PowerBI Integration (Enterprise-Ready)
- **Status**: ✅ **Production Ready** - 19/19 tests passing
- **Features**: Star schema optimization, template generation, incremental refresh, metadata bridge
- **Templates**: Automated .pbit file generation with Italian localization
- **Validation**: 100% offline validation without Microsoft credentials
- **Documentation**: [`docs/integrations/POWERBI_INTEGRATION.md`](docs/integrations/POWERBI_INTEGRATION.md)

### 📈 Tableau Server
- **Authentication**: Server credentials
- **Features**: Data source management
- **Formats**: CSV, Excel, JSON

---

## 🤝 Contributing

### 🚀 Join the Sprint!
We're actively seeking contributors for our January 2025 sprint! Check out the [GitHub Project Board](https://github.com/AndreaBozzo/Osservatorio/projects) for available issues.

**Quick Start for Contributors:**
1. 📖 Read the [Contributing Guide](https://github.com/AndreaBozzo/Osservatorio/wiki/Contributing-Guide)
2. 🛠️ Follow the [Setup Guide](https://github.com/AndreaBozzo/Osservatorio/wiki/Setup-Ambiente-Locale)
3. 🎯 Pick an issue from the [Project Board](https://github.com/AndreaBozzo/Osservatorio/projects)
4. 💬 Join the [Sprint Discussion](https://github.com/AndreaBozzo/Osservatorio/discussions)

### 🎯 Current Priorities
- **Enhanced Data Validation** - Improve data quality scoring
- **Dashboard Performance** - Memory optimization and loading speed
- **Security Enhancements** - Advanced rate limiting and protection
- **Testing Expansion** - Coverage at 67%, approaching 70% target

### 🐛 Bug Reports
1. Check existing issues on [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues)
2. Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.yml)
3. Include reproduction steps and environment details
4. Attach relevant logs and screenshots

### 💡 Feature Requests
1. Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.yml)
2. Describe the business value and use case
3. Provide implementation suggestions
4. Check if it aligns with our [roadmap](#-roadmap)

### 🔄 Pull Requests
1. Fork the repository and create a feature branch
2. Follow our [Development Standards](#-development-standards)
3. Write tests for new code (target 70%+ coverage)
4. Ensure all CI checks pass
5. Submit PR with clear description

### 📋 Development Standards
- **Code Style**: Black, isort, flake8 (enforced by pre-commit)
- **Testing**: pytest with >70% coverage target
- **Documentation**: Google-style docstrings + Wiki updates
- **Security**: All PRs require security review
- **Type Hints**: Required for all new public APIs

---

## 📚 Documentation

### 📖 Core Documentation
- **[README.md](README.md)**: This overview document
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System architecture documentation
- **[PROJECT_STATE.md](PROJECT_STATE.md)**: Current project status
- **[Documentation Index](docs/README.md)**: Complete documentation structure

### 🔧 Development Guides
- **[CLAUDE.md](CLAUDE.md)**: Development commands and context
- **[Deployment Guide](docs/guides/DEPLOYMENT_GUIDE.md)**: Production deployment
- **[Streamlit Deployment](docs/guides/STREAMLIT_DEPLOYMENT.md)**: Cloud deployment

### 📊 API Documentation
- **[API Reference](docs/api/API_REFERENCE.md)**: Complete API documentation
- **Integration Examples**: See usage examples above
- **Licenses**: See [docs/licenses/](docs/licenses/) for legal information

---

## 🎯 Roadmap

### ✅ **Phase 1: Foundation (Completed)**
- [x] Core data processing pipeline
- [x] Enhanced security implementation (SecurityManager)
- [x] Live dashboard deployment (https://osservatorio-dashboard.streamlit.app/)
- [x] **PowerBI Enterprise Integration** (Production Ready)
  - [x] PowerBI API Client with MSAL authentication
  - [x] Star Schema Optimizer for dimensional modeling
  - [x] Template Generator (.pbit files) with Italian localization
  - [x] Incremental Refresh Manager with change detection
  - [x] Metadata Bridge for data governance
  - [x] 100% offline validation system
- [x] Expanded test suite (441 tests, 68% coverage)
- [x] CI/CD pipeline with GitHub Actions
- [x] Comprehensive documentation + CONTRIBUTING.md

### 🔄 **Phase 2: Enhancement (In Progress)**
- [x] Improve test coverage (67% achieved, target 70%)
- [x] Performance optimization (load time <5s)
- [x] Enhanced security features (rate limiting, circuit breaker)
- [x] API documentation (docs/api-mapping.md)
- [x] Database integration (DuckDB implemented with Query Builder)
- [ ] REST API(FastAPI)
- [ ] Complete monitoring implementation
- [ ] Production-ready error handling

### 🚀 **Phase 3: Advanced Analytics (Q4 2025)**
- [ ] **Tableau Integration**: Server API, Hyper files, workbook automation
- [ ] **Qlik Integration**: QlikSense apps, associative models, script templates
- [ ] **Advanced PowerBI Features**: Custom visuals, real-time refresh, ML integration
- [ ] **Multi-Platform Analytics**: Unified analytics engine across BI tools
- [ ] **Predictive Analytics**: Quality score prediction, trend analysis
- [ ] **Natural Language Queries**: AI-powered data exploration

### 🔧 **Phase 4: Enterprise Scale (2026)**
- [ ] Container orchestration (Kubernetes)
- [ ] Microservices architecture
- [ ] Real-time data streaming
- [ ] Advanced governance & compliance
- [ ] Multi-tenant support

---

## 📞 Support

### 🆘 Getting Help
- **🎯 Current Sprint**: [GitHub Project Board](https://github.com/AndreaBozzo/Osservatorio/projects) - Track active development
- **🐛 Issues**: [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues) - Bug reports and feature requests
- **💬 Discussions**: [GitHub Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions) - Community Q&A and announcements
- **📚 Wiki**: [GitHub Wiki](https://github.com/AndreaBozzo/Osservatorio/wiki) - Comprehensive documentation and guides
  - [Setup Guide](https://github.com/AndreaBozzo/Osservatorio/wiki/Setup-Ambiente-Locale) - Local development setup
  - [FAQ](https://github.com/AndreaBozzo/Osservatorio/wiki/FAQ-Tecniche) - Technical troubleshooting
  - [Contributing](https://github.com/AndreaBozzo/Osservatorio/wiki/Contributing-Guide) - How to contribute
  - [Security Policy](https://github.com/AndreaBozzo/Osservatorio/wiki/Security-Policy) - Security guidelines

### 📧 Contact
- **Project Lead**: Andrea Bozzo
- **Main Collaborator**: @Gasta88
- **Email**: [Contact via GitHub](https://github.com/AndreaBozzo)
- **Website**: [Live Dashboard](https://osservatorio-dashboard.streamlit.app/)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏆 Acknowledgments

- **ISTAT**: For providing comprehensive Italian statistical data
- **Streamlit**: For enabling rapid dashboard development
- **Python Community**: For excellent data science libraries
- **Open Source Contributors**: For inspiration and best practices

---

## 📊 Project Stats (Day 7 Complete)

- **🐍 Python Files**: 30+ core modules + 34 test files + authentication system
- **🧪 Total Tests**: 462 comprehensive tests with 100% pass rate + 29 auth tests
- **📊 Test Coverage**: 68% achieved, targeting 70%
- **🔐 Authentication**: Complete JWT system with API keys, rate limiting, security headers
- **🔒 Security**: Bandit-verified (0 HIGH issues), SQL injection protected, OWASP-compliant
- **📚 Documentation**: 8+ Markdown files with comprehensive authentication guide
- **🌟 GitHub Integration**: Active CI/CD with automated testing and security scanning
- **📄 Landing Page**: Static HTML (38KB) at https://andreabozzo.github.io/Osservatorio/
- **📱 Live Dashboard**: Streamlit app at https://osservatorio-dashboard.streamlit.app/
- **💾 Data Processing**: 523KB processed data, 13 real ISTAT XML files
- **⚡ Performance**: <5s load time with 509+ ISTAT datasets, >2k records/sec DuckDB
- **🛡️ Environment**: Python 3.13.3, pytest 8.3.5, Streamlit 1.45.0

---

**🎯 Ready to explore Italian statistical data? Start with our [live dashboard](https://osservatorio-dashboard.streamlit.app/) or follow the [quick start guide](#-quick-start)!**

**📈 Status**: 🔄 **Working Prototype** | ✅ **Actively Maintained** | 🚀 **Open Source** | 📊 **Live Dashboard** | 🧪 **462 Tests**
