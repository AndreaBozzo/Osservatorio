"""
PowerBI API Client per integrazione con Microsoft Power BI Service.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import msal
import pandas as pd
import requests

from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.secure_path import SecurePathValidator, create_secure_validator

logger = get_logger(__name__)


class PowerBIAPIClient:
    """Client per interagire con PowerBI REST API."""

    def __init__(self):
        """Inizializza il client PowerBI."""
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.client_id = Config.POWERBI_CLIENT_ID
        self.client_secret = Config.POWERBI_CLIENT_SECRET
        self.tenant_id = Config.POWERBI_TENANT_ID
        self.workspace_id = Config.POWERBI_WORKSPACE_ID
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Controlla se le credenziali sono disponibili
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning(
                "PowerBI credentials not configured. Set POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, and POWERBI_TENANT_ID environment variables."
            )
            self.app = None
            return

        # Configurazione MSAL
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://analysis.windows.net/powerbi/api/.default"]

        # Inizializza app MSAL
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "Osservatorio-PowerBI-Client/1.0",
            }
        )

        # Initialize secure path validator
        self.path_validator = create_secure_validator(os.getcwd())

        logger.info("PowerBI API Client inizializzato")

    def authenticate(self) -> bool:
        """Autentica con PowerBI usando credenziali service principal."""
        if not self.app:
            logger.error("PowerBI app not initialized - missing credentials")
            return False

        try:
            # Acquisisce token usando client credentials flow
            result = self.app.acquire_token_silent(self.scope, account=None)

            if not result:
                logger.info("Nessun token valido in cache, acquisizione nuovo token...")
                result = self.app.acquire_token_for_client(scopes=self.scope)

            if "access_token" in result:
                self.access_token = result["access_token"]
                # Calcola scadenza token (default 3600 secondi)
                expires_in = result.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(
                    seconds=expires_in - 300
                )  # 5 min buffer

                # Aggiorna header sessione
                self.session.headers.update(
                    {"Authorization": f"Bearer {self.access_token}"}
                )

                logger.info("Autenticazione PowerBI completata")
                return True
            else:
                logger.error(
                    f"Errore autenticazione: {result.get('error_description', 'Unknown error')}"
                )
                return False

        except Exception as e:
            logger.error(f"Errore durante autenticazione PowerBI: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        """Verifica che il client sia autenticato e rinnova il token se necessario."""
        if (
            not self.access_token
            or not self.token_expires_at
            or datetime.now() >= self.token_expires_at
        ):
            logger.info("Token scaduto o mancante, rinnovo...")
            return self.authenticate()
        return True

    def get_workspaces(self) -> List[Dict[str, Any]]:
        """Recupera lista dei workspace disponibili."""
        if not self._ensure_authenticated():
            return []

        try:
            response = self.session.get(f"{self.base_url}/groups")
            response.raise_for_status()

            workspaces = response.json().get("value", [])
            logger.info(f"Recuperati {len(workspaces)} workspace")
            return workspaces

        except requests.RequestException as e:
            logger.error(f"Errore recupero workspace: {e}")
            return []

    def get_datasets(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recupera lista dei dataset nel workspace."""
        if not self._ensure_authenticated():
            return []

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return []

        try:
            response = self.session.get(
                f"{self.base_url}/groups/{workspace_id}/datasets"
            )
            response.raise_for_status()

            datasets = response.json().get("value", [])
            logger.info(
                f"Recuperati {len(datasets)} dataset dal workspace {workspace_id}"
            )
            return datasets

        except requests.RequestException as e:
            logger.error(f"Errore recupero dataset: {e}")
            return []

    def get_reports(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recupera lista dei report nel workspace."""
        if not self._ensure_authenticated():
            return []

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return []

        try:
            response = self.session.get(
                f"{self.base_url}/groups/{workspace_id}/reports"
            )
            response.raise_for_status()

            reports = response.json().get("value", [])
            logger.info(
                f"Recuperati {len(reports)} report dal workspace {workspace_id}"
            )
            return reports

        except requests.RequestException as e:
            logger.error(f"Errore recupero report: {e}")
            return []

    def create_dataset(
        self, dataset_definition: Dict, workspace_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Crea un nuovo dataset in PowerBI."""
        if not self._ensure_authenticated():
            return None

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return None

        try:
            response = self.session.post(
                f"{self.base_url}/groups/{workspace_id}/datasets",
                json=dataset_definition,
            )
            response.raise_for_status()

            dataset = response.json()
            logger.info(
                f"Dataset creato: {dataset.get('name')} (ID: {dataset.get('id')})"
            )
            return dataset

        except requests.RequestException as e:
            logger.error(f"Errore creazione dataset: {e}")
            return None

    def push_data_to_dataset(
        self,
        dataset_id: str,
        table_name: str,
        data: List[Dict[str, Any]],
        workspace_id: Optional[str] = None,
    ) -> bool:
        """Invia dati a un dataset esistente."""
        if not self._ensure_authenticated():
            return False

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return False

        try:
            # Prepara payload
            payload = {"rows": data}

            response = self.session.post(
                f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows",
                json=payload,
            )
            response.raise_for_status()

            logger.info(
                f"Dati inviati al dataset {dataset_id}, tabella {table_name}: {len(data)} righe"
            )
            return True

        except requests.RequestException as e:
            logger.error(f"Errore invio dati: {e}")
            return False

    def refresh_dataset(
        self, dataset_id: str, workspace_id: Optional[str] = None
    ) -> bool:
        """Avvia refresh di un dataset."""
        if not self._ensure_authenticated():
            return False

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return False

        try:
            response = self.session.post(
                f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
            )
            response.raise_for_status()

            logger.info(f"Refresh avviato per dataset {dataset_id}")
            return True

        except requests.RequestException as e:
            logger.error(f"Errore refresh dataset: {e}")
            return False

    def get_dataset_refresh_history(
        self, dataset_id: str, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Recupera cronologia refresh di un dataset."""
        if not self._ensure_authenticated():
            return []

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return []

        try:
            response = self.session.get(
                f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
            )
            response.raise_for_status()

            history = response.json().get("value", [])
            logger.info(
                f"Recuperata cronologia refresh per dataset {dataset_id}: {len(history)} elementi"
            )
            return history

        except requests.RequestException as e:
            logger.error(f"Errore recupero cronologia refresh: {e}")
            return []

    def upload_pbix_file(
        self, file_path: str, dataset_name: str, workspace_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Carica un file PBIX nel workspace."""
        if not self._ensure_authenticated():
            return None

        workspace_id = workspace_id or self.workspace_id
        if not workspace_id:
            logger.error("Workspace ID non specificato")
            return None

        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File non trovato: {file_path}")
            return None

        try:
            # Prepara headers per upload file
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream",
            }

            safe_file = self.path_validator.safe_open(file_path, "rb")
            with safe_file as file:
                response = requests.post(
                    f"{self.base_url}/groups/{workspace_id}/imports",
                    headers=headers,
                    files={"file": file},
                    params={"datasetDisplayName": dataset_name},
                )
                response.raise_for_status()

            result = response.json()
            logger.info(
                f"File PBIX caricato: {dataset_name} (Import ID: {result.get('id')})"
            )
            return result

        except requests.RequestException as e:
            logger.error(f"Errore upload PBIX: {e}")
            return None

    def test_connection(self) -> Dict[str, Any]:
        """Testa la connessione a PowerBI e ritorna informazioni diagnostiche."""
        logger.info("Test connessione PowerBI...")

        test_result = {
            "timestamp": datetime.now().isoformat(),
            "authentication": False,
            "workspaces_accessible": False,
            "workspace_count": 0,
            "datasets_accessible": False,
            "dataset_count": 0,
            "errors": [],
        }

        try:
            # Test autenticazione
            if self.authenticate():
                test_result["authentication"] = True
                logger.info("✅ Autenticazione riuscita")
            else:
                test_result["errors"].append("Autenticazione fallita")
                return test_result

            # Test accesso workspace
            workspaces = self.get_workspaces()
            if workspaces:
                test_result["workspaces_accessible"] = True
                test_result["workspace_count"] = len(workspaces)
                logger.info(f"✅ Workspace accessibili: {len(workspaces)}")
            else:
                test_result["errors"].append("Nessun workspace accessibile")

            # Test accesso dataset nel workspace di default
            if self.workspace_id:
                datasets = self.get_datasets()
                if datasets:
                    test_result["datasets_accessible"] = True
                    test_result["dataset_count"] = len(datasets)
                    logger.info(f"✅ Dataset accessibili: {len(datasets)}")
                else:
                    logger.warning("Nessun dataset trovato nel workspace di default")

            logger.info("Test connessione PowerBI completato")

        except Exception as e:
            error_msg = f"Errore durante test connessione: {e}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result


def main():
    """Funzione di test per il client PowerBI."""
    print("🔗 TEST POWERBI API CLIENT")
    print("=" * 50)

    # Verifica configurazione
    if not all(
        [
            Config.POWERBI_CLIENT_ID,
            Config.POWERBI_CLIENT_SECRET,
            Config.POWERBI_TENANT_ID,
        ]
    ):
        print("❌ Configurazione PowerBI incompleta!")
        print(
            "Imposta le variabili d'ambiente: POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID"
        )
        return

    client = PowerBIAPIClient()

    # Esegui test completo
    test_result = client.test_connection()

    print("\n📊 RISULTATI TEST:")
    print(f"Autenticazione: {'✅' if test_result['authentication'] else '❌'}")
    print(
        f"Workspace accessibili: {'✅' if test_result['workspaces_accessible'] else '❌'}"
    )
    print(f"Numero workspace: {test_result['workspace_count']}")
    print(f"Dataset accessibili: {'✅' if test_result['datasets_accessible'] else '❌'}")
    print(f"Numero dataset: {test_result['dataset_count']}")

    if test_result["errors"]:
        print(f"\n❌ ERRORI:")
        for error in test_result["errors"]:
            print(f"  • {error}")

    # Salva risultati test
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = f"powerbi_test_results_{timestamp}.json"
    path_validator = SecurePathValidator(".")
    safe_file = path_validator.safe_open(test_file, "w", encoding="utf-8")
    with safe_file as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Risultati salvati in: {test_file}")


if __name__ == "__main__":
    main()
