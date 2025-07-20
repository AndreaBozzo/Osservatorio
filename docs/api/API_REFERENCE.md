# 🔌 Osservatorio API Reference

> **Comprehensive API documentation for the Osservatorio ISTAT data processing platform**
> **Version**: 1.0.0
> **Date**: January 18, 2025
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
8. [Circuit Breaker](#-circuit-breaker)
9. [Analyzers](#-analyzers)
10. [Utilities](#-utilities)
11. [Error Handling](#-error-handling)
12. [Rate Limiting](#-rate-limiting)
13. [Examples](#-examples)

---

## 🎯 Overview

The Osservatorio API provides programmatic access to Italian statistical data processing, conversion, and visualization capabilities. The API is designed with **security-first principles** and includes comprehensive **rate limiting**, **input validation**, and **error handling**.

### 🏗️ Architecture
- **Modular Design**: Each component is independently testable
- **Security Integration**: Built-in security at every layer
- **Rate Limiting**: Configurable limits for all external calls
- **Circuit Breaker**: Automatic failure recovery
- **Type Safety**: Full type hints for better IDE support

### 📊 Supported Data Sources
- **ISTAT SDMX API**: 509+ Italian statistical datasets
- **PowerBI Service**: Workspace and dataset management
- **Tableau Server**: Data source and dashboard management

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

