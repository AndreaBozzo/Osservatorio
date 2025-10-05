"""
Enhanced validate_dataset_id function to replace the existing one in dependencies.py
"""

import re
from typing import Dict, List, Optional
from fastapi import HTTPException, status


def validate_dataset_id(dataset_id: str) -> str:
    """
    Enhanced dependency for dataset ID validation with better error messages.

    Args:
        dataset_id: Dataset identifier

    Returns:
        Validated dataset ID (stripped of whitespace)

    Raises:
        HTTPException: If dataset ID is invalid with detailed error information
    """
    
    # Check if dataset_id is provided
    if not dataset_id or not dataset_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Dataset ID is required",
                "message": "Dataset ID cannot be empty or contain only whitespace",
                "examples": ["DCIS_POPRES1", "DEMO_2020", "CENSUS_DATA_2019"],
                "documentation": "https://www.istat.it/en/analysis-and-products/databases"
            }
        )
    
    dataset_id = dataset_id.strip()
    
    # Check basic format - ISTAT dataset IDs are typically alphanumeric with underscores and hyphens
    if not re.match(r'^[A-Za-z0-9_-]+$', dataset_id):
        invalid_chars = re.findall(r'[^A-Za-z0-9_-]', dataset_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid dataset ID format",
                "message": f"Dataset ID contains invalid characters: {', '.join(set(invalid_chars))}",
                "expected_format": "Letters, numbers, underscores, and hyphens only (A-Z, a-z, 0-9, _, -)",
                "provided": dataset_id,
                "examples": ["DCIS_POPRES1", "DEMO-2020", "CENSUS_DATA_2019"],
                "suggestion": f"Remove invalid characters: {', '.join(set(invalid_chars))}"
            }
        )
    
    # Check length constraints (ISTAT dataset IDs are typically 3-50 characters)
    if len(dataset_id) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Dataset ID too short",
                "message": f"Dataset ID must be at least 3 characters long. Current length: {len(dataset_id)}",
                "provided": dataset_id,
                "minimum_length": 3,
                "suggestion": "Use a more descriptive dataset identifier"
            }
        )
    
    if len(dataset_id) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Dataset ID too long",
                "message": f"Dataset ID must be 50 characters or less. Current length: {len(dataset_id)}",
                "provided": dataset_id,
                "maximum_length": 50,
                "suggestion": "Use a shorter, more concise identifier"
            }
        )
    
    # Check for patterns that might indicate common mistakes
    if dataset_id.startswith('_') or dataset_id.startswith('-'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid dataset ID format",
                "message": "Dataset ID cannot start with underscore or hyphen",
                "provided": dataset_id,
                "suggestion": "Remove leading underscore or hyphen",
                "corrected_suggestion": dataset_id.lstrip('_-')
            }
        )
    
    if dataset_id.endswith('_') or dataset_id.endswith('-'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid dataset ID format",
                "message": "Dataset ID cannot end with underscore or hyphen",
                "provided": dataset_id,
                "suggestion": "Remove trailing underscore or hyphen",
                "corrected_suggestion": dataset_id.rstrip('_-')
            }
        )
    
    # Check for multiple consecutive separators
    if '__' in dataset_id or '--' in dataset_id or '_-' in dataset_id or '-_' in dataset_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid dataset ID format",
                "message": "Dataset ID cannot contain consecutive separators (underscores or hyphens)",
                "provided": dataset_id,
                "suggestion": "Use single separators between parts",
                "corrected_suggestion": re.sub(r'[_-]+', '_', dataset_id)
            }
        )
    
    # Enhanced validation: Check if it looks like a valid ISTAT pattern
    # Most ISTAT dataset IDs follow patterns like: DCIS_POPRES1, DEMO_2020, etc.
    if not re.match(r'^[A-Z][A-Z0-9]*[_-]?[A-Z0-9]*[_-]?[A-Z0-9]*$', dataset_id.upper()):
        # This is a warning, not an error - still allow it but suggest checking
        # We don't raise an exception here to maintain backward compatibility
        pass
    
    return dataset_id


def get_dataset_id_suggestions(invalid_id: str) -> List[str]:
    """
    Generate suggestions for common dataset ID patterns.
    
    Args:
        invalid_id: The invalid dataset ID
        
    Returns:
        List of suggested valid dataset IDs
    """
    suggestions = []
    
    # Clean up common issues step by step to preserve word boundaries
    # First, replace common separators and special chars with underscores
    cleaned = re.sub(r'[^A-Za-z0-9_\s-]', '_', invalid_id)  # Replace special chars with underscores
    cleaned = re.sub(r'\s+', '_', cleaned)  # Replace spaces with underscores
    cleaned = re.sub(r'[_-]+', '_', cleaned)  # Fix consecutive separators
    cleaned = cleaned.strip('_-')  # Remove leading/trailing separators
    
    if cleaned and len(cleaned) >= 3:
        suggestions.append(cleaned.upper())
    
    # Add some common ISTAT dataset patterns
    common_patterns = [
        "DCIS_POPRES1",
        "DEMO_2020", 
        "CENSUS_DATA_2019",
        "ECONOMIC_SURVEY_2022",
        "HEALTH_STATS_2021",
        "POPULATION_2020",
        "BUSINESS_REG_2021"
    ]
    
    # Simple similarity matching
    invalid_upper = invalid_id.upper()
    for pattern in common_patterns:
        # Check if any part of the invalid ID matches parts of known patterns
        if any(part in pattern for part in invalid_upper.replace('_', ' ').replace('-', ' ').split() if len(part) > 2):
            if pattern not in suggestions:
                suggestions.append(pattern)
    
    return suggestions[:5]  # Return top 5 suggestions


# Additional helper function for testing the enhanced validation
def test_dataset_id_validation():
    """
    Test function to validate the enhanced dataset ID validation.
    This can be run independently to test various scenarios.
    """
    test_cases = {
        # Valid cases
        "DCIS_POPRES1": True,
        "DEMO_2020": True,
        "census_data_2019": True,
        "ABC123": True,
        "test-dataset-v1": True,
        "DATA_SET_1": True,
        
        # Invalid cases
        "": False,
        "   ": False,
        "AB": False,  # too short
        "A" * 51: False,  # too long
        "_dataset": False,  # leading underscore
        "dataset_": False,  # trailing underscore
        "-dataset": False,  # leading hyphen
        "dataset-": False,  # trailing hyphen
        "dataset__id": False,  # consecutive underscores
        "dataset--id": False,  # consecutive hyphens
        "dataset id": False,  # space
        "dataset@id": False,  # special character
        "dataset.id": False,  # period
        "dataset/id": False,  # slash
    }
    
    results = {}
    for test_id, should_pass in test_cases.items():
        try:
            result = validate_dataset_id(test_id)
            results[test_id] = {"passed": True, "result": result}
        except HTTPException as e:
            results[test_id] = {"passed": False, "error": e.detail}
        
        # Check if result matches expectation
        actual_passed = results[test_id]["passed"]
        if actual_passed != should_pass:
            print(f"MISMATCH: {test_id} - Expected: {should_pass}, Got: {actual_passed}")
    
    return results