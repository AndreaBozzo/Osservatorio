import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests

from ..utils.secure_path import create_secure_validator


class IstatDataflowAnalyzer:
    def __init__(self):
        """Analizza i dataflow ISTAT per trovare quelli più utili"""
        self.base_url = "https://sdmx.istat.it/SDMXWS/rest/"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/xml",
            }
        )

        # Initialize secure path validator for current directory
        self.path_validator = create_secure_validator(os.getcwd())

        # Keywords per categoria con priorità
        self.category_keywords = {
            "popolazione": {
                "keywords": [
                    "popolazione",
                    "popul",
                    "residente",
                    "demografic",
                    "demo",
                    "nascite",
                    "morti",
                    "stranieri",
                ],
                "priority": 10,
            },
            "economia": {
                "keywords": [
                    "pil",
                    "gdp",
                    "economia",
                    "economic",
                    "inflazione",
                    "prezzi",
                    "price",
                    "reddito",
                    "income",
                ],
                "priority": 9,
            },
            "lavoro": {
                "keywords": [
                    "lavoro",
                    "occupazione",
                    "disoccupazione",
                    "employment",
                    "unemploy",
                    "forze_lavoro",
                ],
                "priority": 8,
            },
            "territorio": {
                "keywords": [
                    "regione",
                    "provincia",
                    "comune",
                    "territorial",
                    "geographic",
                ],
                "priority": 7,
            },
            "istruzione": {
                "keywords": [
                    "istruzione",
                    "scuola",
                    "università",
                    "education",
                    "student",
                ],
                "priority": 6,
            },
            "salute": {
                "keywords": ["sanita", "salute", "ospedale", "health", "medical"],
                "priority": 5,
            },
        }

    def parse_dataflow_xml(self, xml_file_path="dataflow_response.xml"):
        """Analizza il file XML dei dataflow scaricato"""
        print(f"📊 Analisi file XML dataflow: {xml_file_path}")

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Namespace SDMX
            namespaces = {
                "str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
                "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
            }

            dataflows = []

            # Prova con namespace
            for dataflow in root.findall(".//str:Dataflow", namespaces):
                df_info = self._extract_dataflow_info(dataflow, namespaces)
                if df_info:
                    dataflows.append(df_info)

            # Se non trova nulla, prova senza namespace
            if not dataflows:
                for dataflow in root.findall(".//Dataflow"):
                    df_info = self._extract_dataflow_info(dataflow, {})
                    if df_info:
                        dataflows.append(df_info)

            print(f"✅ Estratti {len(dataflows)} dataflow dal XML")

            # Categorizza e prioritizza
            categorized_dataflows = self._categorize_dataflows(dataflows)

            return categorized_dataflows

        except Exception as e:
            print(f"❌ Errore parsing XML: {e}")
            return {}

    def _extract_dataflow_info(self, dataflow_elem, namespaces):
        """Estrae informazioni da un elemento dataflow"""
        try:
            df_id = dataflow_elem.get("id", "")

            # Cerca nome in diverse lingue
            name_it = None
            name_en = None

            if namespaces:
                for name_elem in dataflow_elem.findall(".//com:Name", namespaces):
                    lang = name_elem.get(
                        "{http://www.w3.org/XML/1998/namespace}lang", ""
                    )
                    if lang == "it":
                        name_it = name_elem.text
                    elif lang == "en":
                        name_en = name_elem.text
                    elif not name_it and not lang:  # Fallback
                        name_it = name_elem.text
            else:
                for name_elem in dataflow_elem.findall(".//Name"):
                    lang = name_elem.get("lang", "")
                    if lang == "it":
                        name_it = name_elem.text
                    elif lang == "en":
                        name_en = name_elem.text
                    elif not name_it:  # Fallback
                        name_it = name_elem.text

            # Usa nome italiano o inglese come fallback
            display_name = name_it or name_en or df_id

            # Estrai descrizione se disponibile
            description = ""
            if namespaces:
                desc_elem = dataflow_elem.find(".//com:Description", namespaces)
                if desc_elem is not None:
                    description = desc_elem.text or ""
            else:
                desc_elem = dataflow_elem.find(".//Description")
                if desc_elem is not None:
                    description = desc_elem.text or ""

            return {
                "id": df_id,
                "name_it": name_it or "",
                "name_en": name_en or "",
                "display_name": display_name,
                "description": description,
            }

        except Exception as e:
            print(f"⚠️  Errore estrazione dataflow: {e}")
            return None

    def _categorize_dataflows(self, dataflows):
        """Categorizza i dataflow per rilevanza"""
        categorized = {category: [] for category in self.category_keywords.keys()}
        categorized["altri"] = []

        for df in dataflows:
            # Testo da analizzare (nome + descrizione)
            text_to_analyze = (df["display_name"] + " " + df["description"]).lower()

            best_category = None
            best_score = 0

            # Trova la categoria migliore
            for category, config in self.category_keywords.items():
                score = 0
                for keyword in config["keywords"]:
                    if keyword in text_to_analyze:
                        score += config["priority"]

                if score > best_score:
                    best_score = score
                    best_category = category

            # Aggiungi informazioni di scoring
            df["category"] = best_category or "altri"
            df["relevance_score"] = best_score

            # Aggiungi alla categoria appropriata
            if best_category:
                categorized[best_category].append(df)
            else:
                categorized["altri"].append(df)

        # Ordina ogni categoria per score
        for category in categorized:
            categorized[category].sort(key=lambda x: x["relevance_score"], reverse=True)

        return categorized

    def find_top_dataflows_by_category(self, categorized_dataflows, top_n=5):
        """Trova i top dataflow per ogni categoria"""
        top_dataflows = {}

        print("\n🎯 TOP DATAFLOW PER CATEGORIA:")
        print("=" * 50)

        for category, dataflows in categorized_dataflows.items():
            if dataflows:  # Se ci sono dataflow in questa categoria
                top_dataflows[category] = dataflows[:top_n]

                print(f"\n📊 {category.upper()} (Top {min(top_n, len(dataflows))}):")
                for i, df in enumerate(dataflows[:top_n], 1):
                    print(f"  {i}. {df['display_name']}")
                    print(f"     ID: {df['id']} | Score: {df['relevance_score']}")
                    if df["description"]:
                        print(f"     Desc: {df['description'][:100]}...")

        return top_dataflows

    def test_priority_dataflows(self, top_dataflows, max_tests=15):
        """Testa i dataflow prioritari per verificare l'accesso ai dati"""
        print(f"\n🔬 TEST DATAFLOW PRIORITARI (max {max_tests}):")
        print("=" * 50)

        tested_dataflows = []
        test_count = 0

        # Testa in ordine di priorità per categoria
        priority_order = [
            "popolazione",
            "economia",
            "lavoro",
            "territorio",
            "istruzione",
            "salute",
        ]

        for category in priority_order:
            if test_count >= max_tests:
                break

            if category in top_dataflows and top_dataflows[category]:
                print(f"\n📈 Testando categoria: {category.upper()}")

                for df in top_dataflows[category]:
                    if test_count >= max_tests:
                        break

                    test_count += 1
                    result = self._test_single_dataflow(df)
                    tested_dataflows.append(result)

                    # Rate limiting
                    time.sleep(1)

        return tested_dataflows

    def _test_single_dataflow(self, dataflow):
        """Testa un singolo dataflow"""
        df_id = dataflow["id"]
        df_name = dataflow["display_name"]

        print(f"\n  🔍 Test: {df_name} ({df_id})")

        result = {
            "id": df_id,
            "name": df_name,
            "category": dataflow["category"],
            "relevance_score": dataflow["relevance_score"],
            "tests": {},
        }

        # Test 1: Accesso dati
        try:
            data_url = f"{self.base_url}data/{df_id}"
            data_response = self.session.get(data_url, timeout=30)

            result["tests"]["data_access"] = {
                "success": data_response.status_code == 200,
                "status_code": data_response.status_code,
                "size_bytes": (
                    len(data_response.content)
                    if data_response.status_code == 200
                    else 0
                ),
            }

            if data_response.status_code == 200:
                print(f"    ✅ Dati accessibili ({len(data_response.content)} bytes)")

                # Salva sample per analisi successiva in modo sicuro
                sample_filename = f"sample_{df_id}.xml"

                # Valida e sanitizza il nome del file
                if not self.path_validator.validate_filename(sample_filename):
                    sample_filename = self.path_validator.sanitize_filename(
                        sample_filename
                    )

                safe_file = self.path_validator.safe_open(
                    sample_filename, "w", encoding="utf-8"
                )
                if safe_file:
                    with safe_file as f:
                        f.write(data_response.text)
                    result["tests"]["sample_file"] = sample_filename
                else:
                    result["tests"]["sample_file"] = None
                    print(f"    ⚠️  Impossibile salvare sample: {sample_filename}")

                # Prova parsing rapido
                try:
                    root = ET.fromstring(data_response.content)
                    obs_count = len(root.findall('.//*[local-name()="Obs"]'))
                    if obs_count == 0:
                        obs_count = len(
                            root.findall('.//*[local-name()="Observation"]')
                        )

                    result["tests"]["observations_count"] = obs_count
                    print(f"    📊 Osservazioni: {obs_count}")
                except:
                    result["tests"]["parse_error"] = True
                    print(f"    ⚠️  Errore parsing XML")
            else:
                print(
                    f"    ❌ Dati non accessibili (Status: {data_response.status_code})"
                )

        except Exception as e:
            result["tests"]["error"] = str(e)
            print(f"    ❌ Errore: {e}")

        return result

    def create_tableau_ready_dataset_list(self, tested_dataflows):
        """Crea lista dataset pronti per Tableau"""
        print(f"\n📋 CREAZIONE LISTA DATASET TABLEAU-READY:")
        print("=" * 50)

        tableau_ready = []

        for df in tested_dataflows:
            if df["tests"].get("data_access", {}).get("success", False):
                tableau_entry = {
                    "dataflow_id": df["id"],
                    "name": df["name"],
                    "category": df["category"],
                    "relevance_score": df["relevance_score"],
                    "data_size_mb": df["tests"]["data_access"]["size_bytes"]
                    / (1024 * 1024),
                    "observations_count": df["tests"].get("observations_count", 0),
                    "sdmx_data_url": f"{self.base_url}data/{df['id']}",
                    "sample_file": df["tests"].get("sample_file", ""),
                    "tableau_connection_type": self._suggest_tableau_connection(df),
                    "refresh_frequency": self._suggest_refresh_frequency(
                        df["category"]
                    ),
                    "priority": self._calculate_priority(df),
                }

                tableau_ready.append(tableau_entry)

        # Ordina per priorità
        tableau_ready.sort(key=lambda x: x["priority"], reverse=True)

        print(f"✅ {len(tableau_ready)} dataset pronti per Tableau:")
        for i, ds in enumerate(tableau_ready[:10], 1):
            size_mb = ds["data_size_mb"]
            obs_count = ds["observations_count"]
            print(f"  {i}. {ds['name']}")
            print(f"     Categoria: {ds['category']} | Priorità: {ds['priority']}")
            print(f"     Dimensioni: {size_mb:.2f}MB | Osservazioni: {obs_count}")

        return tableau_ready

    def _suggest_tableau_connection(self, dataflow):
        """Suggerisce tipo connessione Tableau"""
        size_mb = dataflow["tests"]["data_access"]["size_bytes"] / (1024 * 1024)

        if size_mb > 50:
            return "bigquery_extract"  # Dataset grandi
        elif size_mb > 5:
            return "google_sheets_import"  # Dataset medi
        else:
            return "direct_connection"  # Dataset piccoli

    def _suggest_refresh_frequency(self, category):
        """Suggerisce frequenza refresh per categoria"""
        frequency_map = {
            "popolazione": "monthly",
            "economia": "quarterly",
            "lavoro": "monthly",
            "territorio": "yearly",
            "istruzione": "yearly",
            "salute": "quarterly",
        }
        return frequency_map.get(category, "quarterly")

    def _calculate_priority(self, dataflow):
        """Calcola priorità per Tableau"""
        base_score = dataflow["relevance_score"]

        # Gestione sicura per tests che potrebbe non esistere
        tests_data = dataflow.get("tests", {})
        data_access = tests_data.get("data_access", {})

        size_bonus = min(5, data_access.get("size_bytes", 0) / (1024 * 1024) / 10)
        obs_bonus = min(5, tests_data.get("observations_count", 0) / 1000)

        return base_score + size_bonus + obs_bonus

    def generate_summary_report(self, categorized_data):
        """Generate a summary report of categorized data"""
        total_dataflows = sum(len(datasets) for datasets in categorized_data.values())
        report = f"""
📊 ISTAT Data Analysis Summary
{'='*50}
Total dataflows analyzed: {total_dataflows}

Category breakdown:
"""
        for category, datasets in categorized_data.items():
            if datasets:
                report += f"• {category.capitalize()}: {len(datasets)} datasets\n"

        report += "\nTop datasets by category:\n"
        for category, datasets in categorized_data.items():
            if datasets:
                report += f"\n{category.upper()}:\n"
                for dataset in datasets[:3]:  # Show top 3
                    report += f"  - {dataset.get('display_name', dataset.get('name', 'Unknown'))}\n"

        return report

    def generate_tableau_implementation_guide(self, tableau_ready_datasets):
        """Genera guida implementazione per Tableau"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON per import automatico
        datasets_config = {
            "timestamp": datetime.now().isoformat(),
            "total_datasets": len(tableau_ready_datasets),
            "categories": {},
            "datasets": tableau_ready_datasets,
        }

        # Raggruppa per categoria
        for ds in tableau_ready_datasets:
            category = ds["category"]
            if category not in datasets_config["categories"]:
                datasets_config["categories"][category] = []
            datasets_config["categories"][category].append(ds["dataflow_id"])

        # Salva configurazione in modo sicuro
        config_filename = f"tableau_istat_datasets_{timestamp}.json"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(config_filename):
            config_filename = self.path_validator.sanitize_filename(config_filename)

        safe_file = self.path_validator.safe_open(
            config_filename, "w", encoding="utf-8"
        )
        if safe_file:
            with safe_file as f:
                json.dump(datasets_config, f, ensure_ascii=False, indent=2)
        else:
            print(f"❌ Impossibile salvare configurazione: {config_filename}")
            return {"error": "Failed to save configuration"}

        # Genera script PowerShell per download in modo sicuro
        ps_script = self._generate_powershell_script(tableau_ready_datasets)
        ps_filename = f"download_istat_data_{timestamp}.ps1"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(ps_filename):
            ps_filename = self.path_validator.sanitize_filename(ps_filename)

        safe_file = self.path_validator.safe_open(ps_filename, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                f.write(ps_script)
        else:
            print(f"❌ Impossibile salvare script PowerShell: {ps_filename}")
            ps_filename = None

        # Genera Tableau Prep flow template in modo sicuro
        prep_flow = self._generate_prep_flow_template(tableau_ready_datasets)
        flow_filename = f"istat_prep_flow_{timestamp}.json"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(flow_filename):
            flow_filename = self.path_validator.sanitize_filename(flow_filename)

        safe_file = self.path_validator.safe_open(flow_filename, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                json.dump(prep_flow, f, ensure_ascii=False, indent=2)
        else:
            print(f"❌ Impossibile salvare flow template: {flow_filename}")
            flow_filename = None

        print(f"\n📁 FILE GENERATI:")
        if config_filename:
            print(f"  • {config_filename} - Configurazione dataset")
        if ps_filename:
            print(f"  • {ps_filename} - Script download PowerShell")
        if flow_filename:
            print(f"  • {flow_filename} - Template Tableau Prep")

        return {
            "config_file": config_filename if config_filename else None,
            "powershell_script": ps_filename if ps_filename else None,
            "prep_flow": flow_filename if flow_filename else None,
        }

    def _generate_powershell_script(self, datasets):
        """Genera script PowerShell per download automatico"""
        script = """# Script PowerShell per download dataset ISTAT
# Generato automaticamente

$baseUrl = "https://sdmx.istat.it/SDMXWS/rest/data/"
$outputDir = "istat_data"

# Crea directory output
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

Write-Host "🇮🇹 Download dataset ISTAT in corso..." -ForegroundColor Green

"""

        for i, ds in enumerate(datasets[:10], 1):  # Top 10
            script += f"""
# Dataset {i}: {ds['name']}
Write-Host "📊 Downloading: {ds['name']}" -ForegroundColor Yellow
$url{i} = "$baseUrl{ds['dataflow_id']}"
$output{i} = "$outputDir\\{ds['dataflow_id']}.xml"
try {{
    Invoke-WebRequest -Uri $url{i} -OutFile $output{i} -TimeoutSec 60
    Write-Host "✅ Salvato: $output{i}" -ForegroundColor Green
}} catch {{
    Write-Host "❌ Errore download {ds['dataflow_id']}: $_" -ForegroundColor Red
}}
Start-Sleep -Seconds 2
"""

        script += """
Write-Host "🎉 Download completato!" -ForegroundColor Green
Write-Host "📁 File salvati in: $outputDir" -ForegroundColor Cyan
"""

        return script

    def _generate_prep_flow_template(self, datasets):
        """Genera template Tableau Prep flow"""
        return {
            "name": "ISTAT_Data_Integration_Flow",
            "description": "Flusso integrazione dati ISTAT automatizzato",
            "steps": [
                {
                    "type": "input",
                    "name": "Load_ISTAT_XMLs",
                    "sources": [ds["dataflow_id"] for ds in datasets[:5]],
                },
                {"type": "union", "name": "Combine_All_ISTAT", "union_type": "manual"},
                {
                    "type": "clean",
                    "name": "Clean_ISTAT_Data",
                    "operations": [
                        "remove_null_rows",
                        "standardize_date_formats",
                        "normalize_region_names",
                    ],
                },
                {
                    "type": "aggregate",
                    "name": "Aggregate_By_Region_Year",
                    "group_by": ["region", "year"],
                    "measures": ["population", "gdp", "employment"],
                },
                {
                    "type": "output",
                    "name": "ISTAT_Integrated_Extract",
                    "format": "hyper",
                    "schedule": "monthly",
                },
            ],
        }


def main():
    """Funzione principale per analisi completa"""
    print("🇮🇹 ISTAT DATAFLOW ANALYZER")
    print("Analisi completa dei 509+ dataflow disponibili")
    print("=" * 60)

    analyzer = IstatDataflowAnalyzer()

    # 1. Analizza XML dataflow
    categorized = analyzer.parse_dataflow_xml()

    if not categorized:
        print(
            "❌ Impossibile analizzare dataflow. Verifica che dataflow_response.xml esista."
        )
        return

    # 2. Trova top dataflow per categoria
    top_dataflows = analyzer.find_top_dataflows_by_category(categorized, top_n=3)

    # 3. Testa dataflow prioritari
    tested = analyzer.test_priority_dataflows(top_dataflows, max_tests=15)

    # 4. Crea lista Tableau-ready
    tableau_ready = analyzer.create_tableau_ready_dataset_list(tested)

    # 5. Genera guida implementazione
    files = analyzer.generate_tableau_implementation_guide(tableau_ready)

    print("\n" + "=" * 60)
    print("✅ ANALISI COMPLETATA!")
    print(f"📊 Dataset analizzati e pronti per Tableau: {len(tableau_ready)}")
    print(f"📁 File generati: {len(files)}")
    print("\n🚀 PROSSIMI PASSI:")
    print("  1. Esegui lo script PowerShell per download dati")
    print("  2. Importa la configurazione JSON in Tableau")
    print("  3. Usa il template Prep flow per elaborazione automatica")


if __name__ == "__main__":
    main()
