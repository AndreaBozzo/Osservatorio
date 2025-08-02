# 🚀 FastAPI REST API Documentation

> **Production-ready REST API for Osservatorio ISTAT Data Platform**
> **Version**: 10.4.0
> **Issue**: #74 Performance Testing Suite Implementation Complete
> **Date**: July 30, 2025

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Quick Start](#-quick-start)
3. [Authentication](#-authentication)
4. [API Endpoints](#-api-endpoints)
5. [OData v4 Integration](#-odata-v4-integration)
6. [Error Handling](#-error-handling)
7. [Performance Monitoring](#-performance-monitoring)
8. [Rate Limiting](#-rate-limiting)
9. [Security Features](#-security-features)
10. [Production Deployment](#-production-deployment)

---

## 🎯 Overview

The Osservatorio FastAPI REST API provides comprehensive access to Italian statistical data from ISTAT with enterprise-grade features:

### 🏗️ Architecture Features
- **JWT Authentication**: Secure API key-based authentication with scope-based access control
- **OData v4 Endpoint**: Direct PowerBI integration with real-time Direct Query
- **Production ISTAT Client**: Circuit breaker pattern with quality validation
- **Rate Limiting**: Configurable per-API-key rate limiting with SQLite persistence
- **Audit Logging**: Complete request tracking and usage analytics
- **Performance Monitoring**: Built-in performance metrics and SLA monitoring

### 📊 Performance Targets
- **Dataset List**: <100ms for 1000 datasets
- **Dataset Detail**: <200ms with data included
- **OData Query**: <500ms for 10k records
- **Authentication**: <50ms per request

---

## 🚀 Quick Start

### 1. Start the Server

```bash
# Development
python -m src.api.fastapi_app

# Production with Uvicorn
uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4

# With environment configuration
JWT_SECRET_KEY=your-secret python -m src.api.fastapi_app
```

### 2. Access Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 3. Health Check

```bash
curl http://localhost:8000/health
```

---

## 🔐 Authentication

### JWT Token-Based Authentication

The API uses JWT tokens generated from API keys with scope-based access control.

#### 1. Generate API Key

```python
from scripts.generate_api_key import main
# Creates API key with specified scopes
```

#### 2. Create JWT Token

```bash
# Using the /auth/token endpoint (requires admin scope)
curl -X POST "http://localhost:8000/auth/token" \
  -H "Authorization: Bearer admin-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "scopes": ["read", "datasets", "odata"],
    "rate_limit": 1000
  }'
```

#### 3. Use JWT Token

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/datasets
```

### Available Scopes

| Scope | Description | Endpoints |
|-------|-------------|-----------|
| `read` | Read access to public data | `/health`, `/odata/$metadata` |
| `datasets` | Dataset access | `/datasets`, `/datasets/{id}` |
| `odata` | OData endpoint access | `/odata/Datasets`, `/odata/*` |
| `admin` | Administrative access | `/auth/*`, `/analytics/usage` |
| `write` | Write operations | Data synchronization endpoints |

---

## 📊 API Endpoints

### System Endpoints

#### `GET /health`
Health check endpoint with system status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "sqlite_metadata": {"status": "operational"},
    "duckdb_analytics": {"status": "operational"}
  }
}
```

### Dataset Endpoints

#### `GET /datasets`
List datasets with filtering and pagination.

**Authentication:** Required (`datasets` scope)

**Parameters:**
- `category` (optional): Filter by dataset category
- `with_analytics` (optional): Filter by analytics data presence
- `page` (default: 1): Page number
- `page_size` (default: 50): Page size
- `include_metadata` (default: false): Include dataset metadata

**Response:**
```json
{
  "datasets": [
    {
      "dataset_id": "DCIS_POPRES1",
      "name": "Popolazione residente",
      "category": "popolazione",
      "has_analytics_data": true,
      "priority": 10
    }
  ],
  "total_count": 500,
  "page": 1,
  "page_size": 50,
  "has_next": true
}
```

#### `GET /datasets/{dataset_id}`
Get detailed information about a specific dataset.

**Authentication:** Required (`datasets` scope)

**Parameters:**
- `include_data` (default: false): Include actual data observations
- `limit` (optional): Limit number of observations

**Response:**
```json
{
  "dataset": {
    "dataset_id": "DCIS_POPRES1",
    "name": "Popolazione residente",
    "category": "popolazione",
    "analytics_stats": {
      "total_observations": 50000,
      "date_range": ["2020", "2023"]
    }
  },
  "data": [
    {
      "territory": "IT",
      "year": 2023,
      "value": 59030133
    }
  ]
}
```

#### `GET /datasets/{dataset_id}/timeseries`
Get time series data for a dataset with flexible filtering.

**Authentication:** Required (`datasets` scope)

**Parameters:**
- `territory_code` (optional): Filter by territory code
- `measure_code` (optional): Filter by measure code
- `start_year` (optional): Start year filter
- `end_year` (optional): End year filter

### Authentication Endpoints

#### `POST /auth/token`
Create a new API key and JWT token.

**Authentication:** Required (`admin` scope)

**Request:**
```json
{
  "name": "My Application",
  "scopes": ["read", "datasets", "odata"],
  "rate_limit": 1000,
  "expires_at": "2025-12-31T23:59:59"
}
```

#### `GET /auth/keys`
List all API keys with usage statistics.

**Authentication:** Required (`admin` scope)

### Analytics Endpoints

#### `GET /analytics/usage`
Get usage analytics and statistics.

**Authentication:** Required (`admin` scope)

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `api_key_id` (optional): Filter by API key ID
- `endpoint` (optional): Filter by endpoint

### ISTAT API Integration Endpoints

#### `GET /api/istat/status`
Get current status of the production ISTAT API client.

**Response:**
```json
{
  "client_status": {
    "circuit_breaker_state": "CLOSED",
    "requests_made": 150,
    "success_rate": 0.98
  },
  "api_health": {
    "status": "operational",
    "response_time_ms": 85
  }
}
```

#### `GET /api/istat/dataflows`
List available ISTAT SDMX dataflows.

#### `GET /api/istat/dataset/{dataset_id}`
Fetch specific dataset from ISTAT API.

#### `POST /api/istat/sync/{dataset_id}`
Synchronize ISTAT dataset to local repository.

**Authentication:** Required (`write` scope)

---

## 🔄 OData v4 Integration

### PowerBI Direct Query Support

The API provides full OData v4 compliance for PowerBI Direct Query connections.

#### `GET /odata/$metadata`
OData service metadata document.

**Authentication:** Public (no authentication required)

#### `GET /odata/Datasets`
OData endpoint for dataset entities.

**Authentication:** Required (`odata` scope)

**OData Parameters:**
- `$select`: Select specific fields
- `$filter`: Filter results
- `$orderby`: Sort results
- `$top`: Limit results
- `$skip`: Skip results for pagination

**Example:**
```bash
curl "http://localhost:8000/odata/Datasets?\$filter=category eq 'popolazione'&\$top=10" \
  -H "Authorization: Bearer jwt-token"
```

### PowerBI Connection Setup

1. **Open PowerBI Desktop**
2. **Get Data** → **OData Feed**
3. **URL**: `http://localhost:8000/odata`
4. **Authentication**: API Key → Paste JWT token

---

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "message": null,
  "timestamp": "2025-07-30T11:30:00",
  "error_type": "http_error",
  "error_code": "HTTP_401",
  "detail": "Invalid or expired token",
  "instance": "http://localhost:8000/datasets"
}
```

### HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 200 | Success | Request processed successfully |
| 401 | Unauthorized | Invalid/expired JWT token |
| 403 | Forbidden | Insufficient permissions (scope) |
| 404 | Not Found | Dataset or resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | ISTAT API unavailable |

---

## 📈 Performance Monitoring

### Built-in Metrics

The API includes comprehensive performance monitoring:

#### Response Time Headers
```
X-Process-Time: 45.67
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 899
X-RateLimit-Reset: 1722334800
```

#### Performance Targets & SLA Monitoring

| Endpoint | SLA Target | Monitoring |
|----------|------------|------------|
| `/health` | <50ms | ✅ Real-time |
| `/datasets` | <100ms | ✅ Real-time |
| `/datasets/{id}` | <200ms | ✅ Real-time |
| `/odata/Datasets` | <500ms | ✅ Real-time |
| `/datasets/{id}/timeseries` | <1000ms | ✅ Real-time |

### Performance Testing Suite

**Issue #74 Implementation**: Comprehensive performance testing and load testing suite.

```bash
# Run performance tests
python tests/performance/load_testing/jwt_token_generator.py

# Run API benchmarks
python -c "
from tests.performance.load_testing.api_benchmarks import APIBenchmark
benchmark = APIBenchmark('http://localhost:8000')
result = benchmark.benchmark_endpoint('/datasets', sla_target_ms=100)
print(f'Response time: {result.response_time_ms:.1f}ms')
"

# Run Locust load tests
locust -f tests/performance/load_testing/locustfile.py --host=http://localhost:8000
```

---

## 🚦 Rate Limiting

### Rate Limit Configuration

- **Default Rate Limit**: 100 requests per hour per API key
- **Configurable**: Set custom limits per API key
- **Algorithm**: Sliding window with SQLite persistence
- **Headers**: Standard rate limit headers in responses

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1722334800
```

### Rate Limit Exceeded Response

```json
{
  "error_type": "rate_limit_exceeded",
  "error_code": "HTTP_429",
  "detail": "Rate limit exceeded",
  "retry_after": 3600
}
```

---

## 🔒 Security Features

### Security Headers

The API includes comprehensive security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

### Security Middleware

- **CORS**: Configurable origins with credential support
- **GZip**: Response compression for large payloads
- **Input Validation**: Comprehensive parameter validation
- **SQL Injection Prevention**: Parameterized queries throughout
- **Path Traversal Protection**: Secure file path handling

### Audit Logging

All API requests are logged with:
- User identification (API key)
- Request details (method, endpoint, params)
- Client information (IP, user agent)
- Response metadata (status, processing time)

---

## 🚀 Production Deployment

### Environment Configuration

Create `.env` file:
```bash
# JWT Configuration
JWT_SECRET_KEY=your-production-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS Configuration
CORS_ORIGINS=["https://yourdomain.com", "https://powerbi.microsoft.com"]

# Rate Limiting
DEFAULT_RATE_LIMIT=1000
RATE_LIMIT_WINDOW=3600

# Database Configuration
SQLITE_DB_PATH=/app/data/databases/osservatorio_metadata.db
DUCKDB_DB_PATH=/app/data/databases/osservatorio.duckdb
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY .env .env

EXPOSE 8000
CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Production Checklist

- [ ] Set strong JWT secret key
- [ ] Configure CORS origins appropriately
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper logging levels
- [ ] Set up monitoring and alerting
- [ ] Configure rate limits for production load
- [ ] Set up database backups
- [ ] Configure reverse proxy (nginx/Apache)

---

## 📊 Monitoring & Observability

### Application Metrics

- **Request Count**: Total API requests
- **Response Times**: P50, P95, P99 percentiles
- **Error Rates**: 4xx and 5xx error percentages
- **Authentication**: Login success/failure rates
- **Rate Limiting**: Rate limit violations

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Detailed status
curl -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/istat/status
```

### Performance Dashboards

Use the built-in analytics endpoint for monitoring:

```bash
curl -H "Authorization: Bearer admin-token" \
  "http://localhost:8000/analytics/usage?start_date=2025-07-30"
```

---

## 🔗 Integration Examples

### Python Client

```python
import requests

class OsservatorioClient:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {jwt_token}"}

    def get_datasets(self, category: str = None):
        params = {"category": category} if category else {}
        response = requests.get(
            f"{self.base_url}/datasets",
            headers=self.headers,
            params=params
        )
        return response.json()

# Usage
client = OsservatorioClient("http://localhost:8000", "your-jwt-token")
datasets = client.get_datasets(category="popolazione")
```

### JavaScript/Node.js Client

```javascript
class OsservatorioAPI {
    constructor(baseUrl, jwtToken) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${jwtToken}`,
            'Content-Type': 'application/json'
        };
    }

    async getDatasets(category = null) {
        const params = category ? `?category=${category}` : '';
        const response = await fetch(`${this.baseUrl}/datasets${params}`, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const api = new OsservatorioAPI('http://localhost:8000', 'your-jwt-token');
const datasets = await api.getDatasets('popolazione');
```

---

## 🛠️ Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run development server
python -m src.api.fastapi_app

# Run tests
pytest tests/integration/test_fastapi_istat_endpoints.py -v
```

### Adding New Endpoints

1. **Define endpoint in** `src/api/fastapi_app.py`
2. **Add authentication dependencies**
3. **Implement business logic**
4. **Add error handling**
5. **Write tests**
6. **Update documentation**

---

## 🔄 API Versioning

Current API version: **v1.0.0**

### Version Headers
```
API-Version: 1.0.0
```

### Future Versioning Strategy
- **Path-based**: `/v2/datasets`
- **Header-based**: `Accept: application/vnd.osservatorio.v2+json`
- **Backward compatibility**: Maintained for 2 major versions

---

## 📞 Support & Resources

### Documentation Links
- **[Authentication Guide](../security/AUTHENTICATION.md)**
- **[PowerBI Integration](../integrations/POWERBI_FASTAPI_CONNECTION.md)**
- **[Performance Testing](PERFORMANCE_TESTING_SUITE.md)**
- **[Production ISTAT Client](PRODUCTION_ISTAT_CLIENT.md)**

### Performance Testing
- **Load Testing**: `tests/performance/load_testing/`
- **Benchmarking**: `tests/performance/load_testing/api_benchmarks.py`
- **JWT Generator**: `tests/performance/load_testing/jwt_token_generator.py`

### API Status
- **Version**: 10.4.0 (Issue #74 Complete)
- **Status**: ✅ Production Ready
- **Performance**: ✅ All SLA targets met
- **Security**: ✅ Enterprise-grade JWT authentication
- **Documentation**: ✅ Complete with examples

---

*Last updated: July 30, 2025 - Issue #74 Performance Testing Suite Implementation Complete*
