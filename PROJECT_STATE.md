# PROJECT_STATE.md - Osservatorio Project Status & Evolution

> **Ultimo aggiornamento**: Gennaio 2025
> **Versione**: 1.0.0
> **Maintainer**: Andrea Bozzo
> **Scopo**: Sincronizzazione stato progetto per Claude Code e team development

## 📊 Executive Summary

**Osservatorio** è un sistema avanzato di elaborazione dati ISTAT con integrazione Tableau/PowerBI. Il progetto è attualmente in fase di evoluzione da sistema di processing a piattaforma pubblica con dashboard interattive.

### 🎯 Stato Attuale
- ✅ **Core System**: Completato e testato (173 test, 100% passing)
- ✅ **Data Pipeline**: 509+ dataset ISTAT processabili
- ✅ **BI Integration**: Tableau + PowerBI funzionanti
- 🔄 **In Progress**: Dashboard pubblica + CI/CD
- ⏳ **Planned**: REST API + Containerizzazione

## 🏗️ Architettura Attuale

```
Sistema Monolitico Python → Target: Microservizi + Dashboard
├── Data Processing Core ✅
├── File Converters ✅
├── BI Integration ✅
├── Test Suite ✅
└── Dashboard 🔄 (IN SVILUPPO)
```

### 📁 Struttura Repository
```bash
Osservatorio/
├── src/                    # ✅ Core completato
│   ├── api/               # ISTAT, PowerBI, Tableau APIs
│   ├── converters/        # XML → CSV/Excel/Parquet/JSON
│   ├── analyzers/         # Categorizzazione dataset
│   └── utils/             # Security, logging, config
├── data/                  # ✅ Storage strutturato
├── scripts/               # ✅ Automazione
├── tests/                 # ✅ 173 test (100% passing)
├── dashboard/             # 🔄 NUOVO - In sviluppo
│   ├── public/           # Streamlit dashboard
│   ├── monitoring/       # Sistema monitoring
│   └── web/              # Landing page
└── api/                   # ⏳ FUTURO - REST API
```

## 🚀 Piano Evolutivo - FASE 1 (In Corso)

### 🎯 Obiettivi Fase 1 (Gennaio-Marzo 2025)

**FOCUS PRIMARIO: Visibilità Pubblica**

1. **Dashboard Interattiva** (Priorità MAX)
   - Streamlit per prototipazione rapida
   - Deploy su Streamlit Cloud (gratuito)
   - Visualizzazioni: popolazione, economia, lavoro
   - Filtri interattivi per regione/periodo

2. **Landing Page**
   - Design moderno con Tailwind CSS
   - Metriche live dal sistema
   - Link a dashboard e documentazione
   - Deploy su Vercel/Netlify

3. **CI/CD Pipeline**
   - GitHub Actions per test automatici
   - Deploy automatico dashboard
   - Quality gates (coverage, linting)
   - Notifiche Slack/Discord

4. **Monitoring Dashboard**
   - Status API ISTAT in tempo reale
   - Metriche di utilizzo
   - Queue processing status
   - Uptime monitoring

### 📋 Task List Immediata

```markdown
## Week 1-2 (Current)
- [ ] Setup dashboard/ directory structure
- [ ] Create basic Streamlit dashboard
- [ ] Implement first visualization (popolazione)
- [ ] Setup GitHub Actions basic pipeline
- [ ] Deploy landing page to GitHub Pages

## Week 3-4
- [ ] Add economia & lavoro visualizations
- [ ] Implement interactive filters
- [ ] Add data refresh automation
- [ ] Setup Streamlit Cloud deployment
- [ ] Create monitoring dashboard base

## Week 5-6
- [ ] Polish UI/UX dashboard
- [ ] Add download functionality
- [ ] Implement caching strategy
- [ ] Setup proper logging/monitoring
- [ ] Create API documentation

## Week 7-8
- [ ] Performance optimization
- [ ] Security review
- [ ] Documentation update
- [ ] Beta testing with users
- [ ] Public launch preparation
```

## 💻 Codice Dashboard - Quick Start

### 1. Streamlit Dashboard Base
```python
# File: dashboard/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from src.api.istat_api import IstatAPI
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter

st.set_page_config(
    page_title="Osservatorio ISTAT",
    page_icon="🇮🇹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache data for performance
@st.cache_data(ttl=3600)
def load_population_data():
    api = IstatAPI()
    converter = IstatXMLToPowerBIConverter()

    # Fetch and convert data
    xml_data = api.get_data("DCIS_POPRES1", {"startPeriod": "2020"})
    result = converter.convert_xml_to_powerbi(
        xml_data,
        "DCIS_POPRES1",
        "Popolazione Residente"
    )

    # Load converted data
    df = pd.read_csv(result['files_created']['csv_file'])
    return df

def main():
    st.title("🇮🇹 Osservatorio Dati ISTAT")
    st.markdown("### La piattaforma open-source per l'analisi dei dati statistici italiani")

    # Sidebar
    st.sidebar.header("Filtri")
    category = st.sidebar.selectbox(
        "Categoria",
        ["Popolazione", "Economia", "Lavoro", "Territorio", "Istruzione", "Salute"]
    )

    # Main content
    if category == "Popolazione":
        render_population_dashboard()
    # ... other categories

def render_population_dashboard():
    st.header("📊 Analisi Popolazione")

    # Load data
    with st.spinner("Caricamento dati..."):
        df = load_population_data()

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_pop = df['Value'].sum()
        st.metric("Popolazione Totale", f"{total_pop:,.0f}", "↑ 0.3%")

    # Visualizations
    fig = px.line(df, x='TIME_PERIOD', y='Value',
                  color='Territory',
                  title='Trend Popolazione per Regione')
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
```

### 2. Deployment Configuration
```yaml
# File: .streamlit/config.toml
[theme]
primaryColor = "#0066CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
port = 8501
```

### 3. GitHub Actions CI/CD
```yaml
# File: .github/workflows/dashboard-deploy.yml
name: Deploy Dashboard

on:
  push:
    branches: [main]
    paths:
      - 'dashboard/**'
      - 'src/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install streamlit pytest

      - name: Run tests
        run: pytest tests/unit/test_dashboard.py

      - name: Deploy to Streamlit Cloud
        env:
          STREAMLIT_TOKEN: ${{ secrets.STREAMLIT_TOKEN }}
        run: |
          # Streamlit deployment logic
```

## 📊 Metriche di Progetto

### Performance Attuali
| Metrica | Valore | Target |
|---------|--------|--------|
| Test Coverage | 41% | 70% |
| Test Success | 100% | 100% |
| API Response | ~500ms | <200ms |
| Dataset Available | 509+ | 600+ |
| Documentation | 85% | 95% |

### KPI Dashboard (Target Fase 1)
| KPI | Target | Timeline |
|-----|--------|----------|
| Dashboard Views | 1000+/mese | 2 mesi |
| GitHub Stars | 50+ | 3 mesi |
| API Users | 10+ | 3 mesi |
| Uptime | 99%+ | Immediato |
| Load Time | <2s | 1 mese |

## 🛠️ Stack Tecnologico

### Current Stack
- **Backend**: Python 3.8+, FastAPI (planned)
- **Data Processing**: Pandas, XML parsing
- **Testing**: Pytest, Coverage.py
- **BI Integration**: Tableau API, PowerBI API
- **Security**: Path validation, HTTPS enforcement

### Dashboard Stack (New)
- **Frontend**: Streamlit, Plotly, Tailwind CSS
- **Deployment**: Streamlit Cloud, Vercel, GitHub Pages
- **Monitoring**: Prometheus (planned), Grafana (planned)
- **CI/CD**: GitHub Actions
- **Analytics**: Google Analytics, Plausible

## 📝 Note per Claude Code

### Priorità di Sviluppo
1. **Dashboard Streamlit** - MASSIMA PRIORITÀ
2. **CI/CD Pipeline** - Setup base per deploy automatico
3. **Landing Page** - Visibilità progetto
4. **Monitoring** - Dashboard stato sistema
5. **Documentation** - Aggiornamento continuo

### Convenzioni Codice
- Docstring Google style per tutte le funzioni
- Type hints ovunque possibile
- Test per ogni nuova feature
- Secure by default (validazione input)
- Logging strutturato con Loguru

### File Critici da Non Modificare
- `src/utils/secure_path.py` - Security core
- `src/api/istat_api.py` - API stabile
- Test esistenti in `tests/` - Devono continuare a passare

### Aree di Sviluppo Libero
- `dashboard/` - Nuova directory per UI
- `api/` - Futura REST API
- `docs/` - Documentazione aggiuntiva
- `scripts/dashboard/` - Script di supporto dashboard

## 🚦 Status Componenti

| Componente | Status | Note |
|------------|--------|------|
| ISTAT API Client | ✅ Stabile | Non modificare |
| PowerBI Converter | ✅ Stabile | Test completi |
| Tableau Converter | ✅ Stabile | Test completi |
| Secure Path | ✅ Stabile | Core security |
| Dashboard | 🔄 In sviluppo | Focus attuale |
| REST API | ⏳ Pianificato | Fase 2 |
| Docker | ⏳ Pianificato | Fase 2 |
| ML Pipeline | ⏳ Pianificato | Fase 3 |

## 🔗 Link Utili

- **Repository**: https://github.com/AndreaBozzo/Osservatorio
- **ISTAT API**: https://sdmx.istat.it/SDMXWS/rest/
- **Streamlit Docs**: https://docs.streamlit.io/
- **Plotly Docs**: https://plotly.com/python/
- **GitHub Actions**: https://docs.github.com/en/actions

## 📅 Prossimi Step Immediati

1. **Creare branch `feature/dashboard`**
2. **Setup struttura dashboard/**
3. **Implementare prima visualizzazione**
4. **Deploy test su Streamlit Cloud**
5. **Raccogliere feedback early adopters**

---

**Nota**: Questo file deve essere aggiornato ad ogni milestone significativa per mantenere Claude Code sincronizzato con lo stato del progetto.
