# Production ISTAT Client API Documentation

## Overview

The `ProductionIstatClient` is a production-ready ISTAT SDMX API client that replaces the exploration-focused `IstatAPITester`. It provides robust, fault-tolerant access to Italian statistical data with comprehensive integration capabilities.

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   FastAPI Endpoints │    │ ProductionIstatClient│    │   ISTAT SDMX API    │
│                     │───▶│                      │───▶│                     │
│ JWT + Rate Limiting │    │ Circuit Breaker      │    │ https://sdmx.istat.it│
└─────────────────────┘    │ Connection Pooling   │    └─────────────────────┘
                           │ Retry Logic          │              │
┌─────────────────────┐    │ Quality Validation   │              │
│ UnifiedRepository   │◀───│ Async Batch Support  │              │
│ SQLite + DuckDB     │    └──────────────────────┘              │
└─────────────────────┘                                          │
                                                                  ▼
                           ┌──────────────────────────────────────────┐
                           │           Monitoring & Metrics           │
                           │  • Response times   • Success/failure    │
                           │  • Circuit breaker  • Rate limiting      │
                           └──────────────────────────────────────────┘
```

## Key Features

### 🔄 **Fault Tolerance**
- **Circuit Breaker**: Prevents cascade failures (5 failure threshold, 60s recovery)
- **Connection Pooling**: Efficient HTTP connections with retry logic
- **Rate Limiting**: Client-side + security manager coordination
- **Graceful Degradation**: Continues operating during partial failures

### 🚀 **Performance**
- **Async Batch Processing**: Concurrent dataset operations with semaphore control
- **Connection Reuse**: HTTP/1.1 keep-alive with pool management
- **Response Caching**: Intelligent caching for metadata operations
- **Metrics Tracking**: Real-time performance monitoring

### 🔐 **Production Ready**
- **Repository Integration**: Direct SQLite + DuckDB coordination
- **JWT Authentication**: Seamless FastAPI integration
- **Quality Validation**: Built-in data scoring and validation
- **Structured Logging**: Comprehensive error reporting and monitoring

## API Reference

### Core Classes

#### `ProductionIstatClient`

Main client class providing production-ready ISTAT API access.

```python
from src.api.production_istat_client import ProductionIstatClient

# Initialize with repository integration
client = ProductionIstatClient(repository=repository)

# Basic initialization
client = ProductionIstatClient()
```

**Constructor Parameters:**
- `repository` (optional): `UnifiedDataRepository` instance for data storage integration

#### Status Enums and Data Classes

```python
from src.api.production_istat_client import (
    ClientStatus,      # HEALTHY, DEGRADED, CIRCUIT_OPEN, MAINTENANCE
    BatchResult,       # Batch processing results
    QualityResult,     # Data quality validation results  
    SyncResult         # Repository synchronization results
)
```

### Core Methods

#### `get_status() -> Dict[str, Any]`

Get current client operational status and metrics.

```python
status = client.get_status()
print(f"Status: {status['status']}")
print(f"Circuit Breaker: {status['circuit_breaker_state']}")
print(f"Rate Limit Remaining: {status['rate_limit_remaining']}")
print(f"Total Requests: {status['metrics']['total_requests']}")
```

**Returns:**
```json
{
  "status": "healthy",
  "circuit_breaker_state": "closed",
  "rate_limit_remaining": 95,
  "metrics": {
    "total_requests": 42,
    "successful_requests": 40,
    "failed_requests": 2,
    "average_response_time": 0.25,
    "last_request_time": "2025-07-29T10:30:45"
  }
}
```

#### `fetch_dataflows(limit: Optional[int] = None) -> Dict[str, Any]`

Fetch available ISTAT SDMX dataflows.

```python
# Get all dataflows
dataflows = client.fetch_dataflows()

# Limit results
dataflows = client.fetch_dataflows(limit=10)
```

**Returns:**
```json
{
  "dataflows": [
    {
      "id": "DCIS_POPRES1",
      "name": "Popolazione residente",
      "agency": "IT1",
      "version": "1.0"
    }
  ],
  "total_count": 150,
  "timestamp": "2025-07-29T10:30:45"
}
```

#### `fetch_dataset(dataset_id: str, include_data: bool = True) -> Dict[str, Any]`

Fetch specific dataset with structure and optional data.

```python
# Fetch with data
result = client.fetch_dataset("DCIS_POPRES1", include_data=True)

# Structure only
result = client.fetch_dataset("DCIS_POPRES1", include_data=False)
```

**Returns:**
```json
{
  "dataset_id": "DCIS_POPRES1",
  "timestamp": "2025-07-29T10:30:45",
  "structure": {
    "status": "success",
    "content_type": "application/xml",
    "size": 15420
  },
  "data": {
    "status": "success", 
    "content_type": "application/xml",
    "size": 125340,
    "observations_count": 1250
  }
}
```

#### `async fetch_dataset_batch(dataset_ids: List[str]) -> BatchResult`

Fetch multiple datasets concurrently.

```python
import asyncio

dataset_ids = ["DCIS_POPRES1", "DCIS_POPSTRRES1", "DCIS_FECONDITA"]
result = await client.fetch_dataset_batch(dataset_ids)

print(f"Successful: {len(result.successful)}")
print(f"Failed: {len(result.failed)}")
print(f"Total time: {result.total_time:.2f}s")
```

**Returns:**
- `BatchResult` with successful/failed dataset lists and timing information

#### `fetch_with_quality_validation(dataset_id: str) -> QualityResult`

Fetch dataset with integrated quality validation.

```python
quality = client.fetch_with_quality_validation("DCIS_POPRES1")

print(f"Quality Score: {quality.quality_score}/100")
print(f"Completeness: {quality.completeness}%") 
print(f"Validation Errors: {len(quality.validation_errors)}")
```

**Returns:**
- `QualityResult` with scoring metrics and validation details

#### `sync_to_repository(dataset_data: Dict) -> SyncResult`

Synchronize dataset to unified repository.

```python
# Fetch dataset first
dataset_result = client.fetch_dataset("DCIS_POPRES1")

# Sync to repository  
sync_result = client.sync_to_repository(dataset_result)

print(f"Records synced: {sync_result.records_synced}")
print(f"Metadata updated: {sync_result.metadata_updated}")
```

**Returns:**
- `SyncResult` with synchronization metrics and timing

#### `health_check() -> Dict[str, Any]`

Perform health check on ISTAT API connectivity.

```python
health = client.health_check()

if health["status"] == "healthy":
    print(f"API responsive in {health['response_time']:.2f}s")
else:
    print(f"API unhealthy: {health['error']}")
```

## FastAPI Integration

The production client is exposed through FastAPI endpoints with JWT authentication:

### Endpoints

#### `GET /api/istat/status`
Get client status and health metrics.

**Authentication:** Required (JWT)  
**Rate Limit:** Applied

```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
     http://localhost:8000/api/istat/status
```

#### `GET /api/istat/dataflows?limit=10`
List available ISTAT dataflows.

**Parameters:**
- `limit` (optional): Maximum number of dataflows to return (1-100)

#### `GET /api/istat/dataset/{dataset_id}?include_data=true&with_quality=false`
Fetch specific dataset.

**Parameters:**
- `include_data`: Include dataset data in response (default: true)
- `with_quality`: Include quality validation (default: false)

#### `POST /api/istat/sync/{dataset_id}`
Synchronize dataset to repository.

**Authentication:** Required (Write permissions)  
**Returns:** Sync results and dataset information

## Error Handling

### Circuit Breaker States

1. **Closed** (Normal): All requests proceed normally
2. **Open** (Fault): Requests fail immediately, API is unavailable  
3. **Half-Open** (Recovery): Limited requests allowed to test recovery

### Error Types

```python
try:
    result = client.fetch_dataset("INVALID_DATASET")
except Exception as e:
    if "Circuit breaker is open" in str(e):
        # Handle circuit breaker fault
        print("API temporarily unavailable")
    elif "Rate limit exceeded" in str(e):
        # Handle rate limiting
        print("Too many requests, slow down")
    else:
        # Handle other errors
        print(f"API error: {e}")
```

### Retry Logic

- **Automatic retries**: 3 attempts with exponential backoff
- **Retryable status codes**: 429, 500, 502, 503, 504
- **Connection pooling**: Maintains persistent connections
- **Timeout handling**: 30s default, 60s for data requests

## Performance Guidelines

### Best Practices

1. **Use batch operations** for multiple datasets:
   ```python
   # ✅ Good - concurrent processing
   result = await client.fetch_dataset_batch(dataset_ids)
   
   # ❌ Avoid - sequential processing
   for dataset_id in dataset_ids:
       result = client.fetch_dataset(dataset_id)
   ```

2. **Monitor circuit breaker status**:
   ```python
   status = client.get_status()
   if status["circuit_breaker_state"] != "closed":
       # Wait before making requests
       time.sleep(60)
   ```

3. **Respect rate limits**:
   ```python
   status = client.get_status()
   if status["rate_limit_remaining"] < 10:
       # Slow down or wait
       time.sleep(300)  # 5 minutes
   ```

### Performance Targets

- **Metadata operations**: < 100ms
- **Dataset fetch**: < 500ms for typical datasets
- **Batch processing**: 5 concurrent requests max
- **Circuit breaker recovery**: 60 seconds
- **Rate limit**: 100 requests/hour

## Integration Examples

### Basic Usage

```python
from src.api.production_istat_client import ProductionIstatClient
from src.database.sqlite.repository import get_unified_repository

# Initialize with repository
repository = get_unified_repository()
client = ProductionIstatClient(repository=repository)

# Check health
health = client.health_check()
if health["status"] != "healthy":
    raise Exception(f"ISTAT API unavailable: {health}")

# Discover datasets
dataflows = client.fetch_dataflows(limit=10)
print(f"Found {len(dataflows['dataflows'])} relevant datasets")

# Process datasets
for dataflow in dataflows["dataflows"][:3]:
    dataset_id = dataflow["id"]
    
    # Fetch with quality validation
    quality = client.fetch_with_quality_validation(dataset_id)
    
    if quality.quality_score > 80:
        # High quality dataset - fetch and sync
        dataset = client.fetch_dataset(dataset_id)
        sync_result = client.sync_to_repository(dataset)
        
        print(f"✅ Synced {dataset_id}: {sync_result.records_synced} records")
    else:
        print(f"⚠️  Low quality dataset {dataset_id}: {quality.quality_score}/100")
```

### Async Batch Processing

```python
import asyncio

async def process_datasets(client, dataset_ids):
    """Process multiple datasets concurrently."""
    
    # Batch fetch
    batch_result = await client.fetch_dataset_batch(dataset_ids)
    
    # Process successful results
    for dataset_id in batch_result.successful:
        dataset = client.fetch_dataset(dataset_id)
        sync_result = client.sync_to_repository(dataset)
        print(f"✅ {dataset_id}: {sync_result.records_synced} records")
    
    # Handle failures
    for dataset_id, error in batch_result.failed:
        print(f"❌ {dataset_id}: {error}")

# Usage
dataset_ids = ["DCIS_POPRES1", "DCIS_POPSTRRES1", "DCIS_FECONDITA"]
asyncio.run(process_datasets(client, dataset_ids))
```

### FastAPI Endpoint Usage

```python
from fastapi import Depends
from src.api.dependencies import get_istat_client

@app.get("/my-endpoint")
async def my_endpoint(client = Depends(get_istat_client)):
    """Custom endpoint using production client."""
    
    # Check client health
    health = client.health_check()
    if health["status"] != "healthy":
        raise HTTPException(503, "ISTAT API unavailable")
    
    # Use client normally
    dataflows = client.fetch_dataflows(limit=5)
    return {"dataflows": dataflows["dataflows"]}
```

## Testing

### Unit Testing

```python
from unittest.mock import Mock, patch
from src.api.production_istat_client import ProductionIstatClient

def test_client_with_mock():
    client = ProductionIstatClient()
    
    with patch.object(client, '_make_request') as mock_request:
        mock_request.return_value = Mock(
            content=b'<xml>mock response</xml>',
            headers={'content-type': 'application/xml'}
        )
        
        result = client.fetch_dataflows()
        assert "dataflows" in result
```

### Integration Testing with Mock Server

```python
from tests.integration.mock_istat_server import MockIstatServerContext

def test_with_mock_server():
    with MockIstatServerContext(port=8081) as mock_server:
        # Override client base URL for testing
        client = ProductionIstatClient()
        client.base_url = f"{mock_server.get_base_url()}/SDMXWS/rest/"
        
        # Test against mock server
        dataflows = client.fetch_dataflows()
        assert len(dataflows["dataflows"]) > 0
```

## Migration Guide

### From IstatAPITester to ProductionIstatClient

| Old Method | New Method | Notes |
|------------|------------|-------|
| `test_api_connectivity()` | `health_check()` | Returns structured health data |
| `discover_available_datasets()` | `fetch_dataflows()` | Returns standardized dataflow list |
| `test_specific_dataset()` | `fetch_dataset()` | Returns structured dataset info |
| Manual file operations | `sync_to_repository()` | Integrated repository sync |
| Manual batch processing | `fetch_dataset_batch()` | Async concurrent processing |

### Key Differences

1. **No file I/O**: All operations work with structured data
2. **No visualization**: Focus on data processing, not exploration
3. **Async support**: Built-in concurrency for batch operations
4. **Repository integration**: Direct SQLite + DuckDB coordination
5. **Production patterns**: Circuit breaker, rate limiting, monitoring

## Troubleshooting

### Common Issues

#### Circuit Breaker Open
```
Exception: Circuit breaker is open. Status: open
```
**Solution**: Wait 60 seconds for automatic recovery, or check ISTAT API status.

#### Rate Limit Exceeded
```
Exception: Rate limit exceeded. Wait 45.2 seconds
```
**Solution**: Implement exponential backoff or reduce request frequency.

#### Repository Sync Failures
```
Repository sync failed for DATASET_ID: Connection error
```
**Solution**: Check database connectivity and repository health.

### Monitoring

Monitor these metrics for production health:

- **Circuit breaker state**: Should be "closed" normally
- **Success/failure ratio**: Target >95% success rate  
- **Average response time**: Target <500ms
- **Rate limit usage**: Stay under 80% of limit

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('src.api.production_istat_client').setLevel(logging.DEBUG)
```

This provides detailed request/response information and timing data.