# 🐳 Docker Deployment - Quick Reference

> **Quick commands for Docker deployment - See [DEPLOYMENT_GUIDE.md](../guides/DEPLOYMENT_GUIDE.md) for complete documentation**

## 🚀 Quick Start Commands

### Development Environment
```bash
# Start all services
docker-compose up -d

# View API logs
docker-compose logs -f osservatorio-api

# Access: http://localhost:8000 (API) | http://localhost:8000/docs (OpenAPI)
```

### Production Environment
```bash
# Production build
BUILD_TARGET=production docker-compose up --build -d

# Custom ports
API_PORT=8080 docker-compose up -d
```

### Monitoring & Performance
```bash
# Start with monitoring
docker-compose --profile monitoring up --build

# Run benchmarking
docker-compose --profile benchmark up build-benchmark

# View benchmark results
docker-compose exec build-benchmark cat /benchmark/results/build_benchmark_*.json
```

## 🔍 Health Monitoring

### Health Check Endpoints
```bash
curl http://localhost:8000/health/live      # Basic API health
curl http://localhost:8000/health/ready     # Dependencies check
curl http://localhost:8000/health/db        # Database health
curl http://localhost:8000/health/cache     # Redis health
curl http://localhost:8000/health/external  # ISTAT API health
curl http://localhost:8000/health/metrics   # System metrics
```

### Docker Health Status
```bash
# Check container health
docker-compose ps

# View health monitor logs
docker-compose logs -f health-monitor

# Container resource usage
docker stats
```

## 🔐 Authentication Quick Test (Issue #132)

```bash
# Register user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login and get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Use token for protected endpoints
curl -X GET "http://localhost:8000/datasets" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🛠️ Management Commands

```bash
# Build and start
docker-compose up --build -d

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View service status
docker-compose ps

# Execute commands in container
docker-compose exec osservatorio-api bash
```

---

**📚 Complete Documentation**: [DEPLOYMENT_GUIDE.md](../guides/DEPLOYMENT_GUIDE.md)
**🔧 Architecture Details**: Full system architecture, configuration, and troubleshooting
**🔐 Security Setup**: Authentication, JWT configuration, and production hardening
