# 📚 Osservatorio Documentation

> **Comprehensive documentation for the Italian statistical data processing platform**

## 🚀 Quick Navigation

### 📖 Getting Started
- **[Quick Start Guide](GETTING_STARTED.md)** - Setup in 5 minutes
- **[Development Guide](guides/DEVELOPMENT.md)** - Contributor workflow
- **[Testing Guide](../TESTING.md)** - 491 tests, 70.34% coverage

### 🏗️ Core Documentation
- **[Architecture](core/ARCHITECTURE.md)** - SQLite + DuckDB design
- **[API Reference](core/API_REFERENCE.md)** - Endpoints & examples
- **[Performance](core/PERFORMANCE.md)** - Benchmarks & optimization

### 📋 Project Management
- **[Project Status](project/PROJECT_STATE.md)** - Current development state
- **[Roadmap](project/ROADMAP.md)** - Strategic SQLite pivot
- **[Changelog](reference/CHANGELOG.md)** - Version history

### 📝 Guides & References
- **[Deployment Guide](guides/DEPLOYMENT.md)** - Production setup
- **[ADR Records](reference/adr/)** - Architectural decisions
- **[API Mapping](api/api-mapping.md)** - ISTAT API documentation

---

## 🎯 Project Overview

**Osservatorio** è una piattaforma per l'elaborazione e visualizzazione dei dati statistici italiani (ISTAT) con architettura **SQLite + DuckDB** ottimizzata per Business Intelligence.

### Key Features
- ✅ **DuckDB Analytics Engine** - High-performance data processing
- ✅ **SQLite Metadata Layer** - Lightweight configuration management
- ✅ **PowerBI Integration** - Native BI tool support
- ✅ **Performance Testing** - >2k records/sec validated
- ✅ **Security Audited** - 0 HIGH severity issues

---

## 📊 Current Status (22 Luglio 2025)

| Component | Status | Coverage | Performance |
|-----------|--------|----------|-------------|
| **DuckDB Engine** | ✅ Complete | 85% | >2k records/sec |
| **Test Suite** | ✅ 491 tests | 70.34% total | 100% pass rate |
| **Security** | ✅ Audited | 100% | 0 HIGH issues |
| **Documentation** | 🔄 85% | Updating | User-friendly |
| **SQLite Layer** | ⏳ Next | Planned | <10ms target |

---

## 🚀 Strategic Architecture

### SQLite + DuckDB Hybrid
```
┌─────────────────────┐     ┌─────────────────────┐
│   DuckDB Engine     │     │  SQLite Metadata    │
├─────────────────────┤     ├─────────────────────┤
│ • ISTAT Analytics   │     │ • Dataset Registry  │
│ • Time Series       │     │ • User Preferences  │
│ • Aggregations      │     │ • API Keys/Auth     │
│ • Performance Data  │     │ • Audit Logging     │
└─────────────────────┘     └─────────────────────┘
         ↓                           ↓
    ┌────────────────────────────────┐
    │   Unified Data Repository      │
    │   (Facade Pattern)             │
    └────────────────────────────────┘
```

### Why This Architecture?
1. **Zero Configuration** - No database servers to manage
2. **High Performance** - SQLite <10ms, DuckDB analytics optimized
3. **BI-First Design** - PowerBI native integration
4. **Migration Ready** - Standard SQL, easy PostgreSQL upgrade
5. **Battle Tested** - SQLite powers millions of apps worldwide

---

## 🎯 Sprint Progress (Days 0-11)

### ✅ Completed (Days 0-3)
- **Day 0**: API Mapping & Documentation
- **Day 1**: Complete DuckDB Implementation
- **Day 2**: Accelerated (completed in Day 1)
- **Day 3**: Performance Testing Suite

### 🔄 Active Sprint (Days 4-11)
- **Day 4**: SQLite Metadata Layer (In Progress)
- **Day 5**: Unified Data Access
- **Day 6**: PowerBI Integration Enhancement
- **Day 7**: Lightweight Auth System
- **Day 8**: FastAPI Development
- **Day 9**: Monitoring & Analytics
- **Day 10**: Testing & Release Prep
- **Day 11**: Sprint Review & Demo

---

## 👥 Contributing

### Quick Contribute
1. **Browse Issues**: [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues)
2. **Setup Locally**: Follow [Getting Started](GETTING_STARTED.md)
3. **Pick Task**: Choose from sprint board
4. **Submit PR**: With clear description

### Skill Levels
- 🟢 **Beginner**: Documentation, test coverage
- 🟡 **Intermediate**: Feature implementation, API design
- 🔴 **Advanced**: Performance optimization, architecture

### Communication
- **Questions**: [GitHub Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions)
- **Bugs**: [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues)
- **Sprint Review**: July 31, 18:00 CET

---

## 🔗 External Links

- **[Live Dashboard](https://osservatorio-dashboard.streamlit.app/)** - Demo Streamlit app
- **[GitHub Project](https://github.com/AndreaBozzo/Osservatorio/projects)** - Sprint board
- **[GitHub Pages](https://andreabozzo.github.io/Osservatorio/)** - Project website
- **[Wiki](https://github.com/AndreaBozzo/Osservatorio/wiki)** - Community documentation

---

## 📄 License & Credits

- **License**: MIT License
- **Maintainer**: Andrea Bozzo
- **Contributors**: [View all contributors](https://github.com/AndreaBozzo/Osservatorio/contributors)
- **Data Source**: ISTAT (Istituto Nazionale di Statistica)

---

**🎯 Ready to start?** Begin with [Getting Started Guide](GETTING_STARTED.md)

*Documentation updated: 22 Luglio 2025*
*Current version: v8.1.0 (Day 5 Complete)*
