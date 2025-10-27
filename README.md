# 🇮🇹 Osservatorio - Italian Statistical Data Platform

> **Modern platform for accessing and analyzing Italian statistical data**

![Status](https://img.shields.io/badge/Status-MVP%20in%20Development-orange.svg)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](src/api/fastapi_app.py)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

## 🎯 What is Osservatorio?

**Osservatorio** is a platform for accessing and analyzing Italian statistical data from ISTAT.
The project provides modern REST APIs to query over 500 statistical datasets with scalable architecture.
Our goal is to unify multiple italian sources, allowing analysts, data scientist and anyone else to utilize them with ease
and on the same platform.

### ✨ Current Status

**Core Features:**

- ✅ **FastAPI Backend**: REST API with JWT authentication and rate limiting
- ✅ **Hybrid Database**: DuckDB (analytics) + SQLite (metadata)
- ✅ **Data Export**: Multiple formats (CSV, JSON, Parquet, Excel)
- ✅ **ISTAT Integration**: Production client for ISTAT SDMX API
- ✅ **Security**: JWT auth, rate limiting, OWASP middleware

**Development Status:**

- 🔧 **Test Suite**: Simplified and focused on MVP essentials ([#159](https://github.com/AndreaBozzo/Osservatorio/issues/159))
- 📊 **Coverage**: 58%+ on core components
- 🐳 **Docker**: Development setup ready
- 📚 **Documentation**: Core guides available

**⚠️ MVP in Active Development** - Not ready for production use yet

## 🚀 Quick Start

### Development Setup

```bash
# Clone repository
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio

# Install dependencies (Python 3.11+)
pip install -e .

# Run tests
pytest tests/unit tests/integration -v

# Start development server
python -m uvicorn src.api.fastapi_app:app --reload

# Access API documentation
# http://localhost:8000/docs
```

### Docker Setup (Alternative)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access API
# http://localhost:8000
# http://localhost:8000/docs
```

## 🏗️ Architecture

**Technology Stack:**

- **Backend**: FastAPI (async REST API with OpenAPI docs)
- **Analytics DB**: DuckDB (columnar, fast aggregations)
- **Metadata DB**: SQLite (lightweight, reliable)
- **Authentication**: JWT tokens with rate limiting
- **Data Sources**: ISTAT SDMX API integration
- **Export**: CSV, JSON, Parquet, Excel formats
- **Security**: OWASP middleware, input validation

## 📁 Project Structure

```
osservatorio/
├── config/                  # Configuration files
│   ├── docker/             # Docker configurations
│   ├── requirements/       # Python dependencies
│   ├── pytest.ini          # Pytest configuration
│   ├── pytest-ci.ini       # CI pytest config
│   └── pytest-fast.ini     # Fast pytest config
├── src/                    # Source code
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── data/                   # Data storage
├── examples/               # Usage examples
├── dashboard/              # Streamlit dashboard
└── bin/                    # External binaries (gitignored)
```

## 📚 Documentation

**Core Guides:**

- [Architecture](docs/core/ARCHITECTURE.md) - System design and architecture
- [Testing](docs/TESTING.md) - Test strategy and guidelines
- [Contributing](CONTRIBUTING.md) - How to contribute
- [Security](SECURITY.md) - Security policy and reporting
- [Changelog](docs/CHANGELOG.md) - Version history

**Technical Docs:**

- [REST API](docs/api/FASTAPI_REST_API.md) - API endpoints and usage
- [Ingestion Pipeline](docs/guides/INGESTION_PIPELINE_GUIDE.md) - Data ingestion guide
- [Project Status](docs/project/PROJECT_STATE.md) - Current development state
- [Collaborator Guide](docs/COLLABORATOR_README.md) - For project collaborators

## 👥 Contributors

Thanks to all the people who have contributed to this project! 🎉

<a href="https://github.com/AndreaBozzo/Osservatorio/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=AndreaBozzo/Osservatorio" alt="Contributors" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

### 🤝 How to Contribute

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** and ensure tests pass (`pytest`)
4. **Commit your changes** (`git commit -m 'Add amazing feature'`)
5. **Push to your fork** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ISTAT** - For providing comprehensive Italian statistical data
- All contributors who have helped shape this project
- The open-source community for the amazing tools and libraries

---

<div align="center">
  <strong>⭐ Star this repository if you find it useful!</strong>
  <br/>
  <sub>Built with ❤️ for the Italian data community</sub>
</div>
