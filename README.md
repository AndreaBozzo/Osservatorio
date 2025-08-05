# 🇮🇹 Osservatorio - Italian Statistical Data Platform

> **Modern enterprise platform for Italian statistical data processing with production-grade FastAPI backend, comprehensive security, and Docker deployment.**

[![CI](https://img.shields.io/badge/CI-Basic%20Tests-blue.svg)](.github/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Multi--stage-blue.svg)](Dockerfile)
[![Python](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11%20|%203.12-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](src/api/fastapi_app.py)
[![Security](https://img.shields.io/badge/Security-Bandit%20|%20OWASP-green.svg)](.pre-commit-config.yaml)
[![Status](https://img.shields.io/badge/Status-Issue%20%2363%20Complete-brightgreen.svg)](docs/project/PROJECT_STATE.md)
[![Pipeline](https://img.shields.io/badge/Pipeline-Unified%20Ingestion-blue.svg)](docs/SYSTEM_USAGE_GUIDE.md)

## 🎯 What is Osservatorio?

**Osservatorio** makes Italian statistical data accessible to everyone. Whether you're a researcher, analyst, or decision-maker, our platform provides reliable access to ISTAT's 509+ datasets with in-development enterprise-grade processing and visualization capabilities.

### ✨ Key Benefits
- **🚀 Production Ready**: FastAPI backend with comprehensive testing and basic CI
- **⚡ High Performance**: DuckDB analytics engine with optimized query processing
- **🛡️ Enterprise Security**: JWT authentication, OWASP compliance, security middleware
- **🐳 Container Ready**: Multi-stage Docker builds with development environments
- **🔄 Modern Architecture**: Async processing, circuit breakers, rate limiting
- **📊 API-First**: RESTful endpoints with comprehensive data analysis capabilities

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone and run with Docker Compose
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio
docker-compose up -d

# Access services:
# - FastAPI: http://localhost:8000
# - Dashboard: http://localhost:8501
# - API Docs: http://localhost:8000/docs
```

### Option 2: Local Development
```bash
# 1. Clone and setup
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install with modern dependency management
pip install -e .[dev]                           # Development dependencies
# or pip install -e .[dev,performance,security] # All optional dependencies

# 3. Run services
make test-fast                                   # Quick test suite
python -m uvicorn src.api.fastapi_app:app --reload  # FastAPI server
streamlit run dashboard/app.py                  # Dashboard
```

### Quick Health Check
```bash
# Test FastAPI endpoint
curl http://localhost:8000/health

# Or use Python client
python -c "from src.api.production_istat_client import ProductionIstatClient; client=ProductionIstatClient(); print('✅ System ready:', client.get_status()['status'])"
```

## 🏗️ Modern Architecture

Osservatorio uses a **microservices-ready architecture** with production patterns:

```
🌐 FastAPI REST API (OpenAPI/Swagger docs)
    ↓ (Security Middleware + JWT Auth)
🔄 Business Logic Layer (Circuit Breakers + Rate Limiting)
    ↓ (Async Processing)
📊 Data Layer: DuckDB Analytics + SQLite Metadata + Redis Cache
    ↓ (Smart Routing + Fallback)
🇮🇹 ISTAT SDMX API (509+ datasets)
```

### Core Components
- **FastAPI Backend**: Modern async web framework with automatic OpenAPI documentation
- **Security Layer**: JWT authentication, OWASP-compliant middleware, rate limiting
- **Data Processing**: DuckDB for analytics, SQLite for metadata, Redis for caching
- **DevOps Ready**: Docker containers, GitHub Actions CI/CD, comprehensive testing
- **Monitoring**: Health checks, performance metrics, security scanning

## 📊 What You Can Do

### For Data Analysts
```python
# REST API access
import requests
response = requests.get("http://localhost:8000/api/v1/dataflows?limit=10")
dataflows = response.json()

# Or use Python client
from src.api.production_istat_client import ProductionIstatClient
client = ProductionIstatClient(enable_cache_fallback=True)
dataset = client.fetch_dataset("DCIS_POPRES1")  # Population data
```

### For API Integration
- **OpenAPI/Swagger**: Interactive API docs at `/docs` endpoint
- **RESTful Design**: Standard HTTP methods with JSON responses
- **Authentication**: JWT token-based security with API key support
- **Rate Limiting**: Fair usage policies with intelligent throttling

### For DevOps Teams
- **Container Ready**: Multi-stage Docker builds for development and production
- **Basic CI**: GitHub Actions with unit testing and code quality checks
- **Security First**: Bandit security scanning, pre-commit hooks
- **Monitoring**: Health checks, performance metrics, structured logging

## 🛡️ Production Features

### Modern Development
- **Python 3.9-3.12**: Multi-version compatibility with matrix testing
- **FastAPI Framework**: High-performance async web framework
- **Docker Deployment**: Multi-stage builds with development and production targets
- **Basic CI**: Automated unit testing and code quality checks

### Security & Compliance
- **JWT Authentication**: Secure token-based authentication
- **OWASP Middleware**: Security headers and best practices
- **Bandit Scanning**: Automated security vulnerability detection
- **Dependency Monitoring**: Automated vulnerability checking with Safety

### Performance & Reliability
- **Async Processing**: Non-blocking operations for better throughput
- **Circuit Breakers**: Automatic fault detection and recovery
- **Rate Limiting**: Configurable request throttling
- **Health Monitoring**: Comprehensive system status and metrics
- **Redis Caching**: High-performance distributed caching

## 📚 Documentation

- **[Architecture Overview](docs/core/ARCHITECTURE.md)** - System design and patterns
- **[Production Client API](docs/api/PRODUCTION_ISTAT_CLIENT.md)** - Complete API reference
- **[Project Status](docs/project/PROJECT_STATE.md)** - Current development state
- **[Developer Guide](docs/project/CLAUDE.md)** - Commands and development context

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Check the [Issues](https://github.com/AndreaBozzo/Osservatorio/issues)** for tasks that need help
2. **Read our [Contributing Guide](docs/guides/CONTRIBUTING.md)** for development standards
3. **Join [Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions)** for questions and ideas
4. **Test First**: Run `pytest tests/ -v` to ensure everything works

### Development Standards
- **Modern Tooling**: ruff, black, mypy, and pre-commit hooks
- **Comprehensive Testing**: Unit, integration, and performance tests
- **Security First**: Bandit scanning, dependency checking, OWASP compliance
- **Basic CI Integration**: GitHub Actions with unit testing and code quality

## 🎯 Use Cases

- **🏛️ Government Agencies**: Access official Italian statistics for policy making
- **🏢 Businesses**: Market research and economic analysis with reliable data
- **🎓 Researchers**: Academic research with comprehensive Italian datasets
- **📊 Analysts**: BI dashboards and reporting with PowerBI integration
- **🔍 Journalists**: Data journalism with verified official sources

## 🏆 Development Metrics

**Modern Development Standards Achieved:**

- ✅ **Basic CI Pipeline**: GitHub Actions with unit testing and code quality
- ✅ **Container Ready**: Multi-stage Docker builds with development environment
- ✅ **Security Scanning**: Bandit, Safety, and OWASP compliance
- ✅ **Code Quality**: ruff, black, mypy, and pre-commit hooks
- ✅ **FastAPI Backend**: Modern async web framework with OpenAPI docs
- ✅ **Production Ready**: JWT auth, rate limiting, monitoring, and health checks

*All tests passing with comprehensive coverage across unit, integration, and performance testing.*

## 📞 Support

- **🐛 Issues**: [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues) for bug reports
- **💬 Discussions**: [GitHub Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions) for questions
- **📚 Documentation**: [docs/](docs/) folder for comprehensive guides
- **🎯 Live Dashboard**: [osservatorio-dashboard.streamlit.app](https://osservatorio-dashboard.streamlit.app/)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**🎯 Ready to explore Italian statistical data?**
**👉 Run `docker-compose up -d` or `make install && make test-fast` to get started**

*Built with modern Python, FastAPI, and Docker for the Italian data community*
