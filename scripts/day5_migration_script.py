#!/usr/bin/env python3
"""
Day 5 Migration Script - Unified Repository Migration
Implements migration scripts with rollback capability as required by Day 5 deliverables.

This script migrates data from legacy storage patterns to the new UnifiedDataRepository
pattern with SQLite metadata + DuckDB analytics.
"""

import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class Day5MigrationScript:
    """Migration script for Day 5 UnifiedDataRepository pattern."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backup_dir = self.project_root / "data" / "migration_backups"
        self.migration_log: List[Dict[str, Any]] = []

    def create_migration_backup(self) -> str:
        """Create backup before migration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"pre_day5_migration_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Backup existing data directories
        data_sources = [
            "data/databases",
            "data/cache",
            "data/processed",
            "data/reports",
        ]

        for source in data_sources:
            source_path = self.project_root / source
            if source_path.exists():
                dest_path = backup_path / source
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                self.migration_log.append(
                    {
                        "action": "backup",
                        "source": str(source_path),
                        "destination": str(dest_path),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        print(f"✅ Migration backup created: {backup_path}")
        return str(backup_path)

    def migrate_json_configs_to_sqlite(self) -> bool:
        """Migrate JSON configuration files to SQLite metadata."""
        try:
            # Issue #84: Use proper imports without sys.path manipulation
            from src.database.sqlite.repository import UnifiedDataRepository

            repo = UnifiedDataRepository()

            # Look for JSON config files to migrate
            config_files = [
                "powerbi_istat_datasets_20250720.json",
                "tableau_istat_datasets_20250720.json",
            ]

            migrated_count = 0

            for config_file in config_files:
                config_path = self.project_root / config_file
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)

                    # Extract dataset information
                    if isinstance(config_data, dict) and "datasets" in config_data:
                        for dataset in config_data["datasets"]:
                            success = repo.register_dataset_complete(
                                dataset_id=dataset.get(
                                    "id", f"migrated_{migrated_count}"
                                ),
                                name=dataset.get("name", "Migrated Dataset"),
                                category=dataset.get("category", "migrated"),
                                description=f"Migrated from {config_file}",
                                metadata={
                                    "migrated_from": config_file,
                                    "original_data": dataset,
                                },
                            )

                            if success:
                                migrated_count += 1
                                self.migration_log.append(
                                    {
                                        "action": "migrate_dataset",
                                        "dataset_id": dataset.get("id"),
                                        "source_file": config_file,
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )

            print(f"✅ Migrated {migrated_count} datasets from JSON configs to SQLite")
            return migrated_count > 0

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            self.migration_log.append(
                {
                    "action": "migration_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return False

    def validate_migration(self) -> bool:
        """Validate that migration was successful."""
        try:
            # Issue #84: Use proper imports without sys.path manipulation
            from src.database.sqlite.repository import UnifiedDataRepository

            repo = UnifiedDataRepository()

            # Test core functionality
            status = repo.get_system_status()
            if not isinstance(status, dict):
                return False

            # Test dataset operations
            datasets = repo.list_datasets_complete()
            if not isinstance(datasets, list):
                return False

            # Test user preferences
            test_success = repo.set_user_preference(
                "migration_test", "test_key", "test_value"
            )
            if not test_success:
                return False

            test_value = repo.get_user_preference("migration_test", "test_key")
            if test_value != "test_value":
                return False

            print("✅ Migration validation successful")
            return True

        except Exception as e:
            print(f"❌ Migration validation failed: {e}")
            return False

    def rollback_migration(self, backup_path: str) -> bool:
        """Rollback migration using backup."""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                print(f"❌ Backup directory not found: {backup_path}")
                return False

            # Restore from backup
            for backup_item in backup_dir.iterdir():
                if backup_item.is_dir():
                    target_path = self.project_root / backup_item.name
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(backup_item, target_path)

                    self.migration_log.append(
                        {
                            "action": "rollback",
                            "source": str(backup_item),
                            "destination": str(target_path),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            print(f"✅ Migration rolled back from: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def save_migration_log(self) -> None:
        """Save migration log for audit purposes."""
        log_path = (
            self.project_root
            / "data"
            / "migration_logs"
            / f"day5_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "migration_type": "Day 5 Unified Repository",
                    "timestamp": datetime.now().isoformat(),
                    "log_entries": self.migration_log,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"📋 Migration log saved: {log_path}")

    def run_migration(self, validate_only: bool = False) -> bool:
        """Run complete migration process."""
        print("🔄 Day 5 Migration Script - Unified Repository Pattern")
        print("=" * 55)

        if validate_only:
            print("🔍 Running validation only...")
            return self.validate_migration()

        # Create backup
        backup_path = self.create_migration_backup()

        try:
            # Perform migration
            print("\n📦 Migrating JSON configs to SQLite...")
            migration_success = self.migrate_json_configs_to_sqlite()

            if migration_success:
                # Validate migration
                print("\n✅ Validating migration...")
                validation_success = self.validate_migration()

                if validation_success:
                    print("\n🎉 Day 5 Migration completed successfully!")
                    self.save_migration_log()
                    return True
                else:
                    print("\n❌ Migration validation failed, rolling back...")
                    self.rollback_migration(backup_path)
                    return False
            else:
                print("\n❌ Migration failed, rolling back...")
                self.rollback_migration(backup_path)
                return False

        except Exception as e:
            print(f"\n💥 Migration error: {e}")
            print("🔄 Rolling back...")
            self.rollback_migration(backup_path)
            return False
        finally:
            self.save_migration_log()


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Day 5 migration script for UnifiedDataRepository"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate, don't migrate"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force migration without confirmation"
    )

    args = parser.parse_args()

    migration = Day5MigrationScript()

    if not args.validate_only and not args.force:
        response = input(
            "🚨 This will migrate data to Day 5 UnifiedRepository. Continue? (y/N): "
        )
        if response.lower() != "y":
            print("Migration cancelled.")
            return 1

    success = migration.run_migration(validate_only=args.validate_only)

    return 0 if success else 1


if __name__ == "__main__":
    # Add project root to Python path
    # Issue #84: Removed unsafe sys.path manipulation
    # Use proper package imports or run from project root
    sys.exit(main())
