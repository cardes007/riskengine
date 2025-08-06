#!/usr/bin/env python3
"""
Test script to verify the lender cashflow transform functionality
"""

import requests
import json
import time

# Test data
test_pl_data = [
    {
        "month": "Jan 2024",
        "revenue": "1000000",
        "cogs": "400000",
        "grossProfit": "600000",
        "opex": "300000",
        "sm": "200000",
        "rd": "50000",
        "ga": "50000",
        "ebitda": "200000",
        "taxes": "40000",
        "interest": "10000",
        "da": "50000",
        "netIncome": "100000"
    },
    {
        "month": "Feb 2024",
        "revenue": "1100000",
        "cogs": "440000",
        "grossProfit": "660000",
        "opex": "320000",
        "sm": "220000",
        "rd": "55000",
        "ga": "45000",
        "ebitda": "240000",
        "taxes": "48000",
        "interest": "11000",
        "da": "52000",
        "netIncome": "129000"
    }
]

test_cohort_data = [
    {
        "name": "Older Cohorts",
        "revenue": ["500000", "480000", "460000", "440000", "420000", "400000", "380000", "360000", "340000", "320000", "300000", "280000"]
    },
    {
        "name": "Jan 2024",
        "revenue": ["1000000", "950000", "900000", "850000", "800000", "750000", "700000", "650000", "600000", "550000", "500000", "450000"]
    },
    {
        "name": "Feb 2024",
        "revenue": ["1100000", "1045000", "990000", "935000", "880000", "825000", "770000", "715000", "660000", "605000", "550000", "495000"]
    }
]

def test_backend():
    """Test the backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backend Endpoints")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Import data
    print("2. Testing data import...")
    try:
        response = requests.post(
            f"{base_url}/import/all",
            json={
                "pl_data": test_pl_data,
                "cohort_data": test_cohort_data
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Data import successful")
            print(f"   📊 S&M records: {result.get('sm_data', {}).get('count', 0)}")
            print(f"   📊 Cohort records: {result.get('cohort_data', {}).get('count', 0)}")
        else:
            print(f"   ❌ Data import failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Data import error: {e}")
        return False
    
    # Test 3: Transform to lender cashflows
    print("3. Testing lender cashflow transform...")
    try:
        response = requests.post(
            f"{base_url}/transform-to-lender-cashflows",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Lender cashflow transform successful")
            print(f"   📄 {result.get('message', '')}")
        else:
            print(f"   ❌ Lender cashflow transform failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Lender cashflow transform error: {e}")
        return False
    
    print("=" * 50)
    print("🎉 All tests passed!")
    return True

if __name__ == "__main__":
    print("Starting backend tests...")
    print("Make sure the backend server is running on http://localhost:8000")
    print()
    
    success = test_backend()
    
    if success:
        print("\n✅ Backend functionality is working correctly!")
        print("You can now use the frontend to:")
        print("1. Import your P&L and cohort data")
        print("2. Click the 'Transform to Lender Cashflows' button")
        print("3. Check the backend directory for generated Excel files")
    else:
        print("\n❌ Some tests failed. Please check the backend server and try again.") 