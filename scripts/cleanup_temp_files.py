#!/usr/bin/env python3
"""
Script per pulizia dei file temporanei del sistema ISTAT.
Può essere eseguito manualmente o schedulato via cron/task scheduler.
"""

import argparse
from pathlib import Path

from utils.logger import get_logger
from utils.temp_file_manager import get_temp_manager

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Pulizia file temporanei sistema ISTAT"
    )
    parser.add_argument(
        "--max-age", type=int, default=24, help="Età massima file in ore (default: 24)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra cosa verrebbe eliminato senza eliminare",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Mostra solo statistiche sui file temporanei",
    )
    parser.add_argument(
        "--cleanup-all",
        action="store_true",
        help="Elimina tutti i file temporanei tracciati",
    )

    args = parser.parse_args()

    temp_manager = get_temp_manager()

    # Mostra statistiche
    if args.stats:
        stats = temp_manager.get_temp_stats()
        print("📊 Statistiche file temporanei:")
        print(f"  Directory base: {stats['base_dir']}")
        print(f"  Directory esistente: {stats['base_dir_exists']}")
        print(f"  File tracciati: {stats['tracked_files']}")
        print(f"  Directory tracciate: {stats['tracked_dirs']}")

        if stats["base_dir_exists"]:
            print(f"  Totale file: {stats.get('total_files', 'N/A')}")
            print(f"  Totale directory: {stats.get('total_dirs', 'N/A')}")
            print(f"  Spazio utilizzato: {stats.get('total_size_mb', 'N/A')} MB")

        return

    # Cleanup completo
    if args.cleanup_all:
        if args.dry_run:
            print("🧽 [DRY RUN] Cleanup completo file temporanei tracciati")
            stats = temp_manager.get_temp_stats()
            print(f"  File da eliminare: {stats['tracked_files']}")
            print(f"  Directory da eliminare: {stats['tracked_dirs']}")
        else:
            print("🧽 Cleanup completo file temporanei...")
            results = temp_manager.cleanup_all()
            print("✅ Cleanup completato:")
            print(f"  File eliminati: {results['files_removed']}")
            print(f"  Directory eliminate: {results['dirs_removed']}")
            print(f"  Errori: {results['errors']}")
        return

    # Cleanup file vecchi
    if args.dry_run:
        print(f"🧽 [DRY RUN] Cleanup file più vecchi di {args.max_age} ore")

        # Simula cosa verrebbe eliminato
        import time

        temp_dir = Path(temp_manager.base_temp_dir)
        if temp_dir.exists():
            cutoff_time = time.time() - (args.max_age * 3600)
            old_files = []

            for item in temp_dir.rglob("*"):
                if item.is_file() and item.stat().st_mtime < cutoff_time:
                    old_files.append(item)

            print(f"  File da eliminare: {len(old_files)}")
            if old_files:
                print("  Alcuni esempi:")
                for file in old_files[:10]:  # Mostra primi 10
                    print(f"    - {file.name}")
                if len(old_files) > 10:
                    print(f"    ... e altri {len(old_files) - 10} file")
        else:
            print("  Directory temporanea non esiste")
    else:
        print(f"🧽 Cleanup file più vecchi di {args.max_age} ore...")
        removed_count = temp_manager.cleanup_old_files(args.max_age)
        print(f"✅ Eliminati {removed_count} file vecchi")


if __name__ == "__main__":
    main()
