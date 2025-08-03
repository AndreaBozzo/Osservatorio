"""
Gestione centralizzata dei file temporanei per il sistema ISTAT.
Implementa best practices per la gestione dei file temporanei.
"""

import atexit
import os
import shutil
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger(__name__)

# Silent mode for tests - reduce logging verbosity
SILENT_MODE = os.getenv("TEMP_FILE_MANAGER_SILENT", "false").lower() == "true"


class TempFileManager:
    """Gestione centralizzata dei file temporanei con cleanup automatico."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._temp_dirs: set[Path] = set()
        self._temp_files: set[Path] = set()
        self._cleanup_registered = False

        # Directory base per file temporanei
        self.base_temp_dir = Path(tempfile.gettempdir()) / "osservatorio_istat"
        self.base_temp_dir.mkdir(exist_ok=True)

        # Registra cleanup all'uscita
        if not self._cleanup_registered:
            atexit.register(self.cleanup_all)
            self._cleanup_registered = True

        if not SILENT_MODE:
            logger.debug(
                f"TempFileManager inizializzato. Base dir: {self.base_temp_dir}"
            )

    def create_temp_dir(
        self, prefix: str = "temp_", cleanup_on_exit: bool = True
    ) -> Path:
        """Crea una directory temporanea con nome univoco."""
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=self.base_temp_dir))

            if cleanup_on_exit:
                self._temp_dirs.add(temp_dir)

            logger.debug(f"Creata directory temporanea: {temp_dir}")
            return temp_dir

        except Exception as e:
            logger.error(f"Errore creazione directory temporanea: {e}")
            raise

    def create_temp_file(
        self, suffix: str = ".tmp", prefix: str = "temp_", cleanup_on_exit: bool = True
    ) -> Path:
        """Crea un file temporaneo con nome univoco."""
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix, prefix=prefix, dir=self.base_temp_dir
            )
            os.close(fd)  # Chiudi il file descriptor

            temp_file = Path(temp_path)

            if cleanup_on_exit:
                self._temp_files.add(temp_file)

            logger.debug(f"Creato file temporaneo: {temp_file}")
            return temp_file

        except Exception as e:
            logger.error(f"Errore creazione file temporaneo: {e}")
            raise

    def get_temp_file_path(
        self, filename: str, subdir: Optional[str] = None, cleanup_on_exit: bool = True
    ) -> Path:
        """Ottiene il path per un file temporaneo con nome specifico."""
        if subdir:
            target_dir = self.base_temp_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.base_temp_dir

        temp_file = target_dir / filename

        if cleanup_on_exit:
            self._temp_files.add(temp_file)

        return temp_file

    @contextmanager
    def temp_directory(self, prefix: str = "temp_"):
        """Context manager per directory temporanea con cleanup automatico."""
        temp_dir = self.create_temp_dir(prefix=prefix, cleanup_on_exit=False)
        try:
            yield temp_dir
        finally:
            self.cleanup_directory(temp_dir)

    @contextmanager
    def temp_file(self, suffix: str = ".tmp", prefix: str = "temp_"):
        """Context manager per file temporaneo con cleanup automatico."""
        temp_file = self.create_temp_file(
            suffix=suffix, prefix=prefix, cleanup_on_exit=False
        )
        try:
            yield temp_file
        finally:
            self.cleanup_file(temp_file)

    def cleanup_file(self, file_path: Path) -> bool:
        """Rimuove un file temporaneo specifico."""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Rimosso file temporaneo: {file_path}")

            # Rimuovi dal tracking
            self._temp_files.discard(file_path)
            return True

        except Exception as e:
            logger.warning(f"Errore rimozione file {file_path}: {e}")
            return False

    def cleanup_directory(self, dir_path: Path) -> bool:
        """Rimuove una directory temporanea e tutto il suo contenuto."""
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.debug(f"Rimossa directory temporanea: {dir_path}")

            # Rimuovi dal tracking
            self._temp_dirs.discard(dir_path)
            return True

        except Exception as e:
            logger.warning(f"Errore rimozione directory {dir_path}: {e}")
            return False

    def cleanup_all(self) -> dict[str, int]:
        """Rimuove tutti i file e directory temporanei tracciati."""
        results = {"files_removed": 0, "dirs_removed": 0, "errors": 0}

        if not SILENT_MODE:
            logger.debug("Pulizia file temporanei in corso...")

        # Cleanup file
        for temp_file in list(self._temp_files):
            if self.cleanup_file(temp_file):
                results["files_removed"] += 1
            else:
                results["errors"] += 1

        # Cleanup directory
        for temp_dir in list(self._temp_dirs):
            if self.cleanup_directory(temp_dir):
                results["dirs_removed"] += 1
            else:
                results["errors"] += 1

        if not SILENT_MODE:
            logger.debug(f"Pulizia completata: {results}")
        return results

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Rimuove file temporanei più vecchi di max_age_hours."""
        removed_count = 0
        cutoff_time = time.time() - (max_age_hours * 3600)

        if not self.base_temp_dir.exists():
            return 0

        try:
            for item in self.base_temp_dir.rglob("*"):
                if item.is_file() and item.stat().st_mtime < cutoff_time:
                    try:
                        item.unlink()
                        removed_count += 1
                        logger.debug(f"Rimosso file vecchio: {item}")
                    except Exception as e:
                        logger.warning(f"Errore rimozione file vecchio {item}: {e}")

        except Exception as e:
            logger.error(f"Errore durante cleanup file vecchi: {e}")

        if removed_count > 0:
            logger.debug(f"Rimossi {removed_count} file temporanei vecchi")

        return removed_count

    def get_temp_stats(self) -> dict:
        """Ottiene statistiche sui file temporanei."""
        stats = {
            "tracked_files": len(self._temp_files),
            "tracked_dirs": len(self._temp_dirs),
            "base_dir": str(self.base_temp_dir),
            "base_dir_exists": self.base_temp_dir.exists(),
        }

        if self.base_temp_dir.exists():
            try:
                all_files = list(self.base_temp_dir.rglob("*"))
                stats["total_files"] = len([f for f in all_files if f.is_file()])
                stats["total_dirs"] = len([f for f in all_files if f.is_dir()])

                # Calcola spazio utilizzato
                total_size = sum(f.stat().st_size for f in all_files if f.is_file())
                stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)

            except Exception as e:
                logger.warning(f"Errore calcolo statistiche: {e}")
                stats["error"] = str(e)

        return stats


# Istanza globale singleton
temp_manager = TempFileManager()


def get_temp_manager() -> TempFileManager:
    """Ottiene l'istanza singleton del TempFileManager."""
    return temp_manager
