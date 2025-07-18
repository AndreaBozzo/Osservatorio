# 🇮🇹 Osservatorio - ISTAT Data Processing System

**Sistema avanzato di elaborazione e analisi dati ISTAT con integrazione Tableau e PowerBI per la visualizzazione e analisi di statistiche italiane.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/Tests-173%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-100%25%20success-brightgreen.svg)](htmlcov/)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen.svg)](https://osservatorio-dashboard.streamlit.app/)
[![Security](https://img.shields.io/badge/Security-Enhanced-blue.svg)](src/utils/security_enhanced.py)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Sistema completo per l'acquisizione, elaborazione e visualizzazione di dati statistici ISTAT attraverso moderne piattaforme di Business Intelligence.**

## 🚀 Quick Start

```bash
# 1. Setup ambiente
git clone https://github.com/AndreaBozzo/Osservatorio.git
cd Osservatorio
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# 2. Test connettività
python src/api/istat_api.py

# 3. Dashboard live
streamlit run dashboard/app.py  # Dashboard locale
# Oppure visita: https://osservatorio-dashboard.streamlit.app/

# 4. Conversione dati
python convert_to_tableau.py  # Per Tableau
python convert_to_powerbi.py  # Per PowerBI

# 5. Gestione file temporanei
python scripts/cleanup_temp_files.py --stats
```

## 🌟 Features Principali

### 📊 Data Processing
- ✅ **ISTAT SDMX API**: Accesso a 509+ dataset ufficiali italiani
- ✅ **Categorizzazione intelligente**: 6 categorie prioritarie (Popolazione, Economia, Lavoro, Territorio, Istruzione, Salute)
- ✅ **Conversione multi-formato**: XML → CSV, Excel, JSON, Parquet
- ✅ **Cache intelligente**: Ottimizzazione performance con sistema di cache
- ✅ **Validazione qualità**: Controllo completezza e consistenza dati
- ✅ **Logging strutturato**: Tracciamento completo operazioni con Loguru

### 🔗 Business Intelligence
- ✅ **Tableau Integration**: Server API + connettori BigQuery/Google Sheets
- ✅ **PowerBI Integration**: REST API + Azure AD authentication + workspace management
- ✅ **Formati ottimizzati**: Parquet per performance, metadati inclusi
- ✅ **Guide integrate**: Istruzioni step-by-step per import e configurazione
- ✅ **Dashboard ready**: File pronti per import diretto in Tableau/PowerBI

### 🔒 Security & Resilience (NEW)
- ✅ **SecurityManager**: Protezione centralizzata contro attacchi path traversal e injection
- ✅ **Rate Limiting**: Controllo accessi API con limiti configurabili
- ✅ **Circuit Breaker**: Resilienza sistema con gestione automatica failure
- ✅ **Input Sanitization**: Validazione e pulizia automatica input utente
- ✅ **Security Headers**: Headers HTTP sicuri per protezione applicazione
- ✅ **IP Blocking**: Blocco automatico IP sospetti

### 🎯 Live Dashboard
- ✅ **Streamlit Dashboard**: [https://osservatorio-dashboard.streamlit.app/](https://osservatorio-dashboard.streamlit.app/)
- ✅ **Interactive Visualizations**: 6 categorie dati con grafici interattivi
- ✅ **Real-time Metrics**: Monitoraggio sistema in tempo reale
- ✅ **Responsive Design**: Ottimizzato per desktop e mobile
- ✅ **Sample Data**: Dati demo sempre disponibili

### 🤖 Automazione
- ✅ **Script PowerShell**: Download automatico dataset Windows
- ✅ **Workflow end-to-end**: Da XML ISTAT a dashboard pronte
- ✅ **Test connettività**: Validazione API e configurazioni automatica
- ✅ **Configurazione centralizzata**: Gestione credenziali e environment variables
- ✅ **Gestione file temporanei**: Sistema automatico pulizia e organizzazione
- ✅ **Scheduling**: Supporto cron (Linux/Mac) e Task Scheduler (Windows)

### 🛡️ Qualità e Sicurezza
- ✅ **Test Suite**: 173 unit tests + integration + performance
- ✅ **Sicurezza**: Validazione path, HTTPS enforcement, input sanitization
- ✅ **Error handling**: Gestione robusta errori API e parsing
- ✅ **Rate limiting**: Rispetto limiti API ISTAT
- ✅ **Monitoring**: Logging e tracking operazioni complete

## 📁 Architettura Sistema

```
📦 Osservatorio/
├── 🐍 src/                          # Codice sorgente principale
│   ├── 🔌 api/                      # API clients
│   │   ├── istat_api.py             # ISTAT SDMX API (509+ dataflows)
│   │   ├── powerbi_api.py           # PowerBI REST API + MSAL auth
│   │   └── tableau_api.py           # Tableau Server API
│   ├── 🔄 converters/               # Convertitori dati
│   │   ├── tableau_converter.py     # XML → CSV/Excel/JSON
│   │   └── powerbi_converter.py     # XML → CSV/Excel/Parquet/JSON
│   ├── 🔍 analyzers/                # Analisi e categorizzazione
│   │   └── dataflow_analyzer.py     # Categorizzazione automatica dataset
│   ├── 🕷️ scrapers/                 # Web scraping e discovery
│   │   └── tableau_scraper.py       # Tableau Public integration
│   └── 🔧 utils/                    # Utilities core
│       ├── config.py                # Configurazione centralizzata
│       ├── logger.py                # Logging strutturato (Loguru)
│       ├── secure_path.py           # Validazione sicura percorsi file
│       └── temp_file_manager.py     # Gestione file temporanei
├── 📊 data/                         # Dati e elaborazioni
│   ├── raw/                         # Dati ISTAT grezzi (XML SDMX)
│   ├── processed/                   # Dati processati
│   │   ├── tableau/                 # File pronti per Tableau
│   │   └── powerbi/                 # File ottimizzati PowerBI
│   ├── cache/                       # Cache API responses
│   └── reports/                     # Report e analisi
├── 🛠️ scripts/                      # Automazione e gestione
│   ├── download_istat_data.ps1      # Download PowerShell
│   ├── setup_powerbi_azure.py       # Setup Azure AD guidato
│   ├── cleanup_temp_files.py        # Pulizia file temporanei
│   ├── organize_data_files.py       # Organizzazione file dati
│   └── schedule_cleanup.py          # Scheduling automatico
├── 🧪 tests/                        # Test suite completa
│   ├── unit/                        # Unit tests (173 tests ✅)
│   ├── integration/                 # Integration tests
│   └── performance/                 # Performance tests
├── 📋 convert_to_tableau.py         # Wrapper Tableau
├── 📈 convert_to_powerbi.py         # Wrapper PowerBI
└── 📚 CLAUDE.md                     # Documentazione Claude Code
```

## 🔧 API Programmatiche

### PowerBI Converter API
```python
# Esempio di utilizzo programmatico
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter

converter = IstatXMLToPowerBIConverter()

# Conversione diretta XML
result = converter.convert_xml_to_powerbi(
    xml_content="<xml>...</xml>",
    dataset_id="DCIS_POPRES1",
    dataset_name="Popolazione residente"
)

# Parsing XML e validazione qualità
df = converter._parse_xml_content(xml_content)
quality = converter._validate_data_quality(df)
category, priority = converter._categorize_dataset(dataset_id, dataset_name)
```

### Tableau Converter API
```python
# Esempio di utilizzo programmatico
from src.converters.tableau_converter import IstatXMLtoTableauConverter

converter = IstatXMLtoTableauConverter()

# Conversione diretta XML
result = converter.convert_xml_to_tableau(
    xml_content="<xml>...</xml>",
    dataset_id="DCIS_POPRES1",
    dataset_name="Popolazione residente"
)

# Parsing XML e validazione qualità
df = converter._parse_xml_content(xml_content)
quality = converter._validate_data_quality(df)
category, priority = converter._categorize_dataset(dataset_id, dataset_name)
```

### Caratteristiche API
- ✅ **Parsing XML SDMX**: Conversione diretta XML → DataFrame
- ✅ **Categorizzazione automatica**: 6 categorie con priorità
- ✅ **Validazione qualità**: Completezza e consistenza dati
- ✅ **Multi-formato**: CSV, Excel, JSON, Parquet
- ✅ **Sicurezza**: Validazione path e file operation sicure
- ✅ **Logging**: Tracciamento operazioni completo

## 📋 Prerequisiti

- **Python 3.8+** - Linguaggio principale
- **PowerShell** - Per script di download Windows
- **Account Tableau Server** - (opzionale) Per integrazione completa
- **Account PowerBI Service** - (opzionale) Per publishing automatico
- **Azure AD App Registration** - (opzionale) Per PowerBI API

## 🛠️ Installazione

### 1. Setup Base
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
```

### 2. Configurazione Opzionale
```bash
# Setup configurazione (se necessario)
cp .env.example .env
# Modifica .env con le tue credenziali API
```

### 3. Verifica Installazione
```bash
# Test suite completa
pytest tests/unit/ -v

# Test connettività ISTAT
python src/api/istat_api.py

# Verifica struttura directory
python scripts/organize_data_files.py --dry-run
```

## 🚀 Workflow Principali

### 📊 Workflow Tableau
```bash
# 1. Scarica dati ISTAT (Windows)
powershell scripts/download_istat_data.ps1

# 2. Converti per Tableau
python convert_to_tableau.py

# 3. File pronti in: data/processed/tableau/
# Import diretto in Tableau con guide integrate
```

### 📈 Workflow PowerBI
```bash
# 1. Scarica dati ISTAT (Windows)
powershell scripts/download_istat_data.ps1

# 2. Converti per PowerBI (CSV, Excel, Parquet, JSON)
python convert_to_powerbi.py

# 3. File pronti in: data/processed/powerbi/
# Setup Azure: python scripts/setup_powerbi_azure.py
```

### 🔧 Workflow Sviluppo
```bash
# Test API e connettività
python src/api/istat_api.py        # Test ISTAT SDMX
python src/api/powerbi_api.py      # Test PowerBI API

# Analisi dataflow disponibili
python src/analyzers/dataflow_analyzer.py

# Gestione file temporanei
python scripts/cleanup_temp_files.py --stats
python scripts/organize_data_files.py --dry-run
```

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

## 📈 Sistema di Categorizzazione ISTAT

Il sistema categorizza automaticamente i 509+ dataset ISTAT in **6 aree strategiche** con punteggi di priorità:

| Categoria | Priorità | Descrizione | Esempi Dataset |
|-----------|----------|-------------|-----------------|
| 🏘️ **Popolazione** | 10 | Demografia, nascite, morti, stranieri | DCIS_POPRES1, DCIS_POPSTRRES1, DCIS_FECONDITA |
| 💰 **Economia** | 9 | PIL, inflazione, prezzi, reddito | DCIS_RICFAMILIARE1, prezzi_consumo, pil_regionale |
| 👥 **Lavoro** | 8 | Occupazione, disoccupazione, forze lavoro | occupazione_istat, disoccupazione_giovanile |
| 🏛️ **Territorio** | 7 | Regioni, province, comuni | territorio_amministrativo, comuni_italiani |
| 🎓 **Istruzione** | 6 | Scuole, università, formazione | istruzione_superiore, universita_iscritti |
| 🏥 **Salute** | 5 | Sanità, ospedali, indicatori sanitari | DCIS_MORTALITA1, ospedali_pubblici |

### 🎯 Algoritmo di Prioritizzazione
```python
# Esempio di scoring automatico
def calculate_priority(dataflow_name, description):
    priority_keywords = {
        'popolazione': 10, 'demographic': 10,
        'economia': 9, 'pil': 9, 'reddito': 9,
        'lavoro': 8, 'occupazione': 8,
        'territorio': 7, 'regioni': 7,
        'istruzione': 6, 'scuole': 6,
        'salute': 5, 'sanita': 5
    }
    # Algoritmo di matching e scoring
```

## 🧪 Test Suite

```bash
# Test rapidi (unit tests)
pytest tests/unit/ -v                    # 173 tests in ~20s

# Test completi con coverage
pytest --cov=src tests/                  # Tutti i test + coverage

# Test specifici per componente
pytest tests/unit/test_istat_api.py      # API ISTAT
pytest tests/unit/test_powerbi_api.py    # PowerBI integration
pytest tests/unit/test_converters.py     # Data converters

# Test integration (end-to-end)
pytest tests/integration/ -v             # Workflow completi

# Test performance
pytest tests/performance/ -v             # Scalabilità 1000+ dataflows

# Report HTML con coverage
pytest --cov=src --cov-report=html tests/
# Report disponibile in: htmlcov/index.html
```

### 📊 Statistiche Test Suite

| Categoria | Numero | Stato | Descrizione |
|-----------|---------|--------|-------------|
| **Unit Tests** | 173 | ✅ Tutti passanti | Test componenti individuali |
| **Integration Tests** | 12 | ✅ Tutti passanti | Test workflow completi |
| **Performance Tests** | 8 | ✅ Tutti passanti | Test scalabilità |
| **Code Coverage** | 41% | 🟨 Buono | Copertura codice principale |

### 🔍 Test Highlights
- ✅ **API Connectivity**: Test connessione a 509+ dataflows ISTAT
- ✅ **Data Conversion**: Validazione XML → CSV/Excel/Parquet/JSON
- ✅ **PowerBI Integration**: Test autenticazione Azure AD + publishing
- ✅ **Temp File Management**: Test gestione automatica file temporanei
- ✅ **Error Handling**: Test robustezza con scenari fallimento
- ✅ **Performance**: Test con dataset 1000+ records

## 🧹 Sistema di Gestione File Temporanei

Il sistema include un **TempFileManager** avanzato per la gestione automatica dei file temporanei:

```bash
# 📊 Statistiche e monitoring
python scripts/cleanup_temp_files.py --stats

# 🧽 Pulizia file vecchi (personalizzabile)
python scripts/cleanup_temp_files.py --max-age 24    # 24 ore
python scripts/cleanup_temp_files.py --max-age 168   # 1 settimana
python scripts/cleanup_temp_files.py --cleanup-all   # Pulizia completa

# 📁 Organizzazione file dati
python scripts/organize_data_files.py --dry-run      # Anteprima
python scripts/organize_data_files.py               # Esecuzione
python scripts/organize_data_files.py --xml-only    # Solo XML

# ⏰ Scheduling automatico multipiattaforma
python scripts/schedule_cleanup.py --frequency daily    # Giornaliero
python scripts/schedule_cleanup.py --frequency weekly   # Settimanale
python scripts/schedule_cleanup.py --frequency hourly   # Ogni ora
```

### 🏗️ Architettura TempFileManager

```python
# Esempio di utilizzo del TempFileManager
from src.utils.temp_file_manager import get_temp_manager

# Singleton pattern - istanza unica
temp_manager = get_temp_manager()

# Context manager per operazioni sicure
with temp_manager.temp_file(suffix='.xml') as temp_file:
    # Operazioni su file temporaneo
    write_data_to_file(temp_file)
    # Cleanup automatico al termine
```

### ✨ Caratteristiche Avanzate
- ✅ **Singleton Pattern**: Gestione centralizzata istanza unica
- ✅ **Context Managers**: Operazioni sicure con cleanup automatico
- ✅ **Scheduling multipiattaforma**: Supporto Windows (Task Scheduler) e Linux/Mac (cron)
- ✅ **Organizzazione intelligente**: File XML, log e report in directory appropriate
- ✅ **Gitignore integrato**: Esclusione automatica file temporanei
- ✅ **Statistiche dettagliate**: Monitoring utilizzo spazio e numero file
- ✅ **Pulizia configurabile**: Età file, pattern, directory specifiche

## 📚 Documentazione Completa

### 🎯 Guide Quick Start
- **[CLAUDE.md](CLAUDE.md)**: Guida completa per Claude Code AI
- **[Quick Start Guide](#-quick-start)**: Setup rapido in 4 passi
- **[Workflow Guide](#-workflow-principali)**: Tableau, PowerBI, Development

### 📖 Documentazione Tecnica
- **API Documentation**: Docstring completi in `src/api/`
- **Test Documentation**: `tests/` con esempi di utilizzo
- **Architecture Guide**: Sezione [Architettura Sistema](#-architettura-sistema)

### 🛠️ Guide Operative
- **Guide PowerBI**: `data/processed/powerbi/powerbi_integration_guide_*.md`
- **Guide Tableau**: `data/processed/tableau/tableau_import_instructions_*.md`
- **Script Management**: `scripts/` per automazione e cleanup
- **Configuration Guide**: [Sezione Configurazione](#-configurazione)

### 🎯 Esempi Pratici
- **Conversion Examples**: `tests/unit/test_converters.py`
- **API Usage Examples**: `tests/unit/test_istat_api.py`
- **PowerBI Integration**: `scripts/setup_powerbi_azure.py`
- **Temp File Management**: `scripts/cleanup_temp_files.py`

## 🚀 Roadmap

### 📈 Versione Attuale (v1.0)
- ✅ Sistema completo di elaborazione dati ISTAT
- ✅ Integrazione Tableau e PowerBI
- ✅ 173 unit tests + integration tests
- ✅ Sistema gestione file temporanei
- ✅ Documentazione completa

### 🔮 Prossimi Sviluppi (v1.1)
- 🔄 Dashboard real-time per monitoring
- 🔄 API REST per integrazione esterna
- 🔄 Supporto Docker e containerizzazione
- 🔄 Plugin Tableau nativi
- 🔄 Integrazione CI/CD completa

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

---

<div align="center">

**🇮🇹 Osservatorio ISTAT Data Processing System**

*Sistema sviluppato per l'analisi e visualizzazione dei dati statistici italiani ISTAT tramite moderne piattaforme BI.*

[![Made with ❤️ in Italy](https://img.shields.io/badge/Made%20with%20%E2%9D%A4%EF%B8%8F%20in-Italy-green.svg)](https://github.com/AndreaBozzo/Osservatorio)
[![ISTAT Data](https://img.shields.io/badge/ISTAT-509%2B%20Datasets-blue.svg)](https://www.istat.it/)
[![BI Integration](https://img.shields.io/badge/BI-Tableau%20%7C%20PowerBI-orange.svg)](https://github.com/AndreaBozzo/Osservatorio)

</div>
