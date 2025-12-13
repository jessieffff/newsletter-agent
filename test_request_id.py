#!/usr/bin/env python3
"""Test request ID middleware and span creation."""

import sys
sys.path.insert(0, "/Users/jiefangli/Downloads/newsletter-agent/apps/api")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

def test_request_id_middleware():
    """Test that x-request-id is generated and returned."""
    print("Testing request ID middleware...")
    
    client = TestClient(app)
    
    # Test 1: No x-request-id provided - should generate one
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    request_id_1 = response.headers["x-request-id"]
    print(f"✓ Generated request ID: {request_id_1}")
    
    # Test 2: Provide x-request-id - should echo it back
    test_id = "test-12345"
    response = client.get("/health", headers={"x-request-id": test_id})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == test_id
    print(f"✓ Echoed request ID: {test_id}")
    
    return True

def main():
    print("Request ID Middleware Test\n" + "="*30)
    
    try:
        test_request_id_middleware()
        print("\n🎉 Request ID middleware works!")
        print("\nNext steps:")
        print("1. Set APPLICATIONINSIGHTS_CONNECTION_STRING to enable export")
        print("2. Run newsletter workflow to see agent spans")
        print("3. Check App Insights for traces with request correlation")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()