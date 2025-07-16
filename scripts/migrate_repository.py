#!/usr/bin/env python3
"""
Script per migrare i file nella nuova struttura.
"""
import shutil
from pathlib import Path
import click
from typing import Dict, List

# Mappatura vecchio → nuovo path
FILE_MAPPING = {
    "Tableau_Scraping_Strategy_for_ISTAT_Data.py": "src/scrapers/tableau_scraper.py",
    "Tableau_Server_API_Analysis_Script.py": "src/api/tableau_api.py",
    "istat_api_tester.py": "src/api/istat_api.py",
    "istat_dataflow_analyzer.py": "src/analyzers/dataflow_analyzer.py",
    "download_istat_data_fixed.ps1": "scripts/download_istat_data.ps1",
}

DIRECTORY_MAPPING = {
    "istat_data": "data/raw/istat",
    "tableau_output": "data/processed/tableau",
}


@click.command()
@click.option("--dry-run", is_flag=True, help="Mostra cosa verrà fatto senza eseguire")
def migrate(dry_run: bool):
    """Migra i file nella nuova struttura."""
    base_path = Path(".")

    # Crea directory
    directories = [
        "src/scrapers",
        "src/analyzers",
        "src/api",
        "src/utils",
        "src/converters",
        "data/raw/istat",
        "data/raw/xml",
        "data/processed/tableau",
        "data/cache",
        "data/reports",
        "tests/unit",
        "tests/integration",
        "docs",
        "scripts",
        "notebooks",
        ".github/workflows",
    ]

    click.echo("📁 Creazione directory...")
    for dir_path in directories:
        full_path = base_path / dir_path
        if dry_run:
            click.echo(f"  Creerebbe: {full_path}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            # Aggiungi __init__.py per moduli Python
            if dir_path.startswith("src/") or dir_path.startswith("tests/"):
                init_file = full_path / "__init__.py"
                init_file.touch()

    # Sposta file
    click.echo("\n📄 Spostamento file...")
    for old_path, new_path in FILE_MAPPING.items():
        old_full = base_path / old_path
        new_full = base_path / new_path

        if old_full.exists():
            if dry_run:
                click.echo(f"  {old_path} → {new_path}")
            else:
                new_full.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_full), str(new_full))
                click.echo(f"  ✓ {old_path} → {new_path}")

    # Sposta directory
    click.echo("\n📁 Spostamento directory...")
    for old_dir, new_dir in DIRECTORY_MAPPING.items():
        old_full = base_path / old_dir
        new_full = base_path / new_dir

        if old_full.exists() and old_full.is_dir():
            if dry_run:
                click.echo(f"  {old_dir}/ → {new_dir}/")
            else:
                new_full.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_full), str(new_full))
                click.echo(f"  ✓ {old_dir}/ → {new_dir}/")

    # Sposta file XML in data/raw/xml/
    click.echo("\n📄 Spostamento file XML...")
    for xml_file in base_path.glob("*.xml"):
        new_path = base_path / "data" / "raw" / "xml" / xml_file.name
        if dry_run:
            click.echo(f"  {xml_file.name} → data/raw/xml/")
        else:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(xml_file), str(new_path))
            click.echo(f"  ✓ {xml_file.name} → data/raw/xml/")

    # Sposta report JSON/HTML
    click.echo("\n📊 Spostamento report...")
    patterns = ["*report*.json", "*report*.html", "*summary*.json"]
    for pattern in patterns:
        for report_file in base_path.glob(pattern):
            new_path = base_path / "data" / "reports" / report_file.name
            if dry_run:
                click.echo(f"  {report_file.name} → data/reports/")
            else:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(report_file), str(new_path))
                click.echo(f"  ✓ {report_file.name} → data/reports/")

    if dry_run:
        click.echo("\n⚠️  Modalità dry-run: nessuna modifica effettuata")
        click.echo("Esegui senza --dry-run per applicare le modifiche")
    else:
        click.echo("\n✅ Migrazione completata!")
        click.echo("📝 Ricorda di:")
        click.echo("  1. Creare README.md, requirements.txt, .gitignore")
        click.echo("  2. Configurare .env con le tue credenziali")
        click.echo("  3. Aggiornare gli import nei file Python")
        click.echo("  4. Eseguire git add per i nuovi file")


if __name__ == "__main__":
    migrate()
