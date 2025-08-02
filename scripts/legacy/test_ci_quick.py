#!/usr/bin/env python3
"""
Script per test rapidi in ambiente CI/CD
Esegue solo i test essenziali per ridurre i tempi di build
"""
import subprocess
import sys


def run_command(cmd, timeout=300):
    """Esegue un comando con timeout"""
    try:
        # Usa python -m pytest per evitare problemi shell
        if cmd.startswith("python -m pytest"):
            cmd = cmd
        else:
            cmd = f"python -m pytest {cmd.replace('python -m pytest ', '')}"

        result = subprocess.run(
            cmd.split(), capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"


def main():
    """Esegue test rapidi per CI"""
    print("🚀 Esecuzione test rapidi per CI/CD...")

    # Test essenziali da eseguire
    essential_tests = [
        "tests/unit/test_config.py",
        "tests/unit/test_logger.py",
        "tests/unit/test_secure_path.py::TestSecurePathValidator::test_init_creates_validator",
        "tests/unit/test_secure_path.py::TestSecurePathValidator::test_validate_filename_valid_names",
        "tests/unit/test_powerbi_converter.py::TestIstatXMLToPowerBIConverter::test_init_creates_converter",
        "tests/unit/test_tableau_converter.py::TestIstatXMLtoTableauConverter::test_init_creates_converter",
    ]

    failed_tests = []

    for test in essential_tests:
        print(f"📋 Esecuzione: {test}")
        success, stdout, stderr = run_command(
            f"python -m pytest {test} -v --tb=short", timeout=60
        )

        if not success:
            failed_tests.append(test)
            print(f"❌ FALLITO: {test}")
            if stderr:
                print(f"   Errore: {stderr}")
        else:
            print(f"✅ PASSATO: {test}")

    if failed_tests:
        print(f"\n❌ Test falliti: {len(failed_tests)}")
        for test in failed_tests:
            print(f"  • {test}")
        sys.exit(1)
    else:
        print("\n✅ Tutti i test essenziali passati!")
        print("Build ready for deployment")


if __name__ == "__main__":
    main()
