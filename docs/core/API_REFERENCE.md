# 🔌 Osservatorio API Reference

> **Comprehensive API documentation for the Osservatorio ISTAT data processing platform**
> **Version**: 8.1.0
> **Date**: July 23, 2025
> **Status**: Production Ready

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Authentication & Security](#-authentication--security)
3. [ISTAT API Client](#-istat-api-client)
4. [PowerBI API Client](#-powerbi-api-client)
5. [Tableau API Client](#-tableau-api-client)
6. [Data Converters](#-data-converters)
7. [Security Manager](#-security-manager)
8. [SQLite Metadata Layer](#-sqlite-metadata-layer)
9. [DuckDB Analytics Engine](#-duckdb-analytics-engine)
10. [Circuit Breaker](#-circuit-breaker)
11. [Analyzers](#-analyzers)
12. [Utilities](#-utilities)
13. [Error Handling](#-error-handling)
14. [Rate Limiting](#-rate-limiting)
15. [Examples](#-examples)

---

## 🎯 Overview

The Osservatorio API provides programmatic access to Italian statistical data processing, conversion, and visualization capabilities. The API is designed with **security-first principles** and includes comprehensive **rate limiting**, **input validation**, and **error handling**.

### 🏗️ Architecture
- **Hybrid Database Design**: SQLite for metadata + DuckDB for analytics (ADR-002)
- **Modular Design**: Each component is independently testable
- **Security Integration**: Built-in security at every layer
- **Rate Limiting**: Configurable limits for all external calls
- **Circuit Breaker**: Automatic failure recovery
- **Type Safety**: Full type hints for better IDE support

### 📊 Supported Data Sources
- **ISTAT SDMX API**: 509+ Italian statistical datasets
- **PowerBI Service**: Workspace and dataset management
- **Tableau Server**: Data source and dashboard management

### 🗃️ Storage Architecture
- **SQLite Metadata Layer**: User preferences, API credentials, audit logs, system configuration
- **DuckDB Analytics Engine**: Time-series data, aggregations, performance analytics
- **Unified Repository**: Single interface combining both databases with intelligent routing

---

## 🔐 Authentication & Security

### 🛡️ Security Features
- **Path Validation**: Prevents directory traversal attacks
- **Input Sanitization**: XSS and injection prevention
- **Rate Limiting**: Configurable request limits
- **IP Blocking**: Automatic suspicious activity blocking
- **Security Headers**: Complete HTTP security headers

### 🔑 Authentication Methods
- **ISTAT API**: No authentication required (public API)
- **PowerBI API**: OAuth 2.0 with Azure AD
- **Tableau API**: Server-based authentication

---

## 🇮🇹 ISTAT API Client

### 📝 Class: `IstatAPITester`

Main client for interacting with the ISTAT SDMX API.

#### 🔧 Initialization
```python
from src.api.istat_api import IstatAPITester

# Initialize client
client = IstatAPITester()
```

#### 🔍 Methods

##### `fetch_dataflows()`
Retrieves all available ISTAT dataflows.

```python
def fetch_dataflows() -> List[Dict[str, Any]]
```

**Returns:**
- `List[Dict[str, Any]]`: List of dataflow information

**Example:**
```python
dataflows = client.fetch_dataflows()
print(f\"Found {len(dataflows)} dataflows\")
```

##### `fetch_dataset_data(dataset_id: str)`
Fetches data for a specific dataset.

```python
def fetch_dataset_data(dataset_id: str) -> str
```

**Parameters:**
- `dataset_id` (str): ISTAT dataset identifier (e.g., \"DCIS_POPRES1\")

**Returns:**
- `str`: XML data content

**Example:**
```python
xml_data = client.fetch_dataset_data(\"DCIS_POPRES1\")
```

##### `test_api_connectivity()`
Tests connectivity to the ISTAT API.

```python
def test_api_connectivity() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Connectivity test results

**Example:**
```python
results = client.test_api_connectivity()
print(f\"API Status: {results['status']}\")
```

#### 🚦 Rate Limiting
- **Limit**: 50 requests per hour
- **Enforcement**: Automatic with `@rate_limit` decorator
- **Behavior**: Raises exception when limit exceeded

#### 🔄 Error Handling
- **Connection Errors**: Automatic retry with exponential backoff
- **Invalid Dataset**: Returns meaningful error messages
- **Rate Limit**: Raises `RateLimitExceeded` exception

---

## 📊 PowerBI API Client

### 📝 Class: `PowerBIAPIClient`

Client for Microsoft PowerBI Service integration.

#### 🔧 Initialization
```python
from src.api.powerbi_api import PowerBIAPIClient

# Initialize client
client = PowerBIAPIClient()
```

#### 🔍 Methods

##### `authenticate()`
Authenticates with PowerBI Service using OAuth 2.0.

```python
def authenticate() -> bool
```

**Returns:**
- `bool`: True if authentication successful

**Example:**
```python
if client.authenticate():
    print(\"Authentication successful\")
```

##### `get_workspaces()`
Retrieves all available PowerBI workspaces.

```python
@rate_limit(max_requests=100, window=3600)
def get_workspaces() -> List[Dict[str, Any]]
```

**Returns:**
- `List[Dict[str, Any]]`: List of workspace information

**Example:**
```python
workspaces = client.get_workspaces()
for workspace in workspaces:
    print(f\"Workspace: {workspace['name']}\")
```

##### `get_datasets(workspace_id: Optional[str] = None)`
Retrieves datasets from a specific workspace.

```python
@rate_limit(max_requests=100, window=3600)
def get_datasets(workspace_id: Optional[str] = None) -> List[Dict[str, Any]]
```

**Parameters:**
- `workspace_id` (Optional[str]): Workspace identifier

**Returns:**
- `List[Dict[str, Any]]`: List of dataset information

**Example:**
```python
datasets = client.get_datasets(workspace_id=\"abc-123\")
```

##### `upload_dataset(dataset_name: str, file_path: str)`
Uploads a dataset to PowerBI Service.

```python
def upload_dataset(dataset_name: str, file_path: str) -> Dict[str, Any]
```

**Parameters:**
- `dataset_name` (str): Name for the dataset
- `file_path` (str): Path to the data file

**Returns:**
- `Dict[str, Any]`: Upload result information

**Example:**
```python
result = client.upload_dataset(\"Population Data\", \"data/population.csv\")
```

#### 🚦 Rate Limiting
- **Limit**: 100 requests per hour
- **Enforcement**: Method-level rate limiting
- **Identifier**: Unique per API endpoint

#### 🔑 Authentication Requirements
- **Client ID**: Azure AD app registration
- **Client Secret**: App registration secret
- **Tenant ID**: Azure AD tenant identifier

---

## 📈 Tableau API Client

### 📝 Class: `TableauAPIClient`

Client for Tableau Server integration.

#### 🔧 Initialization
```python
from src.api.tableau_api import TableauAPIClient

# Initialize client
client = TableauAPIClient()
```

#### 🔍 Methods

##### `connect(server_url: str, username: str, password: str)`
Connects to Tableau Server.

```python
def connect(server_url: str, username: str, password: str) -> bool
```

**Parameters:**
- `server_url` (str): Tableau Server URL
- `username` (str): Username
- `password` (str): Password

**Returns:**
- `bool`: True if connection successful

##### `publish_data_source(name: str, file_path: str)`
Publishes a data source to Tableau Server.

```python
def publish_data_source(name: str, file_path: str) -> Dict[str, Any]
```

**Parameters:**
- `name` (str): Data source name
- `file_path` (str): Path to data file

**Returns:**
- `Dict[str, Any]`: Publication result

---

## 🔄 Data Converters

### 📝 Class: `IstatXMLToPowerBIConverter`

Converts ISTAT XML data to PowerBI-compatible formats.

#### 🔧 Initialization
```python
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter

converter = IstatXMLToPowerBIConverter()
```

#### 🔍 Methods

##### `convert_xml_to_powerbi(xml_input, dataset_id, dataset_name)`
Main conversion method for PowerBI formats.

```python
def convert_xml_to_powerbi(
    xml_input: Union[str, Path],
    dataset_id: str,
    dataset_name: str
) -> Dict[str, Any]
```

**Parameters:**
- `xml_input` (Union[str, Path]): XML content or file path
- `dataset_id` (str): Dataset identifier
- `dataset_name` (str): Human-readable dataset name

**Returns:**
- `Dict[str, Any]`: Conversion result with file paths and metadata

**Example:**
```python
result = converter.convert_xml_to_powerbi(
    xml_input=\"<xml>...</xml>\",
    dataset_id=\"DCIS_POPRES1\",
    dataset_name=\"Popolazione residente\"
)

print(f\"Success: {result['success']}\")
print(f\"Files created: {result['files_created']}\")
```

**Return Structure:**
```python
{
    \"success\": bool,
    \"files_created\": {
        \"csv_file\": str,
        \"excel_file\": str,
        \"parquet_file\": str,
        \"json_file\": str
    },
    \"data_quality\": {
        \"total_rows\": int,
        \"total_columns\": int,
        \"completeness_score\": float,
        \"data_quality_score\": float
    },
    \"summary\": {
        \"dataset_id\": str,
        \"category\": str,
        \"priority\": int,
        \"files_created\": int
    }
}
```

#### 🔍 Internal Methods

##### `_parse_xml_content(xml_content: str)`
Parses XML content into pandas DataFrame.

```python
def _parse_xml_content(xml_content: str) -> pd.DataFrame
```

##### `_categorize_dataset(dataset_id: str, dataset_name: str)`
Automatically categorizes dataset by topic.

```python
def _categorize_dataset(dataset_id: str, dataset_name: str) -> Tuple[str, int]
```

**Returns:**
- `Tuple[str, int]`: (category, priority_score)

**Categories:**
- `popolazione` (Priority: 10)
- `economia` (Priority: 9)
- `lavoro` (Priority: 8)
- `territorio` (Priority: 7)
- `istruzione` (Priority: 6)
- `salute` (Priority: 5)
- `altro` (Priority: 1)

##### `_validate_data_quality(df: pd.DataFrame)`
Validates data quality and completeness.

```python
def _validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Quality metrics and scores

### 📝 Class: `IstatXMLtoTableauConverter`

Converts ISTAT XML data to Tableau-compatible formats.

#### 🔧 Initialization
```python
from src.converters.tableau_converter import IstatXMLtoTableauConverter

converter = IstatXMLtoTableauConverter()
```

#### 🔍 Methods

##### `convert_xml_to_tableau(xml_input, dataset_id, dataset_name)`
Main conversion method for Tableau formats.

```python
def convert_xml_to_tableau(
    xml_input: Union[str, Path],
    dataset_id: str,
    dataset_name: str
) -> Dict[str, Any]
```

**Parameters:** Same as PowerBI converter
**Returns:** Similar structure, optimized for Tableau

---

## 🔒 Security Manager

### 📝 Class: `SecurityManager`

Centralized security management for the application.

#### 🔧 Initialization
```python
from src.utils.security_enhanced import SecurityManager

security = SecurityManager()
```

#### 🔍 Methods

##### `validate_path(path: str, base_dir: Optional[str] = None)`
Validates file paths against security threats.

```python
def validate_path(path: str, base_dir: Optional[str] = None) -> bool
```

**Parameters:**
- `path` (str): File path to validate
- `base_dir` (Optional[str]): Base directory restriction

**Returns:**
- `bool`: True if path is safe

**Example:**
```python
is_safe = security.validate_path(\"/data/user_file.csv\", \"/app/data\")
```

##### `rate_limit(identifier: str, max_requests: int = 100, window: int = 3600)`
Implements rate limiting for requests.

```python
def rate_limit(identifier: str, max_requests: int = 100, window: int = 3600) -> bool
```

**Parameters:**
- `identifier` (str): Unique identifier (IP, user ID, etc.)
- `max_requests` (int): Maximum requests in window
- `window` (int): Time window in seconds

**Returns:**
- `bool`: True if request is allowed

**Example:**
```python
is_allowed = security.rate_limit(\"user_123\", max_requests=50, window=3600)
```

##### `sanitize_input(input_str: str)`
Sanitizes user input to prevent injection attacks.

```python
def sanitize_input(input_str: str) -> str
```

**Parameters:**
- `input_str` (str): Input string to sanitize

**Returns:**
- `str`: Sanitized string

**Example:**
```python
clean_input = security.sanitize_input(user_input)
```

##### `get_security_headers()`
Returns HTTP security headers.

```python
def get_security_headers() -> Dict[str, str]
```

**Returns:**
- `Dict[str, str]`: Security headers

**Example:**
```python
headers = security.get_security_headers()
```

##### `block_ip(ip: str)` / `unblock_ip(ip: str)`
Manages IP blocking.

```python
def block_ip(ip: str) -> None
def unblock_ip(ip: str) -> None
```

#### 🎯 Security Features
- **Path Traversal Protection**: Prevents `../` attacks
- **Windows Reserved Names**: Blocks CON, PRN, AUX, etc.
- **File Extension Validation**: Only allows safe extensions
- **Input Sanitization**: Removes dangerous characters
- **Rate Limiting**: Configurable request limits

---

## 🗃️ SQLite Metadata Layer

### 📝 Overview

The SQLite Metadata Layer provides thread-safe, lightweight storage for application metadata, user preferences, API credentials, and audit logging. It implements the metadata portion of the hybrid SQLite + DuckDB architecture (ADR-002).

### 🏗️ Core Components

#### SQLiteMetadataManager
```python
from src.database.sqlite.manager import SQLiteMetadataManager

# Initialize with default configuration
manager = SQLiteMetadataManager()

# Register a new dataset with metadata
manager.register_dataset(
    dataset_id="DCIS_POPRES1",
    name="Popolazione residente",
    category="popolazione",
    source="ISTAT SDMX",
    metadata={"last_updated": "2025-07-23", "quality": 0.95}
)

# Store user preferences with encryption
manager.set_user_preference(
    user_id="user123",
    key="dashboard_layout",
    value={"widgets": ["chart1", "table2"]},
    encrypted=True
)

# Store API credentials securely
manager.store_api_credentials(
    service_name="istat_api",
    api_key="secret_key_123",
    encrypted=True
)
```

#### Database Schema
The SQLite metadata layer includes 6 optimized tables:

```sql
-- Dataset registry for ISTAT dataset metadata
CREATE TABLE dataset_registry (
    dataset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT DEFAULT 'ISTAT',
    metadata TEXT,  -- JSON metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- User preferences with encryption support
CREATE TABLE user_preferences (
    pref_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    preference_key TEXT NOT NULL,
    preference_value TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- Secure API credential storage
CREATE TABLE api_credentials (
    credential_id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT UNIQUE NOT NULL,
    api_key TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Comprehensive audit logging
CREATE TABLE audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    table_name TEXT,
    record_id TEXT,
    user_id TEXT,
    details TEXT,  -- JSON details
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- System configuration management
CREATE TABLE system_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    config_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Schema migration tracking
CREATE TABLE schema_migrations (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 🔒 Security Features

#### Enhanced Data Protection
- **Fernet Encryption**: Secure encryption for sensitive preferences and API credentials
- **Thread-Safe Operations**: Connection pooling with proper locking mechanisms
- **SQL Injection Prevention**: Parameterized queries throughout the codebase
- **Audit Trail**: Complete operation logging with user tracking

#### Input Validation
```python
# Automatic input validation and sanitization
manager.register_dataset(
    dataset_id="DCIS_POPRES1",  # Validated format
    name="Popolazione residente",  # HTML-escaped
    category="popolazione",  # Enum validation
    metadata={"validated": True}  # JSON schema validation
)
```

### ⚡ Performance Features

#### Optimized Operations
- **Connection Pooling**: Reuses connections for better performance
- **Prepared Statements**: Pre-compiled queries for faster execution
- **Batch Operations**: Efficient bulk insert/update operations
- **Index Optimization**: Strategic indexes on frequently queried columns

```python
# Batch operations for better performance
datasets = [
    {"dataset_id": "DCIS_POPRES1", "name": "Popolazione", "category": "popolazione"},
    {"dataset_id": "DCIS_EMPLO1", "name": "Occupazione", "category": "lavoro"},
]
manager.batch_register_datasets(datasets)
```

### 🔄 Unified Data Repository

#### Repository Pattern Implementation
```python
from src.database.sqlite.repository import UnifiedDataRepository

# Single interface for both SQLite and DuckDB
repo = UnifiedDataRepository()

# Register dataset with complete metadata and analytics setup
repo.register_dataset_complete(
    dataset_id="DCIS_POPRES1",
    name="Popolazione residente",
    category="popolazione",
    analytics_data=dataframe  # Automatically routed to DuckDB
)

# Execute analytics queries (routed to DuckDB)
results = repo.execute_analytics_query(
    "SELECT territorio, SUM(valore) FROM istat.observations WHERE anno = ? GROUP BY territorio",
    params=[2023]
)

# Retrieve metadata (routed to SQLite)
metadata = repo.get_dataset_metadata("DCIS_POPRES1")
```

#### Intelligent Operation Routing
- **Metadata Operations**: Automatically routed to SQLite
- **Analytics Queries**: Automatically routed to DuckDB
- **Transaction Coordination**: Cross-database transaction support
- **Caching Layer**: TTL-based cache for frequently accessed data

### 📊 Usage Examples

#### Complete Metadata Management
```python
from src.database.sqlite import SQLiteMetadataManager
from src.utils.security_enhanced import SecurityManager

# Initialize components
metadata_manager = SQLiteMetadataManager()
security = SecurityManager()

# 1. Register dataset with audit logging
dataset_info = metadata_manager.register_dataset(
    dataset_id="DCIS_POPRES1",
    name="Popolazione residente per comune",
    category="popolazione",
    source="ISTAT SDMX API",
    metadata={
        "description": "Dati popolazione residente italiana",
        "update_frequency": "annual",
        "last_check": "2025-07-23T10:30:00"
    }
)

# 2. Store user dashboard preferences (encrypted)
metadata_manager.set_user_preference(
    user_id="andrea.bozzo",
    key="dashboard_config",
    value={
        "theme": "dark",
        "auto_refresh": True,
        "favorite_datasets": ["DCIS_POPRES1", "DCIS_EMPLO1"]
    },
    encrypted=True
)

# 3. Secure API credential storage
metadata_manager.store_api_credentials(
    service_name="powerbi_service",
    api_key=security.encrypt_data("secret_powerbi_key_123"),
    encrypted=True
)

# 4. Query operations with automatic audit logging
preferences = metadata_manager.get_user_preferences("andrea.bozzo")
datasets = metadata_manager.get_datasets_by_category("popolazione")

# 5. Review audit trail
audit_logs = metadata_manager.get_audit_logs(
    operation="dataset_registered",
    start_date="2025-07-23"
)
```

### 🧪 Testing

The SQLite metadata layer includes comprehensive test coverage:
- **22 Unit Tests**: Complete API coverage with 100% pass rate
- **Thread Safety Tests**: Concurrent operation validation
- **Security Tests**: Encryption and SQL injection prevention
- **Performance Tests**: Benchmarking for metadata operations
- **Integration Tests**: Cross-database operation testing

---

## 🦆 DuckDB Analytics Engine

### 📝 Overview

The DuckDB Analytics Engine provides high-performance data analytics capabilities specifically optimized for ISTAT statistical data processing.

### 🏗️ Core Components

#### DuckDBManager
```python
from src.database.duckdb.manager import DuckDBManager

# Initialize with default configuration
manager = DuckDBManager()

# Execute queries with automatic error handling
result = manager.execute_query("SELECT * FROM dataset_metadata LIMIT 10")

# Bulk insert with optimized performance
manager.bulk_insert("istat.observations", dataframe)
```

#### SimpleDuckDBAdapter
```python
from src.database.duckdb.simple_adapter import SimpleDuckDBAdapter

# Create lightweight adapter
adapter = SimpleDuckDBAdapter(":memory:")
adapter.create_istat_schema()

# Insert and query data
adapter.insert_observations(df)
summary = adapter.get_dataset_summary()
```

### 🔒 Security Features

#### Enhanced SQL Injection Protection
- **Table Name Validation**: Strict alphanumeric checks for all table names
- **Parameterized Queries**: All user data operations use prepared statements
- **Input Sanitization**: Comprehensive validation of database identifiers

#### Type Safety
- **100% MyPy Compliance**: All modules pass strict type checking
- **Runtime Safety**: Proper error handling with meaningful exceptions
- **Connection Safety**: Robust connection lifecycle management

### ⚡ Performance Features

#### Query Optimization
```python
from src.database.duckdb.query_optimizer import QueryOptimizer

optimizer = QueryOptimizer()
optimizer.create_advanced_indexes()

# Optimized time series queries with caching
data = optimizer.get_time_series_data(
    dataset_ids=["DCIS_POPRES1"],
    start_year=2020,
    end_year=2023
)
```

#### Data Partitioning
```python
from src.database.duckdb.partitioning import PartitionManager

partition_manager = PartitionManager()
partition_manager.create_partitioned_tables("hybrid")

# Automatic partition pruning
optimized_query = partition_manager.get_partition_pruning_query(
    base_query="SELECT * FROM istat.observations",
    start_year=2022,
    territories=["IT"]
)
```

### 📊 Usage Examples

#### Complete Data Pipeline
```python
# 1. Initialize components
from src.database.duckdb import DuckDBManager, QueryOptimizer, PartitionManager

manager = DuckDBManager()
optimizer = QueryOptimizer(manager)
partitioner = PartitionManager(manager)

# 2. Create optimized schema
optimizer.create_advanced_indexes()
partitioner.create_partitioned_tables()

# 3. Process data with security validation
secure_data = manager.bulk_insert("istat.datasets_partitioned", df)

# 4. Execute optimized queries
results = optimizer.get_territory_comparison(
    measure_codes=["POP_TOT"],
    year=2023
)
```

### 🧪 Testing

All DuckDB components include comprehensive test coverage:
- **45 Integration Tests**: Complete API coverage
- **Security Tests**: SQL injection and input validation
- **Performance Tests**: Benchmarking and optimization
- **Type Safety Tests**: MyPy compliance verification

---

## 🔄 Circuit Breaker

### 📝 Class: `CircuitBreaker`

Implements circuit breaker pattern for resilient external calls.

#### 🔧 Initialization
```python
from src.utils.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name=\"external_api\"
)
```

#### 🔍 Methods

##### `call(func: Callable, *args, **kwargs)`
Executes a function through the circuit breaker.

```python
def call(func: Callable, *args, **kwargs) -> Any
```

**Parameters:**
- `func` (Callable): Function to execute
- `*args`: Function arguments
- `**kwargs`: Function keyword arguments

**Returns:**
- `Any`: Function result

**Example:**
```python
result = breaker.call(requests.get, \"https://api.example.com/data\")
```

##### `get_stats()`
Returns circuit breaker statistics.

```python
def get_stats() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Circuit breaker statistics

**Example:**
```python
stats = breaker.get_stats()
print(f\"State: {stats['state']}\")
print(f\"Failure rate: {stats['failure_rate']:.2%}\")
```

#### 🎯 Decorator Usage
```python
from src.utils.circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=3, recovery_timeout=30)
def external_api_call():
    return requests.get(\"https://api.example.com/data\")
```

#### 🔄 States
- **CLOSED**: Normal operation
- **OPEN**: Rejecting calls due to failures
- **HALF_OPEN**: Testing if service has recovered

---

## 🔍 Analyzers

### 📝 Class: `DataflowAnalyzer`

Analyzes and categorizes ISTAT dataflows.

#### 🔧 Initialization
```python
from src.analyzers.dataflow_analyzer import DataflowAnalyzer

analyzer = DataflowAnalyzer()
```

#### 🔍 Methods

##### `analyze_dataflows()`
Analyzes all available ISTAT dataflows.

```python
def analyze_dataflows() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Analysis results with categorization

##### `categorize_by_topic(dataflow_info: Dict)`
Categorizes a dataflow by topic.

```python
def categorize_by_topic(dataflow_info: Dict) -> Tuple[str, int]
```

**Parameters:**
- `dataflow_info` (Dict): Dataflow information

**Returns:**
- `Tuple[str, int]`: (category, priority)

---

## 🛠️ Utilities

### 📝 Configuration (`src.utils.config`)

```python
from src.utils.config import Config

# Access configuration
api_url = Config.ISTAT_API_BASE_URL
timeout = Config.ISTAT_API_TIMEOUT
```

### 📋 Logging (`src.utils.logger`)

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info(\"Processing data\")
```

### 📁 Secure Path (`src.utils.secure_path`)

```python
from src.utils.secure_path import SecurePathValidator

validator = SecurePathValidator(\"/app/data\")
is_safe = validator.validate_path(\"/app/data/user_file.csv\")
```

---

## ⚠️ Error Handling

### 🚨 Exception Types

#### `RateLimitExceeded`
Raised when rate limit is exceeded.

```python
try:
    result = api_call()
except RateLimitExceeded as e:
    print(f\"Rate limit exceeded: {e}\")
```

#### `CircuitBreakerError`
Raised when circuit breaker is open.

```python
try:
    result = breaker.call(external_function)
except CircuitBreakerError as e:
    print(f\"Circuit breaker open: {e}\")
```

#### `ValidationError`
Raised for invalid inputs or paths.

```python
try:
    security.validate_path(\"../invalid/path\")
except ValidationError as e:
    print(f\"Validation failed: {e}\")
```

### 🔍 Error Response Format
```python
{
    \"error\": {
        \"type\": \"RateLimitExceeded\",
        \"message\": \"Rate limit exceeded for identifier: user_123\",
        \"details\": {
            \"identifier\": \"user_123\",
            \"limit\": 100,
            \"window\": 3600,
            \"retry_after\": 1800
        }
    }
}
```

---

## 🚦 Rate Limiting

### 📊 Rate Limit Configuration

| Service | Limit | Window | Enforcement |
|---------|-------|--------|-------------|
| ISTAT API | 50 requests | 1 hour | Decorator |
| PowerBI API | 100 requests | 1 hour | Method-level |
| Tableau API | 50 requests | 1 hour | Method-level |
| Security Manager | Configurable | Configurable | Instance-level |

### 🎯 Rate Limit Headers
```python
{
    \"X-RateLimit-Limit\": \"100\",
    \"X-RateLimit-Remaining\": \"75\",
    \"X-RateLimit-Reset\": \"1642607200\",
    \"X-RateLimit-Window\": \"3600\"
}
```

---

## 📚 Examples

### 🎯 Complete Data Processing Pipeline

```python
from src.api.istat_api import IstatAPITester
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter
from src.utils.security_enhanced import SecurityManager

# Initialize components
api_client = IstatAPITester()
converter = IstatXMLToPowerBIConverter()
security = SecurityManager()

# Validate and sanitize dataset ID
dataset_id = security.sanitize_input(\"DCIS_POPRES1\")

# Check rate limit
if not security.rate_limit(\"user_123\", max_requests=50, window=3600):
    raise Exception(\"Rate limit exceeded\")

# Fetch data
xml_data = api_client.fetch_dataset_data(dataset_id)

# Convert to PowerBI format
result = converter.convert_xml_to_powerbi(
    xml_input=xml_data,
    dataset_id=dataset_id,
    dataset_name=\"Popolazione residente\"
)

# Process results
if result[\"success\"]:
    print(f\"Conversion successful!\")
    print(f\"Files created: {result['files_created']}\")
    print(f\"Data quality: {result['data_quality']['completeness_score']:.2%}\")
else:
    print(f\"Conversion failed: {result['error']}\")
```

### 🔒 Security-Enhanced API Call

```python
from src.utils.security_enhanced import SecurityManager, rate_limit
from src.utils.circuit_breaker import circuit_breaker

security = SecurityManager()

@rate_limit(max_requests=100, window=3600)
@circuit_breaker(failure_threshold=5, recovery_timeout=60)
def secure_api_call(endpoint: str, params: dict):
    # Validate endpoint
    if not security.validate_path(endpoint):
        raise ValueError(\"Invalid endpoint\")

    # Sanitize parameters
    clean_params = {
        key: security.sanitize_input(str(value))
        for key, value in params.items()
    }

    # Make API call
    response = requests.get(endpoint, params=clean_params)
    return response.json()

# Usage
try:
    data = secure_api_call(\"/api/data\", {\"category\": \"population\"})
    print(data)
except Exception as e:
    print(f\"API call failed: {e}\")
```

### 📊 Dashboard Data Loading

```python
import streamlit as st
from src.api.istat_api import IstatAPITester
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter

@st.cache_data(ttl=3600)
def load_dashboard_data(category: str):
    \"\"\"Load and cache dashboard data for a specific category.\"\"\"

    # Initialize components
    api_client = IstatAPITester()
    converter = IstatXMLToPowerBIConverter()

    # Get datasets for category
    datasets = api_client.get_datasets_by_category(category)

    processed_data = []
    for dataset in datasets[:5]:  # Limit to 5 datasets
        try:
            # Fetch and convert data
            xml_data = api_client.fetch_dataset_data(dataset[\"id\"])
            result = converter.convert_xml_to_powerbi(
                xml_input=xml_data,
                dataset_id=dataset[\"id\"],
                dataset_name=dataset[\"name\"]
            )

            if result[\"success\"]:
                processed_data.append(result)

        except Exception as e:
            st.error(f\"Error processing {dataset['name']}: {e}\")

    return processed_data

# Usage in Streamlit
category = st.selectbox(\"Select Category\", [\"popolazione\", \"economia\", \"lavoro\"])
data = load_dashboard_data(category)
st.dataframe(data)
```

---

## 🔧 Configuration

### 🌐 Environment Variables

```bash
# ISTAT API Configuration
ISTAT_API_BASE_URL=https://sdmx.istat.it/SDMXWS/rest/
ISTAT_API_TIMEOUT=30

# PowerBI Configuration
POWERBI_CLIENT_ID=your_client_id
POWERBI_CLIENT_SECRET=your_client_secret
POWERBI_TENANT_ID=your_tenant_id
POWERBI_WORKSPACE_ID=your_workspace_id

# Tableau Configuration
TABLEAU_SERVER_URL=https://your-tableau-server.com
TABLEAU_USERNAME=your_username
TABLEAU_PASSWORD=your_password

# Security Configuration
SECURITY_RATE_LIMIT_REQUESTS=100
SECURITY_RATE_LIMIT_WINDOW=3600
SECURITY_BLOCKED_IPS=192.168.1.100,10.0.0.50

# Application Configuration
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_TTL=3600
```

### ⚙️ Configuration File

```python
# config.py
import os

class Config:
    # ISTAT API
    ISTAT_API_BASE_URL = os.getenv(\"ISTAT_API_BASE_URL\", \"https://sdmx.istat.it/SDMXWS/rest/\")
    ISTAT_API_TIMEOUT = int(os.getenv(\"ISTAT_API_TIMEOUT\", \"30\"))

    # PowerBI
    POWERBI_CLIENT_ID = os.getenv(\"POWERBI_CLIENT_ID\")
    POWERBI_CLIENT_SECRET = os.getenv(\"POWERBI_CLIENT_SECRET\")
    POWERBI_TENANT_ID = os.getenv(\"POWERBI_TENANT_ID\")

    # Security
    SECURITY_RATE_LIMIT_REQUESTS = int(os.getenv(\"SECURITY_RATE_LIMIT_REQUESTS\", \"100\"))
    SECURITY_RATE_LIMIT_WINDOW = int(os.getenv(\"SECURITY_RATE_LIMIT_WINDOW\", \"3600\"))
```

---

## 📈 Performance Considerations

### ⚡ Optimization Tips

1. **Use Caching**: Cache API responses and converted data
2. **Batch Operations**: Process multiple datasets together
3. **Async Processing**: Use async for I/O-bound operations
4. **Connection Pooling**: Reuse HTTP connections
5. **Data Formats**: Use Parquet for large datasets

### 📊 Performance Metrics

```python
# Example performance monitoring
import time
from src.utils.logger import get_logger

logger = get_logger(__name__)

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger.info(f\"{func.__name__} took {end_time - start_time:.2f} seconds\")
        return result
    return wrapper

@monitor_performance
def process_dataset(dataset_id):
    # Your processing logic
    pass
```

---

## 🎯 Best Practices

### 🔒 Security Best Practices

1. **Always Validate Input**: Use SecurityManager for all user inputs
2. **Implement Rate Limiting**: Protect against abuse
3. **Use Circuit Breakers**: Handle external service failures
4. **Log Security Events**: Monitor suspicious activities
5. **Regular Security Audits**: Keep dependencies updated

### 📊 Data Processing Best Practices

1. **Validate Data Quality**: Check completeness and consistency
2. **Handle Large Datasets**: Use streaming for large files
3. **Error Recovery**: Implement robust error handling
4. **Monitoring**: Track processing metrics
5. **Testing**: Comprehensive test coverage

### 🚀 Performance Best Practices

1. **Cache Strategically**: Cache expensive operations
2. **Optimize Queries**: Use efficient data access patterns
3. **Monitor Memory**: Track memory usage in long-running processes
4. **Profile Code**: Regular performance profiling
5. **Scale Horizontally**: Design for horizontal scaling

---

## 🛠️ Development & Testing

### 🧪 Testing API Components

```python
import pytest
from unittest.mock import Mock, patch
from src.api.istat_api import IstatAPITester

class TestIstatAPI:
    def setup_method(self):
        self.client = IstatAPITester()

    @patch('requests.Session.get')
    def test_fetch_dataset_data(self, mock_get):
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = \"<xml>test data</xml>\"
        mock_get.return_value = mock_response

        # Test API call
        result = self.client.fetch_dataset_data(\"DCIS_POPRES1\")

        assert result == \"<xml>test data</xml>\"
        mock_get.assert_called_once()
```

### 🔍 Debugging

```python
import logging
from src.utils.logger import get_logger

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)

# Debug API calls
logger.debug(f\"Making API call to {endpoint}\")
logger.debug(f\"Parameters: {params}\")
```

---

## 📋 API Changelog

### Version 1.0.0 (January 2025)
- ✅ Initial API release
- ✅ ISTAT API client with rate limiting
- ✅ PowerBI API client with OAuth
- ✅ Tableau API client
- ✅ Security Manager implementation
- ✅ Circuit Breaker pattern
- ✅ Data converters for multiple formats
- ✅ Comprehensive error handling

### Planned Features
- 🔄 REST API endpoints
- 🔄 WebSocket support for real-time data
- 🔄 GraphQL API
- 🔄 Batch processing API
- 🔄 Webhook support

---

## 🔗 Related Documentation

- **[README.md](README.md)**: Project overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture
- **[PROJECT_AUDIT.md](PROJECT_AUDIT.md)**: Project audit
- **[STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)**: Deployment guide

---

## 📞 Support

For API support and questions:
- **GitHub Issues**: [Report issues](https://github.com/AndreaBozzo/Osservatorio/issues)
- **Documentation**: [Project documentation](https://github.com/AndreaBozzo/Osservatorio)
- **Live Dashboard**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)

---

**📈 API Status**: ✅ **Production Ready** | 🔄 **Actively Maintained** | 🚀 **Feature Complete**

*Last updated: January 18, 2025*
