#!/usr/bin/env python3
"""
Validation Script for Issue #29 - FastAPI REST API Development

Comprehensive validation of all deliverables and acceptance criteria.
This script validates that the FastAPI implementation meets all requirements
from Issue #29 including performance targets, authentication, and OData compliance.

Usage:
    python scripts/validate_issue29_implementation.py
"""
import json
import os
import time
from datetime import datetime, timedelta

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-final-validation-12345"

from fastapi.testclient import TestClient

from src.api.fastapi_app import app


def validate_issue_29_deliverables():
    """Comprehensive validation of Issue #29 deliverables"""

    print("=== FINAL VALIDATION: Issue #29 FastAPI REST API Development ===")
    print("Testing all deliverables and acceptance criteria...")

    client = TestClient(app)
    results = {}

    # Initialize authentication system
    from src.auth.jwt_manager import JWTManager
    from src.auth.sqlite_auth import SQLiteAuthManager
    from src.database.sqlite.manager import get_metadata_manager

    sqlite_manager = get_metadata_manager()
    auth_manager = SQLiteAuthManager(sqlite_manager)
    jwt_manager = JWTManager(sqlite_manager, secret_key=os.environ["JWT_SECRET_KEY"])

    # Create admin API key for testing (handle existing key)
    try:
        admin_key = auth_manager.generate_api_key(
            name=f"validation_admin_{int(time.time())}",
            scopes=["read", "write", "admin"],
        )
        print(f"\n✓ Created new admin API key (ID: {admin_key.id})")
    except Exception:
        # Use existing admin keys if creation fails
        existing_keys = auth_manager.list_api_keys()
        admin_keys = [k for k in existing_keys if "admin" in k.scopes]
        if admin_keys:
            admin_key = admin_keys[0]
            print(f"\n✓ Using existing admin API key (ID: {admin_key.id})")
        else:
            print("\n❌ No admin keys available - cannot proceed with validation")
            return {}, 0

    auth_token = jwt_manager.create_access_token(admin_key)
    headers = {"Authorization": f"Bearer {auth_token.access_token}"}

    print("✓ Admin authentication setup complete")

    # 1. DELIVERABLE: Core FastAPI Application
    print("\n1. Testing Core FastAPI Application...")

    # Health check endpoint
    response = client.get("/health")
    results["health_check"] = response.status_code == 200
    print(f"   ✓ Health check: {response.status_code}")

    # OpenAPI documentation
    response = client.get("/docs")
    results["openapi_docs"] = response.status_code == 200
    print(f"   ✓ OpenAPI docs: {response.status_code}")

    response = client.get("/openapi.json")
    results["openapi_schema"] = response.status_code == 200
    print(f"   ✓ OpenAPI schema: {response.status_code}")

    # 2. DELIVERABLE: JWT Authentication System
    print("\n2. Testing JWT Authentication System...")

    # Test protected endpoint without auth (should fail)
    response = client.get("/datasets")
    results["auth_required"] = response.status_code == 401
    print(f"   ✓ Authentication required: {response.status_code == 401}")

    # Test with valid token (should succeed)
    response = client.get("/datasets", headers=headers)
    results["auth_valid"] = response.status_code == 200
    print(f"   ✓ Valid token accepted: {response.status_code == 200}")

    # Test API key creation
    key_create_payload = {
        "name": "validation_test_key",
        "scopes": ["read", "write"],
        "rate_limit": 100,
    }
    response = client.post("/auth/token", json=key_create_payload, headers=headers)
    results["api_key_creation"] = response.status_code == 200
    print(f"   ✓ API key creation: {response.status_code == 200}")

    # 3. DELIVERABLE: Dataset Management Endpoints
    print("\n3. Testing Dataset Management Endpoints...")

    # List datasets
    start_time = time.time()
    response = client.get("/datasets?page=1&page_size=10", headers=headers)
    dataset_list_time = (time.time() - start_time) * 1000
    results["dataset_list"] = response.status_code == 200
    results["dataset_list_performance"] = dataset_list_time < 100  # <100ms target
    print(
        f"   ✓ Dataset list: {response.status_code == 200} ({dataset_list_time:.1f}ms)"
    )

    if response.status_code == 200:
        datasets_data = response.json()
        total_datasets = datasets_data.get("total_count", 0)
        print(f"     Found {total_datasets} datasets")

        # Test dataset detail
        if datasets_data.get("datasets"):
            dataset_id = datasets_data["datasets"][0]["dataset_id"]
            start_time = time.time()
            response = client.get(f"/datasets/{dataset_id}", headers=headers)
            dataset_detail_time = (time.time() - start_time) * 1000
            results["dataset_detail"] = response.status_code == 200
            results["dataset_detail_performance"] = (
                dataset_detail_time < 200
            )  # <200ms target
            print(
                f"   ✓ Dataset detail: {response.status_code == 200} ({dataset_detail_time:.1f}ms)"
            )

            # Test time series endpoint
            response = client.get(f"/datasets/{dataset_id}/timeseries", headers=headers)
            results["timeseries"] = response.status_code == 200
            print(f"   ✓ Time series: {response.status_code == 200}")

    # 4. DELIVERABLE: OData v4 Endpoint for PowerBI
    print("\n4. Testing OData v4 Endpoint for PowerBI...")

    # Service document
    response = client.get("/odata/", headers=headers)
    results["odata_service"] = response.status_code == 200
    print(f"   ✓ OData service document: {response.status_code == 200}")

    # Metadata document
    response = client.get("/odata/$metadata", headers=headers)
    results["odata_metadata"] = response.status_code == 200
    print(f"   ✓ OData metadata: {response.status_code == 200}")

    # Entity sets
    start_time = time.time()
    response = client.get("/odata/Datasets", headers=headers)
    odata_datasets_time = (time.time() - start_time) * 1000
    results["odata_datasets"] = response.status_code == 200
    results["odata_performance"] = odata_datasets_time < 500  # <500ms target
    print(
        f"   ✓ OData Datasets entity set: {response.status_code == 200} ({odata_datasets_time:.1f}ms)"
    )

    # Test OData query options
    response = client.get(
        "/odata/Datasets?$top=5&$filter=Category eq 'Demografia'", headers=headers
    )
    results["odata_query_options"] = response.status_code == 200
    print(f"   ✓ OData query options: {response.status_code == 200}")

    # 5. DELIVERABLE: Rate Limiting
    print("\n5. Testing Rate Limiting...")

    response = client.get("/datasets", headers=headers)
    has_rate_limit_headers = any(
        "ratelimit" in h.lower() for h in response.headers.keys()
    )
    results["rate_limiting"] = has_rate_limit_headers

    # Show which rate limit headers were found
    rate_headers = {
        k: v for k, v in response.headers.items() if "ratelimit" in k.lower()
    }
    print(f"   ✓ Rate limit headers: {has_rate_limit_headers}")
    if rate_headers:
        print(f"     Found headers: {rate_headers}")

    # 6. DELIVERABLE: Comprehensive Error Handling
    print("\n6. Testing Error Handling...")

    # Test 404 error
    response = client.get("/datasets/NONEXISTENT_DATASET", headers=headers)
    results["error_404"] = response.status_code == 404
    print(f"   ✓ 404 error handling: {response.status_code == 404}")

    # Test validation error
    response = client.get("/datasets?page=-1", headers=headers)
    results["validation_error"] = response.status_code == 422
    print(f"   ✓ Validation error: {response.status_code == 422}")

    # 7. DELIVERABLE: Usage Analytics (Admin)
    print("\n7. Testing Usage Analytics...")

    response = client.get("/analytics/usage", headers=headers)
    results["usage_analytics"] = response.status_code == 200
    print(f"   ✓ Usage analytics: {response.status_code == 200}")

    # Test API key listing
    response = client.get("/auth/keys", headers=headers)
    results["api_key_listing"] = response.status_code == 200
    print(f"   ✓ API key listing: {response.status_code == 200}")

    # 8. DELIVERABLE: Performance Requirements
    print("\n8. Validating Performance Requirements...")

    performance_results = {
        "dataset_list": results.get("dataset_list_performance", False),
        "dataset_detail": results.get("dataset_detail_performance", False),
        "odata_query": results.get("odata_performance", False),
    }

    print(f"   ✓ Dataset List <100ms: {performance_results['dataset_list']}")
    print(f"   ✓ Dataset Detail <200ms: {performance_results['dataset_detail']}")
    print(f"   ✓ OData Query <500ms: {performance_results['odata_query']}")

    # 9. DELIVERABLE: Security & Middleware
    print("\n9. Testing Security & Middleware...")

    # Test CORS headers
    response = client.options("/datasets", headers={"Origin": "http://localhost:3000"})
    has_cors = "access-control-allow-origin" in response.headers
    results["cors_middleware"] = has_cors
    print(f"   ✓ CORS middleware: {has_cors}")

    # Test response time headers
    response = client.get("/health")
    has_timing = "x-process-time" in response.headers
    results["timing_middleware"] = has_timing
    print(f"   ✓ Timing middleware: {has_timing}")

    # FINAL RESULTS SUMMARY
    print("\n" + "=" * 60)
    print("ISSUE #29 DELIVERABLES VALIDATION SUMMARY")
    print("=" * 60)

    deliverables = {
        "Core FastAPI Application": all(
            [
                results.get("health_check", False),
                results.get("openapi_docs", False),
                results.get("openapi_schema", False),
            ]
        ),
        "JWT Authentication System": all(
            [
                results.get("auth_required", False),
                results.get("auth_valid", False),
                results.get("api_key_creation", False),
            ]
        ),
        "Dataset Management Endpoints": all(
            [
                results.get("dataset_list", False),
                results.get("dataset_detail", False),
                results.get("timeseries", False),
            ]
        ),
        "OData v4 PowerBI Integration": all(
            [
                results.get("odata_service", False),
                results.get("odata_metadata", False),
                results.get("odata_datasets", False),
                results.get("odata_query_options", False),
            ]
        ),
        "Rate Limiting & Security": all(
            [
                results.get("rate_limiting", False),
                results.get("cors_middleware", False),
                results.get("timing_middleware", False),
            ]
        ),
        "Error Handling & Validation": all(
            [results.get("error_404", False), results.get("validation_error", False)]
        ),
        "Usage Analytics (Admin)": all(
            [
                results.get("usage_analytics", False),
                results.get("api_key_listing", False),
            ]
        ),
        "Performance Requirements": all(
            [
                performance_results["dataset_list"],
                performance_results["dataset_detail"],
                performance_results["odata_query"],
            ]
        ),
    }

    total_deliverables = len(deliverables)
    completed_deliverables = sum(1 for status in deliverables.values() if status)

    for deliverable, status in deliverables.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {deliverable}")

    print("\n" + "=" * 60)
    print(
        f"OVERALL COMPLETION: {completed_deliverables}/{total_deliverables} deliverables"
    )
    success_rate = (completed_deliverables / total_deliverables) * 100
    print(f"SUCCESS RATE: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 ISSUE #29 IMPLEMENTATION: FULLY FUNCTIONAL")
    elif success_rate >= 80:
        print("⚠️  ISSUE #29 IMPLEMENTATION: MOSTLY FUNCTIONAL")
    else:
        print("❌ ISSUE #29 IMPLEMENTATION: NEEDS ATTENTION")

    print("=" * 60)

    return deliverables, success_rate


if __name__ == "__main__":
    validate_issue_29_deliverables()
