"""
Unit tests for categorization rules database operations.

Tests the database layer for categorization rules including CRUD operations,
data validation, and integration with the SQLite metadata manager.
"""
import json
import sqlite3
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.database.sqlite.manager import SQLiteMetadataManager
from src.database.sqlite.repository import UnifiedDataRepository
from src.database.sqlite.schema import MetadataSchema


class TestCategorizationRulesDatabase:
    """Test categorization rules database operations."""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create temporary database path."""
        return str(tmp_path / "test_categorization_rules.db")

    @pytest.fixture
    def manager(self, temp_db_path):
        """Create SQLite metadata manager with test database."""
        return SQLiteMetadataManager(temp_db_path, auto_create_schema=True)

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create unified repository with test database."""
        with patch("src.database.duckdb.get_manager") as mock_duckdb:
            mock_duckdb.return_value = MagicMock()
            return UnifiedDataRepository(sqlite_db_path=temp_db_path)

    def test_create_categorization_rule(self, manager):
        """Test creating a new categorization rule."""
        success = manager.create_categorization_rule(
            rule_id="test_rule",
            category="popolazione",
            keywords=["popolazione", "demo", "residente"],
            priority=10,
            description="Test population rule",
        )

        assert success is True

        # Verify rule was created
        rules = manager.get_categorization_rules()
        assert len(rules) > 0

        test_rule = next((r for r in rules if r["rule_id"] == "test_rule"), None)
        assert test_rule is not None
        assert test_rule["category"] == "popolazione"
        assert test_rule["keywords"] == ["popolazione", "demo", "residente"]
        assert test_rule["priority"] == 10
        assert test_rule["description"] == "Test population rule"
        assert test_rule["is_active"] is True

    def test_create_duplicate_rule_fails(self, manager):
        """Test that creating a duplicate rule fails."""
        # Create first rule
        success1 = manager.create_categorization_rule(
            rule_id="dup_rule",
            category="economia",
            keywords=["economia", "pil"],
            priority=8,
        )
        assert success1 is True

        # Try to create duplicate
        success2 = manager.create_categorization_rule(
            rule_id="dup_rule", category="lavoro", keywords=["lavoro"], priority=7
        )
        assert success2 is False

    def test_get_categorization_rules_filtering(self, manager):
        """Test filtering categorization rules by category and active status."""
        # Create test rules
        manager.create_categorization_rule("pop_rule", "popolazione", ["pop"], 10)
        manager.create_categorization_rule("econ_rule", "economia", ["econ"], 9)
        manager.create_categorization_rule("inactive_rule", "territorio", ["terr"], 8)

        # Deactivate one rule
        manager.update_categorization_rule("inactive_rule", is_active=False)

        # Test category filtering
        pop_rules = manager.get_categorization_rules(category="popolazione")
        assert len(pop_rules) == 1
        assert pop_rules[0]["rule_id"] == "pop_rule"

        # Test active only filtering
        active_rules = manager.get_categorization_rules(active_only=True)
        rule_ids = [r["rule_id"] for r in active_rules]
        assert "pop_rule" in rule_ids
        assert "econ_rule" in rule_ids
        assert "inactive_rule" not in rule_ids

        # Test getting all rules including inactive
        all_rules = manager.get_categorization_rules(active_only=False)
        all_rule_ids = [r["rule_id"] for r in all_rules]
        assert "inactive_rule" in all_rule_ids

    def test_update_categorization_rule(self, manager):
        """Test updating categorization rule fields."""
        # Create test rule
        manager.create_categorization_rule(
            "update_rule", "popolazione", ["old", "keywords"], 5
        )

        # Update keywords and priority
        success = manager.update_categorization_rule(
            "update_rule",
            keywords=["new", "updated", "keywords"],
            priority=8,
            description="Updated description",
        )
        assert success is True

        # Verify updates
        rules = manager.get_categorization_rules()
        updated_rule = next((r for r in rules if r["rule_id"] == "update_rule"), None)
        assert updated_rule is not None
        assert updated_rule["keywords"] == ["new", "updated", "keywords"]
        assert updated_rule["priority"] == 8
        assert updated_rule["description"] == "Updated description"

    def test_update_nonexistent_rule_fails(self, manager):
        """Test that updating a nonexistent rule fails."""
        success = manager.update_categorization_rule(
            "nonexistent_rule", keywords=["test"]
        )
        assert success is False

    def test_delete_categorization_rule(self, manager):
        """Test deleting a categorization rule."""
        # Create test rule
        manager.create_categorization_rule("delete_rule", "economia", ["delete"], 5)

        # Verify it exists
        rules = manager.get_categorization_rules()
        assert any(r["rule_id"] == "delete_rule" for r in rules)

        # Delete it
        success = manager.delete_categorization_rule("delete_rule")
        assert success is True

        # Verify it's gone
        rules = manager.get_categorization_rules()
        assert not any(r["rule_id"] == "delete_rule" for r in rules)

    def test_delete_nonexistent_rule_fails(self, manager):
        """Test that deleting a nonexistent rule fails."""
        success = manager.delete_categorization_rule("nonexistent_rule")
        assert success is False

    def test_keywords_normalization(self, manager):
        """Test that keywords are properly normalized (lowercase, stripped)."""
        success = manager.create_categorization_rule(
            "norm_rule",
            "popolazione",
            ["  POPOLAZIONE  ", "Demo", " residente\t"],
            priority=5,
        )
        assert success is True

        rules = manager.get_categorization_rules()
        norm_rule = next((r for r in rules if r["rule_id"] == "norm_rule"), None)
        assert norm_rule is not None
        assert norm_rule["keywords"] == ["popolazione", "demo", "residente"]

    def test_empty_keywords_validation(self, manager):
        """Test that rules with empty keywords are rejected."""
        success = manager.create_categorization_rule(
            "empty_rule", "popolazione", [], priority=5  # Empty keywords
        )
        assert success is False

        # Test with only whitespace keywords
        success2 = manager.create_categorization_rule(
            "whitespace_rule",
            "popolazione",
            ["  ", "\t", ""],  # Only whitespace
            priority=5,
        )
        assert success2 is False

    def test_default_categorization_rules_seeded(self, manager):
        """Test that default categorization rules are seeded on schema creation."""
        rules = manager.get_categorization_rules()

        # Should have at least the default rules
        assert len(rules) >= 6  # We defined 6 default rules

        # Check for expected categories
        categories = {r["category"] for r in rules}
        expected_categories = {
            "popolazione",
            "economia",
            "lavoro",
            "territorio",
            "istruzione",
            "salute",
        }
        assert expected_categories.issubset(categories)

        # Check for expected rule IDs
        rule_ids = {r["rule_id"] for r in rules}
        expected_rule_ids = {
            "pop_rule",
            "econ_rule",
            "work_rule",
            "terr_rule",
            "edu_rule",
            "health_rule",
        }
        assert expected_rule_ids.issubset(rule_ids)

    def test_rule_priority_ordering(self, manager):
        """Test that rules are returned in priority order."""
        # Create rules with different priorities
        manager.create_categorization_rule("low_prio", "economia", ["low"], 1)
        manager.create_categorization_rule("high_prio", "economia", ["high"], 10)
        manager.create_categorization_rule("med_prio", "economia", ["med"], 5)

        rules = manager.get_categorization_rules(category="economia")

        # Should be ordered by priority descending
        priorities = [r["priority"] for r in rules]
        assert priorities == sorted(priorities, reverse=True)

    def test_repository_integration(self, repository):
        """Test categorization rules through the unified repository."""
        # Test creating rule through repository
        success = repository.create_categorization_rule(
            "repo_rule",
            "popolazione",
            ["repository", "test"],
            priority=7,
            description="Repository test rule",
        )
        assert success is True

        # Test getting rules through repository
        rules = repository.get_categorization_rules(category="popolazione")
        repo_rule = next((r for r in rules if r["rule_id"] == "repo_rule"), None)
        assert repo_rule is not None
        assert repo_rule["description"] == "Repository test rule"

        # Test updating through repository
        success = repository.update_categorization_rule(
            "repo_rule", priority=9, is_active=False
        )
        assert success is True

        # Test deleting through repository
        success = repository.delete_categorization_rule("repo_rule")
        assert success is True

        # Verify deletion
        rules = repository.get_categorization_rules(active_only=False)
        assert not any(r["rule_id"] == "repo_rule" for r in rules)


class TestCategorizationRulesSchema:
    """Test database schema for categorization rules."""

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create temporary database path."""
        return str(tmp_path / "test_schema.db")

    def test_categorization_rules_table_created(self, temp_db_path):
        """Test that categorization_rules table is created with correct schema."""
        schema = MetadataSchema(temp_db_path)
        schema.create_schema()

        # Verify table exists and has correct structure
        table_info = schema.get_table_info("categorization_rules")
        assert len(table_info) > 0

        # Check required columns exist
        column_names = [col["name"] for col in table_info]
        required_columns = [
            "id",
            "rule_id",
            "category",
            "keywords_json",
            "priority",
            "is_active",
            "description",
            "created_at",
            "updated_at",
        ]
        for col in required_columns:
            assert col in column_names

    def test_schema_version_updated(self, temp_db_path):
        """Test that schema version is updated to 1.1.0."""
        schema = MetadataSchema(temp_db_path)
        schema.create_schema()

        # Connect and check version
        conn = sqlite3.connect(temp_db_path)
        try:
            cursor = conn.execute(
                "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "1.1.0"
        finally:
            conn.close()

    def test_categorization_rules_indexes_created(self, temp_db_path):
        """Test that indexes for categorization rules are created."""
        schema = MetadataSchema(temp_db_path)
        schema.create_schema()

        # Check that indexes exist
        conn = sqlite3.connect(temp_db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%categorization_rules%'"
            )
            indexes = [row[0] for row in cursor.fetchall()]

            expected_indexes = [
                "idx_categorization_rules_category",
                "idx_categorization_rules_active",
                "idx_categorization_rules_priority",
            ]
            for expected_idx in expected_indexes:
                assert expected_idx in indexes
        finally:
            conn.close()
