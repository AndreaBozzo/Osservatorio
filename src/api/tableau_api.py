import json


from ..utils.secure_path import SecurePathValidator


class TableauServerAnalyzer:
    def __init__(self, json_data):
        """Inizializza l'analizzatore con i dati JSON di Tableau Server"""
        self.data = json_data
        self.result = self.data.get("result", {})
        self.user = self.result.get("user", {})
        self.server = self.result.get("server", {})
        self.site = self.result.get("site", {})

    def get_user_info(self):
        """Estrae informazioni utente"""
        return {
            "username": self.user.get("username"),
            "display_name": self.user.get("displayName"),
            "role": self.site.get("role"),
            "domain": self.user.get("domainName"),
            "locale": self.user.get("locale"),
            "timezone": self.user.get("userTimeZone", {}).get("displayName"),
            "sites_count": self.user.get("numberOfSites"),
            "can_web_edit": self.user.get("canWebEditFlow"),
        }

    def get_server_info(self):
        """Estrae informazioni server"""
        version = self.server.get("version", {})
        external_version = version.get("externalVersion", {})

        return {
            "version": f"{external_version.get('major')}.{external_version.get('minor')}.{external_version.get('patch')}",
            "build": version.get("build"),
            "platform": version.get("platform"),
            "bitness": version.get("bitness"),
            "pod_id": self.server.get("podId"),
            "is_beta": self.server.get("betaPod", False),
        }

    def get_available_connectors(self):
        """Estrae connettori OAuth disponibili"""
        oauth_settings = self.server.get("oauthSettings", [])
        connectors = []

        for setting in oauth_settings:
            connector_type = setting.get("type", "")
            display_names = setting.get("displayNames", {})

            connectors.append(
                {
                    "type": connector_type,
                    "name": display_names.get("en", connector_type),
                    "supports_oauth": setting.get("supportsGenericAuth", False),
                    "supports_test_token": setting.get("supportsTestToken", False),
                    "supports_custom_domain": setting.get(
                        "supportsCustomDomain", False
                    ),
                }
            )

        return sorted(connectors, key=lambda x: x["name"])

    def get_site_capabilities(self):
        """Estrae capacità del sito"""
        settings = self.site.get("settings", {})

        return {
            "web_authoring": settings.get("webEditingEnabled", False),
            "flows_enabled": settings.get("flowAutoSaveEnabled", False),
            "collections_enabled": settings.get("collectionsEnabled", False),
            "data_alerts": settings.get("dataAlertsEnabled", False),
            "commenting": settings.get("commentingMentionsEnabled", False),
            "pulse_enabled": settings.get("pulseEnabled", False),
            "generative_ai": settings.get("generativeAiEnabled", False),
            "explain_data": settings.get("explainDataEnabled", False),
            "recycling_bin": settings.get("recycleBinEnabled", False),
            "versioning": self.site.get("versioningEnabled", False),
        }

    def get_governance_settings(self):
        """Estrae impostazioni di governance"""
        settings = self.site.get("settings", {})

        return {
            "catalog_enabled": settings.get("catalogObfuscationEnabled", False),
            "data_management": self.site.get("dataManagementEnabled", False),
            "extract_encryption": self.site.get("extractEncryptionMode"),
            "user_visibility": self.site.get("userVisibility"),
            "mfa_enabled": self.site.get("mfaEnabled", False),
            "mfa_required": self.site.get("mfaRequired", False),
        }

    def find_data_sources(self):
        """Suggerisce possibili fonti dati basate sui connettori disponibili"""
        connectors = self.get_available_connectors()

        # Filtra connettori utili per dati pubblici/statistici
        useful_connectors = [
            conn
            for conn in connectors
            if any(
                keyword in conn["name"].lower()
                for keyword in [
                    "google",
                    "bigquery",
                    "analytics",
                    "sheets",
                    "salesforce",
                    "box",
                    "dropbox",
                    "onedrive",
                    "azure",
                    "amazon",
                ]
            )
        ]

        return useful_connectors

    def generate_scraping_strategy(self):
        """Genera una strategia di scraping basata sulle capacità"""
        strategy = {
            "direct_api": [],
            "web_scraping": [],
            "file_upload": [],
            "recommendations": [],
        }

        connectors = self.find_data_sources()

        # API dirette disponibili
        for conn in connectors:
            if "google" in conn["name"].lower():
                strategy["direct_api"].append(f"Usa {conn['name']} per dati Google")
            elif "bigquery" in conn["name"].lower():
                strategy["direct_api"].append(
                    f"Connessione diretta a BigQuery per grandi dataset"
                )

        # Raccomandazioni generali
        strategy["recommendations"].extend(
            [
                "Considera l'uso di Google Sheets per dati ISTAT elaborati",
                "BigQuery può ospitare grandi dataset statistici",
                "Usa i flussi di Tableau per automatizzare l'elaborazione dati",
                "Implementa governance per tracciare fonti dati",
            ]
        )

        return strategy

    def print_full_analysis(self):
        """Stampa analisi completa"""
        print("=== ANALISI TABLEAU SERVER ===\n")

        # Informazioni utente
        user_info = self.get_user_info()
        print("👤 INFORMAZIONI UTENTE:")
        for key, value in user_info.items():
            print(f"  {key}: {value}")

        # Informazioni server
        print("\n🖥️  INFORMAZIONI SERVER:")
        server_info = self.get_server_info()
        for key, value in server_info.items():
            print(f"  {key}: {value}")

        # Capacità del sito
        print("\n⚙️  CAPACITÀ SITO:")
        capabilities = self.get_site_capabilities()
        for key, value in capabilities.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")

        # Governance
        print("\n🔒 GOVERNANCE:")
        governance = self.get_governance_settings()
        for key, value in governance.items():
            print(f"  {key}: {value}")

        # Connettori disponibili
        print("\n🔌 CONNETTORI DISPONIBILI:")
        connectors = self.find_data_sources()
        for conn in connectors[:10]:  # Primi 10
            oauth_status = "OAuth ✅" if conn["supports_oauth"] else "No OAuth ❌"
            print(f"  • {conn['name']} ({oauth_status})")

        # Strategia di scraping
        print("\n📊 STRATEGIA RACCOLTA DATI:")
        strategy = self.generate_scraping_strategy()

        if strategy["direct_api"]:
            print("  🔗 API DIRETTE:")
            for item in strategy["direct_api"]:
                print(f"    • {item}")

        if strategy["recommendations"]:
            print("  💡 RACCOMANDAZIONI:")
            for item in strategy["recommendations"]:
                print(f"    • {item}")


# Esempio di utilizzo
if __name__ == "__main__":
    # Carica il JSON (sostituisci con il tuo file)
    path_validator = SecurePathValidator(".")
    safe_file = path_validator.safe_open("tableau_config.json", "r")
    with safe_file as f:
        tableau_data = json.load(f)

    analyzer = TableauServerAnalyzer(tableau_data)
    analyzer.print_full_analysis()

    # Esempi di utilizzo specifico
    print("\n=== ESEMPI PRATICI ===")

    # Connettori Google disponibili
    connectors = analyzer.get_available_connectors()
    google_connectors = [c for c in connectors if "google" in c["name"].lower()]

    print("\n📊 CONNETTORI GOOGLE DISPONIBILI:")
    for conn in google_connectors:
        print(f"  • {conn['name']} - OAuth: {conn['supports_oauth']}")

    # Suggerimenti per ISTAT
    print("\n🏛️  SUGGERIMENTI PER DATI ISTAT:")
    print("  1. Usa Google Sheets per caricare CSV ISTAT elaborati")
    print("  2. Configura BigQuery per grandi dataset storici")
    print("  3. Crea flussi automatizzati per aggiornamenti periodici")
    print("  4. Implementa governance per tracciare fonti e qualità dati")
