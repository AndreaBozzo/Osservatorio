"""
Configurazione centralizzata del progetto.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

class Config:
    """Configurazione dell'applicazione."""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    CACHE_DIR = DATA_DIR / "cache"
    LOGS_DIR = BASE_DIR / "logs"
    
    # ISTAT API
    ISTAT_API_BASE_URL = os.getenv(
        "ISTAT_API_BASE_URL", 
        "https://esploradati.istat.it/SDMXWS/rest"
    )
    ISTAT_API_TIMEOUT = int(os.getenv("ISTAT_API_TIMEOUT", "30"))
    
    # Tableau
    TABLEAU_SERVER_URL = os.getenv("TABLEAU_SERVER_URL")
    TABLEAU_USERNAME = os.getenv("TABLEAU_USERNAME")
    TABLEAU_PASSWORD = os.getenv("TABLEAU_PASSWORD")
    TABLEAU_SITE_ID = os.getenv("TABLEAU_SITE_ID", "")
    
    # PowerBI
    POWERBI_CLIENT_ID = os.getenv("POWERBI_CLIENT_ID")
    POWERBI_CLIENT_SECRET = os.getenv("POWERBI_CLIENT_SECRET")
    POWERBI_TENANT_ID = os.getenv("POWERBI_TENANT_ID")
    POWERBI_WORKSPACE_ID = os.getenv("POWERBI_WORKSPACE_ID")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "osservatorio.log"))
    
    # Cache
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))
    
    @classmethod
    def ensure_directories(cls):
        """Crea le directory necessarie se non esistono."""
        for directory in [
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.CACHE_DIR,
            cls.LOGS_DIR,
            cls.RAW_DATA_DIR / "istat",
            cls.RAW_DATA_DIR / "xml",
            cls.PROCESSED_DATA_DIR / "tableau",
            cls.PROCESSED_DATA_DIR / "powerbi",
            cls.DATA_DIR / "reports"
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Crea .gitkeep per mantenere struttura in git
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

# Inizializza directory al caricamento del modulo
Config.ensure_directories()