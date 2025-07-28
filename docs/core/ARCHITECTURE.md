# 🏗️ Osservatorio - Architecture Documentation

> **Comprehensive architectural documentation for the Osservatorio ISTAT data processing platform**
> **Version**: 10.3.0
> **Date**: July 28, 2025
> **Status**: Clean Architecture - Issues #59, #62 & #65 Complete, Prepared for Issue #66

---

## 📋 Table of Contents

1. [System Overview](#-system-overview)
2. [Architecture Principles](#-architecture-principles)
3. [Component Architecture](#-component-architecture)
4. [JWT Authentication Architecture](#-jwt-authentication-architecture) **NEW!**
5. [Data Flow Architecture](#-data-flow-architecture)
6. [Security Architecture](#-security-architecture)
7. [Testing Architecture](#-testing-architecture)
8. [Deployment Architecture](#-deployment-architecture)
9. [Performance Architecture](#-performance-architecture)
10. [PowerBI Integration Architecture](#-powerbi-integration-architecture)
11. [Advanced Analytics Architecture](#-advanced-analytics-architecture)
12. [Integration Architecture](#-integration-architecture)
13. [Future Architecture](#-future-architecture)

---

## 🎯 System Overview

**Osservatorio** is a comprehensive data processing platform designed to extract, transform, and visualize Italian statistical data from ISTAT (Istituto Nazionale di Statistica) sources. The system follows a **layered architecture** with **security-first design** principles.

### 🏢 Business Context
- **Primary Goal**: Democratize access to Italian statistical data
- **Target Users**: Data analysts, researchers, government officials, businesses
- **Data Source**: ISTAT SDMX API (509+ datasets)
- **Output Formats**: Interactive dashboards, CSV, Excel, JSON, Parquet

### 🔧 Technical Context
- **Language**: Python 3.13.3
- **Architecture Pattern**: Layered + Component-based with DuckDB Analytics Engine
- **Deployment**: Cloud-native (Streamlit Cloud)
- **Security**: Enterprise-grade security implementation with SQL injection prevention

---

## 🎨 Architecture Principles

### 1. **Security First**
- All components implement security by default
- Input validation and sanitization at every layer
- Rate limiting and circuit breakers for external calls
- Comprehensive logging and monitoring

### 2. **Modularity**
- Loose coupling between components
- High cohesion within components
- Clear separation of concerns
- Reusable and testable modules

### 3. **Reliability**
- Circuit breaker pattern for external dependencies
- Graceful degradation and fallback mechanisms
- Comprehensive error handling
- Extensive test coverage (491 tests including 45 DuckDB integration tests, 70.34% coverage)

### 4. **Performance**
- Efficient data processing pipelines with DuckDB analytics engine
- Caching strategies for frequently accessed data (85%+ hit rate)
- Optimized file formats (Parquet for large datasets)
- Asynchronous processing where applicable
- 3x query performance improvement with intelligent caching

### 5. **Maintainability**
- Clean code principles
- Comprehensive documentation
- Consistent coding standards
- Automated testing and deployment

---

## 🧩 Component Architecture

### 🏗️ System Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 Presentation Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Dashboard     │  │   Web Assets    │  │   Static Files  │ │
│  │   (Streamlit)   │  │   (HTML/CSS)    │  │   (Config)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔧 Business Logic Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Analyzers     │  │ 🏗️ Converters    │  │   Scrapers      │ │
│  │   (Analysis)    │  │ (BaseConverter)  │  │   (Extract)     │ │
│  │                 │  │ Factory Pattern  │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔌 Service Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   ISTAT API     │  │   PowerBI API   │  │   Tableau API   │ │
│  │   (Data Source) │  │   (BI Platform) │  │   (BI Platform) │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│            🗃️ Hybrid Storage Layer (ADR-002) + Issue #59       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   🗃️ SQLite      │  │   🦆 DuckDB      │  │   🔄 Unified    │ │
│  │   (Metadata)    │  │   (Analytics)   │  │   Repository    │ │
│  │                 │  │                 │  │   (Facade)      │ │
│  │  • User Prefs   │  │  • Time Series  │  │  • Smart Route  │ │
│  │  • API Keys     │  │  • Aggregations │  │  • Cache Layer  │ │
│  │  • Audit Logs   │  │  • Performance  │  │  • Transactions │ │
│  │  • **Datasets** │  │  • Query Build  │  │  • **Migration**│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🛠️ Utility Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Security      │  │   Configuration │  │   Logging       │ │
│  │   (Protection)  │  │   (Settings)    │  │   (Monitoring)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 📦 Component Details

#### 🌐 Presentation Layer
- **Dashboard (`dashboard/app.py`)**
  - Streamlit-based interactive web interface
  - Real-time data visualization with Plotly
  - Responsive design for multiple devices
  - User-friendly filtering and navigation

- **Web Assets (`dashboard/web/`)**
  - Static HTML/CSS/JS files
  - Custom styling and branding
  - Streamlit configuration files

#### 🔧 Business Logic Layer
- **Analyzers (`src/analyzers/`)**
  - **DataflowAnalyzer**: Categorizes ISTAT datasets
  - **Priority Scoring**: Assigns importance scores
  - **Data Quality**: Validates data completeness

- **Converters (`src/converters/`) - REFACTORED Issue #62**
  - **BaseIstatConverter**: **NEW!** Abstract base class with shared XML parsing logic (342 lines)
  - **ConverterFactory**: **NEW!** Factory pattern for centralized converter instantiation
  - **PowerBIConverter**: XML → PowerBI formats (now inherits from BaseIstatConverter)
  - **TableauConverter**: XML → Tableau formats (now inherits from BaseIstatConverter)
  - **Code Reduction**: ~500 lines eliminated (~23% reduction in converter modules)
  - **Multi-format Export**: CSV, Excel, JSON, Parquet with unified validation


#### 🔌 Service Layer
- **ISTAT API Client (`src/api/istat_api.py`) - EVOLUTION TARGET**
  - **Current**: Exploration tool with basic SDMX API access
  - **Future Vision (Issue #66)**: Production-ready client with enterprise patterns
    - Connection pooling for optimal resource management
    - Circuit breaker pattern for resilience
    - Repository integration for unified data access
    - Async operations for improved performance
    - Comprehensive testing and monitoring
  - **509+ Dataset Access**: Complete ISTAT dataset catalog support

- **PowerBI API (`src/api/powerbi_api.py`)**
  - Microsoft PowerBI Service integration
  - Workspace and dataset management
  - OAuth 2.0 authentication

- **Tableau API (`src/api/tableau_api.py`)**
  - Tableau Server integration
  - Data source management
  - RESTful API communication

#### 🗃️ Hybrid Storage Layer (ADR-002)
- **SQLite Metadata Layer (`src/database/sqlite/`) - UPDATED Issue #59**
  - **SQLiteMetadataManager**: Thread-safe metadata management with connection pooling
  - **Schema Management**: 6-table schema for user preferences, API credentials, audit logs
  - **Dataset Configuration**: **NEW!** `dataset_config.py` - Centralized dataset management with SQLite-first, JSON-fallback
  - **Migration System**: **NEW!** JSON to SQLite migration with zero-downtime rollback capabilities
  - **Encryption Support**: Fernet encryption for sensitive data storage
  - **Audit Logging**: Comprehensive operation tracking and user activity monitoring
  - **Repository Pattern**: Unified interface combining SQLite and DuckDB operations

- **DuckDB Analytics Engine (`src/database/duckdb/`)**
  - **DuckDBManager**: High-performance connection management with security validation
  - **SQL Injection Protection**: Enhanced table name validation and parameterized queries
  - **Type Safety**: Implementation with security best practices (bandit scan: 0 HIGH issues)
  - **Performance Monitoring**: Real-time query optimization and statistics

- **Query Builder (`src/database/duckdb/query_builder.py`)**
  - **Fluent Interface**: 826 lines of intuitive query building with method chaining
  - **Intelligent Caching**: Query result caching with >10x speedup validation
  - **ISTAT Patterns**: Specialized methods for time series, territory comparison, category trends
  - **Security**: Parameterized queries with SQL injection protection
  - **Performance**: Cache hit rate optimization and TTL management

- **Query Optimizer (`src/database/duckdb/query_optimizer.py`)**
  - **Smart Caching**: Query result caching with TTL management
  - **Index Management**: Advanced indexing strategies for ISTAT data patterns
  - **Performance Analytics**: Territory comparison, time series, and trend analysis
  - **Statistical Operations**: Built-in analytics functions for ISTAT datasets

- **Data Partitioning (`src/database/duckdb/partitioning.py`)**
  - **Partitioning Strategies**: Year-based, territory-based, and hybrid partitioning
  - **Query Pruning**: Automatic partition pruning for optimal performance
  - **Scalability**: Validated performance >2k records/sec with linear scaling
  - **Memory Optimization**: Efficient storage patterns for analytical workloads

#### 🛠️ Utility Layer
- **Security (`src/utils/security_enhanced.py`)**
  - **SecurityManager**: Centralized security
  - **Rate Limiting**: API protection
  - **Path Validation**: Directory traversal prevention
  - **Input Sanitization**: XSS/injection protection

- **Configuration (`src/utils/config.py`)**
  - Environment variable management
  - Application settings
  - Feature flags and toggles

- **Logging (`src/utils/logger.py`)**
  - Structured logging with Loguru
  - Log levels and filtering
  - Performance monitoring

---

## 🔐 JWT Authentication Architecture

**Enterprise-grade authentication system integrated with SQLite backend (Day 7)**

### 🏗️ Authentication System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    🔐 Authentication Layer (Day 7)              │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  🔑 API Keys    │  │  🎫 JWT Tokens  │  │  ⚡ Rate Limit  │ │
│  │                 │  │                 │  │                 │ │
│  │ • Bcrypt Hash   │  │ • HS256/RS256   │  │ • Sliding Window│ │
│  │ • Scope Perms   │  │ • Blacklisting  │  │ • Per-API/IP    │ │
│  │ • Expiration    │  │ • Refresh Token │  │ • Configurable  │ │
│  │ • CLI Tools     │  │ • Custom Claims │  │ • Violation Log │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              🛡️ Security Headers Middleware                     │
│                                                                 │
│ • CSP (Content Security Policy)                                │
│ • HSTS (HTTP Strict Transport Security)                        │
│ • X-Frame-Options (Clickjacking Protection)                    │
│ • X-Content-Type-Options (MIME Sniffing Prevention)            │
│ • CORS Configuration with Secure Defaults                      │
│ • Authentication Middleware for Request Processing             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🗃️ SQLite Authentication Storage             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  API Credentials│  │  Rate Limits    │  │  Token Blacklist│ │
│  │  • Hashed Keys  │  │  • Time Windows │  │  • Revoked JWT  │ │
│  │  • Scopes       │  │  • Violation Log│  │  • Cleanup Jobs │ │
│  │  • Metadata     │  │  • Statistics   │  │  • Audit Trail  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🔧 Authentication Components

#### 🔑 **SQLite API Key Management** (`src/auth/sqlite_auth.py`)
- **Cryptographic Security**: bcrypt hashing with cost factor 12
- **Scope-Based Permissions**: Fine-grained access control (read, write, admin, analytics, powerbi, tableau)
- **Lifecycle Management**: Create, list, revoke, test API keys
- **Expiration Handling**: Optional time-based expiration with automatic cleanup
- **Usage Tracking**: Request counting and last-used timestamps

#### 🎫 **JWT Token System** (`src/auth/jwt_manager.py`)
- **Algorithm Support**: Both HS256 (HMAC) and RS256 (RSA)
- **Token Types**: Access tokens with configurable expiration
- **Token Blacklisting**: Secure logout with revoked token tracking
- **Custom Claims**: API key metadata embedded in JWT payload
- **Refresh Patterns**: Support for token refresh workflows

#### ⚡ **Rate Limiting** (`src/auth/rate_limiter.py`)
- **Sliding Window Algorithm**: Time-based request counting
- **Multi-Layer Protection**: Per-API-key AND per-IP limits
- **Configurable Windows**: Minute, hour, and day time windows
- **Burst Allowance**: Short-term spike tolerance
- **Violation Logging**: Complete audit trail of limit breaches

#### 🛡️ **Security Headers Middleware** (`src/auth/security_middleware.py`)
- **OWASP Compliance**: Industry-standard security headers
- **Request Authentication**: Automatic API key and JWT validation
- **CORS Management**: Configurable cross-origin resource sharing
- **Security Reporting**: Comprehensive security status reporting

### 🛠️ CLI Management Tools

#### **API Key Management CLI** (`scripts/generate_api_key.py`)
```bash
# Create API key with specific scopes
python scripts/generate_api_key.py create --name "Analytics App" --scopes analytics,read

# List all active API keys
python scripts/generate_api_key.py list

# Revoke compromised key
python scripts/generate_api_key.py revoke --id 123 --reason "Security breach"

# Test key validity
python scripts/generate_api_key.py test --key osv_abc123...

# View usage statistics
python scripts/generate_api_key.py stats

# Cleanup expired tokens
python scripts/generate_api_key.py cleanup
```

### 🔒 Security Features

#### **Database Security**
- **Transaction Safety**: Nested transaction handling with automatic cleanup
- **SQL Injection Protection**: All queries use parameterized statements
- **Connection Management**: Proper resource cleanup and Windows compatibility
- **Audit Logging**: Complete security event tracking

#### **Authentication Security**
- **bcrypt Password Hashing**: Industry-standard key protection
- **Scope Validation**: Strict permission checking
- **Token Validation**: JWT signature verification and expiration checking
- **Rate Limit Enforcement**: Automatic protection against abuse

### 🧪 Testing & Validation

#### **Comprehensive Test Suite** (`tests/unit/test_auth_system.py`)
- **29 Test Methods**: Complete coverage of authentication functionality
- **Integration Testing**: End-to-end authentication flow validation
- **Security Testing**: Attack scenario and edge case testing
- **Performance Testing**: Rate limiting and concurrent access testing

#### **Security Validation**
- **Bandit Security Scan**: 0 high-severity issues verified
- **SQL Injection Testing**: All queries parameterized and tested
- **Authentication Flow Testing**: Complete token lifecycle validation
- **Cross-Platform Testing**: Windows and Linux compatibility verified

---

## 🔄 Data Flow Architecture

### 📊 End-to-End Data Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   🌐 ISTAT   │    │   📥 Fetch   │    │   🔄 Parse   │    │   📊 Analyze │
│   API        │───▶│   XML Data   │───▶│   & Validate │───▶│   & Category │
│   (Source)   │    │   (Raw)      │    │   (Process)  │    │   (Enrich)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   📱 Display │    │   🗃️ Store   │    │   🔄 Convert │    │   ✅ Validate│
│   Dashboard  │◀───│   Hybrid     │◀───│   Multi-     │◀───│   Quality   │
│   (Consume)  │    │   (SQLite+   │    │   Format     │    │   (Check)   │
│             │    │   DuckDB)    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   🔄 Unified        │
              │   Repository        │
              │   • Smart Routing   │
              │   • Metadata → SQLite│
              │   • Analytics → DuckDB│
              └─────────────────────┘
```

### 🔍 Detailed Data Flow

#### 1. **Data Ingestion**
```python
# ISTAT API Client
istat_client = IstatAPITester()
xml_data = istat_client.fetch_dataset("DCIS_POPRES1")
```

#### 2. **Data Processing**
```python
# XML Parsing and Validation
converter = IstatXMLToPowerBIConverter()
result = converter.convert_xml_to_powerbi(
    xml_input=xml_data,
    dataset_id="DCIS_POPRES1",
    dataset_name="Popolazione residente"
)
```

#### 3. **Data Enrichment**
```python
# Automatic categorization
category, priority = converter._categorize_dataset(
    "DCIS_POPRES1",
    "Popolazione residente"
)
# Output: category="popolazione", priority=10
```

#### 4. **Quality Validation**
```python
# Data quality assessment
quality_report = converter._validate_data_quality(dataframe)
# Output: completeness_score, data_quality_score
```

#### 5. **Multi-format Export**
```python
# Generate multiple formats
formats = converter._generate_powerbi_formats(dataframe, dataset_info)
# Output: CSV, Excel, JSON, Parquet files
```

#### 6. **Metadata Registration (SQLite)**
```python
# Register dataset metadata in SQLite
from src.database.sqlite.repository import UnifiedDataRepository

repo = UnifiedDataRepository()
repo.register_dataset_complete(
    dataset_id="DCIS_POPRES1",
    name="Popolazione residente",
    category="popolazione",
    analytics_data=dataframe  # Routed to DuckDB
)
```

#### 7. **Dashboard Integration**
```python
# Real-time visualization with hybrid data access
dashboard.load_data(category="popolazione")
dashboard.render_visualization(data, chart_type="trend")
```

---

## 🔒 Security Architecture

### 🛡️ Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 Network Security                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   HTTPS         │  │   Security      │  │   CORS          │ │
│  │   Enforcement   │  │   Headers       │  │   Configuration │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔐 Application Security                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Input         │  │   Rate          │  │   Path          │ │
│  │   Sanitization  │  │   Limiting      │  │   Validation    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔑 Authentication & Authorization            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   OAuth 2.0     │  │   API Keys      │  │   Session       │ │
│  │   (PowerBI)     │  │   Management    │  │   Management    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    📊 Monitoring & Logging                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Security      │  │   Audit         │  │   Threat        │ │
│  │   Logging       │  │   Trail         │  │   Detection     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🔐 Security Components

#### 1. **SecurityManager**
```python
from src.utils.security_enhanced import SecurityManager

security = SecurityManager()

# Path validation
is_safe = security.validate_path("/data/user_input.csv", "/app/data")

# Rate limiting
is_allowed = security.rate_limit("user_123", max_requests=100, window=3600)

# Input sanitization
clean_input = security.sanitize_input(user_input)
```

#### 2. **Database Security (DuckDB)**
```python
from src.database.duckdb.manager import DuckDBManager

manager = DuckDBManager()

# SQL injection protection with enhanced table name validation
try:
    manager.bulk_insert("istat.observations", dataframe)  # ✅ Safe
    manager.bulk_insert("'; DROP TABLE users; --", dataframe)  # ❌ Blocked
except ValueError as e:
    logger.error(f"Security violation blocked: {e}")

# Parameterized queries for all user data
result = manager.execute_query(
    "SELECT * FROM observations WHERE dataset_id = ? AND year = ?",
    parameters={"dataset_id": user_dataset_id, "year": user_year}
)
```

**Security Features:**
- **Enhanced Table Validation**: Strict alphanumeric checks prevent SQL injection
- **Parameterized Queries**: All user data operations use prepared statements
- **Type Safety**: 100% MyPy compliance ensures runtime safety
- **Connection Security**: Robust connection lifecycle with proper cleanup
- **Error Handling**: Secure error messages without information disclosure

#### 3. **Circuit Breaker**
```python
from src.utils.circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
def external_api_call():
    return requests.get("https://api.external.com/data")
```

#### 3. **Security Headers**
```python
security_headers = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'"
}
```

### 🎯 Security Policies

#### **Input Validation**
- All user inputs are validated and sanitized
- Path traversal attacks prevented
- XSS and injection attacks blocked
- File extension validation

#### **Rate Limiting**
- API endpoints protected with rate limits
- Configurable thresholds per endpoint
- Automatic IP blocking for abuse
- Sliding window algorithm

#### **Authentication**
- OAuth 2.0 for external services
- API key management
- Session timeout management
- Multi-factor authentication (planned)

---

## 🧪 Testing Architecture

### 📊 Testing Pyramid

```
                    ┌─────────────────┐
                    │   🔍 Manual     │
                    │   Testing       │ ◀─── 5% of effort
                    │   (2 tests)     │
                    └─────────────────┘
                           ▲
                    ┌─────────────────┐
                    │   ⚡ Performance │
                    │   Testing       │ ◀─── 10% of effort
                    │   (24 tests)    │
                    └─────────────────┘
                           ▲
                    ┌─────────────────┐
                    │   🔗 Integration│
                    │   Testing       │ ◀─── 15% of effort
                    │   (26 tests)    │
                    └─────────────────┘
                           ▲
            ┌─────────────────────────────────┐
            │           🧪 Unit               │
            │           Testing               │ ◀─── 70% of effort
            │           (351 tests)           │
            └─────────────────────────────────┘
```

### 🔍 Testing Strategy

#### **Unit Tests (156 tests)**
- **Coverage**: Individual functions and methods
- **Scope**: Isolated component testing
- **Tools**: pytest, pytest-mock, unittest.mock
- **Location**: `tests/unit/`

**Example Test Structure**:
```python
class TestSecurityManager:
    def setup_method(self):
        self.security_manager = SecurityManager()

    def test_validate_path_safe_paths(self):
        safe_paths = ["data/test.csv", "reports/analysis.json"]
        for path in safe_paths:
            assert self.security_manager.validate_path(path) is True

    def test_rate_limit_enforcement(self):
        # Test rate limiting functionality
        pass
```

#### **Integration Tests (26 tests)**
- **Coverage**: Component interaction
- **Scope**: API integration, data flow
- **Tools**: pytest, requests-mock
- **Location**: `tests/integration/`

**Example Integration Test**:
```python
def test_istat_api_to_converter_integration():
    # Test complete data flow from API to converter
    api_client = IstatAPITester()
    converter = IstatXMLToPowerBIConverter()

    # Fetch data
    xml_data = api_client.fetch_sample_data()

    # Convert data
    result = converter.convert_xml_to_powerbi(xml_data)

    assert result["success"] is True
    assert len(result["files_created"]) == 4
```

#### **Performance Tests (8 tests)**
- **Coverage**: Scalability and performance
- **Scope**: Memory usage, execution time
- **Tools**: pytest, psutil, memory_profiler
- **Location**: `tests/performance/`

#### **End-to-End Tests (2 tests)**
- **Coverage**: Complete user workflows
- **Scope**: Dashboard functionality, data pipeline
- **Tools**: Selenium, pytest
- **Location**: `tests/e2e/`

### 📈 Testing Metrics
- **Total Tests**: 192 tests
- **Pass Rate**: 100% (192/192)
- **Execution Time**: ~8 seconds
- **Coverage**: 41% (target: 70%)
- **Flaky Tests**: 0% (highly reliable)

---

## 🚀 Deployment Architecture

### ☁️ Cloud Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 Streamlit Cloud                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Load          │  │   Application   │  │   Static        │ │
│  │   Balancer      │  │   Instances     │  │   Assets        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔧 GitHub Actions (CI/CD)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Build         │  │   Test          │  │   Deploy        │ │
│  │   Pipeline      │  │   Pipeline      │  │   Pipeline      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    📊 External Services                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   ISTAT API     │  │   PowerBI       │  │   Tableau       │ │
│  │   (Data Source) │  │   Service       │  │   Server        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🔄 CI/CD Pipeline

#### **GitHub Actions Workflow**
```yaml
name: Deploy Dashboard
on:
  push:
    branches: [main, feature/dashboard]
  pull_request:
    branches: [main]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.13.3'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r dashboard/requirements.txt

    - name: Run tests
      run: |
        pytest tests/unit/ -v --tb=short

    - name: Security scan
      run: |
        pip install bandit safety
        bandit -r src/ -f json -o bandit-report.json
        safety check

    - name: Deploy to Streamlit Cloud
      if: github.ref == 'refs/heads/main'
      run: echo "🚀 Deploying to production"
```

### 🏗️ Deployment Configuration

#### **Streamlit Configuration**
```toml
[theme]
primaryColor = "#0066CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
port = 8501
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

#### **Environment Variables**
```env
# API Configuration
ISTAT_API_BASE_URL=https://sdmx.istat.it/SDMXWS/rest/
ISTAT_API_TIMEOUT=30

# PowerBI Configuration
POWERBI_CLIENT_ID=your_client_id
POWERBI_CLIENT_SECRET=your_client_secret
POWERBI_TENANT_ID=your_tenant_id

# Application Configuration
LOG_LEVEL=INFO
ENABLE_CACHE=true
MAX_CACHE_SIZE=1000
```

---

## ⚡ Performance Architecture

### 📊 Performance Optimization Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    🚀 Performance Layers                       │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   🏎️ Frontend    │  │   ⚡ Backend     │  │   💾 Data        │ │
│  │   Optimization  │  │   Optimization  │  │   Optimization  │ │
│  │                 │  │                 │  │                 │ │
│  │  • Lazy Loading │  │  • Caching      │  │  • Parquet      │ │
│  │  • Code Split   │  │  • Async Ops    │  │  • Compression  │ │
│  │  • Compression  │  │  • Connection   │  │  • Indexing     │ │
│  │  • CDN Assets   │  │    Pooling      │  │  • Pagination   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🔍 Performance Monitoring

#### **Key Performance Indicators**
- **Page Load Time**: <3 seconds (target)
- **API Response Time**: <300ms (target)
- **Memory Usage**: <500MB (target)
- **CPU Usage**: <50% (target)
- **Error Rate**: <0.1% (target)

#### **DuckDB Performance Testing (Day 3 Implementation)**
- **Performance Test Suite**: 24 comprehensive performance tests
  - **Bulk Insert Performance**: >2k records/sec validated (minimum requirement)
  - **Query Caching**: >10x speedup with intelligent TTL management
  - **Concurrent Execution**: Scaling validation with 1-8 threads
  - **Memory Patterns**: Linear scaling with efficient memory usage
  - **Indexing Impact**: Performance optimization for large datasets
  - **Query Builder**: 826 lines with fluent interface and ISTAT-specific patterns

- **Performance Monitoring Tools**:
  - **DuckDBPerformanceProfiler**: Real-time CPU, memory, and execution time tracking
  - **Regression Detection**: Automated baseline comparison with statistical analysis
  - **Cache Analytics**: Hit rate optimization and performance metrics
  - **Memory Profiling**: psutil integration for detailed memory usage patterns

#### **Performance Optimization Techniques**

1. **Data Caching**
```python
import streamlit as st

@st.cache_data(ttl=3600)
def load_dataset(category):
    # Expensive data loading operation
    return process_data(category)
```

2. **Lazy Loading**
```python
def load_data_on_demand(category):
    if category not in st.session_state:
        st.session_state[category] = load_dataset(category)
    return st.session_state[category]
```

3. **File Format Optimization**
```python
# Use Parquet for large datasets
df.to_parquet('large_dataset.parquet', compression='snappy')

# Use CSV for small datasets
df.to_csv('small_dataset.csv', index=False)
```

---

## 📊 PowerBI Integration Architecture

### 🏗️ PowerBI Integration Overview

The **PowerBI Integration** represents a comprehensive enterprise-grade solution for seamless integration between the Osservatorio ISTAT platform and Microsoft PowerBI ecosystem. Implemented as part of Day 6 development cycle, this integration provides optimized data pipelines, automated refresh systems, and governance capabilities.

```
┌─────────────────────────────────────────────────────────────────┐
│                    📊 PowerBI Integration Layer                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   🔧 PowerBI     │  │   🔄 Incremental│  │   📋 Template   │ │
│  │   Optimizer     │  │   Refresh       │  │   Generator     │ │
│  │                 │  │   Manager       │  │                 │ │
│  │  • Star Schema  │  │  • Change Track │  │  • PBIT Files   │ │
│  │  • DAX Measures │  │  • Delta Sync   │  │  • Visualizations│ │
│  │  • Performance  │  │  • SQLite Track │  │  • Italian i18n │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🌉 Metadata Bridge Layer                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   📊 Dataset     │  │   🎯 Quality     │  │   📋 Governance │ │
│  │   Lineage       │  │   Score Sync    │  │   Reporting     │ │
│  │                 │  │                 │  │                 │ │
│  │  • Data Flow    │  │  • Score Prop   │  │  • Compliance   │ │
│  │  • Transform    │  │  • DAX Quality  │  │  • Analytics    │ │
│  │  • Audit Trail  │  │  • Validation   │  │  • Usage Track  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🧩 PowerBI Components Architecture

#### 1. **PowerBI Optimizer (`src/integrations/powerbi/optimizer.py`)**
```python
class PowerBIOptimizer:
    """
    Optimizes ISTAT data for PowerBI consumption through:
    - Star schema generation from metadata
    - DAX measures pre-calculation with 6-hour TTL caching
    - Performance metrics estimation
    - Category-specific optimizations (popolazione, economia, lavoro)
    """
```

**Key Features:**
- **Star Schema Generation**: Automatic fact/dimension table creation
- **DAX Measures Engine**: Pre-calculated measures with intelligent caching
- **Performance Optimization**: Load time estimation and refresh frequency recommendations
- **Category-Specific Logic**: Specialized dimensions for Italian statistical categories

#### 2. **Incremental Refresh Manager (`src/integrations/powerbi/incremental.py`)**
```python
class IncrementalRefreshManager:
    """
    Manages PowerBI incremental refresh with SQLite change tracking:
    - Change detection with timestamp-based deltas
    - Refresh policy management (daily/weekly/monthly)
    - Conflict resolution for concurrent updates
    - Performance monitoring and logging
    """
```

**Architecture Benefits:**
- **SQLite Change Tracking**: Efficient delta detection without external dependencies
- **Policy-Based Refresh**: Configurable refresh windows and frequencies
- **Conflict Resolution**: Handles concurrent data updates gracefully
- **Performance Monitoring**: Real-time refresh status and metrics

#### 3. **Template Generator (`src/integrations/powerbi/templates.py`)**
```python
class TemplateGenerator:
    """
    Generates PowerBI templates (.pbit files) with:
    - Category-specific visualizations for Italian data
    - Italian localization (locale: it-IT, currency: EUR)
    - Pre-configured star schema integration
    - Quality score visualization components
    """
```

**Template Features:**
- **PBIT File Generation**: Complete PowerBI template files with metadata
- **Visualization Library**: 15+ pre-configured charts for ISTAT data categories
- **Italian Localization**: Native Italian formatting and terminology
- **Quality Integration**: Built-in quality score visualizations

#### 4. **Metadata Bridge (`src/integrations/powerbi/metadata_bridge.py`)**
```python
class MetadataBridge:
    """
    Bridges metadata between SQLite and PowerBI Service:
    - Dataset lineage tracking with transformation history
    - Usage analytics synchronization
    - Quality score propagation to PowerBI measures
    - Governance reporting and compliance monitoring
    """
```

**Governance Features:**
- **Dataset Lineage**: Complete data transformation tracking
- **Usage Analytics**: PowerBI Service integration for usage metrics
- **Quality Propagation**: Automatic quality score sync to PowerBI
- **Governance Reporting**: Compliance and audit trail generation

### 🔄 PowerBI Data Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   📊 ISTAT   │    │   🔧 Star    │    │   📋 Template│    │   🔄 Refresh │
│   Data       │───▶│   Schema     │───▶│   Generate   │───▶│   Policy     │
│   (Source)   │    │   (Optimize) │    │   (PBIT)     │    │   (Schedule) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   📊 PowerBI │    │   🌉 Metadata│    │   🎯 Quality │    │   📈 Usage   │
│   Service    │◀───│   Bridge     │◀───│   Scores     │◀───│   Analytics  │
│   (Consume)  │    │   (Sync)     │    │   (Propagate)│    │   (Monitor)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 🎯 PowerBI Integration Features

#### **Enterprise-Grade Features**
- **Security-First Design**: Bandit scan 0 issues, parameterized queries, input validation
- **Performance Optimized**: Caching strategies, efficient delta detection, optimized schemas
- **Production Ready**: Comprehensive error handling, logging, monitoring
- **Italian Localization**: Native Italian formatting and terminology throughout

#### **Advanced Capabilities**
- **Star Schema Automation**: Automatic optimization for PowerBI performance
- **Intelligent Caching**: DAX measures cached with 6-hour TTL for optimal performance
- **Change Detection**: SQLite-based incremental refresh without external dependencies
- **Quality Integration**: Built-in data quality scores in PowerBI visualizations

#### **Integration Benefits**
- **Zero-Configuration**: Works with existing SQLite + DuckDB hybrid architecture
- **Seamless Workflow**: End-to-end pipeline from ISTAT API to PowerBI Service
- **Governance Ready**: Complete audit trail and compliance reporting
- **Scalable Architecture**: Designed for enterprise deployment and scaling

### 📊 PowerBI Performance Metrics

**Validated Performance (Day 6 Testing):**
- **Template Generation**: <3 seconds for complete PBIT creation
- **Star Schema Creation**: <1 second for complex schemas with 6+ dimensions
- **DAX Measures**: 9+ measures generated with <50ms cache retrieval
- **Incremental Refresh**: Delta detection <100ms for change tracking
- **Security Validation**: 0 HIGH severity issues (Bandit scan)

**Architecture Scalability:**
- **Dataset Support**: 500+ ISTAT datasets with automatic categorization
- **Concurrent Users**: Designed for 100+ simultaneous PowerBI users
- **Refresh Frequency**: Supports real-time to monthly refresh cycles
- **Template Library**: Extensible template system for new visualization types

---

## 📈 Advanced Analytics Architecture

The **Advanced Analytics Architecture** extends the core Osservatorio platform with enterprise-grade business intelligence and visualization capabilities. This layer provides multiple integration pathways for popular BI tools and advanced analytics platforms.

### 🎯 Multi-Platform BI Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    🔧 Unified Analytics Layer                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   📊 PowerBI │  │   📈 Tableau │  │   📋 Qlik   │  │   🔍   │ │
│  │   Integration│  │   Integration│  │   Integration│  │  Future │ │
│  │             │  │             │  │             │  │   BI    │ │
│  │  • REST API │  │  • Tableau  │  │  • QlikSense│  │  Tools  │ │
│  │  • Templates│  │    Server   │  │  • Apps     │  │         │ │
│  │  • Star     │  │  • Extracts │  │  • Scripts  │  │         │ │
│  │    Schema   │  │  • Workbooks│  │  • Models   │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🗄️ Unified Data Engine                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   SQLite        │  │   DuckDB        │  │   Data Quality  │ │
│  │   Metadata      │  │   Analytics     │  │   Engine        │ │
│  │                 │  │                 │  │                 │ │
│  │  • 500+ Datasets│  │  • OLAP Cubes   │  │  • Validation   │ │
│  │  • Lineage      │  │  • Aggregations │  │  • Scoring      │ │
│  │  • Quality      │  │  • Vectorized   │  │  • Monitoring   │ │
│  │  • Governance   │  │    Operations   │  │  • Alerting     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🏗️ Analytics Integration Patterns

#### **1. PowerBI Integration (Production Ready)**
- **Status**: ✅ Complete Implementation
- **Components**: API Client, Star Schema Optimizer, Template Generator, Incremental Refresh
- **Features**: Enterprise authentication, automated templates, offline validation
- **Documentation**: [`docs/integrations/POWERBI_INTEGRATION.md`](../integrations/POWERBI_INTEGRATION.md)

#### **2. Tableau Integration (Roadmap)**
- **Status**: 🔄 Planned for Q4 2025
- **Components**: Tableau Server API, Extract optimization, Workbook templates
- **Features**: Hyper file generation, dashboard automation, server publishing

#### **3. Qlik Integration (Future)**
- **Status**: 📋 Backlog
- **Components**: QlikSense integration, app generation, script automation
- **Features**: Associative model optimization, self-service analytics

### 📊 Analytics Data Pipeline Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        A[ISTAT SDMX API] --> B[Raw Data Ingestion]
    end

    subgraph "Processing Layer"
        B --> C[Data Validation]
        C --> D[Quality Scoring]
        D --> E[SQLite Storage]
        E --> F[DuckDB Analytics]
    end

    subgraph "Analytics Optimization"
        F --> G[Star Schema Generator]
        G --> H[Dimensional Modeling]
        H --> I[Measure Calculation]
        I --> J[Template Generation]
    end

    subgraph "BI Platform Delivery"
        J --> K[PowerBI Service]
        J --> L[Tableau Server]
        J --> M[Qlik Sense]
        J --> N[Custom Dashboards]
    end

    subgraph "Governance & Monitoring"
        O[Data Lineage] --> P[Quality Monitoring]
        P --> Q[Usage Analytics]
        Q --> R[Governance Reports]
    end

    E --> O
    K --> O
    L --> O
    M --> O
```

### 🎯 Analytics Features Matrix

| Feature | PowerBI | Tableau | Qlik | Streamlit |
|---------|---------|---------|------|-----------|
| **Authentication** | ✅ MSAL | 🔄 Planned | 📋 Future | ✅ Native |
| **Star Schema** | ✅ Auto | 🔄 Planned | 📋 Future | ✅ DuckDB |
| **Templates** | ✅ PBIT | 🔄 TWB | 📋 QVF | ✅ Python |
| **Incremental Refresh** | ✅ Policy | 🔄 Extract | 📋 Reload | ✅ Cache |
| **Italian Localization** | ✅ i18n | 🔄 Planned | 📋 Future | ✅ Native |
| **Offline Validation** | ✅ Complete | 🔄 Planned | 📋 Future | ✅ Tests |
| **Quality Integration** | ✅ DAX | 🔄 Calcs | 📋 Script | ✅ Metrics |

### 🔧 Advanced Analytics Components

#### **Analytics Engine Core**
```python
class AnalyticsEngine:
    """
    Unified analytics engine supporting multiple BI platforms.
    Provides standardized interfaces for data modeling, template
    generation, and deployment across PowerBI, Tableau, and Qlik.
    """

    def __init__(self):
        self.powerbi_integration = PowerBIOptimizer(repository)
        self.tableau_integration = None  # Future implementation
        self.qlik_integration = None     # Future implementation

    def generate_star_schema(self, dataset_id: str, platform: str):
        """Generate optimized star schema for target platform"""

    def create_template(self, dataset_id: str, platform: str):
        """Create platform-specific template (PBIT, TWB, QVF)"""

    def setup_incremental_refresh(self, dataset_id: str, platform: str):
        """Configure incremental refresh for target platform"""
```

#### **Quality Score Analytics**
```python
class QualityAnalytics:
    """
    Advanced quality score analytics with trend analysis,
    anomaly detection, and predictive quality scoring.
    """

    def calculate_quality_trends(self, dataset_id: str):
        """Analyze quality score trends over time"""

    def detect_quality_anomalies(self, dataset_id: str):
        """Identify unusual quality score patterns"""

    def predict_quality_scores(self, dataset_id: str):
        """Predict future quality scores based on historical data"""
```

#### **Governance Analytics**
```python
class GovernanceAnalytics:
    """
    Enterprise governance with usage analytics, compliance
    monitoring, and automated reporting across all BI platforms.
    """

    def track_cross_platform_usage(self):
        """Monitor usage across PowerBI, Tableau, Qlik"""

    def generate_compliance_report(self):
        """Generate compliance reports for data governance"""

    def monitor_data_lineage(self, dataset_id: str):
        """Track data lineage across all analytics platforms"""
```

### 📈 Analytics Performance Optimization

#### **Caching Strategy**
- **L1 Cache**: In-memory Python objects (1-5 minutes TTL)
- **L2 Cache**: SQLite query results (15-30 minutes TTL)
- **L3 Cache**: DuckDB materialized views (1-6 hours TTL)
- **L4 Cache**: Platform-specific caches (PowerBI datasets, Tableau extracts)

#### **Query Optimization**
```sql
-- Star schema optimized for analytics platforms
CREATE VIEW analytics_fact_optimized AS
SELECT
    dataset_id,
    territory_key,
    time_key,
    measure_key,
    obs_value,
    quality_score,
    last_updated,
    -- Pre-calculated aggregates for performance
    ROW_NUMBER() OVER (PARTITION BY dataset_id ORDER BY last_updated DESC) as recency_rank,
    AVG(quality_score) OVER (PARTITION BY dataset_id) as dataset_avg_quality,
    COUNT(*) OVER (PARTITION BY territory_key) as territory_measure_count
FROM fact_table
WHERE quality_score >= 0.7  -- Filter low-quality data
```

#### **Memory Management**
- **Lazy Loading**: Load analytics components only when needed
- **Batch Processing**: Process large datasets in configurable chunks
- **Memory Profiling**: Built-in memory usage monitoring and alerts
- **Garbage Collection**: Automatic cleanup of unused objects and caches

### 🛡️ Analytics Security Architecture

#### **Multi-Platform Security**
```python
class AnalyticsSecurityManager:
    """
    Unified security management across all analytics platforms
    with platform-specific authentication and authorization.
    """

    def authenticate_platform(self, platform: str, credentials: Dict):
        """Platform-specific authentication (MSAL, Tableau, Qlik)"""

    def validate_cross_platform_access(self, user_id: str, dataset_id: str):
        """Validate user access across multiple platforms"""

    def audit_analytics_access(self, platform: str, action: str):
        """Audit all analytics platform interactions"""
```

#### **Data Protection**
- **Encryption at Rest**: SQLite database encryption
- **Encryption in Transit**: HTTPS/TLS for all API communications
- **Access Control**: Role-based access control (RBAC) across platforms
- **Audit Trail**: Complete logging of all analytics operations

### 🚀 Analytics Deployment Strategy

#### **Staging Environment**
```yaml
# Analytics staging configuration
analytics_staging:
  powerbi:
    workspace_id: "staging-workspace-123"
    dataset_prefix: "staging_"
    refresh_frequency: "hourly"

  tableau:
    server_url: "https://tableau-staging.company.com"
    project: "Osservatorio_Staging"
    refresh_frequency: "daily"

  monitoring:
    enabled: true
    alert_threshold: 0.95
    notification_channel: "slack://analytics-alerts"
```

#### **Production Deployment**
```yaml
# Analytics production configuration
analytics_production:
  powerbi:
    workspace_id: "prod-workspace-456"
    dataset_prefix: ""
    refresh_frequency: "daily"

  tableau:
    server_url: "https://tableau.company.com"
    project: "Osservatorio_Production"
    refresh_frequency: "daily"

  monitoring:
    enabled: true
    alert_threshold: 0.99
    notification_channel: "email://ops-team@company.com"
```

### 📊 Analytics Roadmap

#### **Q3 2025: PowerBI Enhancement**
- ✅ Advanced DAX measures library
- ✅ Custom visual components
- ✅ Real-time refresh capabilities
- ✅ Enhanced Italian localization

#### **Q4 2025: Tableau Integration**
- 🔄 Tableau Server API integration
- 🔄 Hyper file optimization
- 🔄 Workbook template automation
- 🔄 Extract refresh management

#### **Q1 2026: Qlik Integration**
- 📋 QlikSense integration
- 📋 Associative model optimization
- 📋 App generation automation
- 📋 Script template library

#### **Q2 2026: Advanced Analytics**
- 📋 Machine learning integration
- 📋 Predictive analytics
- 📋 Natural language queries
- 📋 AI-powered insights
- **Multi-Dataset Support**: Handles 509+ ISTAT datasets efficiently
- **Concurrent Operations**: Thread-safe operations with connection pooling
- **Memory Efficiency**: Linear scaling with dataset size
- **Cache Performance**: >10x speedup with intelligent TTL management

---

## 🔌 Integration Architecture

### 🌐 External System Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    🏢 Osservatorio Core                        │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   🔌 API        │  │   📊 Data       │  │   🎯 Business   │ │
│  │   Gateway       │  │   Pipeline      │  │   Logic         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   🇮🇹 ISTAT      │  │   📊 PowerBI     │  │   📈 Tableau     │
│   SDMX API      │  │   Service       │  │   Server        │
│                 │  │                 │  │                 │
│  • 509+ datasets│  │  • Workspaces   │  │  • Data Sources │
│  • Real-time    │  │  • Datasets     │  │  • Dashboards   │
│  • Rate limited │  │  • Reports      │  │  • Permissions  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 🔗 Integration Patterns

#### **1. API Client Pattern**
```python
class IstatAPIClient:
    def __init__(self):
        self.base_url = "https://sdmx.istat.it/SDMXWS/rest/"
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(max_requests=50, window=3600)

    @circuit_breaker(failure_threshold=5)
    def fetch_dataflow(self, flow_ref):
        return self.session.get(f"{self.base_url}/dataflow/{flow_ref}")
```

#### **2. Data Transformation Pattern**
```python
class DataTransformer:
    def transform_istat_to_powerbi(self, xml_data):
        # Parse XML
        df = self.parse_xml(xml_data)

        # Apply transformations
        df = self.clean_data(df)
        df = self.categorize_data(df)
        df = self.validate_quality(df)

        # Export formats
        return self.export_multiple_formats(df)
```

#### **3. Event-Driven Pattern**
```python
class EventPublisher:
    def __init__(self):
        self.subscribers = []

    def publish_data_update(self, event_data):
        for subscriber in self.subscribers:
            subscriber.handle_event(event_data)
```

---

## 🚀 Future Architecture

### 🔮 Evolution Roadmap

#### **Next Priority: Issue #66 - Production ISTAT API Client**

**Architectural Vision**: Transform `src/api/istat_api.py` from exploration tool to production-ready component

```
Current State (Exploration)       →       Target State (Production)
┌─────────────────────┐                  ┌─────────────────────┐
│  Manual API Calls  │                  │  Connection Pool    │
│  Basic Error Hand  │       ──→        │  Circuit Breaker    │
│  Limited Testing   │                  │  Repository Integ   │
│  Exploration Code  │                  │  Async Operations   │
└─────────────────────┘                  └─────────────────────┘
```

**Integration Points**:
- SQLite metadata layer (Issue #59 ✅)
- DuckDB analytics engine (✅)
- BaseConverter architecture (Issue #62 ✅)
- Unified repository pattern (✅)

#### **Phase 2: Enhanced Platform (Month 4-6)**
```
Current State                    Future State
     │                              │
     ▼                              ▼
┌─────────────┐                ┌─────────────┐
│  Monolithic │      ───▶      │ Microservices│
│  Application│                │ Architecture │
└─────────────┘                └─────────────┘
     │                              │
     ▼                              ▼
┌─────────────┐                ┌─────────────┐
│  File-based │      ───▶      │  Database   │
│  Storage    │                │  Integration│
└─────────────┘                └─────────────┘
     │                              │
     ▼                              ▼
┌─────────────┐                ┌─────────────┐
│  Manual     │      ───▶      │  Automated  │
│  Deployment │                │  Scaling    │
└─────────────┘                └─────────────┘
```

#### **Microservices Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                    🎯 API Gateway                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Authentication│  │   Rate Limiting │  │   Load Balancing│ │
│  │   Service       │  │   Service       │  │   Service       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🔧 Business Services                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Data          │  │   Analytics     │  │   Notification  │ │
│  │   Processing    │  │   Service       │  │   Service       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    💾 Data Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │   Redis Cache   │  │   File Storage  │ │
│  │   (Primary DB)  │  │   (Session)     │  │   (Assets)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### **Phase 3: AI-Enhanced Platform (Month 6-12)**
```
┌─────────────────────────────────────────────────────────────────┐
│                    🤖 AI/ML Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Predictive    │  │   Anomaly       │  │   Natural       │ │
│  │   Analytics     │  │   Detection     │  │   Language      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    📊 Real-time Processing                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Stream        │  │   Event         │  │   Message       │ │
│  │   Processing    │  │   Processing    │  │   Queue         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 🎯 Technology Evolution

#### **Database Integration**
- **PostgreSQL**: Primary database for structured data
- **Redis**: Caching and session management
- **Elasticsearch**: Full-text search capabilities
- **TimescaleDB**: Time-series data optimization

#### **Container Orchestration**
- **Docker**: Application containerization
- **Kubernetes**: Container orchestration
- **Helm**: Package management
- **Istio**: Service mesh (optional)

#### **Monitoring & Observability**
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Logging and analysis

---

## 📋 Architecture Decision Records (ADRs)

### ADR-001: Python as Primary Language
- **Status**: Accepted
- **Context**: Need for data processing and analysis
- **Decision**: Use Python 3.8+ as primary language
- **Consequences**: Rich ecosystem for data science, mature libraries

### ADR-002: Streamlit for Dashboard
- **Status**: Accepted
- **Context**: Need for rapid dashboard development
- **Decision**: Use Streamlit for web interface
- **Consequences**: Fast development, limited customization

### ADR-003: Layered Architecture
- **Status**: Accepted
- **Context**: Need for maintainable and scalable code
- **Decision**: Implement layered architecture pattern
- **Consequences**: Clear separation of concerns, testability

### ADR-004: Security-First Design
- **Status**: Accepted
- **Context**: Handling sensitive statistical data
- **Decision**: Implement security at every layer
- **Consequences**: Increased complexity, better protection

### ADR-005: Component-Based Testing
- **Status**: Accepted
- **Context**: Need for reliable and maintainable tests
- **Decision**: Use pytest with comprehensive test coverage
- **Consequences**: High confidence in code quality

---

## 🎯 Conclusion

The **Osservatorio** architecture represents a **modern, secure, and scalable** approach to data processing and visualization. The current implementation provides a solid foundation for future growth while maintaining **high code quality**, **comprehensive testing**, and **enterprise-grade security**.

### ✅ Architecture Strengths
- **Modularity**: Clean separation of concerns
- **Security**: Comprehensive security implementation
- **Testability**: Extensive test coverage (192 tests)
- **Maintainability**: Well-documented and organized
- **Scalability**: Prepared for future growth

### 🔮 Future Opportunities
- **Microservices**: Service decomposition
- **AI/ML Integration**: Predictive analytics
- **Real-time Processing**: Stream processing
- **Enterprise Features**: Multi-tenancy, SLA

**The architecture is production-ready and positioned for successful evolution.**

---

**Document Version**: 8.1.0
**Last Updated**: July 23, 2025
**Next Review**: August 23, 2025

## 🆕 Recent Updates (v8.1.0 - Day 4 Complete)

### SQLite + DuckDB Hybrid Architecture Implementation
Following the strategic pivot decision (ADR-002), the architecture now implements a complete SQLite + DuckDB hybrid approach:

#### **Hybrid Database Strategy (Implemented)**
```
┌─────────────────────────────────────────────────────────────────┐
│                    💾 Hybrid Storage Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   🗃️ SQLite      │  │   🦆 DuckDB      │  │   🔄 Unified    │ │
│  │   (Metadata)    │  │   (Analytics)   │  │   Repository    │ │
│  │                 │  │                 │  │   (Facade)      │ │
│  │  • User Prefs   │  │  • Time Series  │  │  • Smart Route  │ │
│  │  • API Keys     │  │  • Aggregations │  │  • Cache Layer  │ │
│  │  • Audit Logs   │  │  • Performance  │  │  • Transactions │ │
│  │  • Config       │  │  • Analytics    │  │  • Cross-DB Ops │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### **Day 4 Implementation Results**
- **Complete SQLite Metadata Layer**: 6-table schema with thread-safe operations
- **Security-Enhanced Storage**: Fernet encryption for sensitive data
- **Unified Repository Pattern**: Single interface combining both databases
- **Comprehensive Testing**: 40+ tests with 100% pass rate, zero failures
- **Production-Ready Security**: Bandit scan reduced from 5 to 2 issues
- **Type Safety**: 83.2% average type hint coverage

#### **Architecture Decision Records (Updated)**
- **[ADR-001: Database Selection](adr/001-database-selection.md)**: Original hybrid approach (superseded)
- **[ADR-002: Strategic Pivot to SQLite](adr/002-strategic-pivot-sqlite.md)**: Strategic pivot decision (active)

#### **Updated Component Architecture**
The data flow now includes intelligent operation routing:

```
ISTAT API → XML Parser → Unified Repository → Dashboard
                      ↗ SQLite (Metadata)
                      ↘ DuckDB (Analytics)
```

#### **Implementation Timeline (Completed)**
- **Day 1-3 (Completed)**: DuckDB analytics engine with performance testing
- **Day 4 (Completed)**: SQLite metadata layer implementation
- **Day 5-8 (Planned)**: PowerBI integration and FastAPI development
