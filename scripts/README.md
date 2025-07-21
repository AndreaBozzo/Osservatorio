# 🛠️ Scripts Attivi

Questa cartella contiene tutti gli script operativi del progetto Osservatorio ISTAT.

## 📋 Scripts Disponibili

### 🧪 **Test e CI/CD**

#### `test_ci.py` ⭐ **PRINCIPALE**
- **Scopo**: Runner unificato per test CI/CD con strategie multiple
- **Utilizzo**: `python scripts/test_ci.py --strategy [auto|full|quick|minimal]`
- **Funzionalità**:
  - Strategia `auto`: Fallback automatico da full → quick → minimal
  - Strategia `full`: Suite completa di test (unit + integration + performance)
  - Strategia `quick`: Test rapidi essenziali per CI/CD
  - Strategia `minimal`: Test ultra-robusti senza dipendenze pytest
- **Utilizzo nei workflow**: GitHub Actions `dashboard-deploy.yml`

#### `generate_test_data.py`
- **Scopo**: Generazione dati mock per test automatici
- **Utilizzo**: `python scripts/generate_test_data.py`
- **Funzionalità**: Crea dati di test per evitare chiamate API durante CI/CD
- **Utilizzo nei workflow**: Integrato in `test_ci.py --generate-data`

### 🔧 **Setup e Configurazione**

#### `setup_powerbi_azure.py`
- **Scopo**: Setup guidato per configurazione Azure AD e PowerBI
- **Utilizzo**: `python scripts/setup_powerbi_azure.py`
- **Funzionalità**:
  - Guida step-by-step per Azure AD app registration
  - Configurazione variabili ambiente PowerBI
  - Creazione file .env
  - Verifica configurazione

#### `test_powerbi_upload.py`
- **Scopo**: Test upload dataset PowerBI Service
- **Utilizzo**: `python scripts/test_powerbi_upload.py`
- **Funzionalità**:
  - Test connessione PowerBI Service
  - Upload dataset di test
  - Verifica autenticazione Azure AD

### 📊 **Gestione Dati**

#### `download_istat_data.ps1`
- **Scopo**: Download dataset ISTAT tramite PowerShell
- **Utilizzo**: `powershell scripts/download_istat_data.ps1`
- **Funzionalità**:
  - Download massivo dati ISTAT
  - Gestione cache e retry
  - Ottimizzato per ambiente Windows

#### `organize_data_files.py`
- **Scopo**: Organizzazione automatica file dati
- **Utilizzo**: `python scripts/organize_data_files.py [--dry-run]`
- **Funzionalità**:
  - Organizza file secondo best practices
  - Modalità dry-run per preview
  - Categorizzazione automatica

### 🧹 **Manutenzione**

#### `cleanup_temp_files.py`
- **Scopo**: Pulizia file temporanei del sistema
- **Utilizzo**: `python scripts/cleanup_temp_files.py [--stats] [--max-age HOURS]`
- **Funzionalità**:
  - Pulizia file temporanei tracciati
  - Statistiche utilizzo
  - Configurazione età massima file

#### `schedule_cleanup.py`
- **Scopo**: Scheduling automatico pulizia
- **Utilizzo**: `python scripts/schedule_cleanup.py`
- **Funzionalità**:
  - Configurazione cron jobs (Linux/Mac)
  - Configurazione Task Scheduler (Windows)
  - Pulizia automatica periodica

## 🚀 Comandi Principali

### Test e CI/CD
```bash
# Test automatici con fallback
python scripts/test_ci.py --strategy auto --generate-data

# Test rapidi per CI/CD
python scripts/test_ci.py --strategy quick

# Test minimali ultra-robusti
python scripts/test_ci.py --strategy minimal
```

### Setup PowerBI
```bash
# Setup guidato PowerBI
python scripts/setup_powerbi_azure.py

# Test upload PowerBI
python scripts/test_powerbi_upload.py
```

### Gestione Dati
```bash
# Download dati ISTAT
powershell scripts/download_istat_data.ps1

# Organizza file dati
python scripts/organize_data_files.py --dry-run
python scripts/organize_data_files.py
```

### Manutenzione
```bash
# Statistiche file temporanei
python scripts/cleanup_temp_files.py --stats

# Pulizia file temporanei (24h)
python scripts/cleanup_temp_files.py --max-age 24

# Setup pulizia automatica
python scripts/schedule_cleanup.py
```

## 🔄 Workflow Integration

### GitHub Actions
- **`dashboard-deploy.yml`**: Utilizza `test_ci.py` per test automatici
- **`deploy-landing-page.yml`**: Deployment GitHub Pages

### Documentazione
- **`docs/project/CLAUDE.md`**: Comandi principali documentati
- **`README.md`**: Guida utente con esempi
- **`DEPLOYMENT_GUIDE.md`**: Procedure di deployment

## 📁 Struttura File

```
scripts/
├── README.md                 # Questo file
├── test_ci.py               # 🧪 Test CI/CD unificato
├── generate_test_data.py    # 📊 Generazione dati test
├── setup_powerbi_azure.py   # 🔧 Setup PowerBI
├── test_powerbi_upload.py   # 📤 Test upload PowerBI
├── download_istat_data.ps1  # 📥 Download dati ISTAT
├── organize_data_files.py   # 🗂️ Organizzazione file
├── cleanup_temp_files.py    # 🧹 Pulizia file temporanei
├── schedule_cleanup.py      # ⏰ Scheduling pulizia
└── legacy/                  # 📦 Script obsoleti
    ├── README.md
    ├── migrate_repository.py
    ├── validate_step1_2.py
    ├── test_ci_quick.py
    └── test_ci_minimal.py
```

## 🎯 Best Practices

### Sviluppo
1. **Testare sempre**: Usa `test_ci.py` prima di commit
2. **Generare dati**: Usa `generate_test_data.py` per test offline
3. **Dry-run**: Usa `--dry-run` per preview operazioni

### Manutenzione
1. **Pulizia regolare**: Esegui `cleanup_temp_files.py` settimanalmente
2. **Monitoring**: Usa `--stats` per monitorare utilizzo
3. **Scheduling**: Configura pulizia automatica

### Sicurezza
1. **Validazione**: Tutti gli script validano input
2. **Fallback**: Strategia fallback per test CI/CD
3. **Timeout**: Timeout configurabili per evitare hang

## 🔗 Collegamenti

- **Scripts Legacy**: [`legacy/README.md`](legacy/README.md)
- **Documentazione**: [`../docs/project/CLAUDE.md`](../docs/project/CLAUDE.md)
- **Deployment**: [`../DEPLOYMENT_GUIDE.md`](../DEPLOYMENT_GUIDE.md)

---

*Ultima revisione: Gennaio 2025*
