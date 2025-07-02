"""
Simple test script for the Federal Budget Dashboard API

Run this after starting the local development server to verify endpoints work.
"""

import requests
import json
import os
from urllib.parse import urljoin

# API base URL (change this for different environments)
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def test_endpoint(endpoint: str, method: str = "GET", params: dict = None):
    """Test a single API endpoint"""
    url = urljoin(BASE_URL, endpoint)
    
    try:
        print(f"Testing {method} {endpoint}...")
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.request(method, url, params=params, timeout=10)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print("  ✅ Success")
        else:
            print(f"  ❌ Error: {response.text[:200]}")
        
        print()
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Connection error: {e}")
        print()
        return None

def main():
    """Run all API tests"""
    print("🧪 Testing Federal Budget Dashboard API")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Test basic endpoints
    test_endpoint("/")
    test_endpoint("/health")
    
    # Test budget endpoints
    test_endpoint("/api/budget")
    test_endpoint("/api/budget/categories")
    test_endpoint("/api/budget/years")
    
    # Test bill endpoints
    test_endpoint("/api/bills")
    test_endpoint("/api/bill/bbb")
    test_endpoint("/api/bill/bbb/changes")
    
    # Test compare endpoints
    test_endpoint("/api/compare", params={"bill_id": "bbb"})
    test_endpoint("/api/compare/summary", params={"bill_id": "bbb"})
    
    print("=" * 50)
    print("✅ API testing completed")
    print()
    print("Next steps:")
    print("1. If tests failed, check your database connection")
    print("2. Make sure you've run the seeding script: python scripts/seed_database.py")
    print("3. Verify your DATABASE_URL environment variable is set")

if __name__ == "__main__":
    main() 