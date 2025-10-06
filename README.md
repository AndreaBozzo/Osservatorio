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

- [Architecture](docs/core/ARCHITECTURE.md) - Current and planned architecture
- [Deployment Guide](docs/core/DEPLOYMENT.md) - Docker setup and production
- [Project Status](docs/project/PROJECT_STATE.md) - Current development state
- [Ingestion](docs/guides/INGESTION_PIPELINE_GUIDE.md) - Current ingestion guidelines
- [REST API](docs/api/FASTAPI_REST_API.md) - REST API Guide

## 👥 Contributors

Thanks to all the people who have contributed to this project! 🎉

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/AndreaBozzo"><img src="https://avatars.githubusercontent.com/AndreaBozzo?s=100" width="100px;" alt="Andrea Bozzo"/><br /><sub><b>Andrea Bozzo</b></sub></a><br /><a href="https://github.com/AndreaBozzo/Osservatorio/commits?author=AndreaBozzo" title="Code">💻</a> <a href="#design-AndreaBozzo" title="Design">🎨</a> <a href="#ideas-AndreaBozzo" title="Ideas & Planning">🤔</a> <a href="#projectManagement-AndreaBozzo" title="Project Management">📆</a> <a href="https://github.com/AndreaBozzo/Osservatorio/commits?author=AndreaBozzo" title="Documentation">📖</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

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
