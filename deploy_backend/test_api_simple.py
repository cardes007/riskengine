import requests
import json

# Test data
test_data = {
    "pl_data": [
        {
            "month": "Jan 24",
            "sm": "150000"
        }
    ],
    "cohort_data": [
        {
            "name": "Jan 24",
            "revenue": ["300000"]
        }
    ]
}

def test_api():
    base_url = "http://localhost:8000"
    print("Testing API...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health: {response.status_code}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_api()
