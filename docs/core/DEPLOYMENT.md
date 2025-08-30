# Docker Compose Instructions

## Development with monitoring
`docker-compose --profile monitoring up --build`

## Run benchmarking
`docker-compose --profile benchmark up build-benchmark`

## Production-like setup
BUILD_TARGET=production docker-compose up --build

## Custom ports
API_PORT=8080 DASHBOARD_PORT=8502 docker-compose up


## Health Monitoring

### Check all health endpoints
```bash
curl http://localhost:8000/health/live

curl http://localhost:8000/health/ready

curl http://localhost:8000/health/db

curl http://localhost:8000/health/cache

curl http://localhost:8000/health/external

curl http://localhost:8000/health/metrics
```

## View health monitor logs
`docker-compose logs -f health-monitor`

## View benchmark results
`docker-compose exec build-benchmark cat /benchmark/results/build_benchmark_*.json`
