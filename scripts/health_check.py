#!/usr/bin/env python3
"""
🏥 Osservatorio Health Check - Interactive System Verification

A human-friendly script to verify that all components are working correctly.
Run this script to get a quick overview of system health.
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from utils import (
    ScriptContext,
    get_script_config,
    print_error,
    print_step,
    print_success,
    print_warning,
    setup_script_logging,
)


def print_header():
    """Print the health check header"""
    print("🏥 Osservatorio Health Check")
    print("=" * 30)
    print(
        f"System health verification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


def print_section(title):
    """Print a section header"""
    print(f"\n📋 {title}")
    print("-" * (len(title) + 4))


def check_status(description, check_func):
    """Check a component and print status"""
    print(f"   {description}...", end=" ", flush=True)
    try:
        result = check_func()
        if result:
            print("✅ OK")
            return True
        else:
            print("❌ FAIL")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def check_database_files():
    """Check if database files exist"""
    db_files = [
        "data/databases/osservatorio_metadata.db",
        "data/databases/osservatorio.duckdb",
    ]
    return all(Path(f).exists() for f in db_files)


def check_fastapi_server():
    """Check if FastAPI server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_fastapi_endpoints():
    """Check key FastAPI endpoints"""
    endpoints = [
        ("Health Check", "/health"),
        ("OpenAPI Docs", "/openapi.json"),
        ("OData Service", "/odata/"),
    ]

    all_good = True
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {name}: {status} ({response.status_code})")
            if response.status_code != 200:
                all_good = False
        except Exception as e:
            print(f"   {name}: ❌ ERROR - {e}")
            all_good = False

    return all_good


def check_python_imports():
    """Check if key modules can be imported"""
    modules = [
        ("FastAPI App", "src.api.fastapi_app"),
        ("Database Manager", "src.database.sqlite.manager"),
        ("Auth System", "src.auth.sqlite_auth"),
        ("DuckDB Integration", "src.database.duckdb.manager"),
    ]

    all_good = True
    for name, module in modules:
        try:
            __import__(module)
            print(f"   {name}: ✅ OK")
        except Exception as e:
            print(f"   {name}: ❌ ERROR - {e}")
            all_good = False

    return all_good


def check_issue29_deliverables():
    """Check Issue #29 specific deliverables"""
    deliverables = [
        ("PowerBI Guide", "docs/integrations/POWERBI_FASTAPI_CONNECTION.md"),
        ("OData Router", "src/api/odata.py"),
        ("JWT Manager", "src/auth/jwt_manager.py"),
        ("Test Suite", "tests/unit/test_fastapi_integration.py"),
    ]

    all_good = True
    for name, file_path in deliverables:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"   {name}: {status}")
        if not exists:
            all_good = False

    return all_good


def main():
    """Main health check routine"""
    print_header()

    total_checks = 0
    passed_checks = 0

    # Check 1: Database Files
    print_section("Database Layer")
    if check_status("SQLite & DuckDB files exist", check_database_files):
        passed_checks += 1
    total_checks += 1

    # Check 2: Python Environment
    print_section("Python Environment")
    print("   Core modules import:")
    if check_python_imports():
        passed_checks += 1
    total_checks += 1

    # Check 3: FastAPI Server
    print_section("FastAPI Server")
    server_running = check_status("Server responding", check_fastapi_server)
    if server_running:
        passed_checks += 1
        print("\n   API Endpoints:")
        if check_fastapi_endpoints():
            passed_checks += 1
        total_checks += 1
    else:
        print("   ⚠️  Server not running. Start with: python src/api/fastapi_app.py")
    total_checks += 1

    # Check 4: Issue #29 Deliverables
    print_section("Issue #29 Deliverables")
    print("   Key files:")
    if check_issue29_deliverables():
        passed_checks += 1
    total_checks += 1

    # Summary
    print_section("Summary")
    percentage = (passed_checks / total_checks) * 100

    if percentage == 100:
        status_emoji = "🎉"
        status_text = "ALL SYSTEMS OPERATIONAL"
    elif percentage >= 75:
        status_emoji = "✅"
        status_text = "MOSTLY OPERATIONAL"
    elif percentage >= 50:
        status_emoji = "⚠️"
        status_text = "PARTIAL ISSUES"
    else:
        status_emoji = "❌"
        status_text = "CRITICAL ISSUES"

    print(f"   {status_emoji} {status_text}")
    print(f"   {passed_checks}/{total_checks} checks passed ({percentage:.1f}%)")

    if not server_running:
        print("\n💡 Quick Start:")
        print("   python src/api/fastapi_app.py")
        print("   Then visit: http://localhost:8000/docs")

    print("\n📊 For detailed API testing:")
    print("   python scripts/validate_issue29_implementation.py")

    return percentage == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
