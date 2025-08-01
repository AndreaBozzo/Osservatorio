"""
FastAPI endpoints for dataflow analysis and categorization.

Provides REST API endpoints for:
- Dataflow XML analysis and categorization
- Categorization rules management (CRUD operations)
- Bulk dataflow analysis operations
- Tableau-ready dataset generation
"""

import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from src.database.sqlite.repository import UnifiedDataRepository, get_unified_repository
from src.services.models import AnalysisFilters
from src.services.models import BulkAnalysisRequest as ServiceBulkRequest
from src.services.service_factory import get_dataflow_analysis_service
from src.utils.logger import get_logger

from .dependencies import (
    check_rate_limit,
    get_current_user,
    get_dataflow_service,
    handle_api_errors,
    log_api_request,
    require_write,
    validate_pagination,
)
from .models import (
    APIResponse,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    CategorizationRuleCreate,
    CategorizationRuleResponse,
    CategorizationRulesListResponse,
    CategorizationRuleUpdate,
    DataflowAnalysisRequest,
    DataflowAnalysisResponse,
    DataflowInfo,
    DataflowTestInfo,
    ErrorResponse,
    TableauReadyDataflow,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Dataflow Analysis"])


@router.post(
    "/dataflow",
    response_model=DataflowAnalysisResponse,
    summary="Analyze ISTAT dataflow XML",
    description="""
    Analyze ISTAT dataflow XML content and categorize dataflows.

    This endpoint processes ISTAT SDMX dataflow XML and:
    - Extracts all dataflow definitions
    - Categorizes them using machine learning rules
    - Optionally tests data access and generates Tableau-ready datasets
    - Returns comprehensive analysis results with performance metrics

    **Input Options:**
    - Provide `xml_content` directly in the request body
    - Upload an XML file using the file upload endpoint
    - Specify `xml_file_path` for server-side files

    **Features:**
    - Smart categorization using database-driven rules
    - Data access testing with error handling
    - Tableau integration recommendations
    - Performance metrics and caching
    """,
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid XML content or parameters"},
        422: {"description": "Validation error in request data"},
        500: {"description": "Internal server error during analysis"},
    },
)
@handle_api_errors
async def analyze_dataflow(
    request: DataflowAnalysisRequest,
    current_user=Depends(get_current_user),
    service=Depends(get_dataflow_service),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> DataflowAnalysisResponse:
    """Analyze ISTAT dataflow XML and categorize dataflows."""

    # Validate input - need either xml_content or xml_file_path
    if not request.xml_content and not request.xml_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either xml_content or xml_file_path must be provided",
        )

    # Get XML content
    xml_content = request.xml_content
    if request.xml_file_path and not xml_content:
        file_path = Path(request.xml_file_path)
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"XML file not found: {request.xml_file_path}",
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                xml_content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read XML file: {str(e)}",
            )

    # Create analysis filters
    filters = AnalysisFilters(
        categories=request.categories,
        min_relevance_score=request.min_relevance_score,
        max_results=request.max_results,
        include_tests=request.include_tests,
        only_tableau_ready=request.only_tableau_ready,
    )

    try:
        # Perform analysis using injected service
        result = await service.analyze_dataflows_from_xml(xml_content, filters)

        # Convert service models to API models
        categorized_dataflows = {}
        for category, dataflows in result.categorized_dataflows.items():
            categorized_dataflows[category.value] = [
                DataflowInfo(
                    id=df.id,
                    name_it=df.name_it,
                    name_en=df.name_en,
                    display_name=df.display_name,
                    description=df.description,
                    category=df.category,
                    relevance_score=df.relevance_score,
                    created_at=df.created_at,
                )
                for df in dataflows
            ]

        # Convert test results
        test_results = []
        for test_result in result.test_results:
            api_test_result = TableauReadyDataflow(
                dataflow=DataflowInfo(
                    id=test_result.dataflow.id,
                    name_it=test_result.dataflow.name_it,
                    name_en=test_result.dataflow.name_en,
                    display_name=test_result.dataflow.display_name,
                    description=test_result.dataflow.description,
                    category=test_result.dataflow.category,
                    relevance_score=test_result.dataflow.relevance_score,
                    created_at=test_result.dataflow.created_at,
                ),
                test=DataflowTestInfo(
                    dataflow_id=test_result.test.dataflow_id,
                    data_access_success=test_result.test.data_access_success,
                    status_code=test_result.test.status_code,
                    size_bytes=test_result.test.size_bytes,
                    size_mb=test_result.test.size_mb,
                    observations_count=test_result.test.observations_count,
                    sample_file=test_result.test.sample_file,
                    parse_error=test_result.test.parse_error,
                    error_message=test_result.test.error_message,
                    tested_at=test_result.test.tested_at,
                    is_successful=test_result.test.is_successful,
                ),
                tableau_ready=test_result.tableau_ready,
                suggested_connection=test_result.suggested_connection,
                suggested_refresh=test_result.suggested_refresh,
                priority=test_result.priority,
            )
            test_results.append(api_test_result)

        return DataflowAnalysisResponse(
            success=True,
            message=f"Successfully analyzed {result.total_analyzed} dataflows",
            total_analyzed=result.total_analyzed,
            categorized_dataflows=categorized_dataflows,
            test_results=test_results,
            tableau_ready_count=result.tableau_ready_count,
            analysis_timestamp=result.analysis_timestamp,
            performance_metrics=result.performance_metrics,
        )

    except Exception as e:
        logger.error(f"Error during dataflow analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post(
    "/dataflow/upload",
    response_model=DataflowAnalysisResponse,
    summary="Upload and analyze XML file",
    description="Upload an ISTAT dataflow XML file and analyze it.",
)
@handle_api_errors
async def upload_and_analyze_xml(
    file: UploadFile = File(..., description="ISTAT dataflow XML file"),
    categories: Optional[str] = Query(
        None, description="Comma-separated list of categories to filter"
    ),
    min_relevance_score: int = Query(0, description="Minimum relevance score"),
    max_results: int = Query(100, description="Maximum number of results"),
    include_tests: bool = Query(
        True, description="Whether to include data access tests"
    ),
    only_tableau_ready: bool = Query(
        False, description="Only return Tableau-ready dataflows"
    ),
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> DataflowAnalysisResponse:
    """Upload and analyze ISTAT dataflow XML file."""

    # Validate file type
    if not file.filename.lower().endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only XML files are supported",
        )

    try:
        # Read file content
        xml_content = await file.read()
        xml_content = xml_content.decode("utf-8")

        # Parse categories if provided
        category_list = None
        if categories:
            from src.services.models import DataflowCategory

            try:
                category_list = []
                valid_categories = [c.value for c in DataflowCategory]
                for cat in categories.split(","):
                    cat = cat.strip()
                    # Validate category exists in enum
                    if cat not in valid_categories:
                        raise ValueError(
                            f"'{cat}' is not a valid category. Valid categories: {valid_categories}"
                        )
                    category_list.append(DataflowCategory(cat))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {str(e)}",
                )

        # Create request object
        request = DataflowAnalysisRequest(
            xml_content=xml_content,
            categories=category_list,
            min_relevance_score=min_relevance_score,
            max_results=max_results,
            include_tests=include_tests,
            only_tableau_ready=only_tableau_ready,
        )

        # Get service and call analyze_dataflow with all dependencies
        service = get_dataflow_analysis_service()

        # Create analysis filters
        filters = AnalysisFilters(
            categories=request.categories,
            min_relevance_score=request.min_relevance_score,
            max_results=request.max_results,
            include_tests=request.include_tests,
            only_tableau_ready=request.only_tableau_ready,
        )

        # Perform analysis using service directly
        result = await service.analyze_dataflows_from_xml(request.xml_content, filters)

        # Convert service models to API models (same logic as analyze_dataflow)
        categorized_dataflows = {}
        for category, dataflows in result.categorized_dataflows.items():
            categorized_dataflows[category.value] = [
                DataflowInfo(
                    id=df.id,
                    name_it=df.name_it,
                    name_en=df.name_en,
                    display_name=df.display_name,
                    description=df.description,
                    category=df.category,
                    relevance_score=df.relevance_score,
                    created_at=df.created_at,
                )
                for df in dataflows
            ]

        # Convert test results
        test_results = []
        for test_result in result.test_results:
            api_test_result = TableauReadyDataflow(
                dataflow=DataflowInfo(
                    id=test_result.dataflow.id,
                    name_it=test_result.dataflow.name_it,
                    name_en=test_result.dataflow.name_en,
                    display_name=test_result.dataflow.display_name,
                    description=test_result.dataflow.description,
                    category=test_result.dataflow.category,
                    relevance_score=test_result.dataflow.relevance_score,
                    created_at=test_result.dataflow.created_at,
                ),
                test=DataflowTestInfo(
                    dataflow_id=test_result.test.dataflow_id,
                    data_access_success=test_result.test.data_access_success,
                    status_code=test_result.test.status_code,
                    size_bytes=test_result.test.size_bytes,
                    size_mb=test_result.test.size_mb,
                    observations_count=test_result.test.observations_count,
                    sample_file=test_result.test.sample_file,
                    parse_error=test_result.test.parse_error,
                    error_message=test_result.test.error_message,
                    tested_at=test_result.test.tested_at,
                    is_successful=test_result.test.is_successful,
                ),
                tableau_ready=test_result.tableau_ready,
                suggested_connection=test_result.suggested_connection,
                suggested_refresh=test_result.suggested_refresh,
                priority=test_result.priority,
            )
            test_results.append(api_test_result)

        return DataflowAnalysisResponse(
            success=True,
            message=f"Successfully analyzed {result.total_analyzed} dataflows",
            total_analyzed=result.total_analyzed,
            categorized_dataflows=categorized_dataflows,
            test_results=test_results,
            tableau_ready_count=result.tableau_ready_count,
            analysis_timestamp=result.analysis_timestamp,
            performance_metrics=result.performance_metrics,
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be UTF-8 encoded"
        )
    except Exception as e:
        logger.error(f"Error processing uploaded file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}",
        )


@router.post(
    "/dataflow/bulk",
    response_model=BulkAnalysisResponse,
    summary="Bulk analyze multiple dataflows",
    description="""
    Perform bulk analysis of multiple dataflows by their IDs.

    This endpoint allows you to analyze multiple specific dataflows without
    needing the full XML. Useful for targeted analysis of known dataflows.
    """,
)
@handle_api_errors
async def bulk_analyze_dataflows(
    request: BulkAnalysisRequest,
    current_user=Depends(get_current_user),
    service=Depends(get_dataflow_service),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> BulkAnalysisResponse:
    """Perform bulk analysis of multiple dataflows."""

    try:
        # Convert API request to service request
        service_request = ServiceBulkRequest(
            dataflow_ids=request.dataflow_ids,
            include_tests=request.include_tests,
            save_samples=request.save_samples,
            max_concurrent=request.max_concurrent,
        )

        # Perform bulk analysis
        results = await service.bulk_analyze(service_request)

        # Convert results to API format
        api_results = []
        errors = []

        for result in results:
            try:
                api_result = TableauReadyDataflow(
                    dataflow=DataflowInfo(
                        id=result.dataflow.id,
                        name_it=result.dataflow.name_it,
                        name_en=result.dataflow.name_en,
                        display_name=result.dataflow.display_name,
                        description=result.dataflow.description,
                        category=result.dataflow.category,
                        relevance_score=result.dataflow.relevance_score,
                        created_at=result.dataflow.created_at,
                    ),
                    test=DataflowTestInfo(
                        dataflow_id=result.test.dataflow_id,
                        data_access_success=result.test.data_access_success,
                        status_code=result.test.status_code,
                        size_bytes=result.test.size_bytes,
                        size_mb=result.test.size_mb,
                        observations_count=result.test.observations_count,
                        sample_file=result.test.sample_file,
                        parse_error=result.test.parse_error,
                        error_message=result.test.error_message,
                        tested_at=result.test.tested_at,
                        is_successful=result.test.is_successful,
                    ),
                    tableau_ready=result.tableau_ready,
                    suggested_connection=result.suggested_connection,
                    suggested_refresh=result.suggested_refresh,
                    priority=result.priority,
                )
                api_results.append(api_result)
            except Exception as e:
                errors.append(
                    f"Failed to process result for {getattr(result, 'dataflow_id', 'unknown')}: {str(e)}"
                )

        return BulkAnalysisResponse(
            success=True,
            message=f"Bulk analysis completed: {len(api_results)}/{len(request.dataflow_ids)} successful",
            requested_count=len(request.dataflow_ids),
            successful_count=len(api_results),
            failed_count=len(request.dataflow_ids) - len(api_results),
            results=api_results,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Error during bulk analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk analysis failed: {str(e)}",
        )


# Categorization Rules Management Endpoints


@router.get(
    "/rules",
    response_model=CategorizationRulesListResponse,
    summary="Get categorization rules",
    description="Retrieve all or filtered categorization rules used for dataflow analysis.",
)
@handle_api_errors
async def get_categorization_rules(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only return active rules"),
    current_user=Depends(get_current_user),
    repository: UnifiedDataRepository = Depends(get_unified_repository),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> CategorizationRulesListResponse:
    """Get categorization rules."""

    try:
        rules_data = repository.get_categorization_rules(category, active_only)

        # Convert to API format
        rules = []
        for rule_data in rules_data:
            rule = CategorizationRuleResponse(
                id=rule_data.get("id"),
                rule_id=rule_data["rule_id"],
                category=rule_data["category"],
                keywords=rule_data["keywords"],
                priority=rule_data["priority"],
                is_active=rule_data["is_active"],
                description=rule_data.get("description"),
                created_at=rule_data.get("created_at"),
                updated_at=rule_data.get("updated_at"),
            )
            rules.append(rule)

        active_count = len([r for r in rules if r.is_active])

        return CategorizationRulesListResponse(
            success=True,
            message=f"Retrieved {len(rules)} categorization rules",
            rules=rules,
            total_count=len(rules),
            active_count=active_count,
        )

    except Exception as e:
        logger.error(f"Error retrieving categorization rules: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rules: {str(e)}",
        )


@router.post(
    "/rules",
    response_model=APIResponse,
    summary="Create categorization rule",
    description="Create a new categorization rule for dataflow analysis.",
    status_code=status.HTTP_201_CREATED,
)
@handle_api_errors
async def create_categorization_rule(
    rule: CategorizationRuleCreate,
    current_user=Depends(require_write),
    repository: UnifiedDataRepository = Depends(get_unified_repository),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> APIResponse:
    """Create a new categorization rule."""

    try:
        success = repository.create_categorization_rule(
            rule_id=rule.rule_id,
            category=rule.category.value,
            keywords=rule.keywords,
            priority=rule.priority,
            description=rule.description,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create rule '{rule.rule_id}' - may already exist",
            )

        return APIResponse(
            success=True,
            message=f"Categorization rule '{rule.rule_id}' created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating categorization rule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}",
        )


@router.put(
    "/rules/{rule_id}",
    response_model=APIResponse,
    summary="Update categorization rule",
    description="Update an existing categorization rule.",
)
@handle_api_errors
async def update_categorization_rule(
    rule_id: str,
    rule_update: CategorizationRuleUpdate,
    current_user=Depends(require_write),
    repository: UnifiedDataRepository = Depends(get_unified_repository),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> APIResponse:
    """Update an existing categorization rule."""

    try:
        success = repository.update_categorization_rule(
            rule_id=rule_id,
            keywords=rule_update.keywords,
            priority=rule_update.priority,
            is_active=rule_update.is_active,
            description=rule_update.description,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categorization rule '{rule_id}' not found",
            )

        return APIResponse(
            success=True,
            message=f"Categorization rule '{rule_id}' updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating categorization rule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rule: {str(e)}",
        )


@router.delete(
    "/rules/{rule_id}",
    response_model=APIResponse,
    summary="Delete categorization rule",
    description="Delete a categorization rule.",
)
@handle_api_errors
async def delete_categorization_rule(
    rule_id: str,
    current_user=Depends(require_write),
    repository: UnifiedDataRepository = Depends(get_unified_repository),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> APIResponse:
    """Delete a categorization rule."""

    try:
        success = repository.delete_categorization_rule(rule_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categorization rule '{rule_id}' not found",
            )

        return APIResponse(
            success=True,
            message=f"Categorization rule '{rule_id}' deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting categorization rule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rule: {str(e)}",
        )


@router.get(
    "/samples/{dataflow_id}",
    response_class=FileResponse,
    summary="Download dataflow sample",
    description="Download a sample XML file for a specific dataflow.",
)
@handle_api_errors
async def download_sample_file(
    dataflow_id: str,
    current_user=Depends(get_current_user),
    _rate_limit=Depends(check_rate_limit),
    _audit=Depends(log_api_request),
) -> FileResponse:
    """Download a sample XML file for a specific dataflow."""

    # This would typically look up the sample file path from the database
    # For now, we'll implement a basic version
    from src.utils.temp_file_manager import get_temp_manager

    try:
        temp_manager = get_temp_manager()
        sample_filename = f"sample_{dataflow_id}.xml"
        sample_path = temp_manager.get_temp_file_path(sample_filename)

        if not sample_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sample file for dataflow '{dataflow_id}' not found",
            )

        return FileResponse(
            path=sample_path,
            media_type="application/xml",
            filename=sample_filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading sample file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download sample: {str(e)}",
        )
