"""
PowerBI Template Generator for Osservatorio ISTAT Data Platform

This module generates PowerBI templates (.pbit files) optimized for ISTAT data
visualization and analysis. Templates include:
- Pre-configured data models with star schema
- Category-specific visualizations
- Italian-localized formatting
- DAX measures for common KPIs
- Quality score integration

Architecture Integration:
- Uses PowerBIOptimizer for star schema definitions
- Leverages SQLite metadata for template customization
- Integrates with existing PowerBI API client
"""

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


from src.database.sqlite.repository import UnifiedDataRepository
from src.utils.logger import get_logger

from .optimizer import PowerBIOptimizer, StarSchemaDefinition

logger = get_logger(__name__)


class PowerBITemplate:
    """Represents a PowerBI template with metadata and content."""

    def __init__(
        self,
        template_id: str,
        name: str,
        category: str,
        description: str,
        star_schema: StarSchemaDefinition,
        dax_measures: Dict[str, str],
        visualizations: List[Dict[str, Any]],
    ):
        self.template_id = template_id
        self.name = name
        self.category = category
        self.description = description
        self.star_schema = star_schema
        self.dax_measures = dax_measures
        self.visualizations = visualizations
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Export template to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "star_schema": self.star_schema.to_dict(),
            "dax_measures": self.dax_measures,
            "visualizations": self.visualizations,
            "created_at": self.created_at.isoformat(),
        }


class VisualizationLibrary:
    """Library of pre-configured visualizations for ISTAT data."""

    @staticmethod
    def get_population_visualizations() -> List[Dict[str, Any]]:
        """Get visualizations for population data."""
        return [
            {
                "type": "line_chart",
                "title": "Popolazione nel Tempo",
                "x_axis": "dim_time[year]",
                "y_axis": "Total Population",
                "legend": "dim_territory[territory_name]",
                "description": "Trend demografico per territorio",
            },
            {
                "type": "bar_chart",
                "title": "Popolazione per Territorio",
                "x_axis": "dim_territory[territory_name]",
                "y_axis": "Total Population",
                "description": "Distribuzione popolazione corrente",
            },
            {
                "type": "map",
                "title": "Densità Demografica",
                "location": "dim_territory[territory_code]",
                "value": "Population Density",
                "description": "Mappa della densità popolazione",
            },
            {
                "type": "donut_chart",
                "title": "Popolazione per Fascia d'Età",
                "category": "dim_age_group[age_group]",
                "value": "Total Population",
                "description": "Distribuzione per età",
            },
            {
                "type": "gauge",
                "title": "Tasso di Crescita",
                "value": "Population Growth Rate",
                "min_value": -0.05,
                "max_value": 0.05,
                "description": "Tasso crescita demografica annuale",
            },
        ]

    @staticmethod
    def get_economic_visualizations() -> List[Dict[str, Any]]:
        """Get visualizations for economic data."""
        return [
            {
                "type": "line_chart",
                "title": "PIL nel Tempo",
                "x_axis": "dim_time[year]",
                "y_axis": "SUM(fact_table[obs_value])",
                "legend": "dim_territory[territory_name]",
                "description": "Evoluzione PIL per territorio",
            },
            {
                "type": "waterfall_chart",
                "title": "Crescita PIL",
                "category": "dim_time[year]",
                "value": "GDP Growth",
                "description": "Contributi alla crescita PIL",
            },
            {
                "type": "scatter_chart",
                "title": "PIL vs Popolazione",
                "x_axis": "GDP Per Capita",
                "y_axis": "Total Population",
                "legend": "dim_territory[territory_name]",
                "description": "Relazione PIL pro-capite e popolazione",
            },
            {
                "type": "treemap",
                "title": "PIL per Settore",
                "category": "dim_sector[sector_name]",
                "value": "SUM(fact_table[obs_value])",
                "description": "Composizione PIL settoriale",
            },
        ]

    @staticmethod
    def get_employment_visualizations() -> List[Dict[str, Any]]:
        """Get visualizations for employment data."""
        return [
            {
                "type": "line_chart",
                "title": "Tasso di Occupazione",
                "x_axis": "dim_time[year]",
                "y_axis": "Employment Rate",
                "legend": "dim_territory[territory_name]",
                "description": "Trend occupazione per territorio",
            },
            {
                "type": "clustered_bar_chart",
                "title": "Occupazione per Età e Genere",
                "x_axis": "dim_age_group[age_group]",
                "y_axis": "Employment Rate",
                "legend": "dim_gender[gender]",
                "description": "Tasso occupazione demografico",
            },
            {
                "type": "funnel_chart",
                "title": "Percorso Occupazionale",
                "stages": ["Popolazione Attiva", "Occupati", "Disoccupati"],
                "values": ["Total Population", "Employment Rate", "Unemployment Rate"],
                "description": "Funnel del mercato del lavoro",
            },
        ]

    @classmethod
    def get_visualizations_for_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get visualizations for specific data category."""
        if category == "popolazione":
            return cls.get_population_visualizations()
        elif category == "economia":
            return cls.get_economic_visualizations()
        elif category == "lavoro":
            return cls.get_employment_visualizations()
        else:
            return cls.get_generic_visualizations()

    @staticmethod
    def get_generic_visualizations() -> List[Dict[str, Any]]:
        """Get generic visualizations for any data type."""
        return [
            {
                "type": "table",
                "title": "Dati Dettagliati",
                "columns": [
                    "dim_time[year]",
                    "dim_territory[territory_name]",
                    "fact_table[obs_value]",
                ],
                "description": "Tabella dati completa",
            },
            {
                "type": "card",
                "title": "Totale Osservazioni",
                "value": "Total Observations",
                "description": "Numero totale record",
            },
            {
                "type": "card",
                "title": "Qualità Media",
                "value": "Quality Score",
                "description": "Punteggio qualità dati",
            },
        ]


class PowerBIReport:
    """Represents a PowerBI report structure."""

    def __init__(self, name: str, pages: List[Dict[str, Any]]):
        self.name = name
        self.pages = pages

    def to_pbix_json(self) -> Dict[str, Any]:
        """Convert report to PowerBI JSON format."""
        return {
            "version": "4.0",
            "name": self.name,
            "pages": self.pages,
            "sections": [],
            "config": {
                "locale": "it-IT",
                "currency": "EUR",
                "dateFormat": "dd/MM/yyyy",
            },
        }


class TemplateGenerator:
    """
    Generates PowerBI templates (.pbit files) optimized for ISTAT data.

    Features:
    - Category-specific templates
    - Italian localization
    - Pre-configured star schema
    - DAX measures integration
    - Quality score visualization
    """

    def __init__(
        self,
        repository: Optional[UnifiedDataRepository] = None,
        optimizer: Optional[PowerBIOptimizer] = None,
    ):
        """Initialize template generator.

        Args:
            repository: Optional unified repository instance
            optimizer: Optional PowerBI optimizer instance
        """
        self.repository = repository or UnifiedDataRepository()
        self.optimizer = optimizer or PowerBIOptimizer(self.repository)
        self.viz_library = VisualizationLibrary()

        # Template storage path
        self.templates_path = Path("templates/powerbi")
        self.templates_path.mkdir(parents=True, exist_ok=True)

        logger.info("PowerBI Template Generator initialized")

    def generate_template(
        self,
        dataset_id: str,
        template_name: Optional[str] = None,
        custom_visualizations: Optional[List[Dict[str, Any]]] = None,
    ) -> PowerBITemplate:
        """Generate PowerBI template for ISTAT dataset.

        Args:
            dataset_id: ISTAT dataset identifier
            template_name: Optional custom template name
            custom_visualizations: Optional custom visualizations

        Returns:
            Generated PowerBITemplate

        Raises:
            ValueError: If dataset not found or invalid
        """
        try:
            # Get dataset metadata
            metadata = self.repository.get_dataset_complete(dataset_id)
            if not metadata:
                raise ValueError(f"Dataset {dataset_id} not found")

            # Generate star schema
            star_schema = self.optimizer.generate_star_schema(dataset_id)

            # Get DAX measures
            dax_measures = self.optimizer.dax_engine.get_standard_measures(dataset_id)

            # Get category-specific visualizations
            category = metadata.get("category", "general")
            visualizations = (
                custom_visualizations
                or self.viz_library.get_visualizations_for_category(category)
            )

            # Create template
            template = PowerBITemplate(
                template_id=f"template_{dataset_id}",
                name=template_name or f"Template {metadata.get('name', dataset_id)}",
                category=category,
                description=f"Template ottimizzato per dataset ISTAT {dataset_id}",
                star_schema=star_schema,
                dax_measures=dax_measures,
                visualizations=visualizations,
            )

            # Store template metadata for library access
            self._store_template_metadata(template, None)

            logger.info(f"Template generated for dataset {dataset_id}")
            return template

        except Exception as e:
            logger.error(f"Failed to generate template for {dataset_id}: {e}")
            raise

    def create_pbit_file(
        self,
        template: PowerBITemplate,
        output_path: Optional[Union[str, Path]] = None,
        include_sample_data: bool = False,
    ) -> Path:
        """Create PowerBI template (.pbit) file.

        Args:
            template: PowerBITemplate to convert
            output_path: Optional output file path
            include_sample_data: Whether to include sample data

        Returns:
            Path to created .pbit file
        """
        try:
            # Set default output path
            if not output_path:
                output_path = self.templates_path / f"{template.template_id}.pbit"
            else:
                output_path = Path(output_path)

            # Generate PowerBI report structure
            report = self._create_report_from_template(template)

            # Create data model
            data_model = self._create_data_model(
                template.star_schema, template.dax_measures
            )

            # Create .pbit file (which is a ZIP archive)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as pbit_file:
                # Add report definition
                pbit_file.writestr(
                    "Report/Layout",
                    json.dumps(report.to_pbix_json(), indent=2, ensure_ascii=False),
                )

                # Add data model
                pbit_file.writestr(
                    "DataModel", json.dumps(data_model, indent=2, ensure_ascii=False)
                )

                # Add metadata
                metadata = self._create_template_metadata(template)
                pbit_file.writestr(
                    "Metadata", json.dumps(metadata, indent=2, ensure_ascii=False)
                )

                # Add connection info
                connection = self._create_connection_info(template)
                pbit_file.writestr(
                    "Connections", json.dumps(connection, indent=2, ensure_ascii=False)
                )

                # Add sample data if requested
                if include_sample_data:
                    sample_data = self._get_sample_data(template)
                    pbit_file.writestr(
                        "Data/SampleData.json",
                        json.dumps(sample_data, indent=2, ensure_ascii=False),
                    )

            # Store template metadata in SQLite
            self._store_template_metadata(template, output_path)

            logger.info(f"PBIT file created: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to create PBIT file: {e}")
            raise

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates.

        Returns:
            List of template metadata dictionaries
        """
        try:
            # Get all datasets and check for PowerBI templates
            datasets = self.repository.list_datasets_complete()
            templates = []

            for dataset in datasets:
                dataset_id = dataset["dataset_id"]
                template_config = self.repository.metadata_manager.get_config(
                    f"dataset.{dataset_id}.powerbi_template"
                )

                if template_config:
                    try:
                        template_data = json.loads(template_config)
                        templates.append(
                            {
                                "dataset_id": dataset_id,
                                "template_id": template_data.get("template_id"),
                                "name": template_data.get("name"),
                                "category": template_data.get("category"),
                                "created_at": template_data.get("created_at"),
                                "description": template_data.get("description"),
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            return templates

        except Exception as e:
            logger.error(f"Failed to get available templates: {e}")
            return []

    def _create_report_from_template(self, template: PowerBITemplate) -> PowerBIReport:
        """Create PowerBI report from template."""
        # Create pages with visualizations
        pages = []

        # Main dashboard page
        main_page = {
            "name": "Dashboard Principale",
            "displayName": "Dashboard",
            "visualContainers": [],
        }

        # Add visualizations to main page
        for i, viz in enumerate(
            template.visualizations[:6]
        ):  # Limit to 6 visualizations per page
            viz_container = {
                "x": (i % 3) * 400,  # 3 columns
                "y": (i // 3) * 300,  # 2 rows
                "width": 380,
                "height": 280,
                "visual": self._create_visual_definition(viz, template),
            }
            main_page["visualContainers"].append(viz_container)

        pages.append(main_page)

        # Create additional pages if more visualizations
        if len(template.visualizations) > 6:
            detail_page = {
                "name": "Dettagli",
                "displayName": "Analisi Dettagliata",
                "visualContainers": [],
            }

            for i, viz in enumerate(template.visualizations[6:]):
                viz_container = {
                    "x": (i % 2) * 500,  # 2 columns for detail page
                    "y": (i // 2) * 400,  # Larger visualizations
                    "width": 480,
                    "height": 380,
                    "visual": self._create_visual_definition(viz, template),
                }
                detail_page["visualContainers"].append(viz_container)

            pages.append(detail_page)

        return PowerBIReport(template.name, pages)

    def _create_visual_definition(
        self, viz: Dict[str, Any], template: PowerBITemplate
    ) -> Dict[str, Any]:
        """Create PowerBI visual definition from visualization spec."""
        return {
            "visualType": viz["type"],
            "title": viz["title"],
            "description": viz.get("description", ""),
            "projections": {
                "Category": [{"queryRef": viz.get("x_axis", "")}],
                "Values": [{"queryRef": viz.get("y_axis", "")}],
                "Legend": [{"queryRef": viz.get("legend", "")}]
                if viz.get("legend")
                else [],
            },
            "formatting": {
                "general": {"locale": "it-IT"},
                "title": {
                    "show": True,
                    "text": viz["title"],
                    "fontSize": 14,
                    "fontColor": "#333333",
                },
            },
        }

    def _create_data_model(
        self, star_schema: StarSchemaDefinition, dax_measures: Dict[str, str]
    ) -> Dict[str, Any]:
        """Create PowerBI data model definition."""
        return {
            "name": "ISTATDataModel",
            "tables": self._create_table_definitions(star_schema),
            "relationships": star_schema.relationships,
            "measures": [
                {
                    "name": name,
                    "expression": expression,
                    "formatString": "#,##0" if "rate" not in name.lower() else "0.00%",
                }
                for name, expression in dax_measures.items()
            ],
            "roles": [],
            "cultures": [{"name": "it-IT", "displayName": "Italiano (Italia)"}],
        }

    def _create_table_definitions(
        self, star_schema: StarSchemaDefinition
    ) -> List[Dict[str, Any]]:
        """Create table definitions for star schema."""
        tables = []

        # Add fact table (using string formatting for PowerBI template, not SQL execution)
        tables.append(
            {
                "name": star_schema.fact_table,
                "source": "SELECT * FROM {}".format(
                    star_schema.fact_table
                ),  # nosec B608
                "columns": self._get_standard_fact_columns(),
            }
        )

        # Add dimension tables (using string formatting for PowerBI template, not SQL execution)
        for dim_table in star_schema.dimension_tables:
            tables.append(
                {
                    "name": dim_table,
                    "source": "SELECT * FROM {}".format(dim_table),  # nosec B608
                    "columns": self._get_dimension_columns(dim_table),
                }
            )

        return tables

    def _get_standard_fact_columns(self) -> List[Dict[str, Any]]:
        """Get standard fact table columns."""
        return [
            {"name": "id", "dataType": "int64", "isKey": True},
            {"name": "time_key", "dataType": "int64"},
            {"name": "territory_key", "dataType": "int64"},
            {"name": "measure_key", "dataType": "int64"},
            {"name": "obs_value", "dataType": "double"},
            {"name": "quality_score", "dataType": "double"},
            {"name": "last_updated", "dataType": "dateTime"},
        ]

    def _get_dimension_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for dimension table."""
        base_columns = [
            {"name": f"{table_name}_key", "dataType": "int64", "isKey": True}
        ]

        if "time" in table_name:
            base_columns.extend(
                [
                    {"name": "year", "dataType": "int64"},
                    {"name": "time_period", "dataType": "string"},
                    {"name": "date", "dataType": "dateTime"},
                ]
            )
        elif "territory" in table_name:
            base_columns.extend(
                [
                    {"name": "territory_code", "dataType": "string"},
                    {"name": "territory_name", "dataType": "string"},
                    {"name": "region", "dataType": "string"},
                    {"name": "area_km2", "dataType": "double"},
                ]
            )
        else:
            # Generic dimension columns
            base_columns.extend(
                [
                    {"name": "name", "dataType": "string"},
                    {"name": "description", "dataType": "string"},
                ]
            )

        return base_columns

    def _create_template_metadata(self, template: PowerBITemplate) -> Dict[str, Any]:
        """Create template metadata."""
        return {
            "version": "1.0",
            "created": template.created_at.isoformat(),
            "author": "Osservatorio ISTAT Platform",
            "description": template.description,
            "category": template.category,
            "locale": "it-IT",
            "datasetId": template.template_id,
            "optimizedFor": "PowerBI Desktop",
            "requirements": {
                "minPowerBIVersion": "2.0",
                "dataConnector": "SQLite + DuckDB",
            },
        }

    def _create_connection_info(self, template: PowerBITemplate) -> Dict[str, Any]:
        """Create connection information."""
        return {
            "connections": [
                {
                    "name": "ISTAT_SQLite_Metadata",
                    "connectionString": "Data Source=data/databases/osservatorio_metadata.db",
                    "provider": "System.Data.SQLite",
                },
                {
                    "name": "ISTAT_DuckDB_Analytics",
                    "connectionString": "Data Source=data/databases/osservatorio.duckdb",
                    "provider": "DuckDB.NET",
                },
            ],
            "refreshPolicy": {
                "enabled": True,
                "frequency": "daily",
                "incrementalRefresh": True,
            },
        }

    def _get_sample_data(self, template: PowerBITemplate) -> Dict[str, Any]:
        """Get sample data for template."""
        try:
            # This would retrieve actual sample data from the database
            # For now, return empty structure
            return {
                "sampleData": {},
                "note": "Sample data can be loaded from the configured data sources",
            }
        except Exception:
            return {"sampleData": {}}

    def _store_template_metadata(
        self, template: PowerBITemplate, file_path: Path = None
    ) -> None:
        """Store template metadata in SQLite."""
        try:
            template_data = template.to_dict()
            template_data["file_path"] = str(file_path) if file_path else None

            # Extract dataset_id from template_id (assuming format "template_{dataset_id}")
            dataset_id = template.template_id.replace("template_", "")

            self.repository.metadata_manager.set_config(
                f"dataset.{dataset_id}.powerbi_template", json.dumps(template_data)
            )

            logger.info(f"Template metadata stored for {dataset_id}")

        except Exception as e:
            logger.error(f"Failed to store template metadata: {e}")
