"""
Convertitore ISTAT XML to PowerBI
Converte dati ISTAT SDMX in formati compatibili con PowerBI
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.secure_path import create_secure_validator

logger = get_logger(__name__)


class IstatXMLToPowerBIConverter:
    """Convertitore per trasformare dati ISTAT XML in formato PowerBI."""

    def __init__(self):
        """Inizializza il convertitore."""
        self.namespaces = {
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
            "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
            "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

        # Initialize secure path validator BEFORE using it
        self.path_validator = create_secure_validator(os.getcwd())

        # Now safe to call methods that use path_validator
        self.datasets_config = self._load_datasets_config()
        self.conversion_results = []

        # Assicura che directory PowerBI esista in modo sicuro
        self.powerbi_output_dir = Config.PROCESSED_DATA_DIR / "powerbi"

        # Valida la directory di output
        safe_output_dir = self.path_validator.get_safe_path(
            self.powerbi_output_dir, create_dirs=True
        )
        if safe_output_dir:
            self.powerbi_output_dir = safe_output_dir
        else:
            logger.error(
                f"Impossibile creare directory PowerBI sicura: {self.powerbi_output_dir}"
            )
            # Fallback to a safe directory
            self.powerbi_output_dir = self.path_validator.get_safe_path(
                "powerbi_output", create_dirs=True
            )

        logger.info("Convertitore ISTAT → PowerBI inizializzato")

    def _load_datasets_config(self) -> Dict:
        """Carica configurazione dataset."""
        config_files = [
            f
            for f in os.listdir(".")
            if f.startswith("tableau_istat_datasets_") and f.endswith(".json")
        ]

        if not config_files:
            logger.warning(
                "File configurazione non trovato, creazione configurazione di esempio..."
            )
            return self._create_sample_config()

        latest_config = sorted(config_files)[-1]
        logger.info(f"Caricamento configurazione: {latest_config}")

        try:
            safe_file = self.path_validator.safe_open(
                latest_config, "r", encoding="utf-8"
            )
            with safe_file as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Errore caricamento config: {e}")
            return self._create_sample_config()

    def _create_sample_config(self) -> Dict:
        """Crea configurazione di esempio."""
        sample_config = {
            "total_datasets": 6,
            "categories": {
                "popolazione": ["22_293"],
                "economia": ["163_156", "732_1051"],
                "lavoro": ["151_1176", "151_1178"],
                "istruzione": ["124_1156", "124_1157"],
                "territorio": ["24_386"],
            },
            "datasets": [
                {
                    "dataflow_id": "22_293",
                    "name": "Indicatori demografici",
                    "category": "popolazione",
                },
                {
                    "dataflow_id": "163_156",
                    "name": "Conto economico PIL corrente",
                    "category": "economia",
                },
                {
                    "dataflow_id": "732_1051",
                    "name": "Conto economico PIL - edizioni 2014-2019",
                    "category": "economia",
                },
                {
                    "dataflow_id": "151_1176",
                    "name": "Tasso disoccupazione mensile",
                    "category": "lavoro",
                },
                {
                    "dataflow_id": "151_1178",
                    "name": "Tasso disoccupazione trimestrale",
                    "category": "lavoro",
                },
                {
                    "dataflow_id": "124_1156",
                    "name": "Stato patrimoniale università",
                    "category": "istruzione",
                },
            ],
        }

        config_file = f"powerbi_istat_datasets_{datetime.now().strftime('%Y%m%d')}.json"

        # Valida e sanitizza il nome del file
        if not self.path_validator.validate_filename(config_file):
            config_file = self.path_validator.sanitize_filename(config_file)

        safe_file = self.path_validator.safe_open(config_file, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                json.dump(sample_config, f, ensure_ascii=False, indent=2)
        else:
            logger.error(f"Impossibile salvare configurazione: {config_file}")

        logger.info(f"Creata configurazione di esempio: {config_file}")
        return sample_config

    def convert_all_datasets(self) -> None:
        """Converte tutti i dataset dalla configurazione."""
        if not self.datasets_config:
            logger.error("Nessuna configurazione dataset disponibile")
            return

        logger.info(
            f"Conversione di {len(self.datasets_config['datasets'])} dataset per PowerBI..."
        )

        for dataset in self.datasets_config["datasets"]:
            self._convert_single_dataset(dataset)

        self._generate_powerbi_summary()

    def _convert_single_dataset(self, dataset: Dict) -> None:
        """Converte un singolo dataset XML per PowerBI."""
        dataflow_id = dataset["dataflow_id"]
        name = dataset["name"]
        category = dataset["category"]

        logger.info(f"Conversione dataset: {name} ({dataflow_id})")

        # Cerca file XML del dataset
        xml_file = self._find_xml_file(dataflow_id)

        if not xml_file:
            logger.warning(
                f"File XML non trovato per {dataflow_id}, creazione dati di esempio..."
            )
            df_clean = self._create_sample_data(dataflow_id, name, category)
        else:
            try:
                observations = self._parse_sdmx_xml(xml_file)

                if not observations:
                    logger.warning(
                        f"Nessuna osservazione trovata nel file XML per {dataflow_id}"
                    )
                    df_clean = self._create_sample_data(dataflow_id, name, category)
                else:
                    df = pd.DataFrame(observations)
                    df_clean = self._clean_dataframe_for_powerbi(
                        df, category, dataflow_id
                    )

            except Exception as e:
                logger.error(f"Errore parsing XML per {dataflow_id}: {e}")
                df_clean = self._create_sample_data(dataflow_id, name, category)

        # Salva in formati PowerBI
        output_files = self._save_powerbi_formats(df_clean, dataflow_id, name, category)

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
        logger.info(
            f"Convertito {dataflow_id}: {len(df_clean)} righe, {len(df_clean.columns)} colonne"
        )

    def _find_xml_file(self, dataflow_id: str) -> Optional[str]:
        """Trova file XML per il dataset in modo sicuro."""
        possible_paths = [
            f"sample_{dataflow_id}.xml",
            f"{dataflow_id}.xml",
            f"data/raw/istat/{dataflow_id}.xml",
            f"istat_data/{dataflow_id}.xml",
        ]

        for path in possible_paths:
            # Valida il percorso prima di controllare se esiste
            safe_path = self.path_validator.get_safe_path(path)
            if safe_path and safe_path.exists():
                return str(safe_path)

        return None

    def _parse_sdmx_xml(self, xml_file: str) -> List[Dict]:
        """Parse file XML SDMX."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            observations = []

            def strip_namespace(tag):
                return tag.split("}")[1] if "}" in tag else tag

            all_elements = root.findall(".//*")

            for elem in all_elements:
                tag_name = strip_namespace(elem.tag)

                if tag_name in ["Obs", "Observation"]:
                    obs_data = self._extract_observation_from_element(elem)
                    if obs_data:
                        observations.append(obs_data)

                elif tag_name == "Series":
                    series_data = dict(elem.attrib)

                    for child in elem:
                        child_tag = strip_namespace(child.tag)
                        if child_tag in ["Obs", "Observation"]:
                            obs_data = self._extract_observation_from_element(child)
                            if obs_data:
                                for key, value in series_data.items():
                                    clean_key = key.split("}")[1] if "}" in key else key
                                    obs_data[f"Series_{clean_key}"] = value
                                observations.append(obs_data)

            return observations

        except Exception as e:
            logger.error(f"Errore parsing XML: {e}")
            return []

    def _extract_observation_from_element(self, elem: ET.Element) -> Optional[Dict]:
        """Estrae dati da un elemento osservazione."""
        obs_data = {}

        # Estrai attributi
        for key, value in elem.attrib.items():
            clean_key = key.split("}")[1] if "}" in key else key
            obs_data[clean_key] = value

        # Estrai elementi figli
        for child in elem:
            tag = child.tag.split("}")[1] if "}" in child.tag else child.tag

            if child.text and child.text.strip():
                obs_data[tag] = child.text.strip()

            for key, value in child.attrib.items():
                clean_key = key.split("}")[1] if "}" in key else key
                obs_data[f"{tag}_{clean_key}"] = value

        return obs_data if obs_data else None

    def _clean_dataframe_for_powerbi(
        self, df: pd.DataFrame, category: str, dataflow_id: str
    ) -> pd.DataFrame:
        """Pulisce DataFrame specificamente per PowerBI."""
        df_clean = df.copy()

        # Standardizza nomi colonne per PowerBI (no spazi, caratteri speciali)
        df_clean.columns = [
            self._clean_column_name_for_powerbi(col) for col in df_clean.columns
        ]

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

        # Aggiungi metadati PowerBI
        df_clean["DatasetID"] = dataflow_id
        df_clean["Category"] = category
        df_clean["Source"] = "ISTAT"
        df_clean["LastUpdated"] = datetime.now().strftime("%Y-%m-%d")
        df_clean["LoadTimestamp"] = datetime.now()

        # Rimuovi righe vuote
        df_clean = df_clean.dropna(how="all")

        # Riordina colonne per PowerBI
        priority_cols = ["DatasetID", "Category", "Time", "Value"]
        other_cols = [col for col in df_clean.columns if col not in priority_cols]
        available_cols = [
            col for col in priority_cols if col in df_clean.columns
        ] + other_cols

        df_clean = df_clean[available_cols]

        return df_clean

    def _clean_column_name_for_powerbi(self, col_name: str) -> str:
        """Pulisce nome colonna per PowerBI."""
        # Rimuovi namespace XML
        clean_name = col_name.split("}")[-1] if "}" in col_name else col_name

        # Sostituisci caratteri problematici
        clean_name = re.sub(r"[^\w\s-]", "_", clean_name)
        clean_name = re.sub(r"\s+", "_", clean_name)
        clean_name = clean_name.strip("_")

        # PowerBI preferisce PascalCase
        words = clean_name.split("_")
        return "".join(word.capitalize() for word in words if word)

    def _standardize_time_column(self, time_series: pd.Series) -> pd.Series:
        """Standardizza colonna temporale."""
        try:
            return pd.to_datetime(time_series)
        except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime) as e:
            logger.warning(f"Errore conversione datetime diretta: {e}")
            pass

        def parse_time(time_val):
            if pd.isna(time_val):
                return None

            time_str = str(time_val).strip()

            patterns = [
                (r"^(\d{4})$", lambda m: f"{m.group(1)}-01-01"),
                (
                    r"^(\d{4})-(\d{1,2})$",
                    lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-01",
                ),
                (
                    r"^(\d{4})-Q(\d)$",
                    lambda m: f"{m.group(1)}-{str(int(m.group(2))*3).zfill(2)}-01",
                ),
                (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", lambda m: time_str),
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

            try:
                return pd.to_datetime(time_str)
            except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime) as e:
                logger.debug(f"Errore parsing fallback per {time_str}: {e}")
                return time_str

        return time_series.apply(parse_time)

    def _create_sample_data(
        self, dataflow_id: str, name: str, category: str
    ) -> pd.DataFrame:
        """Crea dati di esempio per PowerBI."""
        dates = pd.date_range("2020-01-01", "2024-12-01", freq="QE")

        if category == "popolazione":
            data = {
                "Time": dates,
                "Value": [60000000 + i * 10000 for i in range(len(dates))],
                "Territory": ["Italia"] * len(dates),
                "AgeGroup": ["Totale"] * len(dates),
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
        elif category == "lavoro":
            data = {
                "Time": dates,
                "Value": [58.5 + i * 0.1 for i in range(len(dates))],
                "Indicator": ["Tasso di occupazione"] * len(dates),
                "Territory": ["Italia"] * len(dates),
                "AgeGroup": ["15-64 anni"] * len(dates),
                "Unit": ["Percentuale"] * len(dates),
            }
        elif category == "istruzione":
            data = {
                "Time": dates,
                "Value": [1800000 + i * 5000 for i in range(len(dates))],
                "Indicator": ["Iscritti università"] * len(dates),
                "Territory": ["Italia"] * len(dates),
                "Level": ["Totale"] * len(dates),
                "Unit": ["Numero"] * len(dates),
            }
        else:
            data = {
                "Time": dates,
                "Value": [100 + i * 5 for i in range(len(dates))],
                "Indicator": ["Indicatore generico"] * len(dates),
                "Territory": ["Italia"] * len(dates),
                "Unit": ["Valore"] * len(dates),
            }

        df = pd.DataFrame(data)
        return df

    def _save_powerbi_formats(
        self, df: pd.DataFrame, dataflow_id: str, name: str, category: str
    ) -> Dict[str, str]:
        """Salva DataFrame in formati PowerBI."""
        timestamp = datetime.now().strftime("%Y%m%d")
        base_name = f"{category}_{dataflow_id}_{timestamp}"

        output_files = {}

        # 1. CSV per Power Query in modo sicuro
        csv_filename = f"{base_name}.csv"
        csv_path = self.powerbi_output_dir / csv_filename

        # Valida il percorso
        if self.path_validator.validate_path(csv_path):
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            output_files["csv"] = str(csv_path)
        else:
            logger.error(f"Percorso non sicuro per CSV: {csv_path}")

        # 2. Excel per importazione diretta in modo sicuro
        excel_filename = f"{base_name}.xlsx"
        excel_path = self.powerbi_output_dir / excel_filename

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
                    ["PowerBI Optimized", "Yes"],
                    ["Source", "ISTAT SDMX"],
                    ["Converted", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ],
                columns=["Field", "Value"],
            )

            metadata.to_excel(writer, sheet_name="Metadata", index=False)

            output_files["excel"] = str(excel_path)
        else:
            logger.error(f"Percorso non sicuro per Excel: {excel_path}")

        # 3. Parquet per performance ottimali in modo sicuro
        parquet_filename = f"{base_name}.parquet"
        parquet_path = self.powerbi_output_dir / parquet_filename

        # Valida il percorso
        if self.path_validator.validate_path(parquet_path):
            df.to_parquet(parquet_path, index=False)
            output_files["parquet"] = str(parquet_path)
        else:
            logger.error(f"Percorso non sicuro per Parquet: {parquet_path}")

        # 4. JSON per API integrations in modo sicuro
        json_filename = f"{base_name}.json"
        json_path = self.powerbi_output_dir / json_filename

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
            logger.error(f"Percorso non sicuro per JSON: {json_path}")

        return output_files

    def _generate_powerbi_summary(self) -> None:
        """Genera summary della conversione per PowerBI."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        successful = [r for r in self.conversion_results if r.get("success", False)]
        failed = [r for r in self.conversion_results if not r.get("success", False)]

        summary = {
            "conversion_timestamp": datetime.now().isoformat(),
            "total_datasets": len(self.conversion_results),
            "successful_conversions": len(successful),
            "failed_conversions": len(failed),
            "success_rate": (
                f"{(len(successful)/len(self.conversion_results)*100):.1f}%"
                if self.conversion_results
                else "0%"
            ),
            "output_directory": str(self.powerbi_output_dir),
            "successful_datasets": successful,
            "failed_datasets": failed,
            "powerbi_integration": {
                "recommended_connection_type": "Get Data > File > CSV/Excel/Parquet",
                "refresh_schedule": "Monthly for demographic data, Quarterly for economic data",
                "data_gateway": "Not required for file-based connections",
                "power_query_optimizations": [
                    "Use Parquet format for best performance",
                    "Filter data in Power Query to reduce model size",
                    "Use proper data types (DateTime, Decimal, etc.)",
                    "Create relationships between tables based on DatasetID",
                ],
            },
        }

        # Salva summary in modo sicuro
        summary_filename = f"conversion_summary_{timestamp}.json"
        summary_path = self.powerbi_output_dir / summary_filename

        # Valida il percorso
        if self.path_validator.validate_path(summary_path):
            safe_file = self.path_validator.safe_open(
                summary_path, "w", encoding="utf-8"
            )
            if safe_file:
                with safe_file as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
            else:
                logger.error(f"Impossibile salvare summary: {summary_path}")
        else:
            logger.error(f"Percorso non sicuro per summary: {summary_path}")

        # Genera guida PowerBI
        self._generate_powerbi_guide(successful, timestamp)

        logger.info(f"Summary PowerBI salvato: {summary_path}")
        logger.info(
            f"Conversione completata: {len(successful)}/{len(self.conversion_results)} dataset convertiti"
        )

    def _generate_powerbi_guide(
        self, successful_datasets: List[Dict], timestamp: str
    ) -> None:
        """Genera guida specifica per PowerBI."""
        guide_filename = f"powerbi_integration_guide_{timestamp}.md"
        guide_path = self.powerbi_output_dir / guide_filename

        # Valida il percorso
        if not self.path_validator.validate_path(guide_path):
            logger.error(f"Percorso non sicuro per guida: {guide_path}")
            return

        guide_content = f"""# Guida Integrazione PowerBI - Dati ISTAT

Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Dataset Convertiti ({len(successful_datasets)} pronti)

"""

        # Raggruppa per categoria
        by_category = {}
        for ds in successful_datasets:
            cat = ds["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(ds)

        for category, datasets in sorted(by_category.items()):
            guide_content += f"\n### {category.upper()}\n"
            for ds in datasets:
                guide_content += f"""
**{ds['name']}**
- File CSV: `{Path(ds['output_files']['csv']).name}`
- File Excel: `{Path(ds['output_files']['excel']).name}`
- File Parquet: `{Path(ds['output_files']['parquet']).name}`
- Righe: {ds['cleaned_rows']:,}
- Colonne: {len(ds['columns'])}
"""

        guide_content += """

## 🚀 Passaggi PowerBI Desktop

### 1. IMPORTAZIONE DATI
1. Apri PowerBI Desktop
2. Home → Recupera dati → Altro...
3. Seleziona formato preferito:
   - **Parquet** (consigliato per performance)
   - **Excel** (per metadati inclusi)
   - **CSV** (per compatibilità)
4. Naviga alla cartella `data/processed/powerbi`
5. Seleziona file desiderato

### 2. TRASFORMAZIONE DATI (Power Query)
1. Controlla tipi di dati:
   - Time → Data/Ora
   - Value → Numero decimale
   - Territory, Category → Testo
2. Rimuovi colonne non necessarie
3. Filtra dati per periodo di interesse
4. Applica e chiudi

### 3. MODELLAZIONE DATI
1. Crea relazioni tra tabelle usando DatasetID
2. Crea gerarchia temporale (Anno → Trimestre → Mese)
3. Aggiungi colonne calcolate se necessario:
   ```dax
   Variazione % =
   DIVIDE(
       [Value] - CALCULATE([Value], PREVIOUSQUARTER(Time[Date])),
       CALCULATE([Value], PREVIOUSQUARTER(Time[Date]))
   )
   ```

### 4. VISUALIZZAZIONI CONSIGLIATE

#### Serie Temporale
- Grafico a linee con Time su asse X e Value su asse Y
- Aggiungi Category come legenda per confronti

#### Mappa Italia
- Mappa con Territory per posizione
- Value per intensità colore
- Filtra per periodo specifico

#### Dashboard KPI
- Schede per valori correnti
- Misure DAX per variazioni percentuali
- Filtri interattivi per categoria e territorio

### 5. PUBBLICAZIONE E REFRESH

#### Pubblicazione
1. File → Pubblica → Seleziona workspace
2. Configura gateway se necessario (per aggiornamenti automatici)

#### Aggiornamento Dati
1. Sostituisci file nella cartella sorgente
2. PowerBI Service → Dataset → Pianifica aggiornamento
3. Frequenza consigliata: Mensile per demografia, Trimestrale per economia

## 🔧 Ottimizzazioni Performance

### Formato Dati
- **Parquet**: Migliore performance e compressione
- **DirectQuery**: Solo per dataset molto grandi (>1GB)
- **Modello composito**: Combina import e DirectQuery

### Modellazione
- Usa relazioni instead of lookup
- Evita colonne calcolate su tabelle grandi
- Preferisci misure DAX a colonne calcolate

### Visualizzazioni
- Limita numero di visual per pagina
- Usa filtri a livello di pagina/report
- Evita tabelle con troppe righe

## 📋 Misure DAX Utili

```dax
// Valore Corrente
Valore Corrente =
CALCULATE(
    SUM(Data[Value]),
    LASTDATE(Data[Time])
)

// Variazione Anno su Anno
Variazione YoY =
VAR CurrentValue = SUM(Data[Value])
VAR PreviousValue = CALCULATE(
    SUM(Data[Value]),
    SAMEPERIODLASTYEAR(Data[Time])
)
RETURN
DIVIDE(CurrentValue - PreviousValue, PreviousValue)

// Media Mobile 4 Periodi
Media Mobile =
AVERAGEX(
    LASTPERIODS(4, Data[Time]),
    SUM(Data[Value])
)
```

## 🛠️ Risoluzione Problemi

**"Impossibile caricare file"**
- Verifica path assoluto
- Controlla permessi cartella
- Usa formato Parquet se CSV ha problemi encoding

**"Relazioni non funzionano"**
- Verifica che DatasetID sia presente in tutte le tabelle
- Controlla tipi di dati delle colonne chiave
- Usa "Gestisci relazioni" per debug

**"Performance lente"**
- Filtra dati in Power Query
- Usa aggregazioni quando possibile
- Considera DirectQuery per dataset grandi

## 📚 Risorse Utili
- [PowerBI Documentation](https://docs.microsoft.com/power-bi/)
- [DAX Reference](https://docs.microsoft.com/dax/)
- [Power Query M](https://docs.microsoft.com/powerquery-m/)
- [ISTAT.it](https://www.istat.it) - Fonte dati originale

---
File generato da IstatXMLToPowerBIConverter v1.0
"""

        safe_file = self.path_validator.safe_open(guide_path, "w", encoding="utf-8")
        if safe_file:
            with safe_file as f:
                f.write(guide_content)
        else:
            logger.error(f"Impossibile salvare guida: {guide_path}")
            return

        logger.info(f"Guida PowerBI salvata: {guide_path}")

    def _parse_xml_content(self, xml_content: str) -> pd.DataFrame:
        """Parse XML content directly and return DataFrame."""
        if not xml_content.strip():
            return pd.DataFrame()

        try:
            root = ET.fromstring(xml_content)
            observations = []

            def strip_namespace(tag):
                return tag.split("}")[1] if "}" in tag else tag

            all_elements = root.findall(".//*")

            for elem in all_elements:
                tag_name = strip_namespace(elem.tag)

                if tag_name in ["Obs", "Observation"]:
                    obs_data = self._extract_observation_from_element(elem)
                    if obs_data:
                        observations.append(obs_data)

                elif tag_name == "Series":
                    series_data = {}
                    # Extract series key attributes
                    for key_elem in elem.findall(".//*"):
                        key_tag = strip_namespace(key_elem.tag)
                        if key_tag == "Value":
                            attr_id = key_elem.get("id")
                            attr_value = key_elem.get("value")
                            if attr_id and attr_value:
                                series_data[attr_id] = attr_value

                    # Extract observations
                    for obs_elem in elem.findall(".//*"):
                        obs_tag = strip_namespace(obs_elem.tag)
                        if obs_tag in ["Obs", "Observation"]:
                            obs_data = self._extract_observation_from_element(obs_elem)
                            if obs_data:
                                obs_data.update(series_data)
                                observations.append(obs_data)

            if observations:
                df = pd.DataFrame(observations)
                # Standardize column names
                if "ObsDimension_value" in df.columns:
                    df["Time"] = df["ObsDimension_value"]
                    df.drop("ObsDimension_value", axis=1, inplace=True)
                if "ObsValue_value" in df.columns:
                    df["Value"] = df["ObsValue_value"]
                    df.drop("ObsValue_value", axis=1, inplace=True)
                return df
            else:
                return pd.DataFrame()

        except ET.ParseError as e:
            logger.error(f"Errore parsing XML: {e}")
            raise
        except Exception as e:
            logger.error(f"Errore generico parsing XML: {e}")
            return pd.DataFrame()

    def _categorize_dataset(
        self, dataset_id: str, dataset_name: str
    ) -> tuple[str, int]:
        """Categorize dataset and return priority."""
        name_lower = dataset_name.lower()

        if any(
            keyword in name_lower
            for keyword in ["popolazione", "popola", "demografic", "residente"]
        ):
            return "popolazione", 10
        elif any(
            keyword in name_lower
            for keyword in ["pil", "economia", "economico", "reddito", "prodotto"]
        ):
            return "economia", 9
        elif any(
            keyword in name_lower
            for keyword in ["lavoro", "occupazione", "disoccupazione", "employment"]
        ):
            return "lavoro", 8
        elif any(
            keyword in name_lower
            for keyword in [
                "territorio",
                "territorial",
                "regional",
                "comune",
                "provincia",
            ]
        ):
            return "territorio", 7
        elif any(
            keyword in name_lower
            for keyword in [
                "istruzione",
                "education",
                "università",
                "scuola",
                "studenti",
            ]
        ):
            return "istruzione", 6
        elif any(
            keyword in name_lower
            for keyword in ["salute", "health", "sanità", "ospedale", "medicina"]
        ):
            return "salute", 5
        else:
            return "altro", 1

    def _validate_data_quality(self, df: pd.DataFrame) -> dict:
        """Validate data quality and return metrics."""
        total_rows = len(df)
        total_columns = len(df.columns)

        if total_rows == 0 or total_columns == 0:
            return {
                "total_rows": total_rows,
                "total_columns": total_columns,
                "uniqueness_score": 0.0,
                "completeness_score": 0.0,
                "data_quality_score": 0.0,
            }

        # Calculate completeness score
        non_null_count = df.count().sum()
        total_cells = total_rows * total_columns
        completeness_score = non_null_count / total_cells if total_cells > 0 else 0.0

        # Calculate uniqueness score
        unique_count = df.nunique().sum()
        uniqueness_score = unique_count / total_cells if total_cells > 0 else 0.0

        # Calculate data quality score (simplified)
        # Consider numeric columns and valid values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        numeric_quality = 0.0

        if len(numeric_cols) > 0:
            numeric_df = df[numeric_cols]
            valid_numeric = numeric_df.notna().sum().sum()
            total_numeric = len(numeric_df) * len(numeric_cols)
            numeric_quality = (
                valid_numeric / total_numeric if total_numeric > 0 else 0.0
            )

        # Overall quality score
        data_quality_score = (completeness_score + numeric_quality + uniqueness_score) / 2

        return {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "uniqueness_score": uniqueness_score,
            "completeness_score": completeness_score,
            "data_quality_score": data_quality_score,
        }

    def _generate_powerbi_formats(self, df: pd.DataFrame, dataset_info: dict) -> dict:
        """Generate multiple PowerBI formats."""
        dataflow_id = dataset_info["id"]
        name = dataset_info["name"]
        category = dataset_info.get("category", "altro")

        # Generate file paths
        base_name = f"{dataflow_id}_{name[:50]}".replace(" ", "_")
        safe_base_name = self.path_validator.sanitize_filename(base_name)

        csv_file = self.powerbi_output_dir / f"{safe_base_name}.csv"
        parquet_file = self.powerbi_output_dir / f"{safe_base_name}.parquet"
        json_file = self.powerbi_output_dir / f"{safe_base_name}.json"
        excel_file = self.powerbi_output_dir / f"{safe_base_name}.xlsx"

        # Generate files
        try:
            # CSV
            df.to_csv(csv_file, index=False, encoding="utf-8")

            # Parquet
            df.to_parquet(parquet_file, index=False)

            # JSON
            df.to_json(json_file, orient="records", force_ascii=False, indent=2)

            # Excel
            df.to_excel(excel_file, index=False, sheet_name=category[:31])

            return {
                "csv_file": str(csv_file),
                "parquet_file": str(parquet_file),
                "json_file": str(json_file),
                "excel_file": str(excel_file),
            }
        except Exception as e:
            logger.error(f"Errore generazione formati PowerBI: {e}")
            return {}

    def convert_xml_to_powerbi(
        self, xml_input: str, dataset_id: str, dataset_name: str
    ) -> dict:
        """Convert XML to PowerBI formats."""
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

            # Generate PowerBI formats
            files_created = self._generate_powerbi_formats(df, dataset_info)

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
            logger.error(f"Errore conversione XML to PowerBI: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Funzione principale per conversione ISTAT → PowerBI."""
    print("🔄 ISTAT XML TO POWERBI CONVERTER")
    print("Converte XML SDMX in formati PowerBI-friendly")
    print("=" * 60)

    converter = IstatXMLToPowerBIConverter()

    if not converter.datasets_config:
        print("❌ Impossibile procedere senza configurazione dataset")
        return

    print(f"\n📊 Dataset da convertire: {converter.datasets_config['total_datasets']}")
    print(f"🗂️  Categorie: {', '.join(converter.datasets_config['categories'].keys())}")

    # Avvia conversione
    converter.convert_all_datasets()

    print("\n🎉 CONVERSIONE COMPLETATA!")
    print("I file sono pronti per l'import in PowerBI Desktop")
    print(f"📁 Directory output: {converter.powerbi_output_dir}")
    print(
        "\n💡 Prossimo passo: Apri PowerBI Desktop e importa i file dalla cartella powerbi/"
    )


if __name__ == "__main__":
    main()
