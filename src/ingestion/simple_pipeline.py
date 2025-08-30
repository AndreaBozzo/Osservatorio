"""
Simple Ingestion Pipeline - Issue #149
Startup-first approach: simple, readable code with minimal abstraction.

Focus on 7 priority ISTAT datasets with clear scalability path for:
- Additional datasets (8, 9, 10...)
- Additional data sources (APIs beyond ISTAT)
- Additional processing (validation, transformation)
- Additional scheduling (cron, queues)

Key principle: Start simple, iterate based on real needs vs. anticipated complexity.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

from ..api.production_istat_client import ProductionIstatClient
from ..database.duckdb.manager import get_manager
from ..database.sqlite.repository import UnifiedDataRepository
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SimpleIngestionPipeline:
    """
    Simple, scalable ingestion pipeline for ISTAT datasets.

    Design principles:
    - Hardcoded priority datasets for MVP reliability
    - Direct API integration with error handling
    - Direct DuckDB storage without abstraction layers
    - Clear extension points for future needs
    """

    # 7 Priority datasets for MVP - with SDMX parameters that work
    PRIORITY_DATASETS = {
        "101_1015": "Coltivazioni",  # Agricultural data - likely works without complex filters
        "144_107": "Foi – weights until 2010",  # Simple price index data
        "115_333": "Indice della produzione industriale",  # Industrial production
        "120_337": "Indice delle vendite del commercio al dettaglio",  # Retail sales
        "143_222": "Indice dei prezzi all'importazione - dati mensili",  # Import prices
        "145_360": "Prezzi alla produzione dell'industria",  # Producer prices
        "149_319": "Tensione contrattuale",  # Contract tension
    }

    def __init__(self, istat_client: Optional[ProductionIstatClient] = None):
        """Initialize with minimal dependencies."""
        self.istat_client = istat_client or ProductionIstatClient()
        self.duckdb_manager = get_manager()  # Use singleton
        self.repository = UnifiedDataRepository()
        self.ingestion_status = {
            "last_run": None,
            "datasets_processed": {},
            "errors": [],
            "total_records": 0,
        }

        # Ensure schema exists on initialization
        self._ensure_schema_tables_exist_sync()
        logger.info("SimpleIngestionPipeline initialized")

    async def ingest_all_priority_datasets(self) -> dict[str, Any]:
        """
        Ingest all 7 priority datasets.

        Returns:
            Comprehensive ingestion results
        """
        logger.info("Starting ingestion of all 7 priority datasets")
        start_time = datetime.utcnow()
        results = {}
        total_success = 0
        total_errors = 0

        for dataset_id, description in self.PRIORITY_DATASETS.items():
            logger.info(f"Processing {dataset_id}: {description}")

            try:
                result = await self.ingest_single_dataset(dataset_id)
                results[dataset_id] = result

                if result["success"]:
                    total_success += 1
                    logger.info(
                        f"✅ {dataset_id} ingested successfully ({result['records_processed']} records)"
                    )
                else:
                    total_errors += 1
                    logger.error(f"❌ {dataset_id} failed: {result['error']}")

            except Exception as e:
                total_errors += 1
                error_msg = f"Critical error processing {dataset_id}: {str(e)}"
                logger.error(error_msg)
                results[dataset_id] = {
                    "success": False,
                    "error": error_msg,
                    "records_processed": 0,
                }
                self.ingestion_status["errors"].append(
                    {
                        "dataset_id": dataset_id,
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        # Update status tracking
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        self.ingestion_status.update(
            {
                "last_run": end_time.isoformat(),
                "datasets_processed": results,
                "duration_seconds": duration,
            }
        )

        summary = {
            "success": total_errors == 0,
            "total_datasets": len(self.PRIORITY_DATASETS),
            "successful": total_success,
            "failed": total_errors,
            "duration_seconds": duration,
            "results": results,
            "timestamp": end_time.isoformat(),
        }

        logger.info(
            f"Batch ingestion completed: {total_success}/{len(self.PRIORITY_DATASETS)} successful"
        )
        return summary

    async def ingest_single_dataset(
        self, dataset_id: str, retries: int = 3
    ) -> dict[str, Any]:
        """
        Ingest a single dataset with retry logic.

        Extensible design for future:
        - Additional data sources (non-ISTAT APIs)
        - Custom processing logic per dataset
        - Different storage destinations

        Args:
            dataset_id: ISTAT dataset identifier
            retries: Number of retry attempts

        Returns:
            Ingestion result with success status and metrics
        """
        logger.info(f"Starting ingestion for dataset: {dataset_id}")

        # Step 0: Check if dataset is already up-to-date (skip logic)
        try:
            existing_dataset = self.repository.dataset_manager.get_dataset(dataset_id)
            if existing_dataset and existing_dataset.get("is_active") == 1:
                # Check if data exists in DuckDB
                with self.duckdb_manager.get_connection() as conn:
                    duckdb_count = conn.execute(
                        f"SELECT COUNT(*) as count FROM main.istat_observations WHERE dataset_id = '{dataset_id}'"
                    ).df()
                existing_count = int(
                    duckdb_count.iloc[0]["count"] if len(duckdb_count) > 0 else 0
                )

                if existing_count > 0:
                    logger.info(
                        f"⏭️ Skipping {dataset_id}: {existing_count:,} records already exist (last updated: {existing_dataset.get('last_updated', 'unknown')})"
                    )
                    return {
                        "success": True,
                        "dataset_id": dataset_id,
                        "records_processed": 0,
                        "skipped": True,
                        "existing_records": existing_count,
                        "reason": "Dataset already exists and is up-to-date",
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "cached",
                    }
        except Exception as e:
            logger.debug(
                f"Skip check failed for {dataset_id}, proceeding with ingestion: {e}"
            )

        for attempt in range(retries + 1):
            try:
                # Step 1: Fetch data from ISTAT API
                logger.debug(
                    f"Attempt {attempt + 1}/{retries + 1} - Fetching {dataset_id}"
                )
                response = self.istat_client.fetch_dataset(dataset_id)

                logger.info(
                    f"ISTAT response keys for {dataset_id}: {list(response.keys()) if isinstance(response, dict) else type(response)}"
                )
                logger.info(f"ISTAT response type: {type(response)}")
                if isinstance(response, dict) and len(str(response)) < 500:
                    logger.info(f"Full ISTAT response for {dataset_id}: {response}")

                # Handle different response formats
                if isinstance(response, dict):
                    if response.get("success") is False:
                        error_msg = response.get(
                            "error_message", "API returned success=False"
                        )
                        logger.error(f"ISTAT API failed for {dataset_id}: {error_msg}")
                        raise Exception(f"ISTAT API error: {error_msg}")
                    # If success is None or True, continue
                elif response is None:
                    logger.error(f"ISTAT API returned None for {dataset_id}")
                    raise Exception("ISTAT API returned None")
                else:
                    logger.error(
                        f"ISTAT API returned unexpected type {type(response)} for {dataset_id}"
                    )
                    raise Exception(f"Unexpected response type: {type(response)}")

                # Extract data from ProductionIstatClient response
                data_section = response.get("data")
                if not data_section:
                    logger.error(
                        f"Empty/missing data section for {dataset_id}. Response keys: {list(response.keys())}"
                    )
                    raise Exception("Empty data section received from ISTAT API")

                # Check for ISTAT API errors
                if (
                    isinstance(data_section, dict)
                    and data_section.get("status") == "error"
                ):
                    istat_error = data_section.get("error", "Unknown ISTAT error")
                    logger.error(f"ISTAT API error for {dataset_id}: {istat_error}")
                    raise Exception(f"ISTAT API error: {istat_error}")

                # Handle different data formats - UPDATED for real XML processing
                if (
                    isinstance(data_section, dict)
                    and data_section.get("status") == "success"
                ):
                    # Get actual XML content from ProductionIstatClient
                    xml_content = data_section.get("content")
                    data_size = data_section.get("size", 0)

                    if xml_content:
                        logger.info(
                            f"Processing XML data for {dataset_id} (size: {data_size} bytes)"
                        )
                        sdmx_data = xml_content
                    else:
                        logger.warning(
                            f"No XML content in successful response for {dataset_id}"
                        )
                        # Fallback: still process but with limited data
                        sdmx_data = f'<GenericData><DataSet id="{dataset_id}"><Obs/></DataSet></GenericData>'

                elif isinstance(data_section, str):
                    sdmx_data = data_section
                else:
                    logger.error(
                        f"Unexpected data format for {dataset_id}: {type(data_section)}"
                    )
                    raise Exception(f"Unexpected data format: {type(data_section)}")

                # Step 2: Store in DuckDB (direct, no abstraction layers)
                records_processed = await self._store_in_duckdb(dataset_id, sdmx_data)

                # Step 3: Update metadata in SQLite
                await self._update_dataset_metadata(dataset_id, records_processed)

                logger.info(
                    f"✅ {dataset_id} ingested successfully: {records_processed} records"
                )
                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "records_processed": records_processed,
                    "attempt": attempt + 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_source": "istat_api",
                }

            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                logger.warning(error_msg)

                if attempt == retries:  # Last attempt failed
                    logger.error(
                        f"❌ All {retries + 1} attempts failed for {dataset_id}"
                    )
                    return {
                        "success": False,
                        "dataset_id": dataset_id,
                        "error": str(e),
                        "attempts": retries + 1,
                        "records_processed": 0,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                # Wait before retry (exponential backoff)
                wait_time = (2**attempt) * 1  # 1s, 2s, 4s
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        # Should never reach here
        return {"success": False, "error": "Unexpected retry loop exit"}

    async def _store_in_duckdb(self, dataset_id: str, sdmx_data: str) -> int:
        """
        Store SDMX data directly in DuckDB.

        Future extensibility:
        - Custom schemas per dataset type
        - Data transformation pipelines
        - Multiple storage formats (Parquet, Delta, etc.)
        """
        try:
            # Parse SDMX data (simplified XML parsing)
            records = await self._parse_sdmx_simple(sdmx_data, dataset_id)

            if not records:
                logger.warning(f"No records parsed from {dataset_id}")
                return 0

            # Ensure schema tables exist before insertion
            await self._ensure_schema_tables_exist()

            # Direct DuckDB insertion - convert records to DataFrame
            import pandas as pd

            if records:
                df = pd.DataFrame(records)
                # Use unified observations table instead of per-dataset tables
                table_name = "main.istat_observations"

                # Use DuckDBManager's bulk_insert method
                self.duckdb_manager.bulk_insert(table_name, df)
                logger.info(
                    f"Successfully inserted {len(records)} records into {table_name}"
                )
            else:
                logger.warning(f"No records to insert for {dataset_id}")

            self.ingestion_status["total_records"] += len(records)
            return len(records)

        except Exception as e:
            logger.error(f"DuckDB storage failed for {dataset_id}: {e}")
            raise

    async def _parse_sdmx_simple(
        self, sdmx_data: str, dataset_id: str
    ) -> list[dict[str, Any]]:
        """
        Enhanced SDMX parsing for real ISTAT data.

        Handles both SDMX 2.1 GenericData and compact formats.
        """
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(sdmx_data)
            records = []

            # SDMX 2.1 namespace handling
            namespaces = {
                "gen": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
                "mes": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
                "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/compact",
            }

            # Try different SDMX observation patterns
            observation_patterns = [
                # Generic format
                ".//gen:Obs",
                ".//generic:Obs",
                ".//Obs",
                # Compact format
                ".//com:Observation",
                ".//Observation",
                # Fallback patterns
                ".//*[local-name()='Obs']",
                ".//*[local-name()='Observation']",
                ".//*[@TIME_PERIOD]",
                ".//*[@obsValue]",
            ]

            observations = []
            for pattern in observation_patterns:
                try:
                    obs_found = root.findall(pattern, namespaces)
                    if obs_found:
                        observations = obs_found
                        logger.debug(
                            f"Found {len(observations)} observations using pattern: {pattern}"
                        )
                        break
                except Exception:
                    continue

            if not observations:
                logger.warning(
                    f"No observations found in {dataset_id} with standard patterns"
                )
                # Try to find any element with numeric content as fallback
                observations = [
                    elem
                    for elem in root.iter()
                    if elem.text
                    and elem.text.replace(".", "").replace("-", "").isdigit()
                ]
                logger.info(f"Fallback: found {len(observations)} numeric elements")

            for i, obs in enumerate(observations):
                if i > 10000:  # Limit for performance
                    logger.warning(
                        f"Limiting to first 10000 observations from {dataset_id}"
                    )
                    break

                # Extract values from SDMX Generic format
                obs_value = None
                time_period = None
                additional_attributes = {}

                # For SDMX Generic format, values are in child element attributes
                for child in obs:
                    child_tag = (
                        child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    )
                    child_attrs = child.attrib

                    # ObsValue contains the observation value
                    if child_tag == "ObsValue":
                        obs_value = child_attrs.get("value")

                    # ObsDimension with id="TIME_PERIOD" contains the time period
                    elif child_tag == "ObsDimension":
                        if child_attrs.get("id") == "TIME_PERIOD":
                            time_period = child_attrs.get("value")

                    # Store all child attributes in additional_attributes
                    for attr_key, attr_value in child_attrs.items():
                        additional_attributes[
                            f"{child_tag.lower()}_{attr_key.lower()}"
                        ] = attr_value

                # Also check direct attributes of Obs element (fallback)
                for key, value in obs.attrib.items():
                    if "value" in key.lower() or key == "obsValue":
                        obs_value = obs_value or value
                    if "time" in key.lower() or "period" in key.lower():
                        time_period = time_period or value
                    additional_attributes[f"obs_{key.lower()}"] = value

                # Add element text if available
                if obs.text and not obs_value:
                    additional_attributes["raw_text"] = obs.text

                # Create record with fixed structure + JSON for additional data
                record = {
                    "dataset_id": dataset_id,
                    "record_id": i,
                    "ingestion_timestamp": datetime.utcnow().isoformat(),
                    "obs_value": obs_value or "",
                    "time_period": time_period or "",
                    "additional_attributes": additional_attributes
                    if additional_attributes
                    else None,
                }

                records.append(record)

            logger.info(
                f"Successfully parsed {len(records)} observations from {dataset_id}"
            )
            return records

        except ET.ParseError as e:
            logger.error(f"XML parsing failed for {dataset_id}: {e}")
            # Create a single error record
            return [
                {
                    "dataset_id": dataset_id,
                    "parse_error": str(e),
                    "raw_data_sample": sdmx_data[:500],
                    "ingestion_timestamp": datetime.utcnow().isoformat(),
                }
            ]

        except Exception as e:
            logger.error(f"SDMX parsing failed for {dataset_id}: {e}")
            raise

    async def _ensure_schema_tables_exist(self):
        """Ensure DuckDB schema tables exist before insertion."""
        try:
            # Create simple table structure for ingestion pipeline
            # Use direct SQL to avoid potential schema manager issues
            with self.duckdb_manager.get_connection() as conn:
                # Create main schema
                conn.execute("CREATE SCHEMA IF NOT EXISTS main;")

                # Create flexible observations table with JSON for additional attributes
                create_observations_sql = """
                CREATE TABLE IF NOT EXISTS main.istat_observations (
                    dataset_id VARCHAR,
                    record_id INTEGER,
                    ingestion_timestamp VARCHAR,
                    obs_value VARCHAR,
                    time_period VARCHAR,
                    additional_attributes JSON
                );
                """

                # Create sequence first
                conn.execute("CREATE SEQUENCE IF NOT EXISTS obs_id_seq;")
                conn.execute(create_observations_sql)

                logger.debug("DuckDB observations table verified/created")

        except Exception as e:
            logger.error(f"Failed to ensure schema tables exist: {e}")
            raise

    def _ensure_schema_tables_exist_sync(self):
        """Ensure DuckDB schema tables exist before insertion (sync version)."""
        try:
            # Create simple table structure for ingestion pipeline
            # Use direct SQL to avoid potential schema manager issues
            with self.duckdb_manager.get_connection() as conn:
                # Create main schema
                conn.execute("CREATE SCHEMA IF NOT EXISTS main;")

                # Create flexible observations table with JSON for additional attributes
                create_observations_sql = """
                CREATE TABLE IF NOT EXISTS main.istat_observations (
                    dataset_id VARCHAR,
                    record_id INTEGER,
                    ingestion_timestamp VARCHAR,
                    obs_value VARCHAR,
                    time_period VARCHAR,
                    additional_attributes JSON
                );
                """

                # Create sequence first
                conn.execute("CREATE SEQUENCE IF NOT EXISTS obs_id_seq;")
                conn.execute(create_observations_sql)

                logger.debug("DuckDB observations table verified/created (sync)")

        except Exception as e:
            logger.error(f"Failed to ensure schema tables exist (sync): {e}")
            raise

    async def _update_dataset_metadata(self, dataset_id: str, records_count: int):
        """Update dataset metadata in SQLite repository."""
        try:
            metadata = {
                "dataset_id": dataset_id,
                "description": self.PRIORITY_DATASETS.get(
                    dataset_id, "Unknown dataset"
                ),
                "last_updated": datetime.utcnow().isoformat(),
                "records_count": records_count,
                "status": "active" if records_count > 0 else "empty",
                "data_source": "istat_api",
            }

            # Simplified metadata logging for MVP - skip repository update for now
            logger.info(f"Dataset metadata for {dataset_id}: {metadata}")
            logger.debug(
                f"Metadata logged for {dataset_id} (repository update skipped for MVP)"
            )

        except Exception as e:
            logger.warning(f"Metadata update failed for {dataset_id}: {e}")
            # Non-critical error - don't fail the ingestion

    def get_ingestion_status(self) -> dict[str, Any]:
        """
        Get current ingestion status and metrics.

        Extensible for future monitoring:
        - Performance metrics
        - Queue status
        - Health checks
        - Alerting integration
        """
        return {
            "pipeline_status": "healthy"
            if not self.ingestion_status["errors"]
            else "degraded",
            "priority_datasets": list(self.PRIORITY_DATASETS.keys()),
            "last_run": self.ingestion_status["last_run"],
            "total_datasets": len(self.PRIORITY_DATASETS),
            "total_records_ingested": self.ingestion_status["total_records"],
            "recent_errors": self.ingestion_status["errors"][-5:],  # Last 5 errors
            "datasets_status": self.ingestion_status["datasets_processed"],
            "system_info": {
                "duckdb_connected": self.duckdb_manager is not None,
                "istat_client_ready": self.istat_client is not None,
                "repository_ready": self.repository is not None,
            },
        }

    async def health_check(self) -> dict[str, Any]:
        """Simple health check for monitoring."""
        try:
            # Test DuckDB connection (simplified check)
            duckdb_healthy = self.duckdb_manager is not None

            # Test ISTAT client (without making actual API call)
            istat_healthy = hasattr(self.istat_client, "fetch_dataset")

            # Test repository
            repository_healthy = self.repository is not None

            all_healthy = duckdb_healthy and istat_healthy and repository_healthy

            return {
                "healthy": all_healthy,
                "components": {
                    "duckdb": duckdb_healthy,
                    "istat_client": istat_healthy,
                    "repository": repository_healthy,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Factory function for easy integration
def create_simple_pipeline() -> SimpleIngestionPipeline:
    """Create a simple ingestion pipeline instance."""
    return SimpleIngestionPipeline()


# Extension point for future data sources
class DataSourceAdapter:
    """Abstract adapter for extending to non-ISTAT data sources."""

    async def fetch_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Override this method for different data sources."""
        raise NotImplementedError

    def get_priority_datasets(self) -> dict[str, str]:
        """Override to define datasets for each source."""
        raise NotImplementedError


# Example extension for future use
class EurostatAdapter(DataSourceAdapter):
    """Future extension example for Eurostat data."""

    def get_priority_datasets(self) -> dict[str, str]:
        return {
            "EUROSTAT_DEMO": "European demographic data",
            # Add more Eurostat datasets as needed
        }

    async def fetch_dataset(self, dataset_id: str) -> dict[str, Any]:
        # Future implementation for Eurostat API
        pass
