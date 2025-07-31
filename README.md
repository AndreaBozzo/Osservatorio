# 🇮🇹 Osservatorio - Italian Statistical Data Platform

> **Production-ready platform for accessing and processing ISTAT (Italian National Statistics) data with enterprise-grade reliability and performance.**

[![Live Dashboard](https://img.shields.io/badge/Dashboard-Live%20✅-green.svg)](https://osservatorio-dashboard.streamlit.app/)
[![Quality](https://img.shields.io/badge/Quality-83.3%25%20EXCELLENT-green.svg)](quality_assessment_report.json)
[![Python](https://img.shields.io/badge/Python-3.13.3-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/Tests-540%2B%20passing-green.svg)](tests/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](docs/project/PROJECT_STATE.md)

## 🎯 What is Osservatorio?

**Osservatorio** makes Italian statistical data accessible to everyone. Whether you're a researcher, analyst, or decision-maker, our platform provides reliable access to ISTAT's 509+ datasets with in-development enterprise-grade processing and visualization capabilities.

### ✨ Key Benefits
- **🚀 In-Development**: 83.3% EXCELLENT quality rating with comprehensive testing
- **⚡ High Performance**: <100ms cache response, 55x faster batch processing
- **🛡️ Enterprise Security**: Circuit breaker, rate limiting, comprehensive monitoring
- **🔄 Fault Tolerant**: Automatic fallback systems ensure continuous availability
- **📊 BI Integration**: Ready-to-use PowerBI templates and data processing

## 🚀 Quick Start (5 minutes)

### Try the Live Dashboard
**👉 [Visit our live dashboard](https://osservatorio-dashboard.streamlit.app/)** - No installation required!

### Run Locally
```bash
# 1. Clone and setup
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install and run
pip install -r requirements.txt
python quality_demo.py                          # See quality demonstration
streamlit run dashboard/app.py                  # Start dashboard at localhost:8501
```

### Quick Health Check
```bash
python -c "from src.api.production_istat_client import ProductionIstatClient; client=ProductionIstatClient(); print('✅ System ready:', client.get_status()['status'])"
```

## 🏗️ Architecture Overview

Osservatorio uses a **hybrid architecture** optimized for both reliability and performance:

```
🚀 ProductionIstatClient (Enterprise Patterns)
    ↓
🔄 Unified Repository (Smart Data Routing)
    ↓
📊 DuckDB Analytics + 🗃️ SQLite Metadata + 💾 Cache Fallback
    ↓
🇮🇹 ISTAT SDMX API (509+ datasets)
```

### Core Components
- **ProductionIstatClient**: Enterprise-ready API client with circuit breaker and rate limiting
- **Hybrid Storage**: SQLite for metadata, DuckDB for analytics, cache for offline capability
- **Quality Assurance**: Comprehensive testing with 83.3% EXCELLENT quality rating
- **Monitoring**: Real-time performance metrics and health checking

## 📊 What You Can Do

### For Data Analysts
```python
from src.api.production_istat_client import ProductionIstatClient

# Access Italian statistical data reliably
client = ProductionIstatClient(enable_cache_fallback=True)
dataflows = client.fetch_dataflows(limit=10)
dataset = client.fetch_dataset("DCIS_POPRES1")  # Population data
```

### For Researchers
- **509+ ISTAT Datasets**: Population, economy, employment, education, health data
- **Multi-format Export**: CSV, Excel, JSON, Parquet - ready for any analysis tool
- **Quality Validation**: Built-in data quality scoring and validation
- **Historical Data**: Access to time series and territorial comparisons

### For Business Intelligence
- **PowerBI Ready**: Automatic star schema optimization and template generation
- **Real-time Integration**: OData endpoints for live dashboard connectivity
- **Enterprise Security**: JWT authentication, rate limiting, audit logging
- **Scalable Processing**: Concurrent batch operations with intelligent caching

## 🛡️ Production Features

### Reliability (Demonstrated)
- **Circuit Breaker**: Automatic fault detection and recovery
- **Cache Fallback**: <100ms response when API unavailable
- **Rate Limiting**: 100 requests/hour with intelligent coordination
- **Health Monitoring**: Real-time system status and metrics

### Performance (Benchmarked)
- **Client Initialization**: 0.005s (1000x under threshold)
- **Repository Setup**: 0.124s (8x under threshold)
- **Batch Processing**: 55.2x improvement over sequential processing
- **Memory Usage**: Linear scaling with optimized resource management

### Security (Audited)
- **SQL Injection Protection**: All queries parameterized
- **Path Validation**: Directory traversal prevention
- **Error Handling**: Secure error messages without information disclosure
- **Audit Trail**: Comprehensive logging and monitoring

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
- **Quality First**: 83.3% EXCELLENT quality maintained
- **Test Coverage**: 540+ tests, 100% passing rate
- **Security Focused**: 0 high-severity issues (Bandit verified)
- **Performance Tested**: All benchmarks must exceed thresholds

## 🎯 Use Cases

- **🏛️ Government Agencies**: Access official Italian statistics for policy making
- **🏢 Businesses**: Market research and economic analysis with reliable data
- **🎓 Researchers**: Academic research with comprehensive Italian datasets
- **📊 Analysts**: BI dashboards and reporting with PowerBI integration
- **🔍 Journalists**: Data journalism with verified official sources

## 🏆 Quality Metrics

**Overall Quality Score: 83.3% EXCELLENT**

- ✅ **Fast Initialization**: 0.005s (1000x under threshold)
- ✅ **Repository Performance**: 0.124s hybrid setup
- ✅ **Cache Performance**: <0.001s response time
- ✅ **Monitoring Active**: Real-time metrics collection
- ✅ **Async Processing**: 55.2x sequential improvement

*Full quality report available in [quality_assessment_report.json](quality_assessment_report.json)*

## 📞 Support

- **🐛 Issues**: [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues) for bug reports
- **💬 Discussions**: [GitHub Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions) for questions
- **📚 Documentation**: [docs/](docs/) folder for comprehensive guides
- **🎯 Live Dashboard**: [osservatorio-dashboard.streamlit.app](https://osservatorio-dashboard.streamlit.app/)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**🎯 Ready to explore Italian statistical data?**
**👉 [Try our live dashboard](https://osservatorio-dashboard.streamlit.app/) or run `python quality_demo.py` locally**

*Made with ❤️ for the Italian data community*
