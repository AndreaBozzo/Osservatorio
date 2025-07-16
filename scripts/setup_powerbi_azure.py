"""
Script di setup per configurazione Azure AD e PowerBI.
Guida l'utente attraverso la configurazione completa.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Aggiungi il path del progetto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.powerbi_api import PowerBIAPIClient
from src.utils.config import Config


class PowerBISetupWizard:
    """Wizard per setup completo PowerBI."""

    def __init__(self):
        """Inizializza il wizard di setup."""
        self.config = {}
        self.env_file = Path(".env")
        self.setup_log = []

    def log_step(self, message: str, status: str = "INFO"):
        """Log di un passaggio del setup."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {status}: {message}"
        self.setup_log.append(log_entry)
        print(log_entry)

    def run_setup(self):
        """Esegue il setup completo guidato."""
        print("🚀 POWERBI SETUP WIZARD")
        print("=" * 50)
        print(
            "Questa guida ti aiuterà a configurare l'integrazione PowerBI con Azure AD"
        )
        print()

        # Step 1: Verifica prerequisiti
        self.check_prerequisites()

        # Step 2: Guida Azure AD
        self.guide_azure_ad_setup()

        # Step 3: Configurazione credenziali
        self.configure_credentials()

        # Step 4: Test connessione
        self.test_connection()

        # Step 5: Salva configurazione
        self.save_configuration()

        # Step 6: Riepilogo
        self.show_summary()

    def check_prerequisites(self):
        """Verifica i prerequisiti per il setup."""
        self.log_step("Verifica prerequisiti...")

        # Verifica account PowerBI
        print("📋 PREREQUISITI:")
        print("1. Account PowerBI Pro o Premium")
        print("2. Accesso Azure AD con permessi di registrazione app")
        print("3. Workspace PowerBI dedicato")
        print()

        response = input("Hai tutti i prerequisiti? (y/n): ")
        if response.lower() != "y":
            print("❌ Completa i prerequisiti prima di procedere.")
            sys.exit(1)

        self.log_step("Prerequisiti verificati", "SUCCESS")

    def guide_azure_ad_setup(self):
        """Guida l'utente nel setup Azure AD."""
        self.log_step("Guida setup Azure AD...")

        print("\n🔐 CONFIGURAZIONE AZURE AD")
        print("=" * 30)

        # Apri portale Azure
        print("1. Apertura Portale Azure...")
        azure_url = "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"

        open_browser = input("Aprire il portale Azure automaticamente? (y/n): ")
        if open_browser.lower() == "y":
            webbrowser.open(azure_url)
        else:
            print(f"   Vai a: {azure_url}")

        print("\n2. Creazione App Registration:")
        print("   a) Clicca 'Nuova registrazione'")
        print("   b) Nome: 'Osservatorio-PowerBI-Integration'")
        print(
            "   c) Tipi di account supportati: 'Account in questa directory organizzativa'"
        )
        print("   d) URI di reindirizzamento: lascia vuoto")
        print("   e) Clicca 'Registra'")

        input("\nPremi INVIO quando hai completato la registrazione...")

        # Raccoglie IDs
        print("\n3. Raccolta informazioni:")

        self.config["tenant_id"] = input("   Inserisci Directory (tenant) ID: ").strip()
        self.config["client_id"] = input(
            "   Inserisci Application (client) ID: "
        ).strip()

        print("\n4. Creazione Client Secret:")
        print("   a) Vai a 'Certificati e segreti'")
        print("   b) Clicca 'Nuovo segreto client'")
        print("   c) Descrizione: 'Osservatorio PowerBI Secret'")
        print("   d) Scadenza: 24 mesi")
        print("   e) Clicca 'Aggiungi'")
        print("   f) COPIA IL VALORE DEL SEGRETO (non l'ID!)")

        input("\nPremi INVIO quando hai creato il segreto...")

        self.config["client_secret"] = input(
            "   Inserisci Client Secret (valore): "
        ).strip()

        print("\n5. Configurazione permessi API:")
        print("   a) Vai a 'Autorizzazioni API'")
        print("   b) Clicca 'Aggiungi un'autorizzazione'")
        print("   c) Seleziona 'Power BI Service'")
        print("   d) Seleziona 'Autorizzazioni applicazione'")
        print("   e) Seleziona:")
        print("      - App.Read.All")
        print("      - Capacity.ReadWrite.All")
        print("      - Content.Create")
        print("      - Dataset.ReadWrite.All")
        print("      - Report.ReadWrite.All")
        print("      - Workspace.ReadWrite.All")
        print("   f) Clicca 'Aggiungi autorizzazioni'")
        print("   g) Clicca 'Concedi consenso amministratore'")

        input("\nPremi INVIO quando hai configurato i permessi...")

        self.log_step("Setup Azure AD completato", "SUCCESS")

    def configure_credentials(self):
        """Configura le credenziali PowerBI."""
        self.log_step("Configurazione credenziali...")

        print("\n💼 CONFIGURAZIONE WORKSPACE POWERBI")
        print("=" * 40)

        # Apri PowerBI Service
        powerbi_url = "https://app.powerbi.com/groups/me/list"

        open_browser = input("Aprire PowerBI Service automaticamente? (y/n): ")
        if open_browser.lower() == "y":
            webbrowser.open(powerbi_url)
        else:
            print(f"   Vai a: {powerbi_url}")

        print("\n1. Configurazione Workspace:")
        print("   a) Crea nuovo workspace o usa esistente")
        print("   b) Nome suggerito: 'Osservatorio-ISTAT-Analytics'")
        print("   c) Tipo: Pro o Premium")
        print("   d) Aggiungi l'app registrata ai membri del workspace")

        input("\nPremi INVIO quando hai configurato il workspace...")

        # Workspace ID
        print("\n2. Recupero Workspace ID:")
        print("   a) Vai al workspace creato")
        print("   b) Copia l'ID dall'URL (dopo /groups/)")
        print("   c) Esempio: https://app.powerbi.com/groups/[WORKSPACE-ID]/list")

        self.config["workspace_id"] = input("   Inserisci Workspace ID: ").strip()

        self.log_step("Credenziali configurate", "SUCCESS")

    def test_connection(self):
        """Testa la connessione PowerBI."""
        self.log_step("Test connessione PowerBI...")

        print("\n🔗 TEST CONNESSIONE")
        print("=" * 20)

        # Salva temporaneamente le credenziali
        os.environ["POWERBI_TENANT_ID"] = self.config["tenant_id"]
        os.environ["POWERBI_CLIENT_ID"] = self.config["client_id"]
        os.environ["POWERBI_CLIENT_SECRET"] = self.config["client_secret"]
        os.environ["POWERBI_WORKSPACE_ID"] = self.config["workspace_id"]

        try:
            # Crea client e testa
            client = PowerBIAPIClient()
            test_result = client.test_connection()

            if test_result["authentication"]:
                self.log_step("✅ Autenticazione riuscita", "SUCCESS")
            else:
                self.log_step("❌ Autenticazione fallita", "ERROR")
                return False

            if test_result["workspaces_accessible"]:
                self.log_step(
                    f"✅ Workspace accessibili: {test_result['workspace_count']}",
                    "SUCCESS",
                )
            else:
                self.log_step("❌ Nessun workspace accessibile", "WARNING")

            if test_result["datasets_accessible"]:
                self.log_step(
                    f"✅ Dataset accessibili: {test_result['dataset_count']}", "SUCCESS"
                )
            else:
                self.log_step(
                    "ℹ️ Nessun dataset nel workspace (normale per prima configurazione)",
                    "INFO",
                )

            # Salva risultati test
            test_file = (
                f"powerbi_setup_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_result, f, indent=2, ensure_ascii=False)

            self.log_step(f"Risultati test salvati in: {test_file}", "INFO")

            return True

        except Exception as e:
            self.log_step(f"❌ Errore test connessione: {e}", "ERROR")
            return False

    def save_configuration(self):
        """Salva la configurazione nel file .env."""
        self.log_step("Salvataggio configurazione...")

        # Leggi .env esistente se presente
        env_content = []
        if self.env_file.exists():
            with open(self.env_file, "r", encoding="utf-8") as f:
                env_content = f.readlines()

        # Rimuovi configurazioni PowerBI esistenti
        filtered_content = []
        for line in env_content:
            if not line.strip().startswith("POWERBI_"):
                filtered_content.append(line)

        # Aggiungi nuove configurazioni
        if filtered_content and not filtered_content[-1].endswith("\n"):
            filtered_content.append("\n")

        filtered_content.append("\n# PowerBI Configuration\n")
        filtered_content.append(f'POWERBI_TENANT_ID={self.config["tenant_id"]}\n')
        filtered_content.append(f'POWERBI_CLIENT_ID={self.config["client_id"]}\n')
        filtered_content.append(
            f'POWERBI_CLIENT_SECRET={self.config["client_secret"]}\n'
        )
        filtered_content.append(f'POWERBI_WORKSPACE_ID={self.config["workspace_id"]}\n')

        # Salva file
        with open(self.env_file, "w", encoding="utf-8") as f:
            f.writelines(filtered_content)

        self.log_step(f"Configurazione salvata in: {self.env_file}", "SUCCESS")

    def show_summary(self):
        """Mostra il riepilogo del setup."""
        print("\n" + "=" * 50)
        print("🎉 SETUP COMPLETATO!")
        print("=" * 50)

        print("\n📋 RIEPILOGO CONFIGURAZIONE:")
        print(f"   Tenant ID: {self.config['tenant_id']}")
        print(f"   Client ID: {self.config['client_id']}")
        print(f"   Client Secret: {'*' * len(self.config['client_secret'])}")
        print(f"   Workspace ID: {self.config['workspace_id']}")

        print("\n🔧 PROSSIMI PASSI:")
        print("   1. Esegui: python src/api/powerbi_api.py")
        print("   2. Verifica connessione PowerBI Service")
        print("   3. Esegui: python istat_xml_to_powerbi.py")
        print("   4. Testa upload dataset in PowerBI")

        print("\n📁 FILE GENERATI:")
        print(f"   • {self.env_file} - Configurazione environment")
        print("   • powerbi_setup_test_*.json - Risultati test")

        print("\n💡 SUGGERIMENTI:")
        print("   • Mantieni il segreto client sicuro")
        print("   • Rinnova il segreto prima della scadenza")
        print("   • Monitora i permessi del workspace")

        # Salva log setup
        log_file = f"powerbi_setup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("POWERBI SETUP LOG\n")
            f.write("=" * 20 + "\n\n")
            f.write(
                f"Setup completato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            f.write("PASSI ESEGUITI:\n")
            for entry in self.setup_log:
                f.write(f"{entry}\n")

        print(f"\n📝 Log setup salvato in: {log_file}")


def main():
    """Funzione principale del wizard."""
    try:
        wizard = PowerBISetupWizard()
        wizard.run_setup()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrotto dall'utente.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante il setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
