"""
Simple test runner for the enhanced dataset validation
Run this to test your implementation without pytest coverage issues
Save as: test_validation_simple.py
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

from fastapi import HTTPException

from src.api.dependencies import get_dataset_id_suggestions, validate_dataset_id


def test_enhanced_validation():
    """Simple test function to validate our enhanced dataset ID validation."""

    print("🧪 Testing Enhanced Dataset ID Validation")
    print("=" * 50)

    # Test cases
    test_cases = [
        # Valid cases (should pass)
        ("DCIS_POPRES1", True, "Valid ISTAT dataset ID"),
        ("DEMO_2020", True, "Valid demo dataset"),
        ("test-dataset-v1", True, "Valid with hyphens"),
        ("Mixed_Case_123", True, "Mixed case with numbers"),
        # Invalid cases (should fail)
        ("", False, "Empty string"),
        ("   ", False, "Whitespace only"),
        ("AB", False, "Too short"),
        ("A" * 51, False, "Too long"),
        ("_dataset", False, "Leading underscore"),
        ("dataset_", False, "Trailing underscore"),
        ("dataset__id", False, "Consecutive underscores"),
        ("dataset id", False, "Contains space"),
        ("dataset@id", False, "Contains special character"),
        ("dataset.id", False, "Contains period"),
    ]

    passed = 0
    failed = 0

    for dataset_id, should_pass, description in test_cases:
        try:
            result = validate_dataset_id(dataset_id)
            if should_pass:
                print(f"✅ PASS: {description} - '{dataset_id}' -> '{result}'")
                passed += 1
            else:
                print(
                    f"❌ FAIL: {description} - '{dataset_id}' should have failed but passed"
                )
                failed += 1
        except HTTPException as e:
            if not should_pass:
                error_msg = (
                    e.detail.get("error", "Unknown error")
                    if isinstance(e.detail, dict)
                    else str(e.detail)
                )
                print(
                    f"✅ EXPECTED FAIL: {description} - '{dataset_id}' -> {error_msg}"
                )
                passed += 1
            else:
                print(
                    f"❌ UNEXPECTED FAIL: {description} - '{dataset_id}' should have passed"
                )
                print(f"   Error: {e.detail}")
                failed += 1
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {description} - '{dataset_id}' -> {str(e)}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


def test_suggestions():
    """Test the suggestion function."""
    print("\n🔧 Testing Dataset ID Suggestions")
    print("=" * 50)

    test_cases = [
        "dataset id",  # space
        "_dataset_",  # leading/trailing underscores
        "dataset@#id",  # special characters
        "data.set_info",  # periods
        "dataset__id",  # consecutive underscores
    ]

    for invalid_id in test_cases:
        suggestions = get_dataset_id_suggestions(invalid_id)
        print(f"📝 '{invalid_id}' -> Suggestions: {suggestions}")


def test_error_messages():
    """Test that error messages are helpful."""
    print("\n💬 Testing Error Message Quality")
    print("=" * 50)

    error_test_cases = [
        ("", "empty"),
        ("dataset id", "space"),
        ("_dataset", "leading underscore"),
        ("dataset@id", "special character"),
        ("AB", "too short"),
        ("A" * 51, "too long"),
    ]

    for invalid_id, error_type in error_test_cases:
        try:
            validate_dataset_id(invalid_id)
        except HTTPException as e:
            if isinstance(e.detail, dict):
                print(
                    f"🗨️  {error_type.upper()}: {e.detail.get('error', 'No error field')}"
                )
                if "message" in e.detail:
                    print(f"   Message: {e.detail['message']}")
                if "suggestion" in e.detail:
                    print(f"   Suggestion: {e.detail['suggestion']}")
                if "examples" in e.detail:
                    print(f"   Examples: {e.detail['examples']}")
                print()
            else:
                print(f"🗨️  {error_type.upper()}: {e.detail}")


if __name__ == "__main__":
    print("🚀 Running Enhanced Dataset ID Validation Tests")
    print("=" * 60)

    # Run all tests
    validation_success = test_enhanced_validation()
    test_suggestions()
    test_error_messages()

    print("\n" + "=" * 60)
    if validation_success:
        print("✅ All validation tests passed! Your implementation is ready.")

    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
