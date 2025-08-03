"""
Base converter class for ISTAT SDMX data processing.
Eliminates code duplication between PowerBI and Tableau converters.
"""

import os
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from src.database.sqlite.dataset_config import get_dataset_config_manager
from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.secure_path import create_secure_validator

logger = get_logger(__name__)


class BaseIstatConverter(ABC):
    """Abstract base converter for ISTAT SDMX data processing."""

    def __init__(self):
        """Initialize the base converter with common components."""
        # Common SDMX namespaces - Issue #84: Use centralized configuration
        self.namespaces = Config.SDMX_NAMESPACES.copy()

        # Initialize secure path validator
        self.path_validator = create_secure_validator(os.getcwd())

        # Initialize SQLite dataset configuration manager
        self.config_manager = get_dataset_config_manager()

        # Load datasets configuration from SQLite with fallback to JSON
        self.datasets_config = self._load_datasets_config()
        self.conversion_results = []

    def _load_datasets_config(self) -> dict:
        """Load dataset configuration from SQLite metadata database."""
        try:
            logger.info(
                "Loading dataset configuration from SQLite metadata database..."
            )
            config = self.config_manager.get_datasets_config()

            if config and config.get("total_datasets", 0) > 0:
                logger.info(f"✅ Loaded {config['total_datasets']} datasets from SQLite")
                return config
            else:
                logger.warning("SQLite config empty, returning minimal config")
                return {
                    "total_datasets": 0,
                    "categories": {},
                    "datasets": [],
                    "source": "sqlite_empty",
                }

        except Exception as e:
            logger.error(f"SQLite config loading failed: {e}")
            return {
                "total_datasets": 0,
                "categories": {},
                "datasets": [],
                "source": "sqlite_error",
            }

    def _parse_sdmx_xml(self, xml_file: str) -> list[dict]:
        """Parse SDMX XML file and extract observations."""
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
                                    obs_data[clean_key] = value
                                observations.append(obs_data)

            logger.info(f"Parsed {len(observations)} observations from SDMX XML")
            return observations

        except Exception as e:
            logger.error(f"Error parsing SDMX XML: {e}")
            return []

    def _extract_observation_from_element(self, elem) -> Optional[dict]:
        """Extract observation data from XML element."""
        try:
            obs_data = {}

            # Extract attributes
            for key, value in elem.attrib.items():
                clean_key = key.split("}")[1] if "}" in key else key
                obs_data[clean_key] = value

            # Extract child elements
            for child in elem:
                tag_name = child.tag.split("}")[1] if "}" in child.tag else child.tag

                if child.text:
                    obs_data[tag_name] = child.text

                # Also extract attributes from children
                for attr_key, attr_value in child.attrib.items():
                    clean_attr_key = (
                        attr_key.split("}")[1] if "}" in attr_key else attr_key
                    )
                    obs_data[f"{tag_name}_{clean_attr_key}"] = attr_value

            return obs_data if obs_data else None

        except Exception as e:
            logger.error(f"Error extracting observation: {e}")
            return None

    def _parse_xml_content(self, xml_content: str) -> pd.DataFrame:
        """Parse XML content directly and convert to DataFrame."""
        try:
            # Handle empty content
            if not xml_content or not xml_content.strip():
                return pd.DataFrame()

            # Parse XML content
            root = ET.fromstring(xml_content)

            # Extract observations using the same logic
            observations = []

            def strip_namespace(tag):
                return tag.split("}")[1] if "}" in tag else tag

            all_elements = root.findall(".//*")

            # Process Series elements directly (not all elements)
            series_elements = root.findall(
                ".//*/generic:Series",
                {
                    "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"
                },
            )
            if not series_elements:
                # Fallback to generic search if namespaced search fails
                for elem in all_elements:
                    tag_name = strip_namespace(elem.tag)
                    if tag_name == "Series":
                        series_elements.append(elem)

            for series_elem in series_elements:
                series_data = dict(series_elem.attrib)

                # Extract series key values (TERRITORIO, TIPO_DATO, etc.)
                for child in series_elem:
                    child_tag = strip_namespace(child.tag)

                    if child_tag == "SeriesKey":
                        # Extract key-value pairs from SeriesKey
                        for value_elem in child:
                            value_tag = strip_namespace(value_elem.tag)
                            if value_tag == "Value":
                                key_id = value_elem.get("id")
                                key_value = value_elem.get("value")
                                if key_id and key_value:
                                    series_data[key_id] = key_value

                    elif child_tag in ["Obs", "Observation"]:
                        obs_data = self._extract_observation_from_element(child)
                        if obs_data:
                            # Add series data to observation
                            for key, value in series_data.items():
                                clean_key = key.split("}")[1] if "}" in key else key
                                obs_data[clean_key] = value

                            # Rename standard columns for consistency
                            if "ObsDimension_value" in obs_data:
                                obs_data["Time"] = obs_data.pop("ObsDimension_value")
                            if "ObsValue_value" in obs_data:
                                obs_data["Value"] = obs_data.pop("ObsValue_value")

                            observations.append(obs_data)

            # Fallback: process standalone Obs elements
            if not observations:
                for elem in all_elements:
                    tag_name = strip_namespace(elem.tag)
                    if tag_name in ["Obs", "Observation"]:
                        obs_data = self._extract_observation_from_element(elem)
                        if obs_data:
                            # Rename standard columns for consistency
                            if "ObsDimension_value" in obs_data:
                                obs_data["Time"] = obs_data.pop("ObsDimension_value")
                            if "ObsValue_value" in obs_data:
                                obs_data["Value"] = obs_data.pop("ObsValue_value")
                            observations.append(obs_data)

            # Convert to DataFrame
            if observations:
                df = pd.DataFrame(observations)
                logger.info(
                    f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns"
                )
                return df
            else:
                logger.warning("No observations found in XML content")
                return pd.DataFrame()

        except ET.ParseError:
            # Let ParseError bubble up for tests that expect it
            raise
        except Exception as e:
            logger.error(f"Error parsing XML content: {e}")
            return pd.DataFrame()

    def _categorize_dataset(
        self, dataset_id: str, dataset_name: str = ""
    ) -> tuple[str, int]:
        """Categorize dataset and assign priority based on content."""
        category_keywords = {
            "popolazione": [
                "popol",
                "resid",
                "demog",
                "cittadin",
                "stranieri",
                "immigrant",
            ],
            "economia": [
                "pil",
                "gdp",
                "economic",
                "commerci",
                "import",
                "export",
                "prezzi",
                "inflaz",
            ],
            "lavoro": [
                "lavoro",
                "occupaz",
                "disoccupaz",
                "employment",
                "unemploy",
                "salari",
                "stipendi",
            ],
            "territorio": [
                "region",
                "provinc",
                "comun",
                "territor",
                "geografic",
                "amministrativ",
            ],
            "istruzione": [
                "istruz",
                "scuol",
                "universit",
                "educaz",
                "student",
                "diplom",
                "laureat",
            ],
            "salute": [
                "sanit",
                "salut",
                "health",
                "medic",
                "ospedal",
                "malatt",
                "mortalit",
            ],
        }

        category_priorities = {
            "popolazione": 10,
            "economia": 9,
            "lavoro": 8,
            "territorio": 7,
            "istruzione": 6,
            "salute": 5,
            "altro": 1,
        }

        text_to_check = f"{dataset_id} {dataset_name}".lower()

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    return category, category_priorities[category]

        return "altro", category_priorities["altro"]

    def _validate_data_quality(self, df: pd.DataFrame) -> dict:
        """Validate data quality and return quality metrics."""
        if df.empty:
            return {
                "total_rows": 0,
                "total_columns": 0,
                "completeness_score": 0.0,
                "data_quality_score": 0.0,
                "issues": ["Empty dataset"],
            }

        total_cells = len(df) * len(df.columns)
        non_null_cells = df.count().sum()
        completeness_score = non_null_cells / total_cells if total_cells > 0 else 0.0

        # Additional quality checks
        numeric_columns = df.select_dtypes(include=["number"]).columns
        numeric_quality = 1.0

        if len(numeric_columns) > 0:
            # Check for infinite or NaN values in numeric columns
            numeric_issues = (
                df[numeric_columns].isin([float("inf"), float("-inf")]).sum().sum()
            )
            numeric_quality = 1.0 - (numeric_issues / (len(df) * len(numeric_columns)))

        # Overall quality score (weighted average)
        data_quality_score = (completeness_score * 0.7) + (numeric_quality * 0.3)

        issues = []
        if completeness_score < 0.8:
            issues.append("Low completeness score")
        if numeric_quality < 0.9:
            issues.append("Numeric data quality issues")

        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "completeness_score": round(completeness_score, 3),
            "data_quality_score": round(data_quality_score, 3),
            "issues": issues,
        }

    # Abstract methods that subclasses must implement
    @abstractmethod
    def _format_output(self, df: pd.DataFrame, dataset_info: dict) -> dict:
        """Format output data for specific target (PowerBI, Tableau, etc.)."""
        pass

    @abstractmethod
    def _generate_metadata(self, dataset_info: dict) -> dict:
        """Generate metadata for specific target."""
        pass

    @abstractmethod
    def convert_xml_to_target(
        self, xml_input: str, dataset_id: str, dataset_name: str
    ) -> dict:
        """Main conversion method - must be implemented by subclasses."""
        pass
