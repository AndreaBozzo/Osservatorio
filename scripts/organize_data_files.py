#!/usr/bin/env python3
"""
Script per organizzare i file di dati secondo le best practices.
Sposta i file temporanei nella directory appropriata e mantiene la struttura pulita.
"""

import argparse
import glob
import shutil
import sys
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger
from utils.temp_file_manager import get_temp_manager

# Aggiungi src al path
# Issue #84: Removed unsafe sys.path manipulation


logger = get_logger(__name__)


def organize_xml_files(project_dir: Path, dry_run: bool = False):
    """Organizza i file XML temporanei."""

    # Pattern per i file temporanei
    temp_patterns = [
        "data_DCIS_*.xml",
        "structure_DCIS_*.xml",
        "dataflow_response.xml",
        "sample_*.xml",
    ]

    results = {"moved": 0, "errors": 0, "skipped": 0}
    temp_manager = get_temp_manager()

    for pattern in temp_patterns:
        files = list(project_dir.glob(pattern))

        for file_path in files:
            try:
                # Determina la directory di destinazione
                if file_path.name.startswith("data_DCIS_"):
                    target_subdir = "api_responses"
                elif file_path.name.startswith("structure_DCIS_"):
                    target_subdir = "api_responses"
                elif file_path.name == "dataflow_response.xml":
                    target_subdir = "api_responses"
                elif file_path.name.startswith("sample_"):
                    target_subdir = "samples"
                else:
                    target_subdir = "misc"

                # Ottieni il path di destinazione tramite temp_manager
                target_path = temp_manager.get_temp_file_path(
                    file_path.name, target_subdir, cleanup_on_exit=True
                )

                if dry_run:
                    print(f"[DRY RUN] Sposterei: {file_path} -> {target_path}")
                    results["moved"] += 1
                else:
                    # Crea directory se non esiste
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Sposta il file
                    shutil.move(str(file_path), str(target_path))
                    logger.info(f"Spostato: {file_path.name} -> {target_path}")
                    results["moved"] += 1

            except Exception as e:
                logger.error(f"Errore spostamento {file_path}: {e}")
                results["errors"] += 1

    return results


def organize_log_files(project_dir: Path, dry_run: bool = False):
    """Organizza i file di log."""

    logs_dir = project_dir / "logs"

    # Pattern per i file di log
    log_patterns = [
        "*.log",
        "*.log.*",
        "istat_api_test_report_*.html",
        "istat_api_test_report_*.json",
    ]

    results = {"moved": 0, "errors": 0, "skipped": 0}

    for pattern in log_patterns:
        files = list(project_dir.glob(pattern))

        for file_path in files:
            try:
                target_path = logs_dir / file_path.name

                if dry_run:
                    print(f"[DRY RUN] Sposterei: {file_path} -> {target_path}")
                    results["moved"] += 1
                else:
                    # Crea directory se non esiste
                    logs_dir.mkdir(exist_ok=True)

                    # Sposta il file
                    shutil.move(str(file_path), str(target_path))
                    logger.info(f"Spostato: {file_path.name} -> logs/")
                    results["moved"] += 1

            except Exception as e:
                logger.error(f"Errore spostamento {file_path}: {e}")
                results["errors"] += 1

    return results


def organize_report_files(project_dir: Path, dry_run: bool = False):
    """Organizza i file di report."""

    reports_dir = project_dir / "data" / "reports"

    # Pattern per i file di report
    report_patterns = [
        "conversion_summary_*.json",
        "tableau_import_instructions_*.md",
        "powerbi_integration_guide_*.md",
        "tableau_istat_datasets_*.json",
    ]

    results = {"moved": 0, "errors": 0, "skipped": 0}

    for pattern in report_patterns:
        files = list(project_dir.glob(pattern))

        for file_path in files:
            try:
                target_path = reports_dir / file_path.name

                if dry_run:
                    print(f"[DRY RUN] Sposterei: {file_path} -> {target_path}")
                    results["moved"] += 1
                else:
                    # Crea directory se non esiste
                    reports_dir.mkdir(parents=True, exist_ok=True)

                    # Sposta il file
                    shutil.move(str(file_path), str(target_path))
                    logger.info(f"Spostato: {file_path.name} -> data/reports/")
                    results["moved"] += 1

            except Exception as e:
                logger.error(f"Errore spostamento {file_path}: {e}")
                results["errors"] += 1

    return results


def cleanup_empty_directories(project_dir: Path, dry_run: bool = False):
    """Rimuove directory vuote."""

    results = {"removed": 0, "errors": 0}

    # Directory da controllare
    check_dirs = [
        project_dir / "data" / "raw",
        project_dir / "data" / "processed",
        project_dir / "data" / "cache",
    ]

    for check_dir in check_dirs:
        if not check_dir.exists():
            continue

        try:
            # Trova directory vuote
            for subdir in check_dir.rglob("*"):
                if subdir.is_dir() and not any(subdir.iterdir()):
                    if dry_run:
                        print(f"[DRY RUN] Rimuoverei directory vuota: {subdir}")
                        results["removed"] += 1
                    else:
                        subdir.rmdir()
                        logger.info(f"Rimossa directory vuota: {subdir}")
                        results["removed"] += 1

        except Exception as e:
            logger.error(f"Errore rimozione directory vuote in {check_dir}: {e}")
            results["errors"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Organizza file di dati secondo best practices"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra cosa verrebbe fatto senza eseguire",
    )
    parser.add_argument(
        "--xml-only", action="store_true", help="Organizza solo file XML"
    )
    parser.add_argument(
        "--logs-only", action="store_true", help="Organizza solo file di log"
    )
    parser.add_argument(
        "--reports-only", action="store_true", help="Organizza solo file di report"
    )
    parser.add_argument(
        "--cleanup-empty", action="store_true", help="Rimuovi directory vuote"
    )

    args = parser.parse_args()

    project_dir = Path(__file__).parent.parent

    if args.dry_run:
        print("🧹 [DRY RUN] Organizzazione file dati\n")
    else:
        print("🧹 Organizzazione file dati\n")

    total_results = {"moved": 0, "errors": 0, "skipped": 0, "removed": 0}

    # Organizza XML
    if not args.logs_only and not args.reports_only:
        print("📄 Organizzazione file XML...")
        xml_results = organize_xml_files(project_dir, args.dry_run)
        total_results["moved"] += xml_results["moved"]
        total_results["errors"] += xml_results["errors"]
        total_results["skipped"] += xml_results["skipped"]
        print(
            f"  File XML processati: {xml_results['moved']}, errori: {xml_results['errors']}"
        )

    # Organizza log
    if not args.xml_only and not args.reports_only:
        print("📋 Organizzazione file log...")
        log_results = organize_log_files(project_dir, args.dry_run)
        total_results["moved"] += log_results["moved"]
        total_results["errors"] += log_results["errors"]
        total_results["skipped"] += log_results["skipped"]
        print(
            f"  File log processati: {log_results['moved']}, errori: {log_results['errors']}"
        )

    # Organizza report
    if not args.xml_only and not args.logs_only:
        print("📊 Organizzazione file report...")
        report_results = organize_report_files(project_dir, args.dry_run)
        total_results["moved"] += report_results["moved"]
        total_results["errors"] += report_results["errors"]
        total_results["skipped"] += report_results["skipped"]
        print(
            f"  File report processati: {report_results['moved']}, errori: {report_results['errors']}"
        )

    # Cleanup directory vuote
    if args.cleanup_empty:
        print("🗑️  Rimozione directory vuote...")
        cleanup_results = cleanup_empty_directories(project_dir, args.dry_run)
        total_results["removed"] += cleanup_results["removed"]
        total_results["errors"] += cleanup_results["errors"]
        print(
            f"  Directory rimosse: {cleanup_results['removed']}, errori: {cleanup_results['errors']}"
        )

    # Riepilogo
    print(f"\n✅ Organizzazione completata:")
    print(f"  File spostati: {total_results['moved']}")
    print(f"  Directory rimosse: {total_results['removed']}")
    print(f"  Errori: {total_results['errors']}")

    if args.dry_run:
        print("\n💡 Esegui senza --dry-run per applicare le modifiche")


if __name__ == "__main__":
    main()
