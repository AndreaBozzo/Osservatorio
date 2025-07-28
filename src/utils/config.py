"""
Configurazione centralizzata del progetto.
"""

import os
from pathlib import Path

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
        "ISTAT_API_BASE_URL", "https://esploradati.istat.it/SDMXWS/rest"
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
            cls.DATA_DIR / "reports",
        ]:
            directory.mkdir(parents=True, exist_ok=True)

            # Crea .gitkeep per mantenere struttura in git
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()


# Inizializza directory al caricamento del modulo
Config.ensure_directories()


def get_config():
    """Get configuration as dictionary"""
    return {
        "jwt_secret_key": os.getenv("JWT_SECRET_KEY"),
        "jwt_access_token_expire_minutes": int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        ),
        "jwt_refresh_token_expire_days": int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")
        ),
        "rate_limit_requests_per_minute": int(
            os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")
        ),
        "rate_limit_requests_per_hour": int(
            os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000")
        ),
        "rate_limit_requests_per_day": int(
            os.getenv("RATE_LIMIT_REQUESTS_PER_DAY", "10000")
        ),
        # Enhanced Rate Limiting Configuration
        "enhanced_rate_limiting_enabled": os.getenv(
            "ENHANCED_RATE_LIMITING_ENABLED", "true"
        ).lower()
        == "true",
        "redis_url": os.getenv("REDIS_URL"),  # For distributed rate limiting
        "adaptive_rate_limiting_enabled": os.getenv(
            "ADAPTIVE_RATE_LIMITING_ENABLED", "true"
        ).lower()
        == "true",
        "response_time_threshold_ms": float(
            os.getenv("RESPONSE_TIME_THRESHOLD_MS", "2000")
        ),
        "rate_limit_adjustment_factor": float(
            os.getenv("RATE_LIMIT_ADJUSTMENT_FACTOR", "0.8")
        ),
        "min_adjustment_ratio": float(os.getenv("MIN_ADJUSTMENT_RATIO", "0.1")),
        "max_adjustment_ratio": float(os.getenv("MAX_ADJUSTMENT_RATIO", "2.0")),
        "suspicious_activity_threshold": float(
            os.getenv("SUSPICIOUS_ACTIVITY_THRESHOLD", "0.5")
        ),
        "auto_block_critical_threats": os.getenv(
            "AUTO_BLOCK_CRITICAL_THREATS", "true"
        ).lower()
        == "true",
        "ip_block_duration_hours": int(os.getenv("IP_BLOCK_DURATION_HOURS", "24")),
        "security_monitoring_enabled": os.getenv(
            "SECURITY_MONITORING_ENABLED", "true"
        ).lower()
        == "true",
        "alert_email": os.getenv("SECURITY_ALERT_EMAIL"),
        "cleanup_data_retention_days": int(
            os.getenv("CLEANUP_DATA_RETENTION_DAYS", "30")
        ),
    }
