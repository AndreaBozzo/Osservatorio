# 🇮🇹 Osservatorio - Italian Statistical Data Platform

> **Modern platform for accessing and analyzing Italian statistical data**

[![Status](https://img.shields.io/badge/Status-MVP%20in%20Development-orange.svg)]()
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](src/api/fastapi_app.py)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

## 🎯 What is Osservatorio?

**Osservatorio** is a platform for accessing and analyzing Italian statistical data from ISTAT.
The project provides modern REST APIs to query over 500 statistical datasets with scalable architecture.
Our goal is to unify multiple italian sources, allowing analysts, data scientist and anyone else to utilize them with ease
and on the same platform.

**⚠️ STATUS: MVP in active development**

## 🚀 Quick Start

```bash
# Clone and run with Docker
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio
docker-compose up -d

# Access:
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
```

## 🏗️ Architecture

- **FastAPI Backend**: Async REST API with OpenAPI documentation
- **Hybrid Database**: DuckDB (analytics) + SQLite (metadata) + Redis (cache)
- **Authentication**: JWT with rate limiting
- **Docker**: Multi-stage builds for development and production
- **Security**: OWASP middleware, vulnerability scanning

## 📚 Documentation

- [Architecture](docs/core/ARCHITECTURE.md) - Current and planned
architecture
- [Deployment Guide](docs/core/DEPLOYMENT.md) - Docker setup and production
- [Project Status](docs/project/PROJECT_STATE.md) - Current development state
- [Ingestion](docs/guides/INGESTION_PIPELINE_GUIDE.md)  - Current
ingestion guidelines
- [REST API](docs/api/FASTAPI_REST_API.md)  - REST API Guide
