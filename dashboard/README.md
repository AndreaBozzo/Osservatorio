# Dashboard Osservatorio ISTAT

Dashboard interattiva per la visualizzazione dei dati ISTAT con Streamlit.

## 🚀 Quick Start

### 1. Installazione Dipendenze

```bash
# Dalla root del progetto
pip install -r dashboard/requirements.txt

# Oppure install completo
pip install -r requirements.txt
```

### 2. Preparazione Dati

```bash
# Genera i dati processati
python convert_to_powerbi.py
```

### 3. Avvio Dashboard

```bash
# Dalla root del progetto
streamlit run dashboard/app.py

# Oppure
cd dashboard
streamlit run app.py
```

La dashboard sarà disponibile su: http://localhost:8501

## 📊 Caratteristiche

### Categorie Supportate
- 🏘️ **Popolazione** - Dati demografici completi
- 💰 **Economia** - Indicatori economici
- 👥 **Lavoro** - Mercato del lavoro
- 🏛️ **Territorio** - Dati geografici
- 🎓 **Istruzione** - Sistema educativo
- 🏥 **Salute** - Indicatori sanitari

### Funzionalità
- ✅ **Visualizzazioni interattive** con Plotly
- ✅ **Filtri temporali** per periodo personalizzato
- ✅ **Filtri geografici** per area di interesse
- ✅ **Metriche in tempo reale** del sistema
- ✅ **Export dati** (in sviluppo)
- ✅ **Cache intelligente** per performance

## 🏗️ Architettura

```
dashboard/
├── app.py              # App principale Streamlit
├── requirements.txt    # Dipendenze dashboard
├── README.md          # Documentazione
├── public/            # Assets pubblici
├── monitoring/        # Dashboard monitoring
├── web/              # Landing page
├── data/             # Dati cache
└── utils/            # Utilities dashboard
```

## 🔧 Configurazione

### Streamlit Config
La configurazione è in `.streamlit/config.toml`:

```toml
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
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

### Variabili Ambiente
Il dashboard utilizza la configurazione esistente in `src/utils/config.py`.

## 📈 Performance

### Cache Strategy
- **Data Cache**: 1 ora (3600s) per dati processati
- **System Stats**: 30 minuti (1800s) per statistiche sistema
- **Auto-refresh**: Pulsante manuale per aggiornamento

### Ottimizzazioni
- Lazy loading dei dati
- Chunked data processing
- Minimal DOM updates
- Efficient plot rendering

## 🚀 Deployment

### Local Development
```bash
# Dalla root del progetto
streamlit run dashboard/app.py --server.port 8501

# Oppure dalla directory dashboard
cd dashboard
streamlit run app.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect repository su [share.streamlit.io](https://share.streamlit.io)
3. Configurazione:
   - **App path**: `dashboard/app.py`
   - **Branch**: `main`
   - **Python version**: 3.9+
4. Deploy automatico

**🌐 Live Demo**: https://osservatorio-dashboard.streamlit.app/

### Docker (Future)
```bash
# Build image
docker build -t osservatorio-dashboard .

# Run container
docker run -p 8501:8501 osservatorio-dashboard
```

## 🧪 Testing

### Unit Tests
```bash
# Test dashboard components
pytest tests/unit/test_dashboard.py

# Test con coverage
pytest --cov=dashboard tests/unit/test_dashboard.py
```

### Integration Tests
```bash
# Test completi
pytest tests/integration/test_dashboard_integration.py
```

## 📱 Responsive Design

Il dashboard è ottimizzato per:
- 💻 **Desktop**: Layout wide con sidebar
- 📱 **Mobile**: Layout compact con menu collassabile
- 📊 **Tablet**: Layout intermedio

## 🔐 Security

### Data Protection
- Nessun dato sensibile memorizzato
- Cache locale temporanea
- Validazione input utente
- HTTPS enforcement (produzione)

### Access Control
- Nessuna autenticazione richiesta (pubblico)
- Rate limiting tramite Streamlit Cloud
- Monitoring accessi

## 🐛 Troubleshooting

### Errori Comuni

**Dashboard non si avvia:**
```bash
# Verifica dipendenze
pip install -r dashboard/requirements.txt

# Verifica porta
lsof -i :8501  # Linux/Mac
netstat -ano | findstr :8501  # Windows
```

**Dati non caricati:**
```bash
# Genera dati
python convert_to_powerbi.py

# Oppure usa dati di test
python scripts/generate_test_data.py

# Verifica file
ls data/processed/powerbi/
```

**Errori import:**
```bash
# Dalla root del progetto
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%\src         # Windows
```

**Errori matplotlib (Streamlit Cloud):**
- Assicurati che `matplotlib>=3.7.0` sia in `dashboard/requirements.txt`
- Il dashboard ha fallback automatico per gestire moduli mancanti

**Import error locale:**
- Il dashboard usa import robusti con fallback
- Funziona anche senza accesso ai moduli src/
- Dati di esempio automatici se file non disponibili

## 🚦 Status

| Componente | Status | Note |
|------------|--------|------|
| App Base | ✅ Completato | Streamlit + Plotly |
| Dashboard Popolazione | ✅ Completato | Grafici interattivi |
| Dashboard Economia | 🔄 In sviluppo | Base implementata |
| Dashboard Lavoro | 🔄 In sviluppo | Base implementata |
| Altri Dashboard | ⏳ Pianificato | Template generico |
| Export Dati | ⏳ Pianificato | CSV/Excel download |
| Auth System | ⏳ Pianificato | OAuth integration |

## 🔗 Links

- **Live Demo**: TBD (dopo deploy)
- **GitHub**: https://github.com/AndreaBozzo/Osservatorio
- **Streamlit Docs**: https://docs.streamlit.io/
- **Plotly Docs**: https://plotly.com/python/

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Setup base dashboard
- ✅ Configurazione Streamlit
- ✅ Dashboard popolazione completo
- ✅ Cache system
- ✅ Responsive design basic

### v1.1.0 (Planned)
- Dashboard economia avanzato
- Dashboard lavoro avanzato
- Export functionality
- Performance optimizations

### v1.2.0 (Future)
- Real-time data updates
- Advanced analytics
- User authentication
- Multi-language support
