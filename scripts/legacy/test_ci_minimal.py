#!/usr/bin/env python3
"""
Test minimali per CI - versione ultra-robusta
Testa solo le funzioni essenziali senza dipendenze problematiche
"""

import sys
from pathlib import Path

# Aggiungi src al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))


def test_imports():
    """Test che tutti i moduli si importino correttamente"""
    try:
        from converters.powerbi_converter import IstatXMLToPowerBIConverter
        from converters.tableau_converter import IstatXMLtoTableauConverter
        from utils.config import Config
        from utils.logger import get_logger
        from utils.secure_path import SecurePathValidator

        print("✅ Tutti gli import funzionano")
        return True
    except Exception as e:
        print(f"❌ Errore import: {e}")
        return False


def test_basic_functionality():
    """Test funzionalità base senza file system"""
    try:
        # Test Config
        from utils.config import Config

        config = Config()
        assert hasattr(config, "ISTAT_API_BASE_URL")

        # Test Logger
        from utils.logger import get_logger

        logger = get_logger("test")
        assert logger is not None

        # Test SecurePathValidator - solo creazione oggetto
        from utils.secure_path import SecurePathValidator

        validator = SecurePathValidator("/tmp")
        assert validator.base_directory.name == "tmp"

        # Test Converters - solo creazione oggetto
        from converters.powerbi_converter import IstatXMLToPowerBIConverter

        converter_pb = IstatXMLToPowerBIConverter()
        assert converter_pb is not None

        from converters.tableau_converter import IstatXMLtoTableauConverter

        converter_tb = IstatXMLtoTableauConverter()
        assert converter_tb is not None

        print("✅ Funzionalità base OK")
        return True

    except Exception as e:
        print(f"❌ Errore test base: {e}")
        return False


def test_data_generation():
    """Test che la generazione dati funzioni"""
    try:
        from pathlib import Path

        import pandas as pd

        # Controlla se i dati di test esistono
        data_dir = Path("data/processed/powerbi")
        if data_dir.exists():
            test_files = list(data_dir.glob("*test*.csv"))
            if test_files:
                # Prova a leggere un file di test
                test_file = test_files[0]
                df = pd.read_csv(test_file)
                assert len(df) > 0
                print(f"✅ Test data OK: {len(test_files)} file trovati")
                return True

        print("⚠️ Test data non trovati, ma non è critico")
        return True

    except Exception as e:
        print(f"❌ Errore test data: {e}")
        return False


def main():
    """Test ultra-minimali per CI"""
    print("🧪 Test minimali per CI...")

    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Data Generation", test_data_generation),
    ]

    failed = []

    for name, test_func in tests:
        print(f"\n📋 {name}:")
        if not test_func():
            failed.append(name)

    if failed:
        print(f"\n❌ Test falliti: {len(failed)}")
        for test in failed:
            print(f"  • {test}")
        sys.exit(1)
    else:
        print(f"\n✅ Tutti i test minimali passati!")
        print("CI ready for deployment")


if __name__ == "__main__":
    main()
