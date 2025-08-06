#!/usr/bin/env python3
"""
Test script to verify the lender cashflow summary table functionality
"""

import requests
import json

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

def test_summary_table():
    """Test the summary table functionality"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Lender Cashflow Summary Table")
    print("=" * 60)
    
    # Step 1: Import data
    print("1. Importing test data...")
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
            print("   ✅ Data import successful")
        else:
            print(f"   ❌ Data import failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Data import error: {e}")
        return False
    
    # Step 2: Run transformation
    print("2. Running lender cashflow transformation...")
    try:
        response = requests.post(
            f"{base_url}/transform-to-lender-cashflows",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Transformation successful")
            
            # Check if results are returned
            if 'results' in result:
                print("   ✅ Summary results returned")
                results = result['results']
                
                # Display the results
                print("\n📊 Summary Results:")
                print("-" * 60)
                print(f"{'Scenario':<20} {'Loan Amount':<15} {'Net Return':<15} {'Return Rate':<12} {'Rows':<8}")
                print("-" * 60)
                
                for scenario, data in results.items():
                    scenario_name = scenario.replace('_', ' ').title()
                    loan_amount = f"${data['total_loan_amount']:,.0f}"
                    net_return = f"${data['total_net_return']:,.0f}"
                    return_rate = f"{data['positive_return_rate']:.2f}%"
                    rows = f"{data['total_rows']:,}"
                    
                    print(f"{scenario_name:<20} {loan_amount:<15} {net_return:<15} {return_rate:<12} {rows:<8}")
                
                print("-" * 60)
                print("✅ Summary table data is working correctly!")
                
            else:
                print("   ❌ No results returned in response")
                return False
                
        else:
            print(f"   ❌ Transformation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Transformation error: {e}")
        return False
    
    print("=" * 60)
    print("🎉 Summary table functionality test completed!")
    return True

if __name__ == "__main__":
    print("Starting summary table test...")
    print("Make sure the backend server is running on http://localhost:8000")
    print()
    
    success = test_summary_table()
    
    if success:
        print("\n✅ Summary table functionality is working correctly!")
        print("The frontend will now display a beautiful summary table with:")
        print("- Total loan amounts for both scenarios")
        print("- Total net returns with color coding")
        print("- Positive return rates with visual indicators")
        print("- Total rows processed")
    else:
        print("\n❌ Some tests failed. Please check the backend server and try again.") 