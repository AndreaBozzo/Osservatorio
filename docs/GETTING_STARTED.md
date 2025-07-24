# 🚀 Getting Started with Osservatorio

> **Quick setup guide for developers and contributors**

## 📋 Prerequisites

- Python 3.13.3 (verified and tested)
- Git
- 4GB+ RAM recommended for DuckDB analytics

## ⚡ Quick Setup

### 1. Clone and Setup
```bash
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 2. Verify Installation
```bash
# Run tests
pytest tests/ -v

# Check DuckDB integration
python examples/duckdb_demo.py

# Launch dashboard
streamlit run src/dashboard/streamlit_app.py
```

### 3. Development Workflow
```bash
# Code formatting
black .
isort .

# Run linting
flake8 .

# Run performance tests
pytest tests/performance/ -v
```

## 🏗️ Project Structure

```
src/
├── api/                    # API clients (ISTAT, PowerBI)
├── database/duckdb/        # DuckDB analytics engine
├── dashboard/              # Streamlit dashboard
├── data_processing/        # Data transformation
└── utils/                  # Utilities and security

tests/
├── unit/                   # Unit tests
├── integration/            # Integration tests
└── performance/            # Performance benchmarks

docs/
├── core/                   # Core documentation
├── guides/                 # Practical guides
├── reference/              # Reference materials
└── project/                # Project status & roadmap
```

## 🎯 First Contribution

1. **Choose an Issue**: Browse [GitHub Issues](https://github.com/AndreaBozzo/Osservatorio/issues)
2. **Local Development**: Follow setup above
3. **Branch**: Create feature branch `feature/issue-number-description`
4. **Test**: Ensure all tests pass
5. **PR**: Submit with clear description

## 📚 Next Steps

- Read [Development Guide](guides/DEVELOPMENT.md)
- Check [Project Status](project/PROJECT_STATE.md)
- Review [Architecture](core/ARCHITECTURE.md)
- Join [GitHub Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions)

## 🆘 Need Help?

- 📖 Check our [Wiki](https://github.com/AndreaBozzo/Osservatorio/wiki)
- 💬 Ask in [Discussions](https://github.com/AndreaBozzo/Osservatorio/discussions)
- 🐛 Report bugs in [Issues](https://github.com/AndreaBozzo/Osservatorio/issues)

---

**Ready to contribute?** 🚀 Pick an issue and start coding!
