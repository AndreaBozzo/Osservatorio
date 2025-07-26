"""
OData v4 Endpoint for PowerBI Direct Query Integration

Implements OData v4 protocol for seamless PowerBI Direct Query connectivity.
Provides standardized REST interface for business intelligence tools.

Features:
- OData v4 compliant metadata and query endpoints
- PowerBI optimized entity models
- Efficient query translation to DuckDB
- Automatic pagination and filtering
- Performance optimizations for large datasets

Performance target: <500ms for 10k records
"""

import json
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, PlainTextResponse

from src.database.sqlite.repository import get_unified_repository
from src.utils.logger import get_logger

from .dependencies import (
    check_rate_limit,
    get_current_user,
    get_repository,
    log_api_request,
)
from .models import ODataEntitySet, ODataMetadata, ODataResponse

logger = get_logger(__name__)

# OData v4 constants
ODATA_VERSION = "4.0"
ODATA_NAMESPACE = "Osservatorio.ISTAT"
ODATA_CONTAINER = "ISTATDataContainer"


def create_odata_router() -> APIRouter:
    """Create OData v4 router for PowerBI integration"""

    router = APIRouter()

    @router.get("/", response_class=PlainTextResponse, summary="OData Service Document")
    async def odata_service_document(request: Request):
        """
        OData v4 service document listing available entity sets.

        This is the entry point for OData clients like PowerBI.
        Returns a JSON document describing available data entities.
        """
        try:
            base_url = str(request.base_url).rstrip("/") + "/odata"

            service_doc = {
                "@odata.context": f"{base_url}/$metadata",
                "value": [
                    {"name": "Datasets", "kind": "EntitySet", "url": "Datasets"},
                    {
                        "name": "Observations",
                        "kind": "EntitySet",
                        "url": "Observations",
                    },
                    {"name": "Territories", "kind": "EntitySet", "url": "Territories"},
                    {"name": "Measures", "kind": "EntitySet", "url": "Measures"},
                ],
            }

            return JSONResponse(
                content=service_doc,
                headers={
                    "OData-Version": ODATA_VERSION,
                    "Content-Type": "application/json;odata.metadata=minimal",
                },
            )

        except Exception as e:
            logger.error(f"Failed to generate OData service document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate service document",
            )

    @router.get("/$metadata", response_class=PlainTextResponse)
    async def odata_metadata(request: Request):
        """
        OData v4 metadata document (CSDL) describing the data model.

        This XML document defines the entity types, properties, and relationships
        that PowerBI uses to understand the data structure.
        """
        try:
            base_url = str(request.base_url).rstrip("/") + "/odata"

            # Create CSDL XML document
            edmx = Element(
                "edmx:Edmx",
                {
                    "Version": "4.0",
                    "xmlns:edmx": "http://docs.oasis-open.org/odata/ns/edmx",
                },
            )

            # Data Services
            data_services = SubElement(edmx, "edmx:DataServices")

            # Schema
            schema = SubElement(
                data_services,
                "Schema",
                {
                    "Namespace": ODATA_NAMESPACE,
                    "xmlns": "http://docs.oasis-open.org/odata/ns/edm",
                },
            )

            # Dataset EntityType
            dataset_type = SubElement(schema, "EntityType", {"Name": "Dataset"})
            dataset_key = SubElement(dataset_type, "Key")
            SubElement(dataset_key, "PropertyRef", {"Name": "DatasetId"})
            SubElement(
                dataset_type,
                "Property",
                {"Name": "DatasetId", "Type": "Edm.String", "Nullable": "false"},
            )
            SubElement(dataset_type, "Property", {"Name": "Name", "Type": "Edm.String"})
            SubElement(
                dataset_type, "Property", {"Name": "Category", "Type": "Edm.String"}
            )
            SubElement(
                dataset_type, "Property", {"Name": "Description", "Type": "Edm.String"}
            )
            SubElement(
                dataset_type, "Property", {"Name": "IstatAgency", "Type": "Edm.String"}
            )
            SubElement(
                dataset_type, "Property", {"Name": "Priority", "Type": "Edm.Int32"}
            )
            SubElement(
                dataset_type, "Property", {"Name": "RecordCount", "Type": "Edm.Int64"}
            )
            SubElement(
                dataset_type, "Property", {"Name": "MinYear", "Type": "Edm.Int32"}
            )
            SubElement(
                dataset_type, "Property", {"Name": "MaxYear", "Type": "Edm.Int32"}
            )
            SubElement(
                dataset_type,
                "Property",
                {"Name": "TerritoryCount", "Type": "Edm.Int32"},
            )
            SubElement(
                dataset_type, "Property", {"Name": "MeasureCount", "Type": "Edm.Int32"}
            )
            SubElement(
                dataset_type,
                "Property",
                {"Name": "CreatedAt", "Type": "Edm.DateTimeOffset"},
            )
            SubElement(
                dataset_type,
                "Property",
                {"Name": "UpdatedAt", "Type": "Edm.DateTimeOffset"},
            )

            # Observation EntityType
            obs_type = SubElement(schema, "EntityType", {"Name": "Observation"})
            obs_key = SubElement(obs_type, "Key")
            SubElement(obs_key, "PropertyRef", {"Name": "Id"})
            SubElement(
                obs_type,
                "Property",
                {"Name": "Id", "Type": "Edm.Int64", "Nullable": "false"},
            )
            SubElement(
                obs_type, "Property", {"Name": "DatasetId", "Type": "Edm.String"}
            )
            SubElement(obs_type, "Property", {"Name": "Year", "Type": "Edm.Int32"})
            SubElement(
                obs_type, "Property", {"Name": "TimePeriod", "Type": "Edm.String"}
            )
            SubElement(
                obs_type, "Property", {"Name": "TerritoryCode", "Type": "Edm.String"}
            )
            SubElement(
                obs_type, "Property", {"Name": "TerritoryName", "Type": "Edm.String"}
            )
            SubElement(
                obs_type, "Property", {"Name": "MeasureCode", "Type": "Edm.String"}
            )
            SubElement(
                obs_type, "Property", {"Name": "MeasureName", "Type": "Edm.String"}
            )
            SubElement(obs_type, "Property", {"Name": "ObsValue", "Type": "Edm.Double"})
            SubElement(
                obs_type, "Property", {"Name": "ObsStatus", "Type": "Edm.String"}
            )

            # Territory EntityType
            territory_type = SubElement(schema, "EntityType", {"Name": "Territory"})
            territory_key = SubElement(territory_type, "Key")
            SubElement(territory_key, "PropertyRef", {"Name": "TerritoryCode"})
            SubElement(
                territory_type,
                "Property",
                {"Name": "TerritoryCode", "Type": "Edm.String", "Nullable": "false"},
            )
            SubElement(
                territory_type,
                "Property",
                {"Name": "TerritoryName", "Type": "Edm.String"},
            )
            SubElement(
                territory_type, "Property", {"Name": "Level", "Type": "Edm.String"}
            )
            SubElement(
                territory_type, "Property", {"Name": "ParentCode", "Type": "Edm.String"}
            )

            # Measure EntityType
            measure_type = SubElement(schema, "EntityType", {"Name": "Measure"})
            measure_key = SubElement(measure_type, "Key")
            SubElement(measure_key, "PropertyRef", {"Name": "MeasureCode"})
            SubElement(
                measure_type,
                "Property",
                {"Name": "MeasureCode", "Type": "Edm.String", "Nullable": "false"},
            )
            SubElement(
                measure_type, "Property", {"Name": "MeasureName", "Type": "Edm.String"}
            )
            SubElement(measure_type, "Property", {"Name": "Unit", "Type": "Edm.String"})
            SubElement(
                measure_type, "Property", {"Name": "DataType", "Type": "Edm.String"}
            )

            # Entity Container
            container = SubElement(schema, "EntityContainer", {"Name": ODATA_CONTAINER})

            SubElement(
                container,
                "EntitySet",
                {"Name": "Datasets", "EntityType": f"{ODATA_NAMESPACE}.Dataset"},
            )

            SubElement(
                container,
                "EntitySet",
                {
                    "Name": "Observations",
                    "EntityType": f"{ODATA_NAMESPACE}.Observation",
                },
            )

            SubElement(
                container,
                "EntitySet",
                {"Name": "Territories", "EntityType": f"{ODATA_NAMESPACE}.Territory"},
            )

            SubElement(
                container,
                "EntitySet",
                {"Name": "Measures", "EntityType": f"{ODATA_NAMESPACE}.Measure"},
            )

            # Convert to string
            xml_string = tostring(edmx, encoding="unicode")

            return PlainTextResponse(
                content=xml_string,
                headers={
                    "OData-Version": ODATA_VERSION,
                    "Content-Type": "application/xml",
                },
            )

        except Exception as e:
            logger.error(f"Failed to generate OData metadata: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate metadata document",
            )

    @router.get("/Datasets", summary="OData Datasets Entity Set")
    async def odata_datasets(
        request: Request,
        top: Optional[int] = Query(
            None, alias="$top", description="Number of records to return"
        ),
        skip: Optional[int] = Query(
            None, alias="$skip", description="Number of records to skip"
        ),
        filter: Optional[str] = Query(
            None, alias="$filter", description="Filter expression"
        ),
        select: Optional[str] = Query(
            None, alias="$select", description="Properties to select"
        ),
        orderby: Optional[str] = Query(
            None, alias="$orderby", description="Order by expression"
        ),
        count: Optional[bool] = Query(
            None, alias="$count", description="Include count in response"
        ),
        repository=Depends(get_repository),
        current_user=Depends(get_current_user),
        _rate_limit=Depends(check_rate_limit),
        _audit=Depends(log_api_request),
    ):
        """
        OData Datasets entity set for PowerBI Direct Query.

        Supports standard OData query options:
        - $top: Limit number of results
        - $skip: Skip number of results (pagination)
        - $filter: Filter results (e.g., Category eq 'Demographics')
        - $select: Select specific properties
        - $orderby: Order results
        - $count: Include total count
        """
        try:
            base_url = str(request.base_url).rstrip("/") + "/odata"

            # Get datasets from repository
            datasets = repository.list_datasets_complete()

            # Apply OData filters
            filtered_datasets = (
                _apply_odata_filter(datasets, filter) if filter else datasets
            )

            # Apply ordering
            if orderby:
                filtered_datasets = _apply_odata_orderby(filtered_datasets, orderby)

            # Apply pagination
            total_count = len(filtered_datasets)
            if skip:
                filtered_datasets = filtered_datasets[skip:]
            if top:
                filtered_datasets = filtered_datasets[:top]

            # Convert to OData format
            odata_records = []
            for dataset in filtered_datasets:
                analytics_stats = dataset.get("analytics_stats", {})

                record = {
                    "DatasetId": dataset["dataset_id"],
                    "Name": dataset["name"],
                    "Category": dataset["category"],
                    "Description": dataset.get("description"),
                    "IstatAgency": dataset.get("istat_agency"),
                    "Priority": dataset.get("priority", 5),
                    "RecordCount": analytics_stats.get("record_count", 0),
                    "MinYear": analytics_stats.get("min_year"),
                    "MaxYear": analytics_stats.get("max_year"),
                    "TerritoryCount": analytics_stats.get("territory_count", 0),
                    "MeasureCount": analytics_stats.get("measure_count", 0),
                    "CreatedAt": dataset.get("created_at"),
                    "UpdatedAt": dataset.get("updated_at"),
                }

                # Apply $select if specified
                if select:
                    selected_props = [prop.strip() for prop in select.split(",")]
                    record = {k: v for k, v in record.items() if k in selected_props}

                odata_records.append(record)

            # Build response
            response_data = {
                "@odata.context": f"{base_url}/$metadata#Datasets",
                "value": odata_records,
            }

            # Add count if requested
            if count:
                response_data["@odata.count"] = total_count

            return JSONResponse(
                content=jsonable_encoder(response_data),
                headers={
                    "OData-Version": ODATA_VERSION,
                    "Content-Type": "application/json;odata.metadata=minimal",
                },
            )

        except Exception as e:
            logger.error(f"Failed to process OData Datasets query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OData query",
            )

    @router.get("/Observations", summary="OData Observations Entity Set")
    async def odata_observations(
        request: Request,
        top: Optional[int] = Query(
            None, alias="$top", description="Number of records to return"
        ),
        skip: Optional[int] = Query(
            None, alias="$skip", description="Number of records to skip"
        ),
        filter: Optional[str] = Query(
            None, alias="$filter", description="Filter expression"
        ),
        select: Optional[str] = Query(
            None, alias="$select", description="Properties to select"
        ),
        orderby: Optional[str] = Query(
            None, alias="$orderby", description="Order by expression"
        ),
        count: Optional[bool] = Query(
            None, alias="$count", description="Include count in response"
        ),
        repository=Depends(get_repository),
        current_user=Depends(get_current_user),
        _rate_limit=Depends(check_rate_limit),
        _audit=Depends(log_api_request),
    ):
        """
        OData Observations entity set for PowerBI Direct Query.

        Provides access to time series observations with full OData query capabilities.
        Optimized for large datasets with efficient pagination and filtering.

        **Performance**: Target <500ms for 10k records
        """
        try:
            base_url = str(request.base_url).rstrip("/") + "/odata"

            # Parse filter to extract dataset constraint (required for performance)
            dataset_id = _extract_dataset_filter(filter) if filter else None

            if not dataset_id:
                # For performance, require dataset filter for observations
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Filter by DatasetId is required for Observations queries. Example: $filter=DatasetId eq 'DCIS_POPRES1'",
                )

            # Get time series data for the dataset
            time_series = repository.get_dataset_time_series(dataset_id=dataset_id)

            # Convert to OData format with synthetic IDs
            odata_records = []
            for idx, obs in enumerate(time_series):
                record = {
                    "Id": idx + 1,  # Synthetic ID for OData
                    "DatasetId": dataset_id,
                    "Year": obs.get("year"),
                    "TimePeriod": obs.get("time_period"),
                    "TerritoryCode": obs.get("territory_code"),
                    "TerritoryName": obs.get("territory_name"),
                    "MeasureCode": obs.get("measure_code"),
                    "MeasureName": obs.get("measure_name"),
                    "ObsValue": obs.get("obs_value"),
                    "ObsStatus": obs.get("obs_status"),
                }

                # Apply additional filters
                if _matches_odata_filter(record, filter):
                    odata_records.append(record)

            # Apply ordering
            if orderby:
                odata_records = _apply_odata_orderby(odata_records, orderby)

            # Apply pagination
            total_count = len(odata_records)
            if skip:
                odata_records = odata_records[skip:]
            if top:
                odata_records = odata_records[:top]

            # Apply $select if specified
            if select:
                selected_props = [prop.strip() for prop in select.split(",")]
                odata_records = [
                    {k: v for k, v in record.items() if k in selected_props}
                    for record in odata_records
                ]

            # Build response
            response_data = {
                "@odata.context": f"{base_url}/$metadata#Observations",
                "value": odata_records,
            }

            # Add count if requested
            if count:
                response_data["@odata.count"] = total_count

            return JSONResponse(
                content=jsonable_encoder(response_data),
                headers={
                    "OData-Version": ODATA_VERSION,
                    "Content-Type": "application/json;odata.metadata=minimal",
                },
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process OData Observations query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OData query",
            )

    @router.get("/Territories", summary="OData Territories Entity Set")
    async def odata_territories(
        request: Request,
        top: Optional[int] = Query(None, alias="$top"),
        skip: Optional[int] = Query(None, alias="$skip"),
        filter: Optional[str] = Query(None, alias="$filter"),
        select: Optional[str] = Query(None, alias="$select"),
        orderby: Optional[str] = Query(None, alias="$orderby"),
        count: Optional[bool] = Query(None, alias="$count"),
        repository=Depends(get_repository),
        current_user=Depends(get_current_user),
        _rate_limit=Depends(check_rate_limit),
        _audit=Depends(log_api_request),
    ):
        """OData Territories entity set with territory hierarchy information"""
        try:
            base_url = str(request.base_url).rstrip("/") + "/odata"

            # Mock territory data (in real implementation, query from DuckDB)
            territories = [
                {
                    "TerritoryCode": "IT",
                    "TerritoryName": "Italia",
                    "Level": "Country",
                    "ParentCode": None,
                },
                {
                    "TerritoryCode": "ITC1",
                    "TerritoryName": "Piemonte",
                    "Level": "Region",
                    "ParentCode": "IT",
                },
                {
                    "TerritoryCode": "ITH1",
                    "TerritoryName": "Provincia Autonoma di Bolzano/Bozen",
                    "Level": "Province",
                    "ParentCode": "ITH",
                },
            ]

            # Apply OData query options
            filtered_territories = (
                _apply_odata_filter(territories, filter) if filter else territories
            )

            if orderby:
                filtered_territories = _apply_odata_orderby(
                    filtered_territories, orderby
                )

            total_count = len(filtered_territories)
            if skip:
                filtered_territories = filtered_territories[skip:]
            if top:
                filtered_territories = filtered_territories[:top]

            if select:
                selected_props = [prop.strip() for prop in select.split(",")]
                filtered_territories = [
                    {k: v for k, v in territory.items() if k in selected_props}
                    for territory in filtered_territories
                ]

            response_data = {
                "@odata.context": f"{base_url}/$metadata#Territories",
                "value": filtered_territories,
            }

            if count:
                response_data["@odata.count"] = total_count

            return JSONResponse(
                content=jsonable_encoder(response_data),
                headers={
                    "OData-Version": ODATA_VERSION,
                    "Content-Type": "application/json;odata.metadata=minimal",
                },
            )

        except Exception as e:
            logger.error(f"Failed to process OData Territories query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OData query",
            )

    @router.get("/Measures", summary="OData Measures Entity Set")
    async def odata_measures(
        request: Request,
        top: Optional[int] = Query(None, alias="$top"),
        skip: Optional[int] = Query(None, alias="$skip"),
        filter: Optional[str] = Query(None, alias="$filter"),
        select: Optional[str] = Query(None, alias="$select"),
        orderby: Optional[str] = Query(None, alias="$orderby"),
        count: Optional[bool] = Query(None, alias="$count"),
        repository=Depends(get_repository),
        current_user=Depends(get_current_user),
        _rate_limit=Depends(check_rate_limit),
        _audit=Depends(log_api_request),
    ):
        """OData Measures entity set with measure definitions and metadata"""
        try:
            base_url = str(request.base_url).rstrip("/") + "/odata"

            # Mock measures data (in real implementation, query from DuckDB)
            measures = [
                {
                    "MeasureCode": "POP_TOT",
                    "MeasureName": "Popolazione totale",
                    "Unit": "Numero",
                    "DataType": "Integer",
                },
                {
                    "MeasureCode": "POP_DENS",
                    "MeasureName": "Densità di popolazione",
                    "Unit": "Abitanti per km²",
                    "DataType": "Decimal",
                },
            ]

            # Apply OData query options
            filtered_measures = (
                _apply_odata_filter(measures, filter) if filter else measures
            )

            if orderby:
                filtered_measures = _apply_odata_orderby(filtered_measures, orderby)

            total_count = len(filtered_measures)
            if skip:
                filtered_measures = filtered_measures[skip:]
            if top:
                filtered_measures = filtered_measures[:top]

            if select:
                selected_props = [prop.strip() for prop in select.split(",")]
                filtered_measures = [
                    {k: v for k, v in measure.items() if k in selected_props}
                    for measure in filtered_measures
                ]

            response_data = {
                "@odata.context": f"{base_url}/$metadata#Measures",
                "value": filtered_measures,
            }

            if count:
                response_data["@odata.count"] = total_count

            return JSONResponse(
                content=jsonable_encoder(response_data),
                headers={
                    "OData-Version": ODATA_VERSION,
                    "Content-Type": "application/json;odata.metadata=minimal",
                },
            )

        except Exception as e:
            logger.error(f"Failed to process OData Measures query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OData query",
            )

    return router


# Helper functions for OData query processing


def _apply_odata_filter(data: List[Dict], filter_expr: str) -> List[Dict]:
    """Apply basic OData $filter expressions"""
    if not filter_expr:
        return data

    # Simple implementation for common filters
    # In production, use a proper OData expression parser

    filtered_data = []
    for record in data:
        if _matches_odata_filter(record, filter_expr):
            filtered_data.append(record)

    return filtered_data


def _matches_odata_filter(record: Dict, filter_expr: str) -> bool:
    """Check if a record matches an OData filter expression"""
    if not filter_expr:
        return True

    try:
        # Basic parsing for common patterns
        # This is a simplified implementation - production should use a proper parser

        # Handle "eq" (equals) operator
        if " eq " in filter_expr:
            parts = filter_expr.split(" eq ")
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")

                # Handle nested field access (e.g., "DatasetId eq 'VALUE'")
                if field in record:
                    return str(record[field]) == value

        # Handle "ne" (not equals) operator
        if " ne " in filter_expr:
            parts = filter_expr.split(" ne ")
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip().strip("'\"")

                if field in record:
                    return str(record[field]) != value

        # Handle "gt" (greater than) operator
        if " gt " in filter_expr:
            parts = filter_expr.split(" gt ")
            if len(parts) == 2:
                field = parts[0].strip()
                value = parts[1].strip()

                if field in record and record[field] is not None:
                    try:
                        return float(record[field]) > float(value)
                    except (ValueError, TypeError):
                        return False

        # Handle "contains" function
        if "contains(" in filter_expr.lower():
            # Extract contains(field, 'value') pattern
            import re

            match = re.search(
                r"contains\((\w+),\s*'([^']+)'\)", filter_expr, re.IGNORECASE
            )
            if match:
                field = match.group(1)
                value = match.group(2)

                if field in record and record[field]:
                    return value.lower() in str(record[field]).lower()

        return True  # Default to include if we can't parse the filter

    except Exception as e:
        logger.warning(f"Failed to parse OData filter '{filter_expr}': {e}")
        return True


def _apply_odata_orderby(data: List[Dict], orderby_expr: str) -> List[Dict]:
    """Apply OData $orderby expression"""
    if not orderby_expr:
        return data

    try:
        # Parse orderby expression (e.g., "Name asc" or "Priority desc")
        parts = orderby_expr.strip().split()
        field = parts[0]
        direction = parts[1].lower() if len(parts) > 1 else "asc"

        reverse = direction == "desc"

        # Sort the data
        return sorted(data, key=lambda x: x.get(field, ""), reverse=reverse)

    except Exception as e:
        logger.warning(f"Failed to parse OData orderby '{orderby_expr}': {e}")
        return data


def _extract_dataset_filter(filter_expr: str) -> Optional[str]:
    """Extract DatasetId from OData filter expression"""
    if not filter_expr:
        return None

    try:
        # Look for "DatasetId eq 'VALUE'" pattern
        if "DatasetId eq " in filter_expr:
            parts = filter_expr.split("DatasetId eq ")
            if len(parts) > 1:
                value_part = parts[1].split()[0]  # Get first part after "eq"
                return value_part.strip("'\"")

        return None

    except Exception as e:
        logger.warning(f"Failed to extract dataset filter from '{filter_expr}': {e}")
        return None
