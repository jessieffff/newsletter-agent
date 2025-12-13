#!/usr/bin/env python3
"""Test script to verify observability setup works."""

import sys
import os

# Add app to path
sys.path.insert(0, "/Users/jiefangli/Downloads/newsletter-agent/apps/api")

def test_imports():
    """Test that we can import our observability modules without errors."""
    print("Testing imports...")
    try:
        from app.observability import setup_tracing, current_trace_id_hex
        print("✓ API observability module imports OK")
    except Exception as e:
        print(f"✗ API observability import failed: {e}")
        return False
    
    # Test agent observability too
    try:
        from newsletter_agent.observability import span
        print("✓ Agent observability module imports OK") 
    except Exception as e:
        print(f"✗ Agent observability import failed: {e}")
        return False
    
    return True

def test_tracing_setup():
    """Test that tracing setup works."""
    print("\nTesting tracing setup...")
    try:
        from app.observability import setup_tracing
        setup_tracing(service_name="test-service")
        print("✓ Tracing setup completed (no App Insights connection string)")
    except Exception as e:
        print(f"✗ Tracing setup failed: {e}")
        return False
    
    return True

def test_span_creation():
    """Test that we can create spans."""
    print("\nTesting span creation...")
    try:
        from newsletter_agent.observability import span
        with span("test.span", attributes={"test": "value"}):
            print("✓ Span context manager works")
    except Exception as e:
        print(f"✗ Span creation failed: {e}")
        return False
    
    return True

def test_fastapi_instrumentation():
    """Test that FastAPI instrumentation can be imported."""
    print("\nTesting FastAPI instrumentation...")
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        print("✓ FastAPI instrumentation available")
    except Exception as e:
        print(f"✗ FastAPI instrumentation failed: {e}")
        return False
    
    return True

def main():
    print("Newsletter Agent Observability Test\n" + "="*40)
    
    tests = [
        test_imports,
        test_tracing_setup, 
        test_span_creation,
        test_fastapi_instrumentation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All observability components work!")
        print("\nTo enable App Insights export, set:")
        print("export APPLICATIONINSIGHTS_CONNECTION_STRING='InstrumentationKey=...;IngestionEndpoint=...'")
    else:
        print("\n❌ Some components failed")
        sys.exit(1)

if __name__ == "__main__":
    main()