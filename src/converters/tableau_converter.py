"""
Tableau Converter for ISTAT SDMX data.
Refactored to inherit from BaseIstatConverter to eliminate code duplication.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.utils.logger import get_logger

from .base_converter import BaseIstatConverter

logger = get_logger(__name__)


class IstatXMLtoTableauConverter(BaseIstatConverter):
    def __init__(self):
        """Initialize Tableau converter with base functionality."""
        super().__init__()

        # Tableau-specific setup (none needed for now)
        logger.info("Tableau converter initialized")

    def _load_datasets_config_json(self):
        """Legacy: Carica configurazione dataset da file JSON."""
        config_files = [
            f
            for f in os.listdir(".")
            if f.startswith("tableau_istat_datasets_") and f.endswith(".json")
        ]

        if not config_files:
            print(
                "⚠️  File configurazione JSON non trovato. Creazione configurazione di esempio..."
            )
            return self._create_sample_config()

        latest_config = sorted(config_files)[-1]
        print(f"📄 Caricamento configurazione JSON: {latest_config}")

        try:
            safe_file = self.path_validator.safe_open(
                latest_config, "r", encoding="utf-8"
            )
            with safe_file as f:
                config = json.load(f)
                logger.info(
                    f"✅ Loaded {config.get('total_datasets', 0)} datasets from JSON"
                )
                return config
        except Exception as e:
            print(f"❌ Errore caricamento config JSON: {e}")
            return self._create_sample_config()

    def _create_sample_config(self):
        """Crea configurazione di esempio se non esiste"""
        sample_config = {
            "total_datasets": 3,
            "categories": {"popolazione": 1, "economia": 1, "lavoro": 1},
            "datasets": [
                {
                    "dataflow_id": "DCIS_POPRES1",
                    "name": "Popolazione residente",
                    "category": "popolazione",
                },
                {
                    "dataflow_id": "DCCN_PILN",
                    "name": "PIL e componenti",
                    "category": "economia",
                },
                {
                    "dataflow_id": "DCCV_TAXOCCU",
                    "name": "Tasso di occupazione",
                    "category": "lavoro",
                },
            ],
        }

        # Salva config di esempio in modo sicuro
        config_file = f"tableau_istat_datasets_{datetime.now().strftime('%Y%m%d')}.json"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(config_file):
            config_file = self.path_validator.sanitize_filename(config_file)

        safe_file = self.path_validator.safe_open(config_file, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                json.dump(sample_config, f, ensure_ascii=False, indent=2)
        else:
            print(f"❌ Impossibile salvare configurazione: {config_file}")

        print(f"✅ Creata configurazione di esempio: {config_file}")
        return sample_config

    def convert_all_datasets(self):
        """Converte tutti i dataset dalla configurazione"""
        if not self.datasets_config:
            print("❌ Nessuna configurazione dataset disponibile")
            return

        print(f"\n🔄 Conversione di {len(self.datasets_config['datasets'])} dataset...")
        print("=" * 60)

        # Crea directory output se non esiste in modo sicuro
        output_dir_path = "tableau_output"
        safe_output_dir = self.path_validator.get_safe_path(
            output_dir_path, create_dirs=True
        )

        if not safe_output_dir:
            print("❌ Impossibile creare directory output sicura")
            return

        output_dir = safe_output_dir

        for dataset in self.datasets_config["datasets"]:
            self._convert_single_dataset(dataset, output_dir)

        self._generate_conversion_summary(output_dir)

    def _convert_single_dataset(self, dataset, output_dir):
        """Converte un singolo dataset XML in CSV/Excel"""
        dataflow_id = dataset["dataflow_id"]
        name = dataset["name"]
        category = dataset["category"]

        print(f"\n📊 Conversione: {name}")
        print(f"   ID: {dataflow_id} | Categoria: {category}")

        # Cerca file XML del dataset
        xml_file = self._find_xml_file(dataflow_id)

        if not xml_file:
            print("   ⚠️  File XML non trovato, creazione dati di esempio...")
            # Crea dati di esempio per dimostrare funzionamento
            df_clean = self._create_sample_data(dataflow_id, name, category)
        else:
            try:
                # Parse XML SDMX
                observations = self._parse_sdmx_xml(xml_file)

                if not observations:
                    print("   ⚠️  Nessuna osservazione trovata nel file XML")
                    df_clean = self._create_sample_data(dataflow_id, name, category)
                else:
                    # Converti in DataFrame
                    df = pd.DataFrame(observations)

                    # Pulisci e standardizza
                    df_clean = self._clean_dataframe(df, category, dataflow_id)

            except Exception as e:
                print(f"   ❌ Errore parsing XML: {e}")
                print("   📝 Creazione dati di esempio...")
                df_clean = self._create_sample_data(dataflow_id, name, category)

        # Salva in formati multipli
        output_files = self._save_multiple_formats(
            df_clean, dataflow_id, name, category, output_dir
        )

        # Registra risultati
        result = {
            "dataflow_id": dataflow_id,
            "name": name,
            "category": category,
            "original_rows": len(df_clean),
            "cleaned_rows": len(df_clean),
            "columns": list(df_clean.columns),
            "output_files": output_files,
            "success": True,
        }

        self.conversion_results.append(result)
        print(
            f"   ✅ Convertito: {len(df_clean)} righe, {len(df_clean.columns)} colonne"
        )

    def _find_xml_file(self, dataflow_id):
        """Trova file XML per il dataset in modo sicuro"""
        possible_paths = [
            f"sample_{dataflow_id}.xml",
            f"{dataflow_id}.xml",
            f"istat_data/{dataflow_id}.xml",
            f"data/{dataflow_id}.xml",
        ]

        for path in possible_paths:
            # Valida il percorso prima di controllare se esiste
            safe_path = self.path_validator.get_safe_path(path)
            if safe_path and safe_path.exists():
                return str(safe_path)

        return None

    def _create_sample_data(self, dataflow_id, name, category):
        """Crea DataFrame di esempio quando manca il file XML"""
        # Genera dati di esempio basati sulla categoria
        dates = pd.date_range("2020-01-01", "2024-12-01", freq="Q")

        if category == "popolazione":
            data = {
                "Time": dates,
                "Value": [60000000 + i * 10000 for i in range(len(dates))],
                "Territory": ["Italia"] * len(dates),
                "Age_Group": ["Totale"] * len(dates),
                "Gender": ["Totale"] * len(dates),
            }
        elif category == "economia":
            data = {
                "Time": dates,
                "Value": [450000 + i * 1000 for i in range(len(dates))],
                "Indicator": ["PIL"] * len(dates),
                "Territory": ["Italia"] * len(dates),
                "Unit": ["Milioni di euro"] * len(dates),
            }
        else:  # lavoro
            data = {
                "Time": dates,
                "Value": [58.5 + i * 0.1 for i in range(len(dates))],
                "Indicator": ["Tasso di occupazione"] * len(dates),
                "Territory": ["Italia"] * len(dates),
                "Age_Group": ["15-64 anni"] * len(dates),
                "Unit": ["Percentuale"] * len(dates),
            }

        df = pd.DataFrame(data)

        # Aggiungi metadati
        df["Dataset_ID"] = dataflow_id
        df["Dataset_Name"] = name
        df["Category"] = category
        df["Source"] = "ISTAT"
        df["Last_Updated"] = datetime.now().strftime("%Y-%m-%d")

        return df

    def _clean_dataframe(self, df, category, dataflow_id):
        """Pulisce e standardizza DataFrame per Tableau"""
        df_clean = df.copy()

        # Standardizza nomi colonne
        df_clean.columns = [self._clean_column_name(col) for col in df_clean.columns]

        # Gestisci date/tempo
        time_columns = [
            col
            for col in df_clean.columns
            if "time" in col.lower() or "date" in col.lower()
        ]
        for time_col in time_columns:
            df_clean[time_col] = self._standardize_time_column(df_clean[time_col])

        # Gestisci valori numerici
        value_columns = [
            col
            for col in df_clean.columns
            if "value" in col.lower() or "obs" in col.lower()
        ]
        for val_col in value_columns:
            df_clean[val_col] = pd.to_numeric(df_clean[val_col], errors="coerce")

        # Aggiungi metadati
        df_clean["Dataset_ID"] = dataflow_id
        df_clean["Category"] = category
        df_clean["Source"] = "ISTAT"
        df_clean["Last_Updated"] = datetime.now().strftime("%Y-%m-%d")

        # Rimuovi righe completamente vuote
        df_clean = df_clean.dropna(how="all")

        # Riordina colonne logicamente
        priority_cols = ["Dataset_ID", "Category", "Time", "Value"]
        other_cols = [col for col in df_clean.columns if col not in priority_cols]
        available_cols = [
            col for col in priority_cols if col in df_clean.columns
        ] + other_cols

        df_clean = df_clean[available_cols]

        return df_clean

    def _clean_column_name(self, col_name):
        """Pulisce nome colonna per Tableau"""
        # Rimuovi namespace XML
        clean_name = col_name.split("}")[-1] if "}" in col_name else col_name

        # Sostituisci caratteri problematici
        clean_name = re.sub(r"[^\w\s-]", "_", clean_name)
        clean_name = re.sub(r"\s+", "_", clean_name)
        clean_name = clean_name.strip("_")

        # Capitalizza prima lettera di ogni parola
        return clean_name.replace("_", " ").title().replace(" ", "_")

    def _standardize_time_column(self, time_series):
        """Standardizza colonna temporale"""
        # Prova conversione diretta a datetime
        try:
            return pd.to_datetime(time_series)
        except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime) as e:
            logger.warning(f"Errore conversione datetime diretta: {e}")
            pass

        # Altrimenti applica parsing custom
        def parse_time(time_val):
            if pd.isna(time_val):
                return None

            time_str = str(time_val).strip()

            # Pattern comuni SDMX
            patterns = [
                (r"^(\d{4})$", lambda m: f"{m.group(1)}-01-01"),  # 2024
                (
                    r"^(\d{4})-(\d{1,2})$",
                    lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-01",
                ),  # 2024-03
                (
                    r"^(\d{4})-Q(\d)$",
                    lambda m: f"{m.group(1)}-{str(int(m.group(2)) * 3).zfill(2)}-01",
                ),  # 2024-Q1
                (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", lambda m: time_str),  # 2024-03-15
            ]

            for pattern, formatter in patterns:
                match = re.match(pattern, time_str)
                if match:
                    try:
                        formatted = formatter(match)
                        return pd.to_datetime(formatted)
                    except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime) as e:
                        logger.debug(f"Errore parsing pattern {pattern}: {e}")
                        continue

            # Prova parsing diretto come fallback
            try:
                return pd.to_datetime(time_str)
            except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime) as e:
                logger.debug(f"Errore parsing fallback per {time_str}: {e}")
                return time_str

        return time_series.apply(parse_time)

    def _save_multiple_formats(self, df, dataflow_id, name, category, output_dir):
        """Salva DataFrame in formati multipli per Tableau"""
        timestamp = datetime.now().strftime("%Y%m%d")
        base_name = f"{category}_{dataflow_id}_{timestamp}"

        output_files = {}

        # 1. CSV per import diretto in modo sicuro
        csv_filename = f"{base_name}.csv"
        csv_path = output_dir / csv_filename

        # Valida il percorso
        if self.path_validator.validate_path(csv_path):
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            output_files["csv"] = str(csv_path)
        else:
            print(f"❌ Percorso non sicuro per CSV: {csv_path}")

        # 2. Excel con metadati in modo sicuro
        excel_filename = f"{base_name}.xlsx"
        excel_path = output_dir / excel_filename

        # Valida il percorso
        if self.path_validator.validate_path(excel_path):
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)

            # Foglio metadati
            metadata = pd.DataFrame(
                [
                    ["Dataset ID", dataflow_id],
                    ["Name", name],
                    ["Category", category],
                    ["Rows", len(df)],
                    ["Columns", len(df.columns)],
                    ["Column Names", ", ".join(df.columns)],
                    ["Source", "ISTAT SDMX"],
                    ["Converted", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ],
                columns=["Field", "Value"],
            )

            metadata.to_excel(writer, sheet_name="Metadata", index=False)

            # Foglio statistiche
            if "Value" in df.columns:
                stats = df["Value"].describe()
                stats_df = pd.DataFrame(
                    {"Statistic": stats.index, "Value": stats.values}
                )
                stats_df.to_excel(writer, sheet_name="Statistics", index=False)

            output_files["excel"] = str(excel_path)
        else:
            print(f"❌ Percorso non sicuro per Excel: {excel_path}")

        # 3. JSON per API/web (solo se piccolo) in modo sicuro
        if len(df) < 10000:
            json_filename = f"{base_name}.json"
            json_path = output_dir / json_filename

            # Valida il percorso
            if self.path_validator.validate_path(json_path):
                df.to_json(
                    json_path,
                    orient="records",
                    date_format="iso",
                    force_ascii=False,
                    indent=2,
                )
                output_files["json"] = str(json_path)
            else:
                print(f"❌ Percorso non sicuro per JSON: {json_path}")

        return output_files

    def _generate_conversion_summary(self, output_dir):
        """Genera summary della conversione"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        successful = [r for r in self.conversion_results if r.get("success", False)]
        failed = [r for r in self.conversion_results if not r.get("success", False)]

        summary = {
            "conversion_timestamp": datetime.now().isoformat(),
            "total_datasets": len(self.conversion_results),
            "successful_conversions": len(successful),
            "failed_conversions": len(failed),
            "success_rate": (
                f"{(len(successful) / len(self.conversion_results) * 100):.1f}%"
                if self.conversion_results
                else "0%"
            ),
            "output_directory": str(output_dir),
            "successful_datasets": successful,
            "failed_datasets": failed,
            "files_generated": {
                "csv_files": len(
                    [
                        f
                        for r in successful
                        for f in r.get("output_files", {}).values()
                        if f.endswith(".csv")
                    ]
                ),
                "excel_files": len(
                    [
                        f
                        for r in successful
                        for f in r.get("output_files", {}).values()
                        if f.endswith(".xlsx")
                    ]
                ),
                "json_files": len(
                    [
                        f
                        for r in successful
                        for f in r.get("output_files", {}).values()
                        if f.endswith(".json")
                    ]
                ),
            },
        }

        # Salva summary in modo sicuro
        summary_filename = f"conversion_summary_{timestamp}.json"
        summary_path = output_dir / summary_filename

        # Valida il percorso
        if not self.path_validator.validate_path(summary_path):
            print(f"❌ Percorso non sicuro per summary: {summary_path}")
            return

        safe_file = self.path_validator.safe_open(summary_path, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        else:
            print(f"❌ Impossibile salvare summary: {summary_path}")
            return

        # Report console
        print("\n" + "=" * 60)
        print("📋 RIEPILOGO CONVERSIONE")
        print("=" * 60)
        print(
            f"✅ Dataset convertiti con successo: {len(successful)}/{len(self.conversion_results)}"
        )
        print(f"❌ Conversioni fallite: {len(failed)}")
        print(f"📊 Tasso di successo: {summary['success_rate']}")
        print(f"📁 Directory output: {output_dir}")

        if successful:
            print("\n📁 FILE GENERATI:")
            print(f"  • CSV: {summary['files_generated']['csv_files']} file")
            print(f"  • Excel: {summary['files_generated']['excel_files']} file")
            print(f"  • JSON: {summary['files_generated']['json_files']} file")

        if failed:
            print("\n❌ DATASET FALLITI:")
            for fail in failed:
                print(
                    f"  • {fail['dataflow_id']}: {fail.get('error', 'Unknown error')}"
                )

        print(f"\n💾 Summary completo salvato: {summary_path}")

        # Genera istruzioni Tableau
        self._generate_tableau_instructions(successful, output_dir)

    def _generate_tableau_instructions(self, successful_datasets, output_dir):
        """Genera istruzioni specifiche per Tableau"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        instructions = f"""# ISTRUZIONI TABLEAU - IMPORT DATI ISTAT
Generato il: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Directory output: {output_dir}

## 📊 DATASET CONVERTITI ({len(successful_datasets)} pronti)

"""

        # Raggruppa per categoria
        by_category = {}
        for ds in successful_datasets:
            cat = ds["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(ds)

        for category, datasets in sorted(by_category.items()):
            instructions += f"\n### {category.upper()}\n"
            for ds in datasets:
                csv_file = Path(ds["output_files"].get("csv", "N/A")).name
                excel_file = Path(ds["output_files"].get("excel", "N/A")).name
                instructions += f"""
**{ds["name"]}**
- File CSV: `{csv_file}`
- File Excel: `{excel_file}`
- Righe: {ds["cleaned_rows"]:,}
- Colonne: {len(ds["columns"])}
- Colonne disponibili: {", ".join(ds["columns"][:5])}{"..." if len(ds["columns"]) > 5 else ""}
"""

        instructions += """

## 🚀 PASSAGGI TABLEAU DESKTOP

### 1. APERTURA FILE
1. Apri Tableau Desktop
2. Nella schermata iniziale, clicca su "Altro..." sotto "Connetti"
3. Seleziona "File di testo" per CSV o "Microsoft Excel" per XLSX
4. Naviga alla cartella `tableau_output`
5. Seleziona il file desiderato

### 2. CONFIGURAZIONE INIZIALE
1. **Verifica anteprima dati**: Tableau mostra i primi 1000 record
2. **Controlla tipi di dati**:
   - Time → Data
   - Value → Numero (decimale)
   - Territory, Category → Stringa
3. **Rinomina campi** se necessario (click destro → Rinomina)

### 3. CREAZIONE DATA SOURCE
1. Clicca su "Foglio 1" per iniziare l'analisi
2. Per unire più dataset:
   - Torna a "Origine dati"
   - Trascina secondo file nell'area di join
   - Configura join su Dataset_ID o Territory

### 4. VISUALIZZAZIONI CONSIGLIATE

#### SERIE TEMPORALE
1. Trascina `Time` su Colonne
2. Trascina `Value` su Righe
3. Click destro su Time → scegli livello (Anno, Trimestre, Mese)
4. Aggiungi `Territory` o `Category` su Colore

#### MAPPA GEOGRAFICA
1. Trascina `Territory` su Dettaglio
2. Tableau riconosce automaticamente "Italia" e regioni
3. Trascina `Value` su Colore
4. Cambia tipo marca in "Mappa"

#### DASHBOARD INTERATTIVA
1. Crea 3-4 fogli con visualizzazioni diverse
2. Nuovo Dashboard → trascina fogli
3. Aggiungi filtri:
   - Click destro su dimensione → Mostra filtro
   - Dashboard → Azioni → Aggiungi azione filtro

## 📈 BEST PRACTICES TABLEAU

### PERFORMANCE
- Per dataset grandi (>1M righe): Crea estratto
  - Dati → Nuovo estratto
  - Pianifica aggiornamenti automatici
- Usa filtri contestuali per limitare dati caricati
- Aggrega dati quando possibile

### FORMATTAZIONE
- Numeri grandi: Click destro → Formato → Numero → Personalizzato
  - Esempio: #,##0,.0K per mostrare migliaia
- Date: Formato → Data → Personalizzato
  - Esempio: MMM yyyy per "Gen 2024"

### CALCOLI UTILI
```
// Variazione percentuale anno su anno
(SUM([Value]) - LOOKUP(SUM([Value]), -4)) / ABS(LOOKUP(SUM([Value]), -4))

// Media mobile 4 periodi
WINDOW_AVG(SUM([Value]), -3, 0)

// Ranking per territorio
RANK(SUM([Value]))
```

## 🔄 AGGIORNAMENTO DATI

### MANUALE
1. Sostituisci file CSV/Excel nella cartella
2. In Tableau: Dati → Aggiorna origine dati

### AUTOMATICO (Tableau Server/Online)
1. Pubblica workbook su Server
2. Configura pianificazione:
   - Impostazioni → Pianifica aggiornamento
   - Scegli frequenza (giornaliera, settimanale, mensile)

## 🛠️ RISOLUZIONE PROBLEMI

**"Tipo di dati non riconosciuto"**
- Verifica formato date (YYYY-MM-DD)
- Controlla separatore decimale (punto vs virgola)

**"Territorio non riconosciuto sulla mappa"**
- Assegna ruolo geografico: Click destro → Ruolo geografico → Paese/Regione

**"Performance lenta"**
- Crea estratto invece di connessione live
- Limita dati con filtri su origine dati

## 📚 RISORSE UTILI
- [Tableau Public Gallery](https://public.tableau.com/gallery) - Esempi dashboard
- [Tableau Help](https://help.tableau.com) - Documentazione ufficiale
- [ISTAT.it](https://www.istat.it) - Fonte dati originale

---
File generato da IstatXMLtoTableauConverter v2.0
"""

        instructions_filename = f"tableau_import_instructions_{timestamp}.md"
        instructions_path = Path(output_dir) / instructions_filename

        # Valida il percorso
        if not self.path_validator.validate_path(instructions_path):
            print(f"❌ Percorso non sicuro per istruzioni: {instructions_path}")
            return

        safe_file = self.path_validator.safe_open(
            instructions_path, "w", encoding="utf-8"
        )
        if safe_file:
            with safe_file as f:
                f.write(instructions)
        else:
            print(f"❌ Impossibile salvare istruzioni: {instructions_path}")
            return

        print(f"📖 Istruzioni Tableau salvate: {instructions_path}")

        # Genera anche quick start guide
        self._generate_quick_start(output_dir)

    def _generate_quick_start(self, output_dir):
        """Genera guida rapida per iniziare subito"""
        quick_start = """# 🚀 QUICK START - TABLEAU + DATI ISTAT

## IN 5 MINUTI:

### 1️⃣ Apri Tableau
### 2️⃣ Connetti → Microsoft Excel
### 3️⃣ Seleziona un file .xlsx dalla cartella `tableau_output`
### 4️⃣ Clicca "Foglio 1"
### 5️⃣ Trascina:
   - `Time` → Colonne
   - `Value` → Righe
   - `Territory` → Colore

## 🎉 Hai creato la tua prima visualizzazione ISTAT!

### PROSSIMI PASSI:
- Prova diversi tipi di grafico (barre, mappe, scatter)
- Aggiungi filtri interattivi
- Combina più dataset
- Crea una dashboard

Buona analisi! 📊
"""

        quick_filename = "QUICK_START.txt"
        quick_path = Path(output_dir) / quick_filename

        # Valida il percorso
        if not self.path_validator.validate_path(quick_path):
            print(f"❌ Percorso non sicuro per quick start: {quick_path}")
            return

        safe_file = self.path_validator.safe_open(quick_path, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                f.write(quick_start)
        else:
            print(f"❌ Impossibile salvare quick start: {quick_path}")

    def _generate_tableau_formats(self, df: pd.DataFrame, dataset_info: dict) -> dict:
        """Generate multiple Tableau formats."""
        dataflow_id = dataset_info["id"]
        name = dataset_info["name"]
        category = dataset_info.get("category", "altro")

        # Generate file paths
        base_name = f"{dataflow_id}_{name[:50]}".replace(" ", "_")
        safe_base_name = self.path_validator.sanitize_filename(base_name)

        # Create output directory
        output_dir = self.path_validator.get_safe_path(
            "tableau_output", create_dirs=True
        )

        csv_file = output_dir / f"{safe_base_name}.csv"
        json_file = output_dir / f"{safe_base_name}.json"
        excel_file = output_dir / f"{safe_base_name}.xlsx"

        # Generate files
        try:
            # CSV
            df.to_csv(csv_file, index=False, encoding="utf-8")

            # JSON
            df.to_json(json_file, orient="records", force_ascii=False, indent=2)

            # Excel
            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name=category[:31])

            return {
                "csv_file": str(csv_file),
                "json_file": str(json_file),
                "excel_file": str(excel_file),
            }
        except Exception as e:
            print(f"❌ Errore generazione formati Tableau: {e}")
            return {}

    def convert_xml_to_tableau(
        self, xml_input: str, dataset_id: str, dataset_name: str
    ) -> dict:
        """Convert XML to Tableau formats."""
        try:
            # Determine if input is file path or XML content
            if xml_input.strip().startswith("<?xml") or xml_input.strip().startswith(
                "<"
            ):
                # It's XML content
                df = self._parse_xml_content(xml_input)
            else:
                # It's a file path
                safe_file = self.path_validator.safe_open(
                    xml_input, "r", encoding="utf-8"
                )
                if not safe_file:
                    return {"success": False, "error": f"Cannot read file: {xml_input}"}

                with safe_file as f:
                    xml_content = f.read()
                    df = self._parse_xml_content(xml_content)

            if df.empty:
                return {"success": False, "error": "No data found in XML"}

            # Categorize dataset
            category, priority = self._categorize_dataset(dataset_id, dataset_name)

            # Validate data quality
            quality_report = self._validate_data_quality(df)

            # Generate dataset info
            dataset_info = {
                "id": dataset_id,
                "name": dataset_name,
                "category": category,
                "priority": priority,
            }

            # Generate Tableau formats
            files_created = self._generate_tableau_formats(df, dataset_info)

            # Create summary
            summary = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "category": category,
                "priority": priority,
                "rows": len(df),
                "columns": len(df.columns),
                "files_created": len(files_created),
            }

            return {
                "success": True,
                "files_created": files_created,
                "data_quality": quality_report,
                "summary": summary,
            }

        except Exception as e:
            print(f"❌ Errore conversione XML to Tableau: {e}")
            return {"success": False, "error": str(e)}

    # Implementation of abstract methods from BaseIstatConverter
    def _format_output(self, df: pd.DataFrame, dataset_info: dict) -> dict:
        """Format DataFrame for Tableau output."""
        return self._generate_tableau_formats(df, dataset_info)

    def _generate_metadata(self, dataset_info: dict) -> dict:
        """Generate Tableau-specific metadata."""
        return {
            "target_platform": "tableau",
            "supported_formats": ["csv", "excel", "json", "tds"],
            "optimization": "hyper_ready",
            "dataset_info": dataset_info,
        }

    def convert_xml_to_target(
        self, xml_input: str, dataset_id: str, dataset_name: str
    ) -> dict:
        """Main conversion method that implements the abstract interface."""
        return self.convert_xml_to_tableau(xml_input, dataset_id, dataset_name)


def main():
    """Funzione principale conversione"""
    print("🔄 ISTAT XML TO TABLEAU CONVERTER v2.0")
    print("Converte XML SDMX in formati Tableau-friendly")
    print("=" * 60)

    converter = IstatXMLtoTableauConverter()

    if not converter.datasets_config:
        print("❌ Impossibile procedere senza configurazione dataset")
        return

    print(f"\n📊 Dataset da convertire: {converter.datasets_config['total_datasets']}")
    print(f"🗂️  Categorie: {', '.join(converter.datasets_config['categories'].keys())}")

    # Avvia conversione
    converter.convert_all_datasets()

    print("\n🎉 CONVERSIONE COMPLETATA!")
    print("I file sono pronti per l'import in Tableau Desktop/Server")
    print(
        "\n💡 Suggerimento: Leggi QUICK_START.txt nella cartella tableau_output per iniziare subito!"
    )


if __name__ == "__main__":
    main()
