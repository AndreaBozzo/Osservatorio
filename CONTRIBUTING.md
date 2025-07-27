# Contributing to Osservatorio ISTAT Data Platform

Grazie per il tuo interesse nel contribuire al progetto Osservatorio ISTAT! 🎉

Questo documento fornisce le linee guida per contribuire al progetto in modo efficace e coerente.

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Project Structure](#-project-structure)
- [Development Workflow](#-development-workflow)
- [Testing Guidelines](#-testing-guidelines)
- [Code Style](#-code-style)
- [Commit Convention](#-commit-convention)
- [Pull Request Process](#-pull-request-process)
- [Issue Guidelines](#-issue-guidelines)
- [Architecture Principles](#-architecture-principles)

## 🤝 Code of Conduct

Questo progetto aderisce a un codice di condotta basato sul rispetto reciproco:

- **Rispetto**: Tratta tutti i collaboratori con cortesia e professionalità
- **Inclusività**: Accogliamo contributi da sviluppatori di tutti i livelli
- **Costruttività**: Fornisci feedback costruttivo e specifico
- **Collaborazione**: Lavoriamo insieme per migliorare il progetto

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.9+
python --version

# Git
git --version

# Strumenti di sviluppo raccomandati
pip install pre-commit black isort flake8 pytest
```

### Quick Start

```bash
# 1. Fork e clone del repository
git clone https://github.com/YOUR_USERNAME/Osservatorio.git
cd Osservatorio

# 2. Setup ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Installa dipendenze
pip install -e .
pip install -r requirements-dev.txt

# 4. Setup pre-commit hooks
pre-commit install

# 5. Verifica setup
python -m pytest tests/ -v
```

## 🛠️ Development Setup

### Environment Configuration

```bash
# Copia il file di configurazione di esempio
cp .env.example .env

# Configura le variabili necessarie:
# - Database paths
# - API endpoints
# - Authentication settings
```

### Database Setup

```bash
# Crea le directory necessarie
mkdir -p data/databases data/cache data/raw data/processed

# Inizializza i database
python scripts/setup_database.py

# Verifica connessioni
python -c "from src.database.sqlite.manager import get_metadata_manager; print('SQLite OK')"
```

## 📁 Project Structure

```
Osservatorio/
├── src/                    # Codice sorgente principale
│   ├── api/               # FastAPI REST API
│   ├── auth/              # Sistema autenticazione
│   ├── database/          # Layer database (SQLite + DuckDB)
│   ├── integration_clients/ # Client per API esterne
│   ├── pipeline/          # Pipeline dati ETL
│   └── utils/             # Utility e helper
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance tests
├── docs/                  # Documentazione
├── scripts/               # Script utility e deployment
└── data/                  # Dati e cache (git-ignored)
```

## 🔄 Development Workflow

### Branch Strategy

```bash
# Branch principali
main              # Production-ready code
develop           # Integration branch per feature

# Branch temporanei
feature/issue-X   # Nuove funzionalità
bugfix/issue-X    # Bug fixes
hotfix/issue-X    # Fix urgenti per production
```

### Workflow Completo

```bash
# 1. Crea branch per la tua issue
git checkout -b feature/issue-42

# 2. Sviluppa e testa
# ... code changes ...
python -m pytest tests/ -v

# 3. Commit con convenzioni
git add .
git commit -m "feat: add PowerBI direct query support

- Implement OData v4 endpoint
- Add authentication middleware
- Include performance optimizations

Closes #42"

# 4. Push e PR
git push origin feature/issue-42
# Apri PR via GitHub UI
```

## 🧪 Testing Guidelines

### Test Categories

```bash
# Unit tests (fast, isolated)
python -m pytest tests/unit/ -v

# Integration tests (database, API)
python -m pytest tests/integration/ -v

# Performance tests
python -m pytest tests/performance/ -v

# Completa test suite
python -m pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

```python
# Example: Unit test
def test_dataset_validation():
    """Test dataset ID validation logic."""
    from src.utils.validators import validate_dataset_id

    # Valid cases
    assert validate_dataset_id("DCIS_POPRES") == "DCIS_POPRES"

    # Invalid cases
    with pytest.raises(ValueError):
        validate_dataset_id("")
```

### Test Requirements

- **Coverage**: Minimo 80% per nuovo codice
- **Fast**: Unit tests <100ms, integration <5s
- **Isolated**: No dependencies tra test
- **Descriptive**: Nomi test chiari e specifici

## 🎨 Code Style

### Python Style Guide

```python
# Usa Black per formattazione automatica
black src/ tests/

# Isort per import organization
isort src/ tests/

# Flake8 per linting
flake8 src/ tests/
```

### Naming Conventions

```python
# Variabili e funzioni: snake_case
dataset_id = "DCIS_POPRES"
def get_dataset_metadata():

# Classi: PascalCase
class DatasetManager:

# Costanti: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30

# Moduli/file: lowercase
# database_manager.py
```

### Documentation

```python
def process_dataset(dataset_id: str, options: Dict[str, Any]) -> ProcessResult:
    """Process ISTAT dataset with specified options.

    Args:
        dataset_id: ISTAT dataset identifier (e.g., 'DCIS_POPRES')
        options: Processing configuration options

    Returns:
        ProcessResult with success status and metadata

    Raises:
        ValueError: If dataset_id is invalid
        ProcessingError: If processing fails

    Example:
        >>> result = process_dataset('DCIS_POPRES', {'format': 'json'})
        >>> print(result.status)
        'success'
    """
```

## 📝 Commit Convention

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: Nuova funzionalità
- **fix**: Bug fix
- **docs**: Modifiche documentazione
- **style**: Formattazione, missing semicolons, etc.
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Aggiunta o modifica test
- **chore**: Manutenzione, build tasks, etc.

### Examples

```bash
# Feature commit
git commit -m "feat(api): add OData v4 endpoint for PowerBI

- Implement service document and metadata endpoints
- Add query options support ($select, $filter, $top)
- Include authentication middleware integration
- Performance target: <500ms for 10k records

Closes #29"

# Bug fix commit
git commit -m "fix(database): resolve SQLite schema migration issue

- Fix missing scopes_json column in api_credentials table
- Add proper error handling for schema updates
- Include backward compatibility for existing installations

Fixes #50"
```

## 🔄 Pull Request Process

### PR Checklist

- [ ] **Issue Reference**: PR linked a issue specifica
- [ ] **Tests**: Nuovi test per nuovo codice, tutti i test passano
- [ ] **Documentation**: README e docs aggiornati se necessario
- [ ] **Code Style**: Pre-commit hooks passano
- [ ] **Performance**: No regressioni performance
- [ ] **Breaking Changes**: Documentati e giustificati

### PR Description Template

```markdown
## 📋 Description
Brief description of changes and motivation.

## 🔗 Related Issue
Closes #42

## 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

## 📊 Performance Impact
- No performance impact / Improves performance by X% / etc.

## 🔄 Breaking Changes
None / List any breaking changes

## 📸 Screenshots
If applicable, add screenshots to demonstrate changes.
```

### Review Process

1. **Automated Checks**: CI/CD pipeline deve passare
2. **Code Review**: Almeno 1 approval da maintainer
3. **Testing**: Reviewer testa funzionalità se applicabile
4. **Documentation**: Verifica documentazione aggiornata

## 📋 Issue Guidelines

### Creating Issues

```markdown
# Bug Report Template
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g. Windows 10]
- Python version: [e.g. 3.9.7]
- Project version: [e.g. 1.0.0]
```

### Labels Usage

- **Priority**: `priority: critical/high/medium/low`
- **Type**: `type: feature/bug/docs/refactor`
- **Area**: `area: api/database/pipeline/frontend`
- **Status**: `status: ready/in progress/blocked`
- **Effort**: `effort: minutes/hours/days/weeks`

## 🏗️ Architecture Principles

### Design Philosophy

1. **Modularity**: Componenti indipendenti e riusabili
2. **Testability**: Codice facilmente testabile
3. **Performance**: Ottimizzazioni mirate e misurabili
4. **Security**: Security by design
5. **Documentation**: Codice auto-documentante

### Technology Stack

- **Backend**: Python 3.9+, FastAPI, SQLite, DuckDB
- **Frontend**: Streamlit dashboard
- **Testing**: pytest, coverage
- **CI/CD**: GitHub Actions
- **Code Quality**: pre-commit, black, isort, flake8

### Architecture Patterns

- **Repository Pattern**: Database access abstraction
- **Factory Pattern**: Export system flexibility
- **Dependency Injection**: Configuration and testing
- **Event-Driven**: Pipeline processing
- **RESTful APIs**: Standard HTTP interfaces

## 🆘 Getting Help

### Resources

- **Documentation**: `docs/` directory
- **API Docs**: http://localhost:8000/docs (quando FastAPI è in esecuzione)
- **Issues**: GitHub Issues per domande specifiche
- **Discussions**: GitHub Discussions per conversazioni generali

### Contact

- **Project Maintainer**: [Andrea Bozzo](https://github.com/AndreaBozzo)
- **Issues**: Usa GitHub Issues per bug reports e feature requests
- **Questions**: Usa GitHub Discussions per domande generali

## 🎯 Contributing Areas

### High Priority Areas

- **Testing**: Migliorare coverage test
- **Documentation**: Esempi e tutorial
- **Performance**: Ottimizzazioni query e caching
- **Integrations**: Nuovi connettori BI tools

### Good First Issues

Cerca issues con label `good first issue` per iniziare a contribuire.

---

## 📜 License

Contribuendo a questo progetto, accetti che i tuoi contributi saranno sotto la stessa [MIT License](LICENSE) del progetto.

**Grazie per contribuire al progetto Osservatorio ISTAT! 🚀**
