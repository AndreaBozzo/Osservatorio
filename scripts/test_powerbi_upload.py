"""
Script per testare l'upload dei dataset ISTAT in PowerBI.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.api.powerbi_api import PowerBIAPIClient
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PowerBIUploadTester:
    """Tester per upload dataset PowerBI."""

    def __init__(self):
        """Inizializza il tester."""
        self.client = PowerBIAPIClient()
        self.powerbi_dir = Config.PROCESSED_DATA_DIR / "powerbi"
        self.test_results = []

    def find_converted_datasets(self) -> List[Dict]:
        """Trova i dataset convertiti disponibili."""
        logger.info("Ricerca dataset convertiti...")

        # Cerca file di summary
        summary_files = list(self.powerbi_dir.glob("conversion_summary_*.json"))

        if not summary_files:
            logger.warning("Nessun file di summary trovato")
            return []

        # Usa il più recente
        latest_summary = max(summary_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Caricamento summary: {latest_summary}")

        with open(latest_summary, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        return summary_data.get("successful_datasets", [])

    def create_dataset_definition(self, dataset_info: Dict) -> Dict:
        """Crea definizione dataset per PowerBI."""
        dataset_name = f"ISTAT_{dataset_info['category']}_{dataset_info['dataflow_id']}"

        # Leggi un file per determinare le colonne
        parquet_file = dataset_info["output_files"].get("parquet")
        if parquet_file and Path(parquet_file).exists():
            df = pd.read_parquet(parquet_file)
            columns = df.columns.tolist()
        else:
            columns = dataset_info["columns"]

        # Definizione tabella per PowerBI
        table_definition = {"name": "IstatData", "columns": []}

        # Mapping tipi colonne
        for col in columns:
            if col in ["Time", "LoadTimestamp"]:
                col_type = "DateTime"
            elif col in ["Value"]:
                col_type = "Double"
            else:
                col_type = "String"

            table_definition["columns"].append({"name": col, "dataType": col_type})

        # Definizione dataset completa
        dataset_definition = {"name": dataset_name, "tables": [table_definition]}

        return dataset_definition

    def upload_dataset(self, dataset_info: Dict) -> Dict:
        """Carica un dataset in PowerBI."""
        logger.info(f"Upload dataset: {dataset_info['name']}")

        result = {
            "dataset_info": dataset_info,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "dataset_id": None,
            "rows_uploaded": 0,
        }

        try:
            # 1. Crea definizione dataset
            dataset_definition = self.create_dataset_definition(dataset_info)

            # 2. Crea dataset in PowerBI
            logger.info(f"Creazione dataset: {dataset_definition['name']}")
            created_dataset = self.client.create_dataset(dataset_definition)

            if not created_dataset:
                result["error"] = "Errore creazione dataset"
                return result

            result["dataset_id"] = created_dataset["id"]
            logger.info(f"Dataset creato con ID: {created_dataset['id']}")

            # 3. Carica dati dal file Parquet
            parquet_file = dataset_info["output_files"].get("parquet")
            if parquet_file and Path(parquet_file).exists():
                df = pd.read_parquet(parquet_file)

                # Converti DataFrame in dizionari
                data_rows = df.to_dict("records")

                # Converti datetime in string per JSON
                for row in data_rows:
                    for key, value in row.items():
                        if pd.isna(value):
                            row[key] = None
                        elif isinstance(value, pd.Timestamp):
                            row[key] = value.isoformat()

                # 4. Carica dati in PowerBI
                logger.info(f"Caricamento {len(data_rows)} righe...")
                upload_success = self.client.push_data_to_dataset(
                    created_dataset["id"], "IstatData", data_rows
                )

                if upload_success:
                    result["success"] = True
                    result["rows_uploaded"] = len(data_rows)
                    logger.info(f"Upload completato: {len(data_rows)} righe")
                else:
                    result["error"] = "Errore caricamento dati"
            else:
                result["error"] = f"File Parquet non trovato: {parquet_file}"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Errore upload dataset: {e}")

        return result

    def test_dataset_upload(self, limit: int = 3) -> List[Dict]:
        """Testa l'upload di alcuni dataset."""
        logger.info(f"Test upload dataset (limite: {limit})")

        # Trova dataset convertiti
        converted_datasets = self.find_converted_datasets()

        if not converted_datasets:
            logger.error("Nessun dataset convertito trovato")
            return []

        # Seleziona dataset per test (1 per categoria)
        test_datasets = []
        categories_tested = set()

        for dataset in converted_datasets:
            if len(test_datasets) >= limit:
                break

            category = dataset["category"]
            if category not in categories_tested:
                test_datasets.append(dataset)
                categories_tested.add(category)

        logger.info(f"Test di {len(test_datasets)} dataset")

        # Esegui upload per ogni dataset
        results = []
        for dataset in test_datasets:
            result = self.upload_dataset(dataset)
            results.append(result)
            self.test_results.append(result)

        return results

    def generate_test_report(self, results: List[Dict]) -> str:
        """Genera report dei test."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_uploads": len(successful),
            "failed_uploads": len(failed),
            "success_rate": (
                f"{(len(successful)/len(results)*100):.1f}%" if results else "0%"
            ),
            "results": results,
        }

        # Salva report JSON
        report_file = f"powerbi_upload_test_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Genera report testuale
        text_report = f"""POWERBI UPLOAD TEST REPORT
=========================

Test eseguito: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RISULTATI:
- Test totali: {len(results)}
- Upload riusciti: {len(successful)}
- Upload falliti: {len(failed)}
- Tasso di successo: {report['success_rate']}

DETTAGLI UPLOAD:
"""

        for result in results:
            status = "✅ SUCCESSO" if result["success"] else "❌ FALLITO"
            dataset_name = result["dataset_info"]["name"]
            rows = result["rows_uploaded"]

            text_report += f"""
{status} - {dataset_name}
  Dataset ID: {result['dataset_id'] or 'N/A'}
  Righe caricate: {rows}
  Errore: {result['error'] or 'Nessuno'}
"""

        if failed:
            text_report += "\nERRORI DETTAGLIATI:\n"
            for result in failed:
                text_report += (
                    f"- {result['dataset_info']['name']}: {result['error']}\n"
                )

        text_report += f"\nReport completo salvato in: {report_file}\n"

        # Salva report testuale
        text_file = f"powerbi_upload_test_{timestamp}.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text_report)

        logger.info(f"Report generato: {report_file} e {text_file}")

        return text_report

    def cleanup_test_datasets(self):
        """Pulizia dataset di test (opzionale)."""
        logger.info("Pulizia dataset di test...")

        try:
            # Recupera lista dataset nel workspace
            datasets = self.client.get_datasets()

            # Filtra dataset di test ISTAT
            test_datasets = [d for d in datasets if d["name"].startswith("ISTAT_")]

            if not test_datasets:
                logger.info("Nessun dataset di test da rimuovere")
                return

            print(f"\nTrovati {len(test_datasets)} dataset di test:")
            for i, dataset in enumerate(test_datasets, 1):
                print(f"  {i}. {dataset['name']} (ID: {dataset['id']})")

            response = input(
                f"\nRimuovere tutti i {len(test_datasets)} dataset di test? (y/n): "
            )
            if response.lower() != "y":
                logger.info("Pulizia annullata")
                return

            # Rimuovi dataset (non implementato in API base)
            logger.warning(
                "Rimozione dataset non implementata - rimuovi manualmente da PowerBI Service"
            )

        except Exception as e:
            logger.error(f"Errore durante pulizia: {e}")


def main():
    """Funzione principale del tester."""
    print("🔄 POWERBI UPLOAD TESTER")
    print("=" * 30)

    # Verifica configurazione
    if not all(
        [
            Config.POWERBI_CLIENT_ID,
            Config.POWERBI_CLIENT_SECRET,
            Config.POWERBI_TENANT_ID,
        ]
    ):
        print("❌ Configurazione PowerBI incompleta!")
        print("Esegui prima: python scripts/setup_powerbi_azure.py")
        return

    tester = PowerBIUploadTester()

    try:
        # Test connessione
        print("\n1. Test connessione PowerBI...")
        connection_result = tester.client.test_connection()

        if not connection_result["authentication"]:
            print("❌ Autenticazione fallita!")
            return

        print("✅ Connessione riuscita")

        # Test upload dataset
        print("\n2. Test upload dataset...")
        upload_results = tester.test_dataset_upload(limit=3)

        if not upload_results:
            print("❌ Nessun dataset disponibile per il test")
            return

        # Genera report
        print("\n3. Generazione report...")
        report = tester.generate_test_report(upload_results)
        print(report)

        # Opzione pulizia
        print("\n4. Pulizia dataset di test...")
        cleanup = input("Eseguire pulizia dataset di test? (y/n): ")
        if cleanup.lower() == "y":
            tester.cleanup_test_datasets()

        print("\n✅ Test completato!")

    except Exception as e:
        print(f"❌ Errore durante test: {e}")
        logger.error(f"Errore test upload: {e}")


if __name__ == "__main__":
    main()
