"""
Comprehensive tests for the enhanced validate_dataset_id function
Save this as: tests/api/test_enhanced_dependencies.py
"""

import pytest
from fastapi import HTTPException

from src.api.dependencies import get_dataset_id_suggestions, validate_dataset_id


class TestEnhancedValidateDatasetId:
    """Test cases for enhanced dataset ID validation."""

    def test_valid_dataset_ids(self):
        """Test that valid dataset IDs pass validation."""
        valid_ids = [
            "DCIS_POPRES1",
            "DEMO_2020",
            "census_data_2019",
            "ABC123",
            "test-dataset-v1",
            "DATA_SET_1",
            "ECONOMIC-SURVEY-2022",
            "Pop2021",
            "A1B_C2D",
            "Dataset123",
        ]

        for dataset_id in valid_ids:
            result = validate_dataset_id(dataset_id)
            assert result == dataset_id.strip()
            print(f"✅ Valid: '{dataset_id}' -> '{result}'")

    def test_empty_dataset_id(self):
        """Test validation fails for empty dataset ID."""
        empty_cases = ["", "   ", "\t", "\n", "  \t  \n  "]

        for empty_id in empty_cases:
            with pytest.raises(HTTPException) as exc_info:
                validate_dataset_id(empty_id)

            assert exc_info.value.status_code == 400
            error_detail = exc_info.value.detail
            assert isinstance(error_detail, dict)
            assert error_detail["error"] == "Dataset ID is required"
            assert "examples" in error_detail
            print(f"✅ Empty case handled: '{empty_id}'")

    def test_invalid_characters(self):
        """Test validation fails for invalid characters."""
        invalid_cases = [
            ("dataset id", ["space"]),  # space
            ("dataset@id", ["@"]),  # special character
            ("dataset.id", ["."]),  # period
            ("dataset/id", ["/"]),  # slash
            ("dataset\\id", ["\\"]),  # backslash
            ("dataset%id", ["%"]),  # percent
            ("dataset#id", ["#"]),  # hash
            ("dataset!id", ["!"]),  # exclamation
            ("dataset*id", ["*"]),  # asterisk
            ("dataset+id", ["+"]),  # plus
            ("dataset=id", ["="]),  # equals
        ]

        for dataset_id, expected_chars in invalid_cases:
            with pytest.raises(HTTPException) as exc_info:
                validate_dataset_id(dataset_id)

            assert exc_info.value.status_code == 400
            error_detail = exc_info.value.detail
            assert isinstance(error_detail, dict)
            assert error_detail["error"] == "Invalid dataset ID format"
            assert "expected_format" in error_detail
            assert "suggestion" in error_detail
            print(
                f"✅ Invalid chars detected: '{dataset_id}' -> {error_detail['message']}"
            )

    def test_length_constraints(self):
        """Test validation for length constraints."""
        # Too short
        short_cases = ["A", "AB", "12"]
        for short_id in short_cases:
            with pytest.raises(HTTPException) as exc_info:
                validate_dataset_id(short_id)

            error_detail = exc_info.value.detail
            assert error_detail["error"] == "Dataset ID too short"
            assert error_detail["minimum_length"] == 3
            print(f"✅ Too short: '{short_id}'")

        # Too long
        long_id = "A" * 51  # 51 characters
        with pytest.raises(HTTPException) as exc_info:
            validate_dataset_id(long_id)

        error_detail = exc_info.value.detail
        assert error_detail["error"] == "Dataset ID too long"
        assert error_detail["maximum_length"] == 50
        print(f"✅ Too long: {len(long_id)} chars")

    def test_leading_trailing_separators(self):
        """Test validation fails for leading/trailing separators."""
        invalid_cases = [
            "_dataset",
            "dataset_",
            "_dataset_",
            "-dataset",
            "dataset-",
            "-dataset-",
            "__dataset",
            "dataset__",
        ]

        for dataset_id in invalid_cases:
            with pytest.raises(HTTPException) as exc_info:
                validate_dataset_id(dataset_id)

            error_detail = exc_info.value.detail
            assert (
                "cannot start" in error_detail["message"].lower()
                or "cannot end" in error_detail["message"].lower()
            )
            assert "corrected_suggestion" in error_detail
            print(
                f"✅ Leading/trailing separator: '{dataset_id}' -> {error_detail['corrected_suggestion']}"
            )

    def test_consecutive_separators(self):
        """Test validation fails for consecutive separators."""
        invalid_cases = [
            "dataset__id",  # double underscore
            "dataset--id",  # double hyphen
            "dataset_-id",  # underscore-hyphen
            "dataset-_id",  # hyphen-underscore
            "dataset___id",  # triple underscore
        ]

        for dataset_id in invalid_cases:
            with pytest.raises(HTTPException) as exc_info:
                validate_dataset_id(dataset_id)

            error_detail = exc_info.value.detail
            assert "consecutive separators" in error_detail["message"].lower()
            assert "corrected_suggestion" in error_detail
            print(
                f"✅ Consecutive separators: '{dataset_id}' -> {error_detail['corrected_suggestion']}"
            )

    def test_error_message_structure(self):
        """Test that error messages have proper structure."""
        with pytest.raises(HTTPException) as exc_info:
            validate_dataset_id("invalid@id")

        error_detail = exc_info.value.detail
        assert isinstance(error_detail, dict)

        # Check required fields
        required_fields = ["error", "message", "provided"]
        for field in required_fields:
            assert field in error_detail, f"Missing required field: {field}"

        # Check optional helpful fields
        helpful_fields = ["expected_format", "examples", "suggestion"]
        present_fields = [field for field in helpful_fields if field in error_detail]
        assert len(present_fields) > 0, "No helpful fields present"

        print(f"✅ Error structure complete with fields: {list(error_detail.keys())}")

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is handled correctly."""
        test_cases = [
            "  DATASET_ID  ",
            "\tDATASET_ID\t",
            "\nDATASET_ID\n",
            "  \t DATASET_ID \n  ",
        ]

        for padded_id in test_cases:
            result = validate_dataset_id(padded_id)
            assert result == "DATASET_ID"
            print(f"✅ Whitespace handled: '{padded_id}' -> '{result}'")

    def test_case_preservation(self):
        """Test that case is preserved in valid dataset IDs."""
        test_cases = [
            "MixedCase_Dataset",
            "lowercase_dataset",
            "UPPERCASE_DATASET",
            "CamelCase123",
        ]

        for dataset_id in test_cases:
            result = validate_dataset_id(dataset_id)
            assert result == dataset_id
            print(f"✅ Case preserved: '{dataset_id}'")

    def test_edge_cases(self):
        """Test edge cases for validation."""
        # Exactly at length boundaries
        min_length = "ABC"  # 3 chars
        max_length = "A" * 50  # 50 chars

        assert validate_dataset_id(min_length) == min_length
        assert validate_dataset_id(max_length) == max_length
        print(f"✅ Boundary lengths work: {len(min_length)}, {len(max_length)}")

        # Mixed separators (valid)
        mixed_valid = "DATA_SET-V1_2020"
        assert validate_dataset_id(mixed_valid) == mixed_valid
        print(f"✅ Mixed separators: '{mixed_valid}'")

    def test_backward_compatibility(self):
        """Test that the function maintains backward compatibility."""
        # These were valid in the old function and should still be valid
        legacy_valid_ids = [
            "DCIS_POPRES1",
            "ABC123",
            "dataset_id",
            "TEST-DATA",
            "Mixed_Case-123",
        ]

        for dataset_id in legacy_valid_ids:
            result = validate_dataset_id(dataset_id)
            assert result == dataset_id
            print(f"✅ Backward compatible: '{dataset_id}'")


class TestDatasetIdSuggestions:
    """Test cases for dataset ID suggestions."""

    def test_suggestions_generation(self):
        """Test that suggestions are generated for invalid IDs."""
        test_cases = [
            "dataset id",  # with space
            "_dataset_",  # with leading/trailing separators
            "dataset__id",  # with consecutive separators
            "dataset@id",  # with special characters
        ]

        for invalid_id in test_cases:
            suggestions = get_dataset_id_suggestions(invalid_id)
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
            print(f"✅ Suggestions for '{invalid_id}': {suggestions}")

    def test_cleaned_suggestion_included(self):
        """Test that cleaned version of input is included in suggestions."""
        test_cases = [
            ("dataset id", "DATASET_ID"),  # space becomes underscore
            ("_dataset_", "DATASET"),  # leading/trailing underscores removed
            ("dataset@#id", "DATASET_ID"),  # special chars become underscores
            ("data.set_info", "DATA_SET_INFO"),  # periods become underscores
        ]

        for invalid_id, expected_clean in test_cases:
            suggestions = get_dataset_id_suggestions(invalid_id)
            # The cleaned version should be the first suggestion
            assert suggestions[0] == expected_clean, (
                f"Expected '{expected_clean}' but got '{suggestions[0]}' for input '{invalid_id}'"
            )
            print(f"✅ Cleaned suggestion: '{invalid_id}' -> '{suggestions[0]}'")


# Integration test
def test_complete_workflow():
    """Test the complete validation workflow with various inputs."""
    print("\n=== COMPLETE WORKFLOW TEST ===")

    # Test batch of IDs
    test_batch = [
        # Valid IDs
        ("DCIS_POPRES1", True),
        ("DEMO_2020", True),
        ("test-data-v1", True),
        # Invalid IDs
        ("", False),
        ("dataset id", False),
        ("_dataset", False),
        ("dataset__id", False),
        ("AB", False),
        ("A" * 51, False),
    ]

    results = {"passed": 0, "failed": 0}

    for dataset_id, should_pass in test_batch:
        try:
            result = validate_dataset_id(dataset_id)
            if should_pass:
                print(f"✅ PASS: '{dataset_id}' -> '{result}'")
                results["passed"] += 1
            else:
                print(f"❌ UNEXPECTED PASS: '{dataset_id}' should have failed")
                results["failed"] += 1
        except HTTPException as e:
            if not should_pass:
                print(f"✅ EXPECTED FAIL: '{dataset_id}' -> {e.detail['error']}")
                results["passed"] += 1
            else:
                print(
                    f"❌ UNEXPECTED FAIL: '{dataset_id}' should have passed -> {e.detail}"
                )
                results["failed"] += 1

    print(f"\n=== RESULTS: {results['passed']} passed, {results['failed']} failed ===")
    assert results["failed"] == 0, "Some tests failed unexpectedly"


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_complete_workflow()
    print("\n✅ All tests completed successfully!")
