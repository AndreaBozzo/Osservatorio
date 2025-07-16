#!/usr/bin/env python3
"""
Script di conversione ISTAT XML to Tableau
Wrapper per il convertitore tableau_converter.py
"""

import sys
from pathlib import Path

# Aggiungi src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from converters.tableau_converter import IstatXMLtoTableauConverter


def main():
    """Main entry point per conversione Tableau"""
    converter = IstatXMLtoTableauConverter()

    # Directory XML di input
    xml_dir = Path("data/raw/istat/istat_data")

    if not xml_dir.exists():
        print(f"Directory {xml_dir} non trovata!")
        return

    # Processa tutti i file XML
    xml_files = list(xml_dir.glob("*.xml"))

    if not xml_files:
        print(f"Nessun file XML trovato in {xml_dir}")
        return

    print(f"Processando {len(xml_files)} file XML...")

    for xml_file in xml_files:
        try:
            print(f"Processando {xml_file.name}...")
            result = converter.convert_all_datasets()
            if result:
                print(f"✅ {xml_file.name} convertito con successo")
            else:
                print(f"❌ Errore nella conversione di {xml_file.name}")
        except Exception as e:
            print(f"❌ Errore processando {xml_file.name}: {e}")

    print("Conversione completata!")


if __name__ == "__main__":
    main()
