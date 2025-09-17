# 🚀 Osservatorio ISTAT Data Platform - Deployment Guide

> **Docker-focused deployment guide for FastAPI backend and React frontend**
> **Version**: 1.0.0
> **Date**: September 10, 2025
> **Status**: Production Ready - Issue #53 Complete

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Docker Deployment](#-docker-deployment)
3. [Environment Configuration](#-environment-configuration)
4. [Authentication Setup](#-authentication-setup)
5. [Health Checks & Monitoring](#-health-checks--monitoring)
6. [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

Osservatorio ISTAT Data Platform is a comprehensive statistical data platform with advanced architecture:

- **🐳 Docker**: Multi-stage containerized deployment with orchestration
- **🔧 FastAPI**: High-performance async REST API with OpenAPI documentation
- **🏗️ Multi-Database**: SQLite (metadata) + DuckDB (analytics) + PostgreSQL (production)
- **🔐 Authentication**: Complete JWT system with bcrypt, rate limiting, API keys
- **📊 Data Pipeline**: ISTAT SDMX integration with ingestion and export systems
- **🚀 Export System**: Universal data export (CSV, JSON, XML, Excel, OData)
- **⚛️ React**: Modern frontend (coming soon)
- **📈 Monitoring**: Comprehensive health checks, metrics, and performance monitoring

### 🏗️ Detailed System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           🌐 PRODUCTION ENVIRONMENT                                        │
│                                                                                             │
│  ┌─────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────────┐  │
│  │   🌐 NGINX          │   │   🔧 FASTAPI BACKEND      │   │   ⚛️ REACT FRONTEND      │  │
│  │   • SSL Termination │   │   • REST API Endpoints    │   │   • SPA with React 18      │  │
│  │   • Load Balancing  │   │   • OpenAPI/Swagger Docs  │   │   • Data Visualization     │  │
│  │   • Rate Limiting   │   │   • Authentication System │   │   • Export Interface       │  │
│  │   • Security Headers│   │   • Data Export System    │   │   • Dashboard UI           │  │
│  │   • CORS Handling   │   │   • Health Monitoring     │   │   • User Management        │  │
│  └─────────────────────┘   └──────────────────────────┘   └─────────────────────────────┘  │
│           │                              │                              │                    │
│           └──────────────────────────────┼──────────────────────────────┘                    │
└─────────────────────────────────────────┼─────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────┼─────────────────────────────────────────────────────┐
│                    🔧 FASTAPI APPLICATION LAYER                                            │
│                                         │                                                   │
│  ┌─────────────────┐  ┌─────────────────┼─────────────────┐  ┌─────────────────────────┐    │
│  │ 🔐 AUTH SYSTEM  │  │ 📊 DATA PIPELINE│SYSTEM           │  │ 🚀 EXPORT SYSTEM       │    │
│  │ • JWT Tokens    │  │ • ISTAT SDMX    │                 │  │ • Universal Exporter    │    │
│  │ • User Management│  │ • Data Ingestion│                 │  │ • Multiple Formats      │    │
│  │ • API Keys      │  │ • Transformation│                 │  │ • OData Protocol        │    │
│  │ • Rate Limiting │  │ • Validation    │                 │  │ • Streaming Export      │    │
│  │ • Bcrypt Hash   │  │ • Error Handling│                 │  │ • Compression Support  │    │
│  └─────────────────┘  └─────────────────┼─────────────────┘  └─────────────────────────┘    │
│                                         │                                                   │
└─────────────────────────────────────────┼─────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────┼─────────────────────────────────────────────────────┐
│                    💾 DATA PERSISTENCE LAYER                                               │
│                                         │                                                   │
│  ┌───────────────────┐  ┌──────────────┼────────────────┐  ┌─────────────────────────────┐ │
│  │ 📊 SQLITE         │  │ 🏗️ DUCKDB    │                │  │ 🐘 POSTGRESQL              │ │
│  │ • Metadata Store  │  │ • Analytics  │                │  │ • Production Database      │ │
│  │ • User Data       │  │ • Time Series│                │  │ • High Availability        │ │
│  │ • API Keys        │  │ • OLAP Queries│                │  │ • Backup & Recovery        │ │
│  │ • Auth Sessions   │  │ • Aggregations│                │  │ • Connection Pooling       │ │
│  │ • Configuration   │  │ • Performance │                │  │ • Transaction Support     │ │
│  └───────────────────┘  └──────────────┼────────────────┘  └─────────────────────────────┘ │
│                                        │                                                    │
└────────────────────────────────────────┼────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────┼────────────────────────────────────────────────────┐
│                    🔄 CACHING & EXTERNAL SYSTEMS                                          │
│                                        │                                                   │
│  ┌─────────────────────┐  ┌────────────┼──────────────┐  ┌───────────────────────────────┐ │
│  │ 🚀 REDIS            │  │ 🌐 ISTAT │ APIS             │  │ 📈 MONITORING                │ │
│  │ • API Response Cache│  │ • SDMX   │                  │  │ • Health Checks               │ │
│  │ • Session Storage   │  │ • REST   │                  │  │ • Performance Metrics        │ │
│  │ • Rate Limit Data   │  │ • Data   │                  │  │ • Error Tracking             │ │
│  │ • Pub/Sub Messages  │  │ • Metadata│                 │  │ • Resource Monitoring        │ │
│  │ • Background Jobs   │  │ • Validation│               │  │ • Log Aggregation            │ │
│  └─────────────────────┘  └────────────┼──────────────┘  └───────────────────────────────┘ │
└────────────────────────────────────────┼────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────┼────────────────────────────────────────────────────┐
│                    🐳 DOCKER ORCHESTRATION                                                │
│                                        │                                                   │
│  • Multi-stage builds (builder → production → development)                                │
│  • Health checks and service dependencies                                                 │
│  • Volume management and data persistence                                                 │
│  • Network isolation and service discovery                                                │
│  • Resource limits and auto-scaling capabilities                                          │
│  • Rolling updates and zero-downtime deployment                                           │
│  • Environment-specific configurations                                                    │
│  • Security hardening and non-root execution                                              │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Deployment

The primary deployment method for Osservatorio ISTAT Data Platform.

### 🏗️ Multi-Stage Docker Build

Our `Dockerfile` supports multiple build targets:
- **`builder`**: Build dependencies and virtual environment
- **`production`**: Optimized production runtime
- **`development`**: Development with hot reload

### 🚀 Quick Start

#### Development Environment
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f osservatorio-api

# Access API: http://localhost:8000
# Access Docs: http://localhost:8000/docs
```

#### Production Environment
```bash
# Set production target
BUILD_TARGET=production docker-compose up -d

# Custom configuration
API_PORT=8080 docker-compose up -d
```

### 🔧 Docker Services Architecture

The Docker Compose stack provides a comprehensive microservices architecture:

| Service | Description | Port | CPU/Memory | Health Check | Dependencies |
|---------|-------------|------|------------|--------------|-------------|
| `osservatorio-api` | FastAPI Backend with Authentication, Export, Monitoring | 8000 | 2C/2GB | `/health/live` | redis, postgres |
| `postgres` | PostgreSQL Production Database with optimization | 5432 | 2C/2GB | `pg_isready` | None |
| `redis` | Redis Cache, Session Storage, Rate Limiting | 6379 | 1C/1GB | `redis-cli ping` | None |
| `nginx` | Reverse Proxy with SSL, Load Balancing, Security | 80/443 | 1C/512MB | HTTP status | osservatorio-api |
| `health-monitor` | Advanced Health Monitoring with Alerting | - | 0.1C/64MB | Internal checks | All services |
| `build-benchmark` | Docker Build Performance Testing | - | Variable | Build metrics | None |
| `performance-monitor` | System Resource Monitoring (Prometheus) | 9100 | 0.2C/128MB | Metrics endpoint | None |

#### Service Communication Flow
```
🌐 Internet → 🔒 Nginx (SSL/Proxy) → 🔧 FastAPI Backend → 📊 Databases
                    ↓                        ↓              ↓
                🛡️ Security              🔐 Auth System    💾 Data Layer
                🚦 Rate Limiting         📈 Monitoring     🚀 Cache (Redis)
                📊 Load Balancing        🚀 Export API     🏗️ Analytics (DuckDB)
```

### 📊 Monitoring and Profiles

```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Run performance benchmarks
docker-compose --profile benchmark up build-benchmark

# View benchmark results
docker-compose exec build-benchmark cat /benchmark/results/build_benchmark_*.json
```

### 🛠️ Docker Management Commands

```bash
# Build and start services
docker-compose up --build -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Execute commands in running container
docker-compose exec osservatorio-api bash

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Scale services
docker-compose up -d --scale osservatorio-api=3
```

---

## ⚙️ Environment Configuration

### 🌐 Environment Variables

#### Production Environment (`.env.production`)
```bash
# =============================================================================
# APPLICATION CONFIGURATION (Production)
# =============================================================================
OSSERVATORIO_ENV=production
OSSERVATORIO_LOG_LEVEL=WARNING
OSSERVATORIO_DEBUG=false

# Build Configuration
BUILD_TARGET=production
VERSION=1.0.0
BUILD_DATE=
GIT_COMMIT_HASH=

# =============================================================================
# MULTI-DATABASE ARCHITECTURE
# =============================================================================
# SQLite (Primary metadata storage - Fast, reliable, embedded)
DATABASE_URL=sqlite:///data/databases/osservatorio_metadata.db

# DuckDB (Analytics and time series - OLAP optimized)
DUCKDB_URL=data/databases/osservatorio.duckdb
DUCKDB_MEMORY_LIMIT=4GB
DUCKDB_THREADS=4

# PostgreSQL (Production scalability - Optional for large deployments)
POSTGRES_URL=postgresql://osservatorio:${DB_PASSWORD}@postgres:5432/osservatorio
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_CONNECTIONS=200

# =============================================================================
# AUTHENTICATION & SECURITY SYSTEM (Issue #132)
# =============================================================================
# JWT Configuration - MUST BE CHANGED FOR PRODUCTION
JWT_SECRET_KEY=__CHANGE_THIS_SUPER_SECRET_JWT_KEY_FOR_PRODUCTION__
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API Key System
API_KEY_PREFIX=osv_prod_
DEFAULT_RATE_LIMIT=1000
API_KEY_EXPIRY_DAYS=365

# Password Security
PASSWORD_MIN_LENGTH=8
BCRYPT_ROUNDS=12

# Rate Limiting Configuration
RATE_LIMIT_REQUESTS_PER_MINUTE=1000
RATE_LIMIT_BURST=50
RATE_LIMIT_WINDOW=3600

# =============================================================================
# ISTAT DATA PIPELINE INTEGRATION
# =============================================================================
ISTAT_API_BASE_URL=https://sdmx.istat.it/SDMXWS/rest/
ISTAT_API_TIMEOUT=120
ISTAT_API_RATE_LIMIT=50
ISTAT_API_RETRY_ATTEMPTS=3
ISTAT_API_RETRY_DELAY=5

# Data Ingestion Configuration
INGESTION_BATCH_SIZE=5000
INGESTION_CONCURRENCY=8
INGESTION_TIMEOUT=300

# =============================================================================
# EXPORT SYSTEM CONFIGURATION (Issue #150)
# =============================================================================
EXPORT_MAX_ROWS=1000000
EXPORT_TIMEOUT=600
EXPORT_FORMATS=["csv", "json", "xml", "xlsx", "odata"]
EXPORT_COMPRESSION_ENABLED=true
EXPORT_STREAMING_ENABLED=true

# OData Configuration
ODATA_MAX_PAGE_SIZE=10000
ODATA_DEFAULT_PAGE_SIZE=100

# =============================================================================
# CACHING & PERFORMANCE
# =============================================================================
# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_MAXMEMORY=2gb
REDIS_MAXMEMORY_POLICY=allkeys-lru
REDIS_PERSISTENCE=yes

# Application Caching
ENABLE_CACHE=true
CACHE_TTL=7200
CACHE_MAX_SIZE=1000

# Performance Settings
QUERY_MAX_TIME_MS=3000
BULK_INSERT_MAX_TIME_MS=15000
API_RESPONSE_MAX_TIME_MS=1000

# =============================================================================
# MONITORING & HEALTH CHECKS
# =============================================================================
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_INTERVAL=60
ENABLE_METRICS=true
METRICS_RETENTION_DAYS=90
LOG_RETENTION_DAYS=30

# =============================================================================
# CONTAINER RESOURCE LIMITS
# =============================================================================
API_CPU_LIMIT=4.0
API_MEMORY_LIMIT=4G
API_CPU_RESERVATION=1.0
API_MEMORY_RESERVATION=1G

DB_CPU_LIMIT=2.0
DB_MEMORY_LIMIT=2G
REDIS_CPU_LIMIT=1.0
REDIS_MEMORY_LIMIT=1G
```

#### Development Environment (`.env`)
```bash
# Application
OSSERVATORIO_ENV=development
OSSERVATORIO_LOG_LEVEL=DEBUG
OSSERVATORIO_DEBUG=true

# Build Configuration
BUILD_TARGET=development
VERSION=1.0.0-dev

# Database
DATABASE_URL=sqlite:///data/databases/osservatorio_dev.db

# Security (Development Only)
JWT_SECRET_KEY=dev-secret-key-not-for-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Cache
ENABLE_CACHE=false
CACHE_TTL=300
```

### 📁 Docker Compose Environment Variables

```bash
# Ports
API_PORT=8000
REDIS_PORT=6379
POSTGRES_PORT=5432

# Database
DB_PASSWORD=secure_production_password

# Build
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD)
```

---

## 🔐 Authentication Setup

Complete JWT-based authentication system (Issue #132).

### 🔑 User Registration & Login

#### Register New User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password123"
  }'
```

#### Login User
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password123"
  }'
```

#### Use JWT Token
```bash
# Get user profile
curl -X GET "http://localhost:8000/auth/profile" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Access protected endpoints
curl -X GET "http://localhost:8000/datasets" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 🔒 Authentication Configuration

#### JWT Settings
- **Algorithm**: HS256
- **Expiration**: 1 hour (configurable)
- **Blacklist**: Token invalidation on logout
- **Refresh**: Not implemented in MVP (Issue #153)

#### Password Security
- **Hashing**: bcrypt with automatic salt
- **Validation**: Email format and password strength
- **Session**: Stateless JWT tokens

### 🛡️ Security Features

- ✅ Bcrypt password hashing
- ✅ JWT token validation
- ✅ Token blacklisting for logout
- ✅ Rate limiting per endpoint
- ✅ Input validation and sanitization
- ✅ CORS configuration

---

## 📊 Health Checks & Monitoring

### 🔍 Health Check Endpoints

```bash
# Basic API health
curl http://localhost:8000/health/live

# Readiness check (dependencies)
curl http://localhost:8000/health/ready

# Database health
curl http://localhost:8000/health/db

# Cache health (Redis)
curl http://localhost:8000/health/cache

# External APIs health
curl http://localhost:8000/health/external

# System metrics
curl http://localhost:8000/health/metrics
```

### 📈 Docker Health Monitoring

```bash
# View health monitor logs
docker-compose logs -f health-monitor

# Check container health status
docker-compose ps

# Health check details
docker inspect osservatorio-api | grep -A 10 "Health"
```

### 🎯 Health Check Configuration

Each service has optimized health checks:

```yaml
# API Health Check
healthcheck:
  test: curl -f http://localhost:8000/health/live || exit 1
  interval: 30s
  timeout: 15s
  retries: 3
  start_period: 45s

# Redis Health Check
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5

# PostgreSQL Health Check
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U osservatorio -d osservatorio"]
  interval: 10s
  timeout: 5s
  retries: 5
```

---

## 🛠️ Troubleshooting

### 🚨 Common Issues

#### 1. **Docker Build Fails**
```bash
# Check Docker daemon
docker --version
docker info

# Clear build cache
docker builder prune -a

# Rebuild from scratch
docker-compose build --no-cache
```

#### 2. **Container Health Check Fails**
```bash
# Check health status
docker-compose ps
docker inspect [container-name] | grep -A 20 "Health"

# Check logs
docker-compose logs -f [service-name]

# Test health endpoint manually
docker-compose exec osservatorio-api curl http://localhost:8000/health/live
```

#### 3. **Authentication Issues**
```bash
# Verify JWT configuration
docker-compose exec osservatorio-api env | grep JWT

# Test registration
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"test123"}'

# Check authentication logs
docker-compose logs -f osservatorio-api | grep -i auth
```

#### 4. **Database Connection Issues**
```bash
# Check database container
docker-compose exec postgres pg_isready -U osservatorio

# Test database connection from API
docker-compose exec osservatorio-api python -c "
from src.database.sqlite.manager import SQLiteMetadataManager
manager = SQLiteMetadataManager()
print('Database connection:', 'OK' if manager else 'FAILED')
"
```

#### 5. **Performance Issues**
```bash
# Check resource usage
docker stats

# View performance metrics
curl http://localhost:8000/health/metrics

# Check logs for slow queries
docker-compose logs osservatorio-api | grep -i "slow\|timeout"
```

### 🔧 Debug Mode

Enable debug logging:
```bash
# Development environment
OSSERVATORIO_LOG_LEVEL=DEBUG docker-compose up -d

# View debug logs
docker-compose logs -f osservatorio-api | grep DEBUG
```

### 📊 Container Resource Monitoring

```bash
# Monitor all containers
docker stats

# Monitor specific service
docker stats osservatorio-api

# Check memory usage
docker-compose exec osservatorio-api free -h

# Check disk usage
docker-compose exec osservatorio-api df -h
```

---

## 🎯 Production Deployment Checklist

### ✅ Pre-Deployment Checklist

#### Security
- [ ] JWT_SECRET_KEY changed from default
- [ ] DB_PASSWORD set to secure value
- [ ] CORS origins configured for production domains
- [ ] Rate limiting configured appropriately
- [ ] SSL certificates configured (if applicable)

#### Configuration
- [ ] BUILD_TARGET=production set
- [ ] Environment variables configured
- [ ] Database persistence volumes mounted
- [ ] Log retention configured
- [ ] Health checks validated

#### Testing
- [ ] All services start successfully
- [ ] Authentication flow working
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Database connections stable

### ✅ Post-Deployment Verification

#### API Health
- [ ] `curl http://localhost:8000/health/live` returns 200
- [ ] `curl http://localhost:8000/health/ready` returns 200
- [ ] `curl http://localhost:8000/docs` loads OpenAPI documentation

#### Authentication
- [ ] User registration working
- [ ] User login returning JWT token
- [ ] Protected endpoints require authentication
- [ ] Token expiration working correctly

#### Monitoring
- [ ] Health monitor container running
- [ ] Logs being generated and accessible
- [ ] Resource usage within acceptable limits
- [ ] All containers showing healthy status

---

## 🔗 Related Documentation

- **[DEPLOYMENT.md](../core/DEPLOYMENT.md)**: Quick Docker commands
- **[README.md](../../README.md)**: Project overview and setup
- **Issue #53**: Complete Production Deployment Strategy with Docker
- **Issue #132**: User Authentication System Implementation

---

## 📞 Support

For deployment support:
- **GitHub Issues**: [Report deployment issues](https://github.com/AndreaBozzo/Osservatorio/issues)
- **Documentation**: [Complete documentation](https://github.com/AndreaBozzo/Osservatorio)

---

**🚀 Deployment Status**: ✅ **Production Ready** | 🔄 **Docker Native** | 🔐 **Authentication Complete**

*Last updated: September 10, 2025*
