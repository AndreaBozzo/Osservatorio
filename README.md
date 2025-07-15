# Osservatorio - ISTAT Data Processing System

Sistema di elaborazione e analisi dati ISTAT con integrazione Tableau.

## 🚀 Quick Start

# Prerequisiti

- Python 3.8+
- PowerShell (per script di download)
- Account Tableau Server (opzionale)

# Installazione

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
Uso Base

📁 Struttura Progetto

src/ - Codice sorgente principale
data/ - Directory dati (raw, processed)
tests/ - Test automatizzati
docs/ - Documentazione dettagliata
scripts/ - Script utility

🧪 Testing
# Esegui tutti i test
pytest

# Test con coverage
pytest --cov=src tests/

📊 Features

✅ Scraping dati ISTAT
✅ Analisi dataflow
✅ Integrazione Tableau Server
✅ Conversione formati dati
✅ Cache intelligente
✅ Logging strutturato

🤝 Contributing

Fork il progetto
Crea un feature branch (git checkout -b feature/AmazingFeature)
Commit delle modifiche (git commit -m 'Add some AmazingFeature')
Push al branch (git push origin feature/AmazingFeature)
Apri una Pull Request

📄 License
Distribuito sotto licenza MIT. Vedi LICENSE per maggiori informazioni.
👥 Contatti
Andrea Bozzo - @AndreaBozzo
Project Link: https://github.com/AndreaBozzo/Osservatorio
