"""
Validazione Step 1.2: Verifica setup PowerBI completo
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config


def validate_step1_2():
    """Valida che lo Step 1.2 sia pronto per l'esecuzione."""
    print("🔍 VALIDAZIONE STEP 1.2 - POWERBI SETUP")
    print("=" * 50)

    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "step": "1.2",
        "checks": [],
        "overall_status": "PENDING",
        "ready_for_execution": False,
    }

    def add_check(name: str, status: str, message: str, details: str = None):
        """Aggiungi risultato check."""
        validation_results["checks"].append(
            {"name": name, "status": status, "message": message, "details": details}
        )

        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {name}: {message}")
        if details:
            print(f"   └─ {details}")

    # Check 1: Verifica file Step 1.1
    print("\n📋 PREREQUISITI STEP 1.1:")

    powerbi_dir = Config.PROCESSED_DATA_DIR / "powerbi"
    if powerbi_dir.exists():
        add_check("Directory PowerBI", "PASS", "Directory PowerBI esistente")

        # Verifica file convertiti
        conversion_files = list(powerbi_dir.glob("conversion_summary_*.json"))
        if conversion_files:
            add_check(
                "File Conversione",
                "PASS",
                f"Trovati {len(conversion_files)} file di conversione",
            )
        else:
            add_check("File Conversione", "FAIL", "Nessun file di conversione trovato")
    else:
        add_check("Directory PowerBI", "FAIL", "Directory PowerBI non esistente")

    # Check 2: Verifica script setup
    print("\n🔧 SCRIPT SETUP:")

    setup_script = Path("scripts/setup_powerbi_azure.py")
    if setup_script.exists():
        add_check("Script Setup", "PASS", "Script setup PowerBI disponibile")
    else:
        add_check("Script Setup", "FAIL", "Script setup PowerBI mancante")

    upload_script = Path("scripts/test_powerbi_upload.py")
    if upload_script.exists():
        add_check("Script Upload", "PASS", "Script test upload disponibile")
    else:
        add_check("Script Upload", "FAIL", "Script test upload mancante")

    # Check 3: Verifica dipendenze
    print("\n📦 DIPENDENZE:")

    try:
        import msal

        add_check("MSAL Library", "PASS", "MSAL installato per autenticazione Azure")
    except ImportError:
        add_check(
            "MSAL Library", "FAIL", "MSAL non installato - eseguire: pip install msal"
        )

    try:
        import pyarrow

        add_check("PyArrow Library", "PASS", "PyArrow installato per formato Parquet")
    except ImportError:
        add_check(
            "PyArrow Library",
            "FAIL",
            "PyArrow non installato - eseguire: pip install pyarrow",
        )

    # Check 4: Verifica configurazione environment
    print("\n🔐 CONFIGURAZIONE ENVIRONMENT:")

    env_file = Path(".env")
    if env_file.exists():
        add_check("File .env", "PASS", "File .env esistente")
    else:
        add_check(
            "File .env", "WARN", "File .env non esistente - verrà creato durante setup"
        )

    # Verifica variabili PowerBI
    powerbi_vars = [
        "POWERBI_TENANT_ID",
        "POWERBI_CLIENT_ID",
        "POWERBI_CLIENT_SECRET",
        "POWERBI_WORKSPACE_ID",
    ]

    configured_vars = 0
    for var in powerbi_vars:
        value = os.getenv(var)
        if value:
            configured_vars += 1
            add_check(f"Variabile {var}", "PASS", "Configurata")
        else:
            add_check(
                f"Variabile {var}",
                "WARN",
                "Non configurata - da configurare durante setup",
            )

    # Check 5: Verifica API client
    print("\n🔌 API CLIENT:")

    try:
        from src.api.powerbi_api import PowerBIAPIClient

        add_check("PowerBI API Client", "PASS", "Client PowerBI importabile")
    except ImportError as e:
        add_check("PowerBI API Client", "FAIL", f"Errore import: {e}")

    # Check 6: Verifica documentazione
    print("\n📚 DOCUMENTAZIONE:")

    guide_files = list(powerbi_dir.glob("powerbi_integration_guide_*.md"))
    if guide_files:
        add_check("Guida PowerBI", "PASS", "Guida integrazione PowerBI disponibile")
    else:
        add_check("Guida PowerBI", "WARN", "Guida integrazione non trovata")

    # Calcola status complessivo
    failed_checks = len(
        [c for c in validation_results["checks"] if c["status"] == "FAIL"]
    )
    warning_checks = len(
        [c for c in validation_results["checks"] if c["status"] == "WARN"]
    )

    if failed_checks == 0:
        if warning_checks == 0:
            validation_results["overall_status"] = "READY"
            validation_results["ready_for_execution"] = True
        else:
            validation_results["overall_status"] = "READY_WITH_WARNINGS"
            validation_results["ready_for_execution"] = True
    else:
        validation_results["overall_status"] = "NOT_READY"
        validation_results["ready_for_execution"] = False

    # Mostra risultato finale
    print("\n" + "=" * 50)
    print("📊 RISULTATO VALIDAZIONE:")
    print(f"Status: {validation_results['overall_status']}")
    print(f"Controlli falliti: {failed_checks}")
    print(f"Controlli con avvisi: {warning_checks}")
    print(
        f"Pronto per esecuzione: {'✅ SÌ' if validation_results['ready_for_execution'] else '❌ NO'}"
    )

    # Prossimi passi
    print("\n🚀 PROSSIMI PASSI:")
    if validation_results["ready_for_execution"]:
        print("1. Eseguire: python scripts/setup_powerbi_azure.py")
        print("2. Seguire la guida per configurare Azure AD")
        print("3. Testare: python scripts/test_powerbi_upload.py")
        print("4. Verificare upload dataset in PowerBI Service")
    else:
        print("1. Risolvere i controlli falliti mostrati sopra")
        print("2. Rilanciare questa validazione")
        print("3. Procedere con i prossimi passi quando tutto è verde")

    # Salva report
    report_file = f"step1_2_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Report salvato: {report_file}")

    return validation_results


def main():
    """Funzione principale."""
    try:
        results = validate_step1_2()
        sys.exit(0 if results["ready_for_execution"] else 1)
    except Exception as e:
        print(f"❌ Errore durante validazione: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
