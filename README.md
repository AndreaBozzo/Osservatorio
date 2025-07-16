# Osservatorio - ISTAT Data Processing System

Sistema di elaborazione e analisi dati ISTAT con integrazione Tableau e PowerBI per la visualizzazione e analisi di statistiche italiane.

## 🚀 Quick Start

## 📋 Prerequisiti

- Python 3.8+
- PowerShell (per script di download)
- Account Tableau Server (opzionale)
- Account PowerBI Service (opzionale)
- Azure AD App Registration (per PowerBI API)

## 🛠️ Installazione

```bash
# Clone del repository
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio

# Creazione ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows

# Installazione dipendenze
pip install -r requirements.txt

# Setup configurazione
cp .env.example .env
# Modifica .env con le tue credenziali
```

## 🚀 Uso Base

### Conversione Dati per Tableau
```bash
# Scarica dati ISTAT
powershell scripts/download_istat_data.ps1

# Converti per Tableau
python convert_to_tableau.py
```

### Conversione Dati per PowerBI
```bash
# Scarica dati ISTAT
powershell scripts/download_istat_data.ps1

# Converti per PowerBI
python convert_to_powerbi.py
```

### Test API
```bash
# Test connettività ISTAT
python src/api/istat_api.py

# Test connettività PowerBI
python src/api/powerbi_api.py
```

## 📁 Struttura Progetto

```
src/
├── api/                    # API clients
│   ├── istat_api.py       # Client ISTAT SDMX API
│   ├── powerbi_api.py     # Client PowerBI REST API
│   └── tableau_api.py     # Client Tableau Server API
├── analyzers/             # Analisi e categorizzazione dati
├── scrapers/              # Web scraping
├── utils/                 # Configurazione, logging e gestione file temporanei
└── converters/            # Convertitori dati (spostati da root)

data/
├── raw/                   # Dati ISTAT grezzi (XML)
├── processed/             # Dati processati
│   ├── tableau/          # File pronti per Tableau
│   └── powerbi/          # File pronti per PowerBI
├── cache/                # Cache API responses
└── reports/              # Report e analisi

scripts/                  # Script PowerShell per download e gestione file
tests/                    # Test automatizzati (123 tests)
└── unit/                 # Unit tests (89 tests)
└── integration/          # Integration tests
└── performance/          # Performance tests
```

## 🧪 Testing

```bash
# Esegui tutti i test
pytest

# Test con coverage
pytest --cov=src tests/

# Test specifici
pytest tests/unit/          # 89 unit tests
pytest tests/integration/   # Integration tests
pytest tests/performance/   # Performance tests

# Coverage report HTML
pytest --cov=src --cov-report=html tests/
```

### Test Suite
- **89 unit tests** con 49% code coverage - tutti passanti ✅
- **Integration tests** per workflow completi end-to-end
- **Performance tests** per scalabilità con 1000+ dataflows
- **Coverage report** in `htmlcov/index.html`

## 📊 Features

### Data Processing
- ✅ **Fetch dati ISTAT**: Accesso API SDMX per 509+ dataset
- ✅ **Analisi dataflow**: Categorizzazione automatica per priorità
- ✅ **Conversione formati**: XML → CSV, Excel, JSON, Parquet
- ✅ **Cache intelligente**: Ottimizzazione performance API
- ✅ **Logging strutturato**: Tracciamento completo operazioni

### Business Intelligence
- ✅ **Integrazione Tableau**: Server API, connettori, dashboard
- ✅ **Integrazione PowerBI**: REST API, workspace, refresh automatico
- ✅ **Formati ottimizzati**: Parquet per performance, metadati inclusi
- ✅ **Guide integrate**: Istruzioni step-by-step per import

### Automazione
- ✅ **Script PowerShell**: Download automatico dataset
- ✅ **Workflow completi**: Da XML a dashboard pronte
- ✅ **Test connettività**: Validazione API e configurazioni
- ✅ **Configurazione centralizzata**: Gestione credenziali e environment
- ✅ **Gestione file temporanei**: Sistema automatico di pulizia e organizzazione

## 🔧 Configurazione

### Variabili Ambiente (.env)
```env
# ISTAT API
ISTAT_API_BASE_URL=https://esploradati.istat.it/SDMXWS/rest
ISTAT_API_TIMEOUT=30

# PowerBI
POWERBI_CLIENT_ID=your-app-client-id
POWERBI_CLIENT_SECRET=your-app-client-secret
POWERBI_TENANT_ID=your-azure-tenant-id
POWERBI_WORKSPACE_ID=your-workspace-id

# Tableau
TABLEAU_SERVER_URL=https://your-tableau-server.com
TABLEAU_USERNAME=your-username
TABLEAU_PASSWORD=your-password

# Logging
LOG_LEVEL=INFO
ENABLE_CACHE=true
```

### Setup Azure AD per PowerBI
1. Registra nuova app in Azure AD
2. Aggiungi permessi PowerBI Service API
3. Crea client secret
4. Configura workspace PowerBI
5. Imposta variabili ambiente

## 📈 Categorie Dataset ISTAT

Il sistema categorizza automaticamente i dataset ISTAT in 6 aree principali:

1. **Popolazione** (Priorità 10): Demografia, nascite, morti, stranieri
2. **Economia** (Priorità 9): PIL, inflazione, prezzi, reddito
3. **Lavoro** (Priorità 8): Occupazione, disoccupazione, forze lavoro
4. **Territorio** (Priorità 7): Regioni, province, comuni
5. **Istruzione** (Priorità 6): Scuole, università, formazione
6. **Salute** (Priorità 5): Sanità, ospedali, indicatori sanitari

## 🤝 Contributing

```bash
# Fork il progetto
git clone https://github.com/your-username/Osservatorio.git

# Crea un feature branch
git checkout -b feature/AmazingFeature

# Commit delle modifiche
git commit -m 'Add some AmazingFeature'

# Push al branch
git push origin feature/AmazingFeature

# Apri una Pull Request
```

## 📄 License

Distribuito sotto licenza MIT. Vedi LICENSE per maggiori informazioni.

## 👥 Contatti

**Andrea Bozzo** - [@AndreaBozzo](https://github.com/AndreaBozzo)

**Project Link**: [https://github.com/AndreaBozzo/Osservatorio](https://github.com/AndreaBozzo/Osservatorio)

## 🧹 Gestione File Temporanei

Il sistema include un gestore automatico per file temporanei:

```bash
# Statistiche file temporanei
python scripts/cleanup_temp_files.py --stats

# Pulizia file più vecchi di 24 ore
python scripts/cleanup_temp_files.py --max-age 24

# Organizzazione file dati
python scripts/organize_data_files.py

# Scheduling automatico (Windows/Linux)
python scripts/schedule_cleanup.py --frequency daily
```

### Caratteristiche
- ✅ **Gestione centralizzata**: Singleton pattern per TempFileManager
- ✅ **Cleanup automatico**: Rimozione file vecchi schedulata
- ✅ **Organizzazione automatica**: File XML, log e report in directory appropriate
- ✅ **Gitignore aggiornato**: Esclusione automatica file temporanei
- ✅ **Context managers**: Operazioni sicure su file temporanei

## 📚 Documentazione

- **CLAUDE.md**: Guida per Claude Code AI
- **Guide PowerBI**: `data/processed/powerbi/powerbi_integration_guide_*.md`
- **Guide Tableau**: `data/processed/tableau/tableau_import_instructions_*.md`
- **API Documentation**: Consultare i docstring nei file `src/api/`
- **Script Management**: `scripts/` per automazione e cleanup

---

*Sistema sviluppato per l'analisi e visualizzazione dei dati statistici italiani ISTAT tramite moderne piattaforme BI.*
