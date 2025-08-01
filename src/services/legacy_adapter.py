"""
Legacy adapter for backward compatibility during migration.

This module provides an adapter that maintains the same interface as the
legacy IstatDataflowAnalyzer while using the new modern service internally.
This allows for gradual migration without breaking existing code.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .dataflow_analysis_service import DataflowAnalysisService
from .models import AnalysisFilters, DataflowCategory
from .service_factory import get_dataflow_analysis_service


class LegacyDataflowAnalyzerAdapter:
    """
    Adapter class that maintains the legacy IstatDataflowAnalyzer interface
    while using the modern DataflowAnalysisService internally.

    This allows existing code to continue working during the migration period.
    """

    def __init__(self):
        """Initialize the adapter with modern service."""
        import warnings

        # Issue #84 - CRITICAL DEPRECATION WARNING
        warnings.warn(
            "\n"
            + "=" * 80
            + "\n"
            + "⚠️  CRITICAL DEPRECATION WARNING - Issue #84\n"
            + "LegacyDataflowAnalyzerAdapter is DEPRECATED for v1.0.0\n"
            + "\n"
            + "🔄 MIGRATION REQUIRED:\n"
            + "  - Replace with DataflowAnalysisService directly\n"
            + "  - Use get_dataflow_analysis_service() factory\n"
            + "  - Update imports and method calls\n"
            + "\n"
            + "This adapter will be REMOVED in v1.0.0 for architecture cleanliness.\n"
            + "=" * 80
            + "\n",
            DeprecationWarning,
            stacklevel=2,
        )

        self.logger = get_logger(__name__)
        self._service: Optional[DataflowAnalysisService] = None
        self._analysis_result = None

        # Legacy attributes for compatibility
        self.base_url = "https://sdmx.istat.it/SDMXWS/rest/"

        self.logger.warning(
            "🚨 DEPRECATED: LegacyDataflowAnalyzerAdapter used. Migrate to DataflowAnalysisService."
        )

    @property
    def service(self) -> DataflowAnalysisService:
        """Lazy initialization of the modern service."""
        if self._service is None:
            self._service = get_dataflow_analysis_service()
        return self._service

    def parse_dataflow_xml(self, xml_file_path: str = "dataflow_response.xml") -> Dict:
        """
        Legacy method: Parse dataflow XML file.

        Maintains the same interface as the original method but uses
        the modern service internally.
        """
        print(f"📊 Analisi file XML dataflow: {xml_file_path}")

        try:
            # Read XML file
            xml_path = Path(xml_file_path)
            if not xml_path.exists():
                print(f"❌ File non trovato: {xml_file_path}")
                return {}

            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            # Use modern service to analyze
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                filters = AnalysisFilters(
                    include_tests=False
                )  # Don't run tests in parse phase
                result = loop.run_until_complete(
                    self.service.analyze_dataflows_from_xml(xml_content, filters)
                )
                self._analysis_result = result

                # Convert to legacy format
                legacy_format = {}
                for category, dataflows in result.categorized_dataflows.items():
                    legacy_format[category.value] = []
                    for df in dataflows:
                        legacy_format[category.value].append(
                            {
                                "id": df.id,
                                "name_it": df.name_it,
                                "name_en": df.name_en,
                                "display_name": df.display_name,
                                "description": df.description,
                                "category": df.category.value,
                                "relevance_score": df.relevance_score,
                            }
                        )

                print(f"✅ Estratti {result.total_analyzed} dataflow dal XML")
                return legacy_format

            finally:
                loop.close()

        except Exception as e:
            print(f"❌ Errore parsing XML: {e}")
            self.logger.error(f"Legacy adapter parse error: {e}", exc_info=True)
            return {}

    async def analyze_dataflows_xml(self, xml_content: str) -> Dict:
        """
        Legacy async method: Analyze dataflows from XML content.

        This method provides async interface for XML analysis while using
        the modern service internally.
        """
        try:
            filters = AnalysisFilters(include_tests=False, max_results=100)
            result = await self.service.analyze_dataflows_from_xml(xml_content, filters)
            self._analysis_result = result

            # Convert to legacy format
            legacy_format = {
                "total_analyzed": result.total_analyzed,
                "categories": {},
                "timestamp": result.analysis_timestamp.isoformat(),
            }

            for category, dataflows in result.categorized_dataflows.items():
                legacy_format["categories"][category.value] = []
                for df in dataflows:
                    legacy_format["categories"][category.value].append(
                        {
                            "id": df.id,
                            "name_it": df.name_it,
                            "name_en": df.name_en,
                            "display_name": df.display_name,
                            "description": df.description,
                            "category": df.category.value,
                            "relevance_score": df.relevance_score,
                        }
                    )

            return legacy_format

        except Exception as e:
            self.logger.error(f"Legacy adapter analysis error: {e}", exc_info=True)
            return {"error": str(e), "total_analyzed": 0, "categories": {}}

    def find_top_dataflows_by_category(
        self, categorized_dataflows: Dict, top_n: int = 5
    ) -> Dict:
        """
        Legacy method: Find top dataflows by category.

        Maintains compatibility with original interface.
        """
        print("\n🎯 TOP DATAFLOW PER CATEGORIA:")
        print("=" * 50)

        top_dataflows = {}

        for category, dataflows in categorized_dataflows.items():
            if dataflows:
                # Already sorted by relevance_score in modern service
                top_dataflows[category] = dataflows[:top_n]

                print(f"\n📊 {category.upper()} (Top {min(top_n, len(dataflows))}):")
                for i, df in enumerate(dataflows[:top_n], 1):
                    print(f"  {i}. {df['display_name']}")
                    print(f"     ID: {df['id']} | Score: {df['relevance_score']}")
                    if df.get("description"):
                        desc = (
                            df["description"][:100] + "..."
                            if len(df["description"]) > 100
                            else df["description"]
                        )
                        print(f"     Desc: {desc}")

        return top_dataflows

    def test_priority_dataflows(
        self, top_dataflows: Dict, max_tests: int = 15
    ) -> List[Dict]:
        """
        Legacy method: Test priority dataflows.

        Uses modern service for actual testing.
        """
        print(f"\n🔬 TEST DATAFLOW PRIORITARI (max {max_tests}):")
        print("=" * 50)

        # Collect dataflows to test in priority order
        priority_order = [
            "popolazione",
            "economia",
            "lavoro",
            "territorio",
            "istruzione",
            "salute",
        ]

        dataflows_to_test = []
        test_count = 0

        for category in priority_order:
            if test_count >= max_tests:
                break

            if category in top_dataflows and top_dataflows[category]:
                print(f"\n📈 Testando categoria: {category.upper()}")

                for df in top_dataflows[category]:
                    if test_count >= max_tests:
                        break
                    dataflows_to_test.append(df)
                    test_count += 1

        # Use modern service to run tests
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = []
            for df_dict in dataflows_to_test:
                print(f"\n  🔍 Test: {df_dict['display_name']} ({df_dict['id']})")

                # Run individual test
                test_result = loop.run_until_complete(
                    self.service.test_dataflow_access(df_dict["id"], save_sample=True)
                )

                # Convert to legacy format
                legacy_result = {
                    "id": df_dict["id"],
                    "name": df_dict["display_name"],
                    "category": df_dict["category"],
                    "relevance_score": df_dict["relevance_score"],
                    "tests": {
                        "data_access": {
                            "success": test_result.data_access_success,
                            "status_code": test_result.status_code or 0,
                            "size_bytes": test_result.size_bytes,
                        },
                        "observations_count": test_result.observations_count,
                        "sample_file": test_result.sample_file,
                        "parse_error": test_result.parse_error,
                    },
                }

                if test_result.error_message:
                    legacy_result["tests"]["error"] = test_result.error_message

                results.append(legacy_result)

                # Legacy output
                if test_result.data_access_success:
                    print(f"    ✅ Dati accessibili ({test_result.size_bytes} bytes)")
                    print(f"    📊 Osservazioni: {test_result.observations_count}")
                    if test_result.sample_file:
                        print(f"    💾 Sample salvato: {test_result.sample_file}")
                else:
                    print(f"    ❌ Dati non accessibili: {test_result.error_message}")

                # Rate limiting
                import time

                time.sleep(1)

            return results

        finally:
            loop.close()

    def create_tableau_ready_dataset_list(
        self, tested_dataflows: List[Dict]
    ) -> List[Dict]:
        """
        Legacy method: Create Tableau-ready dataset list.

        Converts modern TestResult objects to legacy format.
        """
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

        # Sort by priority
        tableau_ready.sort(key=lambda x: x["priority"], reverse=True)

        print(f"✅ {len(tableau_ready)} dataset pronti per Tableau:")
        for i, ds in enumerate(tableau_ready[:10], 1):
            size_mb = ds["data_size_mb"]
            obs_count = ds["observations_count"]
            print(f"  {i}. {ds['name']}")
            print(f"     Categoria: {ds['category']} | Priorità: {ds['priority']}")
            print(f"     Dimensioni: {size_mb:.2f}MB | Osservazioni: {obs_count}")

        return tableau_ready

    def generate_tableau_implementation_guide(
        self, tableau_ready_datasets: List[Dict]
    ) -> Dict[str, str]:
        """
        Legacy method: Generate Tableau implementation guide.

        Maintains compatibility with original file generation logic.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate configuration JSON
        datasets_config = {
            "timestamp": datetime.now().isoformat(),
            "total_datasets": len(tableau_ready_datasets),
            "categories": {},
            "datasets": tableau_ready_datasets,
        }

        # Group by category
        for ds in tableau_ready_datasets:
            category = ds["category"]
            if category not in datasets_config["categories"]:
                datasets_config["categories"][category] = []
            datasets_config["categories"][category].append(ds["dataflow_id"])

        # Save files using modern temp file management
        config_filename = f"tableau_istat_datasets_{timestamp}.json"
        ps_filename = f"download_istat_data_{timestamp}.ps1"
        flow_filename = f"istat_prep_flow_{timestamp}.json"

        try:
            # Save configuration
            with open(config_filename, "w", encoding="utf-8") as f:
                json.dump(datasets_config, f, ensure_ascii=False, indent=2)

            # Generate and save PowerShell script
            ps_script = self._generate_powershell_script(tableau_ready_datasets)
            with open(ps_filename, "w", encoding="utf-8") as f:
                f.write(ps_script)

            # Generate and save Prep flow template
            prep_flow = self._generate_prep_flow_template(tableau_ready_datasets)
            with open(flow_filename, "w", encoding="utf-8") as f:
                json.dump(prep_flow, f, ensure_ascii=False, indent=2)

            print(f"\n📁 FILE GENERATI:")
            print(f"  • {config_filename} - Configurazione dataset")
            print(f"  • {ps_filename} - Script download PowerShell")
            print(f"  • {flow_filename} - Template Tableau Prep")

            return {
                "config_file": config_filename,
                "powershell_script": ps_filename,
                "prep_flow": flow_filename,
            }

        except Exception as e:
            print(f"❌ Errore generazione file: {e}")
            self.logger.error(f"Legacy adapter file generation error: {e}")
            return {"error": str(e)}

    def generate_summary_report(self, categorized_data: Dict) -> str:
        """Legacy method: Generate summary report."""
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
                    name = dataset.get("display_name", dataset.get("name", "Unknown"))
                    report += f"  - {name}\n"

        return report

    # Private helper methods (maintain legacy behavior)

    def _suggest_tableau_connection(self, dataflow: Dict) -> str:
        """Suggest Tableau connection type based on data size."""
        size_mb = dataflow["tests"]["data_access"]["size_bytes"] / (1024 * 1024)

        if size_mb > 50:
            return "bigquery_extract"
        elif size_mb > 5:
            return "google_sheets_import"
        else:
            return "direct_connection"

    def _suggest_refresh_frequency(self, category: str) -> str:
        """Suggest refresh frequency by category."""
        frequency_map = {
            "popolazione": "monthly",
            "economia": "quarterly",
            "lavoro": "monthly",
            "territorio": "yearly",
            "istruzione": "yearly",
            "salute": "quarterly",
        }
        return frequency_map.get(category, "quarterly")

    def _calculate_priority(self, dataflow: Dict) -> float:
        """Calculate priority score for Tableau integration."""
        base_score = dataflow["relevance_score"]
        tests_data = dataflow.get("tests", {})
        data_access = tests_data.get("data_access", {})

        size_bonus = min(5, data_access.get("size_bytes", 0) / (1024 * 1024) / 10)
        obs_bonus = min(5, tests_data.get("observations_count", 0) / 1000)

        return base_score + size_bonus + obs_bonus

    def _generate_powershell_script(self, datasets: List[Dict]) -> str:
        """Generate PowerShell download script."""
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

    def _generate_prep_flow_template(self, datasets: List[Dict]) -> Dict:
        """Generate Tableau Prep flow template."""
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

    # Private methods for backward compatibility with tests
    def _extract_dataflow_info(self, dataflow_elem, namespaces):
        """Legacy compatibility method - delegates to modern service."""
        # This is a compatibility shim for tests that expect this method
        return self.service._extract_dataflow_info(dataflow_elem, namespaces)

    async def _categorize_dataflows(self, dataflows):
        """Legacy compatibility method - delegates to modern service."""
        # This is a compatibility shim for tests that expect this method
        return await self.service._categorize_dataflows(dataflows)

    async def _test_single_dataflow(self, dataflow_id, save_sample=False):
        """Legacy compatibility method - delegates to modern service."""
        # This is a compatibility shim for tests that expect this method
        return await self.service.test_dataflow_access(dataflow_id, save_sample)


# Factory function for easy migration
def create_legacy_adapter() -> LegacyDataflowAnalyzerAdapter:
    """Create legacy adapter instance."""
    return LegacyDataflowAnalyzerAdapter()


# Main function for backward compatibility
def main():
    """Legacy main function - maintains backward compatibility."""
    print("🇮🇹 ISTAT DATAFLOW ANALYZER (Legacy Compatibility Mode)")
    print("Using modern DataflowAnalysisService internally")
    print("=" * 60)

    adapter = create_legacy_adapter()

    # 1. Analyze XML dataflow
    categorized = adapter.parse_dataflow_xml()

    if not categorized:
        print(
            "❌ Impossibile analizzare dataflow. Verifica che dataflow_response.xml esista."
        )
        return

    # 2. Find top dataflows per category
    top_dataflows = adapter.find_top_dataflows_by_category(categorized, top_n=3)

    # 3. Test priority dataflows
    tested = adapter.test_priority_dataflows(top_dataflows, max_tests=15)

    # 4. Create Tableau-ready list
    tableau_ready = adapter.create_tableau_ready_dataset_list(tested)

    # 5. Generate implementation guide
    files = adapter.generate_tableau_implementation_guide(tableau_ready)

    print("\n" + "=" * 60)
    print("✅ ANALISI COMPLETATA!")
    print(f"📊 Dataset analizzati e pronti per Tableau: {len(tableau_ready)}")
    print(f"📁 File generati: {len(files)}")
    print("\n🚀 PROSSIMI PASSI:")
    print("  1. Esegui lo script PowerShell per download dati")
    print("  2. Importa la configurazione JSON in Tableau")
    print("  3. Usa il template Prep flow per elaborazione automatica")
    print(
        "\n💡 NOTA: Questa versione usa il moderno DataflowAnalysisService internamente"
    )
    print("   per prestazioni e affidabilità migliorate.")


if __name__ == "__main__":
    main()
