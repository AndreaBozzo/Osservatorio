#!/usr/bin/env python3
"""
Script per schedulare la pulizia automatica dei file temporanei.
Supporta sia cron (Linux/Mac) che Task Scheduler (Windows).
"""

import argparse
import os
import sys
from pathlib import Path

from utils.logger import get_logger

# Aggiungi src al path
# Issue #84: Removed unsafe sys.path manipulation


logger = get_logger(__name__)


def create_cron_job(frequency: str, max_age: int, project_dir: Path):
    """Crea un job cron per la pulizia automatica."""

    # Mappa delle frequenze
    freq_map = {
        "daily": "0 2 * * *",  # Ogni giorno alle 2:00
        "weekly": "0 2 * * 0",  # Ogni domenica alle 2:00
        "hourly": "0 * * * *",  # Ogni ora
    }

    if frequency not in freq_map:
        raise ValueError(f"Frequenza non supportata: {frequency}")

    cron_time = freq_map[frequency]
    cleanup_script = project_dir / "scripts" / "cleanup_temp_files.py"
    python_path = sys.executable

    # Comando cron
    cron_command = f"{cron_time} {python_path} {cleanup_script} --max-age {max_age}"

    # Istruzioni per l'utente
    instructions = f"""
📅 Istruzioni per configurare cron job:

1. Apri crontab:
   crontab -e

2. Aggiungi questa riga:
   {cron_command}

3. Salva e chiudi l'editor

4. Verifica che il job sia attivo:
   crontab -l

Il job pulirà automaticamente i file temporanei {frequency} rimuovendo file più vecchi di {max_age} ore.
"""

    return instructions


def create_windows_task(frequency: str, max_age: int, project_dir: Path):
    """Crea un task Windows per la pulizia automatica."""

    # Mappa delle frequenze
    freq_map = {"daily": "DAILY", "weekly": "WEEKLY", "hourly": "HOURLY"}

    if frequency not in freq_map:
        raise ValueError(f"Frequenza non supportata: {frequency}")

    schtasks_freq = freq_map[frequency]
    cleanup_script = project_dir / "scripts" / "cleanup_temp_files.py"
    python_path = sys.executable

    # Comando per creare il task
    task_command = f"""schtasks /create /tn "OsservatorioCleanup" /tr "{python_path} {cleanup_script} --max-age {max_age}" /sc {schtasks_freq} /st 02:00"""

    # Istruzioni per l'utente
    instructions = f"""
📅 Istruzioni per configurare Windows Task:

1. Apri Command Prompt come Amministratore

2. Esegui questo comando:
   {task_command}

3. Verifica che il task sia creato:
   schtasks /query /tn "OsservatorioCleanup"

4. Per eliminare il task (se necessario):
   schtasks /delete /tn "OsservatorioCleanup" /f

Il task pulirà automaticamente i file temporanei {frequency} rimuovendo file più vecchi di {max_age} ore.
"""

    return instructions


def main():
    parser = argparse.ArgumentParser(
        description="Configura pulizia automatica file temporanei"
    )
    parser.add_argument(
        "--frequency",
        choices=["daily", "weekly", "hourly"],
        default="daily",
        help="Frequenza di pulizia (default: daily)",
    )
    parser.add_argument(
        "--max-age", type=int, default=24, help="Età massima file in ore (default: 24)"
    )
    parser.add_argument(
        "--platform",
        choices=["auto", "linux", "windows", "mac"],
        default="auto",
        help="Piattaforma target (default: auto)",
    )

    args = parser.parse_args()

    # Determina la piattaforma
    if args.platform == "auto":
        if os.name == "nt":
            platform = "windows"
        else:
            platform = "linux"  # Include Mac
    else:
        platform = args.platform

    project_dir = Path(__file__).parent.parent

    try:
        if platform == "windows":
            instructions = create_windows_task(
                args.frequency, args.max_age, project_dir
            )
        else:
            instructions = create_cron_job(args.frequency, args.max_age, project_dir)

        print(instructions)

    except Exception as e:
        logger.error(f"Errore configurazione scheduling: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
