"""
Configurazione logging centralizzata.
"""
from loguru import logger
from .config import Config

# Rimuovi handler di default
logger.remove()

# Aggiungi console handler
logger.add(
    sink=lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=Config.LOG_LEVEL
)

# Aggiungi file handler
logger.add(
    Config.LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level=Config.LOG_LEVEL
)

def get_logger(name: str):
    """Ottieni logger con contesto specifico."""
    return logger.bind(name=name)