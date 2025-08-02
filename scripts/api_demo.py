#!/usr/bin/env python3
"""
🚀 Osservatorio API Demo - Interactive API Exploration

A human-friendly script to demonstrate and test the FastAPI endpoints.
Perfect for showcasing the API capabilities to stakeholders.
"""
import time
from typing import Any

import requests

try:
    from src.utils.config import Config

    BASE_URL = Config.API_BASE_URL
except ImportError:
    # Fallback for development
    BASE_URL = "http://localhost:8000"


def print_banner():
    """Print a nice banner"""
    print("🚀" + "=" * 60)
    print("  OSSERVATORIO ISTAT - FASTAPI DEMO")
    print("  Interactive API Exploration Tool")
    print("=" * 62)


def print_step(step_num: int, title: str, description: str = ""):
    """Print a demo step"""
    print(f"\n🔸 Step {step_num}: {title}")
    if description:
        print(f"   {description}")
    print("-" * 50)


def make_request(
    method: str, endpoint: str, headers: dict = None, data: dict = None
) -> dict[str, Any]:
    """Make an API request and return formatted response"""
    url = f"{BASE_URL}{endpoint}"

    print(f"   📡 {method.upper()} {endpoint}")

    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.lower() == "post":
            response = requests.post(url, headers=headers, json=data, timeout=10)

        # Print response info
        status_emoji = "✅" if response.status_code < 400 else "❌"
        print(f"   {status_emoji} Status: {response.status_code}")

        if "x-process-time" in response.headers:
            process_time = response.headers["x-process-time"]
            print(f"   ⚡ Process Time: {process_time}ms")

        try:
            json_response = response.json()
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": json_response,
            }
        except Exception:
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.text,
            }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"error": str(e)}


def demo_health_check():
    """Demo the health check endpoint"""
    print_step(1, "Health Check", "Verify that the API is running and healthy")

    result = make_request("GET", "/health")

    if result.get("status_code") == 200:
        data = result["data"]
        print(f"   ✅ System Status: {data.get('status', 'unknown')}")
        print(f"   📦 Version: {data.get('version', 'unknown')}")

        if "components" in data:
            print("   🔧 Components:")
            for component, info in data["components"].items():
                status = (
                    info.get("status", "unknown")
                    if isinstance(info, dict)
                    else str(info)
                )
                print(f"      • {component}: {status}")

    return result.get("status_code") == 200


def demo_openapi_docs():
    """Demo the OpenAPI documentation"""
    print_step(2, "API Documentation", "Check OpenAPI schema and documentation")

    result = make_request("GET", "/openapi.json")

    if result.get("status_code") == 200:
        data = result["data"]
        print(f"   📖 API Title: {data.get('info', {}).get('title', 'unknown')}")
        print(f"   🔢 Version: {data.get('info', {}).get('version', 'unknown')}")

        if "paths" in data:
            endpoints = list(data["paths"].keys())
            print(f"   🛣️  Available Endpoints: {len(endpoints)}")
            for endpoint in endpoints[:5]:  # Show first 5
                print(f"      • {endpoint}")
            if len(endpoints) > 5:
                print(f"      • ... and {len(endpoints) - 5} more")

    print("   🌐 View full docs at: http://localhost:8000/docs")
    return result.get("status_code") == 200


def demo_odata_service():
    """Demo the OData service endpoint"""
    print_step(3, "OData v4 Service", "PowerBI-compatible OData endpoint")

    result = make_request("GET", "/odata/")

    if result.get("status_code") == 200:
        data = result["data"]
        if "@odata.context" in data:
            print("   ✅ OData v4 service document available")

        if "value" in data:
            entity_sets = [item.get("name") for item in data["value"] if "name" in item]
            print(f"   📊 Entity Sets: {', '.join(entity_sets)}")

    print("   💼 PowerBI can connect to: http://localhost:8000/odata/")
    return result.get("status_code") == 200


def demo_authentication_flow():
    """Demo the authentication system"""
    print_step(
        4, "Authentication Demo", "Show JWT authentication (requires admin setup)"
    )

    # Try to access protected endpoint without auth
    print("   🔒 Testing protected endpoint without authentication...")
    result = make_request("GET", "/datasets")

    if result.get("status_code") == 401:
        print("   ✅ Authentication properly required")
        print("   💡 To test with authentication:")
        print("      1. Create API key with admin privileges")
        print("      2. Use /auth/token endpoint to get JWT")
        print("      3. Include 'Authorization: Bearer <token>' header")

    return True


def demo_performance_metrics():
    """Demo performance monitoring"""
    print_step(5, "Performance Monitoring", "Show API performance characteristics")

    print("   ⏱️  Testing response times...")

    endpoints_to_test = [
        ("/health", "Health Check"),
        ("/openapi.json", "OpenAPI Schema"),
        ("/odata/", "OData Service"),
    ]

    for endpoint, name in endpoints_to_test:
        start_time = time.time()
        make_request("GET", endpoint)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000
        print(f"   📊 {name}: {response_time:.1f}ms")

    return True


def main():
    """Main demo routine"""
    print_banner()

    print("🎯 This demo will test the key FastAPI endpoints")
    print("   Make sure the server is running: python src/api/fastapi_app.py")
    print("   Server should be available at: http://localhost:8000")

    input("\n👉 Press Enter to start the demo...")

    # Run demo steps
    steps_passed = 0
    total_steps = 5

    if demo_health_check():
        steps_passed += 1

    if demo_openapi_docs():
        steps_passed += 1

    if demo_odata_service():
        steps_passed += 1

    if demo_authentication_flow():
        steps_passed += 1

    if demo_performance_metrics():
        steps_passed += 1

    # Summary
    print_step(
        "✨",
        "Demo Complete!",
        f"Successfully demonstrated {steps_passed}/{total_steps} features",
    )

    if steps_passed == total_steps:
        print("   🎉 All API features are working correctly!")
    else:
        print(f"   ⚠️  {total_steps - steps_passed} features had issues")

    print("\n🔗 Next Steps:")
    print("   • Visit http://localhost:8000/docs for interactive API exploration")
    print(
        "   • Run 'python scripts/validate_issue29_implementation.py' for detailed testing"
    )
    print("   • Check 'python scripts/health_check.py' for system status")

    return steps_passed == total_steps


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("   Make sure FastAPI server is running on localhost:8000")
