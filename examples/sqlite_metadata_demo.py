"""
SQLite Metadata Layer Demo for Osservatorio ISTAT Data Platform

Demonstrates the SQLite metadata layer functionality in the hybrid
SQLite + DuckDB architecture as defined in ADR-002.

Features demonstrated:
- Dataset registry management
- User preferences with encryption
- API credentials storage
- Audit logging
- System configuration
- Unified repository facade pattern
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# Import SQLite components
from src.database.sqlite import (
    DatasetManager,
    ConfigurationManager,
    UserManager,
    AuditManager,
    create_metadata_schema,
    get_unified_repository,
)


def demo_metadata_schema():
    """Demonstrate metadata schema creation and verification."""
    print("🗃️ SQLite Metadata Schema Demo")
    print("=" * 50)

    # Create schema
    print("📋 Creating metadata schema...")
    schema = create_metadata_schema("data/demo_metadata.db")

    if schema.verify_schema():
        print("✅ Schema created and verified successfully")

        # Show table information
        print("\n📊 Database Tables:")
        for table_name in schema.SCHEMA_SQL.keys():
            info = schema.get_table_info(table_name)
            print(f"  • {table_name}: {len(info)} columns")
    else:
        print("❌ Schema verification failed")

    print()


def demo_dataset_registry():
    """Demonstrate dataset registry operations."""
    print("📚 Dataset Registry Demo")
    print("=" * 30)

    manager = DatasetManager("data/demo_metadata.db")

    try:
        # Register ISTAT datasets
        datasets = [
            {
                "dataset_id": "DCIS_POPRES1",
                "name": "Popolazione residente",
                "category": "popolazione",
                "description": "Dati sulla popolazione residente italiana per regione e provincia",
                "istat_agency": "ISTAT",
                "priority": 10,
                "metadata": {
                    "frequency": "annual",
                    "unit": "persons",
                    "geo_level": ["national", "regional", "provincial"],
                    "measures": [
                        "total_population",
                        "male_population",
                        "female_population",
                    ],
                },
            },
            {
                "dataset_id": "DCCN_PILN",
                "name": "Prodotto interno lordo",
                "category": "economia",
                "description": "PIL ai prezzi di mercato per regione",
                "istat_agency": "ISTAT",
                "priority": 9,
                "metadata": {
                    "frequency": "annual",
                    "unit": "millions_euros",
                    "geo_level": ["national", "regional"],
                    "measures": ["gdp_current_prices", "gdp_constant_prices"],
                },
            },
            {
                "dataset_id": "DCCV_TAXOCCU",
                "name": "Tasso di occupazione",
                "category": "lavoro",
                "description": "Tasso di occupazione per regione, sesso ed età",
                "istat_agency": "ISTAT",
                "priority": 8,
                "metadata": {
                    "frequency": "quarterly",
                    "unit": "percentage",
                    "geo_level": ["national", "regional"],
                    "dimensions": ["sex", "age_group"],
                },
            },
        ]

        print("📝 Registering datasets...")
        for dataset in datasets:
            success = manager.register_dataset(**dataset)
            if success:
                print(f"  ✅ {dataset['dataset_id']}: {dataset['name']}")
            else:
                print(f"  ❌ Failed to register {dataset['dataset_id']}")

        # List all datasets
        print("\n📊 Registered datasets:")
        all_datasets = manager.list_datasets()
        for dataset in all_datasets:
            print(
                f"  • {dataset['dataset_id']} ({dataset['category']}) - Priority: {dataset['priority']}"
            )

        # List by category
        print("\n🏷️ Population datasets:")
        pop_datasets = manager.list_datasets(category="popolazione")
        for dataset in pop_datasets:
            print(f"  • {dataset['name']}: {dataset['description']}")
            print(f"    Metadata: {json.dumps(dataset['metadata'], indent=6)}")

        # Update dataset statistics
        print("\n📈 Updating dataset statistics...")
        manager.update_dataset_stats(
            "DCIS_POPRES1", quality_score=0.95, record_count=8000
        )
        manager.update_dataset_stats("DCCN_PILN", quality_score=0.92, record_count=1200)

        # Show updated dataset
        updated_dataset = manager.get_dataset("DCIS_POPRES1")
        print(
            f"  📊 DCIS_POPRES1 stats: Quality={updated_dataset['quality_score']}, Records={updated_dataset['record_count']}"
        )

    finally:
        manager.close_connections()

    print()


def demo_user_preferences():
    """Demonstrate user preferences management."""
    print("👤 User Preferences Demo")
    print("=" * 30)

    manager = UserManager("data/demo_metadata.db")

    try:
        # Set various types of preferences
        users = ["analyst1", "analyst2", "admin1"]

        print("⚙️ Setting user preferences...")

        # Analyst 1 preferences
        manager.set_user_preference("analyst1", "theme", "dark")
        manager.set_user_preference("analyst1", "language", "it")
        manager.set_user_preference(
            "analyst1", "dashboard_refresh_interval", 300, "integer"
        )
        manager.set_user_preference(
            "analyst1", "notifications_enabled", True, "boolean"
        )
        manager.set_user_preference(
            "analyst1", "favorite_categories", ["popolazione", "economia"], "json"
        )

        # Analyst 2 preferences
        manager.set_user_preference("analyst2", "theme", "light")
        manager.set_user_preference("analyst2", "language", "en")
        manager.set_user_preference("analyst2", "email_reports", False, "boolean")

        # Admin preferences (with encryption)
        manager.set_user_preference(
            "admin1", "api_key", "super_secret_api_key_123", encrypt=True
        )
        manager.set_user_preference(
            "admin1",
            "admin_settings",
            {"full_access": True, "audit_level": "detailed"},
            "json",
            encrypt=True,
        )

        # Display preferences
        for user_id in users:
            print(f"\n👤 Preferences for {user_id}:")
            preferences = manager.get_user_preferences(user_id)
            for key, value in preferences.items():
                if key == "api_key":
                    print(f"    {key}: [ENCRYPTED]")
                else:
                    print(f"    {key}: {value} ({type(value).__name__})")

        # Test individual preference retrieval
        print("\n🔍 Individual preference tests:")
        theme = manager.get_user_preference("analyst1", "theme")
        print(f"  analyst1 theme: {theme}")

        refresh_interval = manager.get_user_preference(
            "analyst1", "dashboard_refresh_interval"
        )
        print(f"  analyst1 refresh interval: {refresh_interval} seconds")

        favorite_cats = manager.get_user_preference("analyst1", "favorite_categories")
        print(f"  analyst1 favorite categories: {favorite_cats}")

        # Test default values
        unknown_pref = manager.get_user_preference(
            "analyst1", "unknown_setting", "default_value"
        )
        print(f"  unknown setting (default): {unknown_pref}")

    finally:
        manager.close_connections()

    print()


def demo_api_credentials():
    """Demonstrate API credentials management."""
    print("🔐 API Credentials Demo")
    print("=" * 30)

    manager = UserManager("data/demo_metadata.db")

    try:
        # Store API credentials for various services
        print("🔑 Storing API credentials...")

        credentials = [
            {
                "service_name": "istat_api",
                "api_key": "istat_api_key_12345",
                "api_secret": "istat_secret_67890",
                "endpoint_url": "https://sdmx.istat.it/SDMXWS/rest/",
                "rate_limit": 50,
                "expires_at": datetime.now() + timedelta(days=365),
            },
            {
                "service_name": "powerbi_api",
                "api_key": "powerbi_app_id_abcdef",
                "api_secret": "powerbi_secret_ghijkl",
                "endpoint_url": "https://api.powerbi.com/v1.0/",
                "rate_limit": 100,
                "expires_at": datetime.now() + timedelta(days=90),
            },
            {
                "service_name": "tableau_api",
                "api_key": "tableau_token_mnopqr",
                "endpoint_url": "https://tableau.server.com/api/",
                "rate_limit": 200,
                "expires_at": datetime.now() + timedelta(days=180),
            },
        ]

        for cred in credentials:
            success = manager.store_api_credentials(**cred)
            if success:
                print(f"  ✅ {cred['service_name']}: Stored securely")
            else:
                print(f"  ❌ Failed to store {cred['service_name']}")

        # Verify credentials
        print("\n🔍 Verifying API credentials...")

        verification_tests = [
            ("istat_api", "istat_api_key_12345", True),
            ("istat_api", "wrong_key", False),
            ("powerbi_api", "powerbi_app_id_abcdef", True),
            ("nonexistent_service", "any_key", False),
        ]

        for service, key, expected in verification_tests:
            is_valid = manager.verify_api_credentials(service, key)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            expected_status = "✅ Expected" if is_valid == expected else "⚠️ Unexpected"
            print(f"  {service}: {status} {expected_status}")

    finally:
        manager.close_connections()

    print()


def demo_audit_logging():
    """Demonstrate audit logging functionality."""
    print("📋 Audit Logging Demo")
    print("=" * 25)

    manager = AuditManager("data/demo_metadata.db")

    try:
        # Log various user activities
        print("📝 Logging user activities...")

        activities = [
            (
                "analyst1",
                "login",
                "user",
                "analyst1",
                {"ip": "192.168.1.100", "browser": "Chrome"},
            ),
            (
                "analyst1",
                "dataset_view",
                "dataset",
                "DCIS_POPRES1",
                {"duration_seconds": 45},
            ),
            (
                "analyst1",
                "export_data",
                "dataset",
                "DCIS_POPRES1",
                {"format": "csv", "rows": 500},
            ),
            (
                "analyst2",
                "login",
                "user",
                "analyst2",
                {"ip": "192.168.1.101", "browser": "Firefox"},
            ),
            ("analyst2", "dashboard_access", "dashboard", "main", {"widgets": 6}),
            (
                "admin1",
                "user_settings_update",
                "user",
                "analyst1",
                {"changed_fields": ["theme", "language"]},
            ),
            (
                "system",
                "backup_created",
                "system",
                "database",
                {"size_mb": 15.7, "duration_ms": 2500},
            ),
        ]

        for user_id, action, resource_type, resource_id, details in activities:
            success = manager.log_audit(
                user_id,
                action,
                resource_type,
                resource_id,
                details,
                ip_address=details.get("ip"),
                execution_time_ms=details.get("duration_ms"),
            )
            if success:
                print(f"  ✅ {user_id}: {action} on {resource_type}")

        # Query audit logs with various filters
        print("\n🔍 Audit log queries:")

        # All logs for analyst1
        analyst1_logs = manager.get_audit_logs(user_id="analyst1")
        print(f"  📊 analyst1 total activities: {len(analyst1_logs)}")

        # Login activities
        login_logs = manager.get_audit_logs(action="login")
        print(f"  🔑 Total logins: {len(login_logs)}")

        # Dataset-related activities
        dataset_logs = manager.get_audit_logs(resource_type="dataset")
        print(f"  📚 Dataset activities: {len(dataset_logs)}")

        # Recent activities (last 5)
        recent_logs = manager.get_audit_logs(limit=5)
        print("\n📅 Recent activities:")
        for log in recent_logs:
            timestamp = log["timestamp"]
            user = log["user_id"]
            action = log["action"]
            resource = (
                f"{log['resource_type']}/{log['resource_id']}"
                if log["resource_id"]
                else log["resource_type"]
            )
            print(f"    {timestamp}: {user} -> {action} ({resource})")

        # Show detailed log entry
        if recent_logs:
            detailed_log = recent_logs[0]
            print("\n🔍 Detailed log entry:")
            for key, value in detailed_log.items():
                if key == "details_json":
                    continue  # Skip raw JSON
                if key == "details" and value:
                    print(f"    {key}: {json.dumps(value, indent=6)}")
                else:
                    print(f"    {key}: {value}")

    finally:
        manager.close_connections()

    print()


def demo_system_configuration():
    """Demonstrate system configuration management."""
    print("⚙️ System Configuration Demo")
    print("=" * 35)

    manager = ConfigurationManager("data/demo_metadata.db")

    try:
        # Set various system configurations
        print("🔧 Setting system configurations...")

        configs = [
            ("api.istat.rate_limit", "50", "integer", "ISTAT API requests per hour"),
            ("api.istat.timeout", "30", "integer", "ISTAT API timeout in seconds"),
            (
                "dashboard.refresh_interval",
                "300",
                "integer",
                "Dashboard auto-refresh interval",
            ),
            ("cache.default_ttl", "1800", "integer", "Default cache TTL in seconds"),
            ("cache.max_size", "1000", "integer", "Maximum cache entries"),
            ("security.session_timeout", "3600", "integer", "User session timeout"),
            ("logging.level", "INFO", "string", "Application logging level"),
            (
                "features.experimental_analytics",
                "false",
                "string",
                "Enable experimental features",
            ),
            ("database.backup_schedule", "daily", "string", "Backup frequency"),
        ]

        for key, value, config_type, description in configs:
            success = manager.set_config(key, value, config_type, description)
            if success:
                print(f"  ✅ {key}: {value}")

        # Retrieve configurations
        print("\n📖 Configuration values:")

        # Individual configurations
        rate_limit = manager.get_config("api.istat.rate_limit")
        timeout = manager.get_config("api.istat.timeout")
        logging_level = manager.get_config("logging.level")

        print(f"  ISTAT API rate limit: {rate_limit} requests/hour")
        print(f"  ISTAT API timeout: {timeout} seconds")
        print(f"  Logging level: {logging_level}")

        # Test default values
        unknown_config = manager.get_config("unknown.setting", "default_value")
        print(f"  Unknown setting (default): {unknown_config}")

        # Configuration for different environments
        manager.set_config(
            "database.host",
            "localhost",
            "string",
            "Dev database host",
            environment="development",
        )
        manager.set_config(
            "database.host",
            "prod.db.server.com",
            "string",
            "Prod database host",
            environment="production",
        )

        dev_host = manager.get_config("database.host", environment="development")
        prod_host = manager.get_config("database.host", environment="production")

        print(f"  Database host (dev): {dev_host}")
        print(f"  Database host (prod): {prod_host}")

    finally:
        manager.close_connections()

    print()


def demo_unified_repository():
    """Demonstrate unified repository facade pattern."""
    print("🔄 Unified Repository Demo")
    print("=" * 30)

    # Use the unified repository
    repo = get_unified_repository(
        sqlite_db_path="data/demo_metadata.db", duckdb_db_path="data/demo_analytics.db"
    )

    try:
        # Register dataset in both databases
        print("📊 Complete dataset registration...")
        success = repo.register_dataset_complete(
            "UNIFIED_DEMO",
            "Unified Repository Demo Dataset",
            "demo",
            "Demonstration dataset for unified repository",
            "DEMO_AGENCY",
            7,
            {"demo": True, "unified": True, "features": ["metadata", "analytics"]},
        )

        if success:
            print("  ✅ Dataset registered in both SQLite and DuckDB")

            # Get complete dataset information
            complete_dataset = repo.get_dataset_complete("UNIFIED_DEMO")
            if complete_dataset:
                print(f"  📋 Dataset: {complete_dataset['name']}")
                print(f"  📊 Category: {complete_dataset['category']}")
                print(
                    f"  🔧 Has analytics data: {complete_dataset['has_analytics_data']}"
                )
                print(
                    f"  📈 Analytics stats: {complete_dataset.get('analytics_stats', {})}"
                )

        # User preferences with caching
        print("\n👤 User preferences with caching...")
        repo.set_user_preference(
            "demo_user", "demo_setting", "demo_value", cache_minutes=5
        )

        # First access (loads from database and caches)
        value1 = repo.get_user_preference("demo_user", "demo_setting")
        print(f"  📖 First access: {value1}")

        # Second access (from cache)
        value2 = repo.get_user_preference("demo_user", "demo_setting")
        print(f"  💾 Cached access: {value2}")

        # Analytics query with audit
        print("\n📊 Analytics query with audit logging...")
        try:
            results = repo.execute_analytics_query(
                "SELECT 'Unified Repository Demo' as message, 42 as answer",
                user_id="demo_user",
            )
            if results:
                print(f"  ✅ Query result: {results[0]}")
        except Exception as e:
            print(f"  ℹ️ Analytics query info: {e} (expected in demo environment)")

        # System status
        print("\n🔧 System status:")
        status = repo.get_system_status()
        print(f"  SQLite metadata: {status['metadata_database']['status']}")
        print(f"  DuckDB analytics: {status['analytics_database']['status']}")
        print(f"  Cache size: {status['cache']['size']} entries")

        # Show database statistics
        metadata_stats = status["metadata_database"]["stats"]
        print("\n📈 Database statistics:")
        print(f"  Datasets: {metadata_stats.get('dataset_registry_count', 0)}")
        print(f"  User preferences: {metadata_stats.get('user_preferences_count', 0)}")
        print(f"  Audit logs: {metadata_stats.get('audit_log_count', 0)}")
        print(f"  API credentials: {metadata_stats.get('api_credentials_count', 0)}")
        print(f"  System configs: {metadata_stats.get('system_config_count', 0)}")

    finally:
        repo.close()

    print()


def demo_database_statistics():
    """Show overall database statistics."""
    print("📊 Database Statistics Summary")
    print("=" * 35)

    manager = DatasetManager("data/demo_metadata.db")

    try:
        stats = manager.get_database_stats()

        print("📋 SQLite Metadata Database:")
        print(f"  📚 Datasets: {stats.get('dataset_registry_count', 0)}")
        print(f"  👤 User preferences: {stats.get('user_preferences_count', 0)}")
        print(f"  🔐 API credentials: {stats.get('api_credentials_count', 0)}")
        print(f"  📋 Audit logs: {stats.get('audit_log_count', 0)}")
        print(f"  ⚙️ System configs: {stats.get('system_config_count', 0)}")
        print(f"  📏 Database size: {stats.get('database_size_bytes', 0):,} bytes")
        print(f"  🔖 Schema version: {stats.get('schema_version', 'unknown')}")

    finally:
        manager.close_connections()


def main():
    """Main demo function."""
    print("🗃️ SQLite Metadata Layer Demo for Osservatorio ISTAT")
    print("=" * 60)
    print("Demonstrating the SQLite portion of the hybrid SQLite + DuckDB architecture")
    print("as defined in ADR-002: Strategic Pivot to SQLite + DuckDB")
    print()

    # Ensure demo directory exists
    Path("data").mkdir(exist_ok=True)

    # Run all demos
    demo_metadata_schema()
    demo_dataset_registry()
    demo_user_preferences()
    demo_api_credentials()
    demo_audit_logging()
    demo_system_configuration()
    demo_unified_repository()
    demo_database_statistics()

    print("🎉 SQLite Metadata Layer Demo Complete!")
    print()
    print("Next steps:")
    print("  1. Review the created database: data/demo_metadata.db")
    print("  2. Run the tests: pytest tests/unit/test_sqlite_metadata.py -v")
    print(
        "  3. Explore the unified repository: tests/integration/test_unified_repository.py"
    )
    print("  4. Check out the DuckDB analytics demo: python examples/duckdb_demo.py")


if __name__ == "__main__":
    main()
