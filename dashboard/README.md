# Dashboard Components

Questa directory contiene tutti i componenti dell'interfaccia utente del progetto Osservatorio ISTAT.

## Struttura

```
dashboard/
├── app.py              # Applicazione Streamlit principale
├── index.html          # Landing page statica (GitHub Pages)
└── README.md           # Questa documentazione
```

## File Principali

### `app.py`
- **Scopo**: Applicazione Streamlit interattiva per la visualizzazione dei dati ISTAT
- **Entry Point**: Utilizzato tramite `streamlit_app.py` nella root
- **Funzionalità**:
  - Dashboard interattivo con 3 categorie (popolazione, economia, lavoro)
  - Visualizzazioni con Plotly
  - Cache per performance
  - Design responsive

### `index.html`
- **Scopo**: Landing page statica per GitHub Pages
- **Funzionalità**:
  - Presentazione del progetto
  - Link al dashboard Streamlit live
  - Statistiche del progetto
  - Documentazione tecnica
  - Design responsive con Tailwind CSS

## Deployment

### Streamlit Cloud
- **URL**: https://osservatorio-dashboard.streamlit.app/
- **Entry Point**: `streamlit_app.py` (nella root) → `dashboard/app.py`
- **Configurazione**: Auto-deploy da branch main

### GitHub Pages
- **URL**: https://andreabozzo.github.io/Osservatorio/ (se configurato)
- **File**: `dashboard/index.html`
- **Configurazione**: Manuale via repository settings

## Sviluppo Locale

```bash
# Streamlit app
streamlit run dashboard/app.py

# Landing page (serve localmente)
python -m http.server 8000
# Poi apri http://localhost:8000/dashboard/index.html
```

## Note

- **Separazione delle responsabilità**: Streamlit per interattività, HTML statico per presentazione
- **Single Entry Point**: `streamlit_app.py` rimane nella root per compatibilità Streamlit Cloud
- **Path Import**: `from dashboard.app import main` per import pulito
