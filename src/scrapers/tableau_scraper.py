import json
import requests
import pandas as pd
from datetime import datetime
import time


class TableauIstatScraper:
    def __init__(self, config_json):
        """Inizializza lo scraper con la configurazione Tableau"""
        self.config = config_json
        self.base_url = self._extract_base_url()
        self.session = requests.Session()
        self.user_info = config_json["result"]["user"]

    def _extract_base_url(self):
        """Estrae l'URL base dal JSON di configurazione"""
        # Il JSON non contiene l'URL esplicito, ma possiamo dedurlo
        # Tableau Server tipicamente usa pattern come: https://server/
        return "https://tableau-server/"  # Sostituisci con il tuo URL effettivo

    def setup_authentication(self, username, password):
        """Configura l'autenticazione per Tableau Server"""
        auth_payload = {
            "credentials": {
                "name": username,
                "password": password,
                "site": {"contentUrl": self.config["result"]["site"]["urlName"]},
            }
        }

        auth_url = f"{self.base_url}api/3.21/auth/signin"

        try:
            response = self.session.post(auth_url, json=auth_payload)
            if response.status_code == 200:
                self.auth_token = response.json()["credentials"]["token"]
                self.site_id = response.json()["credentials"]["site"]["id"]
                self.session.headers.update(
                    {
                        "X-Tableau-Auth": self.auth_token,
                        "Content-Type": "application/json",
                    }
                )
                return True
            else:
                print(f"Errore autenticazione: {response.status_code}")
                return False
        except Exception as e:
            print(f"Errore durante l'autenticazione: {e}")
            return False

    def get_available_datasources(self):
        """Recupera le fonti dati disponibili"""
        url = f"{self.base_url}api/3.21/sites/{self.site_id}/datasources"

        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get("datasources", {}).get("datasource", [])
            else:
                print(f"Errore nel recupero datasources: {response.status_code}")
                return []
        except Exception as e:
            print(f"Errore: {e}")
            return []

    def get_workbooks(self):
        """Recupera i workbook disponibili"""
        url = f"{self.base_url}api/3.21/sites/{self.site_id}/workbooks"

        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get("workbooks", {}).get("workbook", [])
            else:
                print(f"Errore nel recupero workbooks: {response.status_code}")
                return []
        except Exception as e:
            print(f"Errore: {e}")
            return []

    def search_istat_content(self, search_term="istat"):
        """Cerca contenuto ISTAT nel server"""
        url = f"{self.base_url}api/3.21/sites/{self.site_id}/search"
        params = {"query": search_term, "type": "datasource,workbook,view"}

        try:
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Errore nella ricerca: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Errore: {e}")
            return {}

    def get_datasource_connections(self, datasource_id):
        """Recupera le connessioni di una fonte dati"""
        url = f"{self.base_url}api/3.21/sites/{self.site_id}/datasources/{datasource_id}/connections"

        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get("connections", {}).get("connection", [])
            else:
                print(f"Errore nel recupero connessioni: {response.status_code}")
                return []
        except Exception as e:
            print(f"Errore: {e}")
            return []

    def download_datasource(self, datasource_id, file_path):
        """Scarica una fonte dati"""
        url = f"{self.base_url}api/3.21/sites/{self.site_id}/datasources/{datasource_id}/content"

        try:
            response = self.session.get(url)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"Errore nel download: {response.status_code}")
                return False
        except Exception as e:
            print(f"Errore: {e}")
            return False

    def analyze_tableau_public_urls(self):
        """Analizza URL di Tableau Public per dati ISTAT"""
        # Pattern comuni per URL Tableau Public ISTAT
        potential_urls = [
            "https://public.tableau.com/profile/istat",
            "https://public.tableau.com/search?q=istat",
            "https://public.tableau.com/search?q=italia+statistiche",
            "https://public.tableau.com/search?q=demografia+italia",
        ]

        results = []
        for url in potential_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    results.append(
                        {
                            "url": url,
                            "status": "accessible",
                            "content_length": len(response.content),
                        }
                    )
                else:
                    results.append(
                        {
                            "url": url,
                            "status": f"error_{response.status_code}",
                            "content_length": 0,
                        }
                    )
            except Exception as e:
                results.append(
                    {"url": url, "status": f"error_{str(e)}", "content_length": 0}
                )

        return results

    def create_istat_data_strategy(self):
        """Crea una strategia per raccogliere dati ISTAT"""
        strategy = {
            "timestamp": datetime.now().isoformat(),
            "server_capabilities": self._analyze_server_capabilities(),
            "recommended_connectors": self._get_recommended_connectors(),
            "data_sources": self._suggest_istat_sources(),
            "implementation_steps": self._create_implementation_plan(),
        }

        return strategy

    def _analyze_server_capabilities(self):
        """Analizza le capacità del server per dati ISTAT"""
        capabilities = {
            "web_authoring": self.config["result"]["site"]["settings"][
                "webEditingEnabled"
            ],
            "flows_enabled": self.config["result"]["site"]["settings"][
                "flowAutoSaveEnabled"
            ],
            "data_management": self.config["result"]["site"]["dataManagementEnabled"],
            "scheduling": self.config["result"]["site"]["runNowEnabled"],
            "extract_encryption": self.config["result"]["site"][
                "extractEncryptionMode"
            ],
        }

        return capabilities

    def _get_recommended_connectors(self):
        """Suggerisce connettori utili per dati ISTAT"""
        oauth_settings = self.config["result"]["server"]["oauthSettings"]

        recommended = []
        for setting in oauth_settings:
            connector_name = setting["displayNames"].get("en", setting["type"])

            # Connettori utili per dati pubblici/statistici
            if any(
                keyword in connector_name.lower()
                for keyword in [
                    "google sheets",
                    "bigquery",
                    "box",
                    "dropbox",
                    "onedrive",
                ]
            ):
                recommended.append(
                    {
                        "name": connector_name,
                        "type": setting["type"],
                        "oauth_support": setting["supportsGenericAuth"],
                        "use_case": self._suggest_use_case(connector_name),
                    }
                )

        return recommended

    def _suggest_use_case(self, connector_name):
        """Suggerisce casi d'uso per ogni connettore"""
        use_cases = {
            "google sheets": "Caricamento CSV ISTAT elaborati e condivisione",
            "bigquery": "Storage di grandi dataset storici ISTAT",
            "box": "Condivisione file e collaborazione su dati",
            "dropbox": "Sincronizzazione automatica file dati",
            "onedrive": "Integrazione con Microsoft Office per report",
        }

        for key, value in use_cases.items():
            if key in connector_name.lower():
                return value

        return "Uso generico per dati esterni"

    def _suggest_istat_sources(self):
        """Suggerisce fonti dati ISTAT specifiche"""
        return [
            {
                "source": "ISTAT I.Stat",
                "url": "http://dati.istat.it",
                "method": "API REST",
                "description": "Database multidimensionale delle statistiche ISTAT",
            },
            {
                "source": "ISTAT Open Data",
                "url": "https://www.istat.it/it/dati-analisi-e-prodotti/banche-dati",
                "method": "Download CSV",
                "description": "Dataset aperti in formato CSV",
            },
            {
                "source": "Tableau Public ISTAT",
                "url": "https://public.tableau.com/search?q=istat",
                "method": "Web Scraping",
                "description": "Visualizzazioni pubbliche con dati ISTAT",
            },
        ]

    def _create_implementation_plan(self):
        """Crea un piano di implementazione"""
        return [
            {
                "step": 1,
                "action": "Configurare connettori",
                "description": "Impostare Google Sheets e BigQuery per dati ISTAT",
                "estimated_time": "1-2 ore",
            },
            {
                "step": 2,
                "action": "Creare flussi di dati",
                "description": "Automatizzare il caricamento dati da ISTAT",
                "estimated_time": "2-3 ore",
            },
            {
                "step": 3,
                "action": "Sviluppare dashboard",
                "description": "Creare visualizzazioni per dati demografici/economici",
                "estimated_time": "3-4 ore",
            },
            {
                "step": 4,
                "action": "Implementare governance",
                "description": "Configurare refresh automatici e qualità dati",
                "estimated_time": "1-2 ore",
            },
        ]

    def export_strategy_to_json(self, strategy, filename="istat_strategy.json"):
        """Esporta la strategia in JSON"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(strategy, f, ensure_ascii=False, indent=2)

        print(f"Strategia esportata in {filename}")


# Esempio di utilizzo
if __name__ == "__main__":
    # Carica la configurazione Tableau
    with open("tableau_config.json", "r") as f:
        tableau_config = json.load(f)

    # Inizializza lo scraper
    scraper = TableauIstatScraper(tableau_config)

    # Crea strategia per dati ISTAT
    strategy = scraper.create_istat_data_strategy()

    # Esporta strategia
    scraper.export_strategy_to_json(strategy)

    # Analizza URL Tableau Public
    public_analysis = scraper.analyze_tableau_public_urls()

    print("=== ANALISI TABLEAU PUBLIC ===")
    for result in public_analysis:
        print(f"URL: {result['url']}")
        print(f"Status: {result['status']}")
        print(f"Content: {result['content_length']} bytes")
        print("---")

    # Stampa raccomandazioni
    print("\n=== RACCOMANDAZIONI ===")
    for connector in strategy["recommended_connectors"]:
        print(f"• {connector['name']}: {connector['use_case']}")

    print("\n=== PIANO IMPLEMENTAZIONE ===")
    for step in strategy["implementation_steps"]:
        print(f"{step['step']}. {step['action']}")
        print(f"   {step['description']}")
        print(f"   Tempo stimato: {step['estimated_time']}")
