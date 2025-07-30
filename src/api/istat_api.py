import json
import time
import warnings
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests

from ..utils.secure_path import create_secure_validator
from ..utils.security_enhanced import rate_limit, security_manager
from ..utils.temp_file_manager import get_temp_manager

# seaborn removed - using matplotlib directly


class IstatAPITester:
    def __init__(self):
        """Inizializza il tester API ISTAT"""
        # Issue #66 - This exploration tool is deprecated
        warnings.warn(
            "IstatAPITester is deprecated and will be removed in a future version. "
            "Use ProductionIstatClient for production workflows. "
            "See docs/migration/ISTAT_API_MIGRATION.md for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.base_url = "https://sdmx.istat.it/SDMXWS/rest/"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/xml, application/json",
            }
        )
        self.test_results = []
        self.temp_manager = get_temp_manager()

        # Initialize secure path validator for current directory
        import os

        self.path_validator = create_secure_validator(os.getcwd())

    @rate_limit(max_requests=50, window=3600)  # 50 requests per hour
    def _test_single_endpoint(self, endpoint):
        """Test a single endpoint - helper method for integration tests"""
        # Handle both string and dict parameters first to get endpoint_name
        if isinstance(endpoint, dict):
            endpoint_name = endpoint.get("name", "unknown")
            url = endpoint.get("url", f"{self.base_url}{endpoint_name}/IT1")
        else:
            endpoint_name = endpoint
            url = f"{self.base_url}{endpoint_name}/IT1"

        try:
            # Rate limiting check
            if not security_manager.rate_limit(
                "istat_api_test", max_requests=50, window=3600
            ):
                raise Exception("Rate limit exceeded for ISTAT API testing")

            response = self.session.get(url, timeout=10)

            return {
                "endpoint": endpoint_name,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": 0.1,  # Mock response time
                "content_type": response.headers.get("Content-Type", "unknown"),
                "data_length": len(response.content) if response.content else 0,
            }
        except Exception as e:
            return {
                "endpoint": endpoint_name,
                "success": False,
                "status_code": 500,
                "response_time": 0.0,
                "error": str(e),
            }

    def test_api_connectivity(self):
        """Testa la connettività di base alle API ISTAT SDMX"""
        print("🔍 Test connettività API ISTAT SDMX...")

        endpoints_to_test = [
            {"name": "dataflow", "url": f"{self.base_url}dataflow/IT1"},
            {"name": "codelist", "url": f"{self.base_url}codelist/IT1"},
            {"name": "datastructure", "url": f"{self.base_url}datastructure/IT1"},
        ]

        connectivity_results = []

        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                response = self.session.get(endpoint["url"], timeout=30)
                response_time = time.time() - start_time

                result = {
                    "endpoint": endpoint["name"],
                    "url": endpoint["url"],
                    "status_code": response.status_code,
                    "response_time": round(response_time, 2),
                    "success": response.status_code == 200,
                    "data_length": (
                        len(response.content) if response.status_code == 200 else 0
                    ),
                    "content_type": response.headers.get("content-type", "unknown"),
                }

                if response.status_code == 200:
                    print(
                        f"✅ {endpoint['name']}: OK ({response_time:.2f}s) - {result['content_type']}"
                    )
                else:
                    print(f"❌ {endpoint['name']}: Error {response.status_code}")

                connectivity_results.append(result)

            except Exception as e:
                print(f"❌ {endpoint['name']}: Exception {str(e)}")
                connectivity_results.append(
                    {
                        "endpoint": endpoint["name"],
                        "url": endpoint["url"],
                        "success": False,
                        "error": str(e),
                    }
                )

            time.sleep(1)  # Rate limiting

        return connectivity_results

    def discover_available_datasets(self, limit=20):
        """Scopre i dataflow SDMX disponibili con focus su dati demografici/economici"""
        print(f"\n📊 Scoperta dataflow SDMX disponibili (limit: {limit})...")

        try:
            response = self.session.get(f"{self.base_url}dataflow/IT1", timeout=30)
            if response.status_code != 200:
                print(f"❌ Errore nel recupero dataflow: {response.status_code}")
                return []

            print(
                f"✅ Dataflow recuperati - Content Type: {response.headers.get('content-type', 'unknown')}"
            )

            # Salva la risposta XML per debugging in directory temporanea
            temp_file = self.temp_manager.get_temp_file_path(
                "dataflow_response.xml", "api_responses"
            )
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"📁 Risposta XML salvata in: {temp_file}")

            # Parsing XML semplificato per estrarre ID e nomi
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.content)

            # Namespace SDMX (potrebbe variare)
            namespaces = {
                "str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
                "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
            }

            dataflows = []

            # Cerca dataflow con diversi pattern
            for dataflow in root.findall(".//str:Dataflow", namespaces):
                dataflow_id = dataflow.get("id", "")

                # Cerca il nome
                name_elem = dataflow.find(".//com:Name", namespaces)
                dataflow_name = name_elem.text if name_elem is not None else dataflow_id

                if dataflow_id:
                    dataflows.append(
                        {
                            "id": dataflow_id,
                            "name": dataflow_name,
                            "relevance_score": 1,  # Base score
                        }
                    )

            # Se non trova con namespace, prova senza
            if not dataflows:
                for dataflow in root.findall(".//Dataflow"):
                    dataflow_id = dataflow.get("id", "")
                    name_elem = dataflow.find(".//Name")
                    dataflow_name = (
                        name_elem.text if name_elem is not None else dataflow_id
                    )

                    if dataflow_id:
                        dataflows.append(
                            {
                                "id": dataflow_id,
                                "name": dataflow_name,
                                "relevance_score": 1,
                            }
                        )

            # Filtra per rilevanza
            relevant_keywords = [
                "popolazione",
                "demographic",
                "economia",
                "lavoro",
                "occupazione",
                "inflazione",
                "pil",
                "reddito",
                "famiglia",
                "nascite",
                "morti",
                "popres",
                "demo",
                "econ",
                "employ",
                "gdp",
                "income",
            ]

            relevant_dataflows = []

            for dataflow in dataflows[:limit]:
                name_lower = dataflow["name"].lower()
                id_lower = dataflow["id"].lower()

                relevance = sum(
                    1 for kw in relevant_keywords if kw in name_lower or kw in id_lower
                )

                if relevance > 0:
                    dataflow["relevance_score"] = relevance
                    relevant_dataflows.append(dataflow)

            # Ordina per rilevanza
            relevant_dataflows.sort(key=lambda x: x["relevance_score"], reverse=True)

            print(
                f"✅ Trovati {len(dataflows)} dataflow totali, {len(relevant_dataflows)} rilevanti:"
            )
            for i, dataflow in enumerate(relevant_dataflows[:10]):  # Top 10
                print(
                    f"  {i + 1}. {dataflow['name']} (ID: {dataflow['id']}, Score: {dataflow['relevance_score']})"
                )

            return relevant_dataflows

        except Exception as e:
            print(f"❌ Errore nella scoperta dataflow: {e}")
            return []

    def test_specific_dataset(self, dataset_id, dataset_name="Unknown"):
        """Testa l'accesso a un dataflow SDMX specifico"""
        print(f"\n🔬 Test dataflow specifico: {dataset_name} ({dataset_id})")

        test_result = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Test 1: Struttura dataflow (DSD - Data Structure Definition)
            structure_url = f"{self.base_url}datastructure/IT1/{dataset_id}"
            structure_response = self.session.get(structure_url, timeout=30)

            test_result["structure_test"] = {
                "success": structure_response.status_code == 200,
                "status_code": structure_response.status_code,
                "content_type": structure_response.headers.get(
                    "content-type", "unknown"
                ),
            }

            if structure_response.status_code == 200:
                # Salva struttura per debugging in directory temporanea
                structure_filename = f"structure_{dataset_id}.xml"
                temp_file = self.temp_manager.get_temp_file_path(
                    structure_filename, "api_responses"
                )
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(structure_response.text)
                test_result["structure_test"]["saved_file"] = str(temp_file)
                print(f"  ✅ Struttura: OK - Salvata in {structure_filename}")
            else:
                print(f"  ❌ Struttura: Error {structure_response.status_code}")

            # Test 2: Dati campione (SDMX Data)
            data_url = f"{self.base_url}data/{dataset_id}"
            data_response = self.session.get(data_url, timeout=60)

            test_result["data_test"] = {
                "success": data_response.status_code == 200,
                "status_code": data_response.status_code,
                "content_type": data_response.headers.get("content-type", "unknown"),
            }

            if data_response.status_code == 200:
                # Salva dati per debugging in directory temporanea
                data_filename = f"data_{dataset_id}.xml"
                temp_file = self.temp_manager.get_temp_file_path(
                    data_filename, "api_responses"
                )
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(data_response.text)
                test_result["data_test"]["saved_file"] = str(temp_file)
                test_result["data_test"]["data_size"] = len(data_response.content)
                print(
                    f"  ✅ Dati: OK - {len(data_response.content)} bytes salvati in {data_filename}"
                )
            else:
                print(f"  ❌ Dati: Error {data_response.status_code}")

            # Test 3: Prova parsing semplificato se ha dati
            if test_result["data_test"]["success"]:
                try:
                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(data_response.content)

                    # Conta osservazioni (pattern comune SDMX)
                    observations = root.findall('.//*[local-name()="Obs"]')
                    if not observations:
                        observations = root.findall('.//*[local-name()="Observation"]')

                    test_result["data_test"]["observations_count"] = len(observations)
                    print(f"  📊 Osservazioni trovate: {len(observations)}")

                except Exception as parse_error:
                    test_result["data_test"]["parse_error"] = str(parse_error)
                    print(f"  ⚠️  Errore parsing XML: {parse_error}")

        except Exception as e:
            test_result["error"] = str(e)
            print(f"  ❌ Errore generale: {e}")

        self.test_results.append(test_result)
        return test_result

    def test_popular_datasets(self):
        """Testa accesso ai dataset più popolari/importanti"""
        print("\n📈 Test dataset popolari ISTAT...")

        # Lista dataset noti/importanti
        popular_datasets = [
            {"id": "DCIS_POPRES1", "name": "Popolazione residente"},
            {"id": "DCIS_POPSTRRES1", "name": "Popolazione per struttura"},
            {"id": "DCIS_FECONDITA", "name": "Indicatori di fecondità"},
            {"id": "DCIS_MORTALITA1", "name": "Tavole di mortalità"},
            {"id": "DCIS_RICFAMILIARE1", "name": "Reddito delle famiglie"},
        ]

        successful_tests = 0

        for dataset in popular_datasets:
            result = self.test_specific_dataset(dataset["id"], dataset["name"])
            if result.get("data_test", {}).get("success", False):
                successful_tests += 1
            time.sleep(2)  # Rate limiting

        print(
            f"\n📊 Risultati test dataset popolari: {successful_tests}/{len(popular_datasets)} successi"
        )
        return successful_tests

    def validate_data_quality(self, dataset_id, sample_size=1000):
        """Valida la qualità dei dati di un dataset"""
        print(f"\n🔍 Validazione qualità dati per dataset {dataset_id}...")

        try:
            # Recupera dati campione
            data_url = f"{self.base_url}data/{dataset_id}"
            response = self.session.get(
                data_url, params={"limit": sample_size}, timeout=60
            )

            if response.status_code != 200:
                print(f"❌ Impossibile recuperare dati: {response.status_code}")
                return None

            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                print("❌ Nessun dato trovato")
                return None

            # Converte in DataFrame per analisi
            df = pd.json_normalize(observations)

            quality_report = {
                "dataset_id": dataset_id,
                "total_records": len(df),
                "total_columns": len(df.columns),
                "missing_values": {},
                "data_types": {},
                "type_mismatch_count": {},
                "special_char_count": {},
                "unique_values": {},
                "quality_score": 0,
            }

            # Analisi per colonna
            for col in df.columns:
                # Valori mancanti
                missing_count = df[col].isnull().sum()
                quality_report["missing_values"][col] = {
                    "count": int(missing_count),
                    "percentage": round((missing_count / len(df)) * 100, 2),
                }

                # Tipo dati
                quality_report["data_types"][col] = str(df[col].dtype)

                # Valori diversi dal loro data type
                if len(df) > 0:
                    type_mismatch_count = (df[col].apply(type) != df[col].dtype).sum()
                    quality_report["type_mismatch_count"][col] = {
                        "count": int(type_mismatch_count),
                        "percentage": round((type_mismatch_count / len(df)) * 100, 2),
                    }

                # Valori con caratteri speciali e accenti
                if len(df) > 0:
                    # Versione ISTAT-friendly:
                    special_char_pattern = r"[^\w\s\.\-\+\(\)àèéìíîòóùú/\']"
                    special_char_count = (
                        df[col].str.contains(special_char_pattern, regex=True).sum()
                    )
                    quality_report["special_char_count"][col] = {
                        "count": int(special_char_count),
                        "percentage": round((special_char_count / len(df)) * 100, 2),
                    }

                # Valori unici (se ragionevole)
                if len(df) > 0:
                    unique_count = df[col].nunique()
                    quality_report["unique_values"][col] = {
                        "count": int(unique_count),
                        "percentage": round((unique_count / len(df)) * 100, 2),
                    }

            # Calcola punteggio qualità
            completeness_score = 100 - (
                sum(
                    col["percentage"]
                    for col in quality_report["missing_values"].values()
                )
                / len(df.columns)
            )
            quality_report["quality_score"] = max(0, min(100, completeness_score))

            print(f"✅ Qualità dati analizzata:")
            print(f"  📊 Record: {quality_report['total_records']}")
            print(f"  📋 Colonne: {quality_report['total_columns']}")
            print(f"  🎯 Punteggio qualità: {quality_report['quality_score']:.1f}/100")

            # Salva report in modo sicuro
            report_filename = f"quality_report_{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Valida e sanitizza il nome del file
            if not self.path_validator.validate_filename(report_filename):
                report_filename = self.path_validator.sanitize_filename(report_filename)

            safe_file = self.path_validator.safe_open(
                report_filename, "w", encoding="utf-8"
            )
            if safe_file:
                with safe_file as f:
                    json.dump(quality_report, f, ensure_ascii=False, indent=2)
                print(f"  💾 Report salvato: {report_filename}")
            else:
                print(f"  ❌ Impossibile salvare report: {report_filename}")

            return quality_report

        except Exception as e:
            print(f"❌ Errore validazione qualità: {e}")
            return None

    def create_data_preview_visualization(self, dataset_id, max_records=500):
        """Crea visualizzazioni di anteprima dei dati"""
        print(f"\n📊 Creazione visualizzazioni anteprima per {dataset_id}...")

        try:
            # Recupera dati
            data_url = f"{self.base_url}data/{dataset_id}"
            response = self.session.get(
                data_url, params={"limit": max_records}, timeout=60
            )

            if response.status_code != 200:
                print(f"❌ Errore recupero dati: {response.status_code}")
                return False

            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                print("❌ Nessun dato per visualizzazioni")
                return False

            df = pd.json_normalize(observations)

            # Configura stile grafici
            plt.style.use("default")
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(
                f"Anteprima Dati ISTAT - Dataset {dataset_id}",
                fontsize=16,
                fontweight="bold",
            )

            # Grafico 1: Distribuzione valori mancanti
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                missing_data[missing_data > 0].plot(
                    kind="bar", ax=axes[0, 0], color="coral"
                )
                axes[0, 0].set_title("Valori Mancanti per Colonna")
                axes[0, 0].set_xlabel("Colonne")
                axes[0, 0].set_ylabel("Conteggio")
                axes[0, 0].tick_params(axis="x", rotation=45)
            else:
                axes[0, 0].text(
                    0.5,
                    0.5,
                    "Nessun valore mancante",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=axes[0, 0].transAxes,
                    fontsize=12,
                )
                axes[0, 0].set_title("Valori Mancanti per Colonna")

            # Grafico 2: Tipi di dati
            data_types = df.dtypes.value_counts()
            try:
                # Try new matplotlib API first
                import matplotlib.pyplot as plt
                from matplotlib import colormaps

                cmap = colormaps.get_cmap("Set3")
            except (ImportError, AttributeError):
                # Fallback to older API
                cmap = plt.get_cmap("Set3")
            colors = [cmap(i) for i in range(len(data_types))]
            axes[0, 1].pie(
                data_types.values,
                labels=data_types.index,
                autopct="%1.1f%%",
                colors=colors,
            )
            axes[0, 1].set_title("Distribuzione Tipi di Dati")

            # Grafico 3: Sample delle prime colonne numeriche
            numeric_cols = df.select_dtypes(include=["number"]).columns[:3]
            if len(numeric_cols) > 0:
                df[numeric_cols].hist(ax=axes[1, 0], bins=20, alpha=0.7)
                axes[1, 0].set_title("Distribuzione Valori Numerici (Sample)")
            else:
                axes[1, 0].text(
                    0.5,
                    0.5,
                    "Nessuna colonna numerica trovata",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=axes[1, 0].transAxes,
                    fontsize=12,
                )
                axes[1, 0].set_title("Distribuzione Valori Numerici")

            # Grafico 4: Conteggio record per categoria (se applicabile)
            categorical_cols = df.select_dtypes(include=["object"]).columns
            if len(categorical_cols) > 0:
                first_cat_col = categorical_cols[0]
                value_counts = df[first_cat_col].value_counts().head(10)
                value_counts.plot(kind="barh", ax=axes[1, 1], color="lightblue")
                axes[1, 1].set_title(f"Top 10 Valori - {first_cat_col}")
                axes[1, 1].set_xlabel("Conteggio")
            else:
                axes[1, 1].text(
                    0.5,
                    0.5,
                    "Nessuna colonna categorica trovata",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=axes[1, 1].transAxes,
                    fontsize=12,
                )
                axes[1, 1].set_title("Distribuzione Valori Categorici")

            plt.tight_layout()

            # Salva visualizzazione in modo sicuro
            viz_filename = (
                f"preview_{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )

            # Valida e sanitizza il nome del file
            if not self.path_validator.validate_filename(viz_filename):
                viz_filename = self.path_validator.sanitize_filename(viz_filename)

            safe_path = self.path_validator.get_safe_path(viz_filename)
            if safe_path:
                plt.savefig(safe_path, dpi=300, bbox_inches="tight")
                plt.close()
                print(f"✅ Visualizzazione salvata: {safe_path}")
            else:
                plt.close()
                print(f"❌ Impossibile salvare visualizzazione: {viz_filename}")

            # Crea anche summary statistico in modo sicuro
            summary_filename = (
                f"summary_{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            # Valida e sanitizza il nome del file
            if not self.path_validator.validate_filename(summary_filename):
                summary_filename = self.path_validator.sanitize_filename(
                    summary_filename
                )

            safe_file = self.path_validator.safe_open(
                summary_filename, "w", encoding="utf-8"
            )
            if safe_file:
                with safe_file as f:
                    f.write(f"SUMMARY STATISTICO - Dataset ISTAT {dataset_id}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(
                        f"Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    )
                    f.write(f"Record totali: {len(df)}\n")
                    f.write(f"Colonne totali: {len(df.columns)}\n\n")
                    f.write("COLONNE:\n")
                    for col in df.columns:
                        f.write(f"  • {col} ({df[col].dtype})\n")
                    f.write("\n")
                    f.write("STATISTICHE DESCRITTIVE:\n")
                    f.write(str(df.describe(include="all")))
                print(f"✅ Summary salvato: {summary_filename}")
            else:
                print(f"❌ Impossibile salvare summary: {summary_filename}")

            return True

        except Exception as e:
            print(f"❌ Errore creazione visualizzazioni: {e}")
            return False

    def run_comprehensive_test(self):
        """Esegue test completo delle API ISTAT"""
        print("🚀 AVVIO TEST COMPLETO API ISTAT")
        print("=" * 50)

        test_report = {"timestamp": datetime.now().isoformat(), "tests": {}}

        # Test 1: Connettività
        print("\n1️⃣ TEST CONNETTIVITÀ")
        connectivity_results = self.test_api_connectivity()
        test_report["tests"]["connectivity"] = connectivity_results
        successful_endpoints = sum(
            1 for r in connectivity_results if r.get("success", False)
        )

        if successful_endpoints == 0:
            print("❌ ERRORE CRITICO: Nessun endpoint accessibile!")
            return test_report

        # Test 2: Scoperta dataset
        print("\n2️⃣ SCOPERTA DATASET")
        relevant_datasets = self.discover_available_datasets(limit=50)
        test_report["tests"]["dataset_discovery"] = {
            "total_found": len(relevant_datasets),
            "datasets": relevant_datasets[:10],  # Top 10 per il report
        }

        if not relevant_datasets:
            print("❌ Nessun dataset rilevante trovato!")
            return test_report

        # Test 3: Test dataset specifici
        print("\n3️⃣ TEST DATASET SPECIFICI")
        dataset_test_results = []

        # Testa i primi 3 dataset più rilevanti
        for i, dataset in enumerate(relevant_datasets[:3]):
            print(f"\nTest {i + 1}/3: {dataset['name']}")
            result = self.test_specific_dataset(dataset["id"], dataset["name"])
            dataset_test_results.append(result)

            # Se il test è riuscito, crea visualizzazioni
            if result.get("data_test", {}).get("success", False):
                self.create_data_preview_visualization(dataset["id"])

            time.sleep(3)  # Rate limiting più conservativo

        test_report["tests"]["specific_datasets"] = dataset_test_results

        # Test 4: Dataset popolari
        print("\n4️⃣ TEST DATASET POPOLARI")
        popular_success = self.test_popular_datasets()
        test_report["tests"]["popular_datasets"] = {
            "successful_tests": popular_success,
            "total_tests": 5,
        }

        # Test 5: Validazione qualità
        print("\n5️⃣ VALIDAZIONE QUALITÀ DATI")
        quality_reports = []

        for dataset in relevant_datasets[:2]:  # Primi 2 dataset
            if any(
                r["dataset_id"] == dataset["id"]
                and r.get("data_test", {}).get("success", False)
                for r in dataset_test_results
            ):
                quality_report = self.validate_data_quality(dataset["id"])
                if quality_report:
                    quality_reports.append(quality_report)

        test_report["tests"]["data_quality"] = quality_reports

        # Genera report finale
        print("\n6️⃣ GENERAZIONE REPORT")
        self.generate_final_report(test_report)

        print("\n" + "=" * 50)
        print("✅ TEST COMPLETO TERMINATO!")
        print(
            f"📊 Endpoint funzionanti: {successful_endpoints}/{len(connectivity_results)}"
        )
        print(f"📈 Dataset rilevanti trovati: {len(relevant_datasets)}")
        print(
            f"🔬 Dataset testati con successo: {sum(1 for r in dataset_test_results if r.get('data_test', {}).get('success', False))}"
        )
        print(f"📋 Report qualità generati: {len(quality_reports)}")

        return test_report

    def generate_final_report(self, test_report):
        """Genera report finale dei test"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Report JSON completo in modo sicuro
        json_filename = f"istat_api_test_report_{timestamp}.json"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(json_filename):
            json_filename = self.path_validator.sanitize_filename(json_filename)

        safe_file = self.path_validator.safe_open(json_filename, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                json.dump(test_report, f, ensure_ascii=False, indent=2)
        else:
            print(f"❌ Impossibile salvare report JSON: {json_filename}")
            return

        # Report HTML user-friendly in modo sicuro
        html_filename = f"istat_api_test_report_{timestamp}.html"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(html_filename):
            html_filename = self.path_validator.sanitize_filename(html_filename)

        html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Test API ISTAT</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #0066cc; padding-bottom: 20px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center; }}
        .dataset-card {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f8f9fa; }}
        .status-ok {{ background-color: #d4edda; }}
        .status-error {{ background-color: #f8d7da; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🇮🇹 Report Test API ISTAT</h1>
            <p>Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}</p>
        </div>

        <div class="section">
            <h2>📊 Panoramica Risultati</h2>
            <div class="metric">
                <h3>{len(test_report.get('tests', {}).get('connectivity', []))}</h3>
                <p>Endpoint Testati</p>
            </div>
            <div class="metric">
                <h3>{test_report.get('tests', {}).get('dataset_discovery', {}).get('total_found', 0)}</h3>
                <p>Dataset Rilevanti</p>
            </div>
            <div class="metric">
                <h3>{len(test_report.get('tests', {}).get('specific_datasets', []))}</h3>
                <p>Dataset Testati</p>
            </div>
            <div class="metric">
                <h3>{len(test_report.get('tests', {}).get('data_quality', []))}</h3>
                <p>Report Qualità</p>
            </div>
        </div>

        <div class="section">
            <h2>🔗 Test Connettività</h2>
            <table>
                <tr><th>Endpoint</th><th>Status</th><th>Tempo Risposta</th><th>Dimensione Dati</th></tr>
        """

        for conn in test_report.get("tests", {}).get("connectivity", []):
            status_class = "status-ok" if conn.get("success") else "status-error"
            status_text = (
                "✅ OK"
                if conn.get("success")
                else f"❌ Error {conn.get('status_code', 'N/A')}"
            )
            response_time = (
                f"{conn.get('response_time', 0)}s" if conn.get("success") else "N/A"
            )
            data_size = (
                f"{conn.get('data_length', 0)} bytes" if conn.get("success") else "N/A"
            )

            html_content += f"""
                <tr class="{status_class}">
                    <td>{conn.get('endpoint', 'N/A')}</td>
                    <td>{status_text}</td>
                    <td>{response_time}</td>
                    <td>{data_size}</td>
                </tr>
            """

        html_content += """
            </table>
        </div>

        <div class="section">
            <h2>📈 Dataset Più Rilevanti</h2>
        """

        for dataset in (
            test_report.get("tests", {})
            .get("dataset_discovery", {})
            .get("datasets", [])[:5]
        ):
            html_content += f"""
            <div class="dataset-card">
                <h4>{dataset.get('name', 'N/A')}</h4>
                <p><strong>ID:</strong> {dataset.get('id', 'N/A')}</p>
                <p><strong>Ultimo Aggiornamento:</strong> {dataset.get('last_update', 'N/A')}</p>
                <p><strong>Punteggio Rilevanza:</strong> {dataset.get('relevance_score', 0)}/10</p>
            </div>
            """

        html_content += f"""
        </div>

        <div class="section">
            <h2>🎯 Raccomandazioni per Tableau</h2>
            <ul>
                <li><strong>Connettori Consigliati:</strong> BigQuery per storage, Google Sheets per prototipazione rapida</li>
                <li><strong>Refresh Schedule:</strong> Mensile per dati demografici, trimestrale per dati economici</li>
                <li><strong>Qualità Dati:</strong> Implementare validazione automatica per campi critici</li>
                <li><strong>Governance:</strong> Tracciare lineage dati da ISTAT a dashboard finali</li>
                <li><strong>Performance:</strong> Utilizzare extract per dataset >100MB</li>
            </ul>
        </div>

        <div class="section">
            <h2>📋 File Generati</h2>
            <ul>
                <li>📊 Report JSON completo: {json_filename}</li>
                <li>📈 Visualizzazioni dati: preview_*.png</li>
                <li>📝 Summary statistici: summary_*.txt</li>
                <li>🔍 Report qualità: quality_report_*.json</li>
            </ul>
        </div>

        <div class="section">
            <h2>🚀 Prossimi Passi</h2>
            <ol>
                <li>Configurare connettori BigQuery e Google Sheets in Tableau</li>
                <li>Implementare flussi automatici per i dataset testati con successo</li>
                <li>Creare dashboard pilota con i dati più rilevanti</li>
                <li>Impostare monitoring qualità dati e refresh automatici</li>
                <li>Estendere a ulteriori dataset ISTAT in base alle necessità</li>
            </ol>
        </div>
    </div>
</body>
</html>
        """

        safe_file = self.path_validator.safe_open(html_filename, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                f.write(html_content)
            print(f"✅ Report JSON: {json_filename}")
            print(f"✅ Report HTML: {html_filename}")
        else:
            print(f"❌ Impossibile salvare report HTML: {html_filename}")


def main():
    """Funzione principale per test API ISTAT"""
    print("🇮🇹 ISTAT API TESTER & VALIDATOR")
    print("Sviluppato per integrazione Tableau")
    print("=" * 50)
    print(
        "⚠️  DEPRECATION WARNING: This exploration tool is being replaced by ProductionIstatClient"
    )
    print(
        "🔄 For production use, please use: src.api.production_istat_client.ProductionIstatClient"
    )
    print("📚 This tool remains available for manual testing and exploration only")
    print("=" * 50)

    tester = IstatAPITester()

    # Esegui test completo
    final_report = tester.run_comprehensive_test()

    print("\n📁 TUTTI I FILE SONO STATI GENERATI NELLA DIRECTORY CORRENTE")
    print("🎯 Usa i risultati per configurare i connettori Tableau!")


if __name__ == "__main__":
    main()
