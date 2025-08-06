import requests
import json

test_data = {
    "pl_data": [
        {"month": "Jan 24", "sm": "150000"},
        {"month": "Feb 24", "sm": "180000"}
    ],
    "cohort_data": [
        {"name": "Jan 24", "revenue": ["300000"]},
        {"name": "Feb 24", "revenue": ["200000"]}
    ]
}

def test_api():
    base_url = "http://localhost:8000"
    print("Testing API endpoints...")
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    try:
        response = requests.post(f"{base_url}/import/all", json=test_data)
        print(f"Combined import: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"S&M records: {result['sm_data']['count']}")
            print(f"Cohort records: {result['cohort_data']['count']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Combined import failed: {e}")

if __name__ == "__main__":
    test_api()
