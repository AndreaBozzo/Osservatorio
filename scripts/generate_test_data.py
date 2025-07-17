#!/usr/bin/env python3
"""
Script per generare dati di test per CI/CD
Evita chiamate API ISTAT live durante i test automatici
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.logger import get_logger
from utils.secure_path import create_secure_validator

logger = get_logger(__name__)


def create_mock_data():
    """Crea dati di test per le categorie principali"""

    # Dati mock per popolazione
    population_data = {
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [60244639, 59030133, 58997201, 58850717, 58761146],
        "UNIT_MEASURE": ["N", "N", "N", "N", "N"],
        "SEXISTAT1": ["T", "T", "T", "T", "T"],
    }

    # Dati mock per economia
    economy_data = {
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [1653000, 1775000, 1897000, 1952000, 2010000],
        "UNIT_MEASURE": ["EUR_MIO", "EUR_MIO", "EUR_MIO", "EUR_MIO", "EUR_MIO"],
        "SECTOR": ["TOTAL", "TOTAL", "TOTAL", "TOTAL", "TOTAL"],
    }

    # Dati mock per lavoro
    work_data = {
        "TIME_PERIOD": ["2020", "2021", "2022", "2023", "2024"],
        "TERRITORIO": ["Italia", "Italia", "Italia", "Italia", "Italia"],
        "Value": [58.1, 58.2, 58.8, 59.5, 60.1],
        "UNIT_MEASURE": ["PC", "PC", "PC", "PC", "PC"],
        "AGECLASS": ["15-64", "15-64", "15-64", "15-64", "15-64"],
    }

    return {
        "popolazione": population_data,
        "economia": economy_data,
        "lavoro": work_data,
    }


def generate_test_files():
    """Genera file di test per CI/CD"""
    try:
        # Setup percorsi sicuri
        validator = create_secure_validator(Path(__file__).parent.parent)

        # Directory di output
        output_dir = Path("data/processed/powerbi")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Genera timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Crea dati mock
        mock_data = create_mock_data()

        files_created = []

        for category, data in mock_data.items():
            df = pd.DataFrame(data)

            # Genera tutti i formati
            formats = {
                "csv": "csv",
                "json": "json",
                "xlsx": "xlsx",
                "parquet": "parquet",
            }

            for format_name, extension in formats.items():
                filename = f"{category}_test_{timestamp}.{extension}"
                filepath = output_dir / filename

                # Salva in formato appropriato
                if extension == "csv":
                    df.to_csv(filepath, index=False)
                elif extension == "json":
                    df.to_json(filepath, orient="records", indent=2)
                elif extension == "xlsx":
                    df.to_excel(filepath, index=False, engine="openpyxl")
                elif extension == "parquet":
                    df.to_parquet(filepath, index=False)

                files_created.append(str(filepath))
                logger.info(f"Creato file test: {filepath}")

        # Genera summary di conversione
        summary = {
            "timestamp": timestamp,
            "environment": "CI/CD",
            "files_created": files_created,
            "categories": list(mock_data.keys()),
            "total_files": len(files_created),
            "data_quality": {"completeness_score": 1.0, "data_quality_score": 1.0},
            "notes": "Generated mock data for CI/CD testing",
        }

        summary_file = output_dir / f"conversion_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Generati {len(files_created)} file di test per CI/CD")
        return True

    except Exception as e:
        logger.error(f"Errore generazione dati test: {e}")
        return False


def main():
    """Main entry point"""
    print("🧪 Generazione dati di test per CI/CD...")

    if generate_test_files():
        print("✅ Dati di test generati con successo!")
        print("File disponibili in: data/processed/powerbi/")
    else:
        print("❌ Errore nella generazione dei dati di test")
        sys.exit(1)


if __name__ == "__main__":
    main()
