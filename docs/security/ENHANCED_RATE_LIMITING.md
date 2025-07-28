# Enhanced Rate Limiting and API Protection

## Overview

The Enhanced Rate Limiting system provides advanced protection against API abuse, DoS attacks, and credential stuffing while ensuring legitimate users maintain optimal access to the platform.

## Features

### 🔄 Distributed Rate Limiting
- **Redis Support**: Scales across multiple application instances
- **Consistent Limits**: Shared rate limiting state across all servers
- **High Availability**: Automatic fallback to SQLite if Redis is unavailable

### 🎯 Adaptive Rate Limiting
- **Performance-Based**: Automatically adjusts limits based on API response times
- **Dynamic Thresholds**: Reduces limits when system is under stress
- **Smart Recovery**: Gradually increases limits as performance improves

### 🛡️ IP-Based Protection
- **Suspicious Activity Detection**: Identifies unusual access patterns
- **Automatic Blocking**: Blocks IPs exhibiting critical threat behavior
- **Threat Classification**: Low, Medium, High, and Critical threat levels
- **Temporary Blocks**: Configurable block durations with automatic expiry

### 📊 Security Monitoring
- **Real-time Dashboard**: Live security metrics and threat assessment
- **Alert System**: Proactive notifications for security events
- **Comprehensive Logging**: Detailed audit trail of all security actions
- **Performance Metrics**: API response time tracking and analysis

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Request   │───▶│ Enhanced Rate   │───▶│ Security        │
│                 │    │ Limiter         │    │ Dashboard       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Redis (Optional)│    │ SQLite Storage  │
                       │ Distributed     │    │ - Rate Limits   │
                       │ Rate Limiting   │    │ - Blocked IPs   │
                       └─────────────────┘    │ - Violations    │
                                              │ - Response Times│
                                              └─────────────────┘
```

## Configuration

### Environment Variables

```bash
# Enhanced Rate Limiting
ENHANCED_RATE_LIMITING_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# Adaptive Configuration
ADAPTIVE_RATE_LIMITING_ENABLED=true
RESPONSE_TIME_THRESHOLD_MS=2000
RATE_LIMIT_ADJUSTMENT_FACTOR=0.8
MIN_ADJUSTMENT_RATIO=0.1
MAX_ADJUSTMENT_RATIO=2.0

# Security Settings
SUSPICIOUS_ACTIVITY_THRESHOLD=0.5
AUTO_BLOCK_CRITICAL_THREATS=true
IP_BLOCK_DURATION_HOURS=24

# Monitoring
SECURITY_MONITORING_ENABLED=true
SECURITY_ALERT_EMAIL=admin@example.com
CLEANUP_DATA_RETENTION_DAYS=30
```

### Rate Limit Tiers

| Scope | Requests/Min | Requests/Hour | Requests/Day | Burst |
|-------|-------------|---------------|--------------|-------|
| Read | 60 | 1,000 | 10,000 | 10 |
| Write | 30 | 500 | 5,000 | 5 |
| Admin | 120 | 2,000 | 20,000 | 20 |
| Analytics | 100 | 1,500 | 15,000 | 15 |
| PowerBI | 200 | 3,000 | 30,000 | 30 |
| Tableau | 200 | 3,000 | 30,000 | 30 |

## Implementation

### Basic Setup

```python
from src.auth.security_config import create_security_manager
from src.database.sqlite.manager import SQLiteMetadataManager

# Initialize database manager
db_manager = SQLiteMetadataManager()

# Create security manager with auto-configuration
security_manager = create_security_manager(db_manager)

# Get rate limiter
rate_limiter = security_manager.rate_limiter
```

### Rate Limit Check

```python
from src.auth.models import APIKey

# Check rate limit for authenticated request
api_key = get_api_key_from_request()
ip_address = get_client_ip()

result = rate_limiter.check_enhanced_rate_limit(
    api_key=api_key,
    ip_address=ip_address,
    endpoint="/api/data",
    user_agent=request.headers.get("User-Agent")
)

if not result.allowed:
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"},
        headers=result.to_headers()
    )
```

### Response Time Recording

```python
import time

start_time = time.time()

# Process API request
response = process_request()

# Record response time for adaptive limiting
response_time_ms = (time.time() - start_time) * 1000
security_manager.record_api_response(
    identifier=str(api_key.id),
    identifier_type="api_key",
    endpoint="/api/data",
    response_time_ms=response_time_ms,
    status_code=200
)
```

### Manual IP Blocking

```python
# Block suspicious IP
security_manager.block_ip_address(
    ip_address="192.168.1.100",
    reason="Multiple failed authentication attempts",
    duration_hours=24
)
```

## Security Dashboard

### Web Interface

Access the security dashboard at: `http://your-api-host/api/security/dashboard`

Features:
- Real-time threat score
- Rate limit violations
- Blocked IP addresses
- Performance metrics
- Security alerts

### API Endpoints

```python
# Get security metrics
GET /api/security/metrics

# Get security alerts
GET /api/security/alerts?hours=24

# Get blocked IPs
GET /api/security/blocked-ips

# Unblock IP
POST /api/security/unblock-ip
{
    "ip_hash": "abcd1234",
    "reason": "False positive resolved"
}

# Get rate limit statistics
GET /api/security/rate-limit-stats?hours=24
```

## Threat Detection

### Suspicious Activity Patterns

The system automatically detects:

1. **Rapid Request Patterns**
   - More than 100 requests per minute from single IP
   - Burst requests exceeding normal patterns

2. **Unusual Access Patterns**
   - Accessing multiple different endpoints rapidly
   - Requests from automated tools/bots

3. **Authentication Anomalies**
   - Multiple failed authentication attempts
   - Requests without proper API keys

4. **Performance Impact**
   - Requests causing significant system slowdown
   - Patterns indicating resource exhaustion attacks

### Threat Levels

- **Low (0.0-0.3)**: Normal activity with minor irregularities
- **Medium (0.3-0.5)**: Suspicious patterns requiring monitoring
- **High (0.5-0.7)**: Likely malicious activity requiring intervention
- **Critical (0.7-1.0)**: Confirmed threat requiring immediate blocking

## Monitoring and Alerts

### Automatic Responses

- **Medium Threats**: Reduced rate limits applied
- **High Threats**: Aggressive rate limiting and logging
- **Critical Threats**: Immediate IP blocking (if enabled)

### Alert Triggers

- Rate limit violations exceeding thresholds
- New IP blocks created
- Performance degradation detected
- System errors in security components

### Maintenance

```python
# Run daily maintenance
security_manager.run_security_maintenance()

# Manual cleanup
cleanup_results = rate_limiter.cleanup_old_data(days=30)
```

## Performance Considerations

### Redis Deployment

For production environments with multiple instances:

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

### Database Optimization

- Regular cleanup of old rate limit data
- Proper indexing on frequently queried columns
- Connection pooling for high-traffic scenarios

### Memory Management

- Response time cache automatically limited to recent measurements
- In-memory IP block cache for faster lookups
- Periodic cleanup of expired entries

## Migration Guide

### From Basic Rate Limiting

1. Update configuration to enable enhanced features
2. Install Redis (optional but recommended for production)
3. Run database migrations for new tables
4. Update application code to use enhanced rate limiter
5. Configure monitoring and alerting

### Configuration Migration

```python
# Old configuration
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# New configuration
ENHANCED_RATE_LIMITING_ENABLED=true
ADAPTIVE_RATE_LIMITING_ENABLED=true
RESPONSE_TIME_THRESHOLD_MS=2000
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failures**
   - System automatically falls back to SQLite
   - Check Redis connectivity and credentials
   - Monitor logs for connection errors

2. **False Positive Blocks**
   - Review suspicious activity thresholds
   - Use dashboard to unblock legitimate IPs
   - Adjust threat detection sensitivity

3. **Performance Impact**
   - Monitor response time metrics
   - Adjust adaptive limiting thresholds
   - Consider Redis deployment for scaling

### Debugging

```python
# Get security status
status = security_manager.get_security_status()
print(f"Status: {status}")

# Validate configuration
from src.auth.security_config import validate_security_environment
validation = validate_security_environment()
print(f"Validation: {validation}")
```

## Security Best Practices

1. **Regular Monitoring**: Review security dashboard daily
2. **Threshold Tuning**: Adjust based on legitimate usage patterns
3. **Alert Configuration**: Set up email notifications for critical events
4. **Data Retention**: Balance security needs with storage requirements
5. **Testing**: Regularly test rate limiting and blocking mechanisms
6. **Documentation**: Keep security procedures up to date

## Integration with FastAPI

```python
from fastapi import FastAPI, Request, HTTPException
from src.auth.security_config import create_security_manager

app = FastAPI()
security_manager = create_security_manager(db_manager)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Extract authentication info
    api_key = extract_api_key(request)
    ip_address = request.client.host

    # Check rate limit
    result = security_manager.rate_limiter.check_enhanced_rate_limit(
        api_key=api_key,
        ip_address=ip_address,
        endpoint=request.url.path,
        user_agent=request.headers.get("user-agent")
    )

    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=result.to_headers()
        )

    # Process request
    start_time = time.time()
    response = await call_next(request)
    response_time = (time.time() - start_time) * 1000

    # Record response time
    if api_key:
        security_manager.record_api_response(
            identifier=str(api_key.id),
            identifier_type="api_key",
            endpoint=request.url.path,
            response_time_ms=response_time,
            status_code=response.status_code
        )

    # Add rate limit headers
    for key, value in result.to_headers().items():
        response.headers[key] = value

    return response

# Include security dashboard routes
app.include_router(security_manager.create_security_router())
```

This enhanced rate limiting system provides enterprise-grade API protection while maintaining high performance and scalability for the Osservatorio ISTAT Data Platform.
